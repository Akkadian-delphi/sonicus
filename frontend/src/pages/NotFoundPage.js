import React from "react";
import { Link } from "react-router-dom";

function NotFoundPage() {
  return (
    <div className="container">
      <h1>404 - Page Not Found</h1>
      <p>The page you are looking for does not exist.</p>
      <Link to="/" className="form-link">Go back to Home</Link>
    </div>
  );
}

export default NotFoundPage;
