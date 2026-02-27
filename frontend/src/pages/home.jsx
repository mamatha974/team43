import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import '../styles/Home.css'

function HomePage() {
  const navigate = useNavigate()
  const { member, signOut } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  const modules = [
    { to: '/employees', icon: 'bi-people-fill', title: 'Employee Directory', subtitle: 'Browse records', tone: 'tone-blue' },
    { to: '/employees/manage', icon: 'bi-person-plus-fill', title: 'Manage Employees', subtitle: 'Create, update, exit', tone: 'tone-green' },
    { to: '/onboarding', icon: 'bi-list-check', title: 'Onboarding Checklist', subtitle: 'Track completion', tone: 'tone-indigo' },
    { to: '/role-changes', icon: 'bi-diagram-3-fill', title: 'Role Change Tracking', subtitle: 'Track role/CTC changes', tone: 'tone-slate' },
    { to: '/exit-workflow', icon: 'bi-box-arrow-right', title: 'Exit Workflow', subtitle: 'Capture exits & clearances', tone: 'tone-red' },
    { to: '/document-verification', icon: 'bi-file-earmark-check', title: 'Document Verification', subtitle: 'Upload & verify docs', tone: 'tone-navy' },
    { to: '/compliance-dashboard', icon: 'bi-speedometer2', title: 'Compliance Dashboard', subtitle: 'Monitor compliance gaps', tone: 'tone-cobalt' },
    { to: '/alerts-reminders', icon: 'bi-bell-fill', title: 'Alerts & Reminders', subtitle: 'See pending alerts', tone: 'tone-amber' },
    { to: '/headcount-report', icon: 'bi-people', title: 'Headcount Report', subtitle: 'Total / active / exited', tone: 'tone-emerald' },
    { to: '/joiners-leavers-report', icon: 'bi-bar-chart-line-fill', title: 'Joiners & Leavers', subtitle: 'Monthly trends', tone: 'tone-cyan' },
    { to: '/ctc-level-distribution', icon: 'bi-pie-chart-fill', title: 'CTC & Level Distribution', subtitle: 'Salary band analytics', tone: 'tone-violet' },
    { to: '/compliance-status-report', icon: 'bi-clipboard-data-fill', title: 'Compliance Status Report', subtitle: 'Filter by type/status', tone: 'tone-charcoal' },
  ]

  useEffect(() => {
    function onDocMouseDown(e) {
      if (!menuRef.current) return
      if (!menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', onDocMouseDown)
    return () => document.removeEventListener('mousedown', onDocMouseDown)
  }, [])

  async function onLogout() {
    await signOut()
    navigate('/auth')
  }

  return (
    <div className="home-shell">
      <div className="home-topbar">
        <div className="dropdown" ref={menuRef}>
          <button
            className="home-userbtn"
            type="button"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <i className="bi bi-person-circle" />
          </button>

          <ul className={`dropdown-menu dropdown-menu-end home-dropdown${menuOpen ? ' show' : ''}`}>
            <li className="px-3 pt-2 pb-1">
              <div className="home-userline">
                <i className="bi bi-person-circle" />
                <div>
                  <div className="home-username">{member?.name || '--'}</div>
                  <div className="home-userdetail">{member?.email || '--'}</div>
                  <div className="home-userdetail">{member?.phone || '--'}</div>
                </div>
              </div>
            </li>
            <li><hr className="dropdown-divider" /></li>
            <li className="px-3 pb-3">
              <button className="btn btn-danger w-100" type="button" onClick={onLogout}>Logout</button>
            </li>
          </ul>
        </div>
      </div>

      <main className="home-center" aria-live="polite">
        <section className="home-hero">
          <span className="hero-chip">Hackathon Batch 3</span>
          <h1 className="home-title">People Operations Control Center</h1>
          <p className="home-subtitle">A colorful single workspace for employee lifecycle, compliance, alerts, and analytics.</p>
        </section>

        <div className="home-actions">
          {modules.map((module) => (
            <Link key={module.to} to={module.to} className={`home-module ${module.tone}`}>
              <div className="module-head">
                <i className={`bi ${module.icon}`} />
                <span>Open Module</span>
              </div>
              <div className="module-title">{module.title}</div>
              <div className="module-subtitle">{module.subtitle}</div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  )
}

export default HomePage
