import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const Dashboard = () => {
  const [profileData, setProfileData] = useState(null);
  const [publicData, setPublicData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 获取受保护的用户资料数据
        const profileResponse = await axios.get('/api/profile');
        setProfileData(profileResponse.data);
        
        // 获取公开数据
        const publicResponse = await axios.get('/api/public');
        setPublicData(publicResponse.data);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading) {
    return <div className="dashboard">Loading...</div>;
  }

  return (
    <div className="dashboard">
      <header>
        <h1>Dashboard</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="user-info">
        <h2>Welcome, {user?.username}!</h2>
        <p>Email: {user?.email}</p>
        <p>Role: {user?.role}</p>
      </div>
      
      <div className="data-section">
        <h3>Public Data</h3>
        <pre>{JSON.stringify(publicData, null, 2)}</pre>
      </div>
      
      <div className="data-section">
        <h3>Profile Data (Protected)</h3>
        <pre>{JSON.stringify(profileData, null, 2)}</pre>
      </div>
    </div>
  );
};

export default Dashboard;