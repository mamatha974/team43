import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiGetComplianceStatusReport } from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function ComplianceStatusReportPage() {
  const { token } = useAuth()
  const [status, setStatus] = useState('')
  const [docType, setDocType] = useState('')
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    loadReport()
  }, [])

  async function loadReport() {
    try {
      setError('')
      const data = await apiGetComplianceStatusReport({ token, status, docType })
      setRows(data.rows || [])
    } catch (err) {
      setError(err.message || 'Failed to load compliance status report')
    }
  }

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>Compliance Status Report</h1>
            <p>Filter by status/type and view employee-wise compliance records.</p>
            <div className="schema-snippet">
              table: <span className="key">emp_compliance_master</span><br />
              emp_compliance_tracker_id int UN PK | emp_id int UN | comp_type varchar(60) | status varchar(20) | doc_url varchar(255)
            </div>
          </div>
        </div>
        {error ? <div className="task-card" style={{ color: '#b12d2d' }}>{error}</div> : null}
        <div className="task-card task-controls">
          <select className="task-select" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="verified">Verified</option>
            <option value="missing">Missing</option>
          </select>
          <select className="task-select" value={docType} onChange={(e) => setDocType(e.target.value)}>
            <option value="">All Types</option>
            <option value="PAN">PAN</option>
            <option value="AADHAAR">AADHAAR</option>
            <option value="BANK_PROOF">BANK_PROOF</option>
          </select>
          <button className="task-btn" onClick={loadReport}>Apply Filters</button>
        </div>
        <div className="task-card">
          <table className="task-table">
            <thead><tr><th>Emp ID</th><th>Name</th><th>Doc Type</th><th>Status</th><th>Link</th></tr></thead>
            <tbody>
              {rows.map((r, idx) => (
                <tr key={`${r.emp_id}-${r.doc_type}-${idx}`}>
                  <td>{r.emp_id}</td>
                  <td>{r.full_name}</td>
                  <td>{r.doc_type}</td>
                  <td>{r.status}</td>
                  <td>{r.doc_link || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default ComplianceStatusReportPage
