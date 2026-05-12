import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import Setup from './pages/Setup.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Tracker from './pages/Tracker.jsx'
import Chat from './pages/Chat.jsx'
import { api } from './api.js'

export default function App() {
  const [loading, setLoading] = useState(true)
  const [hasProfile, setHasProfile] = useState(false)
  const location = useLocation()

  useEffect(() => {
    api.getProfile()
      .then((p) => setHasProfile(Boolean(p?.user)))
      .catch(() => setHasProfile(false))
      .finally(() => setLoading(false))
  }, [location.pathname])

  if (loading) {
    return <div className="p-8 text-subtle">Loading…</div>
  }

  return (
    <div className="min-h-full">
      <header className="px-6 py-4 border-b border-muted flex items-center justify-between">
        <Link to="/" className="text-2xl font-semibold tracking-tight">
          Lumen
        </Link>
        <nav className="flex gap-4 text-sm text-subtle">
          <Link to="/" className="hover:text-text">Dashboard</Link>
          <Link to="/tracker" className="hover:text-text">Tracker</Link>
          <Link to="/chat" className="hover:text-text">Chat</Link>
          <Link to="/setup" className="hover:text-text">Settings</Link>
        </nav>
      </header>
      <main className="px-6 py-6 max-w-5xl mx-auto">
        <Routes>
          <Route path="/setup" element={<Setup />} />
          <Route
            path="/"
            element={hasProfile ? <Dashboard /> : <Navigate to="/setup" replace />}
          />
          <Route
            path="/tracker"
            element={hasProfile ? <Tracker /> : <Navigate to="/setup" replace />}
          />
          <Route
            path="/chat"
            element={hasProfile ? <Chat /> : <Navigate to="/setup" replace />}
          />
        </Routes>
      </main>
    </div>
  )
}
