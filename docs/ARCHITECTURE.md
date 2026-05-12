# Lumen — Architecture

A short technical reference covering how the pieces fit together, what guarantees the system makes, and where the seams are if you want to extend it. For setup steps see [the README](../README.md); for a chronological view of changes see [the CHANGELOG](../CHANGELOG.md).

## 1. One-paragraph overview

Lumen is a single-user web app that lets a person log meals, weight, and body measurements in plain language and read back per-meal calorie breakdowns plus daily macro totals. A local backend (FastAPI + SQLite) routes natural-language messages to an LLM (Groq cloud or Ollama local), enforces a strict JSON output contract, persists structured food entries on the same turn, and keeps a profile JSON that the model is grounded against. The frontend is a React PWA that can be installed to the home screen and runs against the same backend.

## 2. Topology

```
┌────────────────────────┐        proxy /api/*         ┌──────────────────────────┐
│  Browser / PWA (React) │ ──────────────────────────► │  FastAPI on :8000        │
│  Vite dev :5173        │                              │   ┌────────────────────┐ │
│  Workbox SW            │                              │   │ routes/            │ │
└────────────────────────┘                              │   │   profile  chat    │ │
                                                        │   │   food  weight     │ │
                                                        │   │   measurements     │ │
                                                        │   └────────────────────┘ │
                                                        │            │             │
                                                        │            ▼             │
                                                        │   ┌────────────────────┐ │
                                                        │   │ SQLite (lumen.db)  │ │
                                                        │   │ user_profile.json  │ │
                                                        │   └────────────────────┘ │
                                                        │            │             │
                                                        │            ▼             │
                                                        │   ┌────────────────────┐ │
                                                        │   │ backend/llm.py     │ │
                                                        │   │  dispatch on       │ │
                                                        │   │  LUMEN_BACKEND     │ │
                                                        │   └────────────────────┘ │
                                                        └──────────────┬───────────┘
                                                                       │
                                                       ┌───────────────┴────────────────┐
                                                       ▼                                ▼
                                              ┌─────────────────┐              ┌─────────────────┐
                                              │ Ollama (local)  │              │ Groq (cloud)    │
                                              │ gemma4 / 3n     │              │ llama-3.1-8b    │
                                              └─────────────────┘              └─────────────────┘
```

## 3. Data model

SQLite, single user (`user_id=1` everywhere). Defined in [`backend/models.py`](../backend/models.py).

| Table | Purpose | Key columns |
|---|---|---|
| `users` | Static biometric/goal fields | `id`, `name`, `calorie_goal`, `height_cm`, `weight_kg`, `sex`, `activity_level` |
| `food_log` | Per-meal items, written by chat and the quick-add form | `date` (YYYY-MM-DD), `meal_type`, `food_name`, `kcal`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `notes` |
| `weight_log` | Numeric weight entries | `weight_kg`, `logged_at` |
| `body_measurements` | Per-type measurements (chest, waist, …) | `measurement_type`, `value`, `unit`, `logged_at` |
| `chat_history` | Full chat transcript | `role`, `content`, `created_at` |

All timestamps stored UTC ISO 8601; converted to local time for display.

Alongside the DB, [`backend/user_profile.json`](../backend/profile_store.py) holds **static** profile fields (a duplicate-by-design copy of the `users` row plus things the user can tune in settings) and **dynamic** LLM-inferred facts (`dietary_preferences`, `cooking_capabilities`, `meal_patterns`, `food_restrictions`, etc.). The JSON file — not the DB row — is what the LLM is grounded against on every chat call.

## 4. The chat happy path

This is the load-bearing flow. Walk it line by line in [`backend/routes/chat.py`](../backend/routes/chat.py).

```
1. POST /api/chat { message, image_b64? }
2. Backend:
     - loads user_profile.json
     - reads today's food_log rows
     - reads the last 7 weight rows
     - builds the system prompt (prompts.py)
     - persists the user message to chat_history
3. llm.chat_json(...) — dispatched to Groq or Ollama
4. Model returns ONE JSON object:
     { intent, reply_markdown, food_entries[], follow_up_options[] }
5. Backend:
     - if food_entries is non-empty, INSERT each row into food_log
     - persists reply_markdown to chat_history
     - schedules profile-learning as a BackgroundTask
     - returns { reply, parsed, follow_up_options, food_entries_added }
6. Frontend re-renders chat and (on next refresh) Dashboard / Calories tab
```

Atomicity: the food rows and the assistant message land in the same request handler, so the user never sees a reply that references items the DB doesn't yet have.

## 5. LLM backend layer

[`backend/llm.py`](../backend/llm.py) hides the choice of provider behind two functions, `chat_json` and `chat_plain`. Selection is at runtime via `LUMEN_BACKEND`:

| Backend | Default model | JSON mode | Multimodal | Notes |
|---|---|---|---|---|
| `groq` | `llama-3.1-8b-instant` | Native `response_format=json_object` | No (8B is text-only) | ~1-3 s per turn, free tier |
| `ollama` | `gemma4` | `format="json"` | Yes (Gemma 3n) | Local, slower, needs disk + RAM |

If an image is attached to a text-only Groq model, the user message is augmented with a polite note rather than the call failing. If the model returns malformed JSON, the wrapper falls back to a plain markdown reply with no DB writes — degraded, not broken.

## 6. The strict chat JSON contract

The system prompt in [`backend/prompts.py`](../backend/prompts.py) demands a single JSON object of shape:

```json
{
  "intent": "calorie_log" | "question" | "general",
  "reply_markdown": "<visible markdown>",
  "food_entries": [
    {
      "date": "YYYY-MM-DD",
      "meal_type": "Breakfast|Lunch|Evening Snack|Dinner|Dessert",
      "food_name": "string",
      "kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0,
      "notes": "assumption note"
    }
  ],
  "follow_up_options": ["string", "..."]
}
```

When `intent == "calorie_log"`, the prompt enforces a specific markdown layout for `reply_markdown` (per-meal totals, then a horizontal rule, then a daily summary with macros). For other intents the entries array must be empty.

Why a single JSON object instead of post-hoc markdown parsing: it makes the DB write atomic with the reply and makes the model's structured output the source of truth instead of relying on regex over its prose.

## 7. Profile-learning loop

After each chat turn a second LLM call (in [`chat.py`](../backend/routes/chat.py), `_run_profile_learning`) asks the model to extract any new durable facts about the user from the latest exchange. The returned JSON patch is applied to `user_profile.json` by [`apply_dynamic_patch`](../backend/profile_store.py), which is **list-additive only** — `*_add` keys append, `*_remove` keys delete, everything else overwrites. So a noisy patch cannot silently drop prior knowledge.

This runs as a `BackgroundTask`, so its failure (timeout, malformed JSON, model glitch) never delays the user-visible chat response.

## 8. Frontend structure

[`frontend/src/`](../frontend/src/):

- `App.jsx` — router, header chrome, profile-gate (redirects to `/setup` until a profile exists).
- `api.js` — thin fetch wrapper, all endpoints in one place.
- `pages/`
  - `Setup.jsx` — onboarding form, writes both `users` row and `user_profile.json`.
  - `Dashboard.jsx` — calorie progress vs goal + a four-up macro grid (protein, carbs, fats, fiber) + nav cards to Tracker / Chat.
  - `Tracker.jsx` — tab switcher for the three trackers.
  - `Chat.jsx` — markdown-rendered chat with `follow_up_options` rendered as clickable chips and an image attach affordance.
- `components/`
  - `CaloriesTab.jsx` — grouped by configured meal section, quick-add form.
  - `WeightTab.jsx` — recharts line chart with 7d/30d/all toggles, log + history.
  - `MeasurementsTab.jsx` — one chart per measurement type, log form.

## 9. PWA & caching strategy

[`frontend/vite.config.js`](../frontend/vite.config.js) configures `vite-plugin-pwa` with:

- `registerType: 'autoUpdate'` — service worker swap on next navigation.
- App shell precached (~7 entries, ~680 KiB).
- Runtime caching:
  - `GET /api/*` → `NetworkFirst` with a 4-second timeout, 24 h cache. The user sees yesterday's logs even on a flaky connection.
  - All other `/api/*` (POST/PATCH/DELETE) → **not cached.** Mutations must hit the network or fail loud — never replay from cache.
- Manifest entries point at SVG icons (regular + maskable). Apple PWA meta tags are in [`frontend/index.html`](../frontend/index.html).

## 10. Local file artifacts (gitignored)

| Path | Purpose | Sensitivity |
|---|---|---|
| `backend/lumen.db` | SQLite database | Personal health data |
| `backend/user_profile.json` | Static + dynamic profile | Personal health data |
| `backend/.env` | Backend selection + Groq API key | **API secret** |
| `backend/.venv/` | Python virtualenv | Build artifact |
| `frontend/node_modules/` | npm deps | Build artifact |
| `frontend/dist/` | Production build output | None |

The `.gitignore` is intentionally aggressive about `.env`, `.env.*`, and bare `env` filename variants.

## 11. Deployment sketch — Raspberry Pi + Groq

Since the Pi only relays JSON between the browser and Groq, even a Pi Zero 2 W is enough. The recommended layout:

```
/home/pi/lumen/
  ├─ backend/        # this repo's backend/, running uvicorn as a systemd unit
  └─ frontend/dist/  # built once with `npm run build`, served as static files
```

Front it with Caddy for auto-TLS so the PWA install criterion (HTTPS or localhost) is met on phones over LAN:

```caddy
lumen.local {
  reverse_proxy /api/* localhost:8000
  root * /home/pi/lumen/frontend/dist
  file_server
  try_files {path} /index.html
}
```

`backend/.env` on the Pi keeps `LUMEN_BACKEND=groq` and the Groq key. Egress is only to `api.groq.com`; everything else stays on-device.

## 12. Extension points / open questions

- **Macro goals.** `users` only has `calorie_goal`. Macro goals are currently hallucinated by the model in the chat summary; the Dashboard intentionally shows consumed values only. Adding `protein_g_goal` etc. is a 1-line schema change + onboarding form addition + system prompt update.
- **Multi-user / auth.** Everything assumes `user_id=1`. The schema already carries `user_id` on each table, so adding auth is mostly a routes-layer change.
- **Vision on Groq.** Groq has multimodal models (`meta-llama/llama-4-scout-…`) — the dispatch in `llm.py` could route image-bearing requests to a vision-capable model and text-only ones to the fast 8B, all on Groq.
- **Profile pruning.** The dynamic profile grows list-additively. Over time it accumulates low-signal entries. No automatic prune yet; periodic manual review of `user_profile.json` is the recommended workflow.
- **Streaming chat.** Replies are currently single-shot. Both backends support streaming; the JSON contract makes streaming complicated because the food-entries write is end-of-response. A token stream for UX with a final JSON commit is doable but not implemented.
