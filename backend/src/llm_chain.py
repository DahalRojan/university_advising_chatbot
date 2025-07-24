import os
import requests
import sys
import json
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

def ask_llm(user_input, context, history):
    """
    Constructs a prompt and sends it to the LLM, requesting a structured JSON response
    that aligns with the persona of an interactive and professional University Advisor.
    """
    system_prompt = """You are an expert University Advisor. Your tone must be empathetic, supportive, and non-judgmental. Your goal is to empower students by guiding them to the information they need.

**CRITICAL INSTRUCTIONS:**
1.  **Be an Interactive Guide, Not a Directory:** Your primary goal is to answer questions using the provided context. Do not simply refer students to another person or office unless the context explicitly says to do so for a very specific query (e.g., "Contact Person for X is Y").
2.  **Handle Broad Questions by Asking Clarifying Questions:** If the user's question is broad (e.g., "tell me about graduate programs") and the context provides a general overview, your main response should be to ask clarifying questions to help the user narrow down their interest. Suggest options based on the context.
    - **Example Interaction:**
      - User: "Tell me about graduate programs."
      - Your Response: "Of course! The university offers a variety of graduate programs, including Doctoral, Master's, and Certificate programs. To give you the best information, could you tell me what field you're interested in, such as Engineering, Business, or Health Sciences?"
3.  **Use Only Provided Context:** Base your answers strictly on the information provided in the context below. If you truly cannot find any relevant information for a specific, detailed question, then you can state that you don't have those details.

You must respond in a valid JSON format with the following keys:
- "answer": Your supportive and informative response.
- "confidence": An integer from 1 to 5.
- "suggested_questions": A list of strings.
"""
    messages = [{"role": "system", "content": system_prompt}]

    for turn in history:
        if turn["sender"].lower() == "user":
            messages.append({"role": "user", "content": turn["text"]})
        else:
            messages.append({"role": "assistant", "content": turn["text"]})

    messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_input}"})

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
        return llm_output
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"LLM Chain Error: {e}")
        return {
            "answer": "I'm sorry, I encountered an issue while processing your request. Please try again.",
            "confidence": 0,
            "suggested_questions": []
        }