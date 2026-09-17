from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.config_routes import router as config_router
from app.api.export import router as export_router
from app.api.health import router as health_router
from app.api.leads import router as leads_router
from app.api.search import router as search_router
from app.api.stats import router as stats_router
from app.config import get_settings
from app.logging_setup import setup_logging
from app.models.entities import init_db

setup_logging()
init_db()

app = FastAPI(title="Lead Finder", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(leads_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(config_router, prefix="/api")

frontend_dist = get_settings().frontend_dist
assets = frontend_dist / "assets"
if assets.exists():
    app.mount("/assets", StaticFiles(directory=assets), name="assets")


@app.get("/")
def index():
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "name": "Lead Finder",
        "docs": "/docs",
        "hint": "Avvia `npm run build` in frontend/ oppure `npm run dev` su porta 5173.",
    }


@app.get("/{path:path}")
def spa(path: str):
    if path.startswith("api/") or path in {"docs", "redoc", "openapi.json"}:
        return {"detail": "Not Found"}
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        candidate = frontend_dist / path
        if candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_file)
    return {"detail": "UI non compilata"}
