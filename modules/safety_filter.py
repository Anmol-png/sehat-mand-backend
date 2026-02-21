"""
============================================================
  safety_filter.py — OPTIMIZED
  1. is_emergency()           → detects life-threatening situations
  2. has_restricted_content() → catches unsafe AI outputs
  3. detect_emotional_state() → detects user distress
============================================================
"""

# ── Emergency keywords (expanded — Roman Urdu + English) ──
EMERGENCY_KEYWORDS = [
    # Cardiac
    "chest pain", "heart attack", "cardiac arrest", "dil ka dora",
    "seene mein dard", "seene mein takleef", "left arm pain", "bayan baazu dard",
    "dil ki dhadkan ruk", "palpitation severe",
    # Breathing
    "can't breathe", "difficulty breathing", "saans nahi",
    "saans lene mein takleef", "not breathing", "choking", "gala band",
    "shortness of breath", "dyspnea",
    # Neurological
    "stroke", "laqwa", "unconscious", "behosh", "seizure", "fits",
    "mircgi", "sudden numbness", "face drooping", "aankhon ka andha hona",
    "sudden confusion", "severe headache", "zarb lagna dimagh",
    # Bleeding
    "severe bleeding", "zyada khoon", "blood vomiting", "khoon ulti",
    "khoon aa raha hai", "haemorrhage", "uncontrolled bleeding",
    # Other emergencies
    "overdose", "zahr", "poisoning", "suicide", "khud ko nuqsan",
    "fainted", "collapsed", "gir gaya", "unconscious pad gaya",
    "severe allergic", "anaphylaxis", "shock",
    # Trauma
    "accident", "hadsa", "head injury", "sir par chot", "broken bone severe",
    "drowning", "doobna", "burn severe", "jalana severe",
    # Pediatric emergencies
    "baby not breathing", "bachay ki saans nahi", "baby unresponsive",
    "bacha behosh",
]

# ── Restricted output patterns (doctor should not produce these) ──
RESTRICTED_OUTPUT_WORDS = [
    # Specific dosages
    " mg ", "milligram", "ml of ", "cc of ",
    "take 1 tablet", "take 2 tablet", "take 500", "take 250",
    "twice a day", "thrice a day", "3 times a day", "per day dose",
    "dosage is", "dose of",
    # Brand names (Pakistan common brands)
    "panadol", "brufen", "flagyl", "augmentin", "disprin", "ponstan",
    "ciprofloxacin", "amoxicillin", "metronidazole", "ibuprofen",
    "paracetamol 500", "aspirin 75", "omeprazole 20",
    "calpol", "risek", "nexum", "losec", "amoxil",
    "clavam", "cefspan", "zithromax", "azithromycin 500",
    # Diagnosis confirmations
    "you have diabetes", "you have cancer", "you are suffering from",
    "diagnosis is confirmed", "aap ko yeh disease hai",
    "yeh cancer hai", "yeh tb hai", "you definitely have",
    # Injection/IV instructions (for user mode)
    "inject", "intravenous", "iv drip", "saline drip start",
]

# ── Emotional distress indicators ─────────────────────────
EMOTIONAL_DISTRESS = [
    "bohot dukhi", "very sad", "pareshan", "upset", "crying", "ro raha",
    "ro rahi", "depressed", "hopeless", "umeed nahi", "zindagi se thak",
    "jina nahi chahta", "jina nahi chahti", "give up on life",
    "koi nahi mera", "akela", "akeli", "abandoned", "worthless",
    "haar gaya", "haar gayi",
]


def is_emergency(message: str) -> bool:
    """Returns True if message contains emergency keywords."""
    msg_lower = message.lower().strip()
    return any(keyword in msg_lower for keyword in EMERGENCY_KEYWORDS)


def has_restricted_content(response: str) -> bool:
    """
    Returns True if AI response contains restricted/unsafe content.
    Only applied in user mode — doctor mode has relaxed rules.
    """
    response_lower = response.lower().strip()
    return any(word in response_lower for word in RESTRICTED_OUTPUT_WORDS)


def detect_emotional_state(message: str) -> str:
    """
    Returns emotional state:
    - 'distressed' : user shows signs of serious distress
    - 'sad'        : user seems down/tired
    - 'normal'     : regular message
    """
    msg_lower = message.lower().strip()
    
    # Check for severe distress (suicidal ideation etc.)
    severe = ["jina nahi chahta", "jina nahi chahti", "suicide", "khud ko nuqsan",
              "zindagi khatam", "mar jana chahta", "mar jana chahti"]
    if any(phrase in msg_lower for phrase in severe):
        return "distressed"
    
    if any(phrase in msg_lower for phrase in EMOTIONAL_DISTRESS):
        return "sad"
    
    return "normal"