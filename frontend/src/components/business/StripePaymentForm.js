/**
 * Stripe Payment Form Component
 * Handles subscription plan selection and payment setup
 */

import React, { useState } from 'react';
import './StripePaymentForm.css';

const StripePaymentForm = ({ formData, onChange, onNext, onBack }) => {
  const [selectedPlan, setSelectedPlan] = useState(formData.subscription_plan || 'starter');

  const plans = [
    {
      id: 'starter',
      name: 'Starter',
      price: 29,
      currency: 'EUR',
      interval: 'month',
      features: [
        'Up to 10 users',
        'Basic sound library',
        'Analytics dashboard',
        'Email support',
        '14-day free trial'
      ],
      popular: true
    },
    {
      id: 'professional',
      name: 'Professional',
      price: 79,
      currency: 'EUR',
      interval: 'month',
      features: [
        'Up to 50 users',
        'Premium sound library',
        'Advanced analytics',
        'Custom branding',
        'Priority support',
        'API access'
      ]
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: 199,
      currency: 'EUR',
      interval: 'month',
      features: [
        'Unlimited users',
        'Full sound library',
        'Advanced reporting',
        'White-label solution',
        'Dedicated support',
        'Custom integrations',
        'SLA guarantee'
      ]
    }
  ];

  const handlePlanSelect = (planId) => {
    setSelectedPlan(planId);
    onChange({ subscription_plan: planId });
  };

  const handleNext = () => {
    // For now, we'll skip actual payment processing during registration
    // Payment will be handled during the trial-to-paid conversion
    onChange({ 
      subscription_plan: selectedPlan,
      payment_method: 'trial' // Placeholder for trial
    });
    onNext();
  };

  const selectedPlanData = plans.find(plan => plan.id === selectedPlan);

  return (
    <div className="stripe-payment-form">
      <div className="step-header">
        <h2>Choose Your Plan</h2>
        <p>Start with a 14-day free trial. No credit card required.</p>
      </div>

      {/* Plan Selection */}
      <div className="plans-grid">
        {plans.map(plan => (
          <div
            key={plan.id}
            className={`plan-card ${selectedPlan === plan.id ? 'selected' : ''} ${plan.popular ? 'popular' : ''}`}
            onClick={() => handlePlanSelect(plan.id)}
          >
            {plan.popular && (
              <div className="popular-badge">Most Popular</div>
            )}
            
            <div className="plan-header">
              <h3>{plan.name}</h3>
              <div className="plan-price">
                <span className="currency">€</span>
                <span className="amount">{plan.price}</span>
                <span className="interval">/{plan.interval}</span>
              </div>
            </div>

            <div className="plan-features">
              {plan.features.map((feature, index) => (
                <div key={index} className="feature">
                  <span className="feature-icon">✓</span>
                  <span>{feature}</span>
                </div>
              ))}
            </div>

            <div className="plan-action">
              {selectedPlan === plan.id ? (
                <div className="selected-indicator">
                  <span className="check-icon">✓</span>
                  Selected
                </div>
              ) : (
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    handlePlanSelect(plan.id);
                  }}
                >
                  Select Plan
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Selected Plan Summary */}
      <div className="selected-plan-summary">
        <h3>Selected Plan: {selectedPlanData?.name}</h3>
        <div className="summary-details">
          <div className="price-info">
            <span>Monthly Price: </span>
            <strong>€{selectedPlanData?.price}/month</strong>
          </div>
          <div className="trial-info">
            <span>Free Trial: </span>
            <strong>14 days (no payment required now)</strong>
          </div>
          <div className="billing-info">
            <span>Billing starts: </span>
            <strong>After your free trial ends</strong>
          </div>
        </div>
      </div>

      {/* Trial Information */}
      <div className="trial-information">
        <h4>🎯 How the Free Trial Works</h4>
        <ul>
          <li>Start using Sonicus immediately with full features</li>
          <li>No credit card required for signup</li>
          <li>Full access to your selected plan features for 14 days</li>
          <li>Add payment method before trial expires to continue service</li>
          <li>Cancel anytime during trial with no charges</li>
        </ul>
      </div>

      {/* Payment Information Notice */}
      <div className="payment-notice">
        <div className="notice-content">
          <h4>💳 Payment Setup</h4>
          <p>
            You can add your payment method after registration through your organization dashboard. 
            We'll send you reminders before your trial expires.
          </p>
        </div>
      </div>

      {/* Step Actions */}
      <div className="step-actions">
        <button
          type="button"
          onClick={onBack}
          className="btn btn-secondary"
        >
          Back
        </button>
        <button
          type="button"
          onClick={handleNext}
          className="btn btn-primary"
        >
          Continue with {selectedPlanData?.name} Plan
        </button>
      </div>
    </div>
  );
};

export default StripePaymentForm;
