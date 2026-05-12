from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routes import profile, chat, food, weight, measurements

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
