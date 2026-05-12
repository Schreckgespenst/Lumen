"""Persistent JSON-backed user profile, analogous to CLAUDE.md.

Stores static fields plus LLM-inferred dynamic fields (dietary prefs, cooking
capabilities, meal patterns, etc.). Always passed to the LLM as system context.
"""
import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent
PROFILE_PATH = BASE_DIR / "user_profile.json"

DEFAULT_PROFILE: Dict[str, Any] = {
    "static": {
        "name": None,
        "age": None,
        "height_cm": None,
        "weight_kg": None,
        "sex": None,
        "activity_level": None,
        "calorie_goal": None,
        "bmr": None,
        "body_fat_pct": None,
        "weight_unit": "kg",
        "measurement_unit": "cm",
        "meal_sections": ["Breakfast", "Lunch", "Evening Snack", "Dinner", "Dessert"],
        "measurement_types": ["chest", "waist", "hips", "arms", "thighs"],
    },
    "dynamic": {
        "dietary_preferences": [],
        "cooking_capabilities": [],
        "meal_patterns": [],
        "physical_activity_habits": [],
        "food_preferences": [],
        "food_restrictions": [],
    },
}


def load_profile() -> Dict[str, Any]:
    if not PROFILE_PATH.exists():
        save_profile(DEFAULT_PROFILE)
        return json.loads(json.dumps(DEFAULT_PROFILE))
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(profile: Dict[str, Any]) -> None:
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)


def update_static(patch: Dict[str, Any]) -> Dict[str, Any]:
    profile = load_profile()
    profile.setdefault("static", {})
    for k, v in patch.items():
        if v is not None:
            profile["static"][k] = v
    save_profile(profile)
    return profile


def apply_dynamic_patch(patch: Dict[str, Any]) -> Dict[str, Any]:
    """Merge a JSON patch returned by the profile-learning LLM call.

    `patch` may contain new keys under `dynamic`, or list-additions like
    {"dietary_preferences_add": ["no red meat"]}. Conservative merge — never
    deletes existing facts unless an explicit `_remove` key is provided.
    """
    profile = load_profile()
    profile.setdefault("dynamic", {})
    dyn = profile["dynamic"]

    for key, val in (patch or {}).items():
        if key.endswith("_add") and isinstance(val, list):
            target = key[:-4]
            existing = dyn.get(target, [])
            if not isinstance(existing, list):
                existing = []
            for item in val:
                if item not in existing:
                    existing.append(item)
            dyn[target] = existing
        elif key.endswith("_remove") and isinstance(val, list):
            target = key[:-7]
            existing = dyn.get(target, [])
            if isinstance(existing, list):
                dyn[target] = [x for x in existing if x not in val]
        else:
            # direct set (overrides)
            dyn[key] = val

    save_profile(profile)
    return profile
