"""
============================================================
  SEHAT MAND PAKISTAN — test_all.py
  Tests: Groq API + Ollama + Firestore doctor fetch
  Run  : python test_all.py
============================================================
"""

import os, requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env from same folder
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

print("=" * 55)
print("  SEHAT MAND PAKISTAN — Full System Test")
print("=" * 55)

# ════════════════════════════════════════════════════════
#  TEST 1 — Groq API
# ════════════════════════════════════════════════════════
print("\n[1/3] Testing Groq API...")
try:
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("  ❌ GROQ_API_KEY not found in .env")
    else:
        client   = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model    = "llama-3.1-8b-instant",
            messages = [{"role": "user", "content": "Say OK in one word."}],
            max_tokens = 10,
        )
        reply = response.choices[0].message.content.strip()
        print(f"  ✅ Groq API working! Response: {reply}")
except Exception as e:
    print(f"  ❌ Groq failed: {e}")

# ════════════════════════════════════════════════════════
#  TEST 2 — Local Ollama
# ════════════════════════════════════════════════════════
print("\n[2/3] Testing Local Ollama...")
try:
    r = requests.post(
        "http://localhost:11434/api/generate",
        json   = {"model": "llama3", "prompt": "Say OK", "stream": False,
                  "options": {"num_predict": 5}},
        timeout = 15,
    )
    if r.status_code == 200:
        reply = r.json().get("response", "").strip()
        print(f"  ✅ Ollama working! Response: {reply}")
    else:
        print(f"  ❌ Ollama returned status: {r.status_code}")
except requests.exceptions.ConnectionError:
    print("  ❌ Ollama not running — start with: ollama serve")
except requests.exceptions.Timeout:
    print("  ⚠️  Ollama timed out (model may be loading, try again)")
except Exception as e:
    print(f"  ❌ Ollama failed: {e}")

# ════════════════════════════════════════════════════════
#  TEST 3 — Firestore Doctor Fetch
# ════════════════════════════════════════════════════════
print("\n[3/3] Testing Firestore doctor fetch...")
try:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from modules.firestore_service import get_doctors_by_specialization

    # Test common specializations
    test_specs = ["cardiologist", "pediatrician", "dermatologist", "gynecologist"]

    for spec in test_specs:
        docs = get_doctors_by_specialization(spec)
        count = len(docs) if docs else 0
        if count > 0:
            sample = docs[0]
            print(f"  ✅ '{spec}' → {count} doctors found")
            print(f"     Sample: {sample.get('name')} | {sample.get('hospital_name')}")
        else:
            print(f"  ❌ '{spec}' → 0 doctors found (check Firestore field name)")

    # Also print raw first document to see exact field names
    print("\n  📋 Checking raw Firestore document structure...")
    docs = get_doctors_by_specialization("cardiologist")
    if docs:
        print(f"  Raw fields: {list(docs[0].keys())}")
        print(f"  specialization value: '{docs[0].get('specialization')}'")
    else:
        # Try fetching any doctor to see structure
        print("  ⚠️  No cardiologist found — check if specialization field name matches")

except Exception as e:
    print(f"  ❌ Firestore failed: {e}")

print("\n" + "=" * 55)
print("  Test Complete!")
print("=" * 55)