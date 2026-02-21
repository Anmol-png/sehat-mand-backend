"""
Run this FIRST to diagnose Firestore connection issues:
  python test_firestore.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from modules.firestore_service import test_connection, get_all_specializations, db

print("=" * 55)
print("  SEHAT MAND — Firestore Diagnostics")
print("=" * 55)

print("\n[1] DB object:", db)

print("\n[2] Testing single-doc connection...")
ok = test_connection()

if ok:
    print("\n[3] Fetching all specializations (may take 15-20s first time)...")
    specs = get_all_specializations()
    print(f"    Found {len(specs)} unique specializations:")
    for s in specs[:20]:
        print(f"      - {s}")
else:
    print("\n[3] Skipped — connection failed.")
    print("\nTROUBLESHOOT:")
    print("  1. Check serviceAccountKey.json is in the project root")
    print("  2. Check Firebase Console → Firestore → Rules allow read")
    print("     Rules should have: allow read, write: if true;  (for dev)")
    print("  3. Check your internet connection")
    print("  4. Verify project_id in serviceAccountKey.json matches your Firebase project")

print("\n" + "=" * 55)