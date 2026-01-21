import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Template, TemplateInputs } from '@/types/template';
import { templates } from '@/data/templates';
import { TemplateGrid } from '@/components/create/TemplateGrid';
import { TemplateInputForm } from '@/components/create/TemplateInputForm';
import { useProjectStore } from '@/stores/projectStore';

export function CreatePage() {
  const navigate = useNavigate();
  const createGuestProject = useProjectStore((s) => s.createGuestProject);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [templateInputs, setTemplateInputs] = useState<TemplateInputs>({});

  const handleSelectTemplate = (template: Template) => {
    setSelectedTemplate(template);
    setTemplateInputs({});
  };

  const handleStartProject = () => {
    if (!selectedTemplate) return;
    const project = createGuestProject(
      selectedTemplate.name,
      selectedTemplate.id,
      templateInputs
    );
    navigate(`/editor/${project.id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      {!selectedTemplate ? (
        <TemplateGrid
          templates={templates}
          onSelectTemplate={handleSelectTemplate}
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
