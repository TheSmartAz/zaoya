# Phase 3: Publishing (v0)

**Duration**: Weeks 7-8
**Status**: Pending
**Complexity**: Medium

---

## Overview

Phase 3 enables users to go from draft to published, shareable page. This phase adds user authentication, implements draft vs published states, deploys the separate origin for security, and generates shareable links. By the end, users can share their pages with the world.

### Connection to Project Goals

- Completes the core loop: "Describe → See → Share"
- Validates user willingness to publish and share
- Establishes the security model (separate origin)
- Enables guest-to-user conversion funnel
- Creates foundation for analytics (Phase 4)

---

## Prerequisites

- [ ] Phase 2 complete (templates, interview, quick actions, versioning)
- [ ] HTML/JS validation working
- [ ] Version snapshots being created
- [ ] Basic project persistence (at least localStorage)

---

## Detailed Tasks

### Task 3.1: User Authentication (Google/Email)

**Goal**: Users can sign up/in to save projects and publish pages

#### Sub-tasks

1. **Set up authentication backend**
   ```python
   # backend/app/services/auth_service.py
   from datetime import datetime, timedelta
   from jose import jwt
   from passlib.context import CryptContext

   SECRET_KEY = os.getenv("JWT_SECRET")
   ALGORITHM = "HS256"
   ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

   class AuthService:
       def create_access_token(self, user_id: str) -> str:
           expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
           to_encode = {"sub": user_id, "exp": expire}
           return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

       def verify_token(self, token: str) -> str | None:
           try:
               payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
               return payload.get("sub")
           except:
               return None

       def hash_password(self, password: str) -> str:
           return pwd_context.hash(password)

       def verify_password(self, plain: str, hashed: str) -> bool:
           return pwd_context.verify(plain, hashed)
   ```

2. **Create user model**
   ```python
   # backend/app/models/user.py
   from sqlalchemy import Column, String, DateTime
   from datetime import datetime

   class User(Base):
       __tablename__ = "users"

       id = Column(String, primary_key=True)
       email = Column(String, unique=True, index=True)
       password_hash = Column(String, nullable=True)  # Null for OAuth users
       name = Column(String, nullable=True)
       avatar_url = Column(String, nullable=True)
       provider = Column(String, default="email")  # email, google
       provider_id = Column(String, nullable=True)
       created_at = Column(DateTime, default=datetime.utcnow)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   ```

3. **Implement Google OAuth**
   ```python
   # backend/app/api/auth.py
   from fastapi import APIRouter, HTTPException
   from google.oauth2 import id_token
   from google.auth.transport import requests

   router = APIRouter()

   @router.post("/auth/google")
   async def google_auth(request: GoogleAuthRequest):
       try:
           # Verify the Google token
           idinfo = id_token.verify_oauth2_token(
               request.credential,
               requests.Request(),
               GOOGLE_CLIENT_ID
           )

           email = idinfo["email"]
           name = idinfo.get("name")
           picture = idinfo.get("picture")

           # Find or create user
           user = await get_or_create_user(
               email=email,
               name=name,
               avatar_url=picture,
               provider="google",
               provider_id=idinfo["sub"]
           )

           # Generate JWT
           token = auth_service.create_access_token(user.id)

           return {"token": token, "user": user_to_dict(user)}

       except ValueError:
           raise HTTPException(status_code=401, detail="Invalid token")

   @router.post("/auth/email/signup")
   async def email_signup(request: EmailSignupRequest):
       existing = await get_user_by_email(request.email)
       if existing:
           raise HTTPException(status_code=400, detail="Email already registered")

       user = await create_user(
           email=request.email,
           password_hash=auth_service.hash_password(request.password),
           provider="email"
       )

       token = auth_service.create_access_token(user.id)
       return {"token": token, "user": user_to_dict(user)}

   @router.post("/auth/email/signin")
   async def email_signin(request: EmailSigninRequest):
       user = await get_user_by_email(request.email)
       if not user or not auth_service.verify_password(request.password, user.password_hash):
           raise HTTPException(status_code=401, detail="Invalid credentials")

       token = auth_service.create_access_token(user.id)
       return {"token": token, "user": user_to_dict(user)}
   ```

4. **Frontend auth store**
   ```typescript
   // frontend/src/stores/authStore.ts
   interface AuthState {
     user: User | null;
     token: string | null;
     isLoading: boolean;

     setAuth: (user: User, token: string) => void;
     logout: () => void;
     checkAuth: () => Promise<void>;
   }

   export const useAuthStore = create<AuthState>()(
     persist(
       (set, get) => ({
         user: null,
         token: null,
         isLoading: true,

         setAuth: (user, token) => {
           set({ user, token, isLoading: false });
         },

         logout: () => {
           set({ user: null, token: null });
         },

         checkAuth: async () => {
           const token = get().token;
           if (!token) {
             set({ isLoading: false });
             return;
           }

           try {
             const response = await fetch('/api/auth/me', {
               headers: { Authorization: `Bearer ${token}` },
             });
             if (response.ok) {
               const user = await response.json();
               set({ user, isLoading: false });
             } else {
               set({ user: null, token: null, isLoading: false });
             }
           } catch {
             set({ isLoading: false });
           }
         },
       }),
       { name: 'zaoya-auth' }
     )
   );
   ```

5. **Auth UI components**
   ```
   frontend/src/components/auth/
   ├── AuthModal.tsx           # Sign in/up modal
   ├── GoogleButton.tsx        # Google OAuth button
   ├── EmailForm.tsx           # Email/password form
   ├── UserMenu.tsx            # Logged-in user dropdown
   └── AuthGuard.tsx           # Protected route wrapper
   ```

6. **Google OAuth setup**
   ```typescript
   // frontend/src/components/auth/GoogleButton.tsx
   import { GoogleLogin } from '@react-oauth/google';

   export function GoogleButton({ onSuccess }: { onSuccess: (user: User) => void }) {
     const handleSuccess = async (response: any) => {
       const result = await fetch('/api/auth/google', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ credential: response.credential }),
       });

       const data = await result.json();
       useAuthStore.getState().setAuth(data.user, data.token);
       onSuccess(data.user);
     };

     return (
       <GoogleLogin
         onSuccess={handleSuccess}
         onError={() => console.error('Google login failed')}
       />
     );
   }
   ```

7. **Dev bypass mode**
   ```typescript
   // frontend/src/config.ts
   export const config = {
     authBypass: import.meta.env.VITE_AUTH_BYPASS === 'true',
   };

   // In AuthGuard.tsx
   if (config.authBypass) {
     return <>{children}</>;
   }
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/services/auth_service.py` | JWT + password handling |
| `backend/app/models/user.py` | User SQLAlchemy model |
| `backend/app/api/auth.py` | Auth endpoints |
| `frontend/src/stores/authStore.ts` | Auth state management |
| `frontend/src/components/auth/AuthModal.tsx` | Sign in/up modal |
| `frontend/src/components/auth/GoogleButton.tsx` | Google OAuth |
| `frontend/src/components/auth/UserMenu.tsx` | User dropdown |

---

### Task 3.2: Guest → Signed-in Conversion

**Goal**: Allow users to start without account, then prompt to save/publish

#### Sub-tasks

1. **Define guest project structure**
   ```typescript
   // frontend/src/types/project.ts
   interface Project {
     id: string;
     name: string;
     templateId: string;
     templateInputs: Record<string, string>;
     currentVersion: Version | null;
     isGuest: boolean;           // True if not yet saved to server
     localStorageKey?: string;   // For guest projects
     userId?: string;            // Set after conversion
     createdAt: number;
     updatedAt: number;
   }
   ```

2. **Guest project storage**
   ```typescript
   // frontend/src/stores/projectStore.ts
   const GUEST_PROJECTS_KEY = 'zaoya-guest-projects';

   export const useProjectStore = create<ProjectState>()(
     persist(
       (set, get) => ({
         projects: [],
         currentProjectId: null,

         createGuestProject: (template, inputs) => {
           const project: Project = {
             id: `guest_${generateId()}`,
             name: template.name,
             templateId: template.id,
             templateInputs: inputs,
             currentVersion: null,
             isGuest: true,
             createdAt: Date.now(),
             updatedAt: Date.now(),
           };
           set((state) => ({
             projects: [...state.projects, project],
             currentProjectId: project.id,
           }));
           return project;
         },

         convertToUserProject: async (projectId: string) => {
           const project = get().projects.find((p) => p.id === projectId);
           if (!project || !project.isGuest) return;

           const token = useAuthStore.getState().token;
           if (!token) throw new Error('Not authenticated');

           // Save to server
           const response = await fetch('/api/projects', {
             method: 'POST',
             headers: {
               'Content-Type': 'application/json',
               Authorization: `Bearer ${token}`,
             },
             body: JSON.stringify(project),
           });

           const savedProject = await response.json();

           // Update local state
           set((state) => ({
             projects: state.projects.map((p) =>
               p.id === projectId
                 ? { ...savedProject, isGuest: false }
                 : p
             ),
           }));

           return savedProject;
         },
       }),
       { name: GUEST_PROJECTS_KEY }
     )
   );
   ```

3. **Conversion prompt UI**
   ```tsx
   // frontend/src/components/project/ConversionPrompt.tsx
   interface ConversionPromptProps {
     project: Project;
     trigger: 'publish' | 'save' | 'limit';
   }

   export function ConversionPrompt({ project, trigger }: ConversionPromptProps) {
     const [showAuth, setShowAuth] = useState(false);

     const messages = {
       publish: "Sign in to publish and share your page",
       save: "Sign in to save your project",
       limit: "Sign in to create more projects (guest limit: 3)",
     };

     return (
       <>
         <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
           <p className="text-blue-800 mb-3">{messages[trigger]}</p>
           <button
             onClick={() => setShowAuth(true)}
             className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
           >
             Sign in to continue
           </button>
         </div>

         <AuthModal
           isOpen={showAuth}
           onClose={() => setShowAuth(false)}
           onSuccess={() => {
             useProjectStore.getState().convertToUserProject(project.id);
           }}
         />
       </>
     );
   }
   ```

4. **Guest project limits**
   ```typescript
   // frontend/src/hooks/useGuestLimits.ts
   const GUEST_PROJECT_LIMIT = 3;

   export function useGuestLimits() {
     const projects = useProjectStore((s) => s.projects);
     const user = useAuthStore((s) => s.user);

     const guestProjects = projects.filter((p) => p.isGuest);
     const canCreateMore = user || guestProjects.length < GUEST_PROJECT_LIMIT;
     const remainingSlots = GUEST_PROJECT_LIMIT - guestProjects.length;

     return {
       canCreateMore,
       remainingSlots,
       isGuest: !user,
       guestProjectCount: guestProjects.length,
     };
   }
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/stores/projectStore.ts` | Project state + guest handling |
| `frontend/src/components/project/ConversionPrompt.tsx` | Sign-in nudge |
| `frontend/src/hooks/useGuestLimits.ts` | Guest limits logic |

---

### Task 3.3: Draft vs Published States

**Goal**: Separate editable draft from immutable published version

#### Sub-tasks

1. **Extend project model**
   ```python
   # backend/app/models/project.py
   class Project(Base):
       __tablename__ = "projects"

       id = Column(String, primary_key=True)
       user_id = Column(String, ForeignKey("users.id"), index=True)
       name = Column(String)
       template_id = Column(String)
       template_inputs = Column(JSON)

       # Draft state (always current working version)
       draft_version_id = Column(String, ForeignKey("versions.id"), nullable=True)

       # Published state (immutable snapshot)
       published_version_id = Column(String, ForeignKey("versions.id"), nullable=True)
       public_id = Column(String, unique=True, index=True, nullable=True)
       published_at = Column(DateTime, nullable=True)

       created_at = Column(DateTime, default=datetime.utcnow)
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   ```

2. **Create publish endpoint**
   ```python
   # backend/app/api/projects.py
   @router.post("/projects/{project_id}/publish")
   async def publish_project(
       project_id: str,
       user: User = Depends(get_current_user)
   ):
       project = await get_project(project_id, user.id)
       if not project:
           raise HTTPException(status_code=404, detail="Project not found")

       if not project.draft_version_id:
           raise HTTPException(status_code=400, detail="No draft to publish")

       # Get current draft version
       draft_version = await get_version(project.draft_version_id)

       # Create published snapshot (copy of draft)
       published_version = await create_version(
           project_id=project.id,
           html=draft_version.html,
           js=draft_version.js,
           metadata={
               **draft_version.metadata,
               "published_at": datetime.utcnow().isoformat(),
           }
       )

       # Generate public ID if first publish
       if not project.public_id:
           project.public_id = generate_public_id()

       # Update project
       project.published_version_id = published_version.id
       project.published_at = datetime.utcnow()
       await save_project(project)

       return {
           "publicId": project.public_id,
           "publishedAt": project.published_at.isoformat(),
           "url": f"https://pages.zaoya.app/p/{project.public_id}",
       }
   ```

3. **Frontend publish flow**
   ```typescript
   // frontend/src/hooks/usePublish.ts
   export function usePublish(projectId: string) {
     const [isPublishing, setIsPublishing] = useState(false);
     const [publishedUrl, setPublishedUrl] = useState<string | null>(null);

     const publish = async () => {
       const token = useAuthStore.getState().token;
       if (!token) {
         // Trigger auth modal
         return { needsAuth: true };
       }

       setIsPublishing(true);
       try {
         const response = await fetch(`/api/projects/${projectId}/publish`, {
           method: 'POST',
           headers: { Authorization: `Bearer ${token}` },
         });

         const data = await response.json();
         setPublishedUrl(data.url);
         return { success: true, url: data.url };
       } catch (error) {
         return { success: false, error };
       } finally {
         setIsPublishing(false);
       }
     };

     return { publish, isPublishing, publishedUrl };
   }
   ```

4. **Publish button UI**
   ```tsx
   // frontend/src/components/editor/PublishButton.tsx
   export function PublishButton({ projectId }: { projectId: string }) {
     const { publish, isPublishing, publishedUrl } = usePublish(projectId);
     const [showSuccess, setShowSuccess] = useState(false);
     const user = useAuthStore((s) => s.user);
     const project = useProjectStore((s) =>
       s.projects.find((p) => p.id === projectId)
     );

     const handlePublish = async () => {
       if (project?.isGuest && !user) {
         // Show conversion prompt
         return;
       }

       const result = await publish();
       if (result.success) {
         setShowSuccess(true);
       }
     };

     return (
       <>
         <button
           onClick={handlePublish}
           disabled={isPublishing}
           className="bg-green-600 text-white px-4 py-2 rounded-lg
                      hover:bg-green-700 disabled:opacity-50"
         >
           {isPublishing ? 'Publishing...' : 'Publish'}
         </button>

         {showSuccess && publishedUrl && (
           <PublishSuccessModal
             url={publishedUrl}
             onClose={() => setShowSuccess(false)}
           />
         )}
       </>
     );
   }
   ```

5. **Draft preview vs published preview**
   ```typescript
   // URL routing
   // /draft/{project_id} → Draft preview (requires auth)
   // /p/{public_id}      → Published preview (public)
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/models/project.py` | Project model with draft/published |
| `backend/app/api/projects.py` | CRUD + publish endpoints |
| `frontend/src/hooks/usePublish.ts` | Publish logic |
| `frontend/src/components/editor/PublishButton.tsx` | Publish UI |
| `frontend/src/components/editor/PublishSuccessModal.tsx` | Success + share |

---

### Task 3.4: Separate Origin Deployment

**Goal**: Serve published pages from `pages.zaoya.app` for security isolation

#### Sub-tasks

1. **Create published page server**
   ```python
   # backend/app/api/pages.py
   from fastapi import APIRouter, Response
   from fastapi.responses import HTMLResponse

   router = APIRouter()

   @router.get("/p/{public_id}")
   async def serve_published_page(public_id: str) -> HTMLResponse:
       project = await get_project_by_public_id(public_id)
       if not project or not project.published_version_id:
           raise HTTPException(status_code=404, detail="Page not found")

       version = await get_version(project.published_version_id)

       # Build full HTML document
       html = build_published_html(
           html_content=version.html,
           js_content=version.js,
           metadata=version.metadata,
       )

       return HTMLResponse(
           content=html,
           headers={
               "Content-Security-Policy": CSP_HEADER,
               "X-Frame-Options": "DENY",
               "X-Content-Type-Options": "nosniff",
           }
       )

   def build_published_html(html_content: str, js_content: str | None, metadata: dict) -> str:
       return f"""<!DOCTYPE html>
   <html lang="en">
   <head>
       <meta charset="UTF-8">
       <meta name="viewport" content="width=device-width, initial-scale=1.0">
       <title>{metadata.get('title', 'Zaoya Page')}</title>
       <meta name="description" content="{metadata.get('description', '')}">

       <!-- Open Graph -->
       <meta property="og:title" content="{metadata.get('title', '')}">
       <meta property="og:description" content="{metadata.get('description', '')}">
       <meta property="og:image" content="{metadata.get('ogImage', '')}">

       <!-- Tailwind CDN -->
       <script src="https://cdn.tailwindcss.com"></script>

       <!-- Zaoya Runtime -->
       <script src="https://zaoya.app/zaoya-runtime.js"></script>
   </head>
   <body>
       {html_content}
       {f'<script>{js_content}</script>' if js_content else ''}

       <!-- Analytics -->
       <script>
           Zaoya.track('page_view', {{ publicId: '{metadata.get("publicId")}' }});
       </script>
   </body>
   </html>"""

   CSP_HEADER = "; ".join([
       "default-src 'none'",
       "img-src 'self' data: blob: https:",
       "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com",
       "script-src 'self' https://zaoya.app",
       "connect-src https://api.zaoya.app",
       "frame-ancestors 'none'",
   ])
   ```

2. **Configure separate domain routing**
   ```python
   # backend/app/main.py
   from fastapi import FastAPI, Request

   app = FastAPI()

   @app.middleware("http")
   async def route_by_domain(request: Request, call_next):
       host = request.headers.get("host", "")

       if host.startswith("pages."):
           # Route to pages router
           request.scope["app"] = pages_app
       else:
           # Route to main app
           request.scope["app"] = main_app

       return await call_next(request)
   ```

3. **Nginx configuration (production)**
   ```nginx
   # zaoya.app - Main application
   server {
       listen 443 ssl;
       server_name zaoya.app www.zaoya.app;

       location / {
           proxy_pass http://localhost:3000;  # Frontend
       }

       location /api {
           proxy_pass http://localhost:8000;  # Backend
       }
   }

   # pages.zaoya.app - Published pages (isolated)
   server {
       listen 443 ssl;
       server_name pages.zaoya.app;

       # No cookies from main domain
       add_header Set-Cookie "";

       location /p/ {
           proxy_pass http://localhost:8000;  # Pages endpoint
       }

       location /zaoya-runtime.js {
           proxy_pass http://localhost:8000/static/zaoya-runtime.js;
           add_header Cache-Control "public, max-age=31536000";
       }
   }
   ```

4. **Development proxy setup**
   ```typescript
   // frontend/vite.config.ts
   export default defineConfig({
     server: {
       proxy: {
         '/api': 'http://localhost:8000',
         '/p': 'http://localhost:8000',  // Simulate pages domain in dev
       },
     },
   });
   ```

5. **Runtime script hosting**
   ```python
   # backend/app/api/static.py
   from fastapi import APIRouter
   from fastapi.responses import FileResponse

   router = APIRouter()

   @router.get("/zaoya-runtime.js")
   async def serve_runtime():
       return FileResponse(
           "static/zaoya-runtime.js",
           media_type="application/javascript",
           headers={
               "Cache-Control": "public, max-age=31536000",
               "Access-Control-Allow-Origin": "https://pages.zaoya.app",
           }
       )
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/api/pages.py` | Published page serving |
| `backend/app/api/static.py` | Static file serving |
| `nginx/zaoya.conf` | Production nginx config |

---

### Task 3.5: Shareable Links (`/p/{id}`)

**Goal**: Clean, memorable URLs for published pages

#### Sub-tasks

1. **Public ID generation**
   ```python
   # backend/app/utils/ids.py
   import secrets
   import string

   def generate_public_id(length: int = 8) -> str:
       """Generate a URL-safe, memorable ID."""
       # Use alphanumeric without confusing chars (0/O, 1/l/I)
       alphabet = string.ascii_lowercase + string.digits
       alphabet = alphabet.replace('0', '').replace('o', '').replace('l', '').replace('1', '')

       return ''.join(secrets.choice(alphabet) for _ in range(length))

   # Examples: k7nm3xvp, a9bcd2ef
   ```

2. **Share UI component**
   ```tsx
   // frontend/src/components/share/SharePanel.tsx
   interface SharePanelProps {
     url: string;
     title: string;
   }

   export function SharePanel({ url, title }: SharePanelProps) {
     const [copied, setCopied] = useState(false);

     const copyToClipboard = async () => {
       await navigator.clipboard.writeText(url);
       setCopied(true);
       setTimeout(() => setCopied(false), 2000);
     };

     const shareOptions = [
       {
         name: 'Copy link',
         icon: '🔗',
         action: copyToClipboard,
       },
       {
         name: 'WhatsApp',
         icon: '💬',
         action: () => window.open(`https://wa.me/?text=${encodeURIComponent(url)}`),
       },
       {
         name: 'Twitter',
         icon: '🐦',
         action: () => window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`),
       },
       {
         name: 'WeChat',
         icon: '📱',
         action: () => setShowQR(true),
       },
     ];

     return (
       <div className="space-y-4">
         <div className="flex items-center gap-2">
           <input
             type="text"
             value={url}
             readOnly
             className="flex-1 p-2 border rounded bg-gray-50"
           />
           <button
             onClick={copyToClipboard}
             className="px-4 py-2 bg-blue-600 text-white rounded"
           >
             {copied ? 'Copied!' : 'Copy'}
           </button>
         </div>

         <div className="flex gap-3">
           {shareOptions.map((option) => (
             <button
               key={option.name}
               onClick={option.action}
               className="flex flex-col items-center p-3 border rounded hover:bg-gray-50"
             >
               <span className="text-2xl">{option.icon}</span>
               <span className="text-xs mt-1">{option.name}</span>
             </button>
           ))}
         </div>
       </div>
     );
   }
   ```

3. **QR code generation**
   ```typescript
   // frontend/src/components/share/QRCode.tsx
   import QRCode from 'qrcode.react';

   export function QRCodeDisplay({ url }: { url: string }) {
     return (
       <div className="flex flex-col items-center p-6">
         <QRCode value={url} size={200} />
         <p className="mt-4 text-sm text-gray-500">
           Scan to open on mobile
         </p>
       </div>
     );
   }
   ```

4. **Open Graph metadata**
   ```python
   # backend/app/services/og_service.py
   def generate_og_metadata(project: Project, version: Version) -> dict:
       return {
           "title": project.name,
           "description": extract_description(version.html),
           "ogImage": generate_og_image(project, version),  # Future: screenshot service
       }

   def extract_description(html: str) -> str:
       """Extract first meaningful text from HTML."""
       from bs4 import BeautifulSoup
       soup = BeautifulSoup(html, 'html.parser')

       # Try meta description first
       meta = soup.find('meta', attrs={'name': 'description'})
       if meta and meta.get('content'):
           return meta['content'][:160]

       # Fall back to first paragraph
       p = soup.find('p')
       if p:
           return p.get_text()[:160]

       return "Created with Zaoya"
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `backend/app/utils/ids.py` | Public ID generation |
| `frontend/src/components/share/SharePanel.tsx` | Share options UI |
| `frontend/src/components/share/QRCode.tsx` | QR code display |
| `backend/app/services/og_service.py` | Open Graph metadata |

---

## Technical Considerations

### Key Dependencies (Phase 3 additions)

| Package | Version | Purpose |
|---------|---------|---------|
| `python-jose` | ^3.3 | JWT handling |
| `passlib` | ^1.7 | Password hashing |
| `google-auth` | ^2.0 | Google OAuth |
| `@react-oauth/google` | ^0.12 | Google sign-in button |
| `qrcode.react` | ^3.1 | QR code generation |
| `beautifulsoup4` | ^4.12 | HTML parsing for OG |

### Architecture Decisions

1. **Why JWT over sessions?**
   - Stateless, scales horizontally
   - Works well with SPA architecture
   - Easy to share across domains

2. **Why separate origin?**
   - User content can't access main app cookies
   - CSP isolation
   - Clear security boundary

3. **Why public ID over slug?**
   - No collision with usernames (v1 feature)
   - Simple to generate
   - Works without auth

---

## Acceptance Criteria

- [ ] Users can sign up/in with Google
- [ ] Users can sign up/in with email/password
- [ ] Guest projects stored in localStorage
- [ ] Guest users prompted to sign in when publishing
- [ ] Projects have separate draft and published versions
- [ ] Publish creates immutable snapshot
- [ ] Published pages served from pages.zaoya.app
- [ ] Published pages have correct CSP headers
- [ ] Share panel shows URL, copy, social options
- [ ] QR code generated for mobile sharing
- [ ] Open Graph meta tags present on published pages

---

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Google OAuth setup complexity | Medium | Medium | Use established library, test thoroughly |
| CORS issues with separate origin | High | Medium | Configure correctly from start |
| Guest project data loss | Medium | High | Clear warning before conversion |
| DNS/SSL for pages subdomain | Low | High | Set up early, test in staging |

---

## Estimated Effort

| Task | Complexity | Effort |
|------|------------|--------|
| 3.1 User Authentication | Large | 4-5 days |
| 3.2 Guest Conversion | Medium | 2-3 days |
| 3.3 Draft vs Published | Medium | 2-3 days |
| 3.4 Separate Origin | Medium | 2-3 days |
| 3.5 Shareable Links | Small | 1-2 days |
| **Testing & Polish** | - | 2-3 days |
| **Total** | **Medium** | **13-19 days (2-3 weeks)** |

---

## Definition of Done

Phase 3 is complete when:
1. Full auth flow works (Google + email)
2. Guest projects convert to user projects
3. Publishing creates shareable link
4. Published pages serve from separate origin
5. Security headers properly configured
6. Share options work (copy, social, QR)
7. No regression in Phase 1-2 functionality
