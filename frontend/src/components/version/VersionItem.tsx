import { Clock, RotateCcw } from 'lucide-react';
import { Version } from '@/types/version';

interface VersionItemProps {
  version: Version;
  isCurrent: boolean;
  onRestore: () => void;
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;

  return date.toLocaleDateString();
}

function getChangeTypeLabel(changeType: string): string {
  switch (changeType) {
    case 'initial':
      return 'Initial';
    case 'refinement':
      return 'Refined';
    case 'quick_action':
      return 'Quick Action';
    case 'restore':
      return 'Restored';
    default:
      return 'Updated';
  }
}

function getChangeTypeColor(changeType: string): string {
  switch (changeType) {
    case 'initial':
      return 'bg-green-100 text-green-700';
    case 'refinement':
      return 'bg-blue-100 text-blue-700';
    case 'quick_action':
      return 'bg-purple-100 text-purple-700';
    case 'restore':
      return 'bg-amber-100 text-amber-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

export function VersionItem({ version, isCurrent, onRestore }: VersionItemProps) {
  return (
    <div className={`p-3 border-b last:border-b-0 ${isCurrent ? 'bg-blue-50' : 'hover:bg-gray-50'}`}>
      <div className="flex justify-between items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-gray-900">v{version.number}</span>
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${getChangeTypeColor(version.metadata.changeType)}`}
            >
              {getChangeTypeLabel(version.metadata.changeType)}
            </span>
            {isCurrent && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                Current
              </span>
            )}
          </div>

          <p className="text-sm text-gray-600 truncate mb-1">
            {version.metadata.prompt}
          </p>

          <div className="flex items-center gap-1 text-xs text-gray-400">
            <Clock size={12} />
            <span>{formatTime(version.metadata.timestamp)}</span>
          </div>
        </div>

        {!isCurrent && (
          <button
            onClick={onRestore}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 px-2 py-1 rounded transition-colors"
            title="Restore this version"
          >
            <RotateCcw size={14} />
            <span>Restore</span>
          </button>
        )}
      </div>
    </div>
  );
}
