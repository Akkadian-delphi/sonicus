import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI
      return (
        <div style={{ 
          padding: '20px', 
          textAlign: 'center', 
          backgroundColor: '#f8f9fa',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <h1 style={{ color: '#dc3545', marginBottom: '20px' }}>
            Oops! Something went wrong
          </h1>
          <div style={{ 
            backgroundColor: 'white', 
            padding: '20px', 
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            maxWidth: '600px',
            textAlign: 'left'
          }}>
            <h3>Error Details:</h3>
            <pre style={{ 
              backgroundColor: '#f8f9fa', 
              padding: '10px', 
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '12px'
            }}>
              {this.state.error && this.state.error.toString()}
            </pre>
            
            <h3>Component Stack:</h3>
            <pre style={{ 
              backgroundColor: '#f8f9fa', 
              padding: '10px', 
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '12px'
            }}>
              {this.state.errorInfo ? this.state.errorInfo.componentStack : 'No component stack available'}
            </pre>
          </div>
          
          <button 
            onClick={() => window.location.reload()} 
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Reload Page
          </button>
          
          <div style={{ marginTop: '20px', color: '#6c757d', fontSize: '14px' }}>
            <p>If this error persists, please check:</p>
            <ul style={{ textAlign: 'left', maxWidth: '400px' }}>
              <li>Authentik authentication configuration in your .env file</li>
              <li>Backend API is running</li>
              <li>Network connectivity</li>
              <li>Browser console for more details</li>
            </ul>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
