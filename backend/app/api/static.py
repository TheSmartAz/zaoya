"""Static file serving for runtime scripts."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response

from app.config import settings

router = APIRouter()

# Zaoya runtime script fallback (used if runtime file is missing)
RUNTIME_SCRIPT = """
window.Zaoya = {
    submitForm: function(data) {
        console.log('Form submitted:', data);
        // Send to Zaoya API
        fetch('/api/forms/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).catch(console.error);
    },

    track: function(event, data) {
        console.log('Track:', event, data);
        // Send analytics to Zaoya API
        fetch('/api/analytics/track', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event, data })
        }).catch(console.error);
    },

    toast: function(message) {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);padding:12px 24px;background:rgba(0,0,0,0.8);color:white;border-radius:8px;z-index:9999;font-family:sans-serif;font-size:14px;';
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    },

    navigate: function(url) {
        window.location.href = url;
    }
};
"""


RUNTIME_PATH = Path(__file__).resolve().parents[3] / "frontend" / "public" / "zaoya-runtime.js"


def _runtime_headers() -> dict:
    pages_origin = settings.pages_url.rstrip("/")
    return {
        "Cache-Control": "public, max-age=31536000, immutable",
        "Access-Control-Allow-Origin": pages_origin,
    }


def _runtime_response():
    if RUNTIME_PATH.exists():
        return FileResponse(
            path=str(RUNTIME_PATH),
            media_type="application/javascript",
            filename="zaoya-runtime.js",
            headers=_runtime_headers(),
        )
    return Response(
        content=RUNTIME_SCRIPT,
        media_type="application/javascript",
        headers=_runtime_headers(),
    )


@router.get("/zaoya-runtime.js")
async def serve_runtime():
    """Serve the Zaoya runtime script."""
    return _runtime_response()


@router.get("/static/zaoya-runtime.js")
async def serve_runtime_static():
    """Serve the Zaoya runtime script from static path."""
    return _runtime_response()
