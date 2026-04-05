import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { MainLayout } from './components/layouts/MainLayout';
import { Toast } from './components/ui/Toast';
import Dashboard from './pages/Dashboard';
import CalendarPage from './pages/Calendar';
import PatientsPage from './pages/Patients/PatientsPage';
import SurgeryPage from './pages/Surgery/SurgeryPage';

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/patients" element={<PatientsPage />} />
          <Route path="/surgery" element={<SurgeryPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MainLayout>
      <Toast />
    </BrowserRouter>
  </QueryClientProvider>
);

export default App;
