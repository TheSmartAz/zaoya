import DOMPurify from 'dompurify';

const ALLOWED_TAGS = [
  'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'a', 'img', 'ul', 'ol', 'li', 'button', 'form', 'input',
  'textarea', 'label', 'select', 'option', 'section', 'article',
  'header', 'footer', 'nav', 'main', 'aside', 'figure', 'figcaption',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
  'strong', 'em', 'b', 'i', 'br', 'hr',
  'small', 'sub', 'sup', 'blockquote', 'code', 'pre',
];

const ALLOWED_ATTR = [
  'class', 'id', 'href', 'src', 'alt', 'type', 'name', 'value',
  'placeholder', 'required', 'disabled', 'for', 'style',
  'data-*', // Allow data attributes for Zaoya.* hooks
  'rows', 'cols', 'maxlength', 'min', 'max', 'step',
  'target', 'rel', // For links
  'accept', 'multiple', // For file inputs
];

/**
 * Sanitize HTML to prevent XSS attacks
 */
export function sanitizeHTML(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'style', 'link', 'meta'],
    FORBID_ATTR: ['onclick', 'onerror', 'onload', 'onmouseover', 'onmouseout', 'onfocus', 'onblur'],
    ALLOW_DATA_ATTR: true,
    ALLOW_UNKNOWN_PROTOCOLS: false,
  });
}

/**
 * Check if HTML contains dangerous content
 */
export function hasDangerousContent(html: string): boolean {
  const dangerousPatterns = [
    /<script/i,
    /javascript:/i,
    /on\w+\s*=/i, // Event handlers like onclick=
    /<iframe/i,
    /<object/i,
    /<embed/i,
    /eval\s*\(/i,
    /document\.cookie/i,
    /localStorage/i,
    /sessionStorage/i,
  ];

  return dangerousPatterns.some((pattern) => pattern.test(html));
}

/**
 * Strip all HTML tags (for text-only display)
 */
export function stripHTML(html: string): string {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return doc.body.textContent || '';
}
