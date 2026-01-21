import { useState } from 'react';
import { Globe } from 'lucide-react';
import { usePublish } from '@/hooks/usePublish';
import { useAuthStore } from '@/stores/authStore';
import { useProjectStore } from '@/stores/projectStore';
import { PublishSuccessModal } from './PublishSuccessModal';
import { ConversionPrompt } from '../project/ConversionPrompt';

interface PublishButtonProps {
  projectId: string;
}

export function PublishButton({ projectId }: PublishButtonProps) {
  const { publish, isPublishing, publishedUrl } = usePublish(projectId);
  const [showSuccess, setShowSuccess] = useState(false);
  const [showConversion, setShowConversion] = useState(false);
  const [publishResult, setPublishResult] = useState<{ url: string } | null>(null);

  const user = useAuthStore((s) => s.user);
  const project = useProjectStore((s) => s.getProject(projectId));

  const handlePublish = async () => {
    if (project?.isGuest && !user) {
      setShowConversion(true);
      return;
    }

    const result = await publish();
    if (result.success && result.url) {
      setPublishResult({ url: result.url });
      setShowSuccess(true);
    }
  };

  return (
    <>
      <button
        onClick={handlePublish}
        disabled={isPublishing}
        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <Globe size={18} />
        {isPublishing ? 'Publishing...' : publishedUrl ? 'Update' : 'Publish'}
      </button>

      {showConversion && project && (
        <ConversionPrompt
          project={project}
          trigger="publish"
          onConverted={() => {
            setShowConversion(false);
            handlePublish();
          }}
        />
      )}

      {showSuccess && publishResult && (
        <PublishSuccessModal
          url={publishResult.url}
          onClose={() => setShowSuccess(false)}
        />
      )}
    </>
  );
}
