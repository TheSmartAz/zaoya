# Custom Domains Implementation Plan

> **Version**: v1 Phase 3
> **Created**: 2025-01-22
> **Updated**: 2025-01-22
> **Status**: Draft (Revised)
> **Complexity**: Medium-Large

---

## Architecture Decision Record

### Decision: Edge + SSL Architecture

| Component | Decision |
|-----------|----------|
| **Edge Server** | Caddy on dedicated Aliyun ECS |
| **SSL Certificates** | Let's Encrypt via Caddy on-demand TLS |
| **Backend** | FastAPI validates domains + serves pages |
| **Certificate Storage** | Local Caddy storage (v1); shared storage for HA (v2+) |

**Rationale**: Self-hosted Caddy provides free SSL via Let's Encrypt, works well in China, and requires no external service dependency. On-demand TLS means certificates are provisioned automatically on first request after domain verification.

---

## Overview

Enable Zaoya users to connect custom domains to their published pages. Users can publish their pages on their own domain (e.g., `example.com` or `www.example.com`) instead of the default `zaoya.app/p/{id}` URL.

### Goals

1. Users can add one custom domain to their project (1:1 mapping)
2. DNS verification ensures domain ownership via TXT record
3. SSL certificates are automatically provisioned (free via Let's Encrypt)
4. Published pages are served on custom domains with HTTPS
5. Deterministic www redirect behavior (no per-user configuration)

### Non-Goals (v1)

- Multiple domains per project (strict 1:1 mapping)
- Per-user www/non-www redirect configuration (deterministic default only)
- Subdomain wildcards (`*.example.com`)
- Domain transfer between projects
- Custom SSL certificate upload
- Punycode/IDN domain support (ASCII only for v1)

### Canonical URL Policy (v1)

**Deterministic behavior with no user configuration:**

| User Configures | Canonical URL | Redirect Behavior |
|-----------------|---------------|-------------------|
| Apex domain (`example.com`) | `https://example.com` | `www.example.com` → 301 → `example.com` |
| Subdomain (`www.example.com`) | `https://www.example.com` | No automatic redirect |
| Other subdomain (`blog.example.com`) | `https://blog.example.com` | No automatic redirect |

This keeps implementation simple while providing sensible defaults.

### Plan Limits

**Domain limits follow project limits (not separate entitlement):**

| Plan | Project Limit | Custom Domains |
|------|---------------|----------------|
| Pro | 1 project | 1 domain (implicit) |
| Team | 3 projects | 3 domains (implicit) |
| Business | 10 projects | 10 domains (implicit) |

Each project may have **at most one custom domain**. Enforced via `UNIQUE(project_id)` constraint.

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Custom Domain Request Flow                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   User Browser                                                              │
│        │                                                                    │
│        │ https://example.com                                                │
│        ▼                                                                    │
│   ┌──────────────────────────────┐                                         │
│   │      Aliyun ECS Server       │                                         │
│   │         (Caddy)              │                                         │
│   │                              │                                         │
│   │  • Receives all custom       │                                         │
│   │    domain traffic            │                                         │
│   │  • On-demand SSL via         │                                         │
│   │    Let's Encrypt             │                                         │
│   │  • Validates domain with     │                                         │
│   │    backend (+ shared secret) │                                         │
│   │  • Proxies to backend        │                                         │
│   │  • Handles www→apex redirect │                                         │
│   └──────────────┬───────────────┘                                         │
│                  │                                                          │
│                  │ 1. Ask: Is this domain valid? (with X-Zaoya-Edge-Secret) │
│                  │ 2. Proxy request with X-Custom-Domain + secret header   │
│                  ▼                                                          │
│   ┌──────────────────────────────┐      ┌────────────────────────────┐    │
│   │      Zaoya Backend           │      │       PostgreSQL           │    │
│   │      (FastAPI)               │      │                            │    │
│   │                              │◄────►│  • custom_domains table    │    │
│   │  • /api/internal/domain/check│      │  • projects table          │    │
│   │  • Validates edge secret     │      │  • audit_events table      │    │
│   │  • Custom domain middleware  │      │  • pages/snapshots         │    │
│   │  • Serves published HTML     │      │                            │    │
│   └──────────────────────────────┘      └────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DNS Setup Options

**Users have two paths depending on their registrar capabilities:**

#### Option A: Subdomain (Recommended - Lowest Support Burden)

| Record | Host | Value |
|--------|------|-------|
| TXT | `_zaoya-verify` | `zaoya-site-verification={token}` |
| CNAME | `www` | `pages.zaoya.app` |

User's custom domain: `www.example.com`

#### Option B: Apex/Root Domain

| Record | Host | Value |
|--------|------|-------|
| TXT | `_zaoya-verify` | `zaoya-site-verification={token}` |
| ALIAS/ANAME | `@` | `pages.zaoya.app` |
| -OR- A | `@` | `{ECS_PUBLIC_IP}` |

User's custom domain: `example.com`

**Note**: Many registrars don't support CNAME at apex (`@`). The UI must clearly show both options with helper text: *"If your provider doesn't support CNAME at @, use ALIAS/ANAME or A record."*

---

## Data Model

### New Table: custom_domains

```sql
CREATE TABLE custom_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
    -- UNIQUE enforces 1:1 mapping

    -- Domain info
    domain VARCHAR(255) NOT NULL UNIQUE,
    is_apex BOOLEAN NOT NULL DEFAULT false,  -- true if apex domain (for www redirect logic)

    -- Verification
    verification_token VARCHAR(64) NOT NULL,
    verification_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- State machine: 'pending' → 'verified' → 'active'
    --                'pending' → 'failed' (after expiry)
    --                'verified' → 'error' (SSL issues)
    verified_at TIMESTAMP WITH TIME ZONE,
    verification_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,  -- created_at + 7 days

    -- SSL status (informational, Caddy manages actual certs)
    ssl_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- Values: 'pending', 'provisioning', 'active', 'error'
    ssl_provisioned_at TIMESTAMP WITH TIME ZONE,

    -- Operational fields
    last_checked_at TIMESTAMP WITH TIME ZONE,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    failure_reason VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_verification_status
        CHECK (verification_status IN ('pending', 'verified', 'failed', 'active')),
    CONSTRAINT valid_ssl_status
        CHECK (ssl_status IN ('pending', 'provisioning', 'active', 'error'))
);

-- Indexes
CREATE INDEX idx_custom_domains_domain ON custom_domains(domain);
CREATE INDEX idx_custom_domains_verification_status ON custom_domains(verification_status);
CREATE INDEX idx_custom_domains_verification_expires ON custom_domains(verification_expires_at)
    WHERE verification_status = 'pending';
```

### State Machine

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
┌─────────┐    TXT record    ┌──────────┐    First HTTPS    ┌────────┐
│ pending │ ───────ok───────►│ verified │ ────request────►  │ active │
└─────────┘                  └──────────┘    served ok      └────────┘
     │                            │                              │
     │ 7 days expired             │ SSL provision                │ SSL renewal
     │ or max attempts            │ fails repeatedly             │ fails
     ▼                            ▼                              ▼
┌─────────┐                  ┌─────────┐                    ┌─────────┐
│ failed  │                  │  error  │◄───────────────────│  error  │
└─────────┘                  └─────────┘                    └─────────┘
```

### SQLAlchemy Model

```python
# backend/app/models/db/custom_domain.py

from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid

from app.models.db import Base

class CustomDomain(Base):
    __tablename__ = "custom_domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Enforces 1:1 mapping
        index=True
    )

    # Domain
    domain = Column(String(255), nullable=False, unique=True, index=True)
    is_apex = Column(Boolean, nullable=False, default=False)

    # Verification
    verification_token = Column(String(64), nullable=False)
    verification_status = Column(String(20), nullable=False, default="pending")
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_expires_at = Column(DateTime(timezone=True), nullable=False)

    # SSL
    ssl_status = Column(String(20), nullable=False, default="pending")
    ssl_provisioned_at = Column(DateTime(timezone=True), nullable=True)

    # Operational
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    failure_reason = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="custom_domain")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.verification_expires_at:
            self.verification_expires_at = datetime.utcnow() + timedelta(days=7)

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('pending', 'verified', 'failed', 'active')",
            name="valid_verification_status"
        ),
        CheckConstraint(
            "ssl_status IN ('pending', 'provisioning', 'active', 'error')",
            name="valid_ssl_status"
        ),
    )
```

### New Table: audit_events (Future-Proofing for Teams)

```sql
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    team_id UUID,  -- Nullable, for future team support

    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,

    metadata JSONB,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_events_user_id ON audit_events(user_id);
CREATE INDEX idx_audit_events_resource ON audit_events(resource_type, resource_id);
CREATE INDEX idx_audit_events_created_at ON audit_events(created_at);
```

**Logged actions for custom domains:**
- `domain.added`
- `domain.verified`
- `domain.removed`
- `domain.verification_failed`

---

## API Endpoints

### Public Endpoints (require auth)

#### POST /api/projects/{project_id}/domain

Add a custom domain to a project.

**Request:**
```json
{
    "domain": "example.com"
}
```

**Response (201):**
```json
{
    "id": "uuid",
    "domain": "example.com",
    "is_apex": true,
    "verification_status": "pending",
    "verification_expires_at": "2025-01-29T10:00:00Z",
    "ssl_status": "pending",
    "dns_instructions": {
        "recommended": {
            "description": "For subdomain (www.example.com)",
            "records": [
                {"type": "TXT", "host": "_zaoya-verify", "value": "zaoya-site-verification=abc123..."},
                {"type": "CNAME", "host": "www", "value": "pages.zaoya.app"}
            ]
        },
        "apex": {
            "description": "For root domain (example.com)",
            "records": [
                {"type": "TXT", "host": "_zaoya-verify", "value": "zaoya-site-verification=abc123..."},
                {"type": "ALIAS", "host": "@", "value": "pages.zaoya.app", "note": "Or use A record with IP: x.x.x.x"}
            ]
        }
    },
    "created_at": "2025-01-22T10:00:00Z"
}
```

**Errors:**
- 400: Invalid domain format
- 400: Domain already in use by another project
- 403: Project not owned by user
- 409: Project already has a custom domain

#### GET /api/projects/{project_id}/domain

Get custom domain configuration for a project.

**Response (200):** Same as POST response with current status

**Errors:**
- 404: No custom domain configured

#### POST /api/projects/{project_id}/domain/verify

Manually trigger domain verification check.

**Response (200):**
```json
{
    "verification_status": "verified",
    "verified_at": "2025-01-22T10:30:00Z",
    "message": "Domain verified successfully"
}
```

**Response (200, not verified):**
```json
{
    "verification_status": "pending",
    "attempt_count": 3,
    "message": "DNS records not found. Please check your configuration.",
    "checks": {
        "txt_record": false,
        "routing_record": true
    }
}
```

#### DELETE /api/projects/{project_id}/domain

Remove custom domain from project.

**Response (204):** No content

### Internal Endpoints (Caddy only)

#### GET /api/internal/domain/check

Called by Caddy to verify if a domain should be issued an SSL certificate.

**Required Headers:**
- `X-Zaoya-Edge-Secret`: Must match `ZAOYA_EDGE_SECRET` env var

**Query Parameters:**
- `domain`: The domain to check (normalized, lowercase, no trailing dot)

**Response (200):** Domain is valid, proceed with SSL
```json
{
    "valid": true,
    "project_id": "uuid",
    "is_apex": true
}
```

**Response (403):** Invalid or missing edge secret
```json
{
    "error": "Forbidden"
}
```

**Response (404):** Domain not valid, reject
```json
{
    "valid": false,
    "reason": "Domain not found or not verified"
}
```

**Security (Defense in Depth):**
1. **Required**: Shared secret header (`X-Zaoya-Edge-Secret`)
2. **Recommended**: Source IP allowlist (Caddy server IP)
3. **Required**: Rate limiting (10 req/min per unique domain)
4. **Required**: Strict domain validation (normalize, lowercase, reject invalid chars)

---

## Services

### DomainService

```python
# backend/app/services/domain_service.py

import dns.resolver
import secrets
import re
from typing import Optional, Tuple, List
from datetime import datetime, timedelta

class DomainService:
    """Service for custom domain management"""

    VERIFICATION_PREFIX = "zaoya-site-verification="
    PAGES_DOMAIN = "pages.zaoya.app"

    # Blocked zones (exact match or suffix)
    BLOCKED_ZONES = [
        "zaoya.app",
        "zaoya.com",
        "localhost",
        "local",
        "internal",
        "example.com",
        "example.org",
        "example.net",
        "test",
        "invalid",
    ]

    @staticmethod
    def normalize_domain(domain: str) -> str:
        """Normalize domain: lowercase, strip whitespace, remove trailing dot"""
        return domain.lower().strip().rstrip(".")

    @staticmethod
    def validate_domain(domain: str) -> Tuple[bool, Optional[str]]:
        """
        Validate domain format.
        Returns (is_valid, error_message)
        """
        domain = DomainService.normalize_domain(domain)

        # Check length
        if len(domain) > 253:
            return False, "Domain too long (max 253 characters)"

        # ASCII only for v1 (no punycode/IDN)
        if not domain.isascii():
            return False, "Only ASCII domains are supported"

        # Basic format check
        domain_pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
        if not re.match(domain_pattern, domain):
            return False, "Invalid domain format"

        # Check for IP addresses
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        if re.match(ip_pattern, domain):
            return False, "IP addresses are not allowed"

        # Block reserved zones (exact match or suffix)
        for blocked in DomainService.BLOCKED_ZONES:
            if domain == blocked or domain.endswith(f".{blocked}"):
                return False, f"Domain '{blocked}' is not allowed"

        return True, None

    @staticmethod
    def is_apex_domain(domain: str) -> bool:
        """Check if domain is apex (no subdomain prefix)"""
        parts = domain.split(".")
        # apex: example.com (2 parts) or example.co.uk (3 parts with known SLD)
        # For simplicity, treat 2-part domains as apex
        return len(parts) == 2

    @staticmethod
    def generate_verification_token() -> str:
        """Generate a random verification token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_dns_instructions(domain: str, token: str, edge_ip: str) -> dict:
        """Return DNS record instructions for the user"""
        base_domain = ".".join(domain.split(".")[-2:])  # Get apex from any subdomain

        return {
            "recommended": {
                "description": f"For subdomain (www.{base_domain})",
                "records": [
                    {
                        "type": "TXT",
                        "host": "_zaoya-verify",
                        "value": f"zaoya-site-verification={token}",
                    },
                    {
                        "type": "CNAME",
                        "host": "www",
                        "value": "pages.zaoya.app",
                    }
                ]
            },
            "apex": {
                "description": f"For root domain ({base_domain})",
                "records": [
                    {
                        "type": "TXT",
                        "host": "_zaoya-verify",
                        "value": f"zaoya-site-verification={token}",
                    },
                    {
                        "type": "ALIAS/ANAME",
                        "host": "@",
                        "value": "pages.zaoya.app",
                        "note": f"If ALIAS not supported, use A record: {edge_ip}",
                    }
                ]
            },
            "help_text": "If your provider doesn't support CNAME/ALIAS at @, use an A record pointing to our server IP."
        }

    @staticmethod
    async def verify_txt_record(domain: str, expected_token: str) -> bool:
        """Check if TXT record exists with correct token"""
        domain = DomainService.normalize_domain(domain)
        # Get base domain for TXT lookup
        parts = domain.split(".")
        base_domain = ".".join(parts[-2:]) if len(parts) > 2 else domain

        try:
            answers = dns.resolver.resolve(
                f"_zaoya-verify.{base_domain}",
                "TXT",
                lifetime=10
            )

            for rdata in answers:
                txt_value = "".join([
                    s.decode() if isinstance(s, bytes) else s
                    for s in rdata.strings
                ])
                expected = f"zaoya-site-verification={expected_token}"
                if txt_value == expected:
                    return True

            return False
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            return False
        except Exception:
            return False

    @staticmethod
    async def verify_routing_record(domain: str) -> Tuple[bool, str]:
        """
        Check if domain has valid routing to our edge.
        Returns (is_valid, record_type)
        """
        domain = DomainService.normalize_domain(domain)

        # Try CNAME first
        try:
            answers = dns.resolver.resolve(domain, "CNAME", lifetime=10)
            for rdata in answers:
                target = str(rdata.target).rstrip(".").lower()
                if target == "pages.zaoya.app":
                    return True, "CNAME"
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            pass
        except Exception:
            pass

        # Try A record (we can't verify it points to us without knowing all our IPs)
        # Just check if A record exists - actual routing will be validated on request
        try:
            answers = dns.resolver.resolve(domain, "A", lifetime=10)
            if answers:
                return True, "A"  # Has A record, assume user configured correctly
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            pass
        except Exception:
            pass

        return False, "none"

    @staticmethod
    async def verify_domain(domain: str, expected_token: str) -> dict:
        """
        Full domain verification check.
        Returns dict with check results.
        """
        txt_valid = await DomainService.verify_txt_record(domain, expected_token)
        routing_valid, routing_type = await DomainService.verify_routing_record(domain)

        return {
            "verified": txt_valid,  # TXT is required for ownership proof
            "checks": {
                "txt_record": txt_valid,
                "routing_record": routing_valid,
                "routing_type": routing_type,
            }
        }
```

### AccessControlService (Future-Proofing for Teams)

```python
# backend/app/services/access_control.py

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db.project import Project
from app.models.db.user import User

class Permission:
    PROJECT_VIEW = "project:view"
    PROJECT_EDIT = "project:edit"
    PROJECT_DELETE = "project:delete"
    PROJECT_PUBLISH = "project:publish"
    DOMAIN_MANAGE = "domain:manage"

class AccessControlService:
    """
    Centralized permission checks.
    Currently user-only; ready for team RBAC extension.
    """

    @staticmethod
    async def can_access_project(
        db: AsyncSession,
        user: User,
        project: Project,
        permission: str
    ) -> bool:
        """
        Check if user has permission on project.
        For v1: Owner has all permissions.
        For v2+: Will check team membership and roles.
        """
        # v1: Simple owner check
        if project.user_id == user.id:
            return True

        # Future: Check team membership
        # if project.owner_type == "team":
        #     member = await get_team_member(db, project.owner_id, user.id)
        #     if member:
        #         return permission in get_role_permissions(member.role)

        return False

    @staticmethod
    async def require_project_access(
        db: AsyncSession,
        user: User,
        project: Project,
        permission: str
    ) -> None:
        """Raise HTTPException if access denied"""
        from fastapi import HTTPException

        if not await AccessControlService.can_access_project(db, user, project, permission):
            raise HTTPException(status_code=403, detail="Access denied")
```

---

## Middleware

### CustomDomainMiddleware (Secure)

```python
# backend/app/middleware/custom_domain.py

import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class CustomDomainMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and handle custom domain requests.

    SECURITY: Only trusts X-Custom-Domain header when:
    1. Valid X-Zaoya-Edge-Secret is present, AND
    2. (Optional) Request is from allowed edge IP

    When Caddy proxies a request, it adds:
    - X-Custom-Domain: The original host header (e.g., example.com)
    - X-Zaoya-Edge-Secret: Shared secret for authentication
    - X-Forwarded-Proto: The original protocol (https)
    """

    ZAOYA_DOMAINS = ["zaoya.app", "localhost", "127.0.0.1"]

    def __init__(self, app, edge_secret: str = None, allowed_edge_ips: list = None):
        super().__init__(app)
        self.edge_secret = edge_secret or os.environ.get("ZAOYA_EDGE_SECRET")
        self.allowed_edge_ips = allowed_edge_ips or []

    async def dispatch(self, request: Request, call_next):
        custom_domain = None
        is_custom_domain = False

        # Only trust X-Custom-Domain if edge secret is valid
        provided_secret = request.headers.get("X-Zaoya-Edge-Secret")
        header_domain = request.headers.get("X-Custom-Domain")

        if header_domain and self._is_valid_edge_request(request, provided_secret):
            # Normalize domain
            normalized = header_domain.lower().strip().rstrip(".")

            # Check if this is actually a custom domain (not our own)
            is_custom_domain = not any(
                normalized.endswith(d) for d in self.ZAOYA_DOMAINS
            )

            if is_custom_domain:
                custom_domain = normalized

        # Attach to request state for downstream handlers
        request.state.custom_domain = custom_domain
        request.state.is_custom_domain = is_custom_domain

        response = await call_next(request)
        return response

    def _is_valid_edge_request(self, request: Request, provided_secret: str) -> bool:
        """Validate the request is from our edge server"""
        # Check secret
        if not self.edge_secret or provided_secret != self.edge_secret:
            return False

        # Optional: Check source IP
        if self.allowed_edge_ips:
            client_ip = request.client.host if request.client else None
            forwarded_for = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            real_ip = request.headers.get("X-Real-IP")

            request_ip = real_ip or forwarded_for or client_ip
            if request_ip not in self.allowed_edge_ips:
                return False

        return True
```

---

## Internal Endpoint Security

### Domain Check Endpoint (Hardened)

```python
# backend/app/api/internal.py

import os
import re
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.db.custom_domain import CustomDomain
from app.database import get_db

router = APIRouter(prefix="/api/internal", tags=["internal"])

EDGE_SECRET = os.environ.get("ZAOYA_EDGE_SECRET")

def verify_edge_secret(request: Request):
    """Dependency to verify edge server authentication"""
    provided = request.headers.get("X-Zaoya-Edge-Secret")
    if not EDGE_SECRET or provided != EDGE_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

def normalize_and_validate_domain(domain: str) -> str:
    """Normalize and strictly validate domain input"""
    if not domain:
        raise HTTPException(status_code=400, detail="Domain required")

    # Normalize
    domain = domain.lower().strip().rstrip(".")

    # Length check
    if len(domain) > 253:
        raise HTTPException(status_code=400, detail="Domain too long")

    # ASCII only
    if not domain.isascii():
        raise HTTPException(status_code=400, detail="Invalid domain")

    # Format check (strict)
    pattern = r'^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
    if not re.match(pattern, domain):
        raise HTTPException(status_code=400, detail="Invalid domain format")

    # No ports
    if ":" in domain:
        raise HTTPException(status_code=400, detail="Invalid domain")

    return domain

@router.get("/domain/check")
async def check_domain(
    domain: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_edge_secret)  # Security check
):
    """
    Called by Caddy to verify if a domain should be issued an SSL certificate.
    Protected by shared secret.
    """
    # Validate and normalize input
    domain = normalize_and_validate_domain(domain)

    # Look up domain
    result = await db.execute(
        select(CustomDomain)
        .where(CustomDomain.domain == domain)
        .where(CustomDomain.verification_status.in_(["verified", "active"]))
    )
    custom_domain = result.scalar_one_or_none()

    if not custom_domain:
        return {"valid": False, "reason": "Domain not found or not verified"}

    # Update SSL status on first successful check
    if custom_domain.ssl_status == "pending":
        custom_domain.ssl_status = "provisioning"
        await db.commit()

    return {
        "valid": True,
        "project_id": str(custom_domain.project_id),
        "is_apex": custom_domain.is_apex
    }

@router.post("/domain/{domain}/ssl-active")
async def mark_ssl_active(
    domain: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_edge_secret)
):
    """Called by Caddy after successful SSL provisioning"""
    domain = normalize_and_validate_domain(domain)

    result = await db.execute(
        select(CustomDomain).where(CustomDomain.domain == domain)
    )
    custom_domain = result.scalar_one_or_none()

    if custom_domain:
        custom_domain.ssl_status = "active"
        custom_domain.ssl_provisioned_at = datetime.utcnow()
        if custom_domain.verification_status == "verified":
            custom_domain.verification_status = "active"
        await db.commit()

    return {"status": "ok"}
```

---

## Infrastructure Setup

### Aliyun ECS Requirements

| Requirement | Specification |
|-------------|---------------|
| OS | Ubuntu 22.04 LTS or Debian 12 |
| vCPU | 1 core minimum (2 recommended) |
| RAM | 1 GB minimum (2 GB recommended) |
| Storage | 20 GB SSD |
| Network | Public IP address (elastic IP recommended) |
| Bandwidth | 1 Mbps minimum |

### Security Group Rules

| Direction | Protocol | Port | Source | Description |
|-----------|----------|------|--------|-------------|
| Inbound | TCP | 80 | 0.0.0.0/0 | HTTP (for ACME challenges) |
| Inbound | TCP | 443 | 0.0.0.0/0 | HTTPS |
| Inbound | TCP | 22 | Your IP only | SSH access |
| Outbound | All | All | 0.0.0.0/0 | Allow all outbound |

### Caddy Installation Script (with Security)

```bash
#!/bin/bash
# setup-caddy.sh
# Run on Aliyun ECS as root

set -e

# Configuration - SET THESE
ZAOYA_EDGE_SECRET="${ZAOYA_EDGE_SECRET:-$(openssl rand -base64 32)}"
ZAOYA_BACKEND_URL="${ZAOYA_BACKEND_URL:-https://api.zaoya.app}"

echo "=== Installing Caddy ==="

apt update
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl

curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list

apt update
apt install -y caddy

echo "=== Configuring Caddy ==="

mv /etc/caddy/Caddyfile /etc/caddy/Caddyfile.default

cat > /etc/caddy/Caddyfile << EOF
{
    email admin@zaoya.app

    on_demand_tls {
        ask ${ZAOYA_BACKEND_URL}/api/internal/domain/check
        interval 1m
        burst 5
    }
}

# Catch-all for custom domains
https:// {
    tls {
        on_demand
    }

    # Handle www -> apex redirect for apex domains
    @www_redirect {
        header_regexp host Host ^www\.(.+)$
    }
    # Note: Redirect logic handled by backend based on is_apex flag

    reverse_proxy ${ZAOYA_BACKEND_URL} {
        header_up X-Custom-Domain {host}
        header_up X-Zaoya-Edge-Secret ${ZAOYA_EDGE_SECRET}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-Proto {scheme}

        health_uri /health
        health_interval 30s
    }

    log {
        output file /var/log/caddy/access.log {
            roll_size 100mb
            roll_keep 5
        }
        format json
    }
}

http://:8080 {
    respond /health "OK" 200
}
EOF

mkdir -p /var/log/caddy
chown caddy:caddy /var/log/caddy

echo "=== Starting Caddy ==="

systemctl enable caddy
systemctl restart caddy
systemctl status caddy

echo "=== Setup Complete ==="
echo ""
echo "IMPORTANT: Save this edge secret and add to backend env:"
echo "ZAOYA_EDGE_SECRET=${ZAOYA_EDGE_SECRET}"
echo ""
echo "Next steps:"
echo "1. Add this IP to backend ALLOWED_EDGE_IPS if using IP allowlist"
echo "2. Point pages.zaoya.app A record to this server's IP"
```

### HA/Scaling Notes (Phase 3.5 / Ops)

> **Warning**: v1 starts with a single Caddy instance. For production reliability:

1. **Multiple Instances**: Deploy 2+ Caddy instances behind a load balancer
2. **Shared Certificate Storage**: Use Caddy's storage modules (Redis, Consul, S3) to share certs across nodes
3. **Centralized Logging**: Ship logs to centralized system (ELK, Loki)
4. **Health Checks**: Load balancer should check `/health` endpoint on port 8080
5. **Sticky Sessions**: Not required (stateless proxy)

---

## Background Jobs

### Domain Verification Job (with Expiry)

```python
# backend/app/jobs/domain_verification.py

from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db.custom_domain import CustomDomain
from app.services.domain_service import DomainService
from app.services.audit_service import AuditService

MAX_VERIFICATION_ATTEMPTS = 100  # ~8 hours at 5-min intervals

async def domain_verification_job(db: AsyncSession):
    """
    Background job to automatically verify pending domains.
    Run every 5 minutes via scheduler.
    """
    now = datetime.utcnow()

    # 1. Expire old pending domains
    expired_result = await db.execute(
        select(CustomDomain)
        .where(CustomDomain.verification_status == "pending")
        .where(CustomDomain.verification_expires_at < now)
    )
    for domain in expired_result.scalars().all():
        domain.verification_status = "failed"
        domain.failure_reason = "Verification period expired (7 days)"
        await AuditService.log(
            db,
            action="domain.verification_failed",
            resource_type="custom_domain",
            resource_id=domain.id,
            metadata={"reason": "expired"}
        )

    # 2. Check pending domains not checked in last 5 minutes
    cutoff = now - timedelta(minutes=5)

    result = await db.execute(
        select(CustomDomain)
        .where(CustomDomain.verification_status == "pending")
        .where(
            (CustomDomain.last_checked_at == None) |
            (CustomDomain.last_checked_at < cutoff)
        )
        .where(CustomDomain.attempt_count < MAX_VERIFICATION_ATTEMPTS)
    )

    for domain in result.scalars().all():
        try:
            verification = await DomainService.verify_domain(
                domain.domain,
                domain.verification_token
            )

            domain.last_checked_at = now
            domain.attempt_count += 1

            if verification["verified"]:
                domain.verification_status = "verified"
                domain.verified_at = now
                domain.failure_reason = None

                await AuditService.log(
                    db,
                    action="domain.verified",
                    resource_type="custom_domain",
                    resource_id=domain.id
                )

        except Exception as e:
            domain.last_checked_at = now
            domain.attempt_count += 1
            # Log but continue

    await db.commit()
```

---

## Frontend Components

### DnsInstructions.tsx (Updated with Both Options)

```tsx
// frontend/src/components/domain/DnsInstructions.tsx

import { useState } from 'react';
import { Copy, Check, AlertCircle } from 'lucide-react';

interface DnsInstructions {
  recommended: {
    description: string;
    records: DnsRecord[];
  };
  apex: {
    description: string;
    records: DnsRecord[];
  };
  help_text: string;
}

interface DnsRecord {
  type: string;
  host: string;
  value: string;
  note?: string;
}

interface Props {
  instructions: DnsInstructions;
  domain: string;
}

export function DnsInstructions({ instructions, domain }: Props) {
  const [copied, setCopied] = useState<string | null>(null);
  const [showApex, setShowApex] = useState(false);

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const renderRecords = (records: DnsRecord[], prefix: string) => (
    <table className="min-w-full text-sm">
      <thead>
        <tr className="border-b">
          <th className="text-left py-2 pr-4">Type</th>
          <th className="text-left py-2 pr-4">Host</th>
          <th className="text-left py-2">Value</th>
        </tr>
      </thead>
      <tbody>
        {records.map((record, i) => (
          <tr key={i} className="border-b">
            <td className="py-2 pr-4 font-mono text-xs">{record.type}</td>
            <td className="py-2 pr-4 font-mono text-xs">{record.host}</td>
            <td className="py-2">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded break-all">
                    {record.value}
                  </code>
                  <button
                    onClick={() => copyToClipboard(record.value, `${prefix}-${i}`)}
                    className="p-1 hover:bg-gray-100 rounded shrink-0"
                    title="Copy"
                  >
                    {copied === `${prefix}-${i}` ? (
                      <Check className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4 text-gray-400" />
                    )}
                  </button>
                </div>
                {record.note && (
                  <span className="text-xs text-gray-500">{record.note}</span>
                )}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <div className="space-y-4">
      <p className="text-sm font-medium">
        Add these DNS records at your domain registrar:
      </p>

      {/* Tab switcher */}
      <div className="flex border-b">
        <button
          onClick={() => setShowApex(false)}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
            !showApex
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Subdomain (Recommended)
        </button>
        <button
          onClick={() => setShowApex(true)}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
            showApex
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Root Domain
        </button>
      </div>

      {/* Instructions */}
      <div className="p-4 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600 mb-3">
          {showApex ? instructions.apex.description : instructions.recommended.description}
        </p>
        {renderRecords(
          showApex ? instructions.apex.records : instructions.recommended.records,
          showApex ? 'apex' : 'rec'
        )}
      </div>

      {/* Help text */}
      <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <p className="text-xs text-amber-800">
          {instructions.help_text}
        </p>
      </div>
    </div>
  );
}
```

---

## Testing Plan

### Manual Testing Checklist

**Domain Addition:**
- [ ] Add valid subdomain (www.example.com)
- [ ] Add valid apex domain (example.com)
- [ ] Reject invalid format (not-a-domain)
- [ ] Reject IP address (192.168.1.1)
- [ ] Reject zaoya.app subdomains
- [ ] Reject localhost/local domains
- [ ] Reject domain already used by another project (400)
- [ ] Reject if project already has domain (409)

**DNS Instructions:**
- [ ] Shows both subdomain and apex options
- [ ] Copy buttons work
- [ ] Help text visible for ALIAS/A fallback

**Verification:**
- [ ] Manual verify button works
- [ ] Shows attempt count
- [ ] Marks as verified when TXT record found
- [ ] Marks as failed after 7 days expiry
- [ ] Auto-verification job runs every 5 minutes

**SSL & Access:**
- [ ] First request triggers SSL provisioning
- [ ] Published page accessible via custom domain
- [ ] www.example.com redirects to example.com (if apex configured)
- [ ] Correct canonical URL in HTML

**Security:**
- [ ] /api/internal/domain/check rejects without X-Zaoya-Edge-Secret
- [ ] X-Custom-Domain header ignored without valid secret
- [ ] Rate limiting on internal endpoint

---

## Implementation Tasks

### Phase 0: Pre-requisites

- [ ] Generate and configure `ZAOYA_EDGE_SECRET` env var
- [ ] Document ECS public IP for DNS setup

### Phase 1: Backend Foundation (Day 1-2)

- [ ] Create Alembic migration for `custom_domains` table (with all fields)
- [ ] Create Alembic migration for `audit_events` table
- [ ] Create `CustomDomain` SQLAlchemy model
- [ ] Update `Project` model with relationship
- [ ] Create `DomainService` with validation and DNS lookup
- [ ] Create `AccessControlService` (centralized permissions)
- [ ] Create `AuditService` for logging
- [ ] Install `dnspython` dependency

### Phase 2: API Endpoints (Day 2-3)

- [ ] POST /api/projects/{id}/domain - Add domain
- [ ] GET /api/projects/{id}/domain - Get domain
- [ ] POST /api/projects/{id}/domain/verify - Verify domain
- [ ] DELETE /api/projects/{id}/domain - Remove domain
- [ ] GET /api/internal/domain/check - Internal check (secured)
- [ ] POST /api/internal/domain/{domain}/ssl-active - SSL callback
- [ ] Add Pydantic schemas

### Phase 3: Middleware & Routing (Day 3)

- [ ] Create `CustomDomainMiddleware` (with secret validation)
- [ ] Register middleware in FastAPI app
- [ ] Update page serving to handle custom domains
- [ ] Add www→apex redirect for apex domains
- [ ] Update canonical URL generation

### Phase 4: Frontend UI (Day 4-5)

- [ ] Create `DomainSettings` component
- [ ] Create `DomainForm` component
- [ ] Create `DnsInstructions` component (both options)
- [ ] Create `DomainStatus` badge component
- [ ] Add domain settings to project settings page
- [ ] Add auto-refresh for pending verification

### Phase 5: Infrastructure (Day 5-6)

- [ ] Set up Aliyun ECS instance
- [ ] Install and configure Caddy with edge secret
- [ ] Configure security group rules
- [ ] Point pages.zaoya.app to ECS IP
- [ ] Test SSL provisioning with test domain
- [ ] Add ECS IP to backend allowlist (optional)

### Phase 6: Background Jobs (Day 6)

- [ ] Create domain verification job with expiry handling
- [ ] Set up APScheduler
- [ ] Configure job to run every 5 minutes
- [ ] Add audit logging

### Phase 7: Testing & Polish (Day 7)

- [ ] Write unit tests for DomainService
- [ ] Write integration tests for API endpoints
- [ ] Manual end-to-end testing
- [ ] Security testing (header spoofing, endpoint access)
- [ ] Documentation updates

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ZAOYA_EDGE_SECRET` | Yes | Shared secret for edge↔backend auth |
| `ALLOWED_EDGE_IPS` | No | Comma-separated list of edge server IPs |
| `EDGE_SERVER_IP` | Yes | Public IP of Caddy ECS (for DNS instructions) |

---

## Security Checklist

- [ ] `ZAOYA_EDGE_SECRET` is cryptographically random (32+ bytes)
- [ ] Secret is stored securely (env var, not in code)
- [ ] `/api/internal/*` endpoints verify secret
- [ ] `X-Custom-Domain` header only trusted with valid secret
- [ ] Domain input is normalized and validated
- [ ] Rate limiting on internal domain check endpoint
- [ ] Audit logging for domain operations
- [ ] No sensitive data in error responses

---

## Rollback Plan

1. **Caddy Issues**: SSH to ECS, `systemctl stop caddy`
2. **Backend Issues**: Remove `CustomDomainMiddleware` from app
3. **Database Issues**: Migration is additive; drop `custom_domains` table if needed

---

## Success Metrics

| Metric | Target |
|--------|--------|
| DNS verification success rate | > 95% |
| SSL provisioning time | < 30 seconds |
| Custom domain page load time | < 2 seconds |
| User setup completion rate | > 80% |
| Security incidents | 0 |

---

## Future Enhancements (v2+)

- Multiple domains per project
- Per-user www/non-www redirect configuration
- Punycode/IDN domain support
- Subdomain wildcards
- Custom SSL certificate upload
- Domain analytics (traffic, geographic data)
- Shared Caddy certificate storage for HA
