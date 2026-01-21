import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { SubmissionsListResponse, SubmissionSummary } from '@/types/submission';

interface UseSubmissionsOptions {
  projectId: string;
  page?: number;
  perPage?: number;
  formId?: string;
}

export function useSubmissions({ projectId, page = 1, perPage = 50, formId }: UseSubmissionsOptions) {
  const [data, setData] = useState<SubmissionsListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSubmissions = async () => {
      setIsLoading(true);
      setError(null);

      const token = useAuthStore.getState().token;
      if (!token) {
        setError('Not authenticated');
        setIsLoading(false);
        return;
      }

      try {
        const params = new URLSearchParams({
          page: String(page),
          per_page: String(perPage),
        });

        if (formId) {
          params.append('form_id', formId);
        }

        const response = await fetch(
          `/api/projects/${projectId}/submissions?${params}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch submissions');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchSubmissions();
  }, [projectId, page, perPage, formId]);

  return { data, isLoading, error };
}

export function useSubmissionSummary(projectId: string) {
  const [data, setData] = useState<SubmissionSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      const token = useAuthStore.getState().token;
      if (!token) return;

      try {
        const response = await fetch(
          `/api/projects/${projectId}/submissions/summary`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.ok) {
          const result = await response.json();
          setData(result);
        }
      } catch {
        // Silently fail for summary
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummary();
  }, [projectId]);

  return { data, isLoading };
}

export function useExportSubmissions() {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const exportSubmissions = async (projectId: string, formId?: string, format: string = 'csv') => {
    setIsExporting(true);
    setError(null);

    const token = useAuthStore.getState().token;
    if (!token) {
      setError('Not authenticated');
      setIsExporting(false);
      return false;
    }

    try {
      const params = new URLSearchParams({ format });
      if (formId) {
        params.append('form_id', formId);
      }

      const response = await fetch(
        `/api/projects/${projectId}/submissions/export?${params}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `submissions-${Date.now()}.csv`;
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="([^"]+)"/);
        if (match?.[1]) {
          filename = match[1];
        }
      }

      // Download the file
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
      return false;
    } finally {
      setIsExporting(false);
    }
  };

  return { exportSubmissions, isExporting, error };
}
