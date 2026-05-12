from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import FoodLog
from ..schemas import FoodIn, FoodOut

router = APIRouter(prefix="/api/food", tags=["food"])


@router.post("", response_model=FoodOut)
def add_food(entry: FoodIn, db: Session = Depends(get_db)):
    row = FoodLog(**entry.model_dump(), user_id=1)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[FoodOut])
def list_food(date: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(FoodLog)
    if date:
        q = q.filter(FoodLog.date == date)
    return q.order_by(FoodLog.created_at.asc()).all()


@router.delete("/{food_id}")
def delete_food(food_id: int, db: Session = Depends(get_db)):
    row = db.query(FoodLog).filter(FoodLog.id == food_id).first()
    if not row:
        raise HTTPException(404, "Entry not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
