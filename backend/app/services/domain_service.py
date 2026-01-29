"""Service for custom domain management."""

import asyncio
import re
import secrets
from typing import Optional, Tuple

import dns.resolver

from app.config import settings


class DomainService:
    """Service for custom domain validation and DNS verification."""

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
        """Normalize domain: lowercase, strip whitespace, remove trailing dot."""
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

        if len(domain) < 4:
            return False, "Domain too short"

        # ASCII only for v1 (no punycode/IDN)
        if not domain.isascii():
            return False, "Only ASCII domains are supported"

        # Basic format check
        domain_pattern = r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
        if not re.match(domain_pattern, domain):
            return False, "Invalid domain format"

        # Check for IP addresses
        ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
        if re.match(ip_pattern, domain):
            return False, "IP addresses are not allowed"

        # Check for ports
        if ":" in domain:
            return False, "Port numbers are not allowed"

        # Block reserved zones (exact match or suffix)
        for blocked in DomainService.BLOCKED_ZONES:
            if domain == blocked or domain.endswith(f".{blocked}"):
                return False, f"Domain '{blocked}' is not allowed"

        return True, None

    @staticmethod
    def is_apex_domain(domain: str) -> bool:
        """
        Check if domain is apex (no subdomain prefix).

        Note: This is a simplified check. For example.com it returns True,
        for www.example.com it returns False.
        """
        parts = DomainService.normalize_domain(domain).split(".")
        # apex: example.com (2 parts)
        # subdomain: www.example.com (3+ parts)
        return len(parts) == 2

    @staticmethod
    def generate_verification_token() -> str:
        """Generate a random verification token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def get_dns_instructions(domain: str, token: str) -> dict:
        """Return DNS record instructions for the user."""
        domain = DomainService.normalize_domain(domain)
        parts = domain.split(".")
        base_domain = ".".join(parts[-2:]) if len(parts) > 2 else domain

        edge_ip = settings.edge_server_ip or "YOUR_SERVER_IP"

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
                    },
                ],
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
                    },
                ],
            },
            "help_text": "If your provider doesn't support CNAME/ALIAS at @, use an A record pointing to our server IP.",
        }

    @staticmethod
    async def verify_txt_record(domain: str, expected_token: str) -> bool:
        """Check if TXT record exists with correct token."""
        domain = DomainService.normalize_domain(domain)
        # Get base domain for TXT lookup
        parts = domain.split(".")
        base_domain = ".".join(parts[-2:]) if len(parts) > 2 else domain

        try:
            # Run DNS lookup in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            answers = await loop.run_in_executor(
                None,
                lambda: dns.resolver.resolve(
                    f"_zaoya-verify.{base_domain}",
                    "TXT",
                    lifetime=10,
                ),
            )

            for rdata in answers:
                txt_value = "".join(
                    [s.decode() if isinstance(s, bytes) else s for s in rdata.strings]
                )
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
        loop = asyncio.get_event_loop()

        # Try CNAME first
        try:
            answers = await loop.run_in_executor(
                None,
                lambda: dns.resolver.resolve(domain, "CNAME", lifetime=10),
            )
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
            answers = await loop.run_in_executor(
                None,
                lambda: dns.resolver.resolve(domain, "A", lifetime=10),
            )
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
            },
        }
