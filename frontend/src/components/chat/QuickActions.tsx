import { QuickAction } from '@/types/quickAction';
import { getActionsByCategory, getQuickActionsForTemplate } from '@/data/quickActions';

interface QuickActionsProps {
  template: string | null;
  onAction: (action: QuickAction) => void;
  disabled?: boolean;
}

export function QuickActions({ template: _template, onAction, disabled = false }: QuickActionsProps) {
  const allActions = getQuickActionsForTemplate(_template);
  const grouped = getActionsByCategory(allActions);

  const renderActionGroup = (actions: QuickAction[], title: string) => {
    if (actions.length === 0) return null;

    return (
      <div className="mb-3">
        <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">{title}</p>
        <div className="flex flex-wrap gap-2">
          {actions.map((action) => (
            <button
              key={action.id}
              onClick={() => onAction(action)}
              disabled={disabled}
              className="px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg
                         hover:bg-blue-50 hover:border-blue-300 hover:text-blue-700
                         disabled:opacity-50 disabled:cursor-not-allowed
                         transition-all duration-200"
              title={action.prompt}
            >
              {action.icon && <span className="mr-1">{action.icon}</span>}
              {action.label}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="p-3 border-t bg-gray-50">
      {renderActionGroup(grouped.style || [], 'Style')}
      {renderActionGroup(grouped.content || [], 'Content')}
      {renderActionGroup(grouped.structure || [], 'Structure')}
    </div>
  );
}
