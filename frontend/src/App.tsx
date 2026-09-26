import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { CacheProvider } from './contexts/CacheContext';
import DashboardLayout from './layouts/DashboardLayout';
import OverviewPage from './pages/OverviewPage';
import DeepResearchPage from './pages/DeepResearchPage';
import RetailPage from './pages/RetailPage';
import AuditPage from './pages/AuditPage';
import TimeMachinePage from './pages/TimeMachinePage';
import AgentUplinkPage from './pages/AgentUplinkPage';
import LandingPage from './pages/LandingPage';
import ClimateFinancePage from './pages/ClimateFinancePage';
import DisasterPage from './pages/DisasterPage';
import IntelSwarmPage from './pages/IntelSwarmPage';

function App() {
  return (
    <CacheProvider>
      <BrowserRouter>
        <Routes>
          {/* Landing Page */}
          <Route path="/" element={<LandingPage />} />

          {/* Main App Routes */}
          <Route path="/app" element={<DashboardLayout />}>
            <Route index element={<OverviewPage />} />
            <Route path="globe" element={<IntelSwarmPage />} />
            <Route path="research" element={<DeepResearchPage />} />
            <Route path="audit" element={<AuditPage />} />
            <Route path="timemachine" element={<TimeMachinePage />} />
            <Route path="retail" element={<RetailPage />} />
            <Route path="finance" element={<ClimateFinancePage />} />
            <Route path="disaster" element={<DisasterPage />} />
            <Route path="chat" element={<AgentUplinkPage />} />
            {/* Redirect /app/* to /app */}
            <Route path="*" element={<Navigate to="/app" replace />} />
          </Route>

          {/* Global Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </CacheProvider>
  );
}

export default App;
