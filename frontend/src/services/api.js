import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Knowledge Base
  searchKnowledgeBase: (query, limit = 10) =>
    api.post('/mcp/kb-lookup', { query, limit }),

  // Tickets
  createTicket: (ticketData) =>
    api.post('/mcp/create-ticket', ticketData),

  // Email
  sendEmail: (emailData) =>
    api.post('/mcp/send-email', emailData),

  // Memory/Logging
  logMemory: (memoryData) =>
    api.post('/mcp/log-memory', memoryData),

  // Calendar
  scheduleMeeting: (meetingData) =>
    api.post('/mcp/schedule-meeting', meetingData),

  // Analytics (mock endpoints - you may need to implement these)
  getAnalytics: () => api.get('/analytics'),
  getTicketStats: () => api.get('/analytics/tickets'),
  getKnowledgeBaseStats: () => api.get('/analytics/kb'),
};

export default api;