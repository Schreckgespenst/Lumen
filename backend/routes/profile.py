from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserSetup, UserOut, ProfilePatch
from ..profile_store import load_profile, update_static, apply_dynamic_patch

router = APIRouter(prefix="/api", tags=["profile"])


@router.post("/setup", response_model=UserOut)
def setup_user(data: UserSetup, db: Session = Depends(get_db)):
    existing = db.query(User).first()
    if existing:
        for k, v in data.model_dump().items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        update_static(data.model_dump())
        return existing
    user = User(**data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    update_static(data.model_dump())
    return user


@router.get("/profile")
def get_profile(db: Session = Depends(get_db)):
    user = db.query(User).first()
    profile = load_profile()
    return {"user": _user_dict(user) if user else None, "profile": profile}


@router.patch("/profile")
def patch_profile(data: ProfilePatch, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if user is None:
        raise HTTPException(404, "No user profile yet — run /api/setup first")
    payload = data.model_dump(exclude_unset=True, exclude={"extras"})
    for k, v in payload.items():
        setattr(user, k, v)
    db.commit()
    update_static(payload)
    if data.extras:
        apply_dynamic_patch(data.extras)
    return {"user": _user_dict(user), "profile": load_profile()}


def _user_dict(u: User):
    return {
        "id": u.id,
        "name": u.name,
        "age": u.age,
        "height_cm": u.height_cm,
        "weight_kg": u.weight_kg,
        "sex": u.sex,
        "activity_level": u.activity_level,
        "calorie_goal": u.calorie_goal,
        "bmr": u.bmr,
        "body_fat_pct": u.body_fat_pct,
        "created_at": u.created_at,
    }
