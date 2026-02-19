# 🏥 Sehat Mand Pakistan — Backend

An AI-powered Tele-Health backend built with Flask, LLaMA 3, and Firebase Firestore.
Designed specifically for Karachi, Pakistan — providing medical guidance, specialist doctor
suggestions, and emergency information in Roman Urdu and English.

---

## ✅ Work Completed

| # | Task | Status |
|---|------|--------|
| 1 | Doctors dataset cleaning (23,007 → 2,834 Karachi doctors) | ✅ Done |
| 2 | Firestore upload (doctors collection — 2,834 documents) | ✅ Done |
| 3 | Intent detection (general advice vs specialist request) | ✅ Done |
| 4 | LLaMA 3 integration via Ollama (local) | ✅ Done |
| 5 | Flask REST API (`POST /api/chat`) | ✅ Done |
| 6 | Safety filters (emergency detection + restricted content) | ✅ Done |
| 7 | Firestore doctor lookup by specialization | ✅ Done |

---

## 🗂️ Project Structure

```
GenAI/
├── app.py                        # Main Flask application
├── requirements.txt              # Python dependencies
├── clean_doctors_dataset.py      # Dataset cleaning script
├── upload_to_firestore.py        # Firestore upload script
└── modules/
      ├── __init__.py
      ├── intent_detector.py      # Detects user intent (general/specialist)
      ├── firestore_service.py    # Firestore queries for doctors
      ├── llama_service.py        # LLaMA 3 via Ollama integration
      └── safety_filter.py        # Emergency + restricted content filter
```

---

## 🔄 Navigation / Request Flow

```
Flutter App
    │
    │  POST /api/chat
    │  { "message": "mujhe bukhar ho raha hai" }
    ▼
┌─────────────────────────────────────────────┐
│                  app.py                      │
│                                             │
│  1. Validate input message                  │
│  2. Check emergency keywords                │
│     └── if emergency → return 1122 alert    │
│  3. Detect intent                           │
│     └── general or specialist?              │
│  4. If specialist → fetch doctors           │
│     └── Firestore query by specialization   │
│  5. Build prompt with context               │
│  6. Call LLaMA 3 via Ollama                 │
│  7. Safety filter on AI response            │
│  8. Return structured JSON                  │
└─────────────────────────────────────────────┘
    │
    │  Response JSON
    │  {
    │    "reply"      : "AI response",
    │    "type"       : "general | specialist | emergency",
    │    "specialist" : "cardiologist",
    │    "doctors"    : [ { name, hospital, phone } ],
    │    "mild_advice": "..."
    │  }
    ▼
Flutter App (displays response)
```

---

## 🧠 Intent Detection Flow

```
User Message
    │
    ├── Contains emergency keywords?
    │   (chest pain, saans nahi, behosh...)
    │   └── YES → Return emergency response immediately
    │
    ├── Contains doctor request phrases?
    │   (kaun sa doctor, specialist chahiye...)
    │   └── YES + specialty matched → type: "specialist"
    │         └── Fetch doctors from Firestore
    │
    └── Symptoms only?
        └── type: "general"
              └── LLaMA gives mild lifestyle advice
```

---

## 🛡️ Safety Rules (LLaMA System Prompt)

- ❌ Never confirm or diagnose any disease
- ❌ Never suggest medicine brand names
- ❌ Never give exact dosage or tablet count
- ❌ Never write a prescription
- ✅ Only give mild general lifestyle advice
- ✅ Only suggest Karachi-based doctors
- ✅ Always recommend consulting a real doctor
- ✅ Detect emergency and advise hospital visit

---

## 🗄️ Firestore Structure

```
doctors (collection)
└── dr_ahmed_raza (document)
    ├── name           : "dr ahmed raza"
    ├── hospital_name  : "akbar hospital clifton karachi"
    ├── specialization : "cardiologist"
    ├── city           : "karachi"
    ├── phone          : "923012345678"
    ├── pmdc           : "12345-P"
    ├── emergency_flag : false
    └── active         : true
```

---

## 🔌 API Endpoints

### `POST /api/chat`
**Request:**
```json
{ "message": "mujhe heart problem hai kaun sa doctor dekhe" }
```
**Response:**
```json
{
  "reply"      : "Aapko cardiologist se milna chahiye...",
  "type"       : "specialist",
  "specialist" : "cardiologist",
  "mild_advice": null,
  "doctors": [
    {
      "name"          : "dr ahmed raza",
      "hospital_name" : "akbar hospital karachi",
      "specialization": "cardiologist",
      "phone"         : "923012345678",
      "pmdc"          : "12345-P",
      "city"          : "karachi"
    }
  ]
}
```

### `GET /api/health`
**Response:**
```json
{ "status": "running", "app": "Sehat Mand Pakistan" }
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + Flask |
| AI Model | LLaMA 3 via Ollama (local) |
| Database | Firebase Firestore |
| Auth | Firebase Authentication |
| Dataset | 2,834 Karachi doctors (cleaned CSV) |

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
pip install flask firebase-admin requests
```

### 2. Add Firebase key
Place your `serviceAccountKey.json` in the root folder.

### 3. Start Ollama
```bash
ollama serve
```

### 4. Run Flask
```bash
python app.py
```

### 5. Test API
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method GET
```

---

## 🔐 Environment & Security

- `serviceAccountKey.json` is in `.gitignore` — never push to GitHub
- `cleaned_doctors.csv` is in `.gitignore`
- LLaMA runs locally — no data sent to external AI APIs
- All responses filtered for restricted medical content

---


## 👨‍💻 Developer

**Project:** Sehat Mand Pakistan  
**City:** Karachi, Pakistan  
**Stack:** Flask · LLaMA 3 · Firebase · Flutter
