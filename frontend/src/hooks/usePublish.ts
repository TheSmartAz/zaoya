import { useState } from 'react';
import { useAuthStore, getAuthHeaders } from '@/stores/authStore';
import { useVersionStore } from '@/stores/versionStore';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

interface PublishResult {
  success: boolean;
  url?: string;
  needsAuth?: boolean;
  error?: string;
}

interface UsePublishReturn {
  publish: () => Promise<PublishResult>;
  isPublishing: boolean;
  publishedUrl: string | null;
}

const formatError = (detail: unknown): string => {
  if (!detail) return 'Failed to publish';
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.join(', ');
  if (typeof detail === 'object' && detail && 'errors' in detail) {
    const errors = (detail as { errors?: string[] }).errors;
    if (errors && errors.length > 0) return errors.join(', ');
  }
  return 'Failed to publish';
};

export function usePublish(projectId: string): UsePublishReturn {
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishedUrl, setPublishedUrl] = useState<string | null>(null);
  const user = useAuthStore((s) => s.user);
  const getCurrentVersion = useVersionStore((s) => s.getCurrentVersion);

  const publish = async (): Promise<PublishResult> => {
    // Check authentication
    if (!user) {
      return { success: false, needsAuth: true };
    }

    const headers = getAuthHeaders();
    if (!headers.Authorization) {
      return { success: false, needsAuth: true };
    }

    // Check if there's content to publish
    const currentVersion = getCurrentVersion();
    if (!currentVersion) {
      return { success: false, error: 'No content to publish. Generate a page first.' };
    }

    setIsPublishing(true);

    try {
      const response = await fetch(`${API_BASE}/api/projects/${projectId}/publish`, {
        method: 'POST',
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        return { success: false, error: formatError(error.detail) };
      }

      const data = await response.json();
      setPublishedUrl(data.url);
      return { success: true, url: data.url };
    } catch (error) {
      return { success: false, error: 'Network error. Please try again.' };
    } finally {
      setIsPublishing(false);
    }
  };

  return {
    publish,
    isPublishing,
    publishedUrl,
  };
}
