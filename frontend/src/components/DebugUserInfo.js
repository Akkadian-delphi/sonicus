import React from 'react';
import { useAuth } from '../hooks/useAuth';

const DebugUserInfo = () => {
  const { user, hasRole, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <div>Not authenticated</div>;
  }

  return (
    <div style={{ 
      position: 'fixed', 
      top: 0, 
      right: 0, 
      background: 'white', 
      border: '1px solid #ccc', 
      padding: '10px', 
      zIndex: 9999,
      fontSize: '12px',
      maxWidth: '300px'
    }}>
      <h4>Debug User Info</h4>
      <pre>{JSON.stringify(user, null, 2)}</pre>
      <p>hasRole('business_admin'): {String(hasRole('business_admin'))}</p>
      <p>hasRole(['business_admin', 'staff']): {String(hasRole(['business_admin', 'staff']))}</p>
    </div>
  );
};

export default DebugUserInfo;
