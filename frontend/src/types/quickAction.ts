/** Quick action category */
export type QuickActionCategory = 'style' | 'content' | 'structure';

/** Quick action for page refinement */
export interface QuickAction {
  id: string;
  label: string;
  prompt: string;
  icon?: string;
  category: QuickActionCategory;
  templates?: string[]; // If empty, show for all templates
}
