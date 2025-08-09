import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import './i18n'; // Initialize i18n
import Navbar from "./components/Navbar";
import ScrollToTop from "./components/ScrollToTop";
import HomePage from "./pages/HomePage";
import PricingPage from "./pages/PricingPage";
import LoginPage from "./pages/LoginPage";
import CustomerRegisterPage from "./pages/CustomerRegisterPage";
import EnhancedBusinessRegistrationPage from "./pages/EnhancedBusinessRegistrationPage";
import BusinessWelcomePage from "./pages/BusinessWelcomePage";
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
import OrganizationDashboard from "./components/OrganizationDashboard";
import UserManagement from "./components/UserManagement";
import OrganizationBranding from "./components/OrganizationBranding";
import CustomThemeBuilder from "./components/CustomThemeBuilder";
import BusinessRegistration from "./components/business/BusinessRegistration";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { TenantProvider, useTenant } from "./context/TenantContext";
import { getDomainContext } from "./utils/domainDetection";

// PrivateRoute component that takes an element prop
const PrivateRoute = ({ element }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return <div>Loading...</div>;
  return isAuthenticated ? element : <Navigate to="/login" />;
};

// B2B2C Route component for organization-specific routes
const OrganizationRoute = ({ element }) => {
  const { isAuthenticated, loading } = useAuth();
  const { isB2B2CMode, loading: tenantLoading } = useTenant();

  if (loading || tenantLoading) return <div>Loading...</div>;
  
  if (!isAuthenticated) return <Navigate to="/login" />;
  if (!isB2B2CMode()) return <Navigate to="/" />;
  
  return element;
};

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <TenantProvider>
          <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <AppContent />
          </Router>
        </TenantProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

// Separate component to use useAuth and useTenant inside providers
const AppContent = () => {
  const { isB2B2CMode, domainContext, loading: tenantLoading } = useTenant();
  
  // Show loading while tenant detection is in progress
  if (tenantLoading) {
    return (
      <div className="tenant-loading">
        <div className="loading-content">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // Get domain context for conditional rendering
  const domain = domainContext || getDomainContext();
  
  return (
    <>
      <ScrollToTop />
      
      {/* Conditional Navbar - different for main domain vs subdomain */}
      {domain.isMainDomain && <Navbar />}
      
      <Routes>
        {/* Main Domain Routes (B2C) - sonicus.eu */}
        {domain.isMainDomain && (
          <>
            <Route path="/" element={<HomePage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/plans" element={<PricingPage />} />
            <Route path="/business/register" element={<BusinessRegistration />} />
            <Route path="/business/welcome" element={<BusinessWelcomePage />} />
          </>
        )}
        
        {/* Subdomain Routes (B2B2C) - company.sonicus.eu */}
        {domain.isSubdomain && (
          <>
            <Route path="/" element={<OrganizationRoute element={<OrganizationDashboard />} />} />
            <Route path="/dashboard" element={<OrganizationRoute element={<OrganizationDashboard />} />} />
            <Route path="/users" element={<OrganizationRoute element={<UserManagement />} />} />
            <Route path="/branding" element={<OrganizationRoute element={<OrganizationBranding />} />} />
            <Route path="/themes" element={<OrganizationRoute element={<CustomThemeBuilder />} />} />
          </>
        )}
        
        {/* Common Routes (both B2C and B2B2C) */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<CustomerRegisterPage />} />
        <Route path="/register-customer" element={<CustomerRegisterPage />} />
        <Route path="/password-reset" element={<PasswordResetPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route path="/auth/oidc/callback" element={<OIDCCallback />} />
        
        {/* User Routes (available in both modes) */}
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
        
        {/* Legacy Organization Routes (backward compatibility) */}
        <Route
          path="/organization/dashboard"
          element={<OrganizationRoute element={<OrganizationDashboard />} />}
        />
        <Route
          path="/organization/users"
          element={<OrganizationRoute element={<UserManagement />} />}
        />
        <Route
          path="/organization/branding"
          element={<OrganizationRoute element={<OrganizationBranding />} />}
        />
        <Route
          path="/organization/themes"
          element={<OrganizationRoute element={<CustomThemeBuilder />} />}
        />
        
        {/* Super Admin (main domain only) */}
        {domain.isMainDomain && (
          <Route path="/super-admin" element={<SuperAdminPage />} />
        )}
        
        {/* 404 handling */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  );
};

export default App;