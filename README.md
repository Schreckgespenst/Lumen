# Lumen

> Local-LLM-powered personal health & fitness tracker. Web prototype to validate logic and LLM behaviour before going mobile.

Stack: **FastAPI + SQLite + Ollama (Gemma)** on the backend, **React (Vite) + Tailwind + Recharts** on the frontend.

The name plays on the model giving "light" to your numbers — a small, local assistant that reads your profile and your day, and tells you what it means.

---

## How it works

- A persistent `backend/user_profile.json` stores static profile fields **and** dynamic facts the LLM learns about you over time (dietary preferences, cooking capabilities, meal patterns, restrictions). It is injected as system context on every chat call — much like a project's `CLAUDE.md`.
- The chat endpoint asks the model to reply with a **single JSON object**: an `intent`, a markdown reply, a list of `food_entries`, and `follow_up_options`. When the intent is `calorie_log`, the backend persists the entries to `food_log` automatically — no separate parsing step.
- A second, async LLM call inspects each conversation turn for new durable facts and patches `user_profile.json`. It fails gracefully so it never blocks the user-visible reply.

---

## Prerequisites

1. **Ollama** — https://ollama.com/download
2. A Gemma model. The shipped default is `gemma4` (matches your existing `gemma_test.py`). Override with `LUMEN_MODEL` env var if you have a different tag.

   ```powershell
   ollama pull gemma3n:e4b      # multimodal, ~7GB, recommended
   # or
   ollama pull gemma3n:e2b      # smaller fallback
   ollama serve                  # if not already running
   ```

   Then either tag it to match the default name or set the env var:

   ```powershell
   $env:LUMEN_MODEL = "gemma3n:e4b"
   ```

3. **Python 3.11+** and **Node 20+**.

---

## Run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

> Run uvicorn from the project root (one level above `backend/`) so the `backend.` package imports resolve. Health check: http://localhost:8000/api/health

Generated files (gitignored):
- `backend/lumen.db` — SQLite database
- `backend/user_profile.json` — the JSON profile (auto-created)

## Run the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api/*` to `http://localhost:8000`.

First load redirects to **/setup** until you save a profile.

---

## Pages

- `/setup` — onboarding form. Editable later from the **Settings** link in the header.
- `/` — dashboard with today's kcal-vs-goal bar and protein total.
- `/tracker` — three tabs:
  - **Calories** — per-meal lists for the selected date, quick-add form.
  - **Weight** — chart with 7d / 30d / all-time filters, log + history.
  - **Body Measurements** — one chart per measurement type, log form.
- `/chat` — free-form chat. Natural language meal logs are parsed by the LLM and written to the DB on the same turn. Follow-up suggestions appear as clickable chips.

---

## API surface

```
POST   /api/setup
GET    /api/profile
PATCH  /api/profile

POST   /api/chat
GET    /api/chat/history
DELETE /api/chat/history

POST   /api/food
GET    /api/food?date=YYYY-MM-DD
DELETE /api/food/{id}

POST   /api/weight
GET    /api/weight
PATCH  /api/weight/{id}
DELETE /api/weight/{id}

POST   /api/measurements
GET    /api/measurements
PATCH  /api/measurements/{id}
DELETE /api/measurements/{id}
```

---

## Known limitations & next steps

- **Single user, no auth.** All entries use `user_id=1`.
- **Strict JSON output depends on the model.** Gemma `e4b` is much more reliable than `e2b` for the structured calorie format. The backend falls back to a plain markdown reply (with no DB writes) when JSON parsing fails — so a weaker model is degraded, not broken.
- **Multimodal food photos** route through Ollama's `images` channel. Quality depends entirely on the underlying model — treat the first numbers it gives as a starting estimate, not gospel.
- **No external nutrition database.** All estimates come from the LLM, so verify before trusting macros on edge-case foods.
- **Profile-learning loop is experimental.** Async, best-effort, list-additive only — it won't drop facts unexpectedly, but it can grow the profile with low-signal entries over time. Inspect `backend/user_profile.json` and prune as needed.
- **Toward mobile:** the API is already split from the UI, so a React Native or Flutter shell can sit on top of the same FastAPI backend running locally (or on a small VPS / on-device with `llama.cpp`).
