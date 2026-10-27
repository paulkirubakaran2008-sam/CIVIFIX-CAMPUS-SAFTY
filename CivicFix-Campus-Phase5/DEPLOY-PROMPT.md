# Prompt: finish CivicFix Campus deployment on free tiers

Paste everything below into an agentic coding tool that has terminal access
(Claude Code, Cursor, etc.) with this project folder open. It tells the
agent exactly what's already done, what's left, and where it must stop and
ask you to do something manually (account signups can't be automated by a
text agent — no tool can click "Verify your email" for you).

---

## PROMPT STARTS HERE

You are finishing the deployment of an existing project called CivicFix
Campus. Read this entire prompt before doing anything.

### Constraints (non-negotiable)

- **Zero budget.** Every service used must be on a real free tier. Before
  using any service, verify its current free-tier limits by checking its
  official pricing page — don't assume, they change.
- **Do not fabricate results.** Never say a step succeeded unless you
  actually ran the command and saw success output. Never invent a URL,
  API response, or test result.
- **Do not commit secrets.** No API key, database URI, or password may
  ever appear in a file that gets committed to git. Use `.env` (already
  gitignored) and each platform's environment-variable dashboard instead.
- **Stop and ask me** whenever a step requires creating an account,
  verifying an email, or clicking through a web signup flow. You cannot do
  this for me. When you hit one of these, tell me exactly what to do,
  what to copy afterward (e.g. "copy the connection string and paste it
  back to me"), and wait.

### What's already done (do not redo this)

- Full-stack app (React/Vite frontend, FastAPI backend) is built and
  working locally
- Real Gemini vision-analysis integration is coded in
  `backend/app/services/gemini_analysis.py`, with automatic fallback to a
  mock provider — but it has **never been tested against the live Gemini
  API**. This must be the first thing verified once a key exists.
- Multi-campus data isolation is built and covered by an automated test
  (`backend/tests/test_api.py::test_campus_isolation`)
- Optional Cloudinary image storage is coded in
  `backend/app/services/image_storage.py`, inactive until 3 env vars are
  set
- `backend/render.yaml`, `frontend/vercel.json`, both `.env.example`
  files, and `DEPLOYMENT.md` already exist with the exact steps and env
  var names required

### What's left — do these in order

**1. Local sanity check.** Run the backend test suite
(`cd backend && pip install -r requirements.txt && pytest`) and the
frontend build (`cd frontend && npm install && npm run build`). Confirm
both succeed before doing anything else. If either fails, fix it and
re-run before proceeding — do not deploy broken code.

**2. Git repository.** Run `git init`, `git add .`, `git commit`. Before
committing, run a secret scan (`git grep -niE "AIza|mongodb\+srv://|api_key\s*="`)
and confirm it's empty. Then STOP and ask me to create an empty GitHub
repo and give you its URL, since that requires my GitHub login.

**3. MongoDB Atlas** (free M0 cluster). STOP and ask me to:
   - create a free account at mongodb.com/cloud/atlas
   - create an M0 cluster
   - create a database user (not the account owner) scoped to this
     project's database only
   - allow network access from anywhere (`0.0.0.0/0`) since Render's free
     tier doesn't have a static IP
   - copy me the `mongodb+srv://...` connection string

   Once I give you the string, do NOT put it in any file. Tell me to save
   it for step 5.

**4. Gemini API key.** STOP and ask me to get a free key at
   aistudio.google.com/apikey and give it to you. Same rule: don't write
   it to any file, hold it for step 5. Also check right now whether
   `gemini-2.5-flash` is still available (it had a scheduled Oct 16 2026
   shutdown) and tell me if I need a different `GEMINI_MODEL` value.

**5. Render backend deployment.** STOP and ask me to:
   - create a free Render account, connect it to the GitHub repo from
     step 2
   - deploy `backend/render.yaml` as a Blueprint (New → Blueprint)
   - when it asks for the `sync: false` variables, paste in: the Atlas
     URI from step 3, a freshly generated `JWT_SECRET` (you can generate
     this yourself: `python -c "import secrets; print(secrets.token_hex(32))"`),
     the Gemini key from step 4, and leave `FRONTEND_ORIGIN` blank for now
   - once deployed, give you the resulting `https://*.onrender.com` URL

   Verify it yourself: `curl https://<that-url>/health` and confirm it
   returns `{"status":"ok",...}`.

**6. Vercel frontend deployment.** STOP and ask me to:
   - create a free Vercel account, import the same GitHub repo, set root
     directory to `frontend`
   - set env var `VITE_API_URL` to the Render URL from step 5
   - deploy, then give you the resulting `https://*.vercel.app` URL

**7. Close the loop.** Tell me to go back to Render's dashboard and set
`FRONTEND_ORIGIN` to the exact Vercel URL from step 6, then redeploy the
backend. Confirm with me once you're told this is done.

**8. Optional: Cloudinary.** Ask if I want persistent image storage. If
yes, walk me through the same STOP-and-ask pattern for
cloudinary.com signup, then set the 3 `CLOUDINARY_*` vars on Render.

**9. Real verification — do not skip this.** Once both URLs are live:
   - Open the Vercel URL yourself if you have browser access, or ask me
     to and report back what you/I see
   - Log in with each of the 4 demo accounts (in `README.md`)
   - Submit a report with a real photo. Check whether the response's
     `ai_provider` field says `gemini-vision-v1` or
     `mock-explainable-v1`. If it's the mock, something's misconfigured —
     check Render's logs (ask me to paste them) for the actual
     `GeminiAnalysisError` reason.
   - Confirm a North Gate Campus login cannot see a Main Campus report
   - Report back honestly which of these worked and which didn't. A
     partial success is a fine outcome to report — a false "it all
     works" is not.

**10. Final report.** Give me the actual public URLs, which env vars are
set where, which free-tier limits I should be aware of, and an honest
list of anything still broken or untested.

## PROMPT ENDS HERE
