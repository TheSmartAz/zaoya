import asyncio
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
        allow_api = settings.environment == "development" and path.startswith("/api/")
        allow_csp_report = path == "/api/csp-report"
        if not (
            path.startswith("/p/")
            or path.startswith("/p-sim/")
            or path.startswith("/p-sim-report/")
            or path.startswith("/og-image/")
            or path.startswith("/uploads/")
            or path == "/zaoya-runtime.js"
            or path.startswith("/static/zaoya-runtime.js")
            or path == "/favicon.ico"
            or allow_api
            or allow_csp_report
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
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.rate_limit_per_minute,
    requests_per_hour=settings.rate_limit_per_hour,
)

# API routers
from app.api.chat import router as chat_router
from app.api.project_chat import router as project_chat_router
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
from app.api.build import router as build_router
from app.api.settings import router as settings_router
from app.api.product_doc import router as product_doc_router
from app.api.files import router as files_router
from app.api.project_versions import router as project_versions_router
from app.api.project_branches import router as project_branches_router
from app.api.thumbnails import router as thumbnails_router
from app.services.failed_version_cleanup import run_failed_version_cleanup_loop
from app.services.thumbnail_queue import ensure_thumbnail_workers_running

app.include_router(chat_router)
app.include_router(project_chat_router)
app.include_router(interview_router)
app.include_router(versions_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(draft_router)
app.include_router(snapshots_router)
app.include_router(build_router)
app.include_router(settings_router)
app.include_router(product_doc_router)
app.include_router(files_router)
app.include_router(project_versions_router)
app.include_router(project_branches_router)
app.include_router(thumbnails_router)
app.include_router(pages_router)  # Published pages (no /api prefix)
app.include_router(static_router)  # Static files


@app.on_event("startup")
async def startup_tasks() -> None:
    asyncio.create_task(run_failed_version_cleanup_loop())
    asyncio.create_task(ensure_thumbnail_workers_running())


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
