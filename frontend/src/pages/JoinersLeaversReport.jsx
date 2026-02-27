import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiGetJoinersLeaversReport } from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function JoinersLeaversReportPage() {
  const { token } = useAuth()
  const [start, setStart] = useState('2025-01-01')
  const [end, setEnd] = useState('2026-12-31')
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    loadReport()
  }, [])

  async function loadReport() {
    try {
      setError('')
      const data = await apiGetJoinersLeaversReport({ token, start, end })
      setRows(data.monthly || [])
    } catch (err) {
      setError(err.message || 'Failed to load joiners/leavers report')
    }
  }

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>Joiners & Leavers Report</h1>
            <p>Month-wise hiring and attrition trends.</p>
            <div className="schema-snippet">
              table: <span className="key">emp_master</span><br />
              emp_id int UN PK | start_date date | end_date date | month_key char(7) | joiners_count int | leavers_count int
            </div>
          </div>
        </div>
        {error ? <div className="task-card" style={{ color: '#b12d2d' }}>{error}</div> : null}
        <div className="task-card task-controls">
          <input className="task-input" type="date" value={start} onChange={(e) => setStart(e.target.value)} />
          <input className="task-input" type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
          <button className="task-btn" onClick={loadReport}>Apply Range</button>
        </div>
        <div className="task-card">
          <table className="task-table">
            <thead><tr><th>Month</th><th>Joiners</th><th>Leavers</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.month}><td>{r.month}</td><td>{r.joiners}</td><td>{r.leavers}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default JoinersLeaversReportPage
