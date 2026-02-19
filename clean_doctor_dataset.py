"""
============================================================
  SEHAT MAND PAKISTAN — Step 1: Doctors Dataset Cleaning
  Input : Excel file (All-Karachi-Drs-List-With-Number-and-Pmdc)
  Output: cleaned_doctors.csv
============================================================
"""

import pandas as pd
import re
import os

# ──────────────────────────────────────────────
# CONFIG — change paths if needed
# ──────────────────────────────────────────────
INPUT_FILE  = "784588866-All-Karachi-Drs-List-With-Number-and-Pmdc-1-1.xlsx"
OUTPUT_FILE = "cleaned_doctors.csv"
TARGET_CITY = "KARACHI"

# ──────────────────────────────────────────────
# STEP 1: Load Excel with correct header
# ──────────────────────────────────────────────
# The Excel has 2 junk rows at top before real headers
print("📂 Loading Excel file...")
df = pd.read_excel(INPUT_FILE, skiprows=1)

# Row 0 in loaded df is actual column names
df.columns = df.iloc[0]
df = df[1:].reset_index(drop=True)

print(f"   Total rows loaded: {len(df)}")
print(f"   Columns: {df.columns.tolist()}\n")

# ──────────────────────────────────────────────
# STEP 2: Keep only needed columns
# ──────────────────────────────────────────────
keep_cols = {
    "Doctor Name"         : "name",
    "Practice Place Name" : "hospital_name",
    "Specialty"           : "specialization",
    "Location Name"       : "city",
    "CELL"                : "phone",
    "PMDC"                : "pmdc"
}

df = df[list(keep_cols.keys())].rename(columns=keep_cols)
print(f"✅ Columns selected and renamed: {df.columns.tolist()}\n")

# ──────────────────────────────────────────────
# STEP 3: Filter Karachi only
# ──────────────────────────────────────────────
df["city"] = df["city"].astype(str).str.strip().str.upper()
df = df[df["city"] == TARGET_CITY].reset_index(drop=True)
print(f"📍 After Karachi filter: {len(df)} doctors\n")

# ──────────────────────────────────────────────
# STEP 4: Clean text columns — lowercase + strip
# ──────────────────────────────────────────────
text_cols = ["name", "hospital_name", "specialization", "city"]

for col in text_cols:
    df[col] = df[col].astype(str).str.strip().str.lower()

print("✅ Text columns: lowercased and stripped\n")

# ──────────────────────────────────────────────
# STEP 5: Clean phone numbers
# - Remove trailing slashes
# - Ensure starts with 92 (Pakistan country code)
# - Drop clearly invalid entries (too short)
# ──────────────────────────────────────────────
def clean_phone(val):
    val = str(val).strip()
    val = val.replace("/", "").replace(" ", "").replace("-", "")
    # Remove .0 from numeric conversion artifacts
    val = re.sub(r"\.0$", "", val)
    # If starts with 923 and is 12 digits → valid Pakistani mobile
    if re.match(r"^923\d{9}$", val):
        return val
    # If starts with 03 → convert to 923 format
    if re.match(r"^03\d{9}$", val):
        return "92" + val[1:]
    # Too short or junk
    if len(val) < 10:
        return None
    return val

df["phone"] = df["phone"].apply(clean_phone)
invalid_phones = df["phone"].isna().sum()
print(f"📞 Phone cleaning done. Invalid/missing phones: {invalid_phones}\n")

# ──────────────────────────────────────────────
# STEP 6: Normalize specializations
# - Fix typos (Speciality names in dataset have known typos)
# - Collapse duplicates caused by leading spaces
# ──────────────────────────────────────────────
specialty_map = {
    "genral practitinor (gp)"          : "general practitioner (gp)",
    "genral physician"                  : "general physician",
    "genral practitinor (gp), genral physician" : "general practitioner (gp)",
    "genral practitinor (gp), gynecologist"     : "general practitioner (gp)",
    "genral practitinor (gp), pediatrician"     : "general practitioner (gp)",
    "pediatrician"                      : "pediatrician",
    "child specialist"                  : "pediatrician",
    "child specialist, pediatrician"    : "pediatrician",
    "gastroenterlolgist"                : "gastroenterologist",
    "gastroentrologist"                 : "gastroenterologist",
    "diabatalogist"                     : "diabetologist",
    "genral surgeon"                    : "general surgeon",
    "general surgery"                   : "general surgeon",
}

def normalize_specialty(val):
    if pd.isna(val) or str(val).strip() in ["", "nan"]:
        return None
    val = str(val).strip().lower()
    return specialty_map.get(val, val)   # use map if exists, else keep cleaned value

df["specialization"] = df["specialization"].apply(normalize_specialty)
print(f"✅ Specializations normalized\n")
print("   Top specializations after cleaning:")
print(df["specialization"].value_counts().head(15).to_string())
print()

# ──────────────────────────────────────────────
# STEP 7: Handle nulls
# - Drop rows where name is null/empty
# - hospital_name → fill null with "clinic not specified"
# - specialization → fill null with "general practitioner (gp)"
# - pmdc → fill null with empty string (optional field)
# ──────────────────────────────────────────────
before = len(df)
df = df[df["name"].notna() & (df["name"].str.strip() != "") & (df["name"] != "nan")]
print(f"🗑️  Dropped {before - len(df)} rows with missing doctor name\n")

df["hospital_name"]  = df["hospital_name"].fillna("clinic not specified")
df["specialization"] = df["specialization"].fillna("general practitioner (gp)")
df["pmdc"]           = df["pmdc"].fillna("").astype(str).str.strip()

# ──────────────────────────────────────────────
# STEP 8: Remove exact duplicates
# ──────────────────────────────────────────────
before = len(df)
df = df.drop_duplicates(subset=["name", "phone"]).reset_index(drop=True)
print(f"♻️  Removed {before - len(df)} duplicate rows (same name + phone)\n")

# ──────────────────────────────────────────────
# STEP 9: Final check + Save
# ──────────────────────────────────────────────
print("=" * 50)
print("📊 FINAL DATASET SUMMARY")
print("=" * 50)
print(f"  Total doctors (Karachi): {len(df)}")
print(f"  Null values remaining:\n{df.isnull().sum().to_string()}")
print(f"  Unique specializations: {df['specialization'].nunique()}")
print()

df.to_csv(OUTPUT_FILE, index=False)
print(f"✅ Cleaned dataset saved → {OUTPUT_FILE}")
print()
print("📋 Sample rows:")
print(df[["name", "hospital_name", "specialization", "phone", "pmdc"]].head(5).to_string())