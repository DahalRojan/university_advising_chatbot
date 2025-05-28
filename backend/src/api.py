# src/api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.retriever import retrieve_similar_docs
from src.llm_chain import ask_llm_with_confidence

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatQuery(BaseModel):
    query: str

@app.post("/chat")
def chat(query: ChatQuery):
    # Retrieve relevant documents
    context_docs = retrieve_similar_docs(query.query)
    
    # Check if we have any relevant docs
    if len(context_docs) == 1 and context_docs[0].startswith("I don't have specific information"):
        return {
            "answer": context_docs[0],
            "confidence": 1,
            "has_relevant_info": False
        }
    
    # Join documents with clear separators
    context = "\n\n---\n\n".join(context_docs)
    
    # Get answer with confidence score
    answer, confidence = ask_llm_with_confidence(query.query, context)
    
    return {
        "answer": answer,
        "confidence": confidence,
        "has_relevant_info": confidence >= 3
    }