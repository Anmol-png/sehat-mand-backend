"""
============================================================
  SEHAT MAND PAKISTAN — Step 3: Flask API
  Endpoints  : POST /api/chat
  AI Model   : LLaMA 3 via Ollama (local)
  Database   : Firebase Firestore
============================================================

FOLDER STRUCTURE:
  ├── app.py
  ├── serviceAccountKey.json
  ├── requirements.txt
  └── modules/
        ├── __init__.py
        ├── firestore_service.py
        ├── llama_service.py
        ├── intent_detector.py
        └── safety_filter.py

INSTALL:
  pip install flask firebase-admin requests
============================================================
"""

from flask import Flask, request, jsonify
from modules.intent_detector  import detect_intent
from modules.firestore_service import get_doctors_by_specialization
from modules.llama_service     import ask_llama
from modules.safety_filter     import is_emergency, has_restricted_content

app = Flask(__name__)

# ──────────────────────────────────────────────
# MAIN CHAT ENDPOINT
# POST /api/chat
# Body: { "message": "mujhe sir dard ho raha hai" }
# ──────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    data    = request.get_json()
    message = data.get("message", "").strip()

    # ── Validate input ───────────────────────────
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # ── Step 1: Emergency check ──────────────────
    if is_emergency(message):
        return jsonify({
            "reply"         : "⚠️ Ye ek emergency lag rahi hai! Foran nazdiki hospital jayein ya 1122 call karein.",
            "type"          : "emergency",
            "doctors"       : [],
            "specialist"    : None,
            "mild_advice"   : None,
        }), 200

    # ── Step 2: Detect intent ────────────────────
    # Returns: { "type": "general" | "specialist", "specialization": "cardiologist" }
    intent = detect_intent(message)

    doctors      = []
    specialist   = None
    context_text = ""

    # ── Step 3: Fetch doctors if specialist asked ─
    if intent["type"] == "specialist":
        specialist = intent.get("specialization")
        doctors    = get_doctors_by_specialization(specialist)

        if doctors:
            # Build context for LLaMA from fetched doctors
            doctor_lines = "\n".join([
                f"- {d['name']} | {d['hospital_name']} | Phone: {d.get('phone', 'N/A')}"
                for d in doctors[:5]   # limit to top 5
            ])
            context_text = f"Yeh Karachi mein available {specialist} doctors hain:\n{doctor_lines}"
        else:
            context_text = f"Karachi mein {specialist} ka koi doctor abhi database mein nahi mila."

    # ── Step 4: Build prompt + call LLaMA 3 ──────
    reply = ask_llama(
        user_message = message,
        intent_type  = intent["type"],
        context      = context_text
    )

    # ── Step 5: Safety filter on LLaMA output ────
    if has_restricted_content(reply):
        reply = "Mujhe khed hai, main yeh specific medical information provide nahi kar sakta. Kripaya ek qualified doctor se rabta karein."

    # ── Step 6: Return structured JSON ───────────
    return jsonify({
        "reply"       : reply,
        "type"        : intent["type"],
        "specialist"  : specialist,
        "doctors"     : doctors[:5],   # max 5 doctors returned
        "mild_advice" : reply if intent["type"] == "general" else None,
    }), 200


# ── Health check endpoint ────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "running", "app": "Sehat Mand Pakistan"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)