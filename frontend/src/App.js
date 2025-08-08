import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import './i18n'; // Initialize i18n
import Navbar from "./components/Navbar";
import ScrollToTop from "./components/ScrollToTop";
import HomePage from "./pages/HomePage";
import PricingPage from "./pages/PricingPage";
import LoginPage from "./pages/LoginPage";
import CustomerRegisterPage from "./pages/CustomerRegisterPage";
import PasswordResetPage from "./pages/PasswordResetPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import AuthCallbackPage from "./pages/AuthCallbackPage";
import OIDCCallback from "./pages/OIDCCallback";
import ProfilePage from "./pages/ProfilePage";
import SoundsPage from "./pages/SoundsPage";
import SoundDetailPage from "./pages/SoundDetailPage";
import SubscriptionsPage from "./pages/SubscriptionsPage";
import InvoicesPage from "./pages/InvoicesPage";
import SuperAdminPage from "./pages/SuperAdminPage";
import NotFoundPage from "./pages/NotFoundPage";
import ErrorBoundary from "./components/ErrorBoundary";
import { AuthProvider, useAuth } from "./hooks/useAuth";

// PrivateRoute component that takes an element prop
const PrivateRoute = ({ element }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  return isAuthenticated ? element : <Navigate to="/login" />;
};

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <AppContent />
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

// Separate component to use useAuth inside AuthProvider
const AppContent = () => {
  return (
    <>
      <ScrollToTop />
      <Navbar />
      <Routes>
          {/* Public routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/pricing" element={<PricingPage />} />
          <Route path="/plans" element={<PricingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<CustomerRegisterPage />} />
        <Route path="/register-customer" element={<CustomerRegisterPage />} />
        <Route path="/password-reset" element={<PasswordResetPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route path="/auth/oidc/callback" element={<OIDCCallback />} />
        <Route
          path="/profile"
          element={<PrivateRoute element={<ProfilePage />} />}
        />
        <Route
          path="/sounds"
          element={<PrivateRoute element={<SoundsPage />} />}
        />
        <Route path="/sounds/:id" element={<SoundDetailPage />} />
        <Route
          path="/subscriptions"
          element={<PrivateRoute element={<SubscriptionsPage />} />}
        />
        <Route
          path="/invoices"
          element={<PrivateRoute element={<InvoicesPage />} />}
        />
        <Route path="/super-admin" element={<SuperAdminPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  );
};

export default App;