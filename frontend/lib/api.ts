/**
 * API Client for University Data Visualization Dashboard
 *
 * Provides typed API methods for communicating with Django REST backend.
 */

import axios, { AxiosInstance, AxiosError } from 'axios';

// API Base URL from environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens (future enhancement)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message);
    } else {
      // Error in request configuration
      console.error('Request Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Type definitions
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface Dataset {
  id: number;
  title: string;
  description: string;
  filename: string;
  file_size: number;
  upload_date: string;
  record_count: number;
  category: string;
  uploaded_by: User;
  records?: DataRecord[];
}

export interface DataRecord {
  id: number;
  dataset: number;
  data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DatasetStatistics {
  total_datasets: number;
  total_records: number;
  total_size: number;
  categories: Array<{ category: string; count: number }>;
  recent_uploads: Dataset[];
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// API Methods
export const api = {
  // Dataset endpoints
  datasets: {
    list: async (params?: {
      page?: number;
      page_size?: number;
    }): Promise<PaginatedResponse<Dataset>> => {
      const response = await apiClient.get('/api/datasets/', { params });
      return response.data;
    },

    get: async (id: number): Promise<Dataset> => {
      const response = await apiClient.get(`/api/datasets/${id}/`);
      return response.data;
    },

    create: async (data: FormData): Promise<Dataset> => {
      const response = await apiClient.post('/api/datasets/', data, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },

    update: async (id: number, data: Partial<Dataset>): Promise<Dataset> => {
      const response = await apiClient.put(`/api/datasets/${id}/`, data);
      return response.data;
    },

    patch: async (id: number, data: Partial<Dataset>): Promise<Dataset> => {
      const response = await apiClient.patch(`/api/datasets/${id}/`, data);
      return response.data;
    },

    delete: async (id: number): Promise<void> => {
      await apiClient.delete(`/api/datasets/${id}/`);
    },

    // Upload file and create new dataset
    uploadFile: async (data: {
      file: File;
      title: string;
      description?: string;
      category?: string;
    }): Promise<Dataset> => {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('title', data.title);
      if (data.description) formData.append('description', data.description);
      if (data.category) formData.append('category', data.category);

      const response = await apiClient.post('/api/datasets/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    },

    // Upload file to existing dataset (legacy)
    upload: async (
      id: number,
      file: File
    ): Promise<{ status: string; records_created: number; message: string }> => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post(
        `/api/datasets/${id}/upload/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    },

    getRecords: async (
      id: number,
      params?: { page?: number; page_size?: number }
    ): Promise<PaginatedResponse<DataRecord>> => {
      const response = await apiClient.get(`/api/datasets/${id}/records/`, {
        params,
      });
      return response.data;
    },

    // Export endpoints
    exportCSV: async (id: number): Promise<Blob> => {
      const response = await apiClient.post(
        `/api/datasets/${id}/export/csv/`,
        {},
        {
          responseType: 'blob',
        }
      );
      return response.data;
    },

    exportExcel: async (id: number): Promise<Blob> => {
      const response = await apiClient.post(
        `/api/datasets/${id}/export/excel/`,
        {},
        {
          responseType: 'blob',
        }
      );
      return response.data;
    },

    exportPDF: async (id: number): Promise<Blob> => {
      const response = await apiClient.post(
        `/api/datasets/${id}/export/pdf/`,
        {},
        {
          responseType: 'blob',
        }
      );
      return response.data;
    },
  },

  // DataRecord endpoints
  records: {
    list: async (params?: {
      dataset_id?: number;
      page?: number;
      page_size?: number;
    }): Promise<PaginatedResponse<DataRecord>> => {
      const response = await apiClient.get('/api/records/', { params });
      return response.data;
    },

    get: async (id: number): Promise<DataRecord> => {
      const response = await apiClient.get(`/api/records/${id}/`);
      return response.data;
    },

    create: async (data: {
      dataset: number;
      data: Record<string, any>;
    }): Promise<DataRecord> => {
      const response = await apiClient.post('/api/records/', data);
      return response.data;
    },

    update: async (id: number, data: Partial<DataRecord>): Promise<DataRecord> => {
      const response = await apiClient.put(`/api/records/${id}/`, data);
      return response.data;
    },

    patch: async (id: number, data: Partial<DataRecord>): Promise<DataRecord> => {
      const response = await apiClient.patch(`/api/records/${id}/`, data);
      return response.data;
    },

    delete: async (id: number): Promise<void> => {
      await apiClient.delete(`/api/records/${id}/`);
    },
  },

  // Statistics endpoints
  statistics: {
    overview: async (): Promise<DatasetStatistics> => {
      const response = await apiClient.get('/api/statistics/overview/');
      return response.data;
    },
  },
};

export default api;
