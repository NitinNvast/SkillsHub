"""SkillsHub FastAPI entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, employees, review, search, skills, uploads
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="SkillsHub API",
    description="AI-Powered Skills Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://frontend:3000",  # docker-compose internal hostname
]
if settings.allowed_origins:
    _cors_origins.extend(o.strip() for o in settings.allowed_origins.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
async def root():
    return {"service": "SkillsHub API", "version": "0.1.0", "status": "ok"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "extraction_model": settings.extraction_model}


# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(employees.router, prefix="/employees", tags=["employees"])
app.include_router(skills.router, prefix="/skills", tags=["skills"])
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(review.router, prefix="/review-queue", tags=["review"])
