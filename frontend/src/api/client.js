import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = `${API_BASE}/api/v1`;

const api = axios.create({
  baseURL: API_PREFIX,
  timeout: 60000,
});

// Documents
export const documentsAPI = {
  upload: (file, onProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total));
      },
    });
  },
  list: () => api.get('/documents/'),
  get: (id) => api.get(`/documents/${id}`),
  delete: (id) => api.delete(`/documents/${id}`),
};

// Sessions
export const sessionsAPI = {
  create: (title = 'New Chat') => api.post('/sessions/', { title }),
  list: () => api.get('/sessions/'),
  delete: (id) => api.delete(`/sessions/${id}`),
  update: (id, title) => api.patch(`/sessions/${id}`, { title }),
};

// Chat
export const chatAPI = {
  send: (sessionId, message, documentIds = null) =>
    api.post('/chat/', {
      session_id: sessionId,
      message,
      document_ids: documentIds,
    }),
  history: (sessionId) => api.get(`/chat/${sessionId}/history`),
};

export default api;
