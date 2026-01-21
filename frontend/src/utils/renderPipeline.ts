import { sanitizeHTML } from './sanitizer';
import { validateJS } from './jsValidator';

/** Processed code result */
export interface ProcessedCode {
  type: 'success';
  html: string;
  js: string | null;
}

/** Validation error result */
export interface ValidationError {
  type: 'error';
  errors: string[];
  suggestion: string;
}

/** Generation result */
export type GenerationResult = ProcessedCode | ValidationError;

/** Normalization options */
export interface NormalizeOptions {
  addViewport?: boolean;
  addTailwindCDN?: boolean;
}

/**
 * Normalize HTML with standard meta tags and CDN links
 */
function normalizeHTML(html: string, options: NormalizeOptions = {}): string {
  const {
    addViewport = true,
    addTailwindCDN = true,
  } = options;

  // If already a full document, just normalize it
  if (html.toLowerCase().includes('<!doctype') || html.toLowerCase().includes('<html')) {
    let normalized = html;

    // Ensure viewport meta tag
    if (addViewport && !normalized.includes('viewport')) {
      normalized = normalized.replace(
        /<head>/i,
        '<head>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'
      );
    }

    // Ensure Tailwind CDN
    if (addTailwindCDN && !normalized.includes('tailwindcss')) {
      normalized = normalized.replace(
        /<head>/i,
        '<head>\n    <script src="https://cdn.tailwindcss.com"></script>'
      );
    }

    return normalized;
  }

  // Wrap partial HTML in a document
  let documentHTML = '<!DOCTYPE html>\n<html lang="en">\n<head>\n';

  if (addViewport) {
    documentHTML += '    <meta charset="UTF-8">\n';
    documentHTML += '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n';
  }

  if (addTailwindCDN) {
    documentHTML += '    <script src="https://cdn.tailwindcss.com"></script>\n';
  }

  documentHTML += '    <title>Zaoya Page</title>\n';
  documentHTML += '</head>\n<body>\n';
  documentHTML += html;
  documentHTML += '\n</body>\n</html>';

  return documentHTML;
}

/**
 * Process generated code through sanitization and validation pipeline
 */
export async function processGeneration(
  rawHtml: string,
  rawJs: string | null
): Promise<GenerationResult> {
  // Step 1: Sanitize HTML
  const sanitizedHtml = sanitizeHTML(rawHtml);

  // Step 2: Validate JS (if present)
  if (rawJs && rawJs.trim()) {
    const jsValidation = validateJS(rawJs);
    if (!jsValidation.valid) {
      return {
        type: 'error',
        errors: jsValidation.errors,
        suggestion: 'Regenerating with stricter constraints...',
      };
    }
  }

  // Step 3: Normalize HTML
  const normalizedHtml = normalizeHTML(sanitizedHtml);

  return {
    type: 'success',
    html: normalizedHtml,
    js: rawJs,
  };
}

/**
 * Quick check if code is safe (for real-time feedback)
 */
export function quickSafetyCheck(html: string, js?: string | null): boolean {
  // Check for obvious danger signs
  const dangerSigns = [
    /<script/i,
    /javascript:/i,
    /on\w+\s*=/i,
    /eva\w*l\s*\(/i, // Obfuscated eval
  ];

  if (dangerSigns.some((pattern) => pattern.test(html))) {
    return false;
  }

  if (js) {
    const result = validateJS(js);
    return result.valid;
  }

  return true;
}

/**
 * Extract the body content from a full HTML document
 */
export function extractBody(html: string): string {
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  return bodyMatch ? bodyMatch[1] : html;
}

/**
 * Inject Zaoya runtime script into HTML
 */
export function injectRuntime(html: string): string {
  const runtimeScript = `
    <script>
      window.Zaoya = {
        submitForm: function(data) {
          console.log('Form submitted:', data);
          // TODO: Send to backend
        },
        track: function(event, data) {
          console.log('Track:', event, data);
          // TODO: Send analytics
        },
        toast: function(message) {
          alert(message);
          // TODO: Show proper toast
        },
        navigate: function(url) {
          window.location.href = url;
        }
      };
    </script>
  `;

  // Insert before closing body tag
  return html.replace(/<\/body>/i, runtimeScript + '\n</body>');
}
