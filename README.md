# 💊 PillPulse AI

> **Scan. Verify. Protect.**
> Transforming handwritten prescriptions into smart medication schedules with zero manual entry.

![PillPulse](https://img.shields.io/badge/PillPulse-AI%20Healthcare-2E75B6?style=for-the-badge)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react)
![Flask](https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask)
![Firebase](https://img.shields.io/badge/Notifications-Firebase%20FCM-FFCA28?style=for-the-badge&logo=firebase)
![Vercel](https://img.shields.io/badge/Hosted-Vercel-000000?style=for-the-badge&logo=vercel)

---

## 🌐 Live Demo

| Service | URL |
|---------|-----|
| Frontend | [pill-pulse-172010-rhl4.vercel.app](https://pill-pulse-172010-rhl4.vercel.app) |
| Backend API | Render (Flask) |

---

## 🚀 What is PillPulse?

PillPulse is an AI-powered medication adherence platform built for India's 320 million chronically ill patients. It bridges the gap between prescription OCR systems that stop at text extraction and reminder apps that require manual entry — no existing system connects both endpoints.

**The problem it solves:**
- Only **15.8%** of hypertensive Indians take medicines correctly
- **69%** of re-hospitalizations are caused by medication non-adherence
- **24%** of handwritten prescriptions are illegible
- **150 million** clarification calls made annually due to illegible prescriptions

---

## ✨ Key Features

### 🔬 Core
- **Prescription OCR** — Upload a handwritten prescription photo, AI extracts medicine names, dosage, frequency and duration
- **Zero Manual Entry** — BD/TDS/OD/AC/PC/HS shorthand auto-converted to exact clock times
- **Confidence Scoring** — Every detected medicine shows a confidence score; low confidence fields flagged for patient review
- **Drug Conflict Auto-Spacing** — Minimum safe inter-dose intervals computed and scheduled automatically

### 🔔 Notifications
- **FCM Push Notifications** — Real-time browser push notifications on Android Chrome
- **Service Worker** — Notifications fire even when the browser tab is closed
- **3-Action Notifications** — ✅ Taken | ⏰ Snooze 15min | ❌ Skip

### 🚨 Escalation Chain
- Skip once → Patient reminded again after 15 minutes
- Skip twice → **Caregiver notified instantly** on their device
- All events logged to dose history dashboard
- DEV MODE — escalates in 10 seconds for live demos

### 👨‍👩‍👧 Dual User System
- **Patient** generates a unique code (e.g. `JOSH-4521`)
- **Caregiver** enters patient code on their own device
- Two separate devices, two separate notification streams, one linked system

### 📊 Dashboard
- Dose history with Taken / Missed / Escalated status
- Weekly adherence percentage bar
- Refill reminders before medicines run out
- Caregiver dashboard auto-refreshes every 30 seconds

### 🏥 Additional Features
- **Symptom Checker** — AI-powered symptom analysis
- **Hospital Locator** — Nearby government hospitals in Chennai on interactive Leaflet.js map
- **Healthcare Actions** — Book appointments, order medicine, telehealth services
- **Animated Splash Screen** — Premium onboarding experience

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Tailwind CSS |
| Backend | Python Flask + REST API |
| Notifications | Firebase Cloud Messaging (FCM) |
| Service Worker | firebase-messaging-sw.js |
| Automation | n8n workflow engine |
| Maps | Leaflet.js + OpenStreetMap |
| Hosting (Frontend) | Vercel |
| Hosting (Backend) | Render |
| Version Control | GitHub |

---

## 📁 Project Structure

```
PillPulse_172010/
├── src/
│   ├── components/
│   │   ├── PrescriptionUpload.tsx    # OCR upload + schedule generation
│   │   ├── Dashboard.tsx             # Patient dose history
│   │   ├── CaregiverDashboard.tsx    # Caregiver monitoring view
│   │   ├── HospitalMap.tsx           # Leaflet.js hospital locator
│   │   ├── SplashScreen.tsx          # Animated loading screen
│   │   └── Onboarding.tsx            # Patient / Caregiver role selection
│   ├── escalationEngine.js           # Skip → remind → escalate logic
│   ├── firebase.js                   # FCM token + permission handling
│   └── App.tsx                       # Main router
├── public/
│   └── firebase-messaging-sw.js      # Background notification handler
├── backend/
│   ├── app.py                        # Flask API
│   ├── requirements.txt              # Python dependencies
│   └── Procfile                      # Render deployment config
├── n8n/
│   ├── medication-reminder.json      # Cron-based reminder workflow
│   ├── refill-prediction.json        # Refill alert workflow
│   └── dose-status-tracker.json     # Missed dose workflow
└── README.md
```

---

## ⚙️ Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- Firebase project with FCM enabled

### 1. Clone the repo
```bash
git clone https://github.com/Joshuamathewj2/PillPulse_172010.git
cd PillPulse_172010
```

### 2. Install frontend dependencies
```bash
npm install
```

### 3. Install backend dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 4. Set up environment variables

Create `.env` in the root folder:
```env
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_MESSAGING_ID=your_messaging_sender_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_FIREBASE_VAPID_KEY=your_vapid_key
VITE_API_URL=http://localhost:5000
```

Create `backend/.env`:
```env
FCM_SERVER_KEY=your_fcm_server_key
PORT=5000
```

### 5. Run both servers

**Terminal 1 — Frontend:**
```bash
npm run dev
```

**Terminal 2 — Backend:**
```bash
cd backend
python app.py
```

App runs at: `http://localhost:5173`

---

## 🔔 How Notifications Work

```
Patient uploads prescription
        ↓
AI extracts medicines → schedule generated
        ↓
Patient clicks "Add to Medication Schedule"
        ↓
FCM permission requested → token stored
        ↓
setTimeout fires at exact medicine time
        ↓
Notification: ✅ Taken | ⏰ Snooze | ❌ Skip
        ↓
Skip 2× → POST /api/notify-caregiver
        ↓
Caregiver's FCM token receives alert instantly
```

---

## 🧪 Demo Mode

Toggle **DEV MODE** (bottom right corner) to run the full escalation chain in **10 seconds** instead of 15 minutes — perfect for live demos and presentations.

```
DEV MODE ON:
Skip limit     = 2 (not 3)
Escalation     = 10 seconds (not 15 minutes)
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/predict` | Upload prescription image → extract medicines |
| POST | `/api/register-patient` | Register patient with FCM token |
| POST | `/api/register-caregiver` | Link caregiver to patient code |
| POST | `/api/notify-caregiver` | Send escalation alert to caregiver |
| POST | `/api/log-dose` | Log taken / skipped / missed event |
| GET | `/api/patient-status` | Get patient dose log for caregiver dashboard |
| POST | `/api/schedule` | Register medication schedule |
| POST | `/api/send-reminders` | Trigger reminders (called by n8n cron) |

---

## 🗺️ Roadmap

- [x] Prescription upload + OCR demo
- [x] Auto schedule generation from shorthand
- [x] FCM push notifications on Android Chrome
- [x] Escalation chain — patient → caregiver
- [x] Dual user system with patient code
- [x] Dose history dashboard
- [x] Hospital locator with Leaflet.js
- [x] Vercel + Render deployment

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🏆 Built At

This project was built for a Healthcare AI Hackathon, targeting India's medication non-adherence crisis affecting 320 million chronically ill patients.

---

<div align="center">
  <strong>💊 PillPulse AI — Scan. Verify. Protect.</strong><br/>
  <em>"Apollo built the highway. PillPulse builds the guardrail."</em>
</div>
