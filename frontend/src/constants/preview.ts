export const THUMBNAIL = {
  // Size: 300 x 600 px (mobile aspect)
  WIDTH: 300,
  HEIGHT: 600,
  ASPECT_RATIO: 1 / 2,

  // Grid layout
  GAP: 16,
  MIN_COLUMNS: 2,
  MAX_COLUMNS: 6,

  // Rendering
  SCALE: 0.2, // Preview rendered at 5x size, scaled down
  VIEWPORT_WIDTH: 375,
  VIEWPORT_HEIGHT: 667,

  // Animation
  DRAG_OPACITY: 0.8,
  DROP_ANIMATION_MS: 200,
} as const

export const OVERVIEW = {
  HEADER_HEIGHT: 64,
  PADDING: 24,
  FOOTER_HEIGHT: 40,
} as const
