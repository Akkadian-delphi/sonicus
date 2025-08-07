import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "../utils/axios";
import "../styles/SoundsPage.css";

function SoundsPage() {
  const [sounds, setSounds] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("");

  // Fetch sounds with optional search and category filters
  const fetchSounds = React.useCallback(() => {
    setLoading(true);
    let url = "/sounds";
    let params = {};
    
    if (searchTerm) params.search = searchTerm;
    if (selectedCategory) params.category = selectedCategory;
    
    axios.get(url, { params })
      .then(res => {
        setSounds(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load sounds:", err);
        setError("Failed to load therapy sounds. Please try again later.");
        setLoading(false);
      });
  }, [searchTerm, selectedCategory]);
  
  useEffect(() => {
    // Fetch categories
    axios.get("/sounds/categories")
      .then(res => setCategories(res.data))
      .catch(err => console.error("Failed to load categories:", err));
  
    // Fetch sounds
    fetchSounds();
  }, [fetchSounds]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchSounds();
  };

  const handleCategoryChange = (e) => {
    setSelectedCategory(e.target.value);
    // Immediately apply the category filter
    setTimeout(fetchSounds, 0);
  };

  if (loading) return <div className="loading">Loading sounds...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="sounds-container">
      <h1>Discover Therapeutic Sounds</h1>
      
      <div className="filters">
        <form className="search-form" onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Search sounds..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>
        
        <select 
          value={selectedCategory} 
          onChange={handleCategoryChange}
          className="category-select"
        >
          <option value="">All Categories</option>
          {categories.map(category => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
      </div>

      <div className="sounds-grid">
        {sounds.length === 0 ? (
          <p>No sounds found. Try adjusting your filters.</p>
        ) : (
          sounds.map(sound => (
            <div key={sound.id} className="sound-card">
              <div className="sound-image">
                {sound.image_url ? (
                  <img src={sound.image_url} alt={sound.title} />
                ) : (
                  <div className="placeholder-image">🎵</div>
                )}
              </div>
              <h3>{sound.title}</h3>
              <p className="category">{sound.category?.name}</p>
              <p className="description">{sound.description?.substring(0, 100)}...</p>
              <Link to={`/sounds/${sound.id}`} className="view-button">
                View Details
              </Link>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default SoundsPage;
