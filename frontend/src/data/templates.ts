import { Template } from '@/types/template';

/** Template definitions */
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
    systemPromptAddition: `Generate a modern link-in-bio style profile page with:
- A centered profile photo area (placeholder if not provided)
- Large, bold name heading
- Clean bio text
- Social/media link buttons arranged vertically
- Mobile-first, centered layout
- Use a clean, modern aesthetic with good whitespace`,
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
    systemPromptAddition: `Generate a festive event invitation page with:
- Large, celebratory event title
- Date/time prominently displayed with icon
- Location details
- RSVP form (name, email, number of guests)
- Event details section
- Use celebratory colors and typography
- Mobile-first single column layout`,
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
    systemPromptAddition: `Generate a modern SaaS-style product landing page with:
- Hero section with product name and tagline
- Clear, prominent call-to-action button
- Features section (if provided)
- Pricing highlight (if provided)
- Clean, professional design
- Mobile-first with strong visual hierarchy`,
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
    systemPromptAddition: `Generate a clean form page with:
- Centered form title
- Well-spaced form fields with labels
- Submit button with clear label
- Use Zaoya.submitForm() for form submission
- Form fields should have proper types (email, tel, etc.)
- Clean, minimal design with good input contrast
- Mobile-first with touch-friendly inputs`,
  },
];

/** Get template by ID */
export function getTemplateById(id: string): Template | undefined {
  return templates.find((t) => t.id === id);
}

/** Get templates by category */
export function getTemplatesByCategory(category: string): Template[] {
  return templates.filter((t) => t.category === category);
}

/** Get all template categories */
export function getTemplateCategories(): Array<{ id: string; name: string; icon: string }> {
  return [
    { id: 'profile', name: 'Personal Profile', icon: '👤' },
    { id: 'event', name: 'Event Invitation', icon: '🎉' },
    { id: 'product', name: 'Product Landing', icon: '🚀' },
    { id: 'form', name: 'Contact/Lead Form', icon: '📝' },
  ];
}
