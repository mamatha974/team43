import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiAddRoleChange, apiGetEmployees, apiGetRoleChanges } from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function RoleChangeTrackingPage() {
  const { token } = useAuth()
  const [employees, setEmployees] = useState([])
  const [empId, setEmpId] = useState('')
  const [timeline, setTimeline] = useState([])
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    role_title: '',
    role_level: '',
    annual_ctc: '',
    effective_from: '',
    effective_to: '',
    notes: '',
  })

  useEffect(() => {
    loadEmployees()
  }, [])

  useEffect(() => {
    if (empId) loadTimeline(empId)
  }, [empId])

  async function loadEmployees() {
    const data = await apiGetEmployees({ token })
    const rows = data.employees || []
    setEmployees(rows)
    if (!empId && rows.length) setEmpId(rows[0].emp_id)
  }

  async function loadTimeline(targetEmpId) {
    try {
      setError('')
      const data = await apiGetRoleChanges({ token, emp_id: targetEmpId })
      setTimeline(data.timeline || [])
    } catch (err) {
      setError(err.message || 'Failed to load role change timeline')
    }
  }

  async function onSubmit(e) {
    e.preventDefault()
    try {
      setError('')
      await apiAddRoleChange({ token, emp_id: empId, payload: form })
      setForm({
        role_title: '',
        role_level: '',
        annual_ctc: '',
        effective_from: '',
        effective_to: '',
        notes: '',
      })
      await loadTimeline(empId)
    } catch (err) {
      setError(err.message || 'Failed to add role change')
    }
  }

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>Job/Role Change Tracking</h1>
            <p>Track role, level and CTC changes with effective date ranges.</p>
            <div className="schema-snippet">
              table: <span className="key">emp_ctc_master</span><br />
              emp_ctc_id int UN PK | emp_id int UN | int_title varchar(30) | ext_title varchar(60) | main_level tinyint UN | sub_level char(1) | start_of_ctc date | end_of_ctc date | ctc_amt int UN
            </div>
          </div>
        </div>

        {error ? <div className="task-card" style={{ color: '#b12d2d' }}>{error}</div> : null}

        <div className="task-card">
          <div className="task-controls" style={{ marginBottom: '10px' }}>
            <select className="task-select" value={empId} onChange={(e) => setEmpId(e.target.value)}>
              {employees.map((e) => (
                <option key={e.emp_id} value={e.emp_id}>{e.emp_id} - {e.full_name}</option>
              ))}
            </select>
            <div className="task-muted">Timeline enforces non-overlapping dates per employee.</div>
          </div>

          <form onSubmit={onSubmit} className="task-grid">
            <input className="task-input" placeholder="Role title" value={form.role_title} onChange={(e) => setForm({ ...form, role_title: e.target.value })} required />
            <input className="task-input" placeholder="Role level" value={form.role_level} onChange={(e) => setForm({ ...form, role_level: e.target.value })} required />
            <input className="task-input" type="number" placeholder="Annual CTC" value={form.annual_ctc} onChange={(e) => setForm({ ...form, annual_ctc: e.target.value })} required />
            <input className="task-input" type="date" value={form.effective_from} onChange={(e) => setForm({ ...form, effective_from: e.target.value })} required />
            <input className="task-input" type="date" value={form.effective_to} onChange={(e) => setForm({ ...form, effective_to: e.target.value })} />
            <textarea className="task-textarea" placeholder="Notes" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            <div>
              <button className="task-btn" type="submit">Add Role Change</button>
            </div>
          </form>
        </div>

        <div className="task-card">
          <h3>Role/CTC Timeline</h3>
          <table className="task-table">
            <thead>
              <tr>
                <th>From</th>
                <th>To</th>
                <th>Role</th>
                <th>Level</th>
                <th>CTC</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {timeline.map((row) => (
                <tr key={row.id}>
                  <td>{row.effective_from}</td>
                  <td>{row.effective_to || 'Current'}</td>
                  <td>{row.role_title}</td>
                  <td>{row.role_level}</td>
                  <td>INR {Number(row.annual_ctc).toLocaleString()}</td>
                  <td>{row.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default RoleChangeTrackingPage
