from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BodyMeasurement
from ..schemas import MeasurementIn, MeasurementOut, MeasurementPatch

router = APIRouter(prefix="/api/measurements", tags=["measurements"])


@router.post("", response_model=MeasurementOut)
def add_measurement(entry: MeasurementIn, db: Session = Depends(get_db)):
    logged_at = entry.logged_at or datetime.now(timezone.utc)
    row = BodyMeasurement(
        user_id=1,
        measurement_type=entry.measurement_type,
        value=entry.value,
        unit=entry.unit,
        logged_at=logged_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[MeasurementOut])
def list_measurements(db: Session = Depends(get_db)):
    return db.query(BodyMeasurement).order_by(BodyMeasurement.logged_at.asc()).all()


@router.patch("/{mid}", response_model=MeasurementOut)
def patch_measurement(mid: int, patch: MeasurementPatch, db: Session = Depends(get_db)):
    row = db.query(BodyMeasurement).filter(BodyMeasurement.id == mid).first()
    if not row:
        raise HTTPException(404, "Entry not found")
    payload = patch.model_dump(exclude_unset=True)
    for k, v in payload.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{mid}")
def delete_measurement(mid: int, db: Session = Depends(get_db)):
    row = db.query(BodyMeasurement).filter(BodyMeasurement.id == mid).first()
    if not row:
        raise HTTPException(404, "Entry not found")
    db.delete(row)
    db.commit()
    return {"ok": True}
