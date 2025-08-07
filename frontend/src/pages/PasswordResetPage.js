import React, { useState } from "react";
import axios from "../utils/axios";

function PasswordResetPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await axios.post("/auth/password-reset", { email });
      setSent(true);
    } catch (err) {
      setError("Failed to send password reset email. Please try again.");
    }
  };

  return (
    <div className="form-container">
      <h2 className="form-title">Password Reset</h2>
      {sent && <div className="success-message">Check your email for reset instructions.</div>}
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">Email</label>
          <input
            type="email"
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <button type="submit" className="form-button">Send Reset Email</button>
      </form>
    </div>
  );
}

export default PasswordResetPage;
