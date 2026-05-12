from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class UserSetup(BaseModel):
    name: str
    age: int
    height_cm: float
    weight_kg: float
    sex: str
    activity_level: str
    calorie_goal: int
    bmr: Optional[int] = None
    body_fat_pct: Optional[float] = None


class UserOut(UserSetup):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProfilePatch(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    sex: Optional[str] = None
    activity_level: Optional[str] = None
    calorie_goal: Optional[int] = None
    bmr: Optional[int] = None
    body_fat_pct: Optional[float] = None
    # dynamic profile keys passed as extras
    extras: Optional[Dict[str, Any]] = None


class FoodIn(BaseModel):
    date: str  # YYYY-MM-DD
    meal_type: str
    food_name: str
    kcal: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    notes: Optional[str] = None


class FoodOut(FoodIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WeightIn(BaseModel):
    weight_kg: float
    logged_at: Optional[datetime] = None


class WeightOut(BaseModel):
    id: int
    weight_kg: float
    logged_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class WeightPatch(BaseModel):
    weight_kg: Optional[float] = None
    logged_at: Optional[datetime] = None


class MeasurementIn(BaseModel):
    measurement_type: str
    value: float
    unit: str = "cm"
    logged_at: Optional[datetime] = None


class MeasurementOut(BaseModel):
    id: int
    measurement_type: str
    value: float
    unit: str
    logged_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class MeasurementPatch(BaseModel):
    measurement_type: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    logged_at: Optional[datetime] = None


class ChatIn(BaseModel):
    message: str
    # optional image as base64 data URL for multimodal input
    image_b64: Optional[str] = None


class ChatOut(BaseModel):
    reply: str
    parsed: Optional[Dict[str, Any]] = None
    follow_up_options: List[str] = []
    food_entries_added: int = 0


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
