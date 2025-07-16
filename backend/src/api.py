from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

from src.retriever import retrieve_similar_docs
from src.llm_chain import ask_llm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for providing reliable resource referrals for common keywords
RESOURCE_REFERRALS = {
    "career": "It sounds like you're thinking about career paths. I highly recommend connecting with Career Services. They can help with resume building, internship searches, and mock interviews.",
    "internship": "For questions about internships, Career Services is the best place to start. They have listings and can help you prepare your application.",
    "tutoring": "If you're looking for academic support, the Tutoring Center offers free help for many introductory courses. I suggest booking an appointment with them early.",
    "stress": "Managing stress is a critical part of university life. The university's Counseling and Psychological Services (CAPS) offers confidential support for students. Please don't hesitate to reach out to them.",
    "anxiety": "Feeling anxious is very common. The university's Counseling and Psychological Services (CAPS) offers confidential support. Please don't hesitate to reach out to them.",
    "financial aid": "For specific questions about loans, grants, or scholarships, the Financial Aid office is the best resource. They can provide details about your specific situation."
}

class ChatQuery(BaseModel):
    query: str
    history: List[Dict[str, Any]] = []

@app.post("/chat")
def chat(query: ChatQuery):
    """
    Handles user queries by checking for greetings, keywords, and then using the RAG pipeline
    with a confidence check for a professional and reliable response.
    """
    user_query_lower = query.query.lower().strip()

    # 1. Handle simple greetings
    GREETINGS = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
    if user_query_lower in GREETINGS:
        return {
            "answer": "Hello! I'm your academic advisor assistant. How can I help you with questions about courses, policies, or university information today?",
            "suggested_questions": [
                "What are the computer science degree requirements?",
                "What is the add/drop deadline for this semester?",
                "Tell me about the academic integrity policy."
            ]
        }

    # 2. Check for resource keywords to provide helpful, direct referrals
    for keyword, referral_text in RESOURCE_REFERRALS.items():
        if keyword in user_query_lower:
            query.query += f"\n\nSystem Note: The user's query mentions '{keyword}'. Please incorporate this helpful referral into your answer: '{referral_text}'"
            break

    # 3. Proceed with the standard RAG pipeline
    context_docs = retrieve_similar_docs(query.query)
    
    if len(context_docs) == 1 and context_docs[0].startswith("I don't have specific information"):
        return {"answer": context_docs[0], "suggested_questions": []}

    context = "\n\n---\n\n".join(context_docs)
    llm_response = ask_llm(query.query, context, query.history)
    confidence = llm_response.get("confidence", 0)

    # 4. CRITICAL: Use confidence score to prevent hallucination and build trust
    if confidence < 3:
        # If the LLM is not confident, do not show its answer.
        # Instead, provide a safe, helpful response.
        clarifying_answer = (
            "I found some information that might be related, but I'm not confident enough to provide a direct answer. "
            "To help me find the right details, could you please make your question more specific? "
            "For example, instead of 'tell me about policies,' you could ask, 'what is the policy on academic dishonesty?'"
        )
        return {
            "answer": clarifying_answer,
            "suggested_questions": llm_response.get("suggested_questions", [])
        }

    # 5. If confidence is high, return the LLM's generated answer
    return {
        "answer": llm_response.get("answer"),
        "suggested_questions": llm_response.get("suggested_questions", [])
    }