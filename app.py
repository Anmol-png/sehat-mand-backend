"""
============================================================
  SEHAT MAND PAKISTAN — app.py
  + Server-side conversation memory (session_id based)
  + FREE hospital search via OpenStreetMap Overpass API
    (no Google billing, no credit card required)
  Body: { "message": "...", "mode": "user"|"doctor", "session_id": "abc123" }
============================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from modules.intent_detector   import detect_intent, detect_clinical_specialty
from modules.firestore_service import get_doctors_by_specialization, warm_up
from modules.llama_service     import ask_user_mode, ask_doctor_mode
from modules.safety_filter     import is_emergency, has_restricted_content
import requests as req
import time
import math

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
        "Please go to the nearest hospital immediately or call:\n"
        "🚑 1122 — Rescue / Ambulance\n"
        "🏥 115  — Edhi Ambulance\n"
        "🚨 1020 — Aman Foundation Karachi\n\n"
        "Do not delay — this could be life threatening!"
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


# ── Haversine distance (km) ───────────────────────────────
def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ════════════════════════════════════════════════════════
#  FREE HOSPITAL SEARCH — GET /api/places/nearby
#  Uses OpenStreetMap Overpass API (100% free, no key needed)
#
#  Query params:
#    lat    — user latitude  (required)
#    lng    — user longitude (required)
#    radius — search radius in metres (optional, default 5000)
# ════════════════════════════════════════════════════════
@app.route("/api/places/nearby", methods=["GET"])
def places_nearby():
    lat    = request.args.get("lat")
    lng    = request.args.get("lng")
    radius = request.args.get("radius", "5000")

    if not lat or not lng:
        return jsonify({"error": "lat and lng are required"}), 400

    try:
        lat_f = float(lat)
        lng_f = float(lng)
        rad_f = float(radius)
    except ValueError:
        return jsonify({"error": "lat, lng, radius must be numbers"}), 400

    print(f"[OSM] Searching hospitals near ({lat_f:.4f}, {lng_f:.4f}) r={rad_f}m")

    # ── Overpass QL query ─────────────────────────────────
    # Simple fast query — no regex (regex causes server timeouts)
    overpass_query = (
        f"[out:json][timeout:25];"
        f"("
        f'node["amenity"="hospital"](around:{rad_f},{lat_f},{lng_f});' 
        f'way["amenity"="hospital"](around:{rad_f},{lat_f},{lng_f});' 
        f'node["amenity"="clinic"](around:{rad_f},{lat_f},{lng_f});' 
        f'way["amenity"="clinic"](around:{rad_f},{lat_f},{lng_f});' 
        f'node["amenity"="doctors"](around:{rad_f},{lat_f},{lng_f});' 
        f'way["amenity"="doctors"](around:{rad_f},{lat_f},{lng_f});' 
        f'node["amenity"="health_post"](around:{rad_f},{lat_f},{lng_f});' 
        f'way["amenity"="health_post"](around:{rad_f},{lat_f},{lng_f});' 
        f'node["healthcare"](around:{rad_f},{lat_f},{lng_f});' 
        f'way["healthcare"](around:{rad_f},{lat_f},{lng_f});' 
        f");out center tags;"
    )

    # Try multiple Overpass mirrors in case one is down
    overpass_mirrors = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    ]

    resp = None
    last_error = None

    for mirror in overpass_mirrors:
        try:
            print(f"[OSM] Trying mirror: {mirror}")
            resp = req.post(
                mirror,
                data   = overpass_query.encode("utf-8"),
                timeout= 20,
                headers= {"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            print(f"[OSM] Success from {mirror} | HTTP {resp.status_code}")
            break  # success — stop trying mirrors
        except req.exceptions.Timeout:
            last_error = f"Timeout on {mirror}"
            print(f"[OSM] Timeout: {mirror}")
        except Exception as e:
            last_error = str(e)
            print(f"[OSM] Error on {mirror}: {e}")
        resp = None

    if resp is None:
        return jsonify({"error": f"All OpenStreetMap mirrors failed. Last error: {last_error}"}), 504

    try:
        osm_data     = resp.json()
        raw_elements = osm_data.get("elements", [])
    except Exception as e:
        print(f"[OSM] JSON parse error: {e} | body: {resp.text[:300]}")
        return jsonify({"error": f"Invalid response from OpenStreetMap: {str(e)}"}), 500

    print(f"[OSM] Raw elements returned: {len(raw_elements)}")

    results = []
    seen_names = set()

    for el in raw_elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:en") or tags.get("name:ur")
        if not name:
            continue  # skip unnamed places

        # Deduplicate by name
        name_key = name.lower().strip()
        if name_key in seen_names:
            continue
        seen_names.add(name_key)

        # Coordinates — nodes have lat/lon directly; ways have "center"
        if el["type"] == "node":
            el_lat = el.get("lat", lat_f)
            el_lng = el.get("lon", lng_f)
        else:
            center = el.get("center", {})
            el_lat = center.get("lat", lat_f)
            el_lng = center.get("lon", lng_f)

        dist_km = _haversine(lat_f, lng_f, el_lat, el_lng)

        # Build address from tags
        address_parts = []
        for key in ["addr:street", "addr:suburb", "addr:city"]:
            val = tags.get(key)
            if val:
                address_parts.append(val)
        address = ", ".join(address_parts) if address_parts else tags.get("addr:full", "")

        phone = tags.get("phone") or tags.get("contact:phone") or ""

        results.append({
            "place_id"   : str(el["id"]),
            "name"       : name,
            "vicinity"   : address,
            "phone"      : phone,
            "geometry"   : {
                "location": {"lat": el_lat, "lng": el_lng}
            },
            "distance_km": round(dist_km, 2),
            # OSM doesn't provide open/closed hours in most cases
            "opening_hours": {"open_now": None},
            "rating"     : None,
        })

    # Sort by distance
    results.sort(key=lambda x: x["distance_km"])
    results = results[:20]  # cap at 20

    print(f"[OSM] Returning {len(results)} hospitals")

    # Return in Google Places-compatible format so Flutter code doesn't change
    return jsonify({
        "status" : "OK" if results else "ZERO_RESULTS",
        "results": results,
    }), 200


# ════════════════════════════════════════════════════════
#  CHAT — POST /api/chat
# ════════════════════════════════════════════════════════
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
                "I'm sorry, I cannot provide this specific medical information. "
                "Please consult a qualified doctor."
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
                "For clinical assessment please examine the patient directly "
                "and consult a senior physician."
            )

        _save_history(session_id, message, reply)

        return jsonify({
            "reply"     : reply,
            "type"      : "clinical",
            "specialist": specialist,
            "doctors"   : doctors,
            "mode"      : "doctor",
        }), 200


# ════════════════════════════════════════════════════════
#  CLEAR SESSION — POST /api/clear
# ════════════════════════════════════════════════════════
@app.route("/api/clear", methods=["POST"])
def clear_session():
    data       = request.get_json()
    session_id = (data.get("session_id") or "").strip()
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]
    return jsonify({"status": "cleared"}), 200


# ════════════════════════════════════════════════════════
#  HEALTH CHECK — GET /api/health
# ════════════════════════════════════════════════════════
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status"         : "running",
        "active_sessions": len(SESSIONS),
        "hospital_search": "OpenStreetMap (free, no API key needed)",
    }), 200


if __name__ == "__main__":
    print("=" * 55)
    print("  SEHAT MAND PAKISTAN — Backend")
    print("  POST /api/chat          — AI chat")
    print("  GET  /api/places/nearby — FREE hospital search")
    print("                            (OpenStreetMap, no billing)")
    print("  POST /api/clear         — Clear session memory")
    print("  GET  /api/health        — Health check")
    print("=" * 55)

    warm_up()
    app.run(debug=True, host="0.0.0.0", port=5000)
