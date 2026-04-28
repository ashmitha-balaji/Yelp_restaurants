import axios from 'axios';

export const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  // Let browser set Content-Type with boundary for FormData; instance default would break multipart
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login: (data) => api.post('/auth/login', data),
};

export const userAPI = {
  getProfile: () => api.get('/users/me'),
  updateProfile: (data) => api.put('/users/me', data),
  uploadPhoto: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('token');
    if (!token) {
      const err = new Error('Not authenticated');
      err.response = { status: 401 };
      throw err;
    }
    const res = await fetch(`${API_BASE}/users/me/photo`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    if (res.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') window.location.href = '/login';
      throw new Error('Session expired');
    }
    if (!res.ok) {
      const err = new Error('Upload failed');
      err.response = { status: res.status };
      throw err;
    }
    return { data: await res.json() };
  },
  getPreferences: () => api.get('/users/me/preferences'),
  updatePreferences: (data) => api.put('/users/me/preferences', data),
};

// Simple in-memory cache for search (5 min TTL) - reduces redundant API calls
const searchCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

const getCacheKey = (params) => JSON.stringify(params);
const getCached = (key) => {
  const entry = searchCache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.timestamp > CACHE_TTL) {
    searchCache.delete(key);
    return null;
  }
  return entry.data;
};

export const restaurantAPI = {
  searchYelp: async (params) => {
    const key = getCacheKey({ yelp: true, ...params });
    const cached = getCached(key);
    if (cached) return { data: cached };
    const res = await api.get('/restaurants/yelp', { params });
    searchCache.set(key, { data: res.data.restaurants || res.data, timestamp: Date.now() });
    return res;
  },
  getYelpById: (yelpId) => api.get(`/restaurants/yelp/${yelpId}`),
  getYelpReviews: (yelpId) => api.get(`/restaurants/yelp/${yelpId}/reviews`),
  // Do not cache local DB search results because owners/seeding can update IDs and records often.
  search: (params) => api.get('/restaurants/', { params }),
  getById: (id) => api.get(`/restaurants/${id}`),
  create: (data) => api.post('/restaurants/', data),
  update: (id, data) => api.put(`/restaurants/${id}`, data),
  claim: (id) => api.post(`/restaurants/${id}/claim`),
  uploadPhoto: (id, file, caption) => {
    const formData = new FormData();
    formData.append('file', file);
    if (caption) formData.append('caption', caption);
    return api.post(`/restaurants/${id}/photos`, formData);
  },
  getOwnerRestaurants: () => api.get('/restaurants/owner/my-restaurants'),
  trackView: (id) => api.post(`/owner-dashboard/restaurants/${id}/track-view`),
};

export const reviewAPI = {
  getRecent: (limit = 6) => api.get('/reviews/recent', { params: { limit } }),
  getForRestaurant: (restaurantId) => api.get(`/reviews/restaurant/${restaurantId}`),
  getMyReviews: () => api.get('/reviews/my-reviews'),
  create: (data) => api.post('/reviews/', data),
  update: (id, data) => api.put(`/reviews/${id}`, data),
  delete: (id) => api.delete(`/reviews/${id}`),
  getJob: (jobId) => api.get(`/reviews/job/${jobId}`),
  uploadPhoto: (reviewId, formData) =>
    api.post(`/reviews/${reviewId}/photo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  reply: (reviewId, reply) => api.post(`/reviews/${reviewId}/reply`, { reply }),
};

export const favoriteAPI = {
  getAll: () => api.get('/favorites/'),
  add: (restaurantId) => api.post('/favorites/', { restaurant_id: restaurantId }),
  remove: (restaurantId) => api.delete(`/favorites/${restaurantId}`),
  check: (restaurantId) => api.get(`/favorites/check/${restaurantId}`),
};

export const aiAPI = {
  chat: (message, conversationHistory) =>
    api.post('/ai-assistant/chat', { message, conversation_history: conversationHistory }),
};

export const historyAPI = {
  get: () => api.get('/history'),
};

export const ownerDashboardAPI = {
  getReviews: (params) => api.get('/owner-dashboard/reviews', { params }),
  getAnalytics: (params) => api.get('/owner-dashboard/analytics', { params }),
};

export const trendingAPI = {
  list: (params = {}) => api.get('/restaurants/trending', { params }),
};

export const waitlistAPI = {
  join: (restaurantId, payload) => api.post(`/waitlist/${restaurantId}`, payload),
  status: (restaurantId) => api.get(`/waitlist/${restaurantId}/status`),
  leave: (restaurantId) => api.delete(`/waitlist/${restaurantId}`),
  ownerQueue: (restaurantId) => api.get(`/waitlist/${restaurantId}`),
  callGuest: (restaurantId, userId) => api.post(`/waitlist/${restaurantId}/notify/${userId}`),
};

export const notificationAPI = {
  unreadCount: () => api.get('/notifications/unread-count'),
  list: (params = {}) => api.get('/notifications/', { params }),
  markRead: (id) => api.put(`/notifications/${id}/read`),
  markAllRead: () => api.put('/notifications/read-all'),
  remove: (id) => api.delete(`/notifications/${id}`),
};

export default api;
