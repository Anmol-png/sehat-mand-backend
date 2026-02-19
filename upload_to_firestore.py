"""
============================================================
  SEHAT MAND PAKISTAN — Step 2: Firestore Upload
  Input : cleaned_doctors.csv
  Upload: Firebase Firestore → 'doctors' collection
============================================================

FOLDER STRUCTURE (keep all 3 files in same folder):
  ├── upload_to_firestore.py
  ├── cleaned_doctors.csv
  └── serviceAccountKey.json

INSTALL REQUIREMENTS:
  pip install firebase-admin pandas
============================================================
"""

import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import math
import time

# ──────────────────────────────────────────────
# STEP 1: Connect to Firebase
# ──────────────────────────────────────────────
print("🔥 Connecting to Firebase...")

cred = credentials.Certificate("serviceAccountKey.json")  # your downloaded key
firebase_admin.initialize_app(cred)

db = firestore.client()
print("✅ Firebase connected!\n")

# ──────────────────────────────────────────────
# STEP 2: Load cleaned CSV
# ──────────────────────────────────────────────
print("📂 Loading cleaned_doctors.csv...")
df = pd.read_csv("cleaned_doctors.csv")

# Replace NaN with None so Firestore accepts it
df = df.where(pd.notnull(df), None)

print(f"   Total doctors to upload: {len(df)}\n")

# ──────────────────────────────────────────────
# STEP 3: Upload to Firestore in batches
# Firestore allows max 500 writes per batch
# ──────────────────────────────────────────────

BATCH_SIZE = 400  # safe limit under 500
collection_ref = db.collection("doctors")

total    = len(df)
uploaded = 0
failed   = 0

print("⬆️  Starting upload to Firestore 'doctors' collection...")
print("=" * 50)

for batch_start in range(0, total, BATCH_SIZE):

    batch     = db.batch()
    batch_df  = df.iloc[batch_start : batch_start + BATCH_SIZE]

    for _, row in batch_df.iterrows():

        # ── Build document data ──────────────────
        doc_data = {
            "name"           : row["name"],
            "hospital_name"  : row["hospital_name"] if row["hospital_name"] else "clinic not specified",
            "specialization" : row["specialization"] if row["specialization"] else "general practitioner (gp)",
            "city"           : row["city"],
            "phone"          : str(row["phone"]) if row["phone"] else None,
            "pmdc"           : str(row["pmdc"])  if row["pmdc"]  else None,
            "emergency_flag" : False,   # default — can be updated later
            "active"         : True,    # for future soft-delete support
        }

        # ── Use doctor name as document ID ───────
        # Replace spaces with underscores for clean Firestore doc ID
        doc_id = str(row["name"]).strip().replace(" ", "_").replace("/", "_")

        # If doc_id is empty fallback to auto ID
        if not doc_id or doc_id == "nan":
            doc_ref = collection_ref.document()
        else:
            doc_ref = collection_ref.document(doc_id)

        batch.set(doc_ref, doc_data)

    # ── Commit this batch ────────────────────────
    try:
        batch.commit()
        uploaded += len(batch_df)
        print(f"   ✅ Uploaded batch: {batch_start + 1} → {min(batch_start + BATCH_SIZE, total)} of {total}")
    except Exception as e:
        failed += len(batch_df)
        print(f"   ❌ Batch failed ({batch_start} → {batch_start + BATCH_SIZE}): {e}")

    # Small delay to avoid rate limiting
    time.sleep(0.5)

# ──────────────────────────────────────────────
# STEP 4: Summary
# ──────────────────────────────────────────────
print()
print("=" * 50)
print("📊 UPLOAD SUMMARY")
print("=" * 50)
print(f"  ✅ Successfully uploaded : {uploaded} doctors")
print(f"  ❌ Failed                : {failed} doctors")
print(f"  📁 Firestore collection  : 'doctors'")
print()
print("🎉 Done! Check your Firebase Console:")
print("   https://console.firebase.google.com")
print("   → Firestore Database → doctors collection")