import os
import requests
from dotenv import load_dotenv

import sys
import torch

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
        {"role": "system", "content": "You are a helpful academic advisor assistant. Your job is to provide clear, accurate, and student-friendly advice on academic planning, course selection, degree requirements, study tips, and related university policies. Always be supportive, informative, and concise. When answering, consider the student's background, goals, and any specific constraints they mention. If more information is needed, ask thoughtful follow-up questions to better assist them."},
        {"role": "user", "content": f"Context: {context}\n\nQuestion: {user_input}"}
    ]
    body = {
        "model": MODEL_NAME,
        "messages": messages
    }
    response = requests.post(API_URL, headers=HEADERS, json=body)

    if response.status_code != 200:
        raise Exception(f"Groq API Error: {response.status_code}\n{response.text}")

    return response.json()["choices"][0]["message"]["content"]
