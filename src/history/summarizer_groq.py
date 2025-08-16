# summarizer_groq.py
import os
from groq import Groq
import dotenv

dotenv.load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def summarizer_fn(text: str) -> str:
    """
    Gọi Groq để tóm tắt. Trả về đoạn tóm tắt ngắn (1-2 câu).
    """
    if not text:
        return ""
    try:
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a financial conversation summary bot. Keep the summary short (2-3 sentences) keeping only core information, financial metrics and main topics."},
                {"role": "user", "content": f"Briefly summarize the following conversation:\n\n{text}"}
            ],
            temperature=0.0,
            max_tokens=200
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"[summarizer_groq] error: {e}")
        return ""
