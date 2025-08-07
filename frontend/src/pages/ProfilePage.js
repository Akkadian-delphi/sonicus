import React from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { getDisplayRole } from "../utils/roleBasedRedirect";

function ProfilePage() {
  const { user } = useAuth();

  if (!user) return <div className="loading">Loading...</div>;

  return (
    <div className="container" style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '30px' }}>
        <h1>Welcome back, {user.email}!</h1>
        <p style={{ color: '#666', fontSize: '1.1rem' }}>
          Role: <strong>{getDisplayRole(user.role)}</strong>
        </p>
      </div>

      {/* Quick Actions */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
        gap: '20px',
        marginBottom: '40px'
      }}>
        <div style={{
          background: 'white',
          padding: '24px',
          borderRadius: '12px',
          boxShadow: '0 2px 12px rgba(0,0,0,0.1)',
          border: '1px solid #e2e8f0'
        }}>
          <h3 style={{ marginBottom: '16px', color: '#2d3748' }}>🎵 Sound Library</h3>
          <p style={{ color: '#666', marginBottom: '16px' }}>
            Explore our collection of therapeutic sounds
          </p>
          <Link 
            to="/sounds" 
            style={{
              display: 'inline-block',
              padding: '10px 20px',
              background: '#667eea',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '6px',
              transition: 'background-color 0.3s'
            }}
          >
            Browse Sounds
          </Link>
        </div>

        <div style={{
          background: 'white',
          padding: '24px',
          borderRadius: '12px',
          boxShadow: '0 2px 12px rgba(0,0,0,0.1)',
          border: '1px solid #e2e8f0'
        }}>
          <h3 style={{ marginBottom: '16px', color: '#2d3748' }}>📊 My Subscriptions</h3>
          <p style={{ color: '#666', marginBottom: '16px' }}>
            Manage your sound subscriptions and preferences
          </p>
          <Link 
            to="/subscriptions" 
            style={{
              display: 'inline-block',
              padding: '10px 20px',
              background: '#48bb78',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '6px',
              transition: 'background-color 0.3s'
            }}
          >
            View Subscriptions
          </Link>
        </div>

        <div style={{
          background: 'white',
          padding: '24px',
          borderRadius: '12px',
          boxShadow: '0 2px 12px rgba(0,0,0,0.1)',
          border: '1px solid #e2e8f0'
        }}>
          <h3 style={{ marginBottom: '16px', color: '#2d3748' }}>💳 Billing</h3>
          <p style={{ color: '#666', marginBottom: '16px' }}>
            View invoices and manage payment methods
          </p>
          <Link 
            to="/invoices" 
            style={{
              display: 'inline-block',
              padding: '10px 20px',
              background: '#ed8936',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '6px',
              transition: 'background-color 0.3s'
            }}
          >
            View Invoices
          </Link>
        </div>
      </div>

      {/* Profile Information */}
      <div style={{
        background: 'white',
        padding: '30px',
        borderRadius: '12px',
        boxShadow: '0 2px 12px rgba(0,0,0,0.1)',
        border: '1px solid #e2e8f0'
      }}>
        <h2 style={{ marginBottom: '20px', color: '#2d3748' }}>Profile Information</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px', color: '#4a5568' }}>
              Email:
            </label>
            <p style={{ color: '#666', fontSize: '1.1rem' }}>{user.email}</p>
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px', color: '#4a5568' }}>
              Status:
            </label>
            <p style={{ 
              color: user.is_active ? '#48bb78' : '#f56565', 
              fontSize: '1.1rem',
              fontWeight: '500'
            }}>
              {user.is_active ? "Active" : "Inactive"}
            </p>
          </div>
          <div>
            <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px', color: '#4a5568' }}>
              Role:
            </label>
            <p style={{ color: '#666', fontSize: '1.1rem' }}>{getDisplayRole(user.role)}</p>
          </div>
          {user.organization && (
            <div>
              <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '5px', color: '#4a5568' }}>
                Organization:
              </label>
              <p style={{ color: '#666', fontSize: '1.1rem' }}>{user.organization.name || 'N/A'}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
