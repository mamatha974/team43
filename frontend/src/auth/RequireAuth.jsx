import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext.jsx'

function RequireAuth({ children }) {
  const { user, status } = useAuth()
  const location = useLocation()

  if (status !== 'ready') {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'grid',
          placeItems: 'center',
          background: '#f1f4fb',
          color: '#1f2937',
          fontFamily: 'Mulish, sans-serif',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: 36,
              height: 36,
              margin: '0 auto 10px',
              borderRadius: '50%',
              border: '3px solid #cbd5e1',
              borderTopColor: '#2563eb',
              animation: 'spin 0.8s linear infinite',
            }}
          />
          <div>Loading session...</div>
        </div>
        <style>{'@keyframes spin { to { transform: rotate(360deg); } }'}</style>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/auth" replace state={{ from: location }} />
  }

  return children
}

export default RequireAuth
