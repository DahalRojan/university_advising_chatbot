import os
import requests
from typing import List, Dict

def generate_conversation_summary(messages: List[Dict[str, str]]) -> str:
    """
    Generate a concise summary of a conversation using the LLM
    
    Args:
        messages: List of message dictionaries with 'sender' and 'text' keys
    
    Returns:
        A concise summary string
    """
    if not messages:
        return "Empty conversation"
    
    # Format conversation for summarization
    conversation_text = ""
    for msg in messages[-10:]:  # Use last 10 messages to avoid token limits
        role = "Student" if msg['sender'] == 'user' else "Advisor"
        conversation_text += f"{role}: {msg['text']}\n"
    
    # Create summarization prompt  
    prompt = f"""Please create a very brief summary (4-6 words) of this university advising conversation. Focus on the main topic or question being discussed.

Conversation:
{conversation_text}

Summary (4-6 words):"""

    try:
        # Use the same LLM configuration as the main chat
        api_url = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        
        if not api_key:
            return "Conversation about university advising"
            
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 20,
            "temperature": 0.3
        }
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            summary = result["choices"][0]["message"]["content"].strip()
            
            # Clean up the summary - remove quotes and extra text
            summary = summary.replace('"', '').replace("'", "")
            if summary.lower().startswith("summary:"):
                summary = summary[8:].strip()
            
            # Limit length and ensure it's reasonable
            if len(summary) > 50:
                summary = summary[:47] + "..."
            
            return summary or "University advising chat"
        else:
            print(f"Summarization API error: {response.status_code}")
            return "University advising chat"
            
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "University advising chat"

def get_fallback_summary(messages: List[Dict[str, str]]) -> str:
    """
    Generate a simple fallback summary based on keywords in the conversation
    """
    if not messages:
        return "Empty conversation"
    
    # Get the first user message (skip greetings)
    user_messages = [msg['text'].lower() for msg in messages if msg['sender'] == 'user']
    
    for msg in user_messages:
        if len(msg) < 5 or any(greeting in msg for greeting in ['hi', 'hello', 'hey']):
            continue
            
        # Extract key topics
        if 'course' in msg or 'class' in msg:
            return "Course inquiry"
        elif 'major' in msg or 'degree' in msg:
            return "Major/degree questions"
        elif 'schedule' in msg or 'time' in msg:
            return "Schedule planning"
        elif 'requirement' in msg:
            return "Requirements discussion"
        elif 'graduate' in msg or 'graduation' in msg:
            return "Graduation planning"
        elif 'transfer' in msg:
            return "Transfer questions"
        else:
            # Use first few words of the first substantial message
            words = msg.split()[:4]
            return " ".join(words).title()
    
    return "University advising chat"