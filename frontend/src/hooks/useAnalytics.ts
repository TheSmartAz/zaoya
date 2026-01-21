import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { AnalyticsResponse } from '@/types/analytics';

export function useAnalytics(projectId: string, days: number = 30) {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setIsLoading(true);
      setError(null);

      const token = useAuthStore.getState().token;
      if (!token) {
        setError('Not authenticated');
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(
          `/api/projects/${projectId}/analytics?days=${days}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch analytics');
        }

        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalytics();
  }, [projectId, days]);

  return { data, isLoading, error };
}
