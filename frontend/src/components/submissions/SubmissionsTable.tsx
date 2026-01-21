import { FormSubmission } from '@/types/submission';

interface SubmissionsTableProps {
  submissions: FormSubmission[];
}

export function SubmissionsTable({ submissions }: SubmissionsTableProps) {
  if (submissions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-gray-500 bg-gray-50 rounded-lg">
        <svg
          className="w-16 h-16 mb-4 text-gray-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p className="text-lg font-medium">No submissions yet</p>
        <p className="text-sm mt-1">Share your page to start collecting responses!</p>
      </div>
    );
  }

  // Get all unique field names across all submissions
  const allFields = new Set<string>();
  submissions.forEach((s) => {
    Object.keys(s.data).forEach((key) => allFields.add(key));
  });
  const fields = Array.from(allFields);

  return (
    <div className="overflow-x-auto bg-white rounded-lg border border-gray-200">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            <th className="p-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Submitted
            </th>
            {fields.map((field) => (
              <th
                key={field}
                className="p-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider"
              >
                {field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {submissions.map((submission) => (
            <tr
              key={submission.id}
              className="hover:bg-gray-50 transition-colors"
            >
              <td className="p-4 text-sm">
                <div className="flex flex-col">
                  <span className="text-gray-900 font-medium">
                    {formatDate(submission.metadata.submitted_at)}
                  </span>
                  <span className="text-gray-500 text-xs">
                    {formatTime(submission.metadata.submitted_at)}
                  </span>
                </div>
              </td>
              {fields.map((field) => (
                <td key={field} className="p-4 text-sm text-gray-700">
                  {formatValue(submission.data[field])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatValue(value: unknown): React.ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-gray-400 italic">-</span>;
  }

  if (typeof value === 'boolean') {
    return value ? (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
        Yes
      </span>
    ) : (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
        No
      </span>
    );
  }

  if (Array.isArray(value)) {
    const displayValue = value.slice(0, 3).join(', ');
    return (
      <span className="text-gray-600" title={value.join(', ')}>
        {displayValue}
        {value.length > 3 && ` (+${value.length - 3} more)`}
      </span>
    );
  }

  if (typeof value === 'object') {
    return <span className="text-gray-400 italic">Object</span>;
  }

  const strValue = String(value);
  if (strValue.length > 50) {
    return (
      <span className="text-gray-600" title={strValue}>
        {strValue.slice(0, 50)}...
      </span>
    );
  }

  return <span className="text-gray-700">{strValue}</span>;
}
