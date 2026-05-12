# Session Handoff — 2026-05-13 (post-0.3.0)

A pointer doc for the next Claude Code session. Read this first to pick up state. Things that already live in [`../README.md`](../README.md), [`./ARCHITECTURE.md`](./ARCHITECTURE.md), and [`../CHANGELOG.md`](../CHANGELOG.md) are not repeated here.

## Where we left off

- Working in [`c:\Users\Shikher Gupta\Documents\PythonProjz\Fitness_App`](..).
- Latest release: **0.3.0** — UI port to match the Stitch design system. See the CHANGELOG entry for the full diff.
- Repo synced with `git@github.com:Schreckgespenst/Lumen`.
- No servers were running at end of session.
- `backend/.env` is intact locally (`LUMEN_BACKEND=groq`, real Groq key, gitignored).

## What's now true that wasn't before

1. **Google Stitch is set up and paired with this repo.** Project ID `17013001233582734211`, design system `assets/8395298068448777005` (`Lumen Dark`). Six screens already generated: Chat, Dashboard, Setup, Tracker/Calories, Tracker/Weight, Tracker/Measurements. To generate or edit more, reuse those IDs — don't make a new project.
2. **Inter is the global font.** Loaded from Google Fonts in `frontend/index.html`. The `.tnum` utility in `frontend/src/index.css` gives tabular numerals; it's applied wherever numbers stack vertically.
3. **Top nav uses `NavLink`** with accent-purple active state. Active route is now obvious without a hover.
4. **Setup form is scaffolded for macro goals** (section dividers labelled "Daily goals" / "Optional"), but the actual `protein_g_goal` / `carbs_g_goal` / `fat_g_goal` inputs are NOT added because the backend doesn't accept them yet. See open action items.

## Open action items the user owns

1. **Rotate the Groq API key.** Still pasted in chat history of an earlier session. https://console.groq.com/keys → delete → create new → paste into `backend/.env`.
2. **Rotate the Google Stitch API key.** Same situation, pasted in chat. Replace via `claude mcp remove stitch` then re-add with a fresh key from Google AI Studio.
3. **Wire macro goals end-to-end.** All three pieces needed:
   - `backend/models.py` — add `protein_g_goal`, `carbs_g_goal`, `fat_g_goal` columns to `User`.
   - `backend/schemas.py` — add the same fields to `UserSetup` (and the patch schema).
   - `backend/lumen.db` — SQLite `ALTER TABLE users ADD COLUMN ...` migration (or wipe + recreate via setup if you're fine losing local data).
   - `frontend/src/pages/Setup.jsx` — add the three inputs under the existing "Daily goals" section.
   - `backend/prompts.py` — feed the goals into the chat system prompt so the model stops fabricating goal numbers in calorie-log replies.
   - `frontend/src/pages/Dashboard.jsx` — switch the macro grid from "consumed only" to a `consumed / goal` format with a thin progress bar per macro, mirroring the calorie bar.

## What the user is most likely to do next

Most-likely path: tackle action item #3 above. It's been open since 0.2.0 and the Setup form is now visually waiting for it.

Plausible alternates:
- Re-run a Stitch generation with edits to a specific screen (use `mcp__stitch__generate_screen_from_text` with the project + design-system IDs above).
- Begin the Raspberry Pi deployment sketch in ARCHITECTURE §11.
- Streaming chat replies (ARCHITECTURE §12, "Streaming chat") — non-trivial because the JSON contract is end-of-response.

## How to start the servers from a cold session

```powershell
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000
npm --prefix frontend run dev
```

Then open http://localhost:5173.

## Memory pointers (auto-loaded in your session)

- [`project_lumen.md`](../../../.claude/projects/c--Users-Shikher-Gupta-Documents-PythonProjz-Fitness-App/memory/project_lumen.md) — durable project picture
- [`project_lumen_stitch.md`](../../../.claude/projects/c--Users-Shikher-Gupta-Documents-PythonProjz-Fitness-App/memory/project_lumen_stitch.md) — Stitch IDs and tool quirks (roundness cap, palette tinting, etc.)
- [`feedback_api_keys.md`](../../../.claude/projects/c--Users-Shikher-Gupta-Documents-PythonProjz-Fitness-App/memory/feedback_api_keys.md) — the recurring "user pastes secrets" pattern

If anything in *this* handoff contradicts memory, trust the handoff (it is newer).

## Conventions the user has implicitly accepted

- Short, terse responses preferred over verbose summaries.
- Working directory is Windows; use PowerShell syntax, Bash tool only for POSIX scripts.
- The user is comfortable running multi-step commands themselves; no babysitting needed.
- API keys in chat: flag in one sentence, recommend rotation, proceed.
- One bundled commit per logical shipment (don't split a coherent change into multiple commits).
- When porting Stitch designs to React, treat Stitch as visual reference and keep our Tailwind tokens as source of truth — don't extract hexes from Stitch's M3 token output.
