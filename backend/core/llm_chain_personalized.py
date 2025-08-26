"""
Enhanced LLM Chain with Personalized Academic Advisor Integration
Fast, context-aware responses with student personalization
"""

import json
import time
import re
import random
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from features.intelligence.personalized_advisor import get_advisor_engine, response_cache
from features.onboarding.onboarding_api import OnboardingAPI
import requests

# Load environment variables
from dotenv import load_dotenv
config_path = Path(__file__).parent.parent / "config" / ".env"
load_dotenv(config_path)

if TYPE_CHECKING:
    from features.intelligence.personalized_advisor import PersonalizedAdvisorEngine

# Configuration
MODEL_NAME = os.getenv("GROQ_MODEL", "llama3-70b-8192")
API_KEY = os.getenv("GROQ_API_KEY")
API_BASE_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")

def ask_llm_personalized(user_input: str, context: str, history: List[Dict], 
                        user_email: str, user_data: Dict, 
                        onboarding_api: OnboardingAPI) -> Dict[str, Any]:
    """
    Enhanced LLM with full personalization and fast response optimization
    """
    start_time = time.time()
    
    # 1. ULTRA-FAST GREETING DETECTION
    is_greeting = _is_greeting(user_input)
    if is_greeting:
        return _handle_personalized_greeting(user_email, user_data, history, onboarding_api)
    
    # 2. CACHE CHECK FOR FREQUENT QUERIES
    advisor_engine = get_advisor_engine(onboarding_api)
    student_context = advisor_engine.get_student_context(user_email, user_data)
    
    # Create safe hash for caching (exclude non-hashable parts)
    cache_context = {k: v for k, v in student_context.items() if isinstance(v, (str, int, float, bool, type(None)))}
    context_hash = str(hash(str(cache_context)))
    
    cache_key = response_cache.get_cache_key(user_email, user_input, context_hash)
    cached_response = response_cache.get(cache_key)
    
    if cached_response:
        print(f"⚡ Cache hit - Response time: {time.time() - start_time:.3f}s")
        return cached_response
    
    # 3. QUICK PATTERN RESPONSES (Common academic questions)
    quick_response = _check_quick_patterns(user_input, student_context, advisor_engine)
    if quick_response:
        response_cache.set(cache_key, quick_response)
        print(f"⚡ Quick pattern - Response time: {time.time() - start_time:.3f}s")
        return quick_response
    
    # 4. FULL PERSONALIZED LLM RESPONSE
    try:
        # Enhance query with student context for better retrieval
        enhanced_query = _enhance_query_with_student_context(user_input, student_context)
        
        # Re-retrieve with enhanced query if it's course-related
        if _is_course_related_query(user_input):
            print(f"📚 Enhanced course query: {enhanced_query}")
            # Import retriever to get fresh results with enhanced query
            from core.retriever import advanced_retrieve
            enhanced_context = "\n".join(advanced_retrieve(enhanced_query, top_k=8))
            context = enhanced_context
        
        # Build personalized prompt with student context
        personalized_prompt = advisor_engine.build_personalized_prompt(
            user_email, user_input, context, history, user_data
        )
        
        # Analyze query intent for better suggestions
        query_intent = advisor_engine._analyze_query_intent(user_input)
        
        # Enhanced system prompt with response format
        system_prompt = f"""{personalized_prompt}

Please provide a comprehensive response to the student's question using the knowledge base provided.

RESPONSE GUIDELINES:
- Be warm and personalized, addressing the student by name when appropriate
- Reference their specific academic context (major, level, goals)
- Provide actionable, specific advice with concrete course recommendations
- Use only information from the provided knowledge base
- When recommending courses, include course codes, titles, and brief descriptions
- Explain how recommended courses align with their major and career goals
- If specific course information is not available, acknowledge limitations professionally
- Keep responses thorough but organized (3-5 paragraphs maximum)

Current query intent: {query_intent}
IMPORTANT: If this is a course recommendation query, provide specific course suggestions with codes and titles from the knowledge base."""
        
        # Build conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add relevant conversation history (last 6 messages for context)
        for msg in history[-6:]:
            role = "user" if msg["sender"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["text"]})
        
        # Add current query
        messages.append({"role": "user", "content": user_input})
        
        # Call LLM API
        response = _call_llm_api(messages)
        
        if response:
            # Since Groq doesn't guarantee JSON format, handle as plain text
            # Try to parse as JSON first, fallback to plain text
            llm_output = None
            try:
                llm_output = json.loads(response)
            except json.JSONDecodeError:
                # Treat as plain text response
                llm_output = {
                    "answer": response,
                    "confidence": 85,  # Default confidence for successful text response
                    "reasoning": "Generated personalized response based on student context",
                    "next_steps": []
                }
            
            # Add personalized suggested questions
            suggested_questions = advisor_engine.generate_suggested_questions(
                student_context, query_intent
            )
            
            final_response = {
                "answer": llm_output.get("answer", response),  # Fallback to raw response
                "confidence": llm_output.get("confidence", 85),
                "reasoning": llm_output.get("reasoning", ""),
                "next_steps": llm_output.get("next_steps", []),
                "suggested_questions": suggested_questions,
                "context_references": llm_output.get("context_references", []),
                "response_time": round(time.time() - start_time, 3),
                "personalization_level": "high" if student_context.get("status") != "error" else "basic"
            }
            
            # Cache successful responses
            if llm_output.get("confidence", 0) > 70:
                response_cache.set(cache_key, final_response)
            
            print(f"✅ Personalized response - Time: {final_response['response_time']}s")
            return final_response
        
        else:
            raise Exception("No response from LLM API")
            
    except Exception as e:
        print(f"❌ Error in personalized LLM: {e}")
        return _fallback_response(user_input, student_context, advisor_engine, start_time)


def _is_greeting(user_input: str) -> bool:
    """Fast greeting detection"""
    pattern = r'^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|how\s+are\s+you|what\'?s\s+up)\s*[.!?]*\s*$'
    return bool(re.match(pattern, user_input.lower().strip()))


def _handle_personalized_greeting(user_email: str, user_data: Dict, history: List[Dict], 
                                 onboarding_api: OnboardingAPI) -> Dict[str, Any]:
    """Generate personalized greeting based on student context"""
    advisor_engine = get_advisor_engine(onboarding_api)
    student_context = advisor_engine.get_student_context(user_email, user_data)
    
    # Get student name
    user_name = user_data.get("name", "").split()[0] if user_data.get("name") else ""
    preferred_name = ""
    
    if student_context.get("status") != "error":
        personal_info = student_context.get("personal_info", {})
        preferred_name = personal_info.get("preferred_name") or personal_info.get("first_name") or user_name
    else:
        preferred_name = user_name
    
    # Check if returning user
    is_returning = len(history) > 0
    
    # Build personalized greeting
    if is_returning:
        greetings = [
            f"Hi again, {preferred_name}! How can I help you continue your academic planning?",
            f"Welcome back, {preferred_name}! What academic questions can I assist with today?",
            f"Hello {preferred_name}! Ready to tackle more academic planning together?"
        ]
    else:
        if student_context.get("status") != "error":
            academic = student_context.get("academic_profile", {})
            major = academic.get("primary_major", "")
            level = academic.get("academic_level", "")
            
            greetings = [
                f"Hello {preferred_name}! I'm excited to help with your {major} {level} program planning. What's on your mind today?",
                f"Hi {preferred_name}! As your academic advisor, I'm here to support your {major} journey. How can I help?",
                f"Welcome {preferred_name}! I see you're working on your {major} degree - I'm here to help with any academic questions you have."
            ]
        else:
            greetings = [
                f"Hello {preferred_name}! I'm your academic advisor assistant. I'd love to help you with course planning, requirements, or any academic questions.",
                f"Hi {preferred_name}! I'm here to support your academic success at Gannon University. What can I help you with today?",
                f"Welcome {preferred_name}! I'm excited to help you navigate your academic journey. What questions do you have?"
            ]
    
    greeting = random.choice(greetings)
    
    # Generate contextual suggested questions
    suggested_questions = advisor_engine.generate_suggested_questions(student_context, "General Inquiry")
    
    return {
        "answer": greeting,
        "confidence": 100,
        "suggested_questions": suggested_questions,
        "response_time": 0.05,  # Ultra-fast greeting
        "personalization_level": "high" if preferred_name else "basic"
    }


def _check_quick_patterns(user_input: str, student_context: Dict, 
                         advisor_engine: "PersonalizedAdvisorEngine") -> Optional[Dict]:
    """Check for common patterns that can be answered quickly"""
    query_lower = user_input.lower().strip()
    
    # Get student info for personalization
    preferred_name = ""
    major = ""
    level = ""
    
    if student_context.get("status") != "error":
        personal_info = student_context.get("personal_info", {})
        academic_info = student_context.get("academic_profile", {})
        preferred_name = personal_info.get("preferred_name", "")
        major = academic_info.get("primary_major", "")
        level = academic_info.get("academic_level", "")
    
    name_part = f"{preferred_name}, " if preferred_name else ""
    
    # Academic status questions
    if "how am i doing" in query_lower or "my progress" in query_lower:
        if student_context.get("status") != "error":
            completion = student_context.get("completion_status", {})
            profile_completion = completion.get("profile_completion", 0)
            academic = student_context.get("academic_profile", {})
            
            response = f"You're making great progress{', ' + preferred_name if preferred_name else ''}! Your academic profile is {profile_completion}% complete. "
            
            if academic.get("cumulative_gpa"):
                response += f"Your current GPA is {academic['cumulative_gpa']}. "
            
            if completion.get("onboarding_complete"):
                response += "You've completed your onboarding, which puts you ahead of the game for academic planning!"
            else:
                response += "Once you complete your full profile, I'll be able to give you even more personalized advice."
            
            return {
                "answer": response,
                "confidence": 95,
                "suggested_questions": [
                    "What courses should I take next semester?",
                    "How can I improve my academic performance?",
                    "What graduation requirements do I still need?"
                ],
                "response_time": 0.1,
                "personalization_level": "high"
            }
    
    # Course planning questions - let full LLM handle with enhanced retrieval
    # Removed quick pattern to allow proper course retrieval and recommendations
    
    # Graduation requirements
    if any(phrase in query_lower for phrase in ["graduation requirements", "degree requirements", "what do i need to graduate"]):
        if major and level:
            response = f"Excellent question{', ' + preferred_name if preferred_name else ''}! For your {major} {level} degree, I'll need to check the specific requirements in our academic catalog. Let me pull up the current degree requirements for your program."
        else:
            response = f"I'd be happy to help with graduation requirements{', ' + preferred_name if preferred_name else ''}! Let me search for the degree requirements that apply to your program."
        
        return {
            "answer": response,
            "confidence": 90,
            "suggested_questions": [
                "How many credits do I need total?",
                "What are my remaining requirements?",
                "When can I graduate?"
            ],
            "response_time": 0.12,
            "personalization_level": "high" if major else "basic"
        }
    
    # Thank you responses
    if any(phrase in query_lower for phrase in ["thank you", "thanks", "thx", "appreciate"]):
        responses = [
            f"You're very welcome{', ' + preferred_name if preferred_name else ''}! I'm always here when you need academic guidance.",
            f"Happy to help{', ' + preferred_name if preferred_name else ''}! Feel free to come back anytime with more questions.",
            f"My pleasure{', ' + preferred_name if preferred_name else ''}! Supporting your academic success is what I'm here for."
        ]
        
        return {
            "answer": random.choice(responses),
            "confidence": 100,
            "suggested_questions": [
                "What else can I help you plan?",
                "Any other academic questions?",
                "Ready to tackle your next semester?"
            ],
            "response_time": 0.05,
            "personalization_level": "high" if preferred_name else "basic"
        }
    
    return None


def _call_llm_api(messages: List[Dict]) -> Optional[str]:
    """Call Groq LLM API"""
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            API_BASE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"LLM API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error calling LLM API: {e}")
        return None


def _fallback_response(user_input: str, student_context: Dict, 
                      advisor_engine: "PersonalizedAdvisorEngine", 
                      start_time: float) -> Dict[str, Any]:
    """Provide fallback response when LLM fails"""
    preferred_name = ""
    if student_context.get("status") != "error":
        personal_info = student_context.get("personal_info", {})
        preferred_name = personal_info.get("preferred_name", "")
    
    name_part = f"{preferred_name}, " if preferred_name else ""
    
    response = f"I'm sorry {name_part}I'm having trouble processing your request right now. Let me help you in a different way - could you try rephrasing your question or let me know specifically what academic topic you'd like guidance on?"
    
    return {
        "answer": response,
        "confidence": 50,
        "suggested_questions": [
            "What courses are available in my program?",
            "Help me plan my next semester",
            "What are my graduation requirements?"
        ],
        "response_time": round(time.time() - start_time, 3),
        "personalization_level": "basic"
    }


# Backwards compatibility
def ask_llm_enhanced(user_input: str, context: str, history: List[Dict], 
                    user_email: str = "unknown") -> Dict[str, Any]:
    """
    Enhanced LLM call with basic personalization (backwards compatibility)
    """
    # For backwards compatibility, use basic user data
    user_data = {"email": user_email, "name": ""}
    
    # Mock onboarding API if not available
    try:
        from features.onboarding.onboarding_api import OnboardingAPI, get_onboarding_api
        onboarding_api = get_onboarding_api()
    except:
        onboarding_api = None
    
    if onboarding_api:
        return ask_llm_personalized(user_input, context, history, user_email, user_data, onboarding_api)
    else:
        # Fallback to original behavior
        return {
            "answer": "I'm here to help with your academic questions!",
            "confidence": 75,
            "suggested_questions": [
                "What courses should I take?",
                "Help me plan my schedule",
                "What are the requirements for my major?"
            ]
        }


def _enhance_query_with_student_context(query: str, student_context: Dict) -> str:
    """
    Enhance the query with student's academic context for better retrieval
    """
    # Get student's academic information
    academic = student_context.get("academic_profile", {})
    major = academic.get("primary_major", "")
    level = academic.get("academic_level", "")
    
    # If it's a course-related query, enhance with major context
    if _is_course_related_query(query):
        enhanced_query = query
        
        # Add degree program and major context
        degree_program = academic.get("degree_program", "")
        if degree_program:
            enhanced_query += f" {degree_program}"
            
            # Add specific course codes based on degree program
            if "data science" in degree_program.lower():
                enhanced_query += " GCIS Data Science Analytics Machine Learning Statistics Python"
            elif "business analytics" in degree_program.lower():
                enhanced_query += " GMBA Business Analytics Data Analytics Predictive Analytics"
            elif "computer" in degree_program.lower() and "information" in degree_program.lower():
                enhanced_query += " GCIS Computer Information Systems Software Engineering"
            elif "business administration" in degree_program.lower():
                enhanced_query += " GMBA MBA Business Administration Management"
            elif "engineering" in degree_program.lower():
                enhanced_query += " Engineering Mathematics Science"
        
        # Fallback to major if no degree program
        elif major:
            if "data science" in major.lower() or "analytics" in major.lower():
                enhanced_query += f" Data Science Analytics Business Analytics Computer Information Systems GCIS GMBA"
            elif "business" in major.lower():
                enhanced_query += f" Business Administration MBA {major}"
            elif "computer" in major.lower():
                enhanced_query += f" Computer Information Systems GCIS {major}"
            else:
                enhanced_query += f" {major}"
        
        # Add level context
        if level:
            enhanced_query += f" {level}"
            
        # Add course-specific terms
        enhanced_query += " course curriculum requirements prerequisites"
        
        return enhanced_query
    
    return query

def _is_course_related_query(query: str) -> bool:
    """
    Determine if a query is related to courses
    """
    query_lower = query.lower()
    course_keywords = [
        "course", "courses", "class", "classes", "curriculum", "schedule",
        "what should i take", "what courses", "which courses", "course recommendations",
        "major requirements", "degree requirements", "prerequisites", "graduation requirements"
    ]
    
    return any(keyword in query_lower for keyword in course_keywords)

# Original function for backwards compatibility
def ask_llm(user_input: str, context: str, history: List[Dict]) -> Dict[str, Any]:
    """Original ask_llm function for backwards compatibility"""
    return ask_llm_enhanced(user_input, context, history, "unknown")
