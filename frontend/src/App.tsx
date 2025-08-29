import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";

import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import BatchManagement from './pages/BatchManagement';
import RuleManagement from './pages/RuleManagement';
import AIAnalysis from './pages/AIAnalysis';
import SystemSettings from './pages/SystemSettings';
import Login from './pages/Login';
import NotFound from './pages/NotFound';

// Create a clinet for React Query
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            cacheTime: 1000 * 60 * 30, // 30 minutes
        },
    },
})

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <Router>
                <div className="App">
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route path="/" element={<Layout />}>
                            <Route index element={<Dashboard />} />
                            <Route path="batches" element={<BatchManagement />} />
                            <Route path="rules" element={<RuleManagement />} />
                            <Route path="ai-analysis" element={<AIAnalysis />} />
                            <Route path="settings" element={<SystemSettings />} />
                        </Route>
                        <Route path="*" element={<NotFound />} />
                    </Routes>
                    <Toaster position="top-right" />
                </div>
            </Router>
        </QueryClientProvider>
    )
}

export default App;