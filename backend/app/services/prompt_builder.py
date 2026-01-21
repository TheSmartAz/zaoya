"""Prompt builder service for constructing AI system prompts with template context."""

from typing import Any, Dict

# Base system prompt for code generation
BASE_SYSTEM_PROMPT = """You are Zaoya, an AI that generates mobile-first web pages.

Rules for HTML generation:
1. Mobile-first design - single column, touch-friendly
2. Use Tailwind CSS classes for styling
3. Include viewport meta tag: <meta name="viewport" content="width=device-width, initial-scale=1.0">
4. Full HTML document structure (html, head, body)
5. Clean, modern aesthetic with good whitespace
6. Limited interactivity - forms should use Zaoya.submitForm()
7. No external JavaScript except CDN links to Tailwind

Available runtime functions:
- Zaoya.submitForm(formData): Submit form data
- Zaoya.track(event, data): Track analytics events
- Zaoya.toast(message): Show a toast notification

Response format:
- Wrap code in ```html ... ``` blocks
- Keep JavaScript minimal and separate in ```js ... ``` if needed
- Always include full HTML document

Generate clean, safe code that follows web standards."""


def build_system_prompt(template: Dict[str, Any], inputs: Dict[str, str]) -> str:
    """Build system prompt with template context and user inputs.

    Args:
        template: Template configuration dict with id, name, systemPromptAddition
        inputs: User-provided input values keyed by input ID

    Returns:
        Complete system prompt string
    """
    template_context = f"""

=== TEMPLATE CONTEXT ===
Template Type: {template.get('name', 'Custom')}
Template ID: {template.get('id', 'custom')}

{template.get('systemPromptAddition', '')}

=== USER PROVIDED INFORMATION ===
"""

    # Format user inputs
    for key, value in inputs.items():
        if value and value.strip():
            # Format key: "firstName" -> "First Name"
            label = key.replace('_', ' ').replace('-', ' ').title()
            template_context += f"\n{label}: {value}"

    template_context += """

=== GENERATION INSTRUCTIONS ===
Using the template context and user information above, generate a complete,
mobile-first HTML page that matches the requested template style.
Include all the information the user provided in an appropriate layout.
"""

    return BASE_SYSTEM_PROMPT + template_context


def build_interview_prompt(
    template: Dict[str, Any],
    known_facts: Dict[str, str],
    questions_asked: list[str],
) -> str:
    """Build prompt for generating interview questions.

    Args:
        template: Template configuration
        known_facts: Information already collected
        questions_asked: Questions already asked (IDs)

    Returns:
        Interview prompt string
    """
    known_section = "\n".join(
        f"- {k}: {v}" for k, v in known_facts.items() if v and v.strip()
    ) or "(none yet)"

    return f"""Based on the user's template choice and inputs, identify what CRITICAL information is missing for a great first generation.

Template: {template.get('name', 'Custom')}

Already known:
{known_section}

Questions already asked: {len(questions_asked)}/6

Ask 1-3 focused questions about:
1. Primary goal/CTA (if unclear from template)
2. Tone/vibe (professional, playful, minimal, bold, elegant)
3. Visual preference (color scheme, style reference)
4. Any missing key content for the template type

IMPORTANT: Max 6 total questions. If you have enough info for a great first generation, say "READY_TO_GENERATE: true"

Format your response as:
QUESTIONS:
1. [Question text] | OPTIONS: [opt1, opt2, opt3, opt4] | SKIP: [skip option text]
2. [Question text] | TYPE: text | SKIP: [skip option text]

Or if ready:
READY_TO_GENERATE: true"""


def format_quick_action_prompt(action: str, template: Dict[str, Any]) -> str:
    """Format a quick action into a full refinement prompt.

    Args:
        action: Quick action prompt text
        template: Current template context

    Returns:
        Full prompt for AI
    """
    return f"""The user selected a quick action: "{action}"

Current template: {template.get('name', 'Custom')}

Apply this change to the existing page. Maintain all existing content and structure,
only modifying what the quick action specifically requests.

Generate the complete updated HTML."""


# Import template data if available (for frontend reference)
try:
    from ..data.templates import templates
    TEMPLATE_LOOKUP = {t.id: t for t in templates}
except ImportError:
    TEMPLATE_LOOKUP = {}
