import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

// 创建axios实例
const apiClient = axios.create({
  baseURL: 'http://localhost:5000',
  timeout: 10000,
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 从localStorage获取access token
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // 如果是401未授权错误且不是刷新token的请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // 尝试刷新token
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await axios.post('/auth/refresh', {}, {
            headers: {
              'Authorization': `Bearer ${refreshToken}`
            }
          });
          
          const { access_token } = response.data;
          
          // 保存新的access token
          localStorage.setItem('accessToken', access_token);
          
          // 更新原请求的Authorization header
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          
          // 重新发送原请求
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // 刷新token失败，清除本地存储并重定向到登录页
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;