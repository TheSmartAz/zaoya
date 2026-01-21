import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { useSubmissions, useSubmissionSummary, useExportSubmissions } from '@/hooks/useSubmissions';
import { SubmissionsTable } from '@/components/submissions/SubmissionsTable';
import { NotificationSettings } from '@/components/project/NotificationSettings';
import { useProjectStore } from '@/stores/projectStore';

export function SubmissionsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const project = useProjectStore((s) => (projectId ? s.getProject(projectId) : null));
  const updateProject = useProjectStore((s) => s.updateProject);

  const { data, isLoading, error } = useSubmissions({
    projectId: projectId || '',
    page,
    perPage: 50,
  });

  const { data: summary } = useSubmissionSummary(projectId || '');
  const { exportSubmissions, isExporting } = useExportSubmissions();

  const handleExport = async () => {
    if (projectId) {
      await exportSubmissions(projectId);
    }
  };

  const handlePrevPage = () => {
    if (page > 1) setPage(page - 1);
  };

  const handleNextPage = () => {
    if (data && page < data.pagination.pages) {
      setPage(page + 1);
    }
  };

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
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Form Submissions</h1>
                {summary && (
                  <p className="text-sm text-gray-500">
                    {summary.total_submissions} total
                    {summary.recent_submissions > 0 && ` (${summary.recent_submissions} in the last 7 days)`}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={handleExport}
                disabled={isExporting || !data || data.submissions.length === 0}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Download size={18} />
                {isExporting ? 'Exporting...' : 'Export CSV'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {project && !project.isGuest && (
          <div className="mb-6">
            <NotificationSettings
              project={project}
              onUpdate={(updates) => projectId && updateProject(projectId, updates)}
            />
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        ) : data?.submissions.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <svg
              className="w-16 h-16 mx-auto mb-4 text-gray-300"
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
            <h3 className="text-lg font-medium text-gray-900 mb-1">No submissions yet</h3>
            <p className="text-gray-500 mb-4">
              Share your published page to start collecting form submissions.
            </p>
            <button
              onClick={() => navigate(-1)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              Go Back
            </button>
          </div>
        ) : (
          <>
            <SubmissionsTable submissions={data?.submissions || []} />

            {/* Pagination */}
            {data && data.pagination.pages > 1 && (
              <div className="flex items-center justify-between mt-6 bg-white px-4 py-3 rounded-lg border border-gray-200">
                <div className="text-sm text-gray-600">
                  Showing {((data.pagination.page - 1) * data.pagination.per_page) + 1} to{' '}
                  {Math.min(data.pagination.page * data.pagination.per_page, data.pagination.total)} of{' '}
                  {data.pagination.total} submissions
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePrevPage}
                    disabled={page === 1}
                    className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft size={18} />
                  </button>

                  <span className="text-sm font-medium text-gray-700">
                    Page {data.pagination.page} of {data.pagination.pages}
                  </span>

                  <button
                    onClick={handleNextPage}
                    disabled={page >= data.pagination.pages}
                    className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronRight size={18} />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
