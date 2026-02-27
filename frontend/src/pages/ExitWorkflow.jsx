import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiGetEmployees, apiGetExitWorkflow, apiSaveExitWorkflow } from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function ExitWorkflowPage() {
  const { token } = useAuth()
  const [employees, setEmployees] = useState([])
  const [empId, setEmpId] = useState('')
  const [exited, setExited] = useState([])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [form, setForm] = useState({
    last_working_day: '',
    reason: '',
    it_clearance: false,
    hr_clearance: false,
    finance_clearance: false,
    remarks: '',
  })

  useEffect(() => {
    loadEmployees()
    loadExited()
  }, [])

  useEffect(() => {
    if (empId) loadWorkflow(empId)
  }, [empId])

  async function loadEmployees() {
    const data = await apiGetEmployees({ token, status: 'active' })
    const rows = data.employees || []
    setEmployees(rows)
    if (!empId && rows.length) setEmpId(rows[0].emp_id)
  }

  async function loadExited() {
    const data = await apiGetEmployees({ token, status: 'exited' })
    setExited(data.employees || [])
  }

  async function loadWorkflow(targetEmpId) {
    try {
      const data = await apiGetExitWorkflow({ token, emp_id: targetEmpId })
      const workflow = data.workflow
      if (workflow) {
        setForm({
          last_working_day: workflow.last_working_day || '',
          reason: workflow.reason || '',
          it_clearance: !!workflow.it_clearance,
          hr_clearance: !!workflow.hr_clearance,
          finance_clearance: !!workflow.finance_clearance,
          remarks: workflow.remarks || '',
        })
      } else {
        setForm({
          last_working_day: '',
          reason: '',
          it_clearance: false,
          hr_clearance: false,
          finance_clearance: false,
          remarks: '',
        })
      }
    } catch (err) {
      setError(err.message || 'Failed to load exit workflow')
    }
  }

  async function onSubmit(e) {
    e.preventDefault()
    try {
      setError('')
      setSuccess('')
      await apiSaveExitWorkflow({ token, emp_id: empId, payload: form })
      setSuccess('Exit workflow saved and employee marked exited.')
      await loadEmployees()
      await loadExited()
    } catch (err) {
      setError(err.message || 'Failed to save exit workflow')
    }
  }

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>Exit Workflow Management</h1>
            <p>Capture last working day, clearances, and keep exited employees separated.</p>
            <div className="schema-snippet">
              table: <span className="key">emp_master</span><br />
              emp_id int UN PK | first_name varchar(50) | middle_name varchar(50) | last_name varchar(50) | start_date date | end_date date
            </div>
          </div>
        </div>

        {error ? <div className="task-card" style={{ color: '#b12d2d' }}>{error}</div> : null}
        {success ? <div className="task-card" style={{ color: '#1f7a4f' }}>{success}</div> : null}

        <div className="task-card">
          <form onSubmit={onSubmit}>
            <div className="task-controls" style={{ marginBottom: '10px' }}>
              <select className="task-select" value={empId} onChange={(e) => setEmpId(e.target.value)}>
                {employees.map((e) => (
                  <option key={e.emp_id} value={e.emp_id}>{e.emp_id} - {e.full_name}</option>
                ))}
              </select>
              <input
                className="task-input"
                type="date"
                value={form.last_working_day}
                onChange={(e) => setForm({ ...form, last_working_day: e.target.value })}
                required
              />
            </div>
            <div className="task-grid">
              <input className="task-input" placeholder="Exit reason" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} />
              <input className="task-input" placeholder="Remarks" value={form.remarks} onChange={(e) => setForm({ ...form, remarks: e.target.value })} />
            </div>
            <div style={{ display: 'flex', gap: '14px', margin: '10px 0' }}>
              <label><input type="checkbox" checked={form.it_clearance} onChange={(e) => setForm({ ...form, it_clearance: e.target.checked })} /> IT Clearance</label>
              <label><input type="checkbox" checked={form.hr_clearance} onChange={(e) => setForm({ ...form, hr_clearance: e.target.checked })} /> HR Clearance</label>
              <label><input type="checkbox" checked={form.finance_clearance} onChange={(e) => setForm({ ...form, finance_clearance: e.target.checked })} /> Finance Clearance</label>
            </div>
            <button className="task-btn" type="submit">Submit Exit</button>
          </form>
        </div>

        <div className="task-card">
          <h3>Exited Employees</h3>
          <table className="task-table">
            <thead>
              <tr>
                <th>Emp ID</th>
                <th>Name</th>
                <th>Department</th>
                <th>Last Working Day</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {exited.map((row) => (
                <tr key={row.id}>
                  <td>{row.emp_id}</td>
                  <td>{row.full_name}</td>
                  <td>{row.department}</td>
                  <td>{row.end_date || '-'}</td>
                  <td>{row.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default ExitWorkflowPage
