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
USER_SYSTEM = """You are a responsible tele-health AI assistant for Pakistani users.

LANGUAGE RULES:
- User writes Roman Urdu → reply in natural Pakistani Roman Urdu.
- User writes English → reply in English.
- Sound like a helpful friend, not a textbook.

CONVERSATION RULES:
- First reply: ask ONE short follow-up question if needed.
- After user replies → STOP asking. Give advice immediately.
- If user says "nahi", "sirf yahi", "bas yahi", "kuch nahi" → give advice NOW.
- NEVER ask more than 1 question total in the whole conversation.

RESPONSE FORMAT (always follow this):
Symptoms ke liye:
- Zyada pani piyein
- Rest karein
- Halki diet follow karein
(add more relevant tips based on symptoms)

If doctor list is provided → present clearly:
1. Name – Hospital – Phone
(briefly explain why this specialist is relevant)

END every reply with:
"Agar tabiyat behtar na ho ya symptoms barh jaen to doctor se rabta karein."

STRICT RULES:
- NEVER diagnose disease by name.
- NEVER suggest medicine brands or dosages.
- Only mention mild/common medicine class if very relevant (no dose).
- NEVER suggest emergency hospital directly.
- Keep replies under 120 words."""


# ═══════════════════════════════════════════════
# DOCTOR SYSTEM PROMPT
# ═══════════════════════════════════════════════
DOCTOR_SYSTEM = """You are a medical AI assistant for Pakistani doctors.

Respond only in professional English.

PERCEPTION LEVELS:
- Mild: simple advice (rest, hydration, lifestyle)
- Medium: follow-up needed, dietary adjustment, monitoring
- High: urgent evaluation recommended

RESPONSE FORMAT:
Risk Perception: Mild / Medium / High

Clinical Impression:

Key Differentials:
-

Investigations (if needed):
-

Management Plan:
- (lifestyle/dietary advice)
- (mild medication class only if relevant — no brands, no dose)

Referral:
- Mention specialist type if needed
- If referral doctors provided → list them clearly
- If emergency → ⚠️ URGENT + Call 1122 Karachi

RULES:
- Do NOT confirm diagnosis.
- No brand names. No exact dosages.
- Keep short and clear — under 150 words."""


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