import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "../utils/axios";
import { useAuth } from "../hooks/useAuth";
import "../styles/SoundDetailPage.css";

function SoundDetailPage() {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [sound, setSound] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscribing, setSubscribing] = useState(false);
  const audioRef = useRef(null);

  const checkSubscription = React.useCallback(async () => {
    try {
      const res = await axios.get("/subscriptions");
      const subscribed = res.data.some(sub => sub.sound_id === parseInt(id));
      setIsSubscribed(subscribed);
    } catch (err) {
      console.error("Failed to check subscription:", err);
    }
  }, [id]);

  useEffect(() => {
    // Fetch sound details
    axios.get(`/sounds/${id}`)
      .then(res => {
        setSound(res.data);
        setLoading(false);
        
        // Check if user is subscribed to this sound
        if (isAuthenticated) {
          checkSubscription();
        }
      })
      .catch(err => {
        console.error("Failed to load sound details:", err);
        setError("Failed to load sound details. Please try again later.");
        setLoading(false);
      });
  }, [id, isAuthenticated, checkSubscription]);

  const handleSubscribe = async () => {
    if (!isAuthenticated) {
      navigate("/login", { state: { from: `/sounds/${id}` } });
      return;
    }

    setSubscribing(true);
    try {
      await axios.post("/subscriptions", { sound_id: id });
      setIsSubscribed(true);
      setSubscribing(false);
    } catch (err) {
      console.error("Failed to subscribe:", err);
      setSubscribing(false);
    }
  };

  const handlePlay = () => {
    if (audioRef.current) {
      audioRef.current.play();
    }
  };

  if (loading) return <div className="loading">Loading sound details...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!sound) return <div className="error">Sound not found.</div>;

  return (
    <div className="sound-detail-container">
      <div className="sound-header">
        <h1>{sound.title}</h1>
        <span className="category-tag">{sound.category.name}</span>
      </div>

      <div className="sound-info">
        <div className="sound-image">
          {sound.image_url ? (
            <img src={sound.image_url} alt={sound.title} />
          ) : (
            <div className="placeholder-image">🎵</div>
          )}
        </div>
        
        <div className="sound-description">
          <p>{sound.description}</p>
          <div className="sound-metadata">
            <p><strong>Duration:</strong> {sound.duration_seconds} seconds</p>
            {sound.tags && sound.tags.length > 0 && (
              <div className="sound-tags">
                <strong>Tags:</strong>
                {sound.tags.map(tag => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="sound-actions">
        {isSubscribed ? (
          <div className="audio-player">
            <h3>Listen to this therapeutic sound</h3>
            <audio 
              ref={audioRef}
              controls
              src={`/api/v1/sounds/stream/${id}`}
              onError={() => setError("Failed to load audio. Please try again.")}
            />
            <button onClick={handlePlay} className="play-button">
              Play Audio
            </button>
          </div>
        ) : (
          <div className="subscription-prompt">
            <h3>Subscribe to access this therapeutic sound</h3>
            <p>Unlock this sound and start your healing journey today.</p>
            <button 
              onClick={handleSubscribe} 
              disabled={subscribing}
              className="subscribe-button"
            >
              {subscribing ? "Processing..." : "Subscribe Now"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default SoundDetailPage;
