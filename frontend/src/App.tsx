import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { CreatePage } from './pages/CreatePage';
import { EditorPage } from './pages/EditorPage';
import { PublishedPage } from './pages/PublishedPage';
import { SubmissionsPage } from './pages/SubmissionsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/create" replace />} />
        <Route path="/create" element={<CreatePage />} />
        <Route path="/editor" element={<EditorPage />} />
        <Route path="/editor/:projectId" element={<EditorPage />} />
        <Route path="/editor/:projectId/submissions" element={<SubmissionsPage />} />
        <Route path="/editor/:projectId/analytics" element={<AnalyticsPage />} />
        <Route path="/p/:publicId" element={<PublishedPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
