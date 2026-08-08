# The Drifting Oracle

A full-stack web application built with **React** (Vite) and **FastAPI**.

## Project Structure

```
The-Drifting-Oracle/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py        # Environment-based settings
│   │   ├── main.py          # App factory & CORS setup
│   │   └── routes.py        # API endpoints
│   ├── .env                 # Environment variables
│   └── requirements.txt     # Python dependencies
├── frontend/                # React (Vite) frontend
│   ├── src/
│   │   ├── api.js           # Backend API utility
│   │   ├── App.jsx          # Main application component
│   │   ├── App.css          # Component styles
│   │   ├── index.css        # Global design system
│   │   └── main.jsx         # Entry point
│   ├── index.html
│   ├── vite.config.js       # Dev server & proxy config
│   └── package.json
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`. API calls are proxied to the backend.

## API Endpoints

| Method | Endpoint       | Description             |
| ------ | -------------- | ----------------------- |
| GET    | `/api/health`  | Health check            |
| GET    | `/api/oracle`  | Get an oracle reading   |
