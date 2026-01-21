"""Server-side HTML and JS validation for security."""

import re
import bleach
from typing import Tuple, List

# Allowed HTML tags (conservative set)
ALLOWED_TAGS = [
    'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'a', 'img', 'ul', 'ol', 'li', 'button', 'form', 'input',
    'textarea', 'label', 'select', 'option', 'section', 'article',
    'header', 'footer', 'nav', 'main', 'table', 'tr', 'td', 'th',
    'thead', 'tbody', 'strong', 'em', 'br', 'hr', 'small', 'sub', 'sup',
]

# Allowed HTML attributes per tag
ALLOWED_ATTRS_BY_TAG = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'title'],
    'input': ['type', 'name', 'value', 'placeholder', 'required', 'disabled'],
    'textarea': ['name', 'placeholder', 'required', 'disabled', 'rows', 'cols'],
    'select': ['name', 'required', 'disabled'],
    'option': ['value', 'disabled', 'selected'],
    'button': ['type', 'disabled', 'name', 'value'],
    'form': ['method', 'action'],
}

# Blocked JavaScript patterns
BLOCKED_JS_PATTERNS = [
    (r'eva\w*l\s*\(', 'Code execution not allowed'),
    (r'Function\s*\(', 'Function constructor not allowed'),
    (r'fetch\s*\(', 'Network requests not allowed'),
    (r'XMLHttpRequest', 'Network requests not allowed'),
    (r'WebSocket', 'WebSockets not allowed'),
    (r'localStorage', 'Local storage not allowed'),
    (r'sessionStorage', 'Session storage not allowed'),
    (r'document\.cookie', 'Cookie access not allowed'),
    (r'window\.(top|parent|opener)', 'Frame access not allowed'),
    (r'setTimeout\s*\(\s*["\']', 'String-based setTimeout not allowed'),
    (r'setInterval\s*\(\s*["\']', 'String-based setInterval not allowed'),
]

# Allowed JavaScript function calls
ALLOWED_JS_CALLS = [
    'Zaoya.submitForm',
    'Zaoya.track',
    'Zaoya.toast',
    'Zaoya.navigate',
    'document.getElementById',
    'document.querySelector',
    'document.querySelectorAll',
    'addEventListener',
    'removeEventListener',
    'console.log',
    'console.warn',
    'console.error',
]


def sanitize_html(html: str) -> str:
    """Sanitize HTML using bleach.

    Args:
        html: Raw HTML string

    Returns:
        Sanitized HTML string
    """
    def allow_attribute(tag: str, name: str, value: str) -> bool:
        if name.startswith("data-"):
            return True
        allowed = ALLOWED_ATTRS_BY_TAG.get(tag, []) + ALLOWED_ATTRS_BY_TAG.get("*", [])
        return name in allowed

    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=allow_attribute,
        strip=True,
        strip_comments=True,
    )


def validate_js(code: str) -> Tuple[bool, List[str]]:
    """Validate JavaScript code for security issues.

    Args:
        code: JavaScript code string

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check against blocked patterns
    for pattern, message in BLOCKED_JS_PATTERNS:
        if re.search(pattern, code):
            errors.append(message)

    # Check for suspicious global access
    blocked_globals = ['fetch', 'XMLHttpRequest', 'WebSocket', 'localStorage', 'sessionStorage']
    for global_name in blocked_globals:
        # Look for direct usage (not as part of a larger identifier)
        pattern = r'\b' + re.escape(global_name) + r'\b'
        if re.search(pattern, code):
            errors.append(f'{global_name} is not allowed')

    return (len(errors) == 0, errors)


def check_for_dangerous_content(html: str) -> List[str]:
    """Check HTML for obviously dangerous content.

    Args:
        html: HTML string to check

    Returns:
        List of danger descriptions found
    """
    dangers = []

    # Allow Tailwind CDN script tag only
    script_tags = re.findall(r'<script[^>]*>', html, re.IGNORECASE)
    for tag in script_tags:
        src_match = re.search(r'src=[\"\\\']([^\"\\\']+)', tag, re.IGNORECASE)
        if not src_match:
            dangers.append('Script tag detected')
            break
        src = src_match.group(1)
        if src != 'https://cdn.tailwindcss.com':
            dangers.append('Script tag detected')
            break

    dangerous_patterns = [
        (r'<iframe', 'Iframe tag detected'),
        (r'<object', 'Object tag detected'),
        (r'<embed', 'Embed tag detected'),
        (r'javascript:', 'javascript: protocol detected'),
        (r'\\son\\w+\\s*=', 'Inline event handler detected'),
    ]

    for pattern, message in dangerous_patterns:
        if re.search(pattern, html, re.IGNORECASE):
            dangers.append(message)

    return dangers


def normalize_html(html: str) -> str:
    """Normalize HTML with standard meta tags.

    Args:
        html: Raw HTML string

    Returns:
        Normalized HTML with proper structure
    """
    # Check if it's a full document
    if re.search(r'<!DOCTYPE|<html', html, re.IGNORECASE):
        # Ensure viewport meta tag
        if 'viewport' not in html:
            html = re.sub(
                r'(<head[^>]*>)',
                r'\1\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
                html,
                count=1,
                flags=re.IGNORECASE
            )

        # Ensure Tailwind CDN
        if 'tailwindcss' not in html:
            html = re.sub(
                r'(<head[^>]*>)',
                r'\1\n    <script src="https://cdn.tailwindcss.com"></script>',
                html,
                count=1,
                flags=re.IGNORECASE
            )

        return html

    # Wrap partial HTML in a document
    wrapped = '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    wrapped += '    <meta charset="UTF-8">\n'
    wrapped += '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
    wrapped += '    <script src="https://cdn.tailwindcss.com"></script>\n'
    wrapped += '    <title>Zaoya Page</title>\n'
    wrapped += '</head>\n<body>\n'
    wrapped += html
    wrapped += '\n</body>\n</html>'

    return wrapped


def process_generation(html: str, js: str = None) -> Tuple[bool, str, str, List[str]]:
    """Process generated code through security pipeline.

    Args:
        html: Generated HTML
        js: Optional generated JavaScript

    Returns:
        Tuple of (is_valid, processed_html, processed_js, errors)
    """
    errors = []

    # Check for dangerous content
    dangers = check_for_dangerous_content(html)
    if dangers:
        errors.extend(dangers)

    # Sanitize HTML (strip head/html wrappers if present)
    body_html = extract_body_content(html)
    sanitized = sanitize_html(body_html)

    # Validate JS if present
    if js and js.strip():
        js_valid, js_errors = validate_js(js)
        if not js_valid:
            errors.extend(js_errors)

    # Normalize HTML
    normalized = normalize_html(sanitized)

    return (len(errors) == 0, normalized, js or '', errors)


def extract_body_content(html: str) -> str:
    """Extract body contents from a full HTML document if present."""
    match = re.search(r'<body[^>]*>(.*?)</body>', html, re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else html
