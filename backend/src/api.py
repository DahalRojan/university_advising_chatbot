# src/api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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

class ChatQuery(BaseModel):
    query: str

@app.post("/chat")
def chat(query: ChatQuery):
    context_docs = retrieve_similar_docs(query.query)
    answer = ask_llm(query.query, "\n".join(context_docs))
    return {"answer": answer}
