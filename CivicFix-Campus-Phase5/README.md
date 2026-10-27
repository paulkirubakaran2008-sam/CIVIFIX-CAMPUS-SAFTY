# CivicFix Campus — Phase 5 + Deployment Prep

**Report. Prioritize. Resolve. Improve.**

Phase 5 added recurring-problem prediction to the Phase 4 foundation. This
pass adds real multi-campus isolation, optional real Gemini vision analysis,
optional persistent image storage, and deployment configuration for
Vercel + Render + MongoDB Atlas. See **[DEPLOYMENT.md](DEPLOYMENT.md)** for
the full deployment walkthrough — this README covers local development.

## Architecture

```text
React + Vite + Tailwind  ──HTTP/Bearer token──>  FastAPI
                                                     │
                                    Gemini vision (if GEMINI_API_KEY set)
                                    ──falls back to── mock analysis
                                                     │
                                              MongoDB (Motor)
                                                     │
                              no MongoDB configured ─┴─> in-memory repository

Uploaded images ──> Cloudinary (if configured) ──else──> local uploads/ folder
```

The repository interface keeps persistence replaceable. MongoDB is used when
`MONGODB_URL` is set; the in-memory repository makes the demo and automated
tests work without a running database. Every read/write is scoped by
`campus_id` at the repository layer, so campus isolation can't be bypassed
by a route forgetting to filter.

## Folder structure

```text
frontend/       React single-page application
backend/app/    API, schemas, authentication, repositories, routes, services
backend/tests/  API tests (including automated campus-isolation coverage)
backend/uploads/ locally stored images (only used when Cloudinary isn't configured)
```

## Features

- Demo student and admin login across **two campuses** (Main Campus, North
  Gate Campus), with server-side isolation between them
- JWT protected API endpoints and role guard
- Dashboard report totals and recent reports
- New report form with image, category, description and campus location
- Image type/size validation (JPEG, PNG, WebP; max 5 MB)
- **Real Gemini vision analysis** when `GEMINI_API_KEY` is set (analyzes the
  actual uploaded photo); automatic fallback to a deterministic, clearly
  labelled mock analysis provider when Gemini is unconfigured, erroring, or
  rate-limited
- Optional persistent image storage via Cloudinary; local-disk fallback for
  development
- MongoDB storage with a local fallback for development/testing
- Severity (1–10), safety risk, people-affected estimate, recommended action
- Explainable 0–100 priority score with a factor-by-factor breakdown (shared
  weighting logic used by both the mock and Gemini providers)
- Duplicate check using category, exact campus location, and description-token similarity
- Support an existing incident; support count increases its priority score
- Protected admin priority queue with assignment and status/resolution-note actions
- Leaflet/OpenStreetMap report markers, coloured by priority
- Analytics API for categories, locations, status, trends and average resolution time
- Explainable recurring-problem prediction endpoint (`GET /predictions`)
- A live frequency-based model when six or more reports exist
- Clearly labelled fictional demo signals when real history is insufficient

### Analysis providers

`GeminiVisionAnalysis` (in `backend/app/services/gemini_analysis.py`) sends
the actual uploaded photo to the Gemini API and asks for a structured JSON
assessment. It is used automatically when `GEMINI_API_KEY` is set, and its
result is tagged `ai_provider: "gemini-vision-v1"`.

`MockVisionAnalysisService` (`backend/app/services/analysis.py`) is the
development fallback: deterministic category profiles plus urgency-word
detection in the description. It does **not** look at the image, and is
tagged `ai_provider: "mock-explainable-v1"`. It's used whenever Gemini is
unconfigured, or automatically as a safety net if Gemini errors, times out,
or hits a quota limit — a report submission never fails just because AI is
unavailable.

Both funnel through a shared priority-weighting module
(`backend/app/services/priority_engine.py`): severity × 30%, safety risk ×
25%, people affected × 20%, supporting reports × 15%, and location
importance × 10%.

## Run locally on Windows

Prerequisites: Node.js 20+, Python 3.11+, and optionally MongoDB Community Server.

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the displayed Vite address (normally `http://localhost:5173`).

For MongoDB, set `MONGODB_URL=mongodb://localhost:27017` in `backend/.env` and create the database automatically on first report. Leaving it blank uses temporary in-memory data.

To use real Gemini analysis locally, also set `GEMINI_API_KEY` in
`backend/.env` (get one at https://aistudio.google.com/apikey). Leaving it
blank uses the mock provider.

Demo accounts:

- Main Campus student: `student@civicfix.edu` / `Student@123`
- Main Campus admin: `admin@civicfix.edu` / `Admin@123`
- North Gate Campus student: `student.north@civicfix.edu` / `Student@123`
- North Gate Campus admin: `admin.north@civicfix.edu` / `Admin@123`

Run API tests:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

## Deploying

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the full Vercel + Render +
MongoDB Atlas + Gemini + Cloudinary walkthrough, environment variable
reference, production testing checklist, and security checklist.

## Known limitations

See the "Known limitations" section of [DEPLOYMENT.md](DEPLOYMENT.md) —
notably, the Gemini integration has not been tested against the live API
from this development environment, and demo accounts use plaintext
passwords in source (fine for labelled fake accounts, not for real users).

## Next phases

Phase 6 covers final testing, UI polish, and completing the actual
Vercel/Render/Atlas deployment once accounts are set up (see DEPLOYMENT.md).

