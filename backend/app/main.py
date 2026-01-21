from urllib.parse import urlparse

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path

# Load configuration
from app.config import settings

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Create FastAPI app with config
app = FastAPI(
    title=settings.api_title,
    description="AI-powered mobile page generator",
    version=settings.api_version,
    debug=settings.debug,
)

# Store config in app state for middleware access
app.state.config = {
    "environment": settings.environment,
}


def _get_pages_host() -> str:
    parsed = urlparse(settings.pages_url)
    return parsed.netloc or settings.pages_url.replace("https://", "").replace("http://", "")


@app.middleware("http")
async def restrict_pages_host(request, call_next):
    pages_host = _get_pages_host()
    host = request.headers.get("host", "")
    path = request.url.path

    if pages_host and host == pages_host:
        if not (
            path.startswith("/p/")
            or path == "/zaoya-runtime.js"
            or path.startswith("/static/zaoya-runtime.js")
        ):
            return Response(status_code=404)

    return await call_next(request)

# CORS middleware (configure properly for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if isinstance(settings.cors_origins, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (order matters - error handler first)
from app.middleware.error_handler import ErrorHandlingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.validation import RequestSizeLimitMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware, max_size_mb=10)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100, requests_per_hour=1000)

# API routers
from app.api.chat import router as chat_router
from app.api.interview import router as interview_router
from app.api.versions import router as versions_router
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.pages import router as pages_router
from app.api.static import router as static_router
from app.api.submissions import router as submissions_router
from app.api.analytics import router as analytics_router
from app.api.draft import router as draft_router
from app.api.snapshots import router as snapshots_router

app.include_router(chat_router)
app.include_router(interview_router)
app.include_router(versions_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(draft_router)
app.include_router(snapshots_router)
app.include_router(pages_router)  # Published pages (no /api prefix)
app.include_router(static_router)  # Static files


@app.get("/")
async def root():
    return {
        "message": "Zaoya API is running",
        "version": settings.api_version,
        "environment": settings.environment,
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
