import { Template } from '@/types/template';

interface TemplateCardProps {
  template: Template;
  onClick: () => void;
}

export function TemplateCard({ template, onClick }: TemplateCardProps) {
  return (
    <button
      onClick={onClick}
      className="w-full p-6 text-left bg-white border-2 border-gray-200 rounded-xl hover:border-blue-400 hover:shadow-lg transition-all duration-200 group"
    >
      <div className="flex flex-col items-center text-center gap-3">
        <span className="text-4xl group-hover:scale-110 transition-transform">
          {template.icon}
        </span>
        <h3 className="font-semibold text-gray-900">
          {template.name}
        </h3>
        <p className="text-sm text-gray-500">
          {template.description}
        </p>
      </div>
    </button>
  );
}
