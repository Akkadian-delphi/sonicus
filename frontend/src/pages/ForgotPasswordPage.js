import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../utils/axios';
import '../styles/ForgotPasswordPage.css';

const ForgotPasswordPage = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [submitted, setSubmitted] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setMessage('');

        try {
            const response = await axios.post('/auth/forgot-password', {
                email: email
            });

            setMessage(response.data.message);
            setSubmitted(true);
        } catch (err) {
            if (err.response?.status === 429) {
                setError('Too many requests. Please try again later.');
            } else {
                setError(err.response?.data?.detail || 'An error occurred. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    if (submitted) {
        return (
            <div className="forgot-password-container">
                <div className="forgot-password-card success-card">
                    <div className="success-icon">📧</div>
                    <h2>Check Your Email</h2>
                    <p className="success-message">{message}</p>
                    <p className="help-text">
                        If you don't see the email in your inbox, please check your spam folder.
                    </p>
                    <div className="action-buttons">
                        <button 
                            onClick={() => navigate('/login')} 
                            className="btn btn-primary"
                        >
                            Back to Login
                        </button>
                        <button 
                            onClick={() => {
                                setSubmitted(false);
                                setEmail('');
                                setMessage('');
                            }}
                            className="btn btn-secondary"
                        >
                            Send Another Email
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="forgot-password-container">
            <div className="forgot-password-card">
                <div className="logo">🎵 Sonicus</div>
                <h2>Forgot Password</h2>
                <p className="subtitle">
                    Enter your email address and we'll send you a link to reset your password.
                </p>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="email">Email Address</label>
                        <input
                            type="email"
                            id="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            placeholder="Enter your email address"
                            disabled={loading}
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button 
                        type="submit" 
                        className="btn btn-primary btn-full"
                        disabled={loading}
                    >
                        {loading ? 'Sending...' : 'Send Reset Link'}
                    </button>
                </form>

                <div className="forgot-password-footer">
                    <p>
                        Remember your password?{' '}
                        <button 
                            onClick={() => navigate('/login')}
                            className="link-button"
                        >
                            Back to Login
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ForgotPasswordPage;
