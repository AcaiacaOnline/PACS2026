import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_URL = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Não redirecionar para login durante OAuth callback
    const isOAuthRequest = error.config?.url?.includes('/auth/oauth/');
    
    if (error.response?.status === 401 && !isOAuthRequest) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('auth_type');
      // Só redirecionar se não estiver na página de login ou callback
      if (!window.location.pathname.includes('/login') && !window.location.hash.includes('session_id')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
