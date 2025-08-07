import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "../utils/axios";
import "../styles/SubscriptionsPage.css";

function SubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchSubscriptions();
  }, []);

  const fetchSubscriptions = async () => {
    try {
      const res = await axios.get("/subscriptions");
      setSubscriptions(res.data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load subscriptions:", err);
      setError("Failed to load your subscriptions. Please try again later.");
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading your subscriptions...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="subscriptions-container">
      <h1>Your Subscriptions</h1>
      
      {subscriptions.length === 0 ? (
        <div className="no-subscriptions">
          <p>You don't have any subscriptions yet.</p>
          <Link to="/" className="browse-button">Browse Sounds</Link>
        </div>
      ) : (
        <div className="subscriptions-list">
          {subscriptions.map(subscription => (
            <div key={subscription.id} className="subscription-card">
              <div className="subscription-info">
                <h3>{subscription.sound.title}</h3>
                <p>Category: {subscription.sound.category.name}</p>
                <p>Subscribed on: {new Date(subscription.created_at).toLocaleDateString()}</p>
                {subscription.expires_at && (
                  <p>Expires on: {new Date(subscription.expires_at).toLocaleDateString()}</p>
                )}
              </div>
              <div className="subscription-actions">
                <Link to={`/sounds/${subscription.sound_id}`} className="listen-button">
                  Listen Now
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SubscriptionsPage;
