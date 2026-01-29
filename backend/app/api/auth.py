"""Authentication API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from ..models.user import GoogleAuthRequest, get_current_user
from ..services.auth_service import auth_service

router = APIRouter()

# In-memory user storage (replace with database in production)
_users_storage: dict = {}


# Helper functions
def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email from storage."""
    return _users_storage.get(email)


def create_user(email: str, password_hash: Optional[str] = None, name: Optional[str] = None,
                avatar_url: Optional[str] = None, provider: str = "email",
                provider_id: Optional[str] = None) -> dict:
    """Create a new user."""
    import time
    user = {
        "id": f"user_{int(time.time())}_{hash(email) % 10000}",
        "email": email,
        "password_hash": password_hash,
        "name": name,
        "avatar_url": avatar_url,
        "provider": provider,
        "provider_id": provider_id,
        "created_at": None,  # Will be set by UserResponse
    }
    _users_storage[email] = user
    return user


def user_to_dict(user: dict) -> dict:
    """Convert user model to dict for response."""
    from datetime import datetime
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user.get("name"),
        "avatar_url": user.get("avatar_url"),
        "provider": user.get("provider", "email"),
        "created_at": datetime.utcnow().isoformat(),
    }


# Dev bypass endpoint
@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    if current_user.get("email") is None:
        for user in _users_storage.values():
            if user.get("id") == current_user.get("id"):
                return user_to_dict(user)
    return user_to_dict(current_user)


# Email signup
@router.post("/auth/email/signup")
async def email_signup(request: dict):
    """Sign up with email and password."""
    email = request.get("email")
    password = request.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    existing = get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = create_user(
        email=email,
        password_hash=auth_service.hash_password(password),
        provider="email"
    )

    token = auth_service.create_access_token(user["id"])

    return {
        "token": token,
        "user": user_to_dict(user)
    }


# Email signin
@router.post("/auth/email/signin")
async def email_signin(request: dict):
    """Sign in with email and password."""
    email = request.get("email")
    password = request.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    password_hash = user.get("password_hash")
    if not password_hash or not auth_service.verify_password(password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth_service.create_access_token(user["id"])

    return {
        "token": token,
        "user": user_to_dict(user)
    }


# Google OAuth (simplified - would need proper token verification in production)
@router.post("/auth/google")
async def google_auth(request: GoogleAuthRequest):
    """Authenticate with Google OAuth."""
    try:
        # In production, verify the token with Google
        # For now, we'll decode it without verification for development
        # import requests
        # from google.oauth2 import id_token
        # from google.auth.transport import requests as google_requests

        # idinfo = id_token.verify_oauth2_token(
        #     request.credential,
        #     google_requests.Request(),
        #     os.getenv("GOOGLE_CLIENT_ID")
        # )

        # For development, parse the JWT without verification
        import base64
        import json

        # Parse JWT (format: header.payload.signature)
        parts = request.credential.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        # Decode payload (base64url)
        payload = parts[1]
        # Add padding if needed
        payload += "=" * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        idinfo = json.loads(decoded)

        email = idinfo.get("email")
        name = idinfo.get("name")
        picture = idinfo.get("picture")
        google_id = idinfo.get("sub")

        if not email:
            raise HTTPException(status_code=400, detail="Invalid token")

        # Find or create user
        user = get_user_by_email(email)
        if not user:
            user = create_user(
                email=email,
                name=name,
                avatar_url=picture,
                provider="google",
                provider_id=google_id
            )

        token = auth_service.create_access_token(user["id"])

        return {
            "token": token,
            "user": user_to_dict(user)
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
