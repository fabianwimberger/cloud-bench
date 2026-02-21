import React from 'react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo)
  }

  handleReload = () => {
    window.location.reload()
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    if (this.props.onReset) {
      this.props.onReset()
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '2rem',
          maxWidth: '600px',
          margin: '2rem auto',
          textAlign: 'center',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
          <div style={{
            padding: '2rem',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px'
          }}>
            <h2 style={{ color: '#dc2626', marginTop: 0 }}>
              Something went wrong
            </h2>
            <p style={{ color: '#7f1d1d' }}>
              The dashboard encountered an error while loading benchmark data.
            </p>
            
            {this.state.error && (
              <details style={{ 
                margin: '1rem 0', 
                textAlign: 'left',
                backgroundColor: '#fff',
                padding: '1rem',
                borderRadius: '4px',
                fontSize: '0.875rem'
              }}>
                <summary style={{ cursor: 'pointer', color: '#374151' }}>
                  Error details
                </summary>
                <pre style={{ 
                  marginTop: '0.5rem',
                  overflow: 'auto',
                  color: '#dc2626'
                }}>
                  {this.state.error.toString()}
                </pre>
              </details>
            )}

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', marginTop: '1.5rem' }}>
              <button
                onClick={this.handleReload}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: '#dc2626',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.875rem'
                }}
              >
                Reload Page
              </button>
              <button
                onClick={this.handleReset}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'white',
                  color: '#374151',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.875rem'
                }}
              >
                Try Again
              </button>
            </div>

            <p style={{ 
              marginTop: '1.5rem', 
              fontSize: '0.875rem', 
              color: '#6b7280' 
            }}>
              If this persists, check that benchmark data exists in <code>data/benchmark-data.json</code>
            </p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
