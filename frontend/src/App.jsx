import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Layout from './components/Layout';
import { isLoggedIn } from './utils/auth';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import SkillGapGIS from './pages/SkillGapGIS';
import IndustryRadar from './pages/IndustryRadar';
import WorkforceTransition from './pages/WorkforceTransition';
import WhatIfPlanner from './pages/WhatIfPlanner';
import EarlyWarning from './pages/EarlyWarning';
import DataExplorer from './pages/DataExplorer';
import Recommendations from './pages/Recommendations';
import Methodology from './pages/Methodology';

function RequireAuth({ children }) {
  const location = useLocation();
  if (!isLoggedIn()) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/gis" element={<SkillGapGIS />} />
        <Route path="/radar" element={<IndustryRadar />} />
        <Route path="/transition" element={<WorkforceTransition />} />
        <Route path="/what-if" element={<WhatIfPlanner />} />
        <Route path="/early-warning" element={<EarlyWarning />} />
        <Route path="/data" element={<DataExplorer />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/methodology" element={<Methodology />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
