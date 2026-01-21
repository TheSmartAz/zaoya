# Phase 2: Core Loop (v0)

**Duration**: Weeks 4-6
**Status**: Pending
**Complexity**: Large

---

## Overview

Phase 2 transforms the basic chat-to-preview into the full "vibe coding" experience. Users select templates, answer adaptive questions, and refine pages with quick action chips. This phase implements the core product loop that makes Zaoya unique.

### Connection to Project Goals

- Implements the signature "Template → Interview → Generate → Refine" flow
- Reduces conversation turns needed (target: < 3 turns)
- Achieves > 70% first-generation acceptance rate
- Adds security layer (sanitization + validation)
- Enables version history for safe iteration

---

## Prerequisites

- [ ] Phase 1 complete (chat + preview working)
- [ ] AI consistently generates valid HTML
- [ ] Streaming chat stable
- [ ] Basic project structure in place

---

## Detailed Tasks

### Task 2.1: Template System (4 Categories)

**Goal**: Users start by selecting a template category that guides AI generation

#### Sub-tasks

1. **Create template data structure**
   ```typescript
   // frontend/src/types/template.ts
   interface Template {
     id: string;
     category: 'profile' | 'event' | 'product' | 'form';
     name: string;
     description: string;
     icon: string;
     exampleImage: string;
     requiredInputs: TemplateInput[];
     optionalInputs: TemplateInput[];
     systemPromptAddition: string;
   }

   interface TemplateInput {
     id: string;
     label: string;
     type: 'text' | 'textarea' | 'date' | 'url' | 'email' | 'image';
     placeholder: string;
     required: boolean;
   }
   ```

2. **Define template configurations**
   ```typescript
   // frontend/src/data/templates.ts
   export const templates: Template[] = [
     {
       id: 'profile',
       category: 'profile',
       name: 'Personal Profile',
       description: 'Link-in-bio, portfolio, about-me page',
       icon: '👤',
       requiredInputs: [
         { id: 'name', label: 'Your Name', type: 'text', placeholder: 'John Doe', required: true },
         { id: 'bio', label: 'Short Bio', type: 'textarea', placeholder: 'Tell us about yourself...', required: true },
       ],
       optionalInputs: [
         { id: 'photo', label: 'Profile Photo', type: 'image', placeholder: '', required: false },
         { id: 'links', label: 'Social Links', type: 'textarea', placeholder: 'One per line...', required: false },
       ],
       systemPromptAddition: 'Generate a modern link-in-bio style profile page...',
     },
     {
       id: 'event',
       category: 'event',
       name: 'Event Invitation',
       description: 'Birthday, wedding, party RSVP',
       icon: '🎉',
       requiredInputs: [
         { id: 'eventName', label: 'Event Name', type: 'text', placeholder: "Sarah's Birthday Party", required: true },
         { id: 'date', label: 'Date & Time', type: 'text', placeholder: 'Saturday, March 15 at 7PM', required: true },
         { id: 'location', label: 'Location', type: 'text', placeholder: '123 Party Street', required: true },
       ],
       optionalInputs: [
         { id: 'rsvpDeadline', label: 'RSVP Deadline', type: 'date', placeholder: '', required: false },
         { id: 'details', label: 'Additional Details', type: 'textarea', placeholder: 'Dress code, parking info...', required: false },
       ],
       systemPromptAddition: 'Generate a festive event invitation page with RSVP form...',
     },
     {
       id: 'product',
       category: 'product',
       name: 'Product Landing',
       description: 'Showcase, launch page, pricing',
       icon: '🚀',
       requiredInputs: [
         { id: 'productName', label: 'Product Name', type: 'text', placeholder: 'SuperApp', required: true },
         { id: 'tagline', label: 'Tagline', type: 'text', placeholder: 'The best app ever', required: true },
         { id: 'cta', label: 'Call to Action', type: 'text', placeholder: 'Get Started Free', required: true },
       ],
       optionalInputs: [
         { id: 'features', label: 'Key Features', type: 'textarea', placeholder: 'One feature per line...', required: false },
         { id: 'price', label: 'Price', type: 'text', placeholder: '$9.99/month', required: false },
       ],
       systemPromptAddition: 'Generate a modern SaaS-style product landing page...',
     },
     {
       id: 'form',
       category: 'form',
       name: 'Contact/Lead Form',
       description: 'Contact, signup, survey',
       icon: '📝',
       requiredInputs: [
         { id: 'formTitle', label: 'Form Title', type: 'text', placeholder: 'Contact Us', required: true },
         { id: 'fields', label: 'Form Fields', type: 'textarea', placeholder: 'Name, Email, Message...', required: true },
       ],
       optionalInputs: [
         { id: 'successMessage', label: 'Success Message', type: 'text', placeholder: 'Thanks for reaching out!', required: false },
         { id: 'notifyEmail', label: 'Notification Email', type: 'email', placeholder: 'you@example.com', required: false },
       ],
       systemPromptAddition: 'Generate a clean form page that collects user information...',
     },
   ];
   ```

3. **Create template selection page**
   ```
   frontend/src/pages/CreatePage.tsx
   frontend/src/components/create/
   ├── TemplateGrid.tsx         # Grid of template cards
   ├── TemplateCard.tsx         # Individual template option
   └── TemplateInputForm.tsx    # Structured inputs after selection
   ```

4. **Build template selection UI**
   ```tsx
   // frontend/src/pages/CreatePage.tsx
   export function CreatePage() {
     const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
     const [templateInputs, setTemplateInputs] = useState<Record<string, string>>({});
     const navigate = useNavigate();

     const handleStartProject = () => {
       // Create project with template + inputs
       const projectId = createProject(selectedTemplate, templateInputs);
       navigate(`/editor/${projectId}`);
     };

     return (
       <div className="container mx-auto p-6">
         {!selectedTemplate ? (
           <TemplateGrid
             templates={templates}
             onSelect={setSelectedTemplate}
           />
         ) : (
           <TemplateInputForm
             template={selectedTemplate}
             values={templateInputs}
             onChange={setTemplateInputs}
             onBack={() => setSelectedTemplate(null)}
             onStart={handleStartProject}
           />
         )}
       </div>
     );
   }
   ```

5. **Inject template context into AI prompt**
   ```python
   # backend/app/services/prompt_builder.py
   def build_system_prompt(template: dict, inputs: dict) -> str:
       base_prompt = SYSTEM_PROMPT
       template_context = f"""
       Template: {template['name']}
       {template['systemPromptAddition']}

       User provided information:
       {format_inputs(inputs)}

       Generate a complete mobile page using this information.
       """
       return base_prompt + template_context
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/types/template.ts` | Template type definitions |
| `frontend/src/data/templates.ts` | Template configurations |
| `frontend/src/pages/CreatePage.tsx` | Template selection page |
| `frontend/src/components/create/TemplateGrid.tsx` | Template grid display |
| `frontend/src/components/create/TemplateCard.tsx` | Individual template card |
| `frontend/src/components/create/TemplateInputForm.tsx` | Input collection form |
| `backend/app/services/prompt_builder.py` | System prompt construction |

---

### Task 2.2: Adaptive Interview Questions

**Goal**: AI asks smart follow-up questions before generating to improve first-gen quality

#### Sub-tasks

1. **Define interview question strategy**
   ```typescript
   // frontend/src/types/interview.ts
   interface InterviewQuestion {
     id: string;
     question: string;
     type: 'single' | 'multi' | 'text' | 'skip';
     options?: string[];
     skipLabel?: string;  // "Not sure—choose for me"
   }

   interface InterviewState {
     knownFacts: Record<string, string>;
     questionsAsked: string[];
     questionsRemaining: number;  // max 6
   }
   ```

2. **Create interview prompt for AI**
   ```python
   INTERVIEW_PROMPT = """Based on the user's template choice and inputs, identify what CRITICAL information is missing for a great first generation.

   Already known:
   {known_facts}

   Ask 1-3 focused questions about:
   1. Primary goal/CTA (if unclear)
   2. Tone/vibe (professional, playful, minimal, bold)
   3. Visual preference (color scheme, style)
   4. Any missing key content

   Format your response as:
   QUESTIONS:
   1. [Question text] | OPTIONS: [opt1, opt2, opt3] | SKIP: [skip option text]
   2. ...

   Or if you have enough information:
   READY_TO_GENERATE: true
   """
   ```

3. **Build interview UI component**
   ```tsx
   // frontend/src/components/chat/InterviewQuestion.tsx
   interface InterviewQuestionProps {
     question: InterviewQuestion;
     onAnswer: (answer: string) => void;
     onSkip: () => void;
   }

   export function InterviewQuestion({
     question,
     onAnswer,
     onSkip,
   }: InterviewQuestionProps) {
     return (
       <div className="space-y-3">
         <p className="text-gray-800">{question.question}</p>

         {question.options && (
           <div className="flex flex-wrap gap-2">
             {question.options.map((option) => (
               <button
                 key={option}
                 onClick={() => onAnswer(option)}
                 className="px-4 py-2 bg-blue-100 rounded-full hover:bg-blue-200"
               >
                 {option}
               </button>
             ))}
           </div>
         )}

         {question.type === 'text' && (
           <input
             type="text"
             onKeyDown={(e) => e.key === 'Enter' && onAnswer(e.currentTarget.value)}
             className="w-full p-2 border rounded"
             placeholder="Type your answer..."
           />
         )}

         <button
           onClick={onSkip}
           className="text-gray-500 text-sm underline"
         >
           {question.skipLabel || "Not sure—choose for me"}
         </button>
       </div>
     );
   }
   ```

4. **Implement interview flow in chat**
   ```typescript
   // frontend/src/hooks/useInterview.ts
   export function useInterview(template: Template, inputs: Record<string, string>) {
     const [state, setState] = useState<InterviewState>({
       knownFacts: inputs,
       questionsAsked: [],
       questionsRemaining: 6,
     });

     const [currentQuestions, setCurrentQuestions] = useState<InterviewQuestion[]>([]);
     const [isReady, setIsReady] = useState(false);

     const fetchQuestions = async () => {
       const response = await fetch('/api/interview', {
         method: 'POST',
         body: JSON.stringify({
           template,
           knownFacts: state.knownFacts,
           questionsAsked: state.questionsAsked,
         }),
       });

       const data = await response.json();

       if (data.readyToGenerate) {
         setIsReady(true);
       } else {
         setCurrentQuestions(data.questions);
       }
     };

     const answerQuestion = (questionId: string, answer: string) => {
       setState((prev) => ({
         ...prev,
         knownFacts: { ...prev.knownFacts, [questionId]: answer },
         questionsAsked: [...prev.questionsAsked, questionId],
         questionsRemaining: prev.questionsRemaining - 1,
       }));
     };

     return {
       currentQuestions,
       isReady,
       knownFacts: state.knownFacts,
       answerQuestion,
       fetchQuestions,
     };
   }
   ```

5. **Add interview API endpoint**
   ```python
   # backend/app/api/interview.py
   @router.post("/interview")
   async def get_interview_questions(request: InterviewRequest):
       questions = await ai_service.generate_interview(
           template=request.template,
           known_facts=request.known_facts,
           questions_asked=request.questions_asked,
       )

       return InterviewResponse(
           ready_to_generate=questions is None,
           questions=questions or [],
       )
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/types/interview.ts` | Interview type definitions |
| `frontend/src/hooks/useInterview.ts` | Interview state management |
| `frontend/src/components/chat/InterviewQuestion.tsx` | Question display + answer |
| `backend/app/api/interview.py` | Interview endpoint |

---

### Task 2.3: Quick Action Chips

**Goal**: Pre-built refinement prompts that reduce friction in iteration

#### Sub-tasks

1. **Define quick action data structure**
   ```typescript
   // frontend/src/types/quickAction.ts
   interface QuickAction {
     id: string;
     label: string;
     prompt: string;
     icon?: string;
     category: 'style' | 'content' | 'structure';
     templates?: string[];  // If empty, show for all templates
   }
   ```

2. **Create quick action configurations**
   ```typescript
   // frontend/src/data/quickActions.ts
   export const universalActions: QuickAction[] = [
     {
       id: 'more-premium',
       label: 'More premium',
       prompt: 'Make the design more premium and sophisticated. Use more whitespace, refined typography, and subtle shadows.',
       icon: '✨',
       category: 'style',
     },
     {
       id: 'more-playful',
       label: 'More playful',
       prompt: 'Make the design more playful and fun. Add some personality, brighter colors, and friendly elements.',
       icon: '🎨',
       category: 'style',
     },
     {
       id: 'shorten-copy',
       label: 'Shorten copy',
       prompt: 'Make all text more concise. Remove filler words and keep only essential information.',
       icon: '✂️',
       category: 'content',
     },
     {
       id: 'more-detail',
       label: 'More detail',
       prompt: 'Expand the content with more details and explanations. Add supporting text where helpful.',
       icon: '📝',
       category: 'content',
     },
     {
       id: 'change-color',
       label: 'Change colors',
       prompt: 'Suggest a new color scheme. What vibe are you going for? (I will offer options)',
       icon: '🎨',
       category: 'style',
     },
     {
       id: 'add-faq',
       label: 'Add FAQ',
       prompt: 'Add a Frequently Asked Questions section with 3-5 relevant questions and answers.',
       icon: '❓',
       category: 'structure',
     },
     {
       id: 'add-testimonials',
       label: 'Add testimonials',
       prompt: 'Add a testimonials section with 2-3 sample testimonials. I will provide real ones later.',
       icon: '💬',
       category: 'structure',
     },
     {
       id: 'adjust-cta',
       label: 'Adjust CTA',
       prompt: 'Improve the call-to-action. Make it more compelling, visible, or change the text.',
       icon: '🎯',
       category: 'content',
     },
   ];

   export const contextualActions: Record<string, QuickAction[]> = {
     event: [
       {
         id: 'add-rsvp',
         label: 'Add RSVP form',
         prompt: 'Add an RSVP form where guests can confirm attendance. Include name, email, and number of guests.',
         icon: '📋',
         category: 'structure',
       },
       {
         id: 'add-countdown',
         label: 'Add countdown',
         prompt: 'Add a countdown timer showing days/hours until the event date.',
         icon: '⏰',
         category: 'structure',
       },
     ],
     product: [
       {
         id: 'add-pricing',
         label: 'Add pricing table',
         prompt: 'Add a pricing table section. What pricing tiers do you have?',
         icon: '💰',
         category: 'structure',
       },
       {
         id: 'add-countdown',
         label: 'Add launch countdown',
         prompt: 'Add a countdown timer for the product launch.',
         icon: '⏰',
         category: 'structure',
       },
     ],
     profile: [
       {
         id: 'add-social',
         label: 'Add social links',
         prompt: 'Add social media links section. Which platforms should I include?',
         icon: '🔗',
         category: 'structure',
       },
     ],
     form: [
       {
         id: 'add-field',
         label: 'Add form field',
         prompt: 'What additional field should I add to the form?',
         icon: '➕',
         category: 'structure',
       },
     ],
   };
   ```

3. **Build quick action chips UI**
   ```tsx
   // frontend/src/components/chat/QuickActions.tsx
   interface QuickActionsProps {
     template: string;
     onAction: (action: QuickAction) => void;
     disabled?: boolean;
   }

   export function QuickActions({ template, onAction, disabled }: QuickActionsProps) {
     const contextual = contextualActions[template] || [];
     const allActions = [...contextual, ...universalActions];

     return (
       <div className="p-3 border-t bg-gray-50">
         <p className="text-xs text-gray-500 mb-2">Quick actions:</p>
         <div className="flex flex-wrap gap-2">
           {allActions.map((action) => (
             <button
               key={action.id}
               onClick={() => onAction(action)}
               disabled={disabled}
               className="px-3 py-1.5 text-sm bg-white border rounded-full
                          hover:bg-blue-50 hover:border-blue-300
                          disabled:opacity-50 disabled:cursor-not-allowed
                          transition-colors"
             >
               {action.icon && <span className="mr-1">{action.icon}</span>}
               {action.label}
             </button>
           ))}
         </div>
       </div>
     );
   }
   ```

4. **Integrate into chat flow**
   ```tsx
   // In ChatPanel.tsx
   const handleQuickAction = (action: QuickAction) => {
     // Add as user message
     addMessage({
       role: 'user',
       content: action.prompt,
       isQuickAction: true,
     });

     // Trigger AI response
     sendMessage([...messages, { role: 'user', content: action.prompt }]);
   };
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/types/quickAction.ts` | Quick action types |
| `frontend/src/data/quickActions.ts` | Quick action definitions |
| `frontend/src/components/chat/QuickActions.tsx` | Chips UI component |

---

### Task 2.4: Version History + Restore

**Goal**: Track every generation as a snapshot; allow reverting

#### Sub-tasks

1. **Define version data structure**
   ```typescript
   // frontend/src/types/version.ts
   interface Version {
     id: string;
     projectId: string;
     number: number;
     html: string;
     js: string | null;
     metadata: {
       prompt: string;       // What triggered this version
       timestamp: number;
       changeType: 'initial' | 'refinement' | 'quick_action' | 'restore';
     };
   }

   interface VersionDiff {
     additions: string[];
     removals: string[];
     summary: string;  // AI-generated summary
   }
   ```

2. **Create version store**
   ```typescript
   // frontend/src/stores/versionStore.ts
   interface VersionState {
     versions: Version[];
     currentVersionId: string | null;

     addVersion: (version: Omit<Version, 'id' | 'number'>) => void;
     restoreVersion: (versionId: string) => void;
     getCurrentVersion: () => Version | null;
     getVersionHistory: () => Version[];
   }

   export const useVersionStore = create<VersionState>((set, get) => ({
     versions: [],
     currentVersionId: null,

     addVersion: (version) => {
       const newVersion: Version = {
         ...version,
         id: generateId(),
         number: get().versions.length + 1,
       };
       set((state) => ({
         versions: [...state.versions, newVersion],
         currentVersionId: newVersion.id,
       }));
     },

     restoreVersion: (versionId) => {
       const version = get().versions.find((v) => v.id === versionId);
       if (version) {
         // Create a new version marked as restore
         get().addVersion({
           projectId: version.projectId,
           html: version.html,
           js: version.js,
           metadata: {
             prompt: `Restored from version ${version.number}`,
             timestamp: Date.now(),
             changeType: 'restore',
           },
         });
       }
     },

     getCurrentVersion: () => {
       const { versions, currentVersionId } = get();
       return versions.find((v) => v.id === currentVersionId) || null;
     },

     getVersionHistory: () => get().versions,
   }));
   ```

3. **Build version history panel**
   ```tsx
   // frontend/src/components/version/VersionHistoryPanel.tsx
   export function VersionHistoryPanel() {
     const versions = useVersionStore((s) => s.getVersionHistory());
     const currentId = useVersionStore((s) => s.currentVersionId);
     const restoreVersion = useVersionStore((s) => s.restoreVersion);

     return (
       <div className="h-full overflow-y-auto">
         <h3 className="p-3 font-semibold border-b">Version History</h3>
         <div className="divide-y">
           {versions.slice().reverse().map((version) => (
             <VersionItem
               key={version.id}
               version={version}
               isCurrent={version.id === currentId}
               onRestore={() => restoreVersion(version.id)}
             />
           ))}
         </div>
       </div>
     );
   }

   function VersionItem({ version, isCurrent, onRestore }: {
     version: Version;
     isCurrent: boolean;
     onRestore: () => void;
   }) {
     return (
       <div className={`p-3 ${isCurrent ? 'bg-blue-50' : ''}`}>
         <div className="flex justify-between items-center">
           <div>
             <span className="font-medium">v{version.number}</span>
             <span className="text-xs text-gray-500 ml-2">
               {formatTime(version.metadata.timestamp)}
             </span>
           </div>
           {!isCurrent && (
             <button
               onClick={onRestore}
               className="text-sm text-blue-600 hover:underline"
             >
               Restore
             </button>
           )}
         </div>
         <p className="text-sm text-gray-600 truncate mt-1">
           {version.metadata.prompt}
         </p>
         <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">
           {version.metadata.changeType}
         </span>
       </div>
     );
   }
   ```

4. **Add version creation on each generation**
   ```typescript
   // In chat handler
   const handleGenerationComplete = (html: string, js: string | null, prompt: string) => {
     addVersion({
       projectId: currentProject.id,
       html,
       js,
       metadata: {
         prompt,
         timestamp: Date.now(),
         changeType: isQuickAction ? 'quick_action' : 'refinement',
       },
     });
   };
   ```

5. **Backend version storage**
   ```python
   # backend/app/models/version.py
   from sqlalchemy import Column, String, Integer, Text, JSON
   from app.database import Base

   class Version(Base):
       __tablename__ = "versions"

       id = Column(String, primary_key=True)
       project_id = Column(String, index=True)
       number = Column(Integer)
       html = Column(Text)
       js = Column(Text, nullable=True)
       metadata = Column(JSON)
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/types/version.ts` | Version type definitions |
| `frontend/src/stores/versionStore.ts` | Version state management |
| `frontend/src/components/version/VersionHistoryPanel.tsx` | History UI |
| `frontend/src/components/version/VersionItem.tsx` | Individual version display |
| `backend/app/models/version.py` | SQLAlchemy model |

---

### Task 2.5: HTML/JS Sanitization + Validation

**Goal**: Ensure generated code is safe to render and publish

#### Sub-tasks

1. **Install sanitization dependencies**
   ```bash
   # Frontend
   npm install dompurify @types/dompurify

   # Backend (for server-side validation)
   pip install bleach
   ```

2. **Create HTML sanitizer**
   ```typescript
   // frontend/src/utils/sanitizer.ts
   import DOMPurify from 'dompurify';

   const ALLOWED_TAGS = [
     'div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
     'a', 'img', 'ul', 'ol', 'li', 'button', 'form', 'input',
     'textarea', 'label', 'select', 'option', 'section', 'article',
     'header', 'footer', 'nav', 'main', 'aside', 'figure', 'figcaption',
     'table', 'thead', 'tbody', 'tr', 'th', 'td',
     'strong', 'em', 'br', 'hr',
   ];

   const ALLOWED_ATTR = [
     'class', 'id', 'href', 'src', 'alt', 'type', 'name', 'value',
     'placeholder', 'required', 'disabled', 'for', 'style',
     'data-*',  // Allow data attributes for Zaoya.* hooks
   ];

   export function sanitizeHTML(html: string): string {
     return DOMPurify.sanitize(html, {
       ALLOWED_TAGS,
       ALLOWED_ATTR,
       FORBID_TAGS: ['script', 'iframe', 'object', 'embed', 'style'],
       FORBID_ATTR: ['onclick', 'onerror', 'onload', 'onmouseover'],
       ALLOW_DATA_ATTR: true,
     });
   }
   ```

3. **Create JS validator using AST**
   ```typescript
   // frontend/src/utils/jsValidator.ts
   import * as acorn from 'acorn';
   import * as walk from 'acorn-walk';

   interface ValidationResult {
     valid: boolean;
     errors: string[];
   }

   const BLOCKED_GLOBALS = [
     'fetch', 'XMLHttpRequest', 'WebSocket',
     'localStorage', 'sessionStorage', 'indexedDB',
     'document.cookie',
     'window.top', 'window.parent', 'parent', 'top',
   ];

   const BLOCKED_PATTERNS = [
     /eval\s*\(/,
     /Function\s*\(/,
     /setTimeout\s*\(\s*['"`]/,
     /setInterval\s*\(\s*['"`]/,
   ];

   export function validateJS(code: string): ValidationResult {
     const errors: string[] = [];

     // Check blocked patterns
     for (const pattern of BLOCKED_PATTERNS) {
       if (pattern.test(code)) {
         errors.push(`Blocked pattern detected: ${pattern.source}`);
       }
     }

     // Parse and walk AST
     try {
       const ast = acorn.parse(code, { ecmaVersion: 2020 });

       walk.simple(ast, {
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
           // Ensure calls are to Zaoya.* or allowed DOM methods
           const callee = getCalleeName(node);
           if (!isAllowedCall(callee)) {
             errors.push(`Blocked call: ${callee}`);
           }
         },
       });
     } catch (e) {
       errors.push(`Parse error: ${e.message}`);
     }

     return {
       valid: errors.length === 0,
       errors,
     };
   }

   function isAllowedCall(callee: string): boolean {
     const allowed = [
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
     ];
     return allowed.some((a) => callee.startsWith(a) || callee === a);
   }
   ```

4. **Backend validation (double-check)**
   ```python
   # backend/app/services/validator.py
   import bleach
   import re

   ALLOWED_TAGS = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                   'a', 'img', 'ul', 'ol', 'li', 'button', 'form', 'input',
                   'textarea', 'label', 'select', 'option', 'section', 'article',
                   'header', 'footer', 'nav', 'main', 'table', 'tr', 'td', 'th']

   ALLOWED_ATTRS = {
       '*': ['class', 'id', 'style'],
       'a': ['href'],
       'img': ['src', 'alt'],
       'input': ['type', 'name', 'value', 'placeholder', 'required'],
       'form': ['data-form-id'],
   }

   def sanitize_html(html: str) -> str:
       return bleach.clean(
           html,
           tags=ALLOWED_TAGS,
           attributes=ALLOWED_ATTRS,
           strip=True,
       )

   BLOCKED_JS_PATTERNS = [
       r'eval\s*\(',
       r'Function\s*\(',
       r'fetch\s*\(',
       r'XMLHttpRequest',
       r'localStorage',
       r'sessionStorage',
       r'document\.cookie',
       r'window\.(top|parent)',
   ]

   def validate_js(code: str) -> tuple[bool, list[str]]:
       errors = []
       for pattern in BLOCKED_JS_PATTERNS:
           if re.search(pattern, code):
               errors.append(f"Blocked pattern: {pattern}")
       return len(errors) == 0, errors
   ```

5. **Integrate into rendering pipeline**
   ```typescript
   // frontend/src/utils/renderPipeline.ts
   export async function processGeneration(
     rawHtml: string,
     rawJs: string | null
   ): Promise<ProcessedCode | ValidationError> {
     // 1. Sanitize HTML
     const sanitizedHtml = sanitizeHTML(rawHtml);

     // 2. Validate JS (if present)
     if (rawJs) {
       const jsValidation = validateJS(rawJs);
       if (!jsValidation.valid) {
         return {
           type: 'error',
           errors: jsValidation.errors,
           suggestion: 'Regenerating with stricter constraints...',
         };
       }
     }

     // 3. Normalize (add viewport, etc.)
     const normalizedHtml = normalizeHTML(sanitizedHtml);

     return {
       type: 'success',
       html: normalizedHtml,
       js: rawJs,
     };
   }
   ```

#### Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/utils/sanitizer.ts` | HTML sanitization |
| `frontend/src/utils/jsValidator.ts` | JS AST validation |
| `frontend/src/utils/renderPipeline.ts` | Full processing pipeline |
| `backend/app/services/validator.py` | Server-side validation |

---

## Technical Considerations

### Key Dependencies (Phase 2 additions)

| Package | Version | Purpose |
|---------|---------|---------|
| `dompurify` | ^3.0 | HTML sanitization |
| `acorn` | ^8.11 | JS parser |
| `acorn-walk` | ^8.3 | AST traversal |
| `bleach` | ^6.1 | Server-side HTML sanitization |

### Architecture Decisions

1. **Why client-side + server-side validation?**
   - Client-side: Fast feedback, good UX
   - Server-side: Security guarantee, can't be bypassed
   - Defense in depth

2. **Why AST-based JS validation?**
   - Regex can be bypassed with obfuscation
   - AST catches semantic issues
   - Can evolve rules without rewriting parser

3. **Why store versions in both client and server?**
   - Client: Fast UI, works offline
   - Server: Persistence, cross-device access
   - Sync on publish or explicit save

---

## Acceptance Criteria

- [ ] User can select from 4 template categories
- [ ] Template inputs are collected before chat starts
- [ ] AI asks 2-6 adaptive questions before first generation
- [ ] Users can skip questions with "Not sure—choose for me"
- [ ] Quick action chips appear after first generation
- [ ] Clicking a chip sends the prompt and triggers generation
- [ ] Contextual chips show based on template type
- [ ] Every generation creates a version snapshot
- [ ] Version history panel shows all versions
- [ ] Clicking "Restore" reverts to that version
- [ ] HTML sanitization removes dangerous elements
- [ ] JS validation catches blocked patterns
- [ ] Invalid JS triggers regeneration request

---

## Risk Factors

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Interview questions too verbose | Medium | Medium | Cap at 6 questions, prioritize high-impact |
| Quick actions don't match user intent | Medium | Low | A/B test prompts, allow customization later |
| Sanitization too aggressive | Medium | High | Test with real generations, whitelist carefully |
| JS validation false positives | Medium | Medium | Build comprehensive test suite |
| Version history grows too large | Low | Medium | Implement pruning (keep last N) |

---

## Estimated Effort

| Task | Complexity | Effort |
|------|------------|--------|
| 2.1 Template System | Medium | 3-4 days |
| 2.2 Adaptive Interview | Large | 4-5 days |
| 2.3 Quick Action Chips | Small | 2 days |
| 2.4 Version History | Medium | 3-4 days |
| 2.5 Sanitization + Validation | Large | 4-5 days |
| **Testing & Polish** | - | 3-4 days |
| **Total** | **Large** | **19-24 days (3-4 weeks)** |

---

## Definition of Done

Phase 2 is complete when:
1. Template selection flow works end-to-end
2. AI interview improves first-generation quality
3. Quick actions reduce iteration friction
4. Version history enables safe experimentation
5. Security validation prevents dangerous code
6. All acceptance criteria pass
7. No regression in Phase 1 functionality
