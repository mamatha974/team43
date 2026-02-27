import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiGetComplianceAlerts } from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function ComplianceAlertsPage() {
  const { token } = useAuth()
  const [alerts, setAlerts] = useState([])
  const [count, setCount] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    loadAlerts()
  }, [])

  async function loadAlerts() {
    try {
      setError('')
      const data = await apiGetComplianceAlerts({ token })
      setAlerts(data.alerts || [])
      setCount(data.count || 0)
    } catch (err) {
      setError(err.message || 'Failed to load alerts')
    }
  }

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>Alerts & Reminder System</h1>
            <p>Employee-wise reminders for missing documents and pending verifications.</p>
            <div className="schema-snippet">
              source: <span className="key">emp_compliance_master + emp_master</span><br />
              rule: status = pending OR doc_url is null | output: emp_id int UN | alert_type varchar(40) | message text
            </div>
          </div>
          <button className="task-btn" onClick={loadAlerts}>Refresh Alerts</button>
        </div>

        {error ? <div className="task-card" style={{ color: '#b12d2d' }}>{error}</div> : null}

        <div className="task-card"><strong>Total Alerts: {count}</strong></div>

        <div className="task-card">
          <table className="task-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Emp ID</th>
                <th>Name</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a, idx) => (
                <tr key={`${a.emp_id}-${a.type}-${idx}`}>
                  <td>{a.type}</td>
                  <td>{a.emp_id}</td>
                  <td>{a.employee_name}</td>
                  <td>{a.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default ComplianceAlertsPage
