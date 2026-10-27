# CivicFix Campus — Deployment Guide

This describes how to take the project from local dev to a public deployment on
Vercel (frontend) + Render (backend) + MongoDB Atlas (database), with optional
real Gemini AI analysis and optional Cloudinary image storage.

**Status: not yet deployed.** Everything below has been prepared and tested
locally (backend test suite passes, `npm run build` succeeds), but nobody has
created the actual Vercel/Render/Atlas/Gemini/Cloudinary accounts for this
project, so there is no live URL yet. Follow the steps below to get one.

---

## 0. What changed from earlier phases

Two things the project didn't have before are now built:

- **Real Gemini vision analysis.** When `GEMINI_API_KEY` is set, `/reports`
  sends the actual uploaded photo to Gemini and uses its assessment. When the
  key is unset, or Gemini errors/times out/hits a quota limit, it
  transparently falls back to the existing deterministic mock provider — a
  report submission never fails just because AI is unavailable. **This has
  not been tested against the real Gemini API** (no network path to Google's
  API from the environment that built this) — test it yourself as the very
  first thing after deploying (see Section 10, "the real-AI test").
- **Real multi-campus isolation.** There are now two campuses (`Main Campus`,
  `North Gate Campus`), each with its own demo student and admin account.
  Every database read/write is scoped by `campus_id` on the backend — a
  North Gate student or admin cannot see, assign, or resolve a Main Campus
  report, even by guessing its ID. Covered by an automated test
  (`test_campus_isolation`).

## 1. Prerequisites

- Node.js 20+, Python 3.11+
- A GitHub account (to host the repo Vercel/Render deploy from)
- Accounts for whichever of these you want to use (all have a free tier as of
  Aug 2026 — verify current limits before relying on them, they change):
  - [Vercel](https://vercel.com) — frontend hosting
  - [Render](https://render.com) — backend hosting
  - [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) — database (optional;
    the app runs fine on the in-memory repository for a demo, but data is
    lost on every restart)
  - [Google AI Studio](https://aistudio.google.com/apikey) — Gemini API key
    (optional; mock analysis is used without it)
  - [Cloudinary](https://cloudinary.com) — persistent image storage
    (optional; local disk is used without it, which does **not** survive a
    Render redeploy)

## 2. GitHub setup

```bash
cd CivicFix-Campus-Phase5
git init
git add .
git commit -m "Prepare CivicFix Campus for deployment"
git branch -M main
git remote add origin https://github.com/<your-username>/civicfix-campus.git
git push -u origin main
```

Before pushing, double check nothing secret is staged:

```bash
git grep -niE "AIza|mongodb\+srv://|api_key\s*=|secret\s*="  -- ':!*.md' ':!**/node_modules/**'
```

This should return nothing (a fresh scan of this repo as of writing found no
committed credentials — `.env` files are git-ignored and only `.env.example`
placeholders are tracked).

## 3. MongoDB Atlas setup (optional but recommended)

1. Create a free (M0) cluster.
2. Database Access → Add New Database User → username/password, read/write
   scoped to this project's database only (least privilege — don't reuse an
   admin user).
3. Network Access → Add IP Address → for Render specifically, allow
   `0.0.0.0/0` (Render's outbound IPs aren't static on the free tier) *or*
   use Render's static outbound IP add-on if you want to restrict this
   properly. Document whichever you choose in your own notes — it's a
   real security trade-off, not a formality.
4. Connect → Drivers → copy the `mongodb+srv://...` connection string.
5. Put it in Render's `MONGODB_URL` env var (Section 6) — never in the repo.

If you skip this, leave `MONGODB_URL` blank and the app uses its in-memory
fallback (fine for a demo, not for anything you need to persist).

## 4. Gemini API setup (optional but requested)

1. Go to https://aistudio.google.com/apikey and create a key.
2. **Do not** put it in any `VITE_`-prefixed variable or any frontend file —
   only in the backend's `GEMINI_API_KEY` env var on Render.
3. Model: `GEMINI_MODEL=gemini-2.5-flash` is the current default here. It has
   a scheduled shutdown of **Oct 16, 2026** — check
   https://ai.google.dev/gemini-api/docs/models before/after that date and
   update the env var if it's been retired.
4. Free tier quotas change — check current limits on the pricing page before
   assuming this stays free at scale.

## 5. Cloudinary setup (optional, recommended for production)

1. Free signup at https://cloudinary.com — no credit card required.
2. Dashboard → copy Cloud Name, API Key, API Secret.
3. Put them in Render's `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` /
   `CLOUDINARY_API_SECRET` env vars.
4. If you skip this, uploaded images are written to the backend's local
   `uploads/` folder, which is **wiped on every Render redeploy or restart**.
   That's fine for a first demo, not for a production deployment — images
   will silently disappear.

## 6. Backend deployment (Render)

1. New → Web Service → connect your GitHub repo.
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   (Render sets `$PORT` automatically — don't hard-code 8000.)
5. Or just use the included `backend/render.yaml` blueprint (New → Blueprint
   → point it at this repo) — it pre-fills the build/start commands and
   marks every secret-bearing env var `sync: false` so Render prompts you to
   type them in rather than storing them in the repo.
6. Environment variables (Render dashboard → Environment):

   | Key | Required | Notes |
   |---|---|---|
   | `MONGODB_URL` | optional | blank = in-memory fallback |
   | `MONGODB_DB` | optional | default `civicfix_campus` |
   | `JWT_SECRET` | **yes** | generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `FRONTEND_ORIGIN` | **yes** | your exact Vercel URL, no trailing slash |
   | `GEMINI_API_KEY` | optional | blank = mock analysis only |
   | `GEMINI_MODEL` | optional | default `gemini-2.5-flash` |
   | `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | optional | blank = local disk (ephemeral) |

7. Deploy, then check `https://<your-service>.onrender.com/health` returns
   `{"status":"ok",...}`.

## 7. Frontend deployment (Vercel)

1. New Project → import the same GitHub repo.
2. Root directory: `frontend`
3. Framework preset: Vite (auto-detected; `frontend/vercel.json` pins the
   build command/output directory explicitly too).
4. Environment variable: `VITE_API_URL` = your Render backend URL (no
   trailing slash), e.g. `https://civicfix-campus-api.onrender.com`.
5. Deploy. Vercel gives you a URL like `https://civicfix-campus.vercel.app`.
6. **Go back to Render and set `FRONTEND_ORIGIN` to this exact URL**, then
   redeploy the backend — until you do, CORS will block every request from
   the deployed frontend.

## 8. CORS

`backend/app/main.py` allows exactly one origin, read from `FRONTEND_ORIGIN`
— never `allow_origins=["*"]`. If you need a second origin (e.g. testing a
preview deploy), that requires a small code change (a list instead of a
single string); this hasn't been added since it wasn't asked for and widens
the attack surface unnecessarily for a two-service demo.

## 9. Image storage

Covered in Section 5. Recap: set the three `CLOUDINARY_*` vars for
persistent storage, or accept that local-disk images vanish on every Render
redeploy. There's no in-between option implemented, and no paid storage
service was added (per the free-tier requirement).

## 10. Production testing checklist

Run these against the real deployed URLs, not localhost:

- [ ] Open the Vercel URL, confirm the login screen renders
- [ ] Log in as each of the 4 demo accounts (2 campuses × student/admin)
- [ ] Submit a report with a real photo as a Main Campus student
- [ ] **The real-AI test**: with `GEMINI_API_KEY` set, submit a report with an
  actual photo of a real-world problem (e.g. a pothole) and confirm in the
  response that `ai_provider` is `gemini-vision-v1`, not
  `mock-explainable-v1`. If it's the mock provider, something's misconfigured
  or Gemini errored — check Render's logs (never the API response, which
  never includes internal error detail).
- [ ] Confirm severity/confidence/safety-risk/recommended-action look
  plausible for that photo — do not just assume it worked
- [ ] Log in as a North Gate student/admin and confirm the Main Campus report
  is **not** visible on the dashboard, admin queue, or map/analytics feeds
- [ ] Resolve/assign a report as the correct-campus admin; confirm a
  wrong-campus admin gets 404 on the same report ID
- [ ] Submit a near-duplicate report and confirm the duplicate-check surfaces
  it
- [ ] Support an existing report and confirm its priority score updates
- [ ] Refresh the page after login (confirms the JWT round-trips correctly
  cross-origin)
- [ ] Open on a phone browser and confirm the layout holds up
- [ ] Turn off `GEMINI_API_KEY` (or use an invalid one) temporarily and
  confirm report submission still succeeds via the mock fallback

## 11. Security checklist

- [x] No secrets committed (verified — see Section 2's grep)
- [x] `GEMINI_API_KEY` only ever read from backend env, never sent to/from
  the frontend
- [x] CORS restricted to the single configured frontend origin
- [x] Campus isolation enforced server-side on every read/write path, with
  an automated regression test
- [x] File upload validated by content-type and size before anything touches
  disk or Gemini
- [x] API errors return generic messages; internals only go to server logs
  (`logger.warning`/`logger.error`, never `response` bodies)
- [ ] **You still need to**: rotate `JWT_SECRET` from the example default,
  set a real one on Render, and never commit `.env`
- [ ] **You still need to**: decide on Atlas network-access scope (open vs.
  static-IP) per Section 3 — this wasn't decided for you
- [ ] Known gap: demo accounts use plaintext passwords in source
  (`backend/app/auth.py`) — acceptable for a labeled college prototype with
  fake accounts, not for anything with real user data. `pwdlib` is already a
  dependency and `hash_password`/`verify_password` helpers now exist in
  `auth.py` for when this moves to persisted, hashed accounts.

## 12. Free-tier / cost information

As of Aug 2026, Vercel, Render, MongoDB Atlas (M0), and Cloudinary all offer
a free tier suitable for a demo/prototype at this scale. Render's free web
services spin down after inactivity and take ~30–60s to wake on the next
request — expect a slow first load after idle periods. Gemini's free tier
has rate limits that change; check the current pricing page rather than
assuming. None of this is guaranteed to stay free — re-verify before a
demo that matters.

## 13. Known limitations

- Demo accounts are hardcoded, not a real user-registration system
- Gemini integration is untested against the live API (see Section 0)
- Only one frontend origin is allowed by CORS at a time
- Cloudinary upload failures fall back to local disk silently (logged, not
  surfaced to the end user) rather than failing the whole report
- The "re-analyze" endpoint (`POST /reports/{id}/analyze`) still only uses
  the mock provider, since it doesn't have the original image bytes on hand
  without re-fetching them from storage — a real re-analysis feature would
  need that fetch added

## 14. Troubleshooting

- **CORS error in browser console**: `FRONTEND_ORIGIN` on Render doesn't
  exactly match the Vercel URL (check for trailing slash / http vs https).
- **401 on every request after login**: `JWT_SECRET` differs between what
  issued the token and what's validating it — usually means Render
  redeployed with a new auto-generated secret; log in again.
- **Images 404 after a Render redeploy**: you're on local-disk storage (no
  Cloudinary configured) — see Section 5.
- **`ai_provider` is always `mock-explainable-v1`**: `GEMINI_API_KEY` is
  unset, invalid, or Gemini is erroring — check Render logs for the specific
  `GeminiAnalysisError` reason (never logged with the key itself).
- **`/health` returns `"storage":"memory"` even though `MONGODB_URL` is
  set**: the connection failed at startup (bad URI, Atlas network-access
  rule not covering Render's egress); check Render's build/deploy logs.

## 15. Final public URLs

Not filled in — no deployment has been performed yet. Once you've completed
Sections 6–7, put your actual URLs here for your own records:

- Frontend: _(pending)_
- Backend: _(pending)_
- Backend health check: _(pending)_/health
