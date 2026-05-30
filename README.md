# 📚 Multi-PDF RAG Chat System
### 100% FREE — No credit card, no paid API

Chat with your PDF documents using Google Gemini AI — completely free.

## 🆓 Why It's Free

| Component | Service | Cost |
|-----------|---------|------|
| LLM (chat) | Google Gemini 2.0 Flash | **FREE** (1,500 req/day) |
| Embeddings | Google text-embedding-004 | **FREE** |
| Vector DB | ChromaDB (local) | **FREE** (runs on your machine) |
| Database | SQLite (local) | **FREE** |
| Backend hosting | Render.com free tier | **FREE** |
| Frontend hosting | Vercel free tier | **FREE** |

**Total cost: $0/month** ✅

---

## 🏗️ Architecture

```
User → React Frontend → FastAPI Backend
                              │
                    ┌─────────┴──────────┐
                    │                    │
              SQLite DB           ChromaDB (local)
            (sessions/docs)      (vector embeddings)
                                         │
                              Google Gemini API (FREE)
                              ├── text-embedding-004
                              └── gemini-2.0-flash
```

## ✨ Features

- 📤 Upload multiple PDFs via drag & drop
- 💬 Chat with your documents using Gemini AI
- 🔍 Semantic search across all PDFs
- 📄 Source citations with page references
- 🗂️ Multiple chat sessions
- 🚀 FastAPI backend with auto Swagger docs
- 🐳 Docker support

---

## 🚀 Quick Start (5 minutes)

### Step 1 — Get your FREE Google API Key

1. Go to **https://aistudio.google.com/apikey**
2. Sign in with your Google account
3. Click **"Create API key"**
4. Copy the key — that's it! No credit card needed.

### Step 2 — Run the project

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/multi-pdf-rag.git
cd multi-pdf-rag

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Add your free API key
cp .env.example .env
# Open .env and set: GOOGLE_API_KEY=your-key-here

# Start backend
uvicorn app.main:app --reload --port 8000
```

Open a new terminal:
```bash
# Frontend setup
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173** 🎉

API docs at **http://localhost:8000/docs**

---

## ☁️ Free Hosting Guide

### Backend → Render.com (Free)

1. Push to GitHub
2. Go to [render.com](https://render.com) → **New Web Service**
3. Connect your GitHub repo
4. Settings:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Environment Variables:
   - `GOOGLE_API_KEY` = your free Gemini key
   - `SECRET_KEY` = any random string
   - `DATABASE_URL` = (leave as sqlite for free, or add Render Postgres)
6. Click **Deploy** ✅

### Frontend → Vercel (Free)

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repo
3. Root Directory: `frontend`
4. Environment Variable: `VITE_API_URL` = `https://your-app.onrender.com`
5. Click **Deploy** ✅

---

## 📁 Project Structure

```
multi-pdf-rag/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── core/config.py       # Settings
│   │   ├── db/
│   │   │   ├── database.py      # SQLAlchemy setup
│   │   │   └── models.py        # Document, Session, Message models
│   │   ├── services/
│   │   │   ├── pdf_processor.py # PDF → text chunks
│   │   │   ├── vector_store.py  # ChromaDB + Gemini embeddings
│   │   │   └── rag_chain.py     # Gemini RAG pipeline
│   │   └── api/routes/
│   │       ├── documents.py     # Upload/manage PDFs
│   │       ├── chat.py          # Chat endpoint
│   │       └── sessions.py      # Session management
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Main chat UI
│   │   └── api/client.js        # API calls
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Description | Where to get |
|----------|-------------|--------------|
| `GOOGLE_API_KEY` | Gemini API key | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `SECRET_KEY` | Random secret string | Run: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | DB connection | Default: SQLite (no setup needed) |

---

## 📊 Free Tier Limits (Gemini)

| Model | Requests/day | Tokens/min |
|-------|-------------|------------|
| gemini-2.0-flash | 1,500 | 1,000,000 |
| text-embedding-004 | generous | very high |

More than enough for personal projects and portfolios!

---

## 🧠 How RAG Works

1. **Upload** → PDF → extract text → split into 512-token chunks
2. **Embed** → each chunk → Gemini embedding vector → stored in ChromaDB
3. **Query** → your question → embed → find top-5 similar chunks
4. **Generate** → chunks + question → Gemini Flash → answer with citations

---

## 📖 API Docs

Once running: `http://localhost:8000/docs`

Key endpoints:
```
POST   /api/v1/documents/upload    # Upload a PDF
GET    /api/v1/documents/          # List all PDFs
DELETE /api/v1/documents/{id}      # Delete a PDF
POST   /api/v1/sessions/           # Create chat session
POST   /api/v1/chat/               # Send message, get AI reply
GET    /api/v1/chat/{id}/history   # Get chat history
```

---

## 📄 License

MIT — free to use, modify, and deploy.
