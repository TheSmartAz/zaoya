/** Template category */
export type TemplateCategory = 'profile' | 'event' | 'product' | 'form';

/** Input field type for template form */
export type TemplateInputType = 'text' | 'textarea' | 'date' | 'url' | 'email' | 'image';

/** Template input field definition */
export interface TemplateInput {
  id: string;
  label: string;
  type: TemplateInputType;
  placeholder: string;
  required: boolean;
}

/** Template definition */
export interface Template {
  id: string;
  category: TemplateCategory;
  name: string;
  description: string;
  icon: string;
  exampleImage?: string;
  requiredInputs: TemplateInput[];
  optionalInputs: TemplateInput[];
  systemPromptAddition: string;
}

/** Template inputs collected from user */
export type TemplateInputs = Record<string, string>;
