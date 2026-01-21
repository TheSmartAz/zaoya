import { DailyAnalytics } from '@/types/analytics';

interface AnalyticsChartProps {
  data: DailyAnalytics[];
  metric?: 'views' | 'visitors' | 'clicks' | 'submissions';
}

export function AnalyticsChart({ data, metric = 'views' }: AnalyticsChartProps) {
  // Find maximum value for scaling
  const maxValue = Math.max(...data.map((d) => d[metric]), 1);

  const metricLabel = {
    views: 'Page Views',
    visitors: 'Unique Visitors',
    clicks: 'CTA Clicks',
    submissions: 'Form Submissions',
  }[metric];

  const metricColor = {
    views: 'bg-blue-500',
    visitors: 'bg-green-500',
    clicks: 'bg-purple-500',
    submissions: 'bg-orange-500',
  }[metric];

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">{metricLabel}</h3>
        <span className="text-sm text-gray-500">
          {data.reduce((sum, d) => sum + d[metric], 0).toLocaleString()} total
        </span>
      </div>

      {/* Chart */}
      <div className="relative h-48">
        <div className="absolute inset-0 flex items-end gap-1">
          {data.map((day) => {
            const height = day[metric] > 0 ? Math.max((day[metric] / maxValue) * 100, 2) : 0;
            const hasValue = day[metric] > 0;

            return (
              <div
                key={day.date}
                className="flex-1 group relative"
                title={`${day.date}: ${day[metric]} ${metric}`}
              >
                <div
                  className={`${metricColor} rounded-t hover:opacity-80 transition-opacity absolute bottom-0 left-0 right-0`}
                  style={{ height: `${height}%` }}
                />

                {/* Tooltip */}
                {hasValue && (
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                    {day[metric]}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Zero line */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gray-200" />
      </div>

      {/* Date labels */}
      <div className="flex justify-between mt-2 text-xs text-gray-500">
        <span>{formatDate(data[0]?.date)}</span>
        <span>{formatDate(data[data.length - 1]?.date)}</span>
      </div>
    </div>
  );
}

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
