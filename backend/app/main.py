"""FastAPI application: CORS, routers, static serving, error envelope.

In production this single process serves both the API under /api and the built
React app from web/dist, so the demo is one URL with no CORS.
"""

from __future__ import annotations

from http import HTTPStatus
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import health, incidents, investigate
from app.config import get_settings

# Repo layout: backend/app/main.py -> parents[2] is the repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = REPO_ROOT / "web" / "dist"

app = FastAPI(
    title="AI Suspicious Message Investigation Agent",
    version="0.1.0",
    description=(
        "Text-only analysis of suspicious messages for an IT helpdesk. "
        "Never fetches URLs; saving an incident requires human approval."
    ),
)

# CORS is only needed for local dev (Vite on :5173 -> API on :8000). In
# production the frontend is served from the same origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---------------------------------------------------------------
app.include_router(health.router, prefix="/api")
app.include_router(investigate.router, prefix="/api")
app.include_router(incidents.router, prefix="/api")


# --- Uniform error envelope: {"error": {"code": "...", "message": "..."}} ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Wrap every HTTPException detail in the shared error shape."""
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        error = {"code": str(exc.detail["code"]), "message": str(exc.detail.get("message", ""))}
    else:
        try:
            code = HTTPStatus(exc.status_code).phrase.upper().replace(" ", "_")
        except ValueError:  # pragma: no cover - unknown status code
            code = "HTTP_ERROR"
        error = {"code": code, "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"error": error})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Return 422 in the same envelope so the frontend has one error path."""
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc.errors())}},
    )


# --- Static SPA (production) ----------------------------------------------
# Registered last: /api routes above always win. If web/dist is missing (dev, or
# a fresh clone before `npm run build`) the API still works on its own.
if WEB_DIST.is_dir():

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:
        """Serve built assets, and fall back to index.html for client routes."""
        if full_path.startswith("api"):
            raise StarletteHTTPException(
                status_code=404,
                detail={"code": "NOT_FOUND", "message": f"No API route matches /{full_path}."},
            )
        candidate = (WEB_DIST / full_path).resolve()
        # Guard against path traversal outside web/dist.
        if full_path and candidate.is_file() and WEB_DIST in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(WEB_DIST / "index.html")


# --- Local dev entrypoint: `python -m app.main` ---------------------------
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
