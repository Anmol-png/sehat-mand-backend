"""
============================================================
  firestore_service.py
  Handles all Firestore queries for doctors
============================================================
"""

import firebase_admin
from firebase_admin import credentials, firestore

# ── Initialize Firebase (only once) ──────────────────────
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()


def get_doctors_by_specialization(specialization: str, city: str = "karachi", limit: int = 5) -> list:
    """
    Fetch doctors from Firestore by specialization and city.
    Returns list of doctor dicts.
    """
    try:
        doctors_ref = db.collection("doctors")

        # Query by city + specialization
        query = (
            doctors_ref
            .where("city", "==", city)
            .where("specialization", "==", specialization.lower().strip())
            .where("active", "==", True)
            .limit(limit)
        )

        docs = query.stream()
        results = []

        for doc in docs:
            d = doc.to_dict()
            results.append({
                "name"          : d.get("name", "N/A"),
                "hospital_name" : d.get("hospital_name", "N/A"),
                "specialization": d.get("specialization", "N/A"),
                "phone"         : d.get("phone", None),
                "pmdc"          : d.get("pmdc", None),
                "city"          : d.get("city", "karachi"),
            })

        # ── Fallback: if exact match returns nothing,
        #    try partial match using Python filter ──────
        if not results:
            results = _fallback_search(specialization, city, limit)

        return results

    except Exception as e:
        print(f"[Firestore Error] {e}")
        return []


def _fallback_search(specialization: str, city: str, limit: int) -> list:
    """
    Fallback: fetch all Karachi doctors and filter by
    partial specialization match in Python.
    Useful for composite specializations like
    'general practitioner (gp), gynecologist'
    """
    try:
        docs = (
            db.collection("doctors")
            .where("city", "==", city)
            .where("active", "==", True)
            .stream()
        )

        results = []
        keyword = specialization.lower().strip()

        for doc in docs:
            d = doc.to_dict()
            spec = str(d.get("specialization", "")).lower()
            if keyword in spec:
                results.append({
                    "name"          : d.get("name", "N/A"),
                    "hospital_name" : d.get("hospital_name", "N/A"),
                    "specialization": d.get("specialization", "N/A"),
                    "phone"         : d.get("phone", None),
                    "pmdc"          : d.get("pmdc", None),
                    "city"          : d.get("city", "karachi"),
                })
            if len(results) >= limit:
                break

        return results

    except Exception as e:
        print(f"[Firestore Fallback Error] {e}")
        return []