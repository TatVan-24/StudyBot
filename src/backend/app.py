"""FastAPI application — runtime-agnostic.

Runs on:
  - Local laptop:        uvicorn backend.app:app --reload
  - AWS Lambda:          wrap with Mangum (pip install mangum) → expose `handler`
  - ECS Fargate / EC2:   uvicorn or gunicorn
  - App Runner:          uvicorn

The choice is yours. Code stays the same.
"""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.backend.config import config
from src.rag_pipeline.llm.adapters import factory
from src.backend import handlers


app = FastAPI(title="StudyBot")


# CORS — allow frontend to live on a different origin (CloudFront / Amplify / separate ALB).
_allowed = ["*"] if config.cors_origins == "*" else [o.strip() for o in config.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons. In serverless this gets re-initialized per cold start; that's fine.
ai_client    = factory.make_ai()
storage      = factory.make_storage()
userstore    = factory.make_userstore()
vector_store = factory.make_vector()


def _resolve_user_id(x_user_id: str | None) -> str:
    """Auth abstraction: extract user_id from header, fall back to default for local dev.

    In production you populate X-User-Id from:
      - Cognito JWT (decoded by API Gateway authorizer)
      - Signed URL claim
      - Custom auth Lambda
    """
    return x_user_id or config.default_user_id


# ── Request models ─────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    session_id: str
    user_id: str
    query: str


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "backends": {
            "ai": config.ai_backend,
            "storage": config.storage_backend,
            "userstore": config.userstore_backend,
            "vector": config.vector_backend,
        },
    }


# ── Upload ─────────────────────────────────────────────────────────────────────

@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(default=None),
    x_user_id: str | None = Header(default=None),
) -> dict:
    user_id = _resolve_user_id(x_user_id)
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    result = handlers.handle_upload(
        user_id=user_id,
        filename=file.filename or "untitled",
        data=data,
        storage=storage,
        userstore=userstore,
        vector_store=vector_store,
        session_id=session_id or None,
    )
    # handle_upload returns error dict for session errors
    if "error" in result:
        status_code = result.get("status", 400)
        raise HTTPException(status_code=status_code, detail=result["error"])
    return result


# ── Query ──────────────────────────────────────────────────────────────────────

@app.post("/query")
def query(req: QueryRequest) -> dict:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    return handlers.handle_query(
        session_id=req.session_id,
        user_id=req.user_id,
        query=req.query,
        ai_client=ai_client,
        userstore=userstore,
        vector_store=vector_store,
        vector_backend=config.vector_backend,
        bedrock_kb_id=config.vector_bedrock_kb_id,
    )


# ── Sessions ───────────────────────────────────────────────────────────────────

@app.get("/sessions")
def list_sessions(x_user_id: str | None = Header(default=None)) -> dict:
    return handlers.handle_list_sessions(_resolve_user_id(x_user_id), userstore)


@app.get("/sessions/{session_id}")
def get_session(
    session_id: str,
    x_user_id: str | None = Header(default=None),
) -> dict:
    result = handlers.handle_get_session(session_id, _resolve_user_id(x_user_id), userstore)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    x_user_id: str | None = Header(default=None),
) -> dict:
    result = handlers.handle_delete_session(session_id, _resolve_user_id(x_user_id), userstore)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result.get("reason"))
    return result


# ── Docs & Queries (backward compat) ──────────────────────────────────────────

@app.get("/docs/list")
def list_docs(x_user_id: str | None = Header(default=None)) -> dict:
    return handlers.handle_list_docs(_resolve_user_id(x_user_id), userstore)


@app.get("/queries/recent")
def recent(x_user_id: str | None = Header(default=None), limit: int = 10) -> dict:
    """Kept for backward compat. Will be removed after Phase 5 (frontend)."""
    return handlers.handle_recent_queries(_resolve_user_id(x_user_id), userstore, limit=limit)


@app.post("/docs/{doc_id}/detach")
def detach_doc(
    doc_id: str,
    session_id: str,
    x_user_id: str | None = Header(default=None),
) -> dict:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    result = handlers.handle_detach_doc(doc_id, session_id, _resolve_user_id(x_user_id), userstore)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("reason"))
    return result


@app.delete("/docs/{doc_id}")
def delete_doc_global(
    doc_id: str,
    x_user_id: str | None = Header(default=None),
) -> dict:
    result = handlers.handle_delete_doc_global(
        doc_id=doc_id,
        user_id=_resolve_user_id(x_user_id),
        userstore=userstore,
        vector_store=vector_store,
        storage=storage
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("reason"))
    return result


@app.get("/progress/summary")
def progress_summary(x_user_id: str | None = Header(default=None)) -> dict:
    return handlers.handle_progress_summary(_resolve_user_id(x_user_id), userstore, handlers.LOG_DIR)


# ── Static frontend ────────────────────────────────────────────────────────────

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if config.serve_frontend:
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        """Convenience: serves frontend/index.html at /. Set SERVE_FRONTEND=false
        if you deploy the frontend separately (CloudFront+S3, Amplify, ALB)."""
        return FileResponse(FRONTEND_DIR / "index.html")
