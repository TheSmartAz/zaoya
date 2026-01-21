import { Template } from '@/types/template';
import { TemplateCard } from './TemplateCard';

interface TemplateGridProps {
  templates: Template[];
  onSelectTemplate: (template: Template) => void;
}

export function TemplateGrid({ templates, onSelectTemplate }: TemplateGridProps) {
  const categories = Array.from(new Set(templates.map((t) => t.category)));

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          What do you want to create?
        </h1>
        <p className="text-gray-500">
          Choose a template to get started fast
        </p>
      </div>

      {categories.map((category) => {
        const categoryTemplates = templates.filter((t) => t.category === category);
        const firstTemplate = categoryTemplates[0];

        return (
          <div key={category} className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">{firstTemplate.icon}</span>
              <h2 className="text-lg font-semibold text-gray-700 capitalize">
                {firstTemplate.name}
              </h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {categoryTemplates.map((template) => (
                <TemplateCard
                  key={template.id}
                  template={template}
                  onClick={() => onSelectTemplate(template)}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
