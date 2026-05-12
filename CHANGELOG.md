# Changelog

All notable changes to Lumen will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-05-13

### Added
- Paired **Google Stitch** project + design system (`Lumen Dark`) and high-fidelity mockups for all six current screens: Chat, Dashboard, Setup, and the three Tracker tabs (Calories, Weight, Measurements). The design system is dark-only, accent `#a855f7`, Inter throughout, with the visual language captured in a markdown spec that ships with the asset.
- `.tnum` utility in [`frontend/src/index.css`](frontend/src/index.css) for `font-variant-numeric: tabular-nums`. Applied to every numeric cell in the UI so columns of numbers no longer dance when digits change.

### Changed
- **Typography:** Inter is now the global font, loaded from Google Fonts in [`frontend/index.html`](frontend/index.html). Replaces the prior system-sans stack.
- **Top nav active state:** `NavLink` replaces `Link`; the active route renders in accent purple instead of just hover-grey. Routes reordered to Dashboard / Chat / Tracker / Settings.
- **Dashboard** Today block: section label is uppercase tracking-wide; consumed kcal is `text-3xl` with `Number.toLocaleString()` for comma grouping. Macro grid values use tabular nums.
- **Setup** form: fields are grouped into three sections with subtle dividers labelled "Daily goals" and "Optional", matching the Stitch mockup hierarchy. Visually scaffolded for the missing macro-goal fields (see Notes).
- **Chat** bubble: role label tightened (smaller, wider letter-spacing); padding 12px → 16px; markdown bodies use tabular nums so kcal/macros in the assistant's reply line up.

### Notes
- The Setup form is scaffolded for `protein_g_goal` / `carbs_g_goal` / `fat_g_goal` but the actual inputs aren't wired yet — `backend/schemas.UserSetup` and `backend/models.User` still only carry `calorie_goal`. Wiring those three fields end-to-end is the next move on the long-standing macro-goals item.

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
