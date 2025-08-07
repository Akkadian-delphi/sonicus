import React, { useState, useEffect } from 'react';

const MobileAdminNav = ({ activeTab, onTabChange, tabs }) => {
  const [isNavOpen, setIsNavOpen] = useState(false);

  // Simple touch handlers without external dependency
  const handlers = {
    onTouchStart: () => {},
    onTouchEnd: () => {}
  };

  return (
    <div className="mobile-admin-nav" {...handlers}>
      {/* Mobile hamburger menu */}
      <div className="mobile-nav-header d-md-none">
        <button
          className="btn navbar-toggler"
          onClick={() => setIsNavOpen(!isNavOpen)}
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>
        <h1 className="mobile-nav-title">Admin Panel</h1>
      </div>

      {/* Navigation tabs */}
      <nav className={`admin-nav-tabs ${isNavOpen ? 'show' : ''}`}>
        <div className="nav-tabs-container">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => {
                onTabChange(tab.id);
                setIsNavOpen(false); // Close mobile menu after selection
              }}
            >
              <span className="nav-tab-icon">{tab.icon}</span>
              <span className="nav-tab-text">{tab.label}</span>
              {tab.badge && (
                <>
                  {' '}
                  <span className="nav-tab-badge">{tab.badge}</span>
                </>
              )}
            </button>
          ))}
        </div>
      </nav>

      {/* Overlay for mobile */}
      {isNavOpen && (
        <div
          className="nav-overlay d-md-none"
          onClick={() => setIsNavOpen(false)}
        />
      )}
    </div>
  );
};

const TouchFriendlyCard = ({ children, className = '', onTap, ...props }) => {
  const [isPressed, setIsPressed] = useState(false);

  const handleTouchStart = () => setIsPressed(true);
  const handleTouchEnd = () => setIsPressed(false);

  return (
    <div
      className={`touch-card ${className} ${isPressed ? 'pressed' : ''}`}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleTouchStart}
      onMouseUp={handleTouchEnd}
      onMouseLeave={handleTouchEnd}
      onClick={onTap}
      {...props}
    >
      {children}
    </div>
  );
};

const SwipeableList = ({ items, onItemSelect, renderItem }) => {
  return (
    <div className="mobile-swipeable-list">
      {items.map((item, index) => (
        <div
          key={item.id || index}
          className="swipeable-list-item"
          onClick={() => onItemSelect && onItemSelect(item)}
        >
          {renderItem ? renderItem(item, index) : (
            <div className="list-item-content">
              <div className="item-title">{item.title || item.name}</div>
              <div className="item-subtitle">{item.subtitle || item.description}</div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const MobileSearchBar = ({ value, onChange, placeholder, onClear }) => {
  const [isFocused, setIsFocused] = useState(false);

  return (
    <div className={`mobile-search-bar ${isFocused ? 'focused' : ''}`}>
      <div className="search-input-container">
        <input
          type="search"
          className="form-control search-input"
          value={value}
          onChange={onChange}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          autoComplete="off"
        />
        {value && (
          <button
            className="btn search-clear-btn"
            onClick={onClear}
            aria-label="Clear search"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

const TouchFriendlyModal = ({ isOpen, onClose, title, children, size = 'md' }) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className={`touch-modal touch-modal-${size}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2 className="modal-title">{title}</h2>
          <button
            className="btn modal-close-btn"
            onClick={onClose}
            aria-label="Close modal"
          >
            ×
          </button>
        </div>
        <div className="modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};

const MobileDataTable = ({ data, columns, onRowAction }) => {
  const [viewMode, setViewMode] = useState('cards');

  return (
    <div className="mobile-data-table">
      <div className="table-controls">
        <div className="view-toggle">
          <button
            className={`btn btn-sm ${viewMode === 'cards' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setViewMode('cards')}
          >
            Cards
          </button>
          <button
            className={`btn btn-sm ${viewMode === 'table' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setViewMode('table')}
          >
            Table
          </button>
        </div>
      </div>

      {viewMode === 'cards' ? (
        <div className="data-cards">
          {data.map((row, index) => (
            <TouchFriendlyCard
              key={index}
              className="data-card"
              onTap={() => onRowAction && onRowAction('view', row)}
            >
              {columns.map((column) => (
                <div key={column.key} className="card-field">
                  <span className="field-label">{column.label}:</span>
                  <span className="field-value">
                    {column.render ? column.render(row[column.key], row) : row[column.key]}
                  </span>
                </div>
              ))}
              {onRowAction && (
                <div className="card-actions">
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRowAction('edit', row);
                    }}
                  >
                    Edit
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRowAction('delete', row);
                    }}
                  >
                    Delete
                  </button>
                </div>
              )}
            </TouchFriendlyCard>
          ))}
        </div>
      ) : (
        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column.key}>{column.label}</th>
                ))}
                {onRowAction && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {data.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => (
                    <td key={column.key}>
                      {column.render ? column.render(row[column.key], row) : row[column.key]}
                    </td>
                  ))}
                  {onRowAction && (
                    <td>
                      <div className="btn-group">
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => onRowAction('edit', row)}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => onRowAction('delete', row)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const FloatingActionButton = ({ actions, primaryAction }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className={`fab-container ${isExpanded ? 'expanded' : ''}`}>
      {actions && actions.map((action, index) => (
        <button
          key={index}
          className="btn btn-secondary fab-action"
          style={{ '--delay': `${index * 50}ms` }}
          onClick={() => {
            action.onClick();
            setIsExpanded(false);
          }}
          aria-label={action.label}
        >
          {action.icon}
        </button>
      ))}
      
      <button
        className="btn btn-primary fab-main"
        onClick={() => {
          if (actions && actions.length > 0) {
            setIsExpanded(!isExpanded);
          } else if (primaryAction) {
            primaryAction.onClick();
          }
        }}
        aria-label={primaryAction?.label || 'Actions'}
      >
        {isExpanded ? '×' : (primaryAction?.icon || '+')}
      </button>
    </div>
  );
};

export {
  MobileAdminNav,
  TouchFriendlyCard,
  SwipeableList,
  MobileSearchBar,
  TouchFriendlyModal,
  MobileDataTable,
  FloatingActionButton
};
