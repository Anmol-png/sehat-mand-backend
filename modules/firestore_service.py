"""
============================================================
  firestore_service.py
  FIX: Uses threading timeout on all Firestore queries.
       Fetches ALL docs once, filters in Python (fastest).
============================================================
"""

import firebase_admin
from firebase_admin import credentials, firestore
import time
import threading

# ── Initialize Firebase (only once) ──────────────────────
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized")
    except Exception as e:
        print(f"⚠️ Firebase init error: {e}")

try:
    db = firestore.client()
except Exception as e:
    db = None
    print(f"⚠️ Firestore client error: {e}")

# ── Cache ─────────────────────────────────────────────────
_cache     = {}
_cache_ttl = 300  # 5 minutes

def _get_cache(key):
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < _cache_ttl:
            return data
    return None

def _set_cache(key, data):
    _cache[key] = (data, time.time())


# ════════════════════════════════════════════════════════
#  FETCH ALL DOCS WITH TIMEOUT
# ════════════════════════════════════════════════════════
def _fetch_all_docs(timeout_sec: int = 10) -> list:
    """
    Fetch all doctor documents from Firestore.
    Uses threading timeout to avoid hanging forever.
    """
    result   = []
    error    = []

    def _fetch():
        try:
            docs = db.collection("doctors").limit(500).stream()
            for doc in docs:
                result.append(doc.to_dict())
        except Exception as e:
            error.append(str(e))

    t = threading.Thread(target=_fetch)
    t.start()
    t.join(timeout=timeout_sec)

    if t.is_alive():
        print(f"[Firestore] ⚠️ Timed out after {timeout_sec}s")
        return []

    if error:
        print(f"[Firestore] ❌ Error: {error[0]}")
        return []

    print(f"[Firestore] ✅ Fetched {len(result)} documents")
    return result


# ════════════════════════════════════════════════════════
#  MAIN FUNCTION
# ════════════════════════════════════════════════════════
def get_doctors_by_specialization(specialization: str, city: str = "karachi", limit: int = 5) -> list:
    if not db:
        return []

    cache_key = f"all_doctors"
    all_docs  = _get_cache(cache_key)

    if all_docs is None:
        print("[Firestore] Fetching all doctors (first time)...")
        all_docs = _fetch_all_docs(timeout_sec=10)
        if all_docs:
            _set_cache(cache_key, all_docs)
        else:
            return []

    # Filter in Python — fast, no index needed
    keyword = specialization.lower().strip()
    matched = []

    for d in all_docs:
        spec = str(d.get("specialization", "")).lower().strip()
        if keyword in spec or spec in keyword:
            matched.append(_fmt(d))

    print(f"[Firestore] '{keyword}' matched {len(matched)} doctors")

    # Prioritize doctors with phone numbers
    return _prioritize(matched, limit)


def _fmt(d: dict) -> dict:
    return {
        "name"          : d.get("name", "N/A"),
        "hospital_name" : d.get("hospital_name", "N/A"),
        "specialization": d.get("specialization", "N/A"),
        "phone"         : d.get("phone", None),
        "pmdc"          : d.get("pmdc", None),
        "city"          : d.get("city", "karachi"),
    }


def _prioritize(doctors: list, limit: int) -> list:
    with_phone    = [d for d in doctors if d.get("phone")]
    without_phone = [d for d in doctors if not d.get("phone")]
    return (with_phone + without_phone)[:limit]


def get_all_specializations() -> list:
    """Returns all unique specialization values — useful for debugging."""
    all_docs = _fetch_all_docs(timeout_sec=10)
    specs = set()
    for d in all_docs:
        s = d.get("specialization", "")
        if s:
            specs.add(str(s).strip())
    return sorted(specs)