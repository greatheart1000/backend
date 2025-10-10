import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const PublicPage = () => {
  const [publicData, setPublicData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const { user } = useAuth();

  useEffect(() => {
    const fetchPublicData = async () => {
      try {
        const response = await axios.get('/api/public');
        setPublicData(response.data);
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to fetch public data');
      } finally {
        setLoading(false);
      }
    };

    fetchPublicData();
  }, []);

  return (
    <div className="public-page">
      <header>
        <h1>JWT Authentication Demo</h1>
        <nav>
          {user ? (
            <Link to="/dashboard">Dashboard</Link>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </nav>
      </header>
      
      <main>
        <h2>Public Page</h2>
        {loading ? (
          <p>Loading public data...</p>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : (
          <div className="data-section">
            <h3>Public Data</h3>
            <pre>{JSON.stringify(publicData, null, 2)}</pre>
          </div>
        )}
        
        <div className="info-section">
          <h3>About this demo</h3>
          <p>This is a full-stack JWT authentication system with:</p>
          <ul>
            <li>User registration and login</li>
            <li>JWT token generation and validation</li>
            <li>Protected routes and resources</li>
            <li>Token refresh functionality</li>
            <li>Role-based access control (RBAC)</li>
          </ul>
        </div>
      </main>
    </div>
  );
};

export default PublicPage;