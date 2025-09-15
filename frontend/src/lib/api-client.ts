import axios, { AxiosError, AxiosResponse } from 'axios';
import type { APIResponse, ApiError } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, //30 seconds
});

//Request interceptor to add auth token
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Repsponse interceptor for error handling
apiClient.interceptors.response.use(
    (response: AxiosResponse<APIResponse>) => response,
    (error: AxiosError<APIResponse>) => {
        // Handle auth errors
        if (error.response?.status === 401) {
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');
            // Add redirect logic here later
            window.location.href = '/login';
        }

        // Transform error response
        const apiError: ApiError = {
            message: error.response?.data?.message || error.message || 'An unexpected error occurred',
            status: error.response?.status || 500,
            details: error.response?.data,
        };
        return Promise.reject(apiError);
    }
);

export default apiClient;