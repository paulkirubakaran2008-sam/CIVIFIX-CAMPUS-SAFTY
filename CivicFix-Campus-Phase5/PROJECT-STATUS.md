# Project Status

Honest snapshot of what is and isn't finished. Kept separate from the
README so nobody has to guess which features are real, which are stubs, and
which have never been tested.

**Overall: roughly 45-50% of the original deployment brief is complete.**

The application itself works. The deployment goal — a live, publicly
accessible URL — has not been reached.

---

## Done and verified

These were tested locally and pass.

| Item | Evidence |
|---|---|
| Core app: report submission, auth, admin queue, map, analytics, predictions | Existing Phase 1-5 work, runs locally |
| Multi-campus data isolation | Enforced in `backend/app/repository.py`; covered by `test_campus_isolation` in `backend/tests/test_api.py` |
| Backend test suite | 8/8 passing |
| Frontend production build | `npm run build` succeeds |
| Deployment config files | `backend/render.yaml`, `frontend/vercel.json`, both `.env.example` files |
| Documentation | `README.md`, `DEPLOYMENT.md`, `SETUP.md` |
| Secret hygiene | No credentials committed; `.env`, `.venv`, `node_modules`, `uploads/` all gitignored and confirmed excluded |
| Environment-driven config | No hardcoded localhost/ports/keys in production paths; CORS reads from `FRONTEND_ORIGIN` |

## Coded but NOT verified

Written against current official documentation, but never executed against
the real service. Treat as unproven until tested.

| Item | Why unverified |
|---|---|
| **Gemini vision analysis** (`backend/app/services/gemini_analysis.py`) | Has never made a live call to Google's API. Needs a real `GEMINI_API_KEY` and a real photo to confirm. If it fails, the app silently falls back to the mock provider — so check that `ai_provider` returns `gemini-vision-v1`, not `mock-explainable-v1`. |
| **Cloudinary image storage** (`backend/app/services/image_storage.py`) | Never tested against a real Cloudinary account. Inactive unless the three `CLOUDINARY_*` env vars are set. |

## Not done

| Item | Status |
|---|---|
| **Actual deployment to Vercel / Render / MongoDB Atlas** | **0%.** No accounts created, no live URL exists. This is the brief's primary stated goal. |
| Production test plan (16 checks in `DEPLOYMENT.md`) | 0% — cannot run against a non-existent deployment |
| Rate limiting on AI endpoints | Not implemented |
| SEO / page metadata | Not implemented |
| Systematic production logging pass | Partial — logging added only for the new Gemini and storage paths |
| Responsive testing on real devices | Not done |
| Git history secret scan | N/A — repo has no prior history; current files scanned clean |

## Known limitations

- **Demo accounts use plaintext passwords** in `backend/app/auth.py`. Acceptable
  for four clearly-labelled fake accounts in a college prototype; not
  acceptable for real users. `pwdlib` is already a dependency and
  `hash_password`/`verify_password` helpers exist in that file for when this
  moves to persisted, hashed accounts.
- **Images vanish on redeploy** unless Cloudinary is configured. The local-disk
  fallback writes to `backend/uploads/`, which is wiped on every Render
  restart.
- **Cloudinary failures fall back silently** to local disk. Logged for
  operators, not surfaced to the end user.
- **CORS allows exactly one origin** at a time. Adding a second (e.g. a preview
  deploy) requires a small code change.
- **`POST /reports/{id}/analyze` only uses the mock provider**, since it doesn't
  have the original image bytes without re-fetching them from storage.
- **Free-tier limits change.** Verify current terms on each provider's pricing
  page before relying on them. Render's free web services also sleep after
  inactivity, causing a 30-60s cold start.

## Next steps

See `DEPLOY-PROMPT.md` for a step-by-step plan to complete the deployment on
free tiers. The two highest-value actions:

1. Create the Render / Vercel / Atlas accounts and deploy — the single
   biggest remaining gap.
2. Run the real-AI test (`DEPLOYMENT.md` section 10) to confirm Gemini
   actually works end to end, rather than silently falling back.
