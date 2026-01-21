import { ExtractedCode } from '@/types'

/**
 * Extract HTML and JavaScript code from AI response
 * Supports markdown code blocks: ```html and ```javascript
 */
export function extractCode(response: string): ExtractedCode {
  // Try to extract HTML code block
  const htmlMatch = response.match(/```html\n([\s\S]*?)```/)

  // Try to extract JavaScript code block
  const jsMatch = response.match(/```javascript\n([\s\S]*?)```/)

  const html = htmlMatch?.[1]?.trim() || ''
  const js = jsMatch?.[1]?.trim() || null

  return {
    html,
    js,
    metadata: {
      hasHtml: !!html,
      hasJs: !!js
    }
  }
}

/**
 * Check if response contains code
 */
export function hasCode(response: string): boolean {
  return /```(html|javascript)/.test(response)
}
