"""
============================================================
  intent_detector.py
  Detects what the user is asking:
  - "general"    → user has symptoms, wants advice
  - "specialist" → user wants a specific type of doctor
============================================================
"""

# ── Keyword map: Roman Urdu + English → specialization ──
SPECIALIST_KEYWORDS = {
    "cardiologist"   : ["heart", "dil", "chest pain", "seene mein dard", "blood pressure", "bp", "cardiac"],
    "gynecologist"   : ["gynecologist", "gynae", "pregnancy", "hamal", "periods", "menses", "mahwari", "ladies doctor"],
    "pediatrician"   : ["child", "bachay", "bacha", "kids doctor", "children", "child specialist", "pediatrician", "paeds"],
    "neurologist"    : ["neurologist", "neuro", "migraine", "brain", "dimagh", "seizure", "fits", "headache", "sir dard"],
    "dermatologist"  : ["skin", "jild", "rash", "eczema", "acne", "pimple", "dermatologist"],
    "orthopedic"     : ["bone", "haddi", "joint", "joron", "knee", "ghutna", "back pain", "kamar dard", "orthopedic"],
    "diabetologist"  : ["diabetes", "sugar", "diabetologist", "blood sugar", "insulin"],
    "gastroenterologist": ["stomach", "pait", "gastro", "ulcer", "liver", "jigar", "acidity", "constipation", "qabz"],
    "ent specialist" : ["ear", "kaan", "nose", "naak", "throat", "gala", "ent", "tonsil", "hearing"],
    "psychiatrist"   : ["mental", "anxiety", "depression", "stress", "psychiatric", "psychiatrist", "neend nahi"],
    "urologist"      : ["kidney", "gurda", "urine", "peshab", "urologist", "bladder"],
    "ophthalmologist": ["eye", "ankh", "vision", "sight", "specs", "glasses", "ophthalmologist"],
    "dentist"        : ["teeth", "daant", "gums", "maseray", "dentist", "tooth"],
    "general practitioner (gp)": ["fever", "bukhar", "flu", "cold", "zukam", "cough", "khansi", "general", "gp"],
}

# ── Phrases that signal user wants a doctor ──────────────
DOCTOR_REQUEST_PHRASES = [
    "kaun sa doctor", "which doctor", "doctor chahiye", "doctor batao",
    "kahan jayein", "specialist", "doctor suggest", "doctor recommend",
    "doctor kon", "kaunsa doctor", "doctor dikhao", "mujhe doctor"
]


def detect_intent(message: str) -> dict:
    """
    Returns dict with:
    - type         : 'general' or 'specialist'
    - specialization: matched specialization string (if specialist)
    """
    msg_lower = message.lower().strip()

    # ── Check if user is asking for a doctor ─────
    wants_doctor = any(phrase in msg_lower for phrase in DOCTOR_REQUEST_PHRASES)

    # ── Match specialization from keywords ───────
    matched_specialization = None
    for specialization, keywords in SPECIALIST_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            matched_specialization = specialization
            break

    # ── Decide intent ─────────────────────────────
    if wants_doctor and matched_specialization:
        return {"type": "specialist", "specialization": matched_specialization}

    elif wants_doctor and not matched_specialization:
        # User asked for a doctor but we couldn't match specialty
        # Default to general practitioner
        return {"type": "specialist", "specialization": "general practitioner (gp)"}

    else:
        # User is describing symptoms → general advice
        return {"type": "general", "specialization": matched_specialization}