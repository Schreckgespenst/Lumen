from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load backend/.env before anything that reads os.environ (e.g. llm.py).
load_dotenv(Path(__file__).resolve().parent / ".env")

from .database import init_db  # noqa: E402
from .routes import profile, chat, food, weight, measurements  # noqa: E402

app = FastAPI(title="Lumen — Local LLM Fitness Tracker", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(food.router)
app.include_router(weight.router)
app.include_router(measurements.router)
