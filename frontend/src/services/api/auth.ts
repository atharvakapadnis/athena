import apiClient from '@/lib/api-client';
import type { APIResponse, User, UserLogin, UserCreate, Token } from '@/types';

export const authService = {
    async login(credentials: UserLogin): Promise<Token> {
        const response = await apiClient.post<APIResponse<Token>>('/api/auth/login', credentials);
        return response.data.data!;
    },

    async register(userData: UserCreate): Promise<User> {
        const response = await apiClient.post<APIResponse<User>>('/api/auth/register', userData);
        return response.data.data!;
    },

    async getCurrentUser(): Promise<User> {
        const response = await apiClient.get<APIResponse<User>>('/api/auth/me');
        return response.data.data!;
    },

    async logout(): Promise<void> {
        //Clear local storage
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
    },
};