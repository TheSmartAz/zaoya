import { TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: number;
  trend?: number;
  size?: 'sm' | 'md';
}

export function StatCard({ label, value, trend, size = 'md' }: StatCardProps) {
  const isPositive = trend !== undefined && trend > 0;
  const isNegative = trend !== undefined && trend < 0;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <span className={`text-gray-500 ${size === 'sm' ? 'text-xs' : 'text-sm'} font-medium`}>
          {label}
        </span>
        {trend !== undefined && (
          <div
            className={`flex items-center gap-1 text-xs font-medium ${
              isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-500'
            }`}
          >
            {isPositive ? <TrendingUp size={14} /> : isNegative ? <TrendingDown size={14} /> : null}
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
      <p className={`text-gray-900 font-semibold mt-1 ${size === 'sm' ? 'text-xl' : 'text-3xl'}`}>
        {value.toLocaleString()}
      </p>
    </div>
  );
}
