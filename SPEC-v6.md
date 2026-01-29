# Zaoya (造鸭) - v6 Specification

> **"Streamlined Chat UX with Interview Widgets and Cleaner Interface."**

v6 focuses on improving the chat experience by removing code from the chat panel, eliminating fixed bottom cards, and transforming the interview flow into an elegant widget system.

---

## Vision

**North Star**: "A focused, conversational AI experience that guides users naturally from idea to published page."

v6 addresses key UX issues from v5:

- **Clean Chat Thread** - No code blocks in chat, all technical content moved to dedicated panels
- **No Fixed Cards** - Remove bottom-fixed cards that break the conversational flow
- **Interview Widget** - Transform questions into an elegant, progressive widget at the end of the chat thread
- **Collapsed History** - Answered questions collapse into compact Q&A pairs

---

## What Changed from v5

| v5 Feature | v6 Change | Rationale |
|------------|-----------|-----------|
| Code blocks in chat | **No code in chat** | Clean conversational experience |
| BuildPlanCard (fixed at bottom) | **Removed** | Cards should flow naturally in chat thread |
| InterviewCard (fixed at bottom) | **InterviewWidget** | Widget at end of thread, one question at a time |
| Questions always visible | **Collapse after answer** | Reduces clutter, shows conversation history |
| Multiple questions visible | **One question per widget** | Focused, less overwhelming |

---

## Part A: Chat Panel Cleanup

### A.1 No Code in Chat

**Removal**: Code blocks are completely filtered from chat messages.

```typescript
// MessageList.tsx
const renderMessageContent = (content: string) => {
  // Remove all code blocks (```html, ```css, ```javascript, etc.)
  const cleaned = content.replace(/```[\s\S]*?```/g, '[Code generated - view in Preview tab]')

  // If message only contains code, show brief summary instead
  if (cleaned.trim().length === 0) {
    return 'I\'ve updated the page. Check the Preview tab to see the changes.'
  }

  return cleaned
}
```

**Behavior**:
- AI responses containing only code: Show summary message instead
- AI responses with code + text: Show text only, code silently extracted
- Extracted HTML is automatically set to preview panel (existing behavior preserved)

### A.2 Remove Fixed Bottom Cards

**Removal**: These cards no longer appear at the bottom of ChatPanel:

- ~~BuildPlanCard~~ (moved to chat thread as a message item)
- ~~InterviewCard~~ (replaced by InterviewWidget)
- ~~TaskBoardCard~~ (moved to chat thread as a message item)

**Rationale**: Fixed cards break the conversational metaphor. Everything should flow naturally in the chat thread.

---

## Part B: InterviewWidget

### B.1 Widget Design

**Placement**: Always appears at the end of the chat thread, after all messages and cards.

**Behavior**:
- Shows only **one question at a time**
- After answering, the question collapses into a compact Q&A pair
- The next question appears in the widget
- When all questions are answered, the widget disappears

### B.2 Widget UI States

#### State 1: Active Question

```
┌─────────────────────────────────────────┐
│ Chat Thread                              │
│                                          │
│ [User] I want a portfolio page           │
│                                          │
│ [AI] Great! Let me ask some questions... │
│                                          │
│ ┌─────────────────────────────────────┐ │
│ │ 📋 Interview                        │ │
│ │ ─────────────────────────────────── │ │
│ │ What type of page?                  │ │
│ │ ○ Portfolio  ○ Landing Page         │ │
│ │ ○ Contact Form  ○ Other             │ │
│ │                                     │ │
│ │ [Skip]                              │ │
│ └─────────────────────────────────────┘ │ ← Current active question
└─────────────────────────────────────────┘
```

#### State 2: Collapsed Q&A + Next Question

```
┌─────────────────────────────────────────┐
│ Chat Thread                              │
│                                          │
│ [User] I want a portfolio page           │
│                                          │
│ [AI] Great! Let me ask some questions... │
│                                          │
│ What type of page? → Portfolio          │ │ ← Collapsed (simplified question, gray answer)
│                                          │
│ ┌─────────────────────────────────────┐ │
│ │ 📋 Interview                        │ │
│ │ ─────────────────────────────────── │ │
│ │ What's your name?                   │ │
│ │ [________________________]          │ │
│ │                                     │ │
│ │ [Skip]                              │ │
│ └─────────────────────────────────────┘ │ ← New active question
└─────────────────────────────────────────┘
```

#### State 3: Multiple Collapsed + Active

```
┌─────────────────────────────────────────┐
│ Chat Thread                              │
│                                          │
│ ...                                      │
│                                          │
│ What type of page? → Portfolio          │ │
│ What's your name? → John Doe             │ │
│ What's your role? → Software Engineer    │ │
│                                          │
│ ┌─────────────────────────────────────┐ │
│ │ 📋 Interview                        │ │
│ │ ─────────────────────────────────── │ │
│ │ Which design style?                 │ │
│ │ ○ Minimalist  ○ Modern              │ │
│ │ ○ Bold  ○ Elegant                   │ │
│ │                                     │ │
│ │ [Skip]                              │ │
│ └─────────────────────────────────────┘ │ ← Active question
└─────────────────────────────────────────┘
```

#### State 4: All Answered (Widget Disappears)

```
┌─────────────────────────────────────────┐
│ Chat Thread                              │
│                                          │
│ ...                                      │
│                                          │
│ What type of page? → Portfolio           │ │
│ What's your name? → John Doe             │ │
│ What's your role? → Software Engineer    │ │
│ Which design style? → Modern             │ │
│ Preferred color? → Blue                  │ │
│                                          │
│ [AI] Perfect! I'll generate your...      │ │ ← AI takes over
└─────────────────────────────────────────┘
```

### B.3 Collapsed Q&A Styling

```css
.interview-collapsed-qa {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  background: #f5f5f5;
  font-size: 14px;
}

.interview-question {
  color: #000000;
  font-weight: 500;
}

.interview-arrow {
  color: #999999;
}

.interview-answer {
  color: #999999;
  font-weight: 400;
}
```

**Visual Example**:
```
What type of page? → Portfolio
^^^^^^^^^^^^^^^^^^^   ^^^^^^^^^
   (black bold)          (gray)
```

### B.4 Question Types

The widget supports all interview question types:

| Type | Widget UI | Answer Format |
|------|-----------|---------------|
| **single_select** | Radio buttons | Selected option (gray) |
| **multi_select** | Checkboxes | Selected options (comma-separated, gray) |
| **text** | Text input | User input (gray) |
| **date** | Date picker | Formatted date (gray) |

### B.5 Skip Behavior

When user clicks **Skip**:
- Question collapses with answer: "Skipped"
- Widget moves to next question
- Backend receives `selected_options: ['skip']` (existing behavior preserved)

**Example**:
```
What's your website URL? → Skipped
```

---

## Part C: BuildPlanCard Relocation

### C.1 New Placement

**v5 Behavior**: BuildPlanCard fixed at bottom of ChatPanel

**v6 Behavior**: BuildPlanCard appears as a **message item** in the chat thread

```
┌─────────────────────────────────────────┐
│ Chat Thread                              │
│                                          │
│ [User] I want a portfolio page           │
│                                          │
│ [AI] Great! Let me ask some questions... │
│                                          │
│ What type of page? → Portfolio          │ │
│ What's your name? → John Doe             │ │
│                                          │
│ ┌─────────────────────────────────────┐ │
│ │ 📋 Build Plan                      │ │
│ │ ─────────────────────────────────── │ │
│ │ Pages: Home, About, Contact         │ │
│ │ Style: Modern                       │ │
│ │ Color: Blue                         │ │
│ │                                     │ │
│ │ [Generate] [Edit]                   │ │
│ └─────────────────────────────────────┘ │ ← Message item in thread
└─────────────────────────────────────────┘
```

### C.2 Auto-Scroll to BuildPlan

When BuildPlanCard appears:
- Auto-scroll to make it visible
- Add highlight animation for 2 seconds
- Focus on the card for user attention

---

## Part D: Data Model Changes

### D.1 New Component: InterviewWidget

```typescript
// frontend/src/components/chat/InterviewWidget.tsx

interface InterviewQuestion {
  id: string
  text: string
  type: 'single_select' | 'multi_select' | 'text' | 'date'
  options?: Array<{ value: string; label: string; description?: string }>
}

interface CollapsedAnswer {
  questionId: string
  questionText: string  // Simplified version
  answer: string  // User's answer (or "Skipped")
}

interface InterviewWidgetProps {
  currentQuestion: InterviewQuestion | null
  collapsedAnswers: CollapsedAnswer[]
  onAnswer: (questionId: string, value: string | string[]) => void
  onSkip: (questionId: string) => void
  isLoading?: boolean
}
```

### D.2 State Management (chatStore Extension)

```typescript
// frontend/src/stores/chatStore.ts

interface ChatStore {
  // ... existing fields ...

  // New fields for interview widget
  interviewCollapsedAnswers: Array<{
    questionId: string
    questionText: string
    answer: string
  }>

  // New actions
  addCollapsedAnswer: (questionId: string, questionText: string, answer: string) => void
  clearCollapsedAnswers: () => void
}
```

---

## Part E: Migration from v5 InterviewCard

### E.1 Behavior Mapping

| v5 InterviewCard | v6 InterviewWidget |
|------------------|-------------------|
| Shows question group with multiple questions | Shows one question at a time |
| Fixed at bottom of ChatPanel | Flows at end of chat thread |
| Question progress (1/3) | Progress shown via collapsed Q&A list |
| Always expanded until group complete | Collapses after each answer |
| Answer/Skip/Generate Now buttons | Answer/Skip buttons (Generate moved to BuildPlanCard) |

### E.2 Backend Compatibility

**No backend changes required**. The widget uses existing interview API:

```
POST /api/projects/{id}/chat
{
  "action": "answer",
  "answers": [...]
}
```

The widget simply changes how questions are presented, not how data is submitted.

---

## Part F: Implementation Checklist

### Frontend Changes

- [ ] Create `InterviewWidget.tsx` component
- [ ] Update `MessageList.tsx` to filter code blocks
- [ ] Remove `InterviewCard` from bottom of ChatPanel
- [ ] Remove `BuildPlanCard` from bottom of ChatPanel
- [ ] Move `BuildPlanCard` to appear as message item in thread
- [ ] Add collapsed answer state to `chatStore`
- [ ] Implement collapse animation (using Framer Motion or CSS transitions)
- [ ] Update auto-scroll behavior for new widget
- [ ] Test all question types (single/multi select, text, date)

### Backend Changes

- [ ] **None** - This is a pure UX improvement

### Documentation

- [ ] Update SPEC-v6 with final implementation details
- [ ] Add component storybook docs for InterviewWidget
- [ ] Update user-facing help text

---

## Part G: Acceptance Criteria

### G.1 Chat Panel Cleanup

- [ ] Code blocks are completely hidden from chat messages
- [ ] Messages with only code show summary text
- [ ] No fixed cards at the bottom of ChatPanel
- [ ] All cards flow naturally in chat thread

### G.2 InterviewWidget

- [ ] Widget appears at end of chat thread
- [ ] Only one question visible at a time
- [ ] After answering, question collapses to compact Q&A pair
- [ ] Collapsed format: "Question → Answer"
- [ ] Collapsed question is black, answer is gray
- [ ] All question types work (select, multi, text, date)
- [ ] Skip button works and shows "Skipped"
- [ ] Widget disappears when all questions answered
- [ ] Collapsed answers persist in chat history

### G.3 BuildPlanCard

- [ ] BuildPlanCard appears as message item in thread
- [ ] Auto-scrolls to BuildPlanCard when it appears
- [ ] BuildPlanCard has highlight animation on appear

### G.4 Overall UX

- [ ] Chat thread feels conversational and focused
- [ ] User always knows what question they're answering
- [ ] Interview feels progressive (one step at a time)
- [ ] No visual clutter from fixed bottom cards
- [ ] Smooth transitions between states

---

## Part H: Edge Cases & Considerations

### H.1 Re-editing Answers

**Question**: Can user change a previous answer?

**Decision**: No, not in v6. Once collapsed, answers are final.

**Workaround**: User can describe the change in chat:
```
"Actually, change the design style from Modern to Minimalist"
```

This triggers a new AI iteration that updates the plan.

### H.2 Interrupted Interview

**Question**: What if user sends a chat message during interview?

**Behavior**:
- InputBar is disabled during interview (existing behavior)
- User must answer or skip all questions to proceed to chat mode

### H.3 Network Error During Answer

**Question**: What if the API call fails when submitting an answer?

**Behavior**:
- Widget shows error state
- Answer is not collapsed (stays active)
- User can retry answering
- Existing error handling in ChatPanel applies

### H.4 Long Question Text

**Question**: What if question text is very long?

**Behavior**:
- In active widget: Full text shown
- In collapsed state: Text truncated to 50 chars with "..."
- Hover on collapsed Q&A shows full question as tooltip

### H.5 Long Answers

**Question**: What if user input is very long?

**Behavior**:
- In active widget: Full input shown
- In collapsed state: Answer truncated to 50 chars with "..."
- Hover shows full answer as tooltip

---

## Part I: Future Enhancements (Out of Scope)

- [ ] Edit collapsed answers (with confirmation)
- [ ] Reorder questions (drag and drop)
- [ ] Bulk skip all remaining questions
- [ ] Question progress indicator (e.g., "3 of 5 questions answered")
- [ ] Save interview as draft and resume later
- [ ] Interview templates (presets for common use cases)

---

## Summary

v6 is a focused UX improvement that makes the chat experience cleaner and more conversational:

| What's New | What It Solves |
|------------|----------------|
| No code in chat | Cleaner, more focused conversations |
| InterviewWidget | Progressive, one-question-at-a-time flow |
| Collapsed Q&A | Reduces clutter, shows history |
| No fixed cards | Everything flows naturally in thread |
| BuildPlanCard in thread | Consistent with conversational metaphor |

**Result**: A more intuitive, less overwhelming interview experience that guides users naturally from idea to generated page.

---

**Document Version**: 6.0
**Updated**: 2026-01-29
**Status**: Draft - Ready for Review
