import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { OverviewPage } from '@/pages/OverviewPage';
import { PerformancePage } from '@/pages/PerformancePage';
import { RAGPage } from '@/pages/RAGPage';
import { AssistantPage } from '@/pages/AssistantPage';
import { AlertsPage } from '@/pages/AlertsPage';
import { SystemPage } from '@/pages/SystemPage';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/performance" element={<PerformancePage />} />
          <Route path="/rag" element={<RAGPage />} />
          <Route path="/assistant" element={<AssistantPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/system" element={<SystemPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;