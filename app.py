"""
============================================================
  SEHAT MAND PAKISTAN — app.py
  + Server-side conversation memory (session_id based)
  Body: { "message": "...", "mode": "user"|"doctor", "session_id": "abc123" }
============================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from modules.intent_detector   import detect_intent, detect_clinical_specialty
from modules.firestore_service import get_doctors_by_specialization, warm_up
from modules.llama_service     import ask_user_mode, ask_doctor_mode
from modules.safety_filter     import is_emergency, has_restricted_content
import time

app = Flask(__name__)
CORS(app)

# ── Server-side conversation memory ──────────────────────
SESSIONS     = {}
SESSION_TTL  = 1800   # 30 minutes
MAX_HISTORY  = 10     # keep last 10 turns


def _get_history(session_id: str) -> list:
    if session_id and session_id in SESSIONS:
        return SESSIONS[session_id]["history"]
    return []


def _save_history(session_id: str, user_msg: str, assistant_msg: str):
    if not session_id:
        return
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {"history": [], "last_active": time.time()}

    SESSIONS[session_id]["history"].append({"role": "user",      "content": user_msg})
    SESSIONS[session_id]["history"].append({"role": "assistant", "content": assistant_msg})
    SESSIONS[session_id]["last_active"] = time.time()

    if len(SESSIONS[session_id]["history"]) > MAX_HISTORY * 2:
        SESSIONS[session_id]["history"] = SESSIONS[session_id]["history"][-(MAX_HISTORY * 2):]


def _cleanup_sessions():
    now     = time.time()
    expired = [sid for sid, s in SESSIONS.items() if now - s["last_active"] > SESSION_TTL]
    for sid in expired:
        del SESSIONS[sid]


EMERGENCY_RESPONSE = {
    "reply": (
        "⚠️ EMERGENCY DETECTED!\n\n"
        "Foran nazdiki hospital jayein ya yeh numbers call karein:\n"
        "🚑 1122 — Rescue / Ambulance\n"
        "🏥 115  — Edhi Ambulance\n"
        "🚨 1020 — Aman Foundation Karachi\n\n"
        "Deri mat karein — yeh life threatening ho sakta hai!"
    ),
    "type"      : "emergency",
    "doctors"   : [],
    "specialist": None,
}


def _format_doctor_context(doctors: list, specialist: str) -> str:
    if not doctors:
        return ""
    lines = []
    for i, d in enumerate(doctors, 1):
        phone = d.get("phone") or "N/A"
        pmdc  = d.get("pmdc")  or "N/A"
        lines.append(
            f"{i}. {d['name'].title()}"
            f" | {d['hospital_name'].title()}"
            f" | Phone: {phone}"
            f" | PMDC: {pmdc}"
        )
    return f"{specialist.title()} doctors in Karachi:\n" + "\n".join(lines)


@app.route("/api/chat", methods=["POST"])
def chat():
    _cleanup_sessions()

    data       = request.get_json()
    message    = (data.get("message") or "").strip()
    mode       = (data.get("mode") or "user").strip().lower()
    session_id = (data.get("session_id") or "").strip()

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400
    if mode not in ("user", "doctor"):
        mode = "user"

    # ── Emergency check ───────────────────────────────────
    if is_emergency(message):
        resp = EMERGENCY_RESPONSE.copy()
        resp["mode"] = mode
        return jsonify(resp), 200

    history = _get_history(session_id)
    print(f"[Session] id={session_id or 'none'} | history_turns={len(history)//2}")

    # ════════════════════════════════════════════════════
    #  USER MODE
    # ════════════════════════════════════════════════════
    if mode == "user":
        intent     = detect_intent(message)
        doctors    = []
        specialist = None
        context    = ""

        print(f"[Intent] type={intent['type']} | spec={intent.get('specialization')}")

        if intent["type"] == "specialist":
            specialist = intent.get("specialization")
            raw_docs   = get_doctors_by_specialization(specialist)
            if raw_docs:
                doctors = raw_docs
                context = _format_doctor_context(doctors, specialist)

        reply = ask_user_mode(message, history=history, doctor_context=context)

        if has_restricted_content(reply):
            reply = (
                "Mujhe khed hai, main yeh specific medical information provide "
                "nahi kar sakta. Kripaya ek qualified doctor se rabta karein."
            )

        _save_history(session_id, message, reply)

        return jsonify({
            "reply"     : reply,
            "type"      : intent["type"],
            "specialist": specialist,
            "doctors"   : doctors,
            "mode"      : "user",
        }), 200

    # ════════════════════════════════════════════════════
    #  DOCTOR MODE
    # ════════════════════════════════════════════════════
    else:
        specialist = detect_clinical_specialty(message)
        doctors    = []
        context    = ""

        if specialist:
            raw_docs = get_doctors_by_specialization(specialist)
            if raw_docs:
                doctors = raw_docs
                context = _format_doctor_context(doctors, specialist)

        reply = ask_doctor_mode(message, history=history, doctor_context=context)

        if has_restricted_content(reply):
            reply = (
                "Clinical assessment ke liye patient ko directly examine "
                "karein aur senior physician se consult karein."
            )

        _save_history(session_id, message, reply)

        return jsonify({
            "reply"     : reply,
            "type"      : "clinical",
            "specialist": specialist,
            "doctors"   : doctors,
            "mode"      : "doctor",
        }), 200


@app.route("/api/clear", methods=["POST"])
def clear_session():
    data       = request.get_json()
    session_id = (data.get("session_id") or "").strip()
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]
    return jsonify({"status": "cleared"}), 200


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "running", "active_sessions": len(SESSIONS)}), 200


if __name__ == "__main__":
    print("=" * 55)
    print("  SEHAT MAND PAKISTAN — Backend")
    print("  POST /api/chat")
    print("  Body: { message, mode, session_id }")
    print("=" * 55)

    # ── Pre-load Firestore cache before accepting requests ──
    warm_up()

    app.run(debug=True, host="0.0.0.0", port=5000)