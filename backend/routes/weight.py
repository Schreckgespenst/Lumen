from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import WeightLog
from ..schemas import WeightIn, WeightOut, WeightPatch

router = APIRouter(prefix="/api/weight", tags=["weight"])


@router.post("", response_model=WeightOut)
def add_weight(entry: WeightIn, db: Session = Depends(get_db)):
    logged_at = entry.logged_at or datetime.now(timezone.utc)
    row = WeightLog(user_id=1, weight_kg=entry.weight_kg, logged_at=logged_at)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[WeightOut])
def list_weight(db: Session = Depends(get_db)):
    return db.query(WeightLog).order_by(WeightLog.logged_at.asc()).all()


@router.patch("/{wid}", response_model=WeightOut)
def patch_weight(wid: int, patch: WeightPatch, db: Session = Depends(get_db)):
    row = db.query(WeightLog).filter(WeightLog.id == wid).first()
    if not row:
        raise HTTPException(404, "Entry not found")
    payload = patch.model_dump(exclude_unset=True)
    for k, v in payload.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{wid}")
def delete_weight(wid: int, db: Session = Depends(get_db)):
    row = db.query(WeightLog).filter(WeightLog.id == wid).first()
    if not row:
        raise HTTPException(404, "Entry not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
