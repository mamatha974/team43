import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiGetComplianceDashboard } from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function ComplianceDashboardPage() {
  const { token } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    loadDashboard()
  }, [])

  async function loadDashboard() {
    try {
      setError('')
      const res = await apiGetComplianceDashboard({ token })
      setData(res)
    } catch (err) {
      setError(err.message || 'Failed to load dashboard')
    }
  }

  const metrics = data?.metrics || {}
  const gaps = data?.employees_with_gaps || []

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>Compliance Dashboard</h1>
            <p>Track missing docs, pending verifications, and employee compliance gaps.</p>
            <div className="schema-snippet">
              source: <span className="key">emp_compliance_master + emp_master</span><br />
              metrics: pending_count int | verified_count int | gap_count int | emp_id int UN
            </div>
          </div>
        </div>

        {error ? <div className="task-card" style={{ color: '#b12d2d' }}>{error}</div> : null}

        <div className="task-grid">
          <div className="task-card"><h3>Active Employees</h3><div>{metrics.active_employees || 0}</div></div>
          <div className="task-card"><h3>Employees With Gaps</h3><div>{metrics.employees_with_gaps || 0}</div></div>
          <div className="task-card"><h3>Pending Verifications</h3><div>{metrics.pending_verifications || 0}</div></div>
          <div className="task-card"><h3>Verified Documents</h3><div>{metrics.verified_documents || 0}</div></div>
        </div>

        <div className="task-card">
          <h3>Employee Compliance Gaps</h3>
          <table className="task-table">
            <thead>
              <tr>
                <th>Emp ID</th>
                <th>Name</th>
                <th>Missing Docs</th>
                <th>Pending Docs</th>
              </tr>
            </thead>
            <tbody>
              {gaps.map((g) => (
                <tr key={g.emp_id}>
                  <td>{g.emp_id}</td>
                  <td>{g.full_name}</td>
                  <td>{(g.missing_docs || []).join(', ') || '-'}</td>
                  <td>{(g.pending_docs || []).join(', ') || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default ComplianceDashboardPage
