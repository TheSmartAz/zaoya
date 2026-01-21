import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp } from 'lucide-react';
import { useAnalytics } from '@/hooks/useAnalytics';
import { StatCard } from '@/components/analytics/StatCard';
import { AnalyticsChart } from '@/components/analytics/AnalyticsChart';

const PERIOD_OPTIONS = [
  { value: 7, label: 'Last 7 days' },
  { value: 30, label: 'Last 30 days' },
  { value: 90, label: 'Last 90 days' },
];

const METRIC_OPTIONS = [
  { value: 'views', label: 'Page Views' },
  { value: 'visitors', label: 'Unique Visitors' },
  { value: 'clicks', label: 'CTA Clicks' },
  { value: 'submissions', label: 'Form Submissions' },
] as const;

export function AnalyticsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [period, setPeriod] = useState(30);
  const [metric, setMetric] = useState<typeof METRIC_OPTIONS[number]['value']>('views');

  const { data, isLoading, error } = useAnalytics(projectId || '', period);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ArrowLeft size={20} className="text-gray-600" />
              </button>
              <div className="flex items-center gap-2">
                <TrendingUp size={24} className="text-blue-600" />
                <h1 className="text-xl font-semibold text-gray-900">Analytics</h1>
              </div>
            </div>

            {/* Period selector */}
            <div className="flex items-center gap-2">
              {PERIOD_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setPeriod(option.value)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    period === option.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        ) : !data ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <p className="text-gray-500">No analytics data available yet.</p>
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard
                label="Page Views"
                value={data.totals.views}
                trend={data.trends.views}
              />
              <StatCard
                label="Unique Visitors"
                value={data.totals.unique_visitors}
                trend={data.trends.visitors}
              />
              <StatCard
                label="CTA Clicks"
                value={data.totals.cta_clicks}
              />
              <StatCard
                label="Form Submissions"
                value={data.totals.form_submissions}
              />
            </div>

            {/* Metric Selector & Chart */}
            <div className="mb-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-sm font-medium text-gray-700">Show chart:</span>
                {METRIC_OPTIONS.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setMetric(option.value)}
                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      metric === option.value
                        ? 'bg-gray-900 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>

              <AnalyticsChart data={data.daily} metric={metric} />
            </div>

            {/* Conversion Rate */}
            {data.totals.views > 0 && (
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <h3 className="font-semibold text-gray-900 mb-4">Conversion Metrics</h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <div>
                    <p className="text-sm text-gray-500">CTR (Clicks / Views)</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {((data.totals.cta_clicks / data.totals.views) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Form Conversion (Submissions / Views)</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {((data.totals.form_submissions / data.totals.views) * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Form Completion (Submissions / Clicks)</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {data.totals.cta_clicks > 0
                        ? ((data.totals.form_submissions / data.totals.cta_clicks) * 100).toFixed(1)
                        : '0'}%
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
