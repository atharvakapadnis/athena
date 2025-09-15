import { BrowserRouter as Router, Routes, Route, Navigate} from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { AuthProvider } from '@/hooks/use-auth';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { RegisterPage } from '@/pages/RegisterPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { ROUTES } from '@/constants';

// Create a new MUI theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

//Create a new QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, //5 minutes
    },
    mutations: {
      retry: 1,
    },
  },
});

function App(){
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Router>
            <Routes>
              {/* Public routes */}
              <Route path={ROUTES.LOGIN} element={<LoginPage />} />
              <Route path={ROUTES.REGISTER} element={<RegisterPage />} />
              
              {/* Protected routes */}
              <Route
                path={ROUTES.DASHBOARD}
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <DashboardPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              {/* Placeholder routes for other pages */}
              <Route
                path={ROUTES.BATCHES}
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <div>Batch Management - Coming Soon</div>
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path={ROUTES.RULES}
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <div>Rule Management - Coming Soon</div>
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path={ROUTES.AI_ANALYSIS}
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <div>AI Analysis - Coming Soon</div>
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              
              <Route
                path={ROUTES.SYSTEM}
                element={
                  <ProtectedRoute>
                    <AppLayout>
                      <div>System Administration - Coming Soon</div>
                    </AppLayout>
                  </ProtectedRoute>
                }
              />

              {/* Default redirect */}
              <Route path="/" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
              
              {/* 404 route */}
              <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
            </Routes>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;