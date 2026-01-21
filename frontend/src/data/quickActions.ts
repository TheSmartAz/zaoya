import { QuickAction } from '@/types/quickAction';

/** Universal quick actions - shown for all template types */
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
    id: 'more-minimal',
    label: 'More minimal',
    prompt: 'Make the design more minimal. Remove unnecessary elements, use more whitespace, simplify the layout.',
    icon: '🌫️',
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
    prompt: 'What color vibe are you looking for? (I\'ll offer options)',
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

/** Contextual quick actions - shown only for specific template types */
export const contextualActions: Record<string, QuickAction[]> = {
  event: [
    {
      id: 'add-rsvp',
      label: 'Add RSVP form',
      prompt: 'Add an RSVP form where guests can confirm attendance. Include name, email, and number of guests.',
      icon: '📋',
      category: 'structure',
      templates: ['event'],
    },
    {
      id: 'add-countdown',
      label: 'Add countdown',
      prompt: 'Add a countdown timer showing days/hours until the event date.',
      icon: '⏰',
      category: 'structure',
      templates: ['event'],
    },
    {
      id: 'add-map',
      label: 'Add map link',
      prompt: 'Add a Google Maps link button for the event location.',
      icon: '🗺️',
      category: 'structure',
      templates: ['event'],
    },
  ],
  product: [
    {
      id: 'add-pricing',
      label: 'Add pricing table',
      prompt: 'Add a pricing table section. What pricing tiers do you have?',
      icon: '💰',
      category: 'structure',
      templates: ['product'],
    },
    {
      id: 'add-countdown',
      label: 'Add launch countdown',
      prompt: 'Add a countdown timer for the product launch.',
      icon: '⏰',
      category: 'structure',
      templates: ['product'],
    },
    {
      id: 'add-features-grid',
      label: 'Add features grid',
      prompt: 'Add a visual grid layout for the features with icons.',
      icon: '🔲',
      category: 'structure',
      templates: ['product'],
    },
  ],
  profile: [
    {
      id: 'add-social',
      label: 'Add social links',
      prompt: 'Add social media links section. Which platforms should I include?',
      icon: '🔗',
      category: 'structure',
      templates: ['profile'],
    },
    {
      id: 'add-portfolio',
      label: 'Add portfolio items',
      prompt: 'Add a portfolio/work samples section with image cards.',
      icon: '🖼️',
      category: 'structure',
      templates: ['profile'],
    },
    {
      id: 'add-contact',
      label: 'Add contact info',
      prompt: 'Add contact information (email, phone, location).',
      icon: '📧',
      category: 'structure',
      templates: ['profile'],
    },
  ],
  form: [
    {
      id: 'add-field',
      label: 'Add form field',
      prompt: 'What additional field should I add to the form?',
      icon: '➕',
      category: 'structure',
      templates: ['form'],
    },
    {
      id: 'add-confirmation',
      label: 'Add confirmation message',
      prompt: 'Add a nice confirmation message that shows after the form is submitted.',
      icon: '✅',
      category: 'structure',
      templates: ['form'],
    },
  ],
};

/** Get quick actions for a specific template */
export function getQuickActionsForTemplate(templateId: string | null): QuickAction[] {
  const contextual = templateId ? (contextualActions[templateId] || []) : [];
  return [...contextual, ...universalActions];
}

/** Get quick actions by category */
export function getActionsByCategory(actions: QuickAction[]): Record<string, QuickAction[]> {
  return {
    style: actions.filter((a) => a.category === 'style'),
    content: actions.filter((a) => a.category === 'content'),
    structure: actions.filter((a) => a.category === 'structure'),
  };
}
