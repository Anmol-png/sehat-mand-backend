"""
============================================================
  SEHAT MAND PAKISTAN — intent_detector.py
============================================================
"""

# ── Greetings ─────────────────────────────────────────────
CHAT_KEYWORDS = [
    "hi", "hello", "hey", "salam", "assalam", "aoa",
    "kaise ho", "kya haal", "how are you", "good morning",
    "good evening", "good night", "subha bakhair", "shab bakhair",
    "theek ho", "kaisa chal raha", "what's up", "wassup",
    "thanks", "shukriya", "thank you", "jazakallah",
    "bye", "goodbye", "khuda hafiz", "allah hafiz",
]

# ── Emotions ──────────────────────────────────────────────
EMOTION_MAP = {
    "sad"      : ["sad", "udaas", "dil dukhi", "rona", "ro raha", "akela", "alone", "lonely"],
    "stressed" : ["stressed", "tension", "pareshan", "takleef", "mushkil", "stress", "pressure", "overwhelmed"],
    "anxious"  : ["anxious", "ghabra", "darr", "fear", "anxiety", "panic", "bechain", "restless"],
    "tired"    : ["tired", "thaka", "thakawat", "exhausted", "neend", "so nahi", "weakness", "kamzor"],
    "angry"    : ["gussa", "angry", "anger", "frustrat", "irritat"],
    "worried"  : ["worried", "fikr", "chinta", "tension hai", "dar lag raha"],
}

# ── Doctor request triggers ───────────────────────────────
DOCTOR_REQUEST_PHRASES = [
    # Urdu / Roman Urdu
    "doctor chahiye", "doctor batao", "doctor suggest", "doctor recommend",
    "doctor kon", "kaunsa doctor", "kaun sa doctor", "doctor dikhao",
    "mujhe doctor", "doctor ka number", "doctor ki zaroorat",
    "specialist chahiye", "specialist batao", "specialist suggest",
    "specialist recommend", "koi specialist", "koi doctor",
    "doctor kahan", "kahan jayein", "kahan dikhayein",
    "doctor bata", "doctor lena", "doctor milao",
    # English
    "suggest doctor", "suggest a doctor", "suggest specialist",
    "recommend doctor", "recommend a doctor", "recommend specialist",
    "which doctor", "which specialist", "find doctor", "find specialist",
    "need a doctor", "need doctor", "need specialist",
    "show doctor", "show specialist", "get doctor",
    "please suggest", "can you suggest", "can you recommend",
    "who should i see", "which hospital",
]

# ── Specialization keywords ───────────────────────────────
SPECIALIST_KEYWORDS = {
    "cardiologist": [
        "heart", "dil", "chest pain", "seene mein dard", "blood pressure",
        "bp", "cardiac", "dil ki dhadkan", "heartbeat", "palpitation",
        "cardiologist", "heart specialist", "heart doctor",
        "heart problem", "dil ka doctor", "dil ka masla",
    ],
    "gynecologist": [
        "gynecologist", "gynae", "pregnancy", "hamal", "periods", "menses",
        "mahwari", "ladies doctor", "delivery", "baby", "baccha plan",
        "female doctor", "aurat ka doctor",
    ],
    "pediatrician": [
        "child", "bachay", "bacha", "kids doctor", "children",
        "child specialist", "pediatrician", "paeds", "bachon ka doctor",
        "baby doctor", "newborn",
    ],
    "neurologist": [
        "neurologist", "neuro", "migraine", "brain", "dimagh",
        "seizure", "fits", "headache", "sir dard", "chakkar",
        "brain doctor", "dimagh ka doctor",
    ],
    "dermatologist": [
        "skin", "jild", "rash", "eczema", "acne", "pimple",
        "dermatologist", "kharish", "khujli", "daag", "dhabbe",
        "skin doctor", "skin specialist",
    ],
    "orthopedic": [
        "bone", "haddi", "joint", "joron", "knee", "ghutna",
        "back pain", "kamar dard", "orthopedic", "fracture", "sprain",
        "bone doctor", "haddi ka doctor", "joint pain",
    ],
    "diabetologist": [
        "diabetes", "sugar", "diabetologist", "blood sugar", "insulin",
        "sugar ka mareez", "sugar level", "diabetes doctor",
    ],
    "gastroenterologist": [
        "stomach", "pait", "gastro", "ulcer", "liver", "jigar",
        "acidity", "constipation", "qabz", "diarrhea", "dast",
        "vomiting", "ultai", "gas", "bloating", "pet ka doctor",
    ],
    "ent specialist": [
        "ear", "kaan", "nose", "naak", "throat", "gala", "ent",
        "tonsil", "hearing", "sunai nahi", "zukam", "naak band",
        "ear doctor", "nose doctor", "throat doctor",
    ],
    "psychiatrist": [
        "mental", "anxiety", "depression", "stress", "psychiatric",
        "psychiatrist", "neend nahi", "nind nahi ati", "mood",
        "psychological", "mental health", "mental doctor",
    ],
    "urologist": [
        "kidney", "gurda", "urine", "peshab", "urologist", "bladder",
        "stone", "pathri", "kidney doctor",
    ],
    "ophthalmologist": [
        "eye", "ankh", "vision", "sight", "specs", "glasses",
        "ophthalmologist", "nazar", "aankhain", "eye doctor",
    ],
    "dentist": [
        "teeth", "daant", "gums", "maseray", "dentist", "tooth",
        "dant dard", "tooth pain", "teeth doctor",
    ],
    "general practitioner (gp)": [
        "fever", "bukhar", "flu", "cold", "zukam", "cough", "khansi",
        "general", "gp", "normal doctor", "family doctor",
    ],
}


def detect_intent(message: str) -> dict:
    msg = message.lower().strip()

    # 1. General chat
    if any(kw in msg for kw in CHAT_KEYWORDS):
        if len(msg.split()) <= 6:
            return {"type": "general_chat", "specialization": None, "emotion": None}

    # 2. Emotion check
    detected_emotion = None
    for emotion, keywords in EMOTION_MAP.items():
        if any(kw in msg for kw in keywords):
            detected_emotion = emotion
            break

    # 3. Doctor/specialist request check
    wants_doctor = any(phrase in msg for phrase in DOCTOR_REQUEST_PHRASES)
    matched_spec = None
    for spec, keywords in SPECIALIST_KEYWORDS.items():
        if any(kw in msg for kw in keywords):
            matched_spec = spec
            break

    # If they mention specialist keyword even without explicit "suggest" phrase
    # e.g. "heart specialist" or "skin doctor" → treat as specialist request
    if matched_spec and any(
        trigger in msg for trigger in [
            "specialist", "doctor", "physician", "expert",
            "daktar", "hakim", "suggest", "recommend", "chahiye", "batao"
        ]
    ):
        wants_doctor = True

    if wants_doctor and matched_spec:
        return {"type": "specialist", "specialization": matched_spec, "emotion": None}

    if wants_doctor and not matched_spec:
        return {"type": "specialist", "specialization": "general practitioner (gp)", "emotion": None}

    # 4. Emotional
    if detected_emotion:
        return {"type": "emotional", "specialization": matched_spec, "emotion": detected_emotion}

    # 5. Default
    return {"type": "general", "specialization": matched_spec, "emotion": None}


# ── Clinical specialty detection (doctor mode) ────────────
CLINICAL_SPECIALTY_MAP = {
    "cardiologist"       : ["chest pain", "heart attack", "cardiac", "palpitation", "angina",
                            "myocardial", "ecg", "troponin", "arrhythmia", "heart failure",
                            "hypertension", "blood pressure"],
    "neurologist"        : ["stiff neck", "photophobia", "meningitis", "seizure", "convulsion",
                            "stroke", "paralysis", "facial droop", "migraine", "altered consciousness",
                            "gcs", "neuro", "brain", "spinal"],
    "gastroenterologist" : ["abdominal pain", "stomach pain", "vomiting blood", "haematemesis",
                            "liver", "hepatitis", "jaundice", "ascites", "diarrhea",
                            "gi bleed", "peptic ulcer", "pancreatitis", "appendicitis"],
    "pediatrician"       : ["child", "infant", "neonate", "baby", "pediatric", "newborn", "toddler"],
    "gynecologist"       : ["pregnant", "pregnancy", "obstetric", "gynae", "uterus", "ovarian",
                            "menstrual", "ectopic", "preeclampsia", "eclampsia", "labour", "delivery"],
    "orthopedic"         : ["fracture", "bone", "joint", "dislocation", "sprain", "ligament",
                            "tendon", "spine", "vertebra", "trauma"],
    "pulmonologist"      : ["pneumonia", "tuberculosis", "tb", "respiratory", "lung", "copd",
                            "asthma", "pleural", "effusion", "bronchitis", "spo2", "dyspnea"],
    "urologist"          : ["kidney stone", "renal", "urinary", "urine", "bladder", "prostate",
                            "uti", "creatinine high"],
    "psychiatrist"       : ["psychiatric", "psychosis", "schizophrenia", "bipolar", "suicidal",
                            "hallucination", "delusion", "anxiety disorder"],
    "diabetologist"      : ["diabetes", "diabetic", "hyperglycemia", "hypoglycemia", "hba1c",
                            "insulin", "blood sugar", "dka", "diabetic ketoacidosis"],
    "ophthalmologist"    : ["eye", "vision loss", "retinal", "glaucoma", "cataract", "conjunctivitis"],
    "dermatologist"      : ["skin rash", "dermatitis", "eczema", "psoriasis", "cellulitis", "abscess"],
    "ent specialist"     : ["ear", "nose", "throat", "ent", "tonsil", "sinusitis", "epistaxis",
                            "hearing loss"],
}


def detect_clinical_specialty(message: str) -> str | None:
    msg        = message.lower().strip()
    best_match = None
    best_count = 0
    for specialty, keywords in CLINICAL_SPECIALTY_MAP.items():
        count = sum(1 for kw in keywords if kw in msg)
        if count > best_count:
            best_count = count
            best_match = specialty
    return best_match if best_count >= 1 else None