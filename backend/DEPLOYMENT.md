# Deployment Guide: RAG AI Financial Assistant Backend & Netlify Integration

This guide walks you through deploying the **Python FastAPI AI Controller** on a cloud container/server (Render, Railway, or Google Cloud Run) and connecting your existing **Netlify-hosted Frontend**.

---

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│  Netlify Frontend (HTML / CSS / JS)          │
│  https://expence-traker-min.netlify.app       │
└──────────────────────┬───────────────────────┘
                       │ 1. Firebase Auth Token
                       │ 2. POST /chat or GET /user/financial-summary
                       ▼
┌──────────────────────────────────────────────┐
│  FastAPI AI Controller (Render / Railway)    │
│  https://your-ai-controller.onrender.com      │
│  ├── Token Verification (Firebase Admin)     │
│  ├── Hybrid RAG & Financial Tools            │
│  ├── ChromaDB Vector Store (Persistent Disk) │
│  └── Google Gemini 1.5 Flash LLM             │
└──────────────────────┬───────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌──────────────────┐       ┌──────────────────┐
│ Cloud Firestore  │       │ Google Gemini    │
│ (yourmemo-9dec5) │       │ Generative AI    │
└──────────────────┘       └──────────────────┘
```

---

## 1. Hosting the Python Backend (e.g. Render / Railway / Fly.io)

### Step 1: Environment Variables on Cloud Host
Set the following environment variables in your cloud provider's dashboard:

| Variable | Recommended Value / Description |
|---|---|
| `ENVIRONMENT` | `production` |
| `PORT` | `8000` (or host provided `$PORT`) |
| `HOST` | `0.0.0.0` |
| `CORS_ORIGINS` | `https://expence-traker-min.netlify.app` *(Never use `*` when authorization headers are present)* |
| `GEMINI_API_KEY` | `AIzaSy...` (Your Google Gemini API Key from Google AI Studio) |
| `GEMINI_MODEL` | `gemini-1.5-flash` |
| `FIREBASE_PROJECT_ID` | `yourmemo-9dec5` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Single-line JSON string of your Firebase Service Account Private Key |
| `CHROMA_PERSIST_DIRECTORY` | `/data/chroma_db` (or persistent disk mount path) |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` |

> **Security Note:** In production, do not commit `firebase-service-account.json` to GitHub. Paste the JSON contents directly into the `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable on Render/Railway.

### Step 2: Build & Start Command
- **Build Command**:
  ```bash
  pip install --upgrade pip && pip install --prefer-binary -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

### Step 3: Persistent Storage for ChromaDB
- On Render or Railway, attach a **Persistent Volume/Disk** mounted at `/data`.
- Set `CHROMA_PERSIST_DIRECTORY=/data/chroma_db`.

---

## 2. Connecting the Frontend on Netlify

### Step 1: Set the Backend URL
In `dashboard/dashboard.js`, the AI Assistant connects using `window.AI_API_BASE_URL`.
By default, it checks:
```javascript
window.AI_API_BASE_URL = window.AI_API_BASE_URL || 'http://localhost:8000';
```

To point your live Netlify deployment to your production backend, you can simply declare it before `dashboard.js` in `dashboard/dashboard.html`:
```html
<script>
    // Set Production AI Controller URL
    window.AI_API_BASE_URL = "https://your-ai-controller.onrender.com";
</script>
<script src="dashboard.js"></script>
```

Or configure Netlify redirect proxy in `netlify.toml`:
```toml
[[redirects]]
  from = "/api/*"
  to = "https://your-ai-controller.onrender.com/:splat"
  status = 200
  force = true
  headers = {X-From = "Netlify"}
```

---

## 3. Production Verification Checklist

1. **Health Check**:
   ```bash
   curl -X GET "https://your-ai-controller.onrender.com/health"
   ```
   *Expected Response:*
   ```json
   {
     "status": "healthy",
     "service": "AI Expense Tracker Controller",
     "environment": "production",
     "gemini_configured": true,
     "firebase_project": "yourmemo-9dec5"
   }
   ```

2. **CORS Check**:
   Confirm that making a request from `https://expence-traker-min.netlify.app` returns:
   `Access-Control-Allow-Origin: https://expence-traker-min.netlify.app`.

3. **Authentication Check**:
   Confirm that calling `POST /chat` without an Authorization header returns `401 Unauthorized`.
