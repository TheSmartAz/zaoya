import { History } from 'lucide-react';
import { useVersionStore } from '@/stores/versionStore';
import { VersionItem } from './VersionItem';

export function VersionHistoryPanel() {
  const versions = useVersionStore((s) => s.getVersionHistory());
  const currentId = useVersionStore((s) => s.currentVersionId);
  const restoreVersion = useVersionStore((s) => s.restoreVersion);
  const isLoading = useVersionStore((s) => s.isLoading);
  const error = useVersionStore((s) => s.error);

  // Show versions in reverse order (newest first)
  const reversedVersions = [...versions].reverse();
  const handleRestore = (versionId: string) => {
    restoreVersion(versionId).catch(() => {
      // Errors are surfaced via store state
    });
  };

  if (isLoading && versions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-400 p-6">
        <History size={32} className="mb-2 opacity-50" />
        <p className="text-sm">Loading versions...</p>
      </div>
    );
  }

  if (error && versions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-red-500 p-6">
        <History size={32} className="mb-2 opacity-50" />
        <p className="text-sm">Failed to load versions</p>
        <p className="text-xs text-center mt-1">{error}</p>
      </div>
    );
  }

  if (versions.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-400 p-6">
        <History size={32} className="mb-2 opacity-50" />
        <p className="text-sm">No versions yet</p>
        <p className="text-xs text-center mt-1">
          Versions are created each time you generate
        </p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b bg-gray-50">
        <h3 className="font-semibold text-gray-700 flex items-center gap-2">
          <History size={18} />
          Version History
        </h3>
        <p className="text-xs text-gray-500 mt-1">
          {versions.length} version{versions.length !== 1 ? 's' : ''}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {reversedVersions.map((version) => (
          <VersionItem
            key={version.id}
            version={version}
            isCurrent={version.id === currentId}
            onRestore={() => handleRestore(version.id)}
          />
        ))}
      </div>
    </div>
  );
}
