"""Credits API endpoints for managing user image generation credits."""

from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.user import get_current_user
from app.models.db.credit import UserCredits, CreditTransaction, CreditPackage
from app.services.image_generation_service import ImageGenerationService
from app.services.rate_limiter import api_rate_limiter


# ============================================================
# Request/Response Models
# ============================================================

class GenerateImageRequest(BaseModel):
    """Request to generate an AI image."""
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = 1024
    height: int = 1024
    quality: str = "standard"
    provider: str = "openai"
    model: Optional[str] = None
    save_to_library: bool = True
    alt_text: Optional[str] = None
    tags: Optional[list[str]] = None


class PurchaseCreditsRequest(BaseModel):
    """Request to purchase credits."""
    package_id: str


router = APIRouter()


# ============================================================
# Helper Functions
# ============================================================

async def get_user_id(current_user: dict, db: AsyncSession) -> UUID:
    """Get UUID for current user."""
    from app.models.db import User

    try:
        uid = UUID(current_user["id"])
    except ValueError:
        # Try to find user by email for dev bypass mode
        if current_user.get("provider") == "dev":
            result = await db.execute(
                select(User).where(User.email == current_user["email"])
            )
            user = result.scalar_one_or_none()
            if user:
                return user.id
        raise HTTPException(status_code=401, detail="Invalid user")

    return uid


# ============================================================
# Credits Balance Endpoints
# ============================================================

@router.get("/credits/balance")
async def get_credit_balance(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's credit balance."""
    user_id = await get_user_id(current_user, db)
    service = ImageGenerationService(db)

    # Check for monthly reset
    await service.check_monthly_reset(user_id)

    balance = await service.get_user_credit_balance(user_id)

    return balance


@router.get("/credits/history")
async def get_credit_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's credit transaction history."""
    user_id = await get_user_id(current_user, db)

    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == user_id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(min(limit, 100))
    )

    transactions = []
    for txn in result.scalars():
        transactions.append({
            "id": str(txn.id),
            "amount": txn.amount,
            "type": txn.transaction_type,
            "description": txn.description,
            "meta_data": txn.meta_data,
            "created_at": txn.created_at.isoformat(),
        })

    return {"transactions": transactions}


# ============================================================
# Credit Packages Endpoints
# ============================================================

@router.get("/credits/packages")
async def list_credit_packages(
    db: AsyncSession = Depends(get_db),
):
    """List available credit packages for purchase."""
    result = await db.execute(
        select(CreditPackage)
        .where(CreditPackage.is_active == True)
        .order_by(CreditPackage.display_order, CreditPackage.credits)
    )

    packages = []
    for pkg in result.scalars():
        packages.append({
            "id": str(pkg.id),
            "name": pkg.name,
            "credits": pkg.credits,
            "price_usd": float(pkg.price_usd),
            "stripe_price_id": pkg.stripe_price_id,
        })

    return {"packages": packages}


@router.get("/images/providers")
async def list_image_providers():
    """List available image generation providers."""
    return {
        "providers": [
            {
                "id": "openai",
                "name": "DALL-E 3",
                "qualities": ["standard", "hd"],
                "sizes": ["1024x1024", "1024x1792", "1792x1024"],
            },
            {
                "id": "stability",
                "name": "Stable Diffusion XL",
                "qualities": ["standard", "hd"],
                "sizes": ["1024x1024"],
            },
            {
                "id": "replicate",
                "name": "Replicate (SDXL)",
                "qualities": ["standard"],
                "sizes": ["1024x1024"],
            },
        ]
    }


# ============================================================
# Image Generation Endpoints
# ============================================================

@router.post("/images/generate")
async def generate_image(
    request: GenerateImageRequest,
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate an AI image.

    Credits are deducted before generation. If generation fails,
    credits are refunded.
    """
    user_id = await get_user_id(current_user, db)

    # Rate limit: 5 requests per minute per user
    is_limited, remaining = await api_rate_limiter.check_and_record(
        identifier=f"image_gen:{user_id}",
        max_attempts=5,
        window_seconds=60,
    )
    if is_limited:
        raise HTTPException(
            status_code=429,
            detail="Too many image generation requests. Please try again later.",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": "5",
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Window": "60",
            },
        )
    service = ImageGenerationService(db)

    # Parse project_id if provided
    pid = UUID(project_id) if project_id else None

    result = await service.generate_image(
        user_id=user_id,
        project_id=pid,
        prompt=request.prompt,
        provider=request.provider,
        negative_prompt=request.negative_prompt,
        width=request.width,
        height=request.height,
        quality=request.quality,
        model=request.model,
        save_to_library=request.save_to_library,
        alt_text=request.alt_text,
        tags=request.tags,
    )

    if not result.get("success"):
        error_code = result.get("error")
        if error_code == "insufficient_credits":
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "Insufficient credits",
                    "required": result.get("required"),
                }
            )
        raise HTTPException(status_code=500, detail=result)

    return result


# ============================================================
# Provider Configuration (for admin)
# ============================================================

@router.post("/admin/credits/packages")
async def create_credit_package(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new credit package (admin only)."""
    # TODO: Add admin check
    package = CreditPackage(
        id=uuid4(),
        name=request.get("name"),
        credits=request.get("credits"),
        price_usd=request.get("price_usd"),
        stripe_price_id=request.get("stripe_price_id"),
        display_order=request.get("display_order", 0),
        created_at=datetime.utcnow(),
    )
    db.add(package)
    await db.commit()
    await db.refresh(package)

    return {
        "id": str(package.id),
        "name": package.name,
        "credits": package.credits,
        "price_usd": float(package.price_usd),
    }


@router.post("/admin/credits/bonus")
async def grant_bonus_credits(
    request: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Grant bonus credits to a user (admin only)."""
    # TODO: Add admin check
    from app.models.db import User

    target_user_id = UUID(request.get("user_id"))
    amount = request.get("amount", 0)

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Get or create credits
    result = await db.execute(
        select(UserCredits).where(UserCredits.user_id == target_user_id)
    )
    credits = result.scalar_one_or_none()

    if not credits:
        credits = UserCredits(
            user_id=target_user_id,
            image_credits=amount,
            monthly_credits=5,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(credits)
    else:
        credits.image_credits += amount
        credits.updated_at = datetime.utcnow()

    # Log transaction
    transaction = CreditTransaction(
        id=uuid4(),
        user_id=target_user_id,
        amount=amount,
        transaction_type="bonus",
        description="Bonus credits granted",
        created_at=datetime.utcnow(),
    )
    db.add(transaction)

    await db.commit()

    return {"granted": amount}
