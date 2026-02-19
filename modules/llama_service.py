"""
============================================================
  llama_service.py
  Calls LLaMA 3 via Ollama local API
  Ollama runs at: http://localhost:11434
============================================================
"""

import requests
import json

OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL_NAME  = "llama3"

# ── Safe system prompt — rules LLaMA must follow ─────────
SYSTEM_PROMPT = """
You are a safe and helpful medical assistant for Pakistani users called "Sehat Mand Pakistan".
You respond in simple Roman Urdu or English depending on what the user writes.

STRICT RULES — you must ALWAYS follow these:
1. NEVER confirm or diagnose any disease
2. NEVER suggest specific medicine brand names (e.g. Panadol, Brufen)
3. NEVER give exact dosage or tablet count
4. NEVER write a prescription
5. ONLY give mild, general lifestyle advice for common symptoms
6. If user asks for a doctor, ONLY suggest Karachi-based doctors
7. Always recommend consulting a real doctor for serious issues
8. Keep responses short, clear, and easy to understand
9. If symptoms sound serious, always say "Please consult a doctor immediately"
10. Be empathetic and caring in tone

You are NOT a replacement for a real doctor. Always remind users to consult a qualified physician.
"""


def ask_llama(user_message: str, intent_type: str, context: str = "") -> str:
    """
    Sends message to LLaMA 3 via Ollama and returns the response text.

    Parameters:
    - user_message : original message from user
    - intent_type  : 'general' or 'specialist'
    - context      : doctor list from Firestore (if specialist)
    """

    # ── Build the full prompt ─────────────────────
    if intent_type == "specialist" and context:
        prompt = f"""
User ne yeh message bheja hai: "{user_message}"

{context}

In doctors mein se user ko suggest karein aur unhe batayein ke doctor se milna kyun zaroori hai.
Apna jawab Roman Urdu ya English mein dein jo user ne use ki ho.
"""
    else:
        prompt = f"""
User ne yeh symptoms bataye hain: "{user_message}"

Mild aur safe general advice dein. Koi diagnosis na karein, koi medicine brand na batayein.
Agar symptoms serious lagte hain to doctor se milne ki salah dein.
Apna jawab Roman Urdu ya English mein dein jo user ne use ki ho.
"""

    # ── Call Ollama API ───────────────────────────
    try:
        payload = {
            "model"  : MODEL_NAME,
            "prompt" : prompt,
            "system" : SYSTEM_PROMPT,
            "stream" : False,   # get full response at once
            "options": {
                "temperature": 0.5,    # lower = more focused, safer responses
                "num_predict": 300,    # max tokens in response
            }
        }

        response = requests.post(
            OLLAMA_URL,
            json    = payload,
            timeout = 60        # 60 second timeout
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", "Mujhe maafi chahiye, abhi jawab dene mein masla aa raha hai.")
        else:
            print(f"[Ollama Error] Status: {response.status_code}")
            return "Mujhe maafi chahiye, AI service abhi available nahi hai. Baad mein try karein."

    except requests.exceptions.ConnectionError:
        return "AI service se connection nahi ho pa raha. Please Ollama ko start karein aur dobara try karein."

    except requests.exceptions.Timeout:
        return "AI service ne time limit se zyada waqt liya. Baad mein try karein."

    except Exception as e:
        print(f"[LLaMA Error] {e}")
        return "Kuch masla aa gaya. Baad mein try karein."