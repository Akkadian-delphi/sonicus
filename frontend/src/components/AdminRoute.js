import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const AdminRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontSize: '1.2rem',
        color: '#6c757d'
      }}>
        Checking admin permissions...
      </div>
    );
  }

  // Check if user is authenticated and is an admin
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Add admin check here - you'll need to store admin status in your user context
  // For now, we'll check if user email contains 'admin' or add is_superuser field
  const isAdmin = user.email?.includes('admin') || user.is_superuser;
  
  if (!isAdmin) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '60px 20px',
        color: '#dc3545'
      }}>
        <h2>Access Denied</h2>
        <p>You don't have permission to access the admin panel.</p>
        <button 
          onClick={() => window.history.back()}
          style={{
            padding: '10px 20px',
            background: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginTop: '20px'
          }}
        >
          Go Back
        </button>
      </div>
    );
  }

  return children;
};

export default AdminRoute;
