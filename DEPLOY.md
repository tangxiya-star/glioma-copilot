# Deploy — Vercel (frontend) + Render (backend)

Deploy the **backend first** (to get its public URL), then the frontend.

---

## Part 1 — Backend on Render

1. Go to <https://render.com> → sign in with GitHub.
2. **New +** → **Blueprint** → connect the `tangxiya-star/glioma-copilot` repo.
   Render reads `render.yaml` and creates the `glioma-copilot-api` web service.
3. When prompted, paste the two secrets (copy from your local `.env`):
   - `ANTHROPIC_API_KEY`
   - `DATABASE_URL`
4. Click **Apply / Deploy**. First build takes ~2–4 min.
5. When live, copy the service URL, e.g. `https://glioma-copilot-api.onrender.com`.
6. Verify: open `<that URL>/health` — you should see
   `{"status":"ok","db":true,"models":{...}}`.

> Free tier sleeps after ~15 min idle; the first request after sleep takes ~30–50s
> to wake. Before the demo, hit `/health` once to warm it up.

### Manual fallback (if the Blueprint errors)
New + → **Web Service** → connect repo → set:
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Env vars: `ANTHROPIC_API_KEY`, `DATABASE_URL`, `PYTHON_VERSION=3.11.9`

---

## Part 2 — Frontend on Vercel

1. Go to <https://vercel.com> → sign in with GitHub → **Add New… → Project**.
2. Import `tangxiya-star/glioma-copilot`.
3. **Root Directory**: set to `frontend` (click *Edit* → pick `frontend`).
   Vercel auto-detects Next.js.
4. **Environment Variables** → add:
   - `NEXT_PUBLIC_API_URL` = the Render URL from Part 1 (e.g. `https://glioma-copilot-api.onrender.com`) — **no trailing slash**.
5. **Deploy**. ~1–2 min → you get `https://<something>.vercel.app`.

CORS is already configured to allow any `*.vercel.app` origin, so no backend change needed.

---

## Part 3 — Verify end-to-end

Open the Vercel URL. You should see the app; select a case → **Analyze** →
classification + matched trials; click a trial → fit table. If the trial/analyze
calls fail, check that `NEXT_PUBLIC_API_URL` points at the live Render URL and that
`<render>/health` returns `db:true`.

## Redeploys
Both platforms auto-redeploy on every `git push` to `main`.
