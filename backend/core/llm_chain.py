import os
import requests
import sys
import json
from dotenv import load_dotenv
from features.intelligence.context_manager import ConversationContextManager

sys.modules['torch.classes'] = type(sys)('torch.classes')

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"))

# Lazy load context manager
context_manager = None

API_URL = os.getenv("GROQ_API_URL")
API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def ask_llm(user_input, context, history):
    """
    Original LLM function - maintained for backward compatibility
    """
    return ask_llm_enhanced(user_input, context, history, user_email="unknown")

def ask_llm_enhanced(user_input, context, history, user_email="unknown"):
    """
    Enhanced LLM call with comprehensive context management and conversation awareness
    """
    # Quick greeting detection for optimized response
    import re
    is_greeting = bool(re.match(r'^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|how\s+are\s+you)\s*\??$', 
                               user_input.lower().strip()))
    
    if is_greeting:
        # Provide natural, capability-focused greeting responses
        greeting_responses = [
            "Hey! I can help you with course info, prerequisites, degree requirements, university policies, and academic planning. What's on your mind?",
            "Hi! I'm here to help with anything academic - courses, requirements, planning your schedule, university policies, you name it. What do you need?",
            "Hello! Need help with course information, degree planning, prerequisites, or university policies? I'm here for all your academic questions.",
            "Hi there! I can assist with course details, academic requirements, planning guidance, and university procedures. What can I help you figure out?"
        ]
        
        # Natural continuation if there's conversation history
        if history and len(history) > 0:
            greeting = "What else can I help you with? I'm here for course info, requirements, planning - whatever you need."
        else:
            import random
            greeting = random.choice(greeting_responses)
        
        return {
            "answer": greeting,
            "confidence": 5,
            "suggested_questions": [
                "What CS courses are available?",
                "What are the prerequisites for [specific course]?",
                "How do I plan my schedule for next semester?"
            ],
            "context_references": []
        }
    
    # Lazy load context manager when needed
    global context_manager
    if context_manager is None:
        from features.intelligence.context_manager import ConversationContextManager
        context_manager = ConversationContextManager()
    
    # Build enhanced conversation context for non-greeting queries
    conversation_context = context_manager.build_enhanced_context(history, user_email, user_input)
    
    # Format context for LLM consumption
    formatted_context = context_manager.format_context_for_llm(conversation_context)
    
    # Warm, supportive academic advisor prompt
    system_prompt = f"""You are a knowledgeable and friendly academic advisor who genuinely cares about student success. Give accurate, helpful answers using ONLY the provided information.

Context: {formatted_context}

ADVISOR PERSONALITY:
- Be warm and approachable while staying professional
- Show genuine interest in helping students succeed
- Use encouraging language when appropriate
- Be supportive without being overly casual

ACCURACY RULES:
- ONLY use information from the provided context
- If asked for course names, provide the EXACT course codes and titles from the context
- NEVER mix course codes from different programs (GCIS vs GMBA vs other prefixes)
- If the context contains multiple programs, focus on the most relevant one for the student
- If explaining academic concepts, acknowledge if you lack detailed explanations: "I have course information but not detailed concept explanations"
- If information is not in the context, say "I don't have that information, but I'd recommend..."
- Never make up course names or numbers
- Keep responses concise but friendly (1-3 sentences)

SUPPORTIVE RESPONSES:
- If student seems stressed/overwhelmed: Acknowledge their feelings and offer encouragement
- If asking about difficult requirements: Frame positively and suggest resources
- If exploring options: Show enthusiasm for their academic journey
- If facing challenges: Provide helpful next steps and support options

Examples:
Q: "List data science courses with names"
A: "Great choice exploring Data Science! From the program: GCIS 516 - Data-Centric Concepts and Methods, GCIS 523 - Statistical Computing..."

Q: "I'm confused about prerequisites"
A: "I understand prerequisites can feel overwhelming! Let me help clarify..."

Q: "Can I handle the workload?"
A: "It's normal to wonder about workload - that shows you're being thoughtful about your planning!"

Q: "What is normalization?" (when asked for concept explanation)
A: "I have course information for GCIS 516 which covers normalization, but I don't have detailed concept explanations. I'd recommend checking your course materials or asking your professor for specific normalization concepts."

Q: "Explain database concepts" 
A: "I can help with course information and requirements, but for detailed academic concepts, you'll want to refer to your textbooks, lecture notes, or office hours with your professor."

NEVER invent course names. ONLY use what's explicitly provided.

You must respond in valid JSON format with these keys:
- "answer": Your natural, conversational response (like ChatGPT would answer)
- "confidence": Integer from 1-5 based on how well you can answer
- "suggested_questions": List of relevant follow-up questions
- "context_references": List of previous topics you referenced (if any)
"""

    # Build enhanced message history with better context formatting
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add only recent conversation history (simplified)
    for turn in history[-4:]:  # Last 2 exchanges only
        role = "user" if turn["sender"].lower() == "user" else "assistant"
        messages.append({"role": role, "content": turn["text"]})
    
    # Add current query with clear context formatting
    current_query = f"""RETRIEVED INFORMATION:
{context}

STUDENT QUESTION: {user_input}

INSTRUCTIONS: Answer using ONLY the information above. If course names are requested, look for patterns like "GCIS XXX - Course Title" or "GCIS XXX Course Title" in the retrieved information and provide those exact matches. 

CRITICAL: If the context contains multiple course prefixes (GCIS, GMBA, etc.), focus on the most relevant program for the student's context. If student mentioned GCIS courses before, prioritize GCIS information over GMBA. Do not mix course codes from different programs."""
    
    messages.append({"role": "user", "content": current_query})
    
    # Prepare API call
    body = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=body)
        response.raise_for_status()
        llm_output = json.loads(response.json()["choices"][0]["message"]["content"])
        
        # Add conversation intelligence metadata to response
        llm_output["conversation_intelligence"] = {
            "context_used": True,
            "conversation_state": conversation_context["conversation_state"],
            "continuity_maintained": conversation_context["context_continuity"]["has_continuity"],
            "entities_referenced": conversation_context["mentioned_entities"],
            "conversation_insights": context_manager.get_conversation_insights(conversation_context)
        }
        
        return llm_output
        
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"Enhanced LLM Chain Error: {e}")
        return {
            "answer": "I'm sorry, I encountered an issue while processing your request. Please try again.",
            "confidence": 0,
            "suggested_questions": [],
            "context_references": [],
            "conversation_intelligence": {
                "context_used": False,
                "error": str(e)
            }
        }