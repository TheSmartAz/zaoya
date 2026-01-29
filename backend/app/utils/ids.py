"""Utility functions for generating IDs."""

import secrets
import string


def generate_public_id(length: int = 8) -> str:
    """Generate a URL-safe, memorable ID.

    Uses alphanumeric without confusing characters (0/O, 1/l/I).

    Args:
        length: Length of the ID to generate

    Returns:
        URL-safe ID string
    """
    # Use lowercase letters and digits
    alphabet = string.ascii_lowercase + string.digits

    # Remove confusing characters
    alphabet = alphabet.replace('0', '').replace('o', '').replace('l', '').replace('1', '')

    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_version_id() -> str:
    """Generate a unique version ID."""
    import time
    return f"ver_{int(time.time() * 1000)}_{secrets.token_hex(4)}"


def generate_project_id() -> str:
    """Generate a unique project ID."""
    import time
    return f"proj_{int(time.time())}_{secrets.token_hex(4)}"
