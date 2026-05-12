from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    sex = Column(String)
    activity_level = Column(String)
    calorie_goal = Column(Integer)
    bmr = Column(Integer, nullable=True)
    body_fat_pct = Column(Float, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class FoodLog(Base):
    __tablename__ = "food_log"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    date = Column(String, index=True)  # YYYY-MM-DD (user local date)
    meal_type = Column(String)
    food_name = Column(String)
    kcal = Column(Float, default=0)
    protein_g = Column(Float, default=0)
    carbs_g = Column(Float, default=0)
    fat_g = Column(Float, default=0)
    fiber_g = Column(Float, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class WeightLog(Base):
    __tablename__ = "weight_log"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    weight_kg = Column(Float, nullable=False)
    logged_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    measurement_type = Column(String)  # chest, waist, hips, arms, thighs
    value = Column(Float, nullable=False)
    unit = Column(String, default="cm")
    logged_at = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    role = Column(String)  # user | assistant
    content = Column(Text)
    created_at = Column(DateTime, default=utcnow)
