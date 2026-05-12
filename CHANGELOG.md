# Changelog

All notable changes to Lumen will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-05-13

### Added
- Cloud LLM backend via **Groq** as an alternative to local Ollama. Selectable through `LUMEN_BACKEND` env var (`groq` | `ollama`). Default model on Groq is `llama-3.1-8b-instant`; on Ollama it is `gemma4`.
- `python-dotenv` auto-loads `backend/.env` on startup so config lives in one place rather than being sourced per shell.
- `backend/.env.example` as a safe-to-commit template.
- **PWA** wrap of the frontend via `vite-plugin-pwa`: web app manifest, service worker (autoUpdate), `theme-color`, Apple-specific meta tags, and SVG icons (regular + maskable). Installable on Android Chrome and desktop Chrome/Edge.
- Workbox runtime caching: app shell precached, GET `/api/*` requests served `NetworkFirst` with a 4s timeout. POST/PATCH/DELETE stay network-only so logged data never replays from stale cache.
- **Dashboard** now surfaces protein, carbs, fats, and fiber totals alongside calories. Previously macros were only visible inside the chat reply.

### Changed
- `backend/llm.py` rewritten around a dispatch on `LUMEN_BACKEND`. Both paths share the same `chat_json` / `chat_plain` surface so route code is backend-agnostic.
- Image inputs on text-only models (Groq Llama 3.1 8B) now append an inline note instead of returning 500.
- `.gitignore` widened to catch `.env`, `.env.*`, and bare `env` filename variants (including the accidental `backend/env` PowerShell file).

### Security
- Earlier development pasted a Groq API key into chat history. **Rotate that key** at https://console.groq.com/keys and replace the value in `backend/.env`. The new `.gitignore` rules prevent that file from being tracked.

## [0.1.0] - 2026-05-12

### Added
- Initial scaffold of the **Lumen** prototype.
- **Backend** — FastAPI + SQLAlchemy + SQLite + Ollama (Gemma 3n / 4). Routes for `/api/setup`, `/api/profile`, `/api/chat`, `/api/food`, `/api/weight`, `/api/measurements`.
- **Frontend** — React (Vite) + Tailwind + Recharts + react-router. Pages: `/setup`, `/` (Dashboard), `/tracker` (Calories / Weight / Body Measurements tabs), `/chat`.
- **Chat LLM contract:** the model replies with a single JSON object — `intent`, `reply_markdown`, `food_entries`, `follow_up_options`. Backend persists `food_entries` atomically with the assistant reply, so a calorie log message becomes DB rows on the same turn.
- **Persistent user profile** in `backend/user_profile.json`. Holds static fields (calorie goal, biometrics, meal section labels, measurement type labels) and dynamic LLM-inferred facts (dietary preferences, cooking capabilities, meal patterns, food restrictions).
- **Async profile learning loop:** after each chat turn the backend asks the LLM for a JSON patch of new durable facts and merges it into `user_profile.json` list-additively. Runs as a FastAPI `BackgroundTask` so failures never block the user-visible reply.
- README with Ollama setup, model pull instructions, run commands.
