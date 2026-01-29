"""AI Image Generation Service.

Supports multiple providers:
- OpenAI DALL-E 3
- Stability AI
- Replicate (for SDXL, etc.)

Manages:
- Credit deduction for generation
- Asset storage
- Generation metadata tracking
"""

import asyncio
import hashlib
import base64
import mimetypes
from io import BytesIO
from datetime import datetime, timedelta
from typing import Optional, Literal
from uuid import UUID, uuid4

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.credit import UserCredits, CreditTransaction
from app.models.db.asset import Asset
from app.models.db import Project
from app.services.storage_service import StorageService


class ImageGenerationProvider:
    """Base class for image generation providers."""

    async def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
    ) -> list[dict]:
        """Generate images. Returns list of {url, metadata} dicts."""
        raise NotImplementedError

    def get_cost(self, width: int, height: int, quality: str = "standard") -> int:
        """Get credit cost for generation."""
        raise NotImplementedError


class OpenAIProvider(ImageGenerationProvider):
    """OpenAI DALL-E 3 provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"

    def get_cost(self, width: int = 1024, height: int = 1024, quality: str = "standard") -> int:
        """DALL-E 3 costs: standard=1 credit, HD=3 credits"""
        if quality == "hd":
            return 3
        return 1

    async def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        model: str = "dall-e-3",
        quality: str = "standard",
    ) -> list[dict]:
        """Generate images using DALL-E 3."""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Map requested size to DALL-E supported sizes
        size = self._get_closest_size(width, height)

        payload = {
            "model": model,
            "prompt": prompt,
            "n": min(num_images, 1),  # DALL-E 3 only supports n=1
            "size": size,
            "quality": quality,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/images/generations",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                error = response.text
                raise Exception(f"OpenAI API error: {error}")

            data = response.json()

        results = []
        for item in data.get("data", []):
            results.append({
                "url": item.get("url"),
                "revised_prompt": item.get("revised_prompt"),
                "metadata": {
                    "provider": "openai",
                    "model": model,
                    "size": size,
                    "quality": quality,
                },
            })

        return results

    def _get_closest_size(self, width: int, height: int) -> str:
        """Get closest DALL-E supported size."""
        # DALL-E 3 supports: 1024x1024, 1024x1792, 1792x1024
        if width == height:
            return "1024x1024"
        if width > height:
            return "1792x1024"
        return "1024x1792"


class StabilityAIProvider(ImageGenerationProvider):
    """Stability AI (Stable Diffusion) provider."""

    def __init__(self, api_key: str, host: str = "https://api.stability.ai"):
        self.api_key = api_key
        self.host = host

    def get_cost(self, width: int = 1024, height: int = 1024, quality: str = "standard") -> int:
        """Stable Diffusion costs: 1 credit per generation"""
        return 1

    async def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        model: str = "stable-diffusion-xl-1024-v1-0",
        quality: str = "standard",
    ) -> list[dict]:
        """Generate images using Stable Diffusion."""
        import httpx
        import base64

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        # SDXL endpoints (optionally upscale for HD)
        engine = "esrgan-v1-x2xx" if quality == "hd" else model
        url = f"{self.host}/v1/generation/{engine}/text-to-image"

        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "width": width,
            "height": height,
            "samples": num_images,
            "steps": 30,
        }

        if negative_prompt:
            payload["text_prompts"].append({
                "text": negative_prompt,
                "weight": -1,
            })

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                error = response.text
                raise Exception(f"Stability AI error: {error}")

            data = response.json()

        results = []
        for artifact in data.get("artifacts", []):
            # Decode base64 image
            image_data = base64.b64decode(artifact.get("base64", ""))

            # In a real implementation, upload to storage and get URL
            # For now, return placeholder
            results.append({
                "url": f"data:image/png;base64,{artifact.get('base64')}",
                "metadata": {
                    "provider": "stability",
                    "model": model,
                    "seed": artifact.get("seed"),
                    "width": width,
                    "height": height,
                },
            })

        return results


class ReplicateProvider(ImageGenerationProvider):
    """Replicate provider - supports many models via API."""

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.replicate.com/v1"

    def get_cost(self, width: int = 1024, height: int = 1024, quality: str = "standard") -> int:
        """Replicate costs vary by model - default to 2 credits"""
        return 2

    async def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        model: str = "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
    ) -> list[dict]:
        """Generate images using Replicate."""
        import httpx

        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json",
        }

        # Create prediction
        payload = {
            "input": {
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_outputs": num_images,
            }
        }

        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt

        async with httpx.AsyncClient(timeout=300.0) as client:
            # Start generation
            response = await client.post(
                f"{self.base_url}/predictions",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                error = response.text
                raise Exception(f"Replicate error: {error}")

            data = response.json()
            prediction_id = data.get("id")

            # Poll for result
            max_attempts = 120  # 2 minutes
            for _ in range(max_attempts):
                await asyncio.sleep(1)

                status_response = await client.get(
                    f"{self.base_url}/predictions/{prediction_id}",
                    headers=headers,
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")

                    if status == "succeeded":
                        results = []
                        for output in status_data.get("output", []):
                            results.append({
                                "url": output,
                                "metadata": {
                                    "provider": "replicate",
                                    "model": model,
                                    "prediction_id": prediction_id,
                                },
                            })
                        return results

                    elif status in ["failed", "canceled"]:
                        error_detail = status_data.get("error")
                        raise Exception(f"Replicate generation {status}: {error_detail}")

        raise Exception("Replicate generation timed out")


class ImageGenerationService:
    """Service for AI image generation with credit management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._providers = {}

    def _get_provider(self, provider_name: str, config: dict) -> ImageGenerationProvider:
        """Get or create a provider instance."""
        if provider_name not in self._providers:
            if provider_name == "openai":
                self._providers[provider_name] = OpenAIProvider(
                    api_key=config.get("api_key", "")
                )
            elif provider_name == "stability":
                self._providers[provider_name] = StabilityAIProvider(
                    api_key=config.get("api_key", ""),
                    host=config.get("host", "https://api.stability.ai")
                )
            elif provider_name == "replicate":
                self._providers[provider_name] = ReplicateProvider(
                    api_token=config.get("api_token", "")
                )
            else:
                raise ValueError(f"Unknown provider: {provider_name}")

        return self._providers[provider_name]

    async def _get_user_credits(self, user_id: UUID) -> UserCredits | None:
        """Get user's credit balance."""
        result = await self.db.execute(
            select(UserCredits).where(UserCredits.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _ensure_credits(self, user_id: UUID) -> UserCredits:
        """Ensure user has a credits record."""
        credits = await self._get_user_credits(user_id)

        if not credits:
            # Create with defaults
            credits = UserCredits(
                user_id=user_id,
                image_credits=0,
                purchased_credits=0,
                credits_used_this_month=0,
                monthly_credits=5,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(credits)
            await self.db.commit()
            await self.db.refresh(credits)

        return credits

    async def _check_and_deduct_credits(
        self,
        user_id: UUID,
        cost: int,
    ) -> bool:
        """
        Check if user has enough credits and deduct them.

        Returns True if successful, False otherwise.
        """
        credits = await self._ensure_credits(user_id)

        # Calculate available credits
        total_credits = (
            credits.monthly_credits
            - credits.credits_used_this_month
            + credits.image_credits
            + credits.purchased_credits
        )

        if total_credits < cost:
            return False

        # Deduct from monthly first, then purchased, then image credits
        remaining_monthly = credits.monthly_credits - credits.credits_used_this_month
        if remaining_monthly > 0:
            deduct_from_monthly = min(remaining_monthly, cost)
            credits.credits_used_this_month += deduct_from_monthly
            cost -= deduct_from_monthly

        if cost > 0 and credits.purchased_credits > 0:
            deduct_from_purchased = min(credits.purchased_credits, cost)
            credits.purchased_credits -= deduct_from_purchased
            cost -= deduct_from_purchased

        if cost > 0 and credits.image_credits > 0:
            credits.image_credits -= cost

        credits.updated_at = datetime.utcnow()
        await self.db.commit()

        # Log transaction
        transaction = CreditTransaction(
            id=uuid4(),
            user_id=user_id,
            amount=-cost,
            transaction_type="usage",
            description="AI image generation",
            meta_data={"service": "image_generation"},
            created_at=datetime.utcnow(),
        )
        self.db.add(transaction)
        await self.db.commit()

        return True

    async def _resolve_image_bytes(self, url: str) -> tuple[bytes | None, str | None]:
        """Resolve image bytes from a URL or data URI."""
        if url.startswith("data:"):
            try:
                header, b64 = url.split(",", 1)
                mime = header.split(";")[0].replace("data:", "")
                data = base64.b64decode(b64)
                return data, mime
            except Exception:
                return None, None

        if url.startswith("http"):
            import httpx

            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return response.content, response.headers.get("content-type")
            except Exception:
                return None, None

        return None, None

    def _guess_extension(self, mime_type: str | None) -> str:
        if not mime_type:
            return ".png"
        ext = mimetypes.guess_extension(mime_type.split(";")[0].strip()) or ".png"
        return ext

    def _get_dimensions(self, data: bytes) -> tuple[int | None, int | None]:
        try:
            from PIL import Image
        except ImportError:
            return None, None

        try:
            with Image.open(BytesIO(data)) as img:
                return img.width, img.height
        except Exception:
            return None, None

    def _generate_thumbnail(self, data: bytes, max_size: int = 400) -> bytes | None:
        try:
            from PIL import Image
        except ImportError:
            return None

        try:
            with Image.open(BytesIO(data)) as img:
                img.thumbnail((max_size, max_size))
                output = BytesIO()
                format_name = "PNG" if img.mode in ("RGBA", "P") else "JPEG"
                if format_name == "JPEG":
                    img = img.convert("RGB")
                img.save(output, format_name, quality=85)
                return output.getvalue()
        except Exception:
            return None

    async def generate_image(
        self,
        user_id: UUID,
        project_id: UUID | None,
        prompt: str,
        provider: str = "openai",
        provider_config: dict | None = None,
        negative_prompt: str | None = None,
        width: int = 1024,
        height: int = 1024,
        quality: str = "standard",
        model: str | None = None,
        save_to_library: bool = True,
        alt_text: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """
        Generate an AI image.

        Args:
            user_id: User requesting generation
            project_id: Optional project to associate with
            prompt: Image description
            provider: AI provider (openai, stability, replicate)
            provider_config: API config for the provider
            negative_prompt: Things to avoid in the image
            width: Image width in pixels
            height: Image height in pixels
            quality: Image quality (standard, hd)
            model: Specific model to use
            save_to_library: Whether to save to asset library
            alt_text: Alt text for accessibility
            tags: Tags for organization

        Returns:
            Dict with generated image data
        """
        provider_config = provider_config or {}

        # Get provider
        image_provider = self._get_provider(provider, provider_config)

        # Calculate cost
        cost = image_provider.get_cost(width, height, quality)

        # Check and deduct credits
        has_credits = await self._check_and_deduct_credits(user_id, cost)
        if not has_credits:
            return {
                "success": False,
                "error": "insufficient_credits",
                "required": cost,
            }

        # Generate image
        try:
            # Build kwargs for provider
            kwargs = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_images": 1,
            }

            if model:
                kwargs["model"] = model
            if quality:
                kwargs["quality"] = quality

            results = await image_provider.generate(**kwargs)

            if not results:
                return {
                    "success": False,
                    "error": "generation_failed",
                }

            result = results[0]

            # Save to asset library if requested
            if save_to_library:
                storage = StorageService()
                stored_url = result.get("url")
                thumbnail_url = None
                storage_key = None
                thumbnail_key = None
                file_size = None
                mime_type = None
                resolved_width = width
                resolved_height = height

                image_bytes, mime_type = await self._resolve_image_bytes(result.get("url", ""))
                if image_bytes:
                    ext = self._guess_extension(mime_type)
                    storage_key = f"{user_id}/generated/{uuid4().hex}{ext}"
                    stored_url = await storage.save_bytes(storage_key, image_bytes, mime_type)

                    thumb_bytes = self._generate_thumbnail(image_bytes)
                    if thumb_bytes:
                        thumbnail_key = f"{user_id}/generated/thumbs/{uuid4().hex}.jpg"
                        thumbnail_url = await storage.save_bytes(thumbnail_key, thumb_bytes, "image/jpeg")

                    dims = self._get_dimensions(image_bytes)
                    if dims[0] and dims[1]:
                        resolved_width, resolved_height = dims
                    file_size = len(image_bytes)

                asset = Asset(
                    id=uuid4(),
                    user_id=user_id,
                    project_id=project_id,
                    asset_type="generated",
                    url=stored_url,
                    thumbnail_url=thumbnail_url,
                    prompt=prompt,
                    generation_provider=provider,
                    generation_metadata={
                        **(result.get("metadata", {}) or {}),
                        "storage_key": storage_key,
                        "thumbnail_key": thumbnail_key,
                        "backend": storage.backend,
                    },
                    width=resolved_width,
                    height=resolved_height,
                    file_size_bytes=file_size,
                    mime_type=mime_type,
                    alt_text=alt_text or prompt,
                    tags=tags or [],
                    created_at=datetime.utcnow(),
                )
                self.db.add(asset)
                await self.db.commit()
                await self.db.refresh(asset)

                return {
                    "success": True,
                    "asset_id": str(asset.id),
                    "url": stored_url,
                    "width": resolved_width,
                    "height": resolved_height,
                    "provider": provider,
                    "metadata": result.get("metadata"),
                }

            return {
                "success": True,
                "url": result["url"],
                "width": width,
                "height": height,
                "provider": provider,
                "metadata": result.get("metadata"),
            }

        except Exception as e:
            # Refund credits on error
            await self._refund_credits(user_id, cost)

            return {
                "success": False,
                "error": str(e),
            }

    async def _refund_credits(self, user_id: UUID, amount: int) -> None:
        """Refund credits for failed generation."""
        credits = await self._ensure_credits(user_id)
        credits.purchased_credits += amount
        credits.updated_at = datetime.utcnow()

        # Log refund transaction
        transaction = CreditTransaction(
            id=uuid4(),
            user_id=user_id,
            amount=amount,
            transaction_type="bonus",
            description="Credit refund (generation failed)",
            created_at=datetime.utcnow(),
        )
        self.db.add(transaction)
        await self.db.commit()

    async def get_user_credit_balance(self, user_id: UUID) -> dict:
        """Get detailed credit balance for a user."""
        credits = await self._ensure_credits(user_id)

        # Calculate totals
        remaining_monthly = credits.monthly_credits - credits.credits_used_this_month
        total_available = (
            remaining_monthly
            + credits.image_credits
            + credits.purchased_credits
        )

        return {
            "total_available": total_available,
            "monthly_credits": credits.monthly_credits,
            "monthly_used": credits.credits_used_this_month,
            "monthly_remaining": remaining_monthly,
            "image_credits": credits.image_credits,
            "purchased_credits": credits.purchased_credits,
            "last_reset": credits.last_monthly_reset.isoformat() if credits.last_monthly_reset else None,
        }

    async def check_monthly_reset(self, user_id: UUID) -> None:
        """Check and perform monthly credit reset if needed."""
        credits = await self._ensure_credits(user_id)
        today = date.today()

        # Check if we need to reset (new month)
        if (
            credits.last_monthly_reset is None
            or credits.last_monthly_reset < today.replace(day=1)
        ):
            # First day of new month - reset
            credits.credits_used_this_month = 0
            credits.last_monthly_reset = today
            await self.db.commit()
