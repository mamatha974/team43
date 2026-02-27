import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiGetCTCLevelDistribution } from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function CTCLevelDistributionPage() {
  const { token } = useAuth()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      setError('')
      const res = await apiGetCTCLevelDistribution({ token })
      setData(res)
    } catch (err) {
      setError(err.message || 'Failed to load distribution data')
    }
  }

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>CTC & Level Distribution Analytics</h1>
            <p>Distribution across salary bands and job levels.</p>
            <div className="schema-snippet">
              source: <span className="key">emp_ctc_master + emp_master</span><br />
              band varchar(20) | main_level tinyint UN | sub_level char(1) | employee_count int
            </div>
          </div>
        </div>
        {error ? <div className="task-card" style={{ color: '#b12d2d' }}>{error}</div> : null}
        <div className="task-grid">
          <div className="task-card">
            <h3>Salary Bands</h3>
            <table className="task-table">
              <tbody>
                {Object.entries(data?.salary_bands || {}).map(([k, v]) => (
                  <tr key={k}><td>{k}</td><td>{v}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="task-card">
            <h3>Level-wise Counts</h3>
            <table className="task-table">
              <tbody>
                {Object.entries(data?.level_counts || {}).map(([k, v]) => (
                  <tr key={k}><td>{k}</td><td>{v}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="task-card">
          <h3>Employee Distribution View</h3>
          <table className="task-table">
            <thead><tr><th>Emp ID</th><th>Name</th><th>Level</th><th>CTC</th><th>Band</th></tr></thead>
            <tbody>
              {(data?.employees || []).map((r) => (
                <tr key={r.emp_id}>
                  <td>{r.emp_id}</td>
                  <td>{r.full_name}</td>
                  <td>{r.level}</td>
                  <td>{r.annual_ctc}</td>
                  <td>{r.salary_band}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default CTCLevelDistributionPage
