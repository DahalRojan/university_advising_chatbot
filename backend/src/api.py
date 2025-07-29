import os
import uuid
import jwt
import datetime
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .llm_chain import ask_llm
from .retriever import advanced_retrieve
from .conversation_db import create_table, add_message, get_history, get_user_sessions, update_session_summary, get_session_summary, delete_conversation
from .summarizer import generate_conversation_summary, get_fallback_summary

# Load environment variables
load_dotenv("./configs/.env")

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

print(f"🍪 Session middleware configuration:")
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

print(f"🍪 Cookie domain configuration: {cookie_domain}")

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
        print(f"🔑 JWT token created for user: {user_data['email']}")
        
        # Redirect to frontend with JWT token in query parameter
        return RedirectResponse(url=f"{FRONTEND_URL}?auth=success&token={jwt_token}")
    except Exception as e:
        print(f"Error creating JWT token: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=token_failed")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        print("❌ No Authorization header found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        user = verify_jwt_token(credentials.credentials)
        print(f"✅ JWT user authenticated: {user.get('email', 'No email')}")
        return user
    except HTTPException as e:
        print(f"❌ JWT verification failed: {e.detail}")
        raise e

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_request: ChatRequest, request: Request, user: dict = Depends(get_current_user)):
    user_email = user["email"]
    user_name = user["name"]
    
    # Generate session_id if not provided
    session_id = chat_request.session_id or str(uuid.uuid4())
    
    try:
        # Add user message to conversation history
        add_message(session_id, user_email, "user", chat_request.message)
        
        # Get conversation history for context
        history = get_history(session_id, user_email)
        
        # Retrieve relevant context from knowledge base
        context = advanced_retrieve(chat_request.message)
        
        # Get LLM response
        response = ask_llm(chat_request.message, context, history)
        
        # Add LLM response to conversation history
        add_message(session_id, user_email, "assistant", response["answer"])
        
        # Generate summary after a few messages (e.g., after 4 messages total)
        updated_history = get_history(session_id, user_email)
        if len(updated_history) >= 4 and len(updated_history) % 2 == 0:  # Every 2 exchanges
            try:
                summary = generate_conversation_summary(updated_history)
                if not summary or summary == "University advising chat":
                    summary = get_fallback_summary(updated_history)
                update_session_summary(session_id, user_email, summary)
            except Exception as e:
                print(f"Error generating summary: {e}")
                # Use fallback summary
                summary = get_fallback_summary(updated_history)
                update_session_summary(session_id, user_email, summary)
        
        return ChatResponse(
            answer=response["answer"],
            confidence=response.get("confidence", 80),
            suggested_questions=response.get("suggested_questions", []),
            session_id=session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

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
        print("🔍 Auth status check - No token provided")
        return {"authenticated": False}
    
    try:
        user = verify_jwt_token(credentials.credentials)
        print(f"🔍 Auth status check - User authenticated: {user.get('email', 'No email')}")
        return {"authenticated": True, "user": user}
    except HTTPException:
        print("🔍 Auth status check - Invalid/expired token")
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

@app.get("/auth/status")
async def auth_status(request: Request):
    """Check if user is authenticated"""
    user = request.session.get('user')
    session_data = dict(request.session)
    
    print(f"Auth status check - Session data: {session_data}")
    print(f"Auth status check - User: {user}")
    print(f"Auth status check - Session ID exists: {bool(request.session)}")
    
    if user:
        return {"authenticated": True, "user": user, "debug": {"session_keys": list(session_data.keys())}}
    return {"authenticated": False, "debug": {"session_data": session_data, "session_exists": bool(request.session)}}

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

# Catch-all route for SPA routing (must be last!)
@app.get("/{path:path}")
async def serve_spa_routes(path: str):
    """Serve frontend for all non-API routes (SPA routing)"""
    # Serve frontend for all non-API routes
    if os.path.exists("./frontend/dist/index.html"):
        return FileResponse("./frontend/dist/index.html")
    return {"message": "Frontend not found - API only mode"}
