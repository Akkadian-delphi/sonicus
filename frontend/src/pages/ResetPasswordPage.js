import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from '../utils/axios';
import '../styles/ResetPasswordPage.css';

const ResetPasswordPage = () => {
    const [searchParams] = useSearchParams();
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState(false);
    const [tokenValid, setTokenValid] = useState(true);
    const navigate = useNavigate();

    const token = searchParams.get('token');

    useEffect(() => {
        if (!token) {
            setTokenValid(false);
            setError('Invalid or missing reset token');
        }
    }, [token]);

    const validatePassword = (pass) => {
        if (pass.length < 8) {
            return 'Password must be at least 8 characters long';
        }
        if (!/(?=.*[a-z])/.test(pass)) {
            return 'Password must contain at least one lowercase letter';
        }
        if (!/(?=.*[A-Z])/.test(pass)) {
            return 'Password must contain at least one uppercase letter';
        }
        if (!/(?=.*\d)/.test(pass)) {
            return 'Password must contain at least one number';
        }
        return null;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // Validate password
        const passwordError = validatePassword(password);
        if (passwordError) {
            setError(passwordError);
            setLoading(false);
            return;
        }

        // Check password confirmation
        if (password !== confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        try {
            // eslint-disable-next-line no-unused-vars
            const response = await axios.post('/auth/reset-password', {
                reset_token: token,
                new_password: password
            });

            setSuccess(true);
        } catch (err) {
            if (err.response?.status === 400) {
                setError('Invalid or expired reset token. Please request a new password reset.');
                setTokenValid(false);
            } else {
                setError(err.response?.data?.detail || 'An error occurred. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="reset-password-container">
                <div className="reset-password-card success-card">
                    <div className="success-icon">✅</div>
                    <h2>Password Reset Successful</h2>
                    <p className="success-message">
                        Your password has been successfully reset. You can now log in with your new password.
                    </p>
                    <button 
                        onClick={() => navigate('/login')}
                        className="btn btn-primary"
                    >
                        Go to Login
                    </button>
                </div>
            </div>
        );
    }

    if (!tokenValid) {
        return (
            <div className="reset-password-container">
                <div className="reset-password-card error-card">
                    <div className="error-icon">❌</div>
                    <h2>Invalid Reset Link</h2>
                    <p className="error-message">
                        This password reset link is invalid or has expired.
                    </p>
                    <div className="action-buttons">
                        <button 
                            onClick={() => navigate('/forgot-password')}
                            className="btn btn-primary"
                        >
                            Request New Reset Link
                        </button>
                        <button 
                            onClick={() => navigate('/login')}
                            className="btn btn-secondary"
                        >
                            Back to Login
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="reset-password-container">
            <div className="reset-password-card">
                <div className="logo">🎵 Sonicus</div>
                <h2>Reset Your Password</h2>
                <p className="subtitle">
                    Enter your new password below.
                </p>

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="password">New Password</label>
                        <input
                            type="password"
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            autoComplete="new-password"
                            required
                            placeholder="Enter your new password"
                            disabled={loading}
                        />
                        <div className="password-requirements">
                            <p>Password must contain:</p>
                            <ul>
                                <li className={password.length >= 8 ? 'valid' : ''}>
                                    At least 8 characters
                                </li>
                                <li className={/(?=.*[a-z])/.test(password) ? 'valid' : ''}>
                                    One lowercase letter
                                </li>
                                <li className={/(?=.*[A-Z])/.test(password) ? 'valid' : ''}>
                                    One uppercase letter
                                </li>
                                <li className={/(?=.*\d)/.test(password) ? 'valid' : ''}>
                                    One number
                                </li>
                            </ul>
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="confirmPassword">Confirm New Password</label>
                        <input
                            type="password"
                            id="confirmPassword"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            autoComplete="new-password"
                            required
                            placeholder="Confirm your new password"
                            disabled={loading}
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button 
                        type="submit" 
                        className="btn btn-primary btn-full"
                        disabled={loading || !password || !confirmPassword}
                    >
                        {loading ? 'Resetting...' : 'Reset Password'}
                    </button>
                </form>

                <div className="reset-password-footer">
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

export default ResetPasswordPage;
