import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiGetHeadcountReport } from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function HeadcountReportPage() {
  const { token } = useAuth()
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    loadReport()
  }, [])

  async function loadReport() {
    try {
      setError('')
      const data = await apiGetHeadcountReport({ token })
      setSummary(data.summary)
    } catch (err) {
      setError(err.message || 'Failed to load headcount report')
    }
  }

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>Headcount Report</h1>
            <p>Real-time view of total, active, and exited employee counts.</p>
            <div className="schema-snippet">
              table: <span className="key">emp_master</span><br />
              total_count int | active_count int | exited_count int
            </div>
          </div>
          <button className="task-btn" onClick={loadReport}>Refresh</button>
        </div>

        {error ? <div className="task-card" style={{ color: '#b12d2d' }}>{error}</div> : null}

        <div className="task-grid">
          <div className="task-card"><h3>Total Employees</h3><div>{summary?.total_employees ?? 0}</div></div>
          <div className="task-card"><h3>Active Employees</h3><div>{summary?.active_employees ?? 0}</div></div>
          <div className="task-card"><h3>Exited Employees</h3><div>{summary?.exited_employees ?? 0}</div></div>
        </div>
      </div>
    </div>
  )
}

export default HeadcountReportPage
