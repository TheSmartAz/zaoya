# Phase 4: Forms + Analytics (v0)

**Duration**: Weeks 9-10
**Status**: Pending
**Complexity**: Medium

---

## Overview

Phase 4 completes the v0 MVP by adding the dynamic capabilities that make pages truly useful: form submissions and basic analytics. Users can create pages with working contact forms, see who's visiting, and track conversions. This phase also includes security hardening to prepare for production launch.

### Connection to Project Goals

- Enables real utility (forms that actually work)
- Provides feedback loop (analytics)
- Validates monetization potential (form submissions as value)
- Prepares for production deployment
- Completes the "5-minute to published page" metric

---

## Prerequisites

- [ ] Phase 3 complete (auth, publishing, separate origin)
- [ ] Published pages accessible via `/p/{public_id}`
- [ ] Zaoya runtime working in published pages
- [ ] User authentication functional

---

## Detailed Tasks

### Task 4.1: Form Submission Handling

**Goal**: Forms in published pages submit data to the platform

#### Sub-tasks

1. **Create submission model**
   ```python
   # backend/app/models/submission.py
   from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
   from datetime import datetime

   class FormSubmission(Base):
       __tablename__ = "form_submissions"

       id = Column(String, primary_key=True)
       project_id = Column(String, ForeignKey("projects.id"), index=True)
       form_id = Column(String, index=True)  # For multiple forms per page

       data = Column(JSON)  # Form field values
       metadata = Column(JSON)  # IP, user agent, timestamp, etc.

       created_at = Column(DateTime, default=datetime.utcnow)

       # For notification tracking
       notification_sent = Column(Boolean, default=False)
       notification_sent_at = Column(DateTime, nullable=True)
   ```

2. **Create submission API endpoint**
   ```python
   # backend/app/api/submissions.py
   from fastapi import APIRouter, Request, HTTPException

   router = APIRouter()

   @router.post("/submissions/{public_id}")
   async def submit_form(
       public_id: str,
       request: Request,
       form_data: FormSubmissionRequest
   ):
       # Verify project exists and is published
       project = await get_project_by_public_id(public_id)
       if not project or not project.published_version_id:
           raise HTTPException(status_code=404, detail="Page not found")

       # Rate limit check (by IP)
       client_ip = request.client.host
       if await is_rate_limited(client_ip, public_id):
           raise HTTPException(status_code=429, detail="Too many submissions")

       # Validate form data
       sanitized_data = sanitize_form_data(form_data.data)

       # Create submission
       submission = await create_submission(
           project_id=project.id,
           form_id=form_data.form_id or "default",
           data=sanitized_data,
           metadata={
               "ip": client_ip,
               "user_agent": request.headers.get("user-agent"),
               "referer": request.headers.get("referer"),
               "submitted_at": datetime.utcnow().isoformat(),
           }
       )

       # Queue notification if enabled
       if project.notification_email:
           await queue_notification(project, submission)

       return {"success": True, "submission_id": submission.id}

   def sanitize_form_data(data: dict) -> dict:
       """Remove potentially dangerous content from form data."""
       sanitized = {}
       for key, value in data.items():
           if isinstance(value, str):
               # Strip HTML, limit length
               sanitized[key] = bleach.clean(value[:10000])
           elif isinstance(value, (int, float, bool)):
               sanitized[key] = value
           elif isinstance(value, list):
               sanitized[key] = [bleach.clean(str(v))[:1000] for v in value[:100]]
       return sanitized
   ```

3. **Update zaoya-runtime.js for form handling**
   ```javascript
   // frontend/public/zaoya-runtime.js
   window.Zaoya = {
     // ... existing methods ...

     submitForm: async function(formElement) {
       const formData = new FormData(formElement);
       const data = Object.fromEntries(formData.entries());
       const formId = formElement.dataset.formId || 'default';

       // Get public ID from page
       const publicId = document.querySelector('meta[name="zaoya-public-id"]')?.content;
       if (!publicId) {
         console.error('Zaoya: No public ID found');
         return { success: false, error: 'Configuration error' };
       }

       try {
         const response = await fetch(`https://api.zaoya.app/submissions/${publicId}`, {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ form_id: formId, data }),
         });

         if (!response.ok) {
           throw new Error(await response.text());
         }

         const result = await response.json();

         // Track submission
         Zaoya.track('form_submit', { form_id: formId });

         return result;
       } catch (error) {
         console.error('Zaoya: Form submission failed', error);
         return { success: false, error: error.message };
       }
     },

     // Auto-attach to forms with data-zaoya-form attribute
     _initForms: function() {
       document.querySelectorAll('form[data-zaoya-form]').forEach(form => {
         form.addEventListener('submit', async (e) => {
           e.preventDefault();

           const submitBtn = form.querySelector('[type="submit"]');
           const originalText = submitBtn?.textContent;

           if (submitBtn) {
             submitBtn.disabled = true;
             submitBtn.textContent = 'Submitting...';
           }

           const result = await Zaoya.submitForm(form);

           if (result.success) {
             // Show success message
             const successMsg = form.dataset.successMessage || 'Thanks for your submission!';
             Zaoya.toast(successMsg);

             // Optionally redirect
             const redirectUrl = form.dataset.redirectUrl;
             if (redirectUrl) {
               Zaoya.navigate(redirectUrl);
             } else {
               form.reset();
             }
           } else {
             Zaoya.toast('Something went wrong. Please try again.');
           }

           if (submitBtn) {
             submitBtn.disabled = false;
             submitBtn.textContent = originalText;
           }
         });
       });
     },
   };

   // Initialize on load
   document.addEventListener('DOMContentLoaded', () => {
     Zaoya._initForms();
   });
   ```

4. **Rate limiting**
   ```python
   # backend/app/services/rate_limiter.py
   from datetime import datetime, timedelta
   from collections import defaultdict
   import asyncio

   # Simple in-memory rate limiter (use Redis in production)
   class RateLimiter:
       def __init__(self):
           self.submissions = defaultdict(list)
           self.lock = asyncio.Lock()

       async def is_limited(
           self,
           ip: str,
           public_id: str,
           max_submissions: int = 10,
           window_minutes: int = 60
       ) -> bool:
           key = f"{ip}:{public_id}"
           now = datetime.utcnow()
           window_start = now - timedelta(minutes=window_minutes)

           async with self.lock:
               # Clean old entries
               self.submissions[key] = [
                   ts for ts in self.submissions[key]
                   if ts > window_start
               ]

               # Check limit
               if len(self.submissions[key]) >= max_submissions:
                   return True

               # Record this attempt
               self.submissions[key].append(now)
               return False

   rate_limiter = RateLimiter()
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/models/submission.py` | Submission SQLAlchemy model |
| `backend/app/api/submissions.py` | Submission endpoint |
| `backend/app/services/rate_limiter.py` | Rate limiting |
| Update `frontend/public/zaoya-runtime.js` | Form handling |

---

### Task 4.2: Submission Dashboard + CSV Export

**Goal**: Page owners can view and export form submissions

#### Sub-tasks

1. **Create submissions list endpoint**
   ```python
   # backend/app/api/submissions.py
   @router.get("/projects/{project_id}/submissions")
   async def list_submissions(
       project_id: str,
       page: int = 1,
       per_page: int = 50,
       form_id: str = None,
       user: User = Depends(get_current_user)
   ):
       project = await get_project(project_id, user.id)
       if not project:
           raise HTTPException(status_code=404)

       query = select(FormSubmission).where(
           FormSubmission.project_id == project_id
       )

       if form_id:
           query = query.where(FormSubmission.form_id == form_id)

       query = query.order_by(FormSubmission.created_at.desc())
       query = query.offset((page - 1) * per_page).limit(per_page)

       submissions = await db.execute(query)
       total = await count_submissions(project_id, form_id)

       return {
           "submissions": [s.to_dict() for s in submissions],
           "pagination": {
               "page": page,
               "per_page": per_page,
               "total": total,
               "pages": (total + per_page - 1) // per_page,
           }
       }
   ```

2. **Create CSV export endpoint**
   ```python
   @router.get("/projects/{project_id}/submissions/export")
   async def export_submissions(
       project_id: str,
       form_id: str = None,
       format: str = "csv",
       user: User = Depends(get_current_user)
   ):
       project = await get_project(project_id, user.id)
       if not project:
           raise HTTPException(status_code=404)

       submissions = await get_all_submissions(project_id, form_id)

       if format == "csv":
           output = generate_csv(submissions)
           filename = f"{project.name}-submissions-{datetime.now().strftime('%Y%m%d')}.csv"
           return Response(
               content=output,
               media_type="text/csv",
               headers={"Content-Disposition": f"attachment; filename={filename}"}
           )
       else:
           return {"submissions": [s.to_dict() for s in submissions]}

   def generate_csv(submissions: list[FormSubmission]) -> str:
       import csv
       import io

       if not submissions:
           return ""

       # Collect all unique keys from all submissions
       all_keys = set()
       for s in submissions:
           all_keys.update(s.data.keys())

       output = io.StringIO()
       writer = csv.writer(output)

       # Header row
       headers = ["Submitted At", "Form ID"] + sorted(all_keys)
       writer.writerow(headers)

       # Data rows
       for s in submissions:
           row = [
               s.created_at.isoformat(),
               s.form_id,
           ] + [s.data.get(key, "") for key in sorted(all_keys)]
           writer.writerow(row)

       return output.getvalue()
   ```

3. **Build submissions dashboard UI**
   ```tsx
   // frontend/src/pages/SubmissionsPage.tsx
   export function SubmissionsPage() {
     const { projectId } = useParams();
     const [submissions, setSubmissions] = useState<Submission[]>([]);
     const [pagination, setPagination] = useState({ page: 1, total: 0 });

     const fetchSubmissions = async (page: number) => {
       const token = useAuthStore.getState().token;
       const response = await fetch(
         `/api/projects/${projectId}/submissions?page=${page}`,
         { headers: { Authorization: `Bearer ${token}` } }
       );
       const data = await response.json();
       setSubmissions(data.submissions);
       setPagination(data.pagination);
     };

     const handleExport = async () => {
       const token = useAuthStore.getState().token;
       const response = await fetch(
         `/api/projects/${projectId}/submissions/export`,
         { headers: { Authorization: `Bearer ${token}` } }
       );
       const blob = await response.blob();
       const url = URL.createObjectURL(blob);
       const a = document.createElement('a');
       a.href = url;
       a.download = `submissions-${projectId}.csv`;
       a.click();
     };

     return (
       <div className="container mx-auto p-6">
         <div className="flex justify-between items-center mb-6">
           <h1 className="text-2xl font-bold">Form Submissions</h1>
           <button
             onClick={handleExport}
             className="px-4 py-2 bg-green-600 text-white rounded"
           >
             Export CSV
           </button>
         </div>

         <SubmissionsTable submissions={submissions} />

         <Pagination
           current={pagination.page}
           total={pagination.pages}
           onChange={(page) => fetchSubmissions(page)}
         />
       </div>
     );
   }
   ```

4. **Submissions table component**
   ```tsx
   // frontend/src/components/submissions/SubmissionsTable.tsx
   export function SubmissionsTable({ submissions }: { submissions: Submission[] }) {
     if (submissions.length === 0) {
       return (
         <div className="text-center py-12 text-gray-500">
           No submissions yet. Share your page to start collecting responses!
         </div>
       );
     }

     // Get all unique field names
     const allFields = new Set<string>();
     submissions.forEach((s) => {
       Object.keys(s.data).forEach((key) => allFields.add(key));
     });
     const fields = Array.from(allFields);

     return (
       <div className="overflow-x-auto">
         <table className="w-full border-collapse">
           <thead>
             <tr className="bg-gray-100">
               <th className="p-3 text-left">Submitted</th>
               {fields.map((field) => (
                 <th key={field} className="p-3 text-left capitalize">
                   {field}
                 </th>
               ))}
             </tr>
           </thead>
           <tbody>
             {submissions.map((submission) => (
               <tr key={submission.id} className="border-b hover:bg-gray-50">
                 <td className="p-3 text-sm text-gray-500">
                   {formatDate(submission.created_at)}
                 </td>
                 {fields.map((field) => (
                   <td key={field} className="p-3">
                     {submission.data[field] || '-'}
                   </td>
                 ))}
               </tr>
             ))}
           </tbody>
         </table>
       </div>
     );
   }
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/pages/SubmissionsPage.tsx` | Submissions dashboard |
| `frontend/src/components/submissions/SubmissionsTable.tsx` | Table display |
| `frontend/src/components/submissions/SubmissionDetail.tsx` | Single submission view |

---

### Task 4.3: Basic Analytics (Views, Clicks, Submits)

**Goal**: Track page performance with simple metrics

#### Sub-tasks

1. **Create analytics model**
   ```python
   # backend/app/models/analytics.py
   from sqlalchemy import Column, String, Integer, Date, JSON

   class PageAnalytics(Base):
       __tablename__ = "page_analytics"

       id = Column(String, primary_key=True)
       project_id = Column(String, ForeignKey("projects.id"), index=True)
       date = Column(Date, index=True)

       # Aggregated daily counts
       views = Column(Integer, default=0)
       unique_visitors = Column(Integer, default=0)
       cta_clicks = Column(Integer, default=0)
       form_submissions = Column(Integer, default=0)

       # Event breakdown (optional detail)
       events = Column(JSON, default=dict)  # {"button_signup": 5, "link_twitter": 3}

       class Config:
           # Unique constraint on project_id + date
           __table_args__ = (
               UniqueConstraint('project_id', 'date', name='unique_project_date'),
           )
   ```

2. **Create tracking endpoint**
   ```python
   # backend/app/api/analytics.py
   from fastapi import APIRouter, Request
   from datetime import date

   router = APIRouter()

   @router.post("/track/{public_id}")
   async def track_event(
       public_id: str,
       request: Request,
       event: TrackEventRequest
   ):
       project = await get_project_by_public_id(public_id)
       if not project:
           return {"success": False}  # Silently fail for invalid pages

       today = date.today()

       # Get or create today's analytics record
       analytics = await get_or_create_analytics(project.id, today)

       # Update based on event type
       if event.type == "page_view":
           analytics.views += 1
           # Track unique by hashing IP (privacy-friendly)
           visitor_hash = hash_visitor(request.client.host)
           if visitor_hash not in (analytics.events.get("visitors") or []):
               analytics.unique_visitors += 1
               analytics.events.setdefault("visitors", []).append(visitor_hash)

       elif event.type == "cta_click":
           analytics.cta_clicks += 1
           event_name = event.data.get("button", "unknown")
           analytics.events[event_name] = analytics.events.get(event_name, 0) + 1

       elif event.type == "form_submit":
           analytics.form_submissions += 1

       await save_analytics(analytics)
       return {"success": True}

   def hash_visitor(ip: str) -> str:
       """Hash IP for privacy-friendly unique visitor counting."""
       import hashlib
       # Add daily salt so we can't track across days
       salt = date.today().isoformat()
       return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()[:16]
   ```

3. **Update Zaoya runtime for tracking**
   ```javascript
   // frontend/public/zaoya-runtime.js
   window.Zaoya = {
     // ... existing methods ...

     track: async function(eventType, data = {}) {
       const publicId = document.querySelector('meta[name="zaoya-public-id"]')?.content;
       if (!publicId) return;

       try {
         await fetch(`https://api.zaoya.app/track/${publicId}`, {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ type: eventType, data }),
           // Fire and forget - don't block on response
           keepalive: true,
         });
       } catch {
         // Silently fail
       }
     },

     // Track CTA clicks automatically
     _initTracking: function() {
       // Track page view
       Zaoya.track('page_view');

       // Track clicks on elements with data-track attribute
       document.addEventListener('click', (e) => {
         const tracked = e.target.closest('[data-track]');
         if (tracked) {
           const eventName = tracked.dataset.track;
           Zaoya.track('cta_click', { button: eventName });
         }
       });

       // Track all button/link clicks as CTA
       document.addEventListener('click', (e) => {
         const element = e.target.closest('button, a[href]');
         if (element && !element.dataset.track) {
           const label = element.textContent?.trim().slice(0, 50) ||
                        element.getAttribute('aria-label') ||
                        'unknown';
           Zaoya.track('cta_click', { button: label });
         }
       });
     },
   };

   document.addEventListener('DOMContentLoaded', () => {
     Zaoya._initForms();
     Zaoya._initTracking();
   });
   ```

4. **Create analytics dashboard endpoint**
   ```python
   @router.get("/projects/{project_id}/analytics")
   async def get_analytics(
       project_id: str,
       days: int = 30,
       user: User = Depends(get_current_user)
   ):
       project = await get_project(project_id, user.id)
       if not project:
           raise HTTPException(status_code=404)

       end_date = date.today()
       start_date = end_date - timedelta(days=days)

       daily_data = await get_analytics_range(project_id, start_date, end_date)

       # Aggregate totals
       totals = {
           "views": sum(d.views for d in daily_data),
           "unique_visitors": sum(d.unique_visitors for d in daily_data),
           "cta_clicks": sum(d.cta_clicks for d in daily_data),
           "form_submissions": sum(d.form_submissions for d in daily_data),
       }

       # Calculate trends (compare to previous period)
       prev_start = start_date - timedelta(days=days)
       prev_data = await get_analytics_range(project_id, prev_start, start_date)
       prev_totals = {
           "views": sum(d.views for d in prev_data),
           "unique_visitors": sum(d.unique_visitors for d in prev_data),
       }

       return {
           "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
           "totals": totals,
           "trends": {
               "views": calculate_trend(totals["views"], prev_totals["views"]),
               "visitors": calculate_trend(totals["unique_visitors"], prev_totals["unique_visitors"]),
           },
           "daily": [
               {
                   "date": d.date.isoformat(),
                   "views": d.views,
                   "visitors": d.unique_visitors,
                   "clicks": d.cta_clicks,
                   "submissions": d.form_submissions,
               }
               for d in daily_data
           ],
       }

   def calculate_trend(current: int, previous: int) -> float:
       if previous == 0:
           return 100 if current > 0 else 0
       return round((current - previous) / previous * 100, 1)
   ```

5. **Build analytics dashboard UI**
   ```tsx
   // frontend/src/pages/AnalyticsPage.tsx
   export function AnalyticsPage() {
     const { projectId } = useParams();
     const [analytics, setAnalytics] = useState<Analytics | null>(null);
     const [period, setPeriod] = useState(30);

     useEffect(() => {
       fetchAnalytics();
     }, [projectId, period]);

     return (
       <div className="container mx-auto p-6">
         <div className="flex justify-between items-center mb-6">
           <h1 className="text-2xl font-bold">Analytics</h1>
           <select
             value={period}
             onChange={(e) => setPeriod(Number(e.target.value))}
             className="border rounded p-2"
           >
             <option value={7}>Last 7 days</option>
             <option value={30}>Last 30 days</option>
             <option value={90}>Last 90 days</option>
           </select>
         </div>

         {analytics && (
           <>
             <div className="grid grid-cols-4 gap-4 mb-8">
               <StatCard
                 label="Page Views"
                 value={analytics.totals.views}
                 trend={analytics.trends.views}
               />
               <StatCard
                 label="Unique Visitors"
                 value={analytics.totals.unique_visitors}
                 trend={analytics.trends.visitors}
               />
               <StatCard
                 label="CTA Clicks"
                 value={analytics.totals.cta_clicks}
               />
               <StatCard
                 label="Form Submissions"
                 value={analytics.totals.form_submissions}
               />
             </div>

             <AnalyticsChart data={analytics.daily} />
           </>
         )}
       </div>
     );
   }
   ```

6. **Simple chart component**
   ```tsx
   // frontend/src/components/analytics/AnalyticsChart.tsx
   export function AnalyticsChart({ data }: { data: DailyAnalytics[] }) {
     // Simple bar/line chart using CSS or lightweight library
     const maxViews = Math.max(...data.map((d) => d.views), 1);

     return (
       <div className="bg-white rounded-lg p-4 border">
         <h3 className="font-semibold mb-4">Daily Views</h3>
         <div className="flex items-end gap-1 h-40">
           {data.map((day) => (
             <div
               key={day.date}
               className="flex-1 bg-blue-500 rounded-t hover:bg-blue-600 transition-colors"
               style={{ height: `${(day.views / maxViews) * 100}%` }}
               title={`${day.date}: ${day.views} views`}
             />
           ))}
         </div>
         <div className="flex justify-between text-xs text-gray-500 mt-2">
           <span>{data[0]?.date}</span>
           <span>{data[data.length - 1]?.date}</span>
         </div>
       </div>
     );
   }
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/models/analytics.py` | Analytics SQLAlchemy model |
| `backend/app/api/analytics.py` | Tracking + dashboard endpoints |
| `frontend/src/pages/AnalyticsPage.tsx` | Analytics dashboard |
| `frontend/src/components/analytics/StatCard.tsx` | Metric display |
| `frontend/src/components/analytics/AnalyticsChart.tsx` | Simple chart |

---

### Task 4.4: Email Notifications (Optional)

**Goal**: Page owners can receive email when forms are submitted

#### Sub-tasks

1. **Add notification settings to project**
   ```python
   # Update backend/app/models/project.py
   class Project(Base):
       # ... existing fields ...

       notification_email = Column(String, nullable=True)
       notification_enabled = Column(Boolean, default=False)
   ```

2. **Create email service**
   ```python
   # backend/app/services/email_service.py
   import httpx
   from string import Template

   class EmailService:
       def __init__(self):
           self.api_key = os.getenv("EMAIL_API_KEY")  # Resend, SendGrid, etc.
           self.from_email = "notifications@zaoya.app"

       async def send_submission_notification(
           self,
           to_email: str,
           project_name: str,
           submission_data: dict
       ):
           subject = f"New submission on {project_name}"

           body = Template("""
           You received a new form submission on your Zaoya page "$project_name".

           Submission details:
           $fields

           View all submissions: https://zaoya.app/dashboard/$project_id/submissions

           ---
           Zaoya - Create pages with AI
           """).substitute(
               project_name=project_name,
               fields=format_fields(submission_data),
               project_id=submission_data.get("project_id"),
           )

           await self._send(to_email, subject, body)

       async def _send(self, to: str, subject: str, body: str):
           # Using Resend API as example
           async with httpx.AsyncClient() as client:
               await client.post(
                   "https://api.resend.com/emails",
                   headers={"Authorization": f"Bearer {self.api_key}"},
                   json={
                       "from": self.from_email,
                       "to": to,
                       "subject": subject,
                       "text": body,
                   }
               )

   email_service = EmailService()
   ```

3. **Queue notifications**
   ```python
   # backend/app/services/notification_queue.py
   import asyncio
   from collections import deque

   class NotificationQueue:
       def __init__(self):
           self.queue = deque()
           self._running = False

       async def add(self, project: Project, submission: FormSubmission):
           if project.notification_enabled and project.notification_email:
               self.queue.append((project, submission))
               if not self._running:
                   asyncio.create_task(self._process())

       async def _process(self):
           self._running = True
           while self.queue:
               project, submission = self.queue.popleft()
               try:
                   await email_service.send_submission_notification(
                       to_email=project.notification_email,
                       project_name=project.name,
                       submission_data=submission.data,
                   )
                   submission.notification_sent = True
                   submission.notification_sent_at = datetime.utcnow()
                   await save_submission(submission)
               except Exception as e:
                   print(f"Failed to send notification: {e}")
                   # Re-queue for retry? Or log and move on
           self._running = False

   notification_queue = NotificationQueue()
   ```

4. **Notification settings UI**
   ```tsx
   // frontend/src/components/project/NotificationSettings.tsx
   export function NotificationSettings({ project }: { project: Project }) {
     const [email, setEmail] = useState(project.notification_email || '');
     const [enabled, setEnabled] = useState(project.notification_enabled);

     const handleSave = async () => {
       await fetch(`/api/projects/${project.id}`, {
         method: 'PATCH',
         headers: {
           'Content-Type': 'application/json',
           Authorization: `Bearer ${token}`,
         },
         body: JSON.stringify({
           notification_email: email,
           notification_enabled: enabled,
         }),
       });
     };

     return (
       <div className="space-y-4">
         <h3 className="font-semibold">Email Notifications</h3>

         <label className="flex items-center gap-2">
           <input
             type="checkbox"
             checked={enabled}
             onChange={(e) => setEnabled(e.target.checked)}
           />
           <span>Send email when form is submitted</span>
         </label>

         {enabled && (
           <input
             type="email"
             value={email}
             onChange={(e) => setEmail(e.target.value)}
             placeholder="your@email.com"
             className="w-full p-2 border rounded"
           />
         )}

         <button
           onClick={handleSave}
           className="px-4 py-2 bg-blue-600 text-white rounded"
         >
           Save
         </button>
       </div>
     );
   }
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/services/email_service.py` | Email sending |
| `backend/app/services/notification_queue.py` | Async notification queue |
| `frontend/src/components/project/NotificationSettings.tsx` | Settings UI |

---

### Task 4.5: Security Hardening

**Goal**: Prepare for production with comprehensive security measures

#### Sub-tasks

1. **Input validation layer**
   ```python
   # backend/app/middleware/validation.py
   from fastapi import Request, HTTPException
   from pydantic import ValidationError

   async def validate_request_size(request: Request, call_next):
       # Limit request body size
       content_length = request.headers.get("content-length")
       if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
           raise HTTPException(status_code=413, detail="Request too large")
       return await call_next(request)
   ```

2. **Rate limiting middleware**
   ```python
   # backend/app/middleware/rate_limit.py
   from fastapi import Request, HTTPException
   from datetime import datetime, timedelta
   from collections import defaultdict

   class GlobalRateLimiter:
       def __init__(self):
           self.requests = defaultdict(list)

       async def __call__(self, request: Request, call_next):
           ip = request.client.host
           now = datetime.utcnow()
           window_start = now - timedelta(minutes=1)

           # Clean old requests
           self.requests[ip] = [ts for ts in self.requests[ip] if ts > window_start]

           # Check limit (100 requests per minute per IP)
           if len(self.requests[ip]) >= 100:
               raise HTTPException(status_code=429, detail="Too many requests")

           self.requests[ip].append(now)
           return await call_next(request)
   ```

3. **Security headers**
   ```python
   # backend/app/middleware/security_headers.py
   from fastapi import Request

   async def add_security_headers(request: Request, call_next):
       response = await call_next(request)

       # Common security headers
       response.headers["X-Content-Type-Options"] = "nosniff"
       response.headers["X-Frame-Options"] = "DENY"
       response.headers["X-XSS-Protection"] = "1; mode=block"
       response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

       # HSTS (only in production)
       if os.getenv("ENV") == "production":
           response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

       return response
   ```

4. **Database security**
   ```python
   # backend/app/database.py
   from sqlalchemy import create_engine
   from sqlalchemy.pool import QueuePool

   # Use connection pooling
   engine = create_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=5,
       max_overflow=10,
       pool_timeout=30,
       pool_recycle=1800,
   )

   # Parameterized queries only (SQLAlchemy handles this)
   # Never use string interpolation for SQL
   ```

5. **Secrets management**
   ```python
   # backend/app/config.py
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       database_url: str
       jwt_secret: str
       google_client_id: str
       google_client_secret: str
       email_api_key: str

       # AI API keys
       glm_api_key: str
       deepseek_api_key: str
       # ... other models

       class Config:
           env_file = ".env"
           env_file_encoding = "utf-8"

   settings = Settings()
   ```

6. **Error handling (don't leak info)**
   ```python
   # backend/app/middleware/error_handler.py
   from fastapi import Request
   from fastapi.responses import JSONResponse
   import traceback

   async def error_handler(request: Request, call_next):
       try:
           return await call_next(request)
       except Exception as e:
           # Log full error internally
           print(f"Error: {e}")
           print(traceback.format_exc())

           # Return generic message to client
           return JSONResponse(
               status_code=500,
               content={"detail": "Internal server error"}
           )
   ```

7. **Security checklist before launch**
   ```markdown
   ## Pre-Launch Security Checklist

   ### Authentication
   - [ ] JWT tokens expire appropriately
   - [ ] Password hashing uses bcrypt
   - [ ] OAuth secrets not in code
   - [ ] Session invalidation on password change

   ### Input Validation
   - [ ] All user input sanitized
   - [ ] File uploads validated (type, size)
   - [ ] SQL injection prevented (parameterized queries)
   - [ ] XSS prevented (output encoding)

   ### Network Security
   - [ ] HTTPS enforced everywhere
   - [ ] CORS properly configured
   - [ ] Rate limiting in place
   - [ ] CSP headers on published pages

   ### Data Protection
   - [ ] Sensitive data encrypted at rest
   - [ ] Secrets in environment variables
   - [ ] Database backups encrypted
   - [ ] Logs don't contain secrets

   ### Monitoring
   - [ ] Error logging configured
   - [ ] Failed login attempts tracked
   - [ ] Rate limit violations logged
   - [ ] Unusual activity alerts
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/middleware/validation.py` | Request validation |
| `backend/app/middleware/rate_limit.py` | Rate limiting |
| `backend/app/middleware/security_headers.py` | Security headers |
| `backend/app/middleware/error_handler.py` | Safe error handling |
| `backend/app/config.py` | Centralized config |
| `docs/SECURITY_CHECKLIST.md` | Pre-launch checklist |

---

## Technical Considerations

### Key Dependencies (Phase 4 additions)

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | ^0.26 | Email API calls |
| `pydantic-settings` | ^2.0 | Configuration management |

### Architecture Decisions

1. **Why simple in-memory rate limiting for v0?**
   - Sufficient for initial launch
   - No Redis dependency
   - Upgrade path clear (add Redis later)

2. **Why daily aggregated analytics?**
   - Privacy-friendly (no raw events stored)
   - Simple to query and display
   - Sufficient granularity for v0

3. **Why fire-and-forget tracking?**
   - Doesn't slow down page load
   - Acceptable to lose some events
   - Better user experience

---

## Acceptance Criteria

- [ ] Forms submit data via Zaoya.submitForm()
- [ ] Submissions stored in database per project
- [ ] Submission dashboard shows all entries
- [ ] CSV export downloads properly formatted file
- [ ] Page views tracked when page loads
- [ ] CTA clicks tracked when buttons/links clicked
- [ ] Analytics dashboard shows views, visitors, clicks, submissions
- [ ] Trend comparison (vs previous period) displayed
- [ ] Email notifications send when enabled
- [ ] Rate limiting prevents abuse
- [ ] Security headers present on all responses
- [ ] No sensitive data in error messages

---

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Analytics tracking blocked | Medium | Low | Fire-and-forget, not critical path |
| Email delivery issues | Medium | Medium | Queue with retries, fallback notification |
| Rate limiter too aggressive | Medium | Medium | Tune limits, allow burst |
| Form spam | High | Medium | Rate limit, CAPTCHA option in v1 |

---

## Estimated Effort

| Task | Complexity | Effort |
|------|------------|--------|
| 4.1 Form Submission | Medium | 3-4 days |
| 4.2 Submission Dashboard | Medium | 2-3 days |
| 4.3 Basic Analytics | Medium | 3-4 days |
| 4.4 Email Notifications | Small | 1-2 days |
| 4.5 Security Hardening | Medium | 2-3 days |
| **Testing & Polish** | - | 2-3 days |
| **Total** | **Medium** | **13-19 days (2-3 weeks)** |

---

## Definition of Done

Phase 4 is complete when:
1. Forms work end-to-end (submit → store → view → export)
2. Analytics track views, clicks, and submissions
3. Email notifications work for form submissions
4. Security hardening complete (rate limits, headers, validation)
5. Pre-launch security checklist passed
6. All acceptance criteria met
7. No regression in Phase 1-3 functionality
8. Ready for production deployment

---

## v0 Complete

When Phase 4 is done, Zaoya v0 is complete:

- ✅ Chat-first AI page generation
- ✅ Template selection + adaptive interview
- ✅ Quick action refinement
- ✅ Version history + restore
- ✅ User authentication
- ✅ Guest → user conversion
- ✅ Draft → published flow
- ✅ Secure page hosting (separate origin)
- ✅ Working form submissions
- ✅ Basic analytics
- ✅ Production-ready security

**Next**: Launch, gather feedback, plan v1 features!
