import { useState } from 'react';
import { useProjectStore } from '@/stores/projectStore';
import { useAuthStore } from '@/stores/authStore';
import { AuthModal } from '@/components/auth/AuthModal';
import { Project } from '@/types/project';

interface ConversionPromptProps {
  project: Project;
  trigger?: 'publish' | 'save' | 'limit';
  onConverted?: () => void;
}

export function ConversionPrompt({ project, trigger = 'publish', onConverted }: ConversionPromptProps) {
  const [showAuth, setShowAuth] = useState(false);
  const [isConverting, setIsConverting] = useState(false);
  const { convertToUserProject } = useProjectStore();
  const { user } = useAuthStore();

  const messages = {
    publish: {
      title: 'Sign in to publish your page',
      description: 'Publish your page and share it with the world using a unique link.',
    },
    save: {
      title: 'Sign in to save your project',
      description: 'Save your project to the cloud so you can access it from any device.',
    },
    limit: {
      title: 'Sign in to create more projects',
      description: 'You’ve reached the guest project limit. Sign in to save unlimited projects.',
    },
  };

  const { title, description } = messages[trigger];

  const handleSignInSuccess = async () => {
    if (!user) return;

    setIsConverting(true);
    try {
      await convertToUserProject(project.id);
      onConverted?.();
    } catch (error) {
      console.error('Failed to convert project:', error);
    } finally {
      setIsConverting(false);
    }
  };

  return (
    <>
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-blue-900 font-semibold mb-1">{title}</h3>
        <p className="text-blue-700 text-sm mb-4">{description}</p>
        <button
          onClick={() => setShowAuth(true)}
          disabled={isConverting}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isConverting ? 'Converting...' : 'Sign in to continue'}
        </button>
      </div>

      <AuthModal
        isOpen={showAuth}
        onClose={() => setShowAuth(false)}
        onSuccess={handleSignInSuccess}
        title={title}
      />
    </>
  );
}
