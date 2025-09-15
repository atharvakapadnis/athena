import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService } from '@/services/api';
import { QUERY_KEYS } from '@/constants';
import type { User, UserLogin, UserCreate } from '@/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: UserLogin) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('authToken')
  );
  const queryClient = useQueryClient();

  // Fetch current user data when token exists
  const {
    data: user,
    isLoading,
    error,
  } = useQuery({
    queryKey: QUERY_KEYS.CURRENT_USER,
    queryFn: authService.getCurrentUser,
    enabled: !!token,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Clear token if user fetch fails (invalid token)
  useEffect(() => {
    if (error && token) {
      setToken(null);
      localStorage.removeItem('authToken');
    }
  }, [error, token]);

  const loginMutation = useMutation({
    mutationFn: authService.login,
    onSuccess: (tokenData) => {
      const newToken = tokenData.access_token;
      setToken(newToken);
      localStorage.setItem('authToken', newToken);
      // Invalidate and refetch user data
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CURRENT_USER });
    },
  });

  const registerMutation = useMutation({
    mutationFn: authService.register,
    onSuccess: () => {
      // Registration successful, user can now login
      // We don't auto-login for security reasons
    },
  });

  const login = async (credentials: UserLogin) => {
    await loginMutation.mutateAsync(credentials);
  };

  const register = async (userData: UserCreate) => {
    await registerMutation.mutateAsync(userData);
  };

  const logout = () => {
    setToken(null);
    authService.logout();
    queryClient.clear(); // Clear all cached data
  };

  const isAuthenticated = !!token && !!user;

  return (
    <AuthContext.Provider
      value={{
        user: user || null, // Fix: Handle undefined case
        isLoading: isLoading && !!token,
        isAuthenticated,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}