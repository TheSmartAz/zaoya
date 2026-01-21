import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function PublishedPage() {
  const { publicId } = useParams<{ publicId: string }>();
  const [html, setHtml] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!publicId) return;

    const fetchPage = async () => {
      try {
        const response = await fetch(`/p/${publicId}`);
        if (response.ok) {
          const content = await response.text();
          setHtml(content);
        } else {
          setError('Page not found');
        }
      } catch (err) {
        setError('Failed to load page');
      } finally {
        setLoading(false);
      }
    };

    fetchPage();
  }, [publicId]);

  const handleBack = () => {
    navigate('/create');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <h1 className="text-2xl font-semibold text-gray-800 mb-2">Page Not Found</h1>
          <p className="text-gray-500 mb-4">{error}</p>
          <button
            onClick={handleBack}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create Your Own Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Back button overlay - only visible in development */}
      <div className="fixed top-4 left-4 z-50">
        <button
          onClick={handleBack}
          className="flex items-center gap-2 px-3 py-2 bg-white/80 backdrop-blur rounded-lg shadow hover:bg-white transition-colors"
        >
          <ArrowLeft size={18} />
          <span className="text-sm">Create Page</span>
        </button>
      </div>

      {/* Render the published page */}
      {html && (
        <iframe
          srcDoc={html}
          title={`Published page: ${publicId}`}
          className="w-full h-screen border-0"
          sandbox="allow-scripts allow-same-origin allow-forms"
        />
      )}
    </div>
  );
}
