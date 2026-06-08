import { useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { useStore } from './stores';
import { Spin } from 'antd';

const Home = lazy(() => import('./pages/Home'));
const Tasks = lazy(() => import('./pages/Tasks'));
const Downloads = lazy(() => import('./pages/Downloads'));
const Settings = lazy(() => import('./pages/Settings'));
const About = lazy(() => import('./pages/About'));

function LoadingFallback() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
      <Spin size="large" />
    </div>
  );
}

function App() {
  const { fetchConfig } = useStore();

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Suspense fallback={<LoadingFallback />}><Home /></Suspense>} />
          <Route path="tasks" element={<Suspense fallback={<LoadingFallback />}><Tasks /></Suspense>} />
          <Route path="downloads" element={<Suspense fallback={<LoadingFallback />}><Downloads /></Suspense>} />
          <Route path="settings" element={<Suspense fallback={<LoadingFallback />}><Settings /></Suspense>} />
          <Route path="about" element={<Suspense fallback={<LoadingFallback />}><About /></Suspense>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
