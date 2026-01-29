# Phase 4: Thumbnails + SEO (Week 4)

**Focus**: Reliable thumbnail generation and social media optimization.

---

## Overview

This phase implements a robust thumbnail generation system with queue management and fallback strategies. It also adds basic SEO support to make published pages shareable on social media platforms with proper titles, descriptions, and Open Graph images.

**Key Goals**:
- Generate reliable thumbnails for project dashboards
- Create separate OG Images for social sharing
- Add SEO metadata tags to published pages
- Handle thumbnail failures gracefully without blocking publish

---

## Prerequisites

- Phase 1 (Foundation) is complete
- Playwright is available for headless browser automation
- CDN or static file storage is configured

---

## Detailed Tasks

### 4.1 Thumbnail Queue Design

**Priority**: High

**Queue Table Schema**:
```sql
CREATE TABLE thumbnail_jobs (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  page_id UUID REFERENCES pages(id),
  type VARCHAR(20),  -- 'thumbnail' | 'og_image'
  status VARCHAR(20),  -- 'queued' | 'running' | 'done' | 'failed'
  attempts INT DEFAULT 0,
  max_attempts INT DEFAULT 3,
  next_run_at TIMESTAMP,
  last_error TEXT,
  image_url TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

**Tasks**:
1. Create queue management system
2. Implement worker pool (max 2 concurrent)
3. Add job scheduling with exponential backoff
4. Implement job deduplication (new job cancels old)
5. Create queue monitoring endpoints

**Worker Constraints**:
- Max 2 concurrent jobs per type
- 30s timeout per page
- Exponential backoff: 30s → 45s → 60s
- Deduplication: new job for same page cancels old

**Acceptance Criteria**:
- [ ] Queue system processes jobs sequentially
- [ ] Worker pool respects concurrency limits
- [ ] Failed jobs retry with backoff
- [ ] Duplicate jobs are deduplicated

### 4.2 Thumbnail vs OG Image

**Priority**: High

**Two Separate Types**:

| Aspect | Thumbnail | OG Image |
|--------|-----------|----------|
| Size | 300x600 (mobile) | 1200x630 (standard) |
| Purpose | Dashboard, editor | Social sharing |
| Quality | Standard | High |
| Generation | Async queue | On-demand |
| Blocking | No | No |

**Tasks**:
1. Implement thumbnail generation (300x600):
   - Playwright headless screenshot
   - Mobile viewport (375x667)
   - Full page scroll capture
2. Implement OG Image generation (1200x630):
   - Playwright with desktop viewport
   - Higher quality rendering
   - On-demand generation
3. Add separate storage paths
4. Implement separate queue workers

**Acceptance Criteria**:
- [ ] Thumbnails generated at 300x600
- [ ] OG Images generated at 1200x630
- [ ] Separate storage paths
- [ ] Independent queue workers

### 4.3 Worker Logic with Fallbacks

**Priority**: High

**Three-Tier Fallback Strategy**:

**Tier 1: Server-side (Playwright)**
- Headless browser screenshot
- Full page rendering
- 30s timeout

**Tier 2: Client-side (html2canvas)**
- Fallback when server fails
- User-triggered generation
- Browser-based capture

**Tier 3: SVG Placeholder**
- Auto-generated on failure
- Page title + theme color
- Minimal visual appeal

**Tasks**:
1. Implement primary Playwright worker
2. Add client-side fallback (html2canvas)
3. Create SVG placeholder generator
4. Implement fallback chain logic
5. Add UI for user-triggered retry

**Fallback Logic**:
```python
async def generate_thumbnail(page):
    try:
        # Tier 1: Playwright
        return await playwright_screenshot(page)
    except TimeoutError:
        try:
            # Tier 2: Client-side
            return await client_side_generation(page)
        except Exception:
            # Tier 3: SVG placeholder
            return generate_svg_placeholder(page)
```

**Acceptance Criteria**:
- [ ] Primary worker uses Playwright
- [ ] Fallback to client-side on failure
- [ ] Final fallback to SVG placeholder
- [ ] User can retry failed thumbnails
- [ ] Thumbnail failure never blocks publish

### 4.4 Frontend UI States

**Priority**: Medium

**Thumbnail States**:
- **Pending**: Shows clock icon ⏱
- **Generating**: Shows spinner 🔄
- **Done**: Shows thumbnail image 🖼
- **Failed**: Shows error + retry button 🔄

**OG Image States**:
- **Pending/Generating**: Uses placeholder
- **Done**: Shows OG image
- **Failed**: Keeps placeholder, user can retry

**Tasks**:
1. Create `ThumbnailDisplay` component
2. Implement state management (pending/generating/done/failed)
3. Add one-click retry button
4. Show loading indicators
5. Display error messages

**Acceptance Criteria**:
- [ ] UI clearly shows all states
- [ ] Failed thumbnails show retry button
- [ ] Loading indicators are visible
- [ ] Error messages are helpful

### 4.5 Basic SEO Tags

**Priority**: High

**SEO Metadata**:
```html
<!-- Basic -->
<title>{pageTitle} | {projectName}</title>
<meta name="description" content="{pageDescription}">

<!-- Canonical -->
<link rel="canonical" href="https://pages.zaoya.app/p/{public_id}/{page_slug}">

<!-- Open Graph -->
<meta property="og:title" content="{pageTitle}">
<meta property="og:description" content="{pageDescription}">
<meta property="og:image" content="{thumbnailUrl}">
<meta property="og:url" content="{canonicalUrl}">
<meta property="og:type" content="website">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{pageTitle}">
<meta name="twitter:description" content="{pageDescription}">
<meta name="twitter:image" content="{thumbnailUrl}">

<!-- Favicon -->
<link rel="icon" href="{faviconUrl}">

<!-- Robots -->
<meta name="robots" content="index, follow">
```

**Tasks**:
1. Create SEO template for published pages
2. Implement metadata extraction from ProductDoc
3. Add OG Image URL to metadata
4. Generate canonical URLs correctly
5. Add favicon support

**Data Sources**:
| Tag | Source |
|-----|--------|
| title | Page title or ProductDoc.project_name |
| description | ProductDoc.overview or page.summary |
| og:image | Page OG Image (separate from thumbnail) |
| canonical | Generated from public_id + page_slug |
| favicon | Project settings |

**Acceptance Criteria**:
- [ ] All SEO tags rendered correctly
- [ ] Title includes page + project name
- [ ] Description pulled from ProductDoc
- [ ] Canonical URL is accurate
- [ ] OG Image URL points to correct image

### 4.6 OG Image Generation

**Priority**: Medium

**Generation Strategy**: Mixed (proactive + on-demand)

**Tasks**:
1. Add OG Image job to queue after publish (low priority)
2. Detect first social share access
3. Upgrade OG Image job to high priority on demand
4. Implement 302 redirect to generation endpoint:
   ```
   GET /og-image/{project_id}/{page_id}
   → 302 redirect to generated image
   → Or generate synchronously if not exists
   ```
5. Cache generated images to CDN

**Acceptance Criteria**:
- [ ] OG Image queued after publish
- [ ] First social share triggers generation
- [ ] Generated images cached to CDN
- [ ] Redirect endpoint works correctly

---

## Technical Considerations

### Playwright Configuration
```javascript
const browser = await playwright.chromium.launch();
const page = await browser.newPage({
  viewport: { width: 375, height: 667 },  // Mobile
  deviceScaleFactor: 2
});
await page.goto(url);
await page.waitForLoadState('networkidle');
const screenshot = await page.screenshot({
  fullPage: true,
  type: 'png'
});
```

### Exponential Backoff
```
Attempt 1: 0s delay
Attempt 2: 30s delay
Attempt 3: 45s delay
After 3: Mark as failed, show placeholder
```

### Queue Processing
```python
async def process_thumbnail_queue():
    while True:
        async with semaphore(2):  # Max 2 concurrent
            job = await get_next_job()
            if job:
                await process_job(job)
            else:
                await asyncio.sleep(1)
```

### Storage Strategy
- Thumbnails: `/thumbnails/{project_id}/{page_id}.png`
- OG Images: `/og-images/{project_id}/{page_id}.png`
- CDN: CloudFlare or AWS CloudFront

---

## Risk Factors

| Risk | Impact | Mitigation |
|------|--------|------------|
| Playwright timeouts | Medium | 30s timeout, fallback to client-side |
| Queue growth unbounded | Low | Deduplication, cleanup job |
| CDN bandwidth costs | Low | Cache aggressively, use compression |
| OG Image slow generation | Low | On-demand with placeholder fallback |

---

## Estimated Scope

**Complexity**: Medium

**Effort Drivers**:
- Queue system design (2 days)
- Worker implementation (2 days)
- Fallback chain (1-2 days)
- SEO tags (1 day)
- Frontend UI (1 day)

**Total Estimated Duration**: 1 week

---

## Dependencies

- **Internal**: Phase 1 (Foundation)
- **External**: Playwright, CDN
- **Storage**: S3 or similar for image storage

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Thumbnail success rate | > 95% |
| Thumbnail generation time | < 30s |
| OG Image generation time | < 45s |
| Publish blocked by thumbnail | 0% |
| Social share preview accuracy | 100% |

---

## API Endpoints

```
POST /api/projects/{id}/thumbnails/generate
POST /api/projects/{id}/thumbnails/{thumbnail_id}/retry
GET /og-image/{project_id}/{page_id}
GET /api/thumbnails/queue/status
```

---

## Notes

- Thumbnail failure must NOT block publish (core requirement)
- Separate queues for thumbnails and OG Images
- Client-side fallback provides resilience
- SEO tags make pages shareable on social platforms
- OG Images generated on-demand to save resources

---

**Next Phase**: Week 5 - Polish
