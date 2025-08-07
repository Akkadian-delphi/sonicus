import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import axios from '../utils/axios';
import './RegistrationCompletion.css';

const RegistrationCompletion = ({ onComplete }) => {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    telephone: '',
    preferred_payment_method: ''
  });
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPaymentMethods();
  }, []);

  const fetchPaymentMethods = async () => {
    try {
      const response = await axios.get('/payment-methods/recommended', {
        params: {
          currency: 'USD',
          platform: detectPlatform()
        }
      });
      setPaymentMethods(response.data);
    } catch (error) {
      console.error('Error fetching payment methods:', error);
      setError('Failed to load payment methods');
    }
  };

  const detectPlatform = () => {
    const userAgent = navigator.userAgent;
    if (/iPad|iPhone|iPod/.test(userAgent)) return 'ios';
    if (/Android/.test(userAgent)) return 'android';
    return 'web';
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const payload = {};
      
      // Only include fields that have values
      if (formData.telephone.trim()) {
        payload.telephone = formData.telephone.trim();
      }
      
      if (formData.preferred_payment_method) {
        payload.preferred_payment_method = formData.preferred_payment_method;
      }

      const response = await axios.put('/users/complete-registration', payload);
      
      console.log('Registration completed:', response.data);
      
      // Call the completion callback
      if (onComplete) {
        onComplete(response.data);
      }
      
    } catch (error) {
      console.error('Registration completion error:', error);
      setError(
        error.response?.data?.detail || 
        'Failed to complete registration. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = () => {
    if (onComplete) {
      onComplete(user);
    }
  };

  return (
    <div className="registration-completion">
      <div className="completion-container">
        <h2>Complete Your Registration</h2>
        <p className="completion-subtitle">
          Help us provide you with the best experience by sharing a few optional details.
        </p>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="completion-form">
          {/* Telephone Field */}
          <div className="form-group">
            <label htmlFor="telephone">
              Phone Number <span className="optional">(Optional)</span>
            </label>
            <input
              type="tel"
              id="telephone"
              name="telephone"
              value={formData.telephone}
              onChange={handleInputChange}
              placeholder="+1 (555) 123-4567"
              className="form-input"
            />
            <small className="field-help">
              We'll only use this for important account updates
            </small>
          </div>

          {/* Payment Method Selection */}
          <div className="form-group">
            <label htmlFor="preferred_payment_method">
              Preferred Payment Method <span className="optional">(Optional)</span>
            </label>
            <select
              id="preferred_payment_method"
              name="preferred_payment_method"
              value={formData.preferred_payment_method}
              onChange={handleInputChange}
              className="form-select"
            >
              <option value="">Choose your preferred method</option>
              {paymentMethods.map((method) => (
                <option key={method.value} value={method.value}>
                  {method.name} - {method.description}
                  {method.processing_fee > 0 && ` (${method.processing_fee}% fee)`}
                </option>
              ))}
            </select>
            <small className="field-help">
              This will be your default payment option for subscriptions
            </small>
          </div>

          {/* Trial Information */}
          <div className="trial-info">
            <div className="trial-badge">
              <span className="trial-icon">🎉</span>
              <div className="trial-text">
                <strong>7-Day Free Trial Activated!</strong>
                <p>Enjoy full access to all premium sounds and features.</p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="form-actions">
            <button
              type="button"
              onClick={handleSkip}
              className="btn-skip"
              disabled={loading}
            >
              Skip for Now
            </button>
            <button
              type="submit"
              className="btn-complete"
              disabled={loading}
            >
              {loading ? 'Completing...' : 'Complete Registration'}
            </button>
          </div>
        </form>

        {/* Available Payment Methods Info */}
        {paymentMethods.length > 0 && (
          <div className="payment-methods-info">
            <h4>Available Payment Methods</h4>
            <div className="payment-methods-grid">
              {paymentMethods.slice(0, 4).map((method) => (
                <div key={method.value} className="payment-method-card">
                  <div className="payment-method-icon">
                    {getPaymentMethodIcon(method.icon)}
                  </div>
                  <div className="payment-method-details">
                    <strong>{method.name}</strong>
                    <small>{method.processing_time}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Helper function to get payment method icons
const getPaymentMethodIcon = (iconName) => {
  const icons = {
    'credit-card': '💳',
    'debit-card': '💳',
    'paypal': '🅿️',
    'apple-pay': '🍎',
    'google-pay': '🅶',
    'bank-transfer': '🏦',
    'crypto': '₿'
  };
  return icons[iconName] || '💳';
};

export default RegistrationCompletion;
