import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiError } from '../types';

// API base URL - can be configured via environment variable
// Use /api prefix for all API calls to separate from page routes
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,  // Use empty base URL to rely on Vite proxy
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      (error: AxiosError) => {
        if (error.response) {
          // Server responded with error status
          const apiError: ApiError = {
            error: error.response.data as string || 'api_error',
            message: (error.response.data as Record<string, unknown>)?.message as string || 'An error occurred',
            details: (error.response.data as Record<string, unknown>)?.details as Record<string, unknown>,
          };
          return Promise.reject(apiError);
        } else if (error.request) {
          // Request made but no response
          const apiError: ApiError = {
            error: 'network_error',
            message: 'Network error. Please check your connection.',
          };
          return Promise.reject(apiError);
        } else {
          // Something else happened
          const apiError: ApiError = {
            error: 'unknown_error',
            message: error.message || 'An unexpected error occurred',
          };
          return Promise.reject(apiError);
        }
      }
    );
  }

  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }

  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for custom instances if needed
export { ApiClient };
export default apiClient;
