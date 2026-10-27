# CivicFix Campus — Project Review 1 Report

**Student:** Sam Paul Kirubakaran
**Institution:** Rathinam Technical Campus / Rathinam Global University
**Project:** CivicFix Campus — AI-Powered Multi-Campus Problem Resolution Platform
**Repository:** https://github.com/paulkirubakaran2008-sam/civicfix-campus
**Review window:** September 8–17, 2026

---

## 1. Project Overview

CivicFix Campus is a full-stack web application that lets students report
campus maintenance problems (potholes, garbage overflow, broken
streetlights, water leaks, damaged infrastructure) with a photo and
location. Each report is analysed by AI to estimate severity, safety risk,
and the number of people affected, then scored by an explainable priority
engine so campus operations staff can work through a ranked queue instead
of an unordered inbox.

The system supports multiple campuses with enforced data isolation: a
student or administrator at one campus cannot see or act on reports
belonging to another.

**Tagline:** Report. Prioritize. Resolve. Improve.

### Technology stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Leaflet (maps), Recharts (analytics) |
| Backend | Python 3.11+, FastAPI, Uvicorn |
| Database | MongoDB (via Motor async driver), with in-memory fallback |
| AI | Google Gemini vision API, with deterministic fallback provider |
| Auth | JWT bearer tokens, role-based access (student / admin) |
| Image storage | Cloudinary (optional), local filesystem fallback |
| Testing | pytest (8 automated API tests) |

---

## 2. What I Have Completed So Far

### 2.1 Core application (complete and running)

- **Student portal** — dashboard with report totals, submission form with
  image upload, category selection, and campus location
- **Admin portal** — priority-ranked operations queue, report assignment,
  status updates with resolution notes
- **Authentication** — JWT-based login with role guards; admin-only routes
  return 403 to non-admin users
- **Map view** — Leaflet/OpenStreetMap markers colour-coded by priority level
- **Analytics** — breakdowns by category, location, and status; trend data
  and average resolution time
- **Recurring problem prediction** — frequency-based model that activates
  once six or more reports exist; clearly labelled demo signals below that
  threshold

### 2.2 Multi-campus data isolation (complete, automated test passing)

This was the most security-sensitive module. Two campuses exist (Main
Campus and North Gate Campus), each with its own student and admin account.

Isolation is enforced **at the repository layer**
(`backend/app/repository.py`), not in the frontend and not in individual
route handlers. Every read and write funnels through methods that scope
each query by `campus_id`. This means a route cannot accidentally leak
data by forgetting to filter.

Verified by an automated test (`test_campus_isolation` in
`backend/tests/test_api.py`) which asserts that:
- A North Gate student cannot see a Main Campus report in their list
- A North Gate admin cannot see it in the admin queue
- A North Gate admin receives HTTP 404 when trying to assign it **by
  direct ID** (proving the block is server-side, not just UI filtering)
- A Main Campus admin *can* act on it, confirming the filter isn't simply
  blocking everything

### 2.3 Real Gemini AI integration (implemented, pending live verification)

`backend/app/services/gemini_analysis.py` sends the actual uploaded photo
to Google's Gemini vision API and requests a structured JSON assessment
covering category match, confidence, severity, safety risk, people
affected, and a recommended action.

Design decisions worth noting:
- The API key is read **only** from backend environment variables and is
  never exposed to the frontend, placed in any `VITE_` variable, or
  included in any API response
- Gemini error responses are never echoed back to the client, since some
  error payloads can reflect the original request (including the key)
- On any failure — error, timeout, quota exhaustion, or missing key — the
  system falls back automatically to a deterministic mock provider, so
  **report submission never fails because AI is unavailable**
- Every report records which provider analysed it (`gemini-vision-v1` vs
  `mock-explainable-v1`), so results are never misrepresented as real
  vision analysis when they aren't

### 2.4 Explainable priority engine (complete)

Both analysis providers feed into one shared weighting module
(`backend/app/services/priority_engine.py`), producing a 0–100 score from:

| Factor | Weight |
|---|---|
| Severity | 30% |
| Safety risk | 25% |
| People affected | 20% |
| Supporting reports | 15% |
| Location importance | 10% |

The full factor-by-factor breakdown is returned with each report and shown
in the UI, so a priority score is explainable rather than a black box.

### 2.5 Duplicate detection and support (complete)

Before submitting, the app checks for similar existing reports by category,
exact campus location, and description-token similarity. Rather than
creating a duplicate, a student can "support" the existing report, which
increases its support count and recalculates its priority score.

### 2.6 Deployment preparation (complete)

- Environment-variable-driven configuration; no hardcoded ports, URLs,
  credentials, or `localhost` references in production code paths
- CORS restricted to a single configured origin via `FRONTEND_ORIGIN`
  (never `allow_origins=["*"]`)
- `GET /health` endpoint returning service and storage status
- Deployment configs: `backend/render.yaml` (with all secret-bearing
  variables marked `sync: false`) and `frontend/vercel.json` (with SPA
  rewrite so direct route navigation doesn't 404)
- `.env.example` for both frontend and backend, placeholders only
- Hardened `.gitignore`; verified no credentials are committed anywhere
- Persistent image storage via Cloudinary implemented, because Render's
  filesystem is ephemeral and local-disk images would vanish on every
  redeploy

### 2.7 Documentation (complete)

| File | Contents |
|---|---|
| `README.md` | Project overview, architecture, features, local setup, demo accounts |
| `DEPLOYMENT.md` | Full deployment walkthrough, environment variable reference, 16-point production test plan, security checklist, troubleshooting |
| `PROJECT-STATUS.md` | Honest breakdown of what is verified, coded-but-untested, and not started |
| `SETUP.md` | Beginner-friendly setup instructions with batch scripts |

---

## 3. What Is Currently Working

Verified by actually running it, not assumed:

| Check | Result |
|---|---|
| Backend test suite (`pytest`) | **8/8 passing**, including campus isolation |
| Frontend production build (`npm run build`) | **Succeeds** — 2419 modules, no errors |
| Backend server startup | Confirmed running on `http://localhost:8000` |
| `GET /health` endpoint | Returns `{"status":"ok","service":"civicfix-api"}` |
| Frontend dev server | Runs on `http://localhost:5173` |
| Secret scan of repository | **Clean** — no API keys, connection strings, or credentials found |
| Gitignore verification | `.venv`, `node_modules`, `.env`, `uploads/`, `__pycache__` all correctly excluded |

### Demo accounts (for evaluation)

| Campus | Role | Email | Password |
|---|---|---|---|
| Main Campus | Student | student@civicfix.edu | Student@123 |
| Main Campus | Admin | admin@civicfix.edu | Admin@123 |
| North Gate | Student | student.north@civicfix.edu | Student@123 |
| North Gate | Admin | admin.north@civicfix.edu | Admin@123 |

To demonstrate campus isolation: submit a report as the Main Campus
student, then log in as the North Gate admin and confirm it does not
appear.

---

## 4. Pending Work and Next Steps

I am stating these plainly rather than claiming completion.

### 4.1 Implemented but not yet verified against the live service

- **Gemini vision analysis.** The integration is written against current
  official API documentation, but has **never made a live call** to
  Google's API, because the development environment had no network access
  to it. This must be tested with a real API key and a real photograph.
  The correct verification is to check that a submitted report returns
  `ai_provider: "gemini-vision-v1"` and not `"mock-explainable-v1"` — if
  it silently falls back, something is misconfigured.
- **Cloudinary image storage.** Same situation: coded, inactive until the
  three `CLOUDINARY_*` environment variables are set, never tested
  against a real account.

### 4.2 Not started

- **Live public deployment.** The project is deployment-*ready* but is not
  deployed. No Vercel, Render, or MongoDB Atlas accounts have been created
  yet, so there is no public URL. This is the main remaining milestone.
- **Production test plan.** The 16-point checklist in `DEPLOYMENT.md`
  cannot be executed until a deployment exists.
- **Rate limiting** on AI analysis endpoints
- **SEO / page metadata**
- **Responsive testing** on real tablet and mobile devices

### 4.3 Known limitations I intend to address

- **Demo accounts use plaintext passwords** in `backend/app/auth.py`. This
  is acceptable for four clearly-labelled fake accounts in a prototype but
  not for real users. The `pwdlib` library is already a dependency and
  `hash_password` / `verify_password` helper functions already exist in
  that file, ready for migration to persisted, hashed accounts.
- **`POST /reports/{id}/analyze`** currently only uses the mock provider,
  because it does not have the original image bytes without re-fetching
  them from storage.
- **CORS permits one origin at a time**; supporting a preview deployment
  alongside production would require a small code change.

### 4.4 Next steps, in order

1. Create free-tier accounts: MongoDB Atlas (M0 cluster), Google AI Studio
   (Gemini key), Render, Vercel
2. Deploy the backend to Render using the existing `render.yaml` blueprint
3. Deploy the frontend to Vercel, set `VITE_API_URL` to the Render URL
4. Set `FRONTEND_ORIGIN` on Render to the Vercel URL and redeploy (CORS
   will block all requests until this is done)
5. **Run the real-AI test** — submit an actual pothole photograph and
   confirm Gemini genuinely analyses it
6. Execute the full 16-point production test plan, including live
   cross-campus isolation testing
7. Add rate limiting and SEO metadata
8. Migrate demo authentication to hashed, persisted accounts

---

## 5. Honest Self-Assessment

Against the original full project brief, I estimate **45–50% complete**.

The application itself is functional and its most security-sensitive
component — multi-campus isolation — is implemented correctly at the data
layer and backed by an automated test. Deployment configuration and
documentation are thorough.

What is genuinely not finished is the deployment itself, and the live
verification of the Gemini integration. I have deliberately avoided
claiming either of these works, because I have not observed them working.
The code is written and ready; it has not been proven in production.

All cost constraints were respected: every service in the target
architecture (GitHub, Vercel, Render, MongoDB Atlas, Gemini, Cloudinary)
has a free tier, and no paid service was introduced.
