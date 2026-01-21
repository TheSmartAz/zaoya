/**
 * Build complete HTML document for preview iframe
 */
export function buildPreviewDocument(html: string, js: string | null): string {
  const runtimeScript = '<script src="/zaoya-runtime.js"><\/script>'
  const jsScript = js ? `<script>${js}<\/script>` : ''

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <script src="https://cdn.tailwindcss.com"><\/script>
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
  </style>
</head>
<body>
  ${html}
  ${runtimeScript}
  ${jsScript}
</body>
</html>`
}
