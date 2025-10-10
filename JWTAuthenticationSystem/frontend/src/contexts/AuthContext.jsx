import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // 初始化时检查是否有有效的token
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      // 验证token有效性
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      axios.get('/auth/me')
        .then(response => {
          setUser(response.data.user);
        })
        .catch(() => {
          // Token无效，清除它
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          delete axios.defaults.headers.common['Authorization'];
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  // 登录函数
  const login = async (username, password) => {
    try {
      const response = await axios.post('/auth/login', { username, password });
      const { access_token, refresh_token, user } = response.data;
      
      // 保存token到localStorage
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      
      // 设置默认authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // 设置用户状态
      setUser(user);
      
      return response.data;
    } catch (error) {
      throw error;
    }
  };

  // 注册函数
  const register = async (username, email, password) => {
    try {
      const response = await axios.post('/auth/register', { username, email, password });
      const { access_token, refresh_token, user } = response.data;
      
      // 保存token到localStorage
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      
      // 设置默认authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // 设置用户状态
      setUser(user);
      
      return response.data;
    } catch (error) {
      throw error;
    }
  };

  // 登出函数
  const logout = () => {
    // 清除token
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    delete axios.defaults.headers.common['Authorization'];
    
    // 清除用户状态
    setUser(null);
  };

  // 刷新token函数
  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      
      const response = await axios.post('/auth/refresh', {}, {
        headers: {
          'Authorization': `Bearer ${refreshToken}`
        }
      });
      
      const { access_token } = response.data;
      
      // 更新token
      localStorage.setItem('accessToken', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return access_token;
    } catch (error) {
      // 刷新失败，登出用户
      logout();
      throw error;
    }
  };

  const value = {
    user,
    login,
    register,
    logout,
    refreshToken,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};