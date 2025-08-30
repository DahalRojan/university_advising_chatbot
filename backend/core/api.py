import os
import uuid
import jwt
import datetime
from typing import List, Optional
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .llm_chain import ask_llm, ask_llm_enhanced
from .llm_chain_personalized import ask_llm_personalized
from .retriever import advanced_retrieve, advanced_retrieve_with_confidence
from .conversation_db import create_table, add_message, get_history, get_user_sessions, update_session_summary, get_session_summary, delete_conversation
from utils.summarizer import generate_conversation_summary, get_fallback_summary
from features.intelligence.context_manager import ConversationContextManager
from features.intelligence.query_consistency import QueryConsistencyEngine
from features.intelligence.fallback_manager import SmartFallbackManager
from features.onboarding.onboarding_api import (
    OnboardingAPI, get_onboarding_api, 
    CourseSearchRequest, CourseResponse, DepartmentResponse,
    StudentProfileRequest, StudentProfileResponse,
    AcademicGoalRequest, CourseInterestRequest, OnboardingProgressRequest,
    OnboardingStepResponse, OnboardingProgressResponse,
    validate_user_email, validate_course_code
)
from features.auth.password_auth import get_password_auth_manager
from features.auth.models import (
    UserRegistrationRequest, UserLoginRequest, EmailVerificationRequest,
    UserRegistrationResponse, UserLoginResponse, EmailVerificationResponse,
    ResendVerificationRequest, ResendVerificationResponse,
    CheckAvailabilityRequest, CheckAvailabilityResponse
)

# Load environment variables
load_dotenv("./config/.env")

# Validate required environment variables
required_env_vars = {
    'OAUTH_CLIENT_ID': os.getenv("OAUTH_CLIENT_ID"),
    'OAUTH_CLIENT_SECRET': os.getenv("OAUTH_CLIENT_SECRET"), 
    'OAUTH_TENANT_ID': os.getenv("OAUTH_TENANT_ID"),
    'SESSION_SECRET': os.getenv("SESSION_SECRET", "supersecret")
}

missing_vars = [key for key, value in required_env_vars.items() if not value and key != 'SESSION_SECRET']
if missing_vars:
    print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
    print("OAuth features will be disabled until these are provided.")

app = FastAPI()

# Mount static files (frontend assets)
if os.path.exists("./frontend/dist"):
    app.mount("/assets", StaticFiles(directory="./frontend/dist/assets"), name="assets")
    app.mount("/static", StaticFiles(directory="./frontend/dist"), name="static")

# Health check endpoint for Cloud Run
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Serve frontend root
@app.get("/")
async def serve_frontend_root():
    if os.path.exists("./frontend/dist/index.html"):
        return FileResponse("./frontend/dist/index.html")
    return {"message": "Frontend not found - API only mode"}

# Frontend URL configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Configure CORS origins - include both development and production URLs
cors_origins = [
    "http://localhost:5173", 
    "http://localhost:5174", 
    "http://127.0.0.1:5173", 
    "http://127.0.0.1:5174"
]

# Add production frontend URL if provided
if FRONTEND_URL and FRONTEND_URL not in cors_origins:
    cors_origins.append(FRONTEND_URL)

# Add common Cloudflare Pages patterns for production deployment
if FRONTEND_URL and not FRONTEND_URL.startswith("http://localhost") and not FRONTEND_URL.startswith("http://127.0.0.1"):
    # Add .pages.dev variants to handle different deployment URLs
    if ".pages.dev" not in FRONTEND_URL:
        base_name = FRONTEND_URL.replace("https://", "").replace("http://", "").split(".")[0]
        cors_origins.append(f"https://{base_name}.pages.dev")

# Always add the actual Cloudflare Pages URL
cors_origins.append("https://university-advising-chatbot.pages.dev")

print(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware (required for Authlib)
# Detect if running locally - check multiple indicators
is_local = (
    os.getenv("ENVIRONMENT", "development").lower() == "development" or 
    os.getenv("PORT") != "8080" or
    FRONTEND_URL.startswith("http://localhost") or
    FRONTEND_URL.startswith("http://127.0.0.1")
)

print(f"[COOKIE] Session middleware configuration:")
print(f"   - is_local: {is_local}")
print(f"   - FRONTEND_URL: {FRONTEND_URL}")
print(f"   - same_site: {'lax' if is_local else 'none'}")
print(f"   - https_only: {not is_local}")

# Configure cookie domain for cross-origin requests
cookie_domain = None
if not is_local and FRONTEND_URL:
    from urllib.parse import urlparse
    parsed_url = urlparse(FRONTEND_URL)
    # For Cloudflare Pages, use the base domain to allow cross-subdomain cookies
    if 'pages.dev' in parsed_url.netloc:
        cookie_domain = '.pages.dev'
    else:
        cookie_domain = parsed_url.netloc

print(f"[COOKIE] Cookie domain configuration: {cookie_domain}")

app.add_middleware(
    SessionMiddleware, 
    secret_key=required_env_vars['SESSION_SECRET'],
    max_age=3600,  # 1 hour session timeout for security
    same_site='none' if not is_local else 'lax',  # 'none' required for cross-site
    https_only=not is_local,  # Only HTTPS in production
    path="/",  # All paths
    domain=cookie_domain  # Explicit domain for cross-origin cookies
)

# OAuth configuration
CLIENT_ID = required_env_vars['OAUTH_CLIENT_ID']
CLIENT_SECRET = required_env_vars['OAUTH_CLIENT_SECRET']
TENANT_ID = required_env_vars['OAUTH_TENANT_ID']
OAUTH_METADATA_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"

# Initialize conversation database
create_table()

# Lazy load enhanced components only when needed
context_manager = None
consistency_engine = None
fallback_manager = None

# Simple response cache for common queries
QUICK_RESPONSES = {
    "when do classes start": "I don't have the Fall 2025 start date. Check the academic calendar.",
    "when does fall start": "I don't have the Fall 2025 start date. Check the academic calendar.", 
    "when does fall 2025 start": "I don't have the Fall 2025 start date. Check the academic calendar.",
    "how to pay fines": "You can pay fines through Gannon Self-Service or at www.gannon.edu/epayment using E-Check, Credit Card, or Cashier's Check.",
    "how do i pay fines": "You can pay fines through Gannon Self-Service or at www.gannon.edu/epayment using E-Check, Credit Card, or Cashier's Check.",
    "what happens if i break rules": "Depending on the severity, disciplinary actions may include Written Warning, Official Warning, Probation, Suspension, or Expulsion.",
    "smoking policy": "The university prohibits the use of tobacco products, including smoking, on all University owned, operated, or leased property.",
}

def get_enhanced_components():
    """Lazy load enhanced components only when needed for non-greeting queries"""
    global context_manager, consistency_engine, fallback_manager
    if context_manager is None:
        print("Lazy loading enhanced conversation intelligence...")
        context_manager = ConversationContextManager()
        consistency_engine = QueryConsistencyEngine()
        fallback_manager = SmartFallbackManager()
        print("Enhanced components loaded successfully")
    return context_manager, consistency_engine, fallback_manager

# JWT Configuration
JWT_SECRET = required_env_vars['SESSION_SECRET']  # Reuse session secret for JWT
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# JWT Security
security = HTTPBearer(auto_error=False)

def create_jwt_token(user_data: dict) -> str:
    """Create JWT token for user"""
    payload = {
        "user_id": user_data["id"],
        "name": user_data["name"],
        "email": user_data["email"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "id": payload["user_id"],
            "name": payload["name"],
            "email": payload["email"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# OAuth setup - Modified for multi-tenant support
oauth = OAuth()

if TENANT_ID == 'common':
    # For multi-tenant, use manual configuration to avoid issuer validation issues
    oauth.register(
        name='azure',
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        authorize_url=f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize',
        access_token_url=f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token',
        jwks_uri=f'https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys',
        client_kwargs={
            'scope': 'openid profile email User.Read',
            'response_type': 'code',
            'response_mode': 'query'
        }
    )
else:
    # For single tenant, use the standard configuration
    oauth.register(
        name='azure',
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        server_metadata_url=OAUTH_METADATA_URL,
        client_kwargs={
            'scope': 'openid profile email User.Read',
            'response_type': 'code',
            'response_mode': 'query'
        }
    )

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: str = None

class ChatResponse(BaseModel):
    answer: str
    confidence: int
    suggested_questions: list[str]
    session_id: str

@app.get('/login')
async def login(request: Request):
    # Only force HTTPS in production, keep HTTP for localhost
    redirect_uri = str(request.url_for('auth'))
    print(f"DEBUG: Original redirect_uri: {redirect_uri}")
    print(f"DEBUG: Request hostname: {request.url.hostname}")
    
    if request.url.hostname not in ['localhost', '127.0.0.1']:
        redirect_uri = redirect_uri.replace('http://', 'https://')
        print(f"DEBUG: Changed to HTTPS: {redirect_uri}")
    else:
        print(f"DEBUG: Keeping HTTP for localhost: {redirect_uri}")
    
    return await oauth.azure.authorize_redirect(request, redirect_uri)

@app.post('/login')
async def post_login_redirect():
    """
    Handle incorrect POST to /login - redirect to proper endpoints
    This fixes the 405 Method Not Allowed error
    """
    raise HTTPException(
        status_code=400, 
        detail="Use GET /login for OAuth or POST /auth/login for username/password login"
    )

@app.get('/auth')
async def auth(request: Request):
    import httpx
    
    print(f"Auth callback received with query params: {dict(request.query_params)}")
    
    # Get the authorization code from the callback
    code = request.query_params.get('code')
    if not code:
        print("No authorization code received")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=no_code")
    
    try:
        # For multi-tenant, manually exchange code for token to avoid issuer validation
        if TENANT_ID == 'common':
            # Manually exchange authorization code for access token
            token_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
            token_data = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': str(request.url_for('auth')) if request.url.hostname in ['localhost', '127.0.0.1'] else str(request.url_for('auth')).replace('http://', 'https://'),
                'scope': 'openid profile email User.Read'
            }
            
            async with httpx.AsyncClient() as client:
                token_response = await client.post(token_url, data=token_data)
                if token_response.status_code != 200:
                    print(f"Token exchange failed: {token_response.status_code} - {token_response.text}")
                    return RedirectResponse(url=f"{FRONTEND_URL}/login?error=token_failed")
                
                token = token_response.json()
                print(f"Token received successfully: {bool(token.get('access_token'))}")
                
                # Get user info from Microsoft Graph API
                headers = {'Authorization': f"Bearer {token['access_token']}"}
                user_response = await client.get('https://graph.microsoft.com/v1.0/me', headers=headers)
                
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    user = {
                        'oid': user_data.get('id'),
                        'name': user_data.get('displayName', ''),
                        'email': user_data.get('mail') or user_data.get('userPrincipalName', ''),
                        'preferred_username': user_data.get('userPrincipalName', '')
                    }
                    print(f"User info from Graph API: {user.get('name', 'Unknown')}")
                else:
                    print(f"Failed to get user info: {user_response.status_code}")
                    return RedirectResponse(url=f"{FRONTEND_URL}/login?error=user_info_failed")
        
        else:
            # For single tenant, use standard OAuth flow
            token = await oauth.azure.authorize_access_token(request)
            user = await oauth.azure.parse_id_token(request, token)
            print(f"User parsed from ID token: {user.get('name', 'Unknown')}")
            
    except Exception as e:
        print(f"Error during authentication: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=auth_failed")
    
    try:
        # Create user data for JWT
        user_data = {
            "id": user['oid'],
            "name": user.get('name', ''),
            "email": user.get('email', user.get('preferred_username', ''))
        }
        
        # Create JWT token
        jwt_token = create_jwt_token(user_data)
        print(f"[JWT] JWT token created for user: {user_data['email']}")
        
        # Redirect to frontend with JWT token in query parameter
        return RedirectResponse(url=f"{FRONTEND_URL}?auth=success&token={jwt_token}")
    except Exception as e:
        print(f"Error creating JWT token: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=token_failed")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        print("[AUTH] No Authorization header found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        user = verify_jwt_token(credentials.credentials)
        print(f"[AUTH] JWT user authenticated: {user.get('email', 'No email')}")
        return user
    except HTTPException as e:
        print(f"[AUTH] JWT verification failed: {e.detail}")
        raise e

@app.post("/chat", response_model=ChatResponse)
async def chat_enhanced(chat_request: ChatRequest, request: Request, user: dict = Depends(get_current_user)):
    """
    Enhanced chat endpoint with Phase 1 conversation intelligence:
    - Context-aware conversations with entity tracking
    - Query consistency checking to prevent contradictions
    - Smart fallback management to reduce unhelpful responses
    - Confidence-based retrieval with detailed analysis
    """
    user_email = user["email"]
    user_name = user["name"]
    
    # Generate session_id if not provided
    session_id = chat_request.session_id or str(uuid.uuid4())
    
    try:
        print(f"Processing enhanced chat request from {user_email}")
        print(f"   Query: {chat_request.message}")
        print(f"   Session: {session_id}")
        
        # Add user message to conversation history
        add_message(session_id, user_email, "user", chat_request.message)
        
        # Get conversation history for context (excluding current message for similarity check)
        full_history = get_history(session_id, user_email)
        history_for_similarity = full_history[:-1]  # Exclude current message
        history_for_context = full_history[:-1]     # For LLM context
        
        print(f"   History length: {len(history_for_context)} messages")
        
        # Ultra-fast response checks
        import re
        query_clean = chat_request.message.lower().strip()
        
        # 1. Check for cached quick responses
        for pattern, response in QUICK_RESPONSES.items():
            if pattern in query_clean:
                print(f"Quick response cache hit for: {pattern}")
                add_message(session_id, user_email, "assistant", response)
                return ChatResponse(
                    answer=response,
                    confidence=100,
                    suggested_questions=["What else can I help with?"],
                    session_id=session_id
                )
        
        # 2. Check for greetings
        is_greeting = bool(re.match(r'^\\s*(hi|hello|hey|greetings|good\\s+(morning|afternoon|evening)|how\\s+are\\s+you)\\s*\\??$', query_clean))
        
        if is_greeting:
            print("Greeting detected - using instant local response")
            
            # Warm, personalized greeting responses
            import random
            user_name = user["name"].split()[0] if user.get("name") else ""
            
            if history_for_context and len(history_for_context) > 0:
                returning_greetings = [
                    f"Hi{' ' + user_name if user_name else ''}! What else can I help you with today?",
                    f"Welcome back{' ' + user_name if user_name else ''}! How can I assist you further?",
                    f"Hello again{' ' + user_name if user_name else ''}! What's your next question?"
                ]
                greeting_response = random.choice(returning_greetings)
            else:
                first_greetings = [
                    f"Hello{' ' + user_name if user_name else ''}! I'm here to help with your academic planning. What can I assist you with today?",
                    f"Hi{' ' + user_name if user_name else ''}! I'm your academic advisor assistant. I can help with courses, requirements, and planning - what's on your mind?",
                    f"Welcome{' ' + user_name if user_name else ''}! I'm excited to help you with your academic journey. What questions do you have?",
                    f"Hello{' ' + user_name if user_name else ''}! I'm here to support your academic success. How can I help you today?"
                ]
                greeting_response = random.choice(first_greetings)
            
            # Add messages to history
            add_message(session_id, user_email, "assistant", greeting_response)
            
            print(f"[OK] Ultra-fast greeting response (no component loading)")
            
            return ChatResponse(
                answer=greeting_response,
                confidence=100,
                suggested_questions=[
                    "What CS courses are available?",
                    "What are the prerequisites for [specific course]?",
                    "How do I plan my schedule for next semester?"
                ],
                session_id=session_id
            )
        
        # Only load enhanced components for non-greeting queries
        print("Loading enhanced components for complex query...")
        context_manager, consistency_engine, fallback_manager = get_enhanced_components()
        
        # PHASE 1 ENHANCEMENT 1: Check for query similarity (consistency)
        print("Checking query consistency...")
        query_similarity = consistency_engine.check_query_similarity(
            chat_request.message, history_for_similarity, session_id
        )
        
        if query_similarity.get("is_similar"):
            print(f"   [OK] Similar query detected (score: {query_similarity['similarity_score']:.2f})")
            print(f"   Previous query: {query_similarity['similar_query']}")
        else:
            print("   [INFO] No similar previous queries found")
        
        # Handle very similar queries with cached responses
        if (query_similarity.get("is_similar") and 
            query_similarity.get("similarity_score", 0) > 0.9 and
            query_similarity.get("consistency_requirement") == "return_previous"):
            
            print("   [CACHE] Returning enhanced cached response")
            cached_response = consistency_engine._create_cached_response(query_similarity, chat_request.message)
            
            # Add response to history
            add_message(session_id, user_email, "assistant", cached_response["answer"])
            
            return ChatResponse(
                answer=cached_response["answer"],
                confidence=cached_response.get("confidence", 4) * 20,  # Convert 1-5 to 0-100
                suggested_questions=cached_response.get("suggested_questions", []),
                session_id=session_id
            )
        
        # PHASE 1 ENHANCEMENT 2: Enhanced retrieval with confidence scoring
        print("Performing enhanced retrieval...")
        retrieval_result = advanced_retrieve_with_confidence(chat_request.message)
        
        print(f"   Retrieval confidence: {retrieval_result['confidence']['confidence_score']:.2f}")
        print(f"   Documents found: {retrieval_result['retrieval_details']['final_docs_count']}")
        print(f"   Recommendation: {retrieval_result['recommendation']['action']}")
        
        # PHASE 1 ENHANCEMENT 3: Smart fallback analysis
        print("Analyzing fallback requirements...")
        
        # Build conversation context for fallback analysis
        if history_for_context:
            conversation_context = context_manager.build_enhanced_context(
                history_for_context, user_email, chat_request.message
            )
        else:
            conversation_context = None
        
        # Preliminary LLM confidence estimation based on retrieval
        estimated_llm_confidence = min(5, max(1, int(retrieval_result['confidence']['confidence_score'] * 5)))
        
        fallback_decision = fallback_manager.should_provide_fallback(
            retrieval_result, estimated_llm_confidence, chat_request.message, conversation_context
        )
        
        print(f"   Fallback decision: {fallback_decision['should_fallback']} ({fallback_decision.get('fallback_type', 'none')})")
        print(f"   Query category: {fallback_decision['query_category']}")
        
        # DISABLED: Skip direct fallback - let LLM handle everything naturally
        
        # PHASE 1 ENHANCEMENT 4: Enhanced LLM call with full personalization
        print("Generating personalized advisor response...")
        context_documents = retrieval_result.get("documents_text", "")
        
        # Get onboarding API for student context
        onboarding_api = get_onboarding_api()
        
        response = ask_llm_personalized(
            chat_request.message, 
            context_documents, 
            history_for_context, 
            user_email,
            user,  # Pass full user data including name from JWT
            onboarding_api
        )
        
        print(f"   LLM confidence: {response.get('confidence', 3)}")
        print(f"   Response length: {len(response.get('answer', ''))}")
        
        # PHASE 1 ENHANCEMENT 5: Apply consistency checking
        if query_similarity.get("is_similar"):
            print("Applying consistency awareness...")
            response = consistency_engine.generate_consistency_aware_response(
                query_similarity, response, chat_request.message
            )
        
        # DISABLED: Skip fallback enhancement - let LLM response stand alone
        
        # Add LLM response to conversation history
        add_message(session_id, user_email, "assistant", response["answer"])
        
        # Enhanced summary generation (existing logic with minor improvements)
        updated_history = get_history(session_id, user_email)
        if len(updated_history) >= 4 and len(updated_history) % 2 == 0:  # Every 2 exchanges
            try:
                summary = generate_conversation_summary(updated_history)
                if not summary or summary == "University advising chat":
                    summary = get_fallback_summary(updated_history)
                update_session_summary(session_id, user_email, summary)
                print(f"   Generated conversation summary: {summary}")
            except Exception as e:
                print(f"   ⚠️ Error generating summary: {e}")
                summary = get_fallback_summary(updated_history)
                update_session_summary(session_id, user_email, summary)
        
        # Log final response details
        final_confidence = response.get("confidence", 3)
        print(f"[OK] Enhanced response generated successfully")
        print(f"   Final confidence: {final_confidence}")
        print(f"   Suggested questions: {len(response.get('suggested_questions', []))}")
        print(f"   Context references: {len(response.get('context_references', []))}")
        
        return ChatResponse(
            answer=response["answer"],
            confidence=final_confidence * 20 if final_confidence <= 5 else final_confidence,  # Normalize to 0-100
            suggested_questions=response.get("suggested_questions", []),
            session_id=session_id
        )
        
    except Exception as e:
        print(f"[ERROR] Enhanced chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Enhanced chat error: {str(e)}")

@app.get("/user/sessions")
async def get_user_chat_sessions(request: Request, user: dict = Depends(get_current_user)):
    """Get user's recent chat sessions"""
    user_email = user["email"]
    sessions = get_user_sessions(user_email)
    return {"sessions": sessions}

@app.get("/chat/{session_id}/history")
async def get_chat_history(session_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Get chat history for a specific session"""
    user_email = user["email"]
    history = get_history(session_id, user_email)
    return {"history": history, "session_id": session_id}

@app.delete("/chat/{session_id}")
async def delete_chat_session(session_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Delete a specific chat session"""
    user_email = user["email"]
    success = delete_conversation(session_id, user_email)
    if success:
        return {"message": "Conversation deleted successfully", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")

@app.get("/auth/status")
async def auth_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Check if user is authenticated via JWT token"""
    if not credentials:
        print("[AUTH] Auth status check - No token provided")
        return {"authenticated": False}
    
    try:
        user = verify_jwt_token(credentials.credentials)
        print(f"[AUTH] Auth status check - User authenticated: {user.get('email', 'No email')}")
        return {"authenticated": True, "user": user}
    except HTTPException:
        print("[AUTH] Auth status check - Invalid/expired token")
        return {"authenticated": False}

@app.get("/user/profile")
async def get_user_profile(user: dict = Depends(get_current_user)):
    """Get authenticated user's profile information"""
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"]
    }

@app.post("/logout")
async def logout(request: Request):
    """Logout user by clearing session"""
    request.session.clear()
    return {"message": "Logged out successfully"}

@app.get("/clear-session")
async def clear_session(request: Request):
    """Force clear all session data"""
    request.session.clear()
    return {"message": "Session completely cleared", "session_data": dict(request.session)}

# =========================================================
# PASSWORD-BASED AUTHENTICATION ENDPOINTS
# =========================================================

@app.post("/auth/register", response_model=UserRegistrationResponse)
async def register_user(
    registration_data: UserRegistrationRequest,
    request: Request
):
    """Register a new user with username/password"""
    auth_manager = get_password_auth_manager()
    client_ip = request.client.host
    
    try:
        result = auth_manager.register_user(
            username=registration_data.username,
            email=registration_data.email,
            password=registration_data.password,
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            ip_address=client_ip
        )
        
        return UserRegistrationResponse(
            success=result["success"],
            message=result["message"],
            email=result["email"],
            user_id=str(result["user_id"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

@app.post("/auth/login", response_model=UserLoginResponse)
async def login_user(
    login_data: UserLoginRequest,
    request: Request
):
    """Login user with username/password"""
    auth_manager = get_password_auth_manager()
    client_ip = request.client.host
    
    try:
        user_data = auth_manager.authenticate_user(
            identifier=login_data.identifier,
            password=login_data.password,
            ip_address=client_ip
        )
        
        # Create JWT token (same as OAuth flow)
        jwt_token = create_jwt_token(user_data)
        
        return UserLoginResponse(
            success=True,
            user=user_data,
            token=jwt_token,
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/auth/verify-email", response_model=EmailVerificationResponse)
async def verify_email(verification_data: EmailVerificationRequest):
    """Verify user email with verification token"""
    auth_manager = get_password_auth_manager()
    
    print(f"[EMAIL_VERIFY] Received verification request")
    print(f"[EMAIL_VERIFY] Token length: {len(verification_data.token)}")
    print(f"[EMAIL_VERIFY] Token preview: {verification_data.token[:20]}...")
    
    try:
        verified = auth_manager.verify_email(verification_data.token)
        
        if verified:
            return EmailVerificationResponse(
                success=True,
                message="Email verified successfully! You can now log in."
            )
        else:
            return EmailVerificationResponse(
                success=False,
                message="Invalid or expired verification token"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Email verification failed")

@app.post("/auth/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    resend_data: ResendVerificationRequest
):
    """Resend email verification to user"""
    auth_manager = get_password_auth_manager()
    
    try:
        sent = auth_manager.resend_verification_email(resend_data.email)
        
        if sent:
            return ResendVerificationResponse(
                success=True,
                message="Verification email sent. Please check your inbox."
            )
        else:
            return ResendVerificationResponse(
                success=False,
                message="Could not send verification email. Email may already be verified or account may not exist."
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to resend verification email")

@app.post("/auth/check-availability", response_model=CheckAvailabilityResponse)
async def check_availability(
    availability_data: CheckAvailabilityRequest
):
    """Check if username or email is available"""
    auth_manager = get_password_auth_manager()
    
    try:
        response = CheckAvailabilityResponse()
        
        if availability_data.username:
            response.username_available = auth_manager.check_username_availability(
                availability_data.username
            )
        
        if availability_data.email:
            response.email_available = auth_manager.check_email_availability(
                availability_data.email
            )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Availability check failed")

@app.get("/test/config")
async def test_config():
    """Test endpoint to verify OAuth configuration"""
    return {
        "client_id": CLIENT_ID[:10] + "...",  # Only show first 10 chars for security
        "tenant_id": TENANT_ID,
        "metadata_url": OAUTH_METADATA_URL,
        "frontend_url": FRONTEND_URL
    }

@app.get("/test/auth")
async def test_auth(request: Request):
    """Test endpoint to check authentication"""
    session_data = dict(request.session)
    user = request.session.get('user')
    return {
        "session_exists": bool(session_data),
        "session_data": session_data,
        "user_authenticated": bool(user),
        "user_info": user if user else None
    }

@app.post("/admin/ingest")
async def trigger_data_ingestion():
    """Admin endpoint to run data ingestion"""
    try:
        from .ingest_data import ingest
        ingest()
        return {"message": "Data ingestion completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.get("/admin/collection-status")
async def check_collection_status():
    """Check vector database collection status"""
    try:
        from .retriever import client, COLLECTION
        collections = [c.name for c in client.get_collections().collections]
        collection_info = None
        if COLLECTION in collections:
            collection_info = client.get_collection(COLLECTION)
        
        return {
            "collection_exists": COLLECTION in collections,
            "collection_name": COLLECTION,
            "all_collections": collections,
            "collection_info": collection_info.dict() if collection_info else None
        }
    except Exception as e:
        return {"error": str(e), "collection_exists": False}

# =========================================================
# ONBOARDING API ENDPOINTS
# =========================================================

@app.get("/api/onboarding/departments", response_model=List[DepartmentResponse])
async def get_departments(
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Get all active departments for course selection"""
    return onboarding_api.get_departments()

@app.post("/api/onboarding/courses/search", response_model=List[CourseResponse])
async def search_courses(
    search_request: CourseSearchRequest,
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Search courses with filters for onboarding course selection"""
    return onboarding_api.search_courses(search_request)

@app.get("/api/onboarding/courses/department/{department_code}", response_model=List[CourseResponse])
async def get_courses_by_department(
    department_code: str,
    level: str = "undergraduate",
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Get all courses for a specific department"""
    return onboarding_api.get_courses_by_department(department_code, level)

@app.get("/api/onboarding/steps", response_model=List[OnboardingStepResponse])
async def get_onboarding_steps(
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Get all onboarding steps for the workflow"""
    return onboarding_api.get_onboarding_steps()

@app.post("/api/onboarding/profile")
async def create_or_update_profile(
    profile_data: StudentProfileRequest,
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Create or update student profile during onboarding"""
    user_email = validate_user_email(user["email"])
    success = onboarding_api.create_or_update_student_profile(user_email, profile_data)
    return {"success": success, "message": "Profile updated successfully"}

@app.get("/api/onboarding/profile", response_model=Optional[StudentProfileResponse])
async def get_student_profile(
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Get student profile and dashboard data"""
    user_email = validate_user_email(user["email"])
    profile = onboarding_api.get_student_dashboard(user_email, user_data=user)
    if not profile:
        # Create empty profile if it doesn't exist
        empty_profile_data = StudentProfileRequest()
        onboarding_api.create_or_update_student_profile(user_email, empty_profile_data)
        profile = onboarding_api.get_student_dashboard(user_email, user_data=user)
    return profile

@app.post("/api/onboarding/progress")
async def update_onboarding_progress(
    progress_data: OnboardingProgressRequest,
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Update student onboarding progress"""
    user_email = validate_user_email(user["email"])
    success = onboarding_api.update_onboarding_progress(user_email, progress_data)
    return {"success": success, "message": "Onboarding progress updated successfully"}

@app.get("/api/onboarding/progress", response_model=List[OnboardingProgressResponse])
async def get_onboarding_progress(
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Get student's onboarding progress"""
    user_email = validate_user_email(user["email"])
    return onboarding_api.get_student_onboarding_progress(user_email)

@app.get("/api/onboarding/status")
async def get_onboarding_status(
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Check if user has completed onboarding"""
    user_email = validate_user_email(user["email"])
    profile = onboarding_api.get_student_dashboard(user_email, user_data=user)
    
    if not profile:
        # Create empty profile for new users
        try:
            from features.onboarding.onboarding_api import StudentProfileRequest
            empty_profile = StudentProfileRequest()
            onboarding_api.create_or_update_student_profile(user_email, empty_profile)
            profile = onboarding_api.get_student_dashboard(user_email, user_data=user)
        except Exception as e:
            print(f"Failed to create profile for {user_email}: {e}")
            # If profile creation fails, assume onboarding not complete
            return {
                "isComplete": False,
                "completionPercentage": 0,
                "profileCompletionPercentage": 0
            }
    
    return {
        "isComplete": profile.is_onboarding_complete if profile else False,
        "completionPercentage": profile.onboarding_progress_percentage if profile else 0,
        "profileCompletionPercentage": profile.profile_completion_percentage if profile else 0
    }

@app.post("/api/onboarding/complete")
async def complete_onboarding(
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Mark onboarding as completed (skip remaining steps)"""
    user_email = validate_user_email(user["email"])
    
    try:
        # Update the profile to mark onboarding as complete
        with onboarding_api.db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE student_profiles 
                    SET is_onboarding_complete = true,
                        profile_completion_percentage = 100,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_email = %s
                """, (user_email,))
                
                if cur.rowcount == 0:
                    # Profile doesn't exist, create one
                    from features.onboarding.onboarding_api import StudentProfileRequest
                    empty_profile = StudentProfileRequest()
                    onboarding_api.create_or_update_student_profile(user_email, empty_profile)
                    
                    # Now update it to complete
                    cur.execute("""
                        UPDATE student_profiles 
                        SET is_onboarding_complete = true,
                            profile_completion_percentage = 100,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_email = %s
                    """, (user_email,))
                
                conn.commit()
        
        return {"success": True, "message": "Onboarding completed successfully"}
    
    except Exception as e:
        print(f"Failed to complete onboarding for {user_email}: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete onboarding")

@app.post("/api/onboarding/course-interests")
async def add_course_interest(
    interest_data: CourseInterestRequest,
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Add course to student's interest list"""
    user_email = validate_user_email(user["email"])
    validate_course_code(interest_data.course_code)
    success = onboarding_api.add_course_interest(user_email, interest_data)
    return {"success": success, "message": "Course interest added successfully"}

@app.get("/api/onboarding/course-interests")
async def get_course_interests(
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Get student's course interests"""
    user_email = validate_user_email(user["email"])
    return {"course_interests": onboarding_api.get_student_course_interests(user_email)}

@app.post("/api/onboarding/academic-goals")
async def add_academic_goal(
    goal_data: AcademicGoalRequest,
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Add academic goal for student"""
    user_email = validate_user_email(user["email"])
    success = onboarding_api.add_academic_goal(user_email, goal_data)
    return {"success": success, "message": "Academic goal added successfully"}

@app.get("/api/onboarding/academic-goals")
async def get_academic_goals(
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Get student's academic goals"""
    user_email = validate_user_email(user["email"])
    return {"academic_goals": onboarding_api.get_student_academic_goals(user_email)}

@app.get("/api/onboarding/academic-history")
async def get_academic_history(
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Get student's academic history (completed and enrolled courses)"""
    user_email = validate_user_email(user["email"])
    print(f"🔍 Getting academic history for user: {user_email}")
    academic_history = onboarding_api.get_student_academic_history(user_email)
    print(f"📚 Academic history found: {len(academic_history)} courses for {user_email}")
    return {"academic_history": academic_history}

@app.get("/api/onboarding/field-interests")
async def get_field_interests(
    user: dict = Depends(get_current_user),
    onboarding_api: OnboardingAPI = Depends(get_onboarding_api)
):
    """Get student's field interests from onboarding"""
    user_email = validate_user_email(user["email"])
    return {"field_interests": onboarding_api.get_student_field_interests(user_email)}

# Catch-all route for SPA routing (must be last!)
@app.get("/{path:path}")
async def serve_spa_routes(path: str):
    """Serve frontend for all non-API routes (SPA routing)"""
    # Serve frontend for all non-API routes
    if os.path.exists("./frontend/dist/index.html"):
        return FileResponse("./frontend/dist/index.html")
    return {"message": "Frontend not found - API only mode"}
