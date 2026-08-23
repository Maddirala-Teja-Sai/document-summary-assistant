"""
Application configuration.
All settings are constants — no secrets or API keys required for local fallback.
Set GROQ_API_KEY in your .env file for the best (LLM-powered) experience.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths & Environment Loading
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Search for .env in backend/ or root
env_candidates = [
    BASE_DIR / ".env",
    BASE_DIR.parent / ".env",
]
for candidate in env_candidates:
    if candidate.exists():
        load_dotenv(dotenv_path=candidate)
        break

TEMP_DIR: Path = BASE_DIR / "tmp"
TEMP_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# File upload limits
# ---------------------------------------------------------------------------
MAX_FILE_SIZE_MB: int = 10
MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_FILES_PER_REQUEST: int = 5

# Supported upload extensions
ALLOWED_EXTENSIONS: set[str] = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".tiff",
    ".bmp",
}

# ---------------------------------------------------------------------------
# Summarization lengths
# Each entry: (sentence_count, label)
# sentence_count drives sentence selection
# ---------------------------------------------------------------------------
SUMMARY_LENGTHS: dict[str, dict] = {
    "short":  {"sentences": 3,  "label": "Short"},
    "medium": {"sentences": 7,  "label": "Medium"},
    "long":   {"sentences": 12, "label": "Long"},
}

DEFAULT_SUMMARY_LENGTH: str = "medium"

# ---------------------------------------------------------------------------
# CORS — allowed origins for the FastAPI CORS middleware
# Add your Vercel frontend URL here when deployed
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS: list[str] = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # Alternate local port
    "http://127.0.0.1:5173",
    # "https://your-app.vercel.app",  # Add after deployment
]

# ---------------------------------------------------------------------------
# Groq API — LLM-powered summarization and classification
# Get a free key (no credit card) at https://console.groq.com
# Falls back to local pipeline if key is not set or API is unavailable
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_TIMEOUT: int = 30   # seconds per API call
