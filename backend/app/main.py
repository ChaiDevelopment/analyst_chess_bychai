from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

app = FastAPI(
    title="Chess Review API",
    description="Free, local-first chess game analysis powered by Stockfish.",
    version="1.0.0",
)

# When Vercel calls this public Railway API directly, its browser origin must
# be listed in Railway's CORS_ORIGINS variable (see backend/.env.example).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "Chess Review API",
        "docs": "/docs",
        "health": "/api/health",
    }
