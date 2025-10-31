import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://18.117.190.231:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Knowledge Base API
  searchKnowledgeBase: async (query, limit = 10) => {
    try {
      const response = await api.get('/mcp/search-knowledge-base', {
        params: { query, limit }
      });
      return response;
    } catch (error) {
      throw error;
    }
  },

  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response;
    } catch (error) {
      throw error;
    }
  },

  // Email automation status
  getEmailAutomationStatus: async () => {
    try {
      const response = await api.get('/mcp/email-automation-status');
      return response;
    } catch (error) {
      throw error;
    }
  },

  // Email automation stats
  getEmailAutomationStats: async () => {
    try {
      const response = await api.get('/mcp/email-automation-stats');
      return response;
    } catch (error) {
      throw error;
    }
  },

  // Analytics dashboard
  getAnalyticsDashboard: async (days = 7) => {
    try {
      const response = await api.get('/analytics/dashboard', {
        params: { days }
      });
      return response;
    } catch (error) {
      throw error;
    }
  }
};

export default api;