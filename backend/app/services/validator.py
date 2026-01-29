"""Server-side HTML and JS validation for security."""

import re
import bleach
from typing import Tuple, List, Optional

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

_HTML_RULES = [
    {
        "rule_id": "csp-no-tailwind-cdn",
        "pattern": r"cdn\\.tailwindcss\\.com",
        "category": "csp",
        "message": "External Tailwind CDN not allowed",
        "suggested_fix": "Inline Tailwind styles using the built-in compiler.",
        "severity": "critical",
        "flags": re.IGNORECASE,
    },
    {
        "rule_id": "html-no-script-tag",
        "pattern": r"<script[^>]*>",
        "category": "js-security",
        "message": "Script tag detected",
        "suggested_fix": "Remove script tags and use Zaoya runtime helpers instead.",
        "severity": "critical",
        "flags": re.IGNORECASE,
    },
    {
        "rule_id": "html-no-iframe",
        "pattern": r"<iframe",
        "category": "html-whitelist",
        "message": "Iframe tag detected",
        "suggested_fix": "Remove iframe elements from the page.",
        "severity": "critical",
        "flags": re.IGNORECASE,
    },
    {
        "rule_id": "html-no-object",
        "pattern": r"<object",
        "category": "html-whitelist",
        "message": "Object tag detected",
        "suggested_fix": "Remove object/embed elements from the page.",
        "severity": "critical",
        "flags": re.IGNORECASE,
    },
    {
        "rule_id": "html-no-embed",
        "pattern": r"<embed",
        "category": "html-whitelist",
        "message": "Embed tag detected",
        "suggested_fix": "Remove object/embed elements from the page.",
        "severity": "critical",
        "flags": re.IGNORECASE,
    },
    {
        "rule_id": "html-no-javascript-protocol",
        "pattern": r"javascript:",
        "category": "js-security",
        "message": "javascript: protocol detected",
        "suggested_fix": "Replace javascript: URLs with safe event handlers.",
        "severity": "critical",
        "flags": re.IGNORECASE,
    },
    {
        "rule_id": "html-no-inline-event",
        "pattern": r"\\son\\w+\\s*=",
        "category": "js-security",
        "message": "Inline event handler detected",
        "suggested_fix": "Remove inline event handlers and use approved JS helpers.",
        "severity": "critical",
        "flags": re.IGNORECASE,
    },
]

_JS_RULES = [
    {
        "rule_id": "js-no-eval",
        "pattern": r"eva\\w*l\\s*\\(",
        "category": "js-security",
        "message": "Code execution not allowed",
        "suggested_fix": "Remove eval usage and use safe helpers.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-function-constructor",
        "pattern": r"Function\\s*\\(",
        "category": "js-security",
        "message": "Function constructor not allowed",
        "suggested_fix": "Remove Function constructor usage.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-fetch",
        "pattern": r"fetch\\s*\\(",
        "category": "js-security",
        "message": "Network requests not allowed",
        "suggested_fix": "Avoid fetch calls; use Zaoya.submitForm/track.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-xhr",
        "pattern": r"XMLHttpRequest",
        "category": "js-security",
        "message": "Network requests not allowed",
        "suggested_fix": "Avoid XMLHttpRequest; use Zaoya.submitForm/track.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-websocket",
        "pattern": r"WebSocket",
        "category": "js-security",
        "message": "WebSockets not allowed",
        "suggested_fix": "Remove WebSocket usage.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-localstorage",
        "pattern": r"localStorage",
        "category": "js-security",
        "message": "Local storage not allowed",
        "suggested_fix": "Remove localStorage usage.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-sessionstorage",
        "pattern": r"sessionStorage",
        "category": "js-security",
        "message": "Session storage not allowed",
        "suggested_fix": "Remove sessionStorage usage.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-cookie",
        "pattern": r"document\\.cookie",
        "category": "js-security",
        "message": "Cookie access not allowed",
        "suggested_fix": "Remove document.cookie access.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-frame-access",
        "pattern": r"window\\.(top|parent|opener)",
        "category": "js-security",
        "message": "Frame access not allowed",
        "suggested_fix": "Remove window.top/parent/opener usage.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-string-timeout",
        "pattern": r"setTimeout\\s*\\(\\s*[\"\\']",
        "category": "js-security",
        "message": "String-based setTimeout not allowed",
        "suggested_fix": "Use function callbacks instead of string-based timers.",
        "severity": "critical",
    },
    {
        "rule_id": "js-no-string-interval",
        "pattern": r"setInterval\\s*\\(\\s*[\"\\']",
        "category": "js-security",
        "message": "String-based setInterval not allowed",
        "suggested_fix": "Use function callbacks instead of string-based timers.",
        "severity": "critical",
    },
]


def _line_excerpt(text: str, match: re.Match) -> tuple[Optional[int], str]:
    start = match.start()
    line = text.count("\\n", 0, start) + 1
    line_start = text.rfind("\\n", 0, start) + 1
    line_end = text.find("\\n", match.end())
    if line_end == -1:
        line_end = len(text)
    excerpt = text[line_start:line_end].strip()
    if len(excerpt) > 200:
        excerpt = excerpt[:197] + "..."
    return line, excerpt


def _build_error_detail(
    *,
    rule_id: str,
    category: str,
    message: str,
    suggested_fix: str,
    severity: str,
    path: Optional[str],
    line: Optional[int],
    excerpt: str,
) -> dict:
    return {
        "ruleId": rule_id,
        "ruleCategory": category,
        "path": path or "",
        "line": line,
        "excerpt": excerpt,
        "message": message,
        "suggestedFix": suggested_fix,
        "severity": severity,
    }


def _scan_html_errors(html: str, path: Optional[str] = None) -> List[dict]:
    details: List[dict] = []
    for rule in _HTML_RULES:
        pattern = rule["pattern"]
        flags = rule.get("flags", 0)
        match = re.search(pattern, html, flags)
        if not match:
            continue
        line, excerpt = _line_excerpt(html, match)
        details.append(
            _build_error_detail(
                rule_id=rule["rule_id"],
                category=rule["category"],
                message=rule["message"],
                suggested_fix=rule["suggested_fix"],
                severity=rule["severity"],
                path=path,
                line=line,
                excerpt=excerpt,
            )
        )
    return details


def _scan_js_errors(code: str, path: Optional[str] = None) -> List[dict]:
    details: List[dict] = []
    seen_rules: set[str] = set()

    for rule in _JS_RULES:
        match = re.search(rule["pattern"], code)
        if not match:
            continue
        if rule["rule_id"] in seen_rules:
            continue
        line, excerpt = _line_excerpt(code, match)
        details.append(
            _build_error_detail(
                rule_id=rule["rule_id"],
                category=rule["category"],
                message=rule["message"],
                suggested_fix=rule["suggested_fix"],
                severity=rule["severity"],
                path=path,
                line=line,
                excerpt=excerpt,
            )
        )
        seen_rules.add(rule["rule_id"])

    blocked_globals = ['fetch', 'XMLHttpRequest', 'WebSocket', 'localStorage', 'sessionStorage']
    for global_name in blocked_globals:
        pattern = r'\\b' + re.escape(global_name) + r'\\b'
        if not re.search(pattern, code):
            continue
        rule_id = f'js-no-{global_name.lower()}'
        if rule_id in seen_rules:
            continue
        match = re.search(pattern, code)
        if not match:
            continue
        line, excerpt = _line_excerpt(code, match)
        details.append(
            _build_error_detail(
                rule_id=rule_id,
                category="js-security",
                message=f'{global_name} is not allowed',
                suggested_fix=f'Remove {global_name} usage.',
                severity="critical",
                path=path,
                line=line,
                excerpt=excerpt,
            )
        )
        seen_rules.add(rule_id)

    return details

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


def validate_js_with_details(code: str, path: Optional[str] = None) -> Tuple[bool, List[str], List[dict]]:
    details = _scan_js_errors(code, path)
    errors = [detail.get("message", "") for detail in details]
    return (len(errors) == 0, errors, details)

def validate_html(html: str, path: Optional[str] = None) -> dict:
    """Validate HTML for dangerous content and return normalized output."""
    warnings: List[str] = []
    error_details = _scan_html_errors(html, path)
    errors = [detail.get("message", "") for detail in error_details]

    body_html = extract_body_content(html)
    sanitized = sanitize_html(body_html)
    normalized = normalize_html(sanitized)

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "normalized_html": normalized,
        "error_details": error_details,
    }


def check_for_dangerous_content(html: str) -> List[str]:
    """Check HTML for obviously dangerous content.

    Args:
        html: HTML string to check

    Returns:
        List of danger descriptions found
    """
    return [detail.get("message", "") for detail in _scan_html_errors(html)]


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

        return html

    # Wrap partial HTML in a document
    wrapped = '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
    wrapped += '    <meta charset="UTF-8">\n'
    wrapped += '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
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

    html_result = validate_html(html)
    errors.extend(html_result.get("errors", []))
    normalized = html_result.get("normalized_html") or ""

    if js and js.strip():
        js_valid, js_errors = validate_js(js)
        if not js_valid:
            errors.extend(js_errors)

    return (len(errors) == 0, normalized, js or '', errors)


def extract_body_content(html: str) -> str:
    """Extract body contents from a full HTML document if present."""
    match = re.search(r'<body[^>]*>(.*?)</body>', html, re.IGNORECASE | re.DOTALL)
    return match.group(1) if match else html
