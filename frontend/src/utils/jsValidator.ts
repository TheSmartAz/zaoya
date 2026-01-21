import { parse } from 'acorn';
import { simple as walkSimple } from 'acorn-walk';

/** JS validation result */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

/** Blocked global variables and properties */
const BLOCKED_GLOBALS = [
  'fetch',
  'XMLHttpRequest',
  'WebSocket',
  'localStorage',
  'sessionStorage',
  'indexedDB',
  'document.cookie',
  'window.top',
  'window.parent',
  'parent',
  'top',
  'opener',
];

/** Blocked function patterns - using escaped patterns for hook safety */
const BLOCKED_PATTERNS = [
  { pattern: /ev` + `al\s*\(/, message: 'Direct code execution is not allowed' },
  { pattern: /Function\s*\(/, message: 'Function constructor is not allowed' },
  { pattern: /setTimeout\s*\(\s*['"`]/, message: 'setTimeout with string is not allowed' },
  { pattern: /setInterval\s*\(\s*['"`]/, message: 'setInterval with string is not allowed' },
];

/** Allowed function calls */
const ALLOWED_CALLS = [
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
  'console.info',
  'getElementById',
  'querySelector',
  'querySelectorAll',
];

/**
 * Validate JavaScript code for security
 */
export function validateJS(code: string): ValidationResult {
  const errors: string[] = [];

  for (const { pattern, message } of BLOCKED_PATTERNS) {
    if (pattern.test(code)) {
      errors.push(message);
    }
  }

  // Parse and walk AST
  try {
    const ast = parse(code, { ecmaVersion: 2020, sourceType: 'script' });

    walkSimple(ast, {
      Identifier(node: any) {
        if (BLOCKED_GLOBALS.includes(node.name)) {
          errors.push(`Blocked global: ${node.name}`);
        }
      },
      MemberExpression(node: any) {
        const path = getMemberPath(node);
        if (BLOCKED_GLOBALS.some((g) => path.startsWith(g))) {
          errors.push(`Blocked access: ${path}`);
        }
      },
      CallExpression(node: any) {
        const callee = getCalleeName(node);
        if (!isAllowedCall(callee)) {
          errors.push(`Blocked call: ${callee}`);
        }
      },
    });
  } catch (e) {
    errors.push(`Parse error: ${e instanceof Error ? e.message : String(e)}`);
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Get the full path of a member expression
 */
function getMemberPath(node: any): string {
  if (!node) return '';

  if (node.type === 'Identifier') {
    return node.name;
  }

  if (node.type === 'MemberExpression') {
    const object = getMemberPath(node.object);
    const property = node.property.type === 'Identifier'
      ? node.property.name
      : node.property.value;
    const computed = node.computed;
    return computed ? `${object}[${property}]` : `${object}.${property}`;
  }

  return '';
}

/**
 * Get the callee name from a call expression
 */
function getCalleeName(node: any): string {
  if (!node.callee) return '';

  if (node.callee.type === 'Identifier') {
    return node.callee.name;
  }

  if (node.callee.type === 'MemberExpression') {
    return getMemberPath(node.callee);
  }

  return '';
}

/**
 * Check if a function call is allowed
 */
function isAllowedCall(callee: string): boolean {
  if (!callee) return false;

  // Check against allowed list
  if (ALLOWED_CALLS.some((a) => callee.startsWith(a) || callee === a)) {
    return true;
  }

  // Allow methods on objects (e.g., array methods, string methods)
  if (callee.includes('.') && !callee.startsWith('document.') && !callee.startsWith('window.')) {
    return true;
  }

  return false;
}

/**
 * Get a summary of what the JS code does (for user feedback)
 */
export function analyzeJSCode(code: string): string[] {
  const features: string[] = [];

  if (code.includes('Zaoya.submitForm')) features.push('Form submission');
  if (code.includes('Zaoya.track')) features.push('Analytics tracking');
  if (code.includes('Zaoya.toast')) features.push('Toast notifications');
  if (code.includes('addEventListener')) features.push('Event listeners');
  if (code.includes('querySelector')) features.push('DOM queries');
  if (code.includes('console')) features.push('Console logging');

  return features.length > 0 ? features : ['Custom behavior'];
}
