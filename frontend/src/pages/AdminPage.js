import React from 'react';
import AdminDashboard from '../components/AdminDashboard';
import AdminRoute from '../components/AdminRoute';

const AdminPage = () => {
  return (
    <AdminRoute>
      <AdminDashboard />
    </AdminRoute>
  );
};

export default AdminPage;
