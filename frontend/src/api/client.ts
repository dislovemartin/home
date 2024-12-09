import axios from 'axios';
import { useAuthStore } from '@store/auth';

const baseURL = import.meta.env.VITE_API_URL || '/api';

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const modelApi = {
  list: async () => {
    const response = await apiClient.get('/models');
    return response.data;
  },

  get: async (id: string) => {
    const response = await apiClient.get(`/models/${id}`);
    return response.data;
  },

  optimize: async (id: string, config: any) => {
    const response = await apiClient.post(`/models/${id}/optimize`, config);
    return response.data;
  },

  delete: async (id: string) => {
    const response = await apiClient.delete(`/models/${id}`);
    return response.data;
  },
};

export const metricsApi = {
  getGpuMetrics: async () => {
    const response = await apiClient.get('/metrics/gpu');
    return response.data;
  },

  getModelMetrics: async (id: string) => {
    const response = await apiClient.get(`/metrics/models/${id}`);
    return response.data;
  },

  getSystemMetrics: async () => {
    const response = await apiClient.get('/metrics/system');
    return response.data;
  },
};

export const authApi = {
  login: async (username: string, password: string) => {
    const response = await apiClient.post('/token', {
      username,
      password,
    });
    return response.data;
  },

  logout: async () => {
    const response = await apiClient.post('/logout');
    return response.data;
  },

  me: async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  },
}; 