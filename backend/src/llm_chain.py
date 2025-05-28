# src/llm_chain.py
import os
import requests
import sys
import torch
from dotenv import load_dotenv

sys.modules['torch.classes'] = type(sys)('torch.classes')

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../configs/.env"))

API_URL = os.getenv("GROQ_API_URL")
API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def ask_llm(user_input, context):
    messages = [
        {"role": "system", "content": """You are a helpful academic advisor assistant. 
        
VERY IMPORTANT: Your responses must be based ONLY on the information provided in the context below. 
- If the context doesn't contain sufficient information to answer the question, explicitly state: "I don't have enough information to answer this question accurately based on the available data."
- DO NOT make up or infer information that isn't present in the context.
- When answering, cite specific parts of the context by stating "According to the provided information..."
- Be precise and accurate. It's better to acknowledge limitations than to provide potentially incorrect information.
- When quoting directly from the context, use quotation marks.
        
You should be supportive, informative, and concise while strictly adhering to the information in the context."""},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_input}"}
    ]
    
    body = {
        "model": MODEL_NAME,
        "messages": messages
    }
    
    response = requests.post(API_URL, headers=HEADERS, json=body)

    if response.status_code != 200:
        raise Exception(f"Groq API Error: {response.status_code}\n{response.text}")

    return response.json()["choices"][0]["message"]["content"]

# New function that adds confidence assessment
def ask_llm_with_confidence(user_input, context):
    # Regular LLM call
    answer = ask_llm(user_input, context)
    
    # Confidence check prompt
    confidence_prompt = f"""
    Context: {context}
    
    Question: {user_input}
    
    Answer you provided: {answer}
    
    On a scale of 1-5, rate your confidence in this answer based ONLY on the provided context:
    1: No relevant information in context
    2: Some related information but not specific enough
    3: Partial information available
    4: Most information available
    5: Complete information available
    
    Return ONLY the number.
    """
    
    confidence_messages = [
        {"role": "system", "content": "You objectively evaluate the confidence of answers based on available context."},
        {"role": "user", "content": confidence_prompt}
    ]
    
    # Get confidence score
    confidence_response = requests.post(API_URL, headers=HEADERS, json={
        "model": MODEL_NAME,
        "messages": confidence_messages
    })
    
    if confidence_response.status_code != 200:
        return answer, 0
    
    try:
        confidence = int(confidence_response.json()["choices"][0]["message"]["content"].strip())
    except:
        confidence = 0
        
    return answer, confidence