"""
============================================================
  safety_filter.py
  Two functions:
  1. is_emergency()       — detects emergency keywords
  2. has_restricted_content() — detects unsafe AI output
============================================================
"""

# ── Emergency keywords (Roman Urdu + English) ────────────
EMERGENCY_KEYWORDS = [
    # English
    "chest pain", "heart attack", "can't breathe", "difficulty breathing",
    "unconscious", "severe bleeding", "not breathing", "stroke",
    "overdose", "poisoning", "suicide", "seizure", "fits",
    "severe chest", "collapsed", "fainted", "choking",
    # Roman Urdu
    "seene mein dard", "saans nahi", "behosh", "zyada khoon",
    "neend nahi aa rahi aur dil ghabra raha hai",
    "zehr", "khud ko nuqsan", "girane wala", "dil band",
    "sans rukk", "haath sonn", "aankh andhi",
]

# ── Restricted words in AI output ────────────────────────
RESTRICTED_OUTPUT_WORDS = [
    # Dosage related
    "mg", "milligram", "tablet", "tablets", "capsule", "capsules",
    "twice a day", "once a day", "3 times", "dosage", "dose",
    "take 1", "take 2", "take 500", "per day",
    # Brand names
    "panadol", "brufen", "flagyl", "augmentin", "disprin",
    "ciprofloxacin", "amoxicillin", "metronidazole", "ibuprofen",
    # Diagnosis confirmation
    "you have", "you are suffering from", "diagnosis is",
    "aap ko yeh disease hai", "yeh cancer hai", "yeh diabetes hai",
]


def is_emergency(message: str) -> bool:
    """
    Returns True if message contains emergency keywords.
    """
    msg_lower = message.lower().strip()
    return any(keyword in msg_lower for keyword in EMERGENCY_KEYWORDS)


def has_restricted_content(response: str) -> bool:
    """
    Returns True if LLaMA response contains restricted/unsafe content.
    """
    response_lower = response.lower().strip()
    return any(word in response_lower for word in RESTRICTED_OUTPUT_WORDS)