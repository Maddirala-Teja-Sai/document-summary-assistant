"""
FastAPI application entry point for the Document Summary Assistant.

Startup sequence:
  1. FastAPI app is created with title, description, and version metadata.
  2. CORS middleware is added for the React frontend.
  3. On lifespan start:
     - Groq API key is checked (warning logged if missing).
     - NLTK tokenizer data downloaded (needed by local fallback).
  4. All API routes are registered under the /api prefix.
  5. A global exception handler formats unexpected errors as JSON.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import ALLOWED_ORIGINS, GROQ_API_KEY

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — runs on startup and shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: check Groq key, pre-load local fallback models.
    Shutdown: log goodbye.
    """
    logger.info("Starting up Document Summary Assistant…")

    # ── Groq key check ──────────────────────────────────────────────────────
    if GROQ_API_KEY:
        logger.info("✅ GROQ_API_KEY detected — LLM-powered analysis enabled.")
    else:
        logger.warning(
            "⚠️  GROQ_API_KEY not set. "
            "App will use the local fallback pipeline (lower quality). "
            "Get a free key at https://console.groq.com"
        )

    # ── Local fallback: NLTK ─────────────────────────────────────────────────
    try:
        import nltk
        nltk.download("punkt",     quiet=True)
        nltk.download("punkt_tab", quiet=True)
        logger.info("NLTK tokenizer data ready (used by local fallback).")
    except Exception as exc:
        logger.warning("NLTK download failed (fallback summarizer may not work): %s", exc)

    logger.info("Ready to accept requests.")
    yield
    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Document Summary Assistant",
    description=(
        "Upload PDF or image documents and receive intelligent summaries "
        "and automatic document-type classification. "
        "Powered by Groq with a local fallback pipeline."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected server error occurred. Please try again.",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(router)
