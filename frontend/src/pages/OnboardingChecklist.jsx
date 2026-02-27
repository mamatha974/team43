import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiGetEmployees, apiGetOnboarding, apiGetOnboardingProgress, apiUpdateOnboardingItem } from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function OnboardingChecklistPage() {
  const { token } = useAuth()
  const [employees, setEmployees] = useState([])
  const [empId, setEmpId] = useState('')
  const [onboarding, setOnboarding] = useState(null)
  const [progress, setProgress] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    loadEmployees()
    loadProgress()
  }, [])

  useEffect(() => {
    if (empId) loadOnboarding(empId)
  }, [empId])

  async function loadEmployees() {
    const data = await apiGetEmployees({ token, status: 'active' })
    const rows = data.employees || []
    setEmployees(rows)
    if (!empId && rows.length) setEmpId(rows[0].emp_id)
  }

  async function loadProgress() {
    const data = await apiGetOnboardingProgress({ token })
    setProgress(data.progress || [])
  }

  async function loadOnboarding(targetEmpId) {
    try {
      setError('')
      const data = await apiGetOnboarding({ token, emp_id: targetEmpId })
      setOnboarding(data)
    } catch (err) {
      setError(err.message || 'Failed to load checklist')
    }
  }

  async function markItem(item, isCompleted) {
    await apiUpdateOnboardingItem({
      token,
      emp_id: empId,
      item_id: item.id,
      is_completed: isCompleted,
      document_ref: item.document_ref || '',
    })
    await loadOnboarding(empId)
    await loadProgress()
  }

  async function attachDocument(item, value) {
    await apiUpdateOnboardingItem({
      token,
      emp_id: empId,
      item_id: item.id,
      document_ref: value,
    })
    await loadOnboarding(empId)
    await loadProgress()
  }

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>Onboarding Checklist</h1>
            <p>Track document collection and completion progress per employee.</p>
            <div className="schema-snippet">
              table: <span className="key">emp_master</span><br />
              emp_id int UN PK | first_name varchar(50) | middle_name varchar(50) | last_name varchar(50) | start_date date | end_date date
            </div>
          </div>
        </div>

        {error ? <div className="task-card" style={{ color: '#b12d2d' }}>{error}</div> : null}

        <div className="task-card task-controls">
          <select className="task-select" value={empId} onChange={(e) => setEmpId(e.target.value)}>
            {employees.map((e) => (
              <option key={e.emp_id} value={e.emp_id}>{e.emp_id} - {e.full_name}</option>
            ))}
          </select>
          <div>
            <strong>
              Completion: {onboarding?.completed_count || 0}/{onboarding?.total_count || 0}
            </strong>
            <div className="task-progress" style={{ marginTop: '8px' }}>
              <div style={{ width: `${onboarding?.progress_percentage || 0}%` }} />
            </div>
          </div>
        </div>

        <div className="task-grid">
          <div className="task-card">
            <h3>Checklist Items</h3>
            <div className="task-list">
              {(onboarding?.items || []).map((item) => (
                <div className="task-item" key={item.id}>
                  <div>
                    <div><strong>{item.item_name}</strong></div>
                    <div className="task-muted">Document: {item.document_ref || 'Not provided'}</div>
                  </div>
                  <div style={{ display: 'grid', gap: '6px' }}>
                    <button className="task-btn secondary" onClick={() => markItem(item, !item.is_completed)}>
                      {item.is_completed ? 'Mark Pending' : 'Mark Complete'}
                    </button>
                    <input
                      className="task-input"
                      placeholder="Document ref"
                      defaultValue={item.document_ref || ''}
                      onBlur={(e) => attachDocument(item, e.target.value)}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="task-card">
            <h3>HR Progress View</h3>
            <table className="task-table">
              <thead>
                <tr>
                  <th>Emp ID</th>
                  <th>Name</th>
                  <th>Progress</th>
                </tr>
              </thead>
              <tbody>
                {progress.map((row) => (
                  <tr key={row.emp_id}>
                    <td>{row.emp_id}</td>
                    <td>{row.full_name}</td>
                    <td>{row.progress_percentage}% ({row.completed_count}/{row.total_count})</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OnboardingChecklistPage
