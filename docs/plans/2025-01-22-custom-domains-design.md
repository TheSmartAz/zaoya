# Custom Domains Implementation Plan

> **Version**: v1 Phase 3
> **Created**: 2025-01-22
> **Status**: Draft
> **Complexity**: Medium-Large

---

## Overview

Enable Zaoya users to connect custom domains to their published pages. Users can publish their pages on their own domain (e.g., `example.com`) instead of the default `zaoya.app/p/{id}` URL.

### Goals

1. Users can add a custom domain to their project
2. DNS verification ensures domain ownership
3. SSL certificates are automatically provisioned (free via Let's Encrypt)
4. Published pages are served on custom domains with HTTPS
5. Zero ongoing cost for SSL certificates

### Non-Goals (v1)

- Multiple domains per project (1:1 mapping only)
- www/non-www redirect configuration
- Subdomain wildcards (`*.example.com`)
- Domain transfer between projects
- Custom SSL certificate upload

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
│   │    backend before issuing    │                                         │
│   │    certificate               │                                         │
│   │  • Proxies to backend        │                                         │
│   └──────────────┬───────────────┘                                         │
│                  │                                                          │
│                  │ 1. Ask: Is this domain valid?                            │
│                  │ 2. Proxy request with X-Custom-Domain header             │
│                  ▼                                                          │
│   ┌──────────────────────────────┐      ┌────────────────────────────┐    │
│   │      Zaoya Backend           │      │       PostgreSQL           │    │
│   │      (FastAPI)               │      │                            │    │
│   │                              │◄────►│  • custom_domains table    │    │
│   │  • /api/internal/domain/check│      │  • projects table          │    │
│   │  • Custom domain middleware  │      │  • pages/snapshots         │    │
│   │  • Serves published HTML     │      │                            │    │
│   └──────────────────────────────┘      └────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Domain Configuration Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Domain Setup Flow                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. User adds domain in Zaoya UI                                            │
│     └─► Backend generates verification token                                │
│     └─► Returns DNS instructions                                            │
│                                                                             │
│  2. User configures DNS at registrar                                        │
│     └─► TXT record: _zaoya-verify.example.com = zaoya-site-verification=xxx │
│     └─► CNAME record: example.com → pages.zaoya.app                         │
│                                                                             │
│  3. User clicks "Verify" or waits for auto-check                            │
│     └─► Backend queries DNS for TXT record                                  │
│     └─► If match: mark domain as verified                                   │
│                                                                             │
│  4. First request to custom domain                                          │
│     └─► Caddy asks backend: "Is example.com valid?"                         │
│     └─► Backend returns 200 (verified domain exists)                        │
│     └─► Caddy provisions SSL certificate via Let's Encrypt                  │
│     └─► Caddy proxies request to backend                                    │
│     └─► Backend serves published page                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### New Table: custom_domains

```sql
CREATE TABLE custom_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

    -- Domain info
    domain VARCHAR(255) NOT NULL UNIQUE,

    -- Verification
    verification_token VARCHAR(64) NOT NULL,
    verification_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- Values: 'pending', 'verified', 'failed'
    verified_at TIMESTAMP WITH TIME ZONE,

    -- SSL status (informational, Caddy manages actual certs)
    ssl_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- Values: 'pending', 'provisioning', 'active', 'error'
    ssl_provisioned_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_verification_status
        CHECK (verification_status IN ('pending', 'verified', 'failed')),
    CONSTRAINT valid_ssl_status
        CHECK (ssl_status IN ('pending', 'provisioning', 'active', 'error'))
);

-- Indexes
CREATE INDEX idx_custom_domains_project_id ON custom_domains(project_id);
CREATE INDEX idx_custom_domains_domain ON custom_domains(domain);
CREATE INDEX idx_custom_domains_verification_status ON custom_domains(verification_status);
```

### SQLAlchemy Model

```python
# backend/app/models/db/custom_domain.py

from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.db import Base

class CustomDomain(Base):
    __tablename__ = "custom_domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    # Domain
    domain = Column(String(255), nullable=False, unique=True, index=True)

    # Verification
    verification_token = Column(String(64), nullable=False)
    verification_status = Column(String(20), nullable=False, default="pending")
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # SSL
    ssl_status = Column(String(20), nullable=False, default="pending")
    ssl_provisioned_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="custom_domain")

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('pending', 'verified', 'failed')",
            name="valid_verification_status"
        ),
        CheckConstraint(
            "ssl_status IN ('pending', 'provisioning', 'active', 'error')",
            name="valid_ssl_status"
        ),
    )
```

### Update Project Model

```python
# Add to Project model
custom_domain = relationship("CustomDomain", back_populates="project", uselist=False)
```

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
    "verification_status": "pending",
    "verification_token": "abc123xyz...",
    "ssl_status": "pending",
    "dns_records": [
        {
            "type": "TXT",
            "host": "_zaoya-verify",
            "value": "zaoya-site-verification=abc123xyz..."
        },
        {
            "type": "CNAME",
            "host": "@",
            "value": "pages.zaoya.app"
        }
    ],
    "created_at": "2025-01-22T10:00:00Z"
}
```

**Errors:**
- 400: Invalid domain format
- 400: Domain already in use
- 403: Project not owned by user
- 409: Project already has a custom domain

#### GET /api/projects/{project_id}/domain

Get custom domain configuration for a project.

**Response (200):**
```json
{
    "id": "uuid",
    "domain": "example.com",
    "verification_status": "verified",
    "verified_at": "2025-01-22T10:30:00Z",
    "ssl_status": "active",
    "ssl_provisioned_at": "2025-01-22T10:31:00Z",
    "dns_records": [
        {
            "type": "TXT",
            "host": "_zaoya-verify",
            "value": "zaoya-site-verification=abc123xyz..."
        },
        {
            "type": "CNAME",
            "host": "@",
            "value": "pages.zaoya.app"
        }
    ],
    "created_at": "2025-01-22T10:00:00Z"
}
```

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
    "message": "DNS records not found. Please check your configuration.",
    "checks": {
        "txt_record": false,
        "cname_record": true
    }
}
```

#### DELETE /api/projects/{project_id}/domain

Remove custom domain from project.

**Response (204):** No content

### Internal Endpoints (no auth, called by Caddy)

#### GET /api/internal/domain/check

Called by Caddy to verify if a domain should be issued an SSL certificate.

**Query Parameters:**
- `domain`: The domain to check (e.g., `example.com`)

**Response (200):** Domain is valid, proceed with SSL
```json
{
    "valid": true,
    "project_id": "uuid"
}
```

**Response (404):** Domain not valid, reject
```json
{
    "valid": false,
    "reason": "Domain not found or not verified"
}
```

**Security:**
- This endpoint should only be accessible from the Caddy server IP
- Consider adding a shared secret header for additional security

---

## Services

### DomainService

```python
# backend/app/services/domain_service.py

import dns.resolver
import secrets
import re
from typing import Optional, Tuple

class DomainService:
    """Service for custom domain management"""

    VERIFICATION_PREFIX = "zaoya-site-verification="
    PAGES_DOMAIN = "pages.zaoya.app"

    @staticmethod
    def validate_domain(domain: str) -> Tuple[bool, Optional[str]]:
        """
        Validate domain format.
        Returns (is_valid, error_message)
        """
        # Basic format check
        domain_pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if not re.match(domain_pattern, domain):
            return False, "Invalid domain format"

        # Block zaoya domains
        if "zaoya" in domain.lower():
            return False, "Cannot use zaoya domains"

        # Block common reserved domains
        blocked = ["localhost", "example.com", "test.com"]
        if domain.lower() in blocked:
            return False, "This domain is not allowed"

        return True, None

    @staticmethod
    def generate_verification_token() -> str:
        """Generate a random verification token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_dns_instructions(domain: str, token: str) -> list:
        """Return DNS record instructions for the user"""
        return [
            {
                "type": "TXT",
                "host": "_zaoya-verify",
                "value": f"zaoya-site-verification={token}",
                "description": "Verification record to prove domain ownership"
            },
            {
                "type": "CNAME",
                "host": "@",
                "value": "pages.zaoya.app",
                "description": "Points your domain to Zaoya servers"
            }
        ]

    @staticmethod
    async def verify_txt_record(domain: str, expected_token: str) -> bool:
        """Check if TXT record exists with correct token"""
        try:
            answers = dns.resolver.resolve(
                f"_zaoya-verify.{domain}",
                "TXT",
                lifetime=10  # 10 second timeout
            )

            for rdata in answers:
                # TXT records may be split into multiple strings
                txt_value = "".join([s.decode() if isinstance(s, bytes) else s for s in rdata.strings])
                expected = f"zaoya-site-verification={expected_token}"
                if txt_value == expected:
                    return True

            return False
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            return False
        except Exception:
            return False

    @staticmethod
    async def verify_cname_record(domain: str) -> bool:
        """Check if CNAME points to pages.zaoya.app"""
        try:
            answers = dns.resolver.resolve(domain, "CNAME", lifetime=10)
            for rdata in answers:
                target = str(rdata.target).rstrip(".")
                if target.lower() == "pages.zaoya.app":
                    return True
            return False
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            # CNAME might not exist if using A record - that's also valid
            # The actual routing will be verified when Caddy proxies
            return True
        except Exception:
            return True  # Don't block on CNAME check failures

    @staticmethod
    async def verify_domain(domain: str, expected_token: str) -> dict:
        """
        Full domain verification check.
        Returns dict with check results.
        """
        txt_valid = await DomainService.verify_txt_record(domain, expected_token)
        cname_valid = await DomainService.verify_cname_record(domain)

        return {
            "verified": txt_valid,  # TXT is required, CNAME is advisory
            "checks": {
                "txt_record": txt_valid,
                "cname_record": cname_valid
            }
        }
```

---

## Middleware

### CustomDomainMiddleware

```python
# backend/app/middleware/custom_domain.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class CustomDomainMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and handle custom domain requests.

    When Caddy proxies a request, it adds:
    - X-Custom-Domain: The original host header (e.g., example.com)
    - X-Forwarded-Proto: The original protocol (https)
    """

    ZAOYA_DOMAINS = ["zaoya.app", "localhost", "127.0.0.1"]

    async def dispatch(self, request: Request, call_next):
        custom_domain = request.headers.get("X-Custom-Domain")

        # Check if this is a custom domain request
        is_custom_domain = False
        if custom_domain:
            is_custom_domain = not any(
                custom_domain.endswith(d) for d in self.ZAOYA_DOMAINS
            )

        # Attach to request state for downstream handlers
        request.state.custom_domain = custom_domain if is_custom_domain else None
        request.state.is_custom_domain = is_custom_domain

        response = await call_next(request)
        return response
```

---

## Frontend Components

### Component Structure

```
frontend/src/components/domain/
├── DomainSettings.tsx        # Main container component
├── DomainForm.tsx            # Add domain form
├── DomainStatus.tsx          # Status badge component
├── DnsInstructions.tsx       # DNS records table with copy
├── DomainVerifying.tsx       # Verification in progress UI
└── index.ts                  # Exports
```

### DomainSettings.tsx (Main Component)

```tsx
// frontend/src/components/domain/DomainSettings.tsx

import { useState, useEffect } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { DomainForm } from './DomainForm';
import { DomainStatus } from './DomainStatus';
import { DnsInstructions } from './DnsInstructions';

interface CustomDomainData {
  id: string;
  domain: string;
  verification_status: 'pending' | 'verified' | 'failed';
  ssl_status: 'pending' | 'provisioning' | 'active' | 'error';
  dns_records: DnsRecord[];
  verified_at?: string;
}

interface DnsRecord {
  type: string;
  host: string;
  value: string;
}

export function DomainSettings() {
  const { currentProject } = useProjectStore();
  const [domainData, setDomainData] = useState<CustomDomainData | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);

  // Fetch domain data on mount
  useEffect(() => {
    fetchDomainData();
  }, [currentProject?.id]);

  // Auto-refresh when pending
  useEffect(() => {
    if (domainData?.verification_status === 'pending') {
      const interval = setInterval(fetchDomainData, 30000); // 30 seconds
      return () => clearInterval(interval);
    }
  }, [domainData?.verification_status]);

  const fetchDomainData = async () => {
    try {
      const res = await fetch(`/api/projects/${currentProject?.id}/domain`);
      if (res.ok) {
        setDomainData(await res.json());
      } else if (res.status === 404) {
        setDomainData(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddDomain = async (domain: string) => {
    const res = await fetch(`/api/projects/${currentProject?.id}/domain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain }),
    });
    if (res.ok) {
      setDomainData(await res.json());
    }
  };

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await fetch(`/api/projects/${currentProject?.id}/domain/verify`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setDomainData(prev => prev ? { ...prev, ...data } : null);
      }
    } finally {
      setVerifying(false);
    }
  };

  const handleRemove = async () => {
    if (!confirm('Remove custom domain? This cannot be undone.')) return;

    await fetch(`/api/projects/${currentProject?.id}/domain`, {
      method: 'DELETE',
    });
    setDomainData(null);
  };

  if (loading) {
    return <div className="animate-pulse">Loading...</div>;
  }

  // No domain configured
  if (!domainData) {
    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Custom Domain</h3>
        <p className="text-sm text-gray-500">
          Connect your own domain to this project.
        </p>
        <DomainForm onSubmit={handleAddDomain} />
      </div>
    );
  }

  // Domain configured
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Custom Domain</h3>
        <button
          onClick={handleRemove}
          className="text-sm text-red-600 hover:text-red-700"
        >
          Remove
        </button>
      </div>

      <div className="p-4 border rounded-lg space-y-4">
        <div className="flex items-center justify-between">
          <span className="font-medium">{domainData.domain}</span>
          <DomainStatus
            verificationStatus={domainData.verification_status}
            sslStatus={domainData.ssl_status}
          />
        </div>

        {domainData.verification_status === 'pending' && (
          <>
            <DnsInstructions records={domainData.dns_records} />
            <button
              onClick={handleVerify}
              disabled={verifying}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {verifying ? 'Checking...' : 'Check Verification'}
            </button>
            <p className="text-xs text-gray-500">
              DNS changes can take up to 48 hours to propagate.
            </p>
          </>
        )}

        {domainData.verification_status === 'verified' && (
          <p className="text-sm text-green-600">
            Your domain is active! Visit{' '}
            <a
              href={`https://${domainData.domain}`}
              target="_blank"
              rel="noopener noreferrer"
              className="underline"
            >
              https://{domainData.domain}
            </a>
          </p>
        )}
      </div>
    </div>
  );
}
```

### DnsInstructions.tsx

```tsx
// frontend/src/components/domain/DnsInstructions.tsx

import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

interface DnsRecord {
  type: string;
  host: string;
  value: string;
}

interface Props {
  records: DnsRecord[];
}

export function DnsInstructions({ records }: Props) {
  const [copied, setCopied] = useState<string | null>(null);

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="space-y-3">
      <p className="text-sm font-medium">
        Add these DNS records at your domain registrar:
      </p>

      <div className="overflow-x-auto">
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
                <td className="py-2 pr-4 font-mono">{record.type}</td>
                <td className="py-2 pr-4 font-mono">{record.host}</td>
                <td className="py-2">
                  <div className="flex items-center gap-2">
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded break-all">
                      {record.value}
                    </code>
                    <button
                      onClick={() => copyToClipboard(record.value, `${i}`)}
                      className="p-1 hover:bg-gray-100 rounded"
                      title="Copy"
                    >
                      {copied === `${i}` ? (
                        <Check className="w-4 h-4 text-green-600" />
                      ) : (
                        <Copy className="w-4 h-4 text-gray-400" />
                      )}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## Infrastructure Setup

### Aliyun ECS Requirements

| Requirement | Specification |
|-------------|---------------|
| OS | Ubuntu 22.04 LTS or Debian 12 |
| vCPU | 1 core minimum |
| RAM | 1 GB minimum |
| Storage | 20 GB SSD |
| Network | Public IP address |
| Bandwidth | 1 Mbps minimum |

### Security Group Rules

| Direction | Protocol | Port | Source | Description |
|-----------|----------|------|--------|-------------|
| Inbound | TCP | 80 | 0.0.0.0/0 | HTTP (for ACME challenges) |
| Inbound | TCP | 443 | 0.0.0.0/0 | HTTPS |
| Inbound | TCP | 22 | Your IP | SSH access |
| Outbound | All | All | 0.0.0.0/0 | Allow all outbound |

### Caddy Installation Script

```bash
#!/bin/bash
# setup-caddy.sh
# Run on Aliyun ECS as root

set -e

echo "=== Installing Caddy ==="

# Install dependencies
apt update
apt install -y debian-keyring debian-archive-keyring apt-transport-https curl

# Add Caddy repository
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list

# Install Caddy
apt update
apt install -y caddy

echo "=== Configuring Caddy ==="

# Backup default config
mv /etc/caddy/Caddyfile /etc/caddy/Caddyfile.default

# Create Zaoya Caddyfile
cat > /etc/caddy/Caddyfile << 'EOF'
{
    # Global options
    email admin@zaoya.app

    # On-demand TLS configuration
    on_demand_tls {
        # Ask backend if domain is valid before issuing cert
        ask https://api.zaoya.app/api/internal/domain/check

        # Rate limiting to prevent abuse
        interval 1m
        burst 5
    }
}

# Catch-all server for custom domains
https:// {
    tls {
        on_demand
    }

    # Proxy to Zaoya backend
    reverse_proxy https://api.zaoya.app {
        # Pass original host
        header_up X-Custom-Domain {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-Proto {scheme}

        # Health check
        health_uri /health
        health_interval 30s
    }

    # Logging
    log {
        output file /var/log/caddy/access.log
        format json
    }
}

# Health check endpoint (internal)
http://:8080 {
    respond /health "OK" 200
}
EOF

# Create log directory
mkdir -p /var/log/caddy
chown caddy:caddy /var/log/caddy

echo "=== Starting Caddy ==="

# Enable and start Caddy
systemctl enable caddy
systemctl restart caddy

# Check status
systemctl status caddy

echo "=== Setup Complete ==="
echo "Caddy is now running and will proxy custom domain requests."
echo "Make sure to:"
echo "1. Point pages.zaoya.app A record to this server's IP"
echo "2. Update backend to handle /api/internal/domain/check endpoint"
```

### DNS Configuration for pages.zaoya.app

At your domain registrar for zaoya.app:

| Type | Host | Value | TTL |
|------|------|-------|-----|
| A | pages | {ECS_PUBLIC_IP} | 300 |

---

## Background Jobs

### Domain Verification Job

```python
# backend/app/jobs/domain_verification.py

from datetime import datetime, timedelta
from sqlalchemy import select
from app.models.db.custom_domain import CustomDomain
from app.services.domain_service import DomainService

async def domain_verification_job(db_session):
    """
    Background job to automatically verify pending domains.
    Run every 5 minutes via scheduler.
    """
    # Get pending domains that haven't been checked recently
    cutoff = datetime.utcnow() - timedelta(minutes=5)

    result = await db_session.execute(
        select(CustomDomain)
        .where(CustomDomain.verification_status == "pending")
        .where(CustomDomain.updated_at < cutoff)
    )

    pending_domains = result.scalars().all()

    for domain in pending_domains:
        try:
            verification = await DomainService.verify_domain(
                domain.domain,
                domain.verification_token
            )

            if verification["verified"]:
                domain.verification_status = "verified"
                domain.verified_at = datetime.utcnow()

                # TODO: Send verification success email
                # await send_domain_verified_email(domain)

            domain.updated_at = datetime.utcnow()

        except Exception as e:
            # Log error but continue with other domains
            print(f"Error verifying domain {domain.domain}: {e}")

    await db_session.commit()
```

### Scheduler Configuration

```python
# backend/app/main.py (add to startup)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.domain_verification import domain_verification_job

scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def start_scheduler():
    scheduler.add_job(
        domain_verification_job,
        "interval",
        minutes=5,
        id="domain_verification",
        replace_existing=True
    )
    scheduler.start()

@app.on_event("shutdown")
async def stop_scheduler():
    scheduler.shutdown()
```

---

## Testing Plan

### Unit Tests

```python
# backend/tests/test_domain_service.py

import pytest
from app.services.domain_service import DomainService

class TestDomainService:

    def test_validate_domain_valid(self):
        valid, error = DomainService.validate_domain("example.com")
        assert valid is True
        assert error is None

    def test_validate_domain_invalid_format(self):
        valid, error = DomainService.validate_domain("not-a-domain")
        assert valid is False
        assert "Invalid domain" in error

    def test_validate_domain_blocks_zaoya(self):
        valid, error = DomainService.validate_domain("fake.zaoya.app")
        assert valid is False
        assert "zaoya" in error.lower()

    def test_generate_verification_token(self):
        token = DomainService.generate_verification_token()
        assert len(token) > 20
        assert token.isalnum() or "-" in token or "_" in token

    def test_get_dns_instructions(self):
        records = DomainService.get_dns_instructions("example.com", "abc123")
        assert len(records) == 2
        assert records[0]["type"] == "TXT"
        assert records[1]["type"] == "CNAME"
        assert "abc123" in records[0]["value"]
```

### Integration Tests

```python
# backend/tests/test_domain_api.py

import pytest
from httpx import AsyncClient

class TestDomainAPI:

    async def test_add_domain(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/projects/test-project-id/domain",
            json={"domain": "example.com"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["domain"] == "example.com"
        assert data["verification_status"] == "pending"
        assert "dns_records" in data

    async def test_add_duplicate_domain(self, client: AsyncClient, auth_headers):
        # First add
        await client.post(
            "/api/projects/test-project-id/domain",
            json={"domain": "duplicate.com"},
            headers=auth_headers
        )

        # Second add should fail
        response = await client.post(
            "/api/projects/test-project-id-2/domain",
            json={"domain": "duplicate.com"},
            headers=auth_headers
        )
        assert response.status_code == 400

    async def test_internal_domain_check_verified(self, client: AsyncClient):
        # Setup: Create verified domain
        # ...

        response = await client.get(
            "/api/internal/domain/check",
            params={"domain": "verified-example.com"}
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True

    async def test_internal_domain_check_not_found(self, client: AsyncClient):
        response = await client.get(
            "/api/internal/domain/check",
            params={"domain": "nonexistent.com"}
        )
        assert response.status_code == 404
```

### Manual Testing Checklist

- [ ] Add domain with valid format
- [ ] Add domain with invalid format (should fail)
- [ ] Add domain already used by another project (should fail)
- [ ] View DNS instructions after adding domain
- [ ] Copy DNS values using copy buttons
- [ ] Trigger manual verification check
- [ ] Verify domain after DNS records are set
- [ ] Access published page via custom domain
- [ ] Remove custom domain
- [ ] Test SSL certificate provisioning (first request)
- [ ] Test auto-refresh of verification status

---

## Implementation Tasks

### Phase 1: Backend Foundation (Day 1-2)

- [ ] Create database migration for `custom_domains` table
- [ ] Create `CustomDomain` SQLAlchemy model
- [ ] Update `Project` model with relationship
- [ ] Create `DomainService` with validation and DNS lookup
- [ ] Install `dnspython` dependency

### Phase 2: API Endpoints (Day 2-3)

- [ ] POST /api/projects/{id}/domain - Add domain
- [ ] GET /api/projects/{id}/domain - Get domain
- [ ] POST /api/projects/{id}/domain/verify - Verify domain
- [ ] DELETE /api/projects/{id}/domain - Remove domain
- [ ] GET /api/internal/domain/check - Internal check for Caddy
- [ ] Add request/response schemas (Pydantic)

### Phase 3: Middleware & Routing (Day 3)

- [ ] Create `CustomDomainMiddleware`
- [ ] Register middleware in FastAPI app
- [ ] Update page serving to handle custom domains
- [ ] Test page serving with mock custom domain header

### Phase 4: Frontend UI (Day 4-5)

- [ ] Create `DomainSettings` component
- [ ] Create `DomainForm` component
- [ ] Create `DnsInstructions` component with copy buttons
- [ ] Create `DomainStatus` badge component
- [ ] Add domain settings to project settings page
- [ ] Add auto-refresh for pending verification

### Phase 5: Infrastructure (Day 5-6)

- [ ] Set up Aliyun ECS instance
- [ ] Install and configure Caddy
- [ ] Configure security group rules
- [ ] Point pages.zaoya.app to ECS IP
- [ ] Test SSL provisioning with test domain

### Phase 6: Background Jobs (Day 6)

- [ ] Create domain verification job
- [ ] Set up APScheduler
- [ ] Configure job to run every 5 minutes
- [ ] Add email notification on verification success (optional)

### Phase 7: Testing & Polish (Day 7)

- [ ] Write unit tests for DomainService
- [ ] Write integration tests for API endpoints
- [ ] Manual end-to-end testing
- [ ] Error handling improvements
- [ ] Documentation updates

---

## Security Considerations

1. **Domain Ownership Verification**: TXT record verification ensures only domain owners can connect domains

2. **Rate Limiting**: Caddy's on-demand TLS is rate-limited to prevent certificate exhaustion attacks

3. **Internal Endpoint Protection**: `/api/internal/domain/check` should be restricted to Caddy server IP or use a shared secret

4. **Input Validation**: Domain format is strictly validated to prevent injection attacks

5. **No Wildcard Support**: Only exact domain matches are allowed to prevent subdomain takeover

---

## Rollback Plan

If issues occur after deployment:

1. **Caddy Issues**: SSH to ECS, `systemctl stop caddy`, traffic will fail over
2. **Backend Issues**: Remove CustomDomainMiddleware registration to disable feature
3. **Database Issues**: Migration is additive (new table), no rollback needed unless dropping

---

## Success Metrics

| Metric | Target |
|--------|--------|
| DNS verification success rate | > 95% |
| SSL provisioning time | < 30 seconds |
| Custom domain page load time | < 2 seconds |
| User setup completion rate | > 80% |

---

## Future Enhancements (v2+)

- Multiple domains per project
- www/non-www redirect configuration
- Subdomain wildcards
- Custom SSL certificate upload
- Domain analytics (traffic, geographic data)
- Automatic www redirect setup
