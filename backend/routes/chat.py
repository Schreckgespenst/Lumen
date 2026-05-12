import json
from datetime import date, datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ChatMessage, FoodLog, WeightLog
from ..schemas import ChatIn, ChatOut, ChatMessageOut
from ..profile_store import load_profile, apply_dynamic_patch
from ..prompts import build_system_prompt, PROFILE_LEARNING_PROMPT
from ..llm import chat_json, chat_plain, _extract_json

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _todays_log(db: Session, today_str: str):
    rows = (
        db.query(FoodLog)
        .filter(FoodLog.date == today_str)
        .order_by(FoodLog.created_at.asc())
        .all()
    )
    return [
        {
            "meal_type": r.meal_type,
            "food_name": r.food_name,
            "kcal": r.kcal,
            "protein_g": r.protein_g,
            "carbs_g": r.carbs_g,
            "fat_g": r.fat_g,
            "fiber_g": r.fiber_g,
            "notes": r.notes,
        }
        for r in rows
    ]


def _recent_weight(db: Session, limit: int = 7):
    rows = (
        db.query(WeightLog)
        .order_by(WeightLog.logged_at.desc())
        .limit(limit)
        .all()
    )
    return [{"weight_kg": r.weight_kg, "logged_at": r.logged_at.isoformat()} for r in rows]


def _run_profile_learning(user_msg: str, reply_summary: str):
    profile = load_profile()
    dyn = profile.get("dynamic", {})
    prompt = PROFILE_LEARNING_PROMPT.format(
        user_msg=user_msg,
        reply_summary=reply_summary[:1000],
        existing_dynamic=json.dumps(dyn, ensure_ascii=False),
    )
    raw = chat_plain(system_prompt="You extract durable user facts as JSON.", user_message=prompt)
    patch = _extract_json(raw)
    if patch:
        apply_dynamic_patch(patch)


@router.post("", response_model=ChatOut)
def post_chat(
    payload: ChatIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    today = date.today().isoformat()
    profile = load_profile()
    todays_log = _todays_log(db, today)
    recent_w = _recent_weight(db)

    system_prompt = build_system_prompt(today, profile, todays_log, recent_w)

    # Pull last ~6 turns for short-term context
    history_rows = (
        db.query(ChatMessage)
        .order_by(ChatMessage.created_at.desc())
        .limit(6)
        .all()
    )
    history = list(reversed([{"role": r.role, "content": r.content} for r in history_rows]))

    db.add(ChatMessage(role="user", content=payload.message))
    db.commit()

    parsed = chat_json(
        system_prompt=system_prompt,
        user_message=payload.message,
        image_b64=payload.image_b64,
        history=history,
    )

    reply_md = parsed.get("reply_markdown", "")
    food_entries = parsed.get("food_entries", []) or []
    follow_ups = parsed.get("follow_up_options", []) or []

    added = 0
    for fe in food_entries:
        try:
            row = FoodLog(
                user_id=1,
                date=fe.get("date") or today,
                meal_type=fe.get("meal_type") or "Other",
                food_name=fe.get("food_name") or "(unnamed)",
                kcal=float(fe.get("kcal") or 0),
                protein_g=float(fe.get("protein_g") or 0),
                carbs_g=float(fe.get("carbs_g") or 0),
                fat_g=float(fe.get("fat_g") or 0),
                fiber_g=float(fe.get("fiber_g") or 0),
                notes=fe.get("notes") or None,
            )
            db.add(row)
            added += 1
        except (TypeError, ValueError):
            continue
    if added:
        db.commit()

    db.add(ChatMessage(role="assistant", content=reply_md))
    db.commit()

    # Profile learning runs async — failure is non-fatal.
    background.add_task(_run_profile_learning, payload.message, reply_md)

    return ChatOut(
        reply=reply_md,
        parsed=parsed,
        follow_up_options=follow_ups,
        food_entries_added=added,
    )


@router.get("/history", response_model=list[ChatMessageOut])
def history(db: Session = Depends(get_db)):
    return db.query(ChatMessage).order_by(ChatMessage.created_at.asc()).all()


@router.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    db.query(ChatMessage).delete()
    db.commit()
    return {"ok": True}
