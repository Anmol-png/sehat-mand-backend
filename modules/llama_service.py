"""
============================================================
  SEHAT MAND PAKISTAN — llama_service.py
  + Improved Roman Urdu quality in prompts
============================================================
"""

import os
import requests
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = "llama-3.1-8b-instant"
OLLAMA_URL   = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


# ═══════════════════════════════════════════════
# USER SYSTEM PROMPT — Improved Roman Urdu
# ═══════════════════════════════════════════════
USER_SYSTEM = """You are a responsible SehatMand  AI assistant for Karachi users.

LANGUAGE RULES:
- If user writes in Roman Urdu → reply in natural Pakistani Roman Urdu.
- If user writes in English → reply in English.
- If user says Salam/Hi/Hello → respond with greeting and 1–2 lines about your health assistant app.

TONE:
- Sound like a helpful, caring friend.
- Do not sound robotic or textbook-style.
- Avoid unnecessary talk (gher zaroori baat na karein).


- If user asks for doctor recommendation → provide doctor info only.
- If user asks about medicine → respond:
  "Medication ke liye Doctor AI Panel use karein ya doctor se consult karein."
  Do NOT suggest medicine names, brands, or dosage.

RESPONSE STRUCTURE RULES:

If giving suggestions:
Heading:
Suggestions:
- Relevant advice based on symptoms (dynamic, not hard-coded)
- Practical and meaningful tips only

If giving doctor list:
Heading:
Doctor Information:
1. Name – Hospital – Phone
   (1–2 lines why relevant specialist)

If asking follow-up:
Heading:
Follow-up Question:
(Short question only, no advice)

STRICT MEDICAL SAFETY RULES:
- Never diagnose disease by name.
- Never suggest medicine brands.
- Never give dosage.
- Only general mild medicine class if absolutely necessary (no dose).
- Do not suggest emergency hospital directly.
- Keep response under 150 words.

Always end with:
"Agar tabiyat zyada kharab ho rahi ho ya symptoms barh rahe hon to doctor se consult karein."""


# ═══════════════════════════════════════════════
# DOCTOR SYSTEM PROMPT
# ═══════════════════════════════════════════════
DOCTOR_SYSTEM = """You are a medical AI assistant for Pakistani doctors.

LANGUAGE RULES:
- Respond in professional English or Roman Urdu based on user message.
- Use Roman Urdu for short patient instructions if needed.

PERCEPTION LEVELS:
- Mild: simple advice (rest, hydration, lifestyle), may include mild medicine class if relevant — no brands, no dose
- Medium: follow-up needed, dietary adjustment, monitoring, may include mild medicine class if relevant
- High: urgent evaluation recommended
  - High risk if user mentions heart attack, chest pain, severe pain
  - High risk if heart or kidney related symptoms > 2 days

RESPONSE FORMAT:
Risk Perception: Mild / Medium / High

Management Plan:
- Lifestyle / dietary advice
- Mild medication class only if relevant — no brands, no dosage

Referral:
- Mention specialist type if needed
- If emergency → ⚠️ URGENT + Call 1122 Karachi

RULES:
- Do NOT confirm diagnosis
- Do NOT list doctor names directly to the user
- If user asks for doctor suggestion, respond:
  "Doctor consultation ke liye please user AI panel me jaaen."
- Keep reply concise and clear — under 150 words
"""


def _call_groq(system: str, messages: list):
    if not groq_client:
        return None
    try:
        full_messages = [{"role": "system", "content": system}] + messages
        response = groq_client.chat.completions.create(
            model       = GROQ_MODEL,
            messages    = full_messages,
            temperature = 0.5,
            max_tokens  = 350,
        )
        print("[AI] ✅ Groq responded")
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Groq] ❌ {e}")
        return None


def _call_ollama(system: str, messages: list):
    try:
        history_text = ""
        for m in messages[:-1]:
            role = "User" if m["role"] == "user" else "Assistant"
            history_text += f"{role}: {m['content']}\n"
        last_msg = messages[-1]["content"] if messages else ""

        payload = {
            "model"  : OLLAMA_MODEL,
            "system" : system,
            "prompt" : f"{history_text}User: {last_msg}",
            "stream" : False,
            "options": {"temperature": 0.5, "num_predict": 300, "num_ctx": 2048},
        }
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        if r.status_code == 200:
            print("[AI] ✅ Ollama responded")
            return r.json().get("response", "").strip()
        return None
    except requests.exceptions.ConnectionError:
        print("[Ollama] ❌ Not running")
        return None
    except Exception as e:
        print(f"[Ollama] ❌ {e}")
        return None


def _call_ai(system: str, messages: list):
    result = _call_groq(system, messages)
    if result:
        return result
    print("[Fallback] 🔄 Switching to Ollama...")
    return _call_ollama(system, messages)


def ask_user_mode(message: str, history: list = None, doctor_context: str = "") -> str:
    history = history or []

    current_content = message
    if doctor_context:
        current_content += f"\n\n[Doctor List]\n{doctor_context}\nPresent this list clearly to the user."

    messages = history + [{"role": "user", "content": current_content}]

    result = _call_ai(USER_SYSTEM, messages)
    if result:
        return result
    return "Service abhi available nahi. Aaram karen, pani piyen, aur doctor se milen agar theek nahi hua."


def ask_doctor_mode(message: str, history: list = None, doctor_context: str = "") -> str:
    history = history or []

    current_content = message
    if doctor_context:
        current_content += f"\n\n[Referral Doctors in Karachi]\n{doctor_context}"

    messages = history + [{"role": "user", "content": current_content}]

    result = _call_ai(DOCTOR_SYSTEM, messages)
    if result:
        return result
    return "Clinical AI unavailable. Assess vitals immediately. Emergency: Call 1122 Karachi."