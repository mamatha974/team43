import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext.jsx'
import {
  apiAddEmployeeDocument,
  apiGetEmployeeDocuments,
  apiGetEmployees,
  apiUpdateDocumentStatus,
} from '../api/employeeApi.js'
import '../styles/TaskModules.css'

function DocumentVerificationPage() {
  const { token } = useAuth()
  const [employees, setEmployees] = useState([])
  const [empId, setEmpId] = useState('')
  const [documents, setDocuments] = useState([])
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    doc_type: '',
    doc_number: '',
    doc_link: '',
    remarks: '',
  })

  useEffect(() => {
    loadEmployees()
  }, [])

  useEffect(() => {
    if (empId) loadDocuments(empId)
  }, [empId])

  async function loadEmployees() {
    const data = await apiGetEmployees({ token })
    const rows = data.employees || []
    setEmployees(rows)
    if (!empId && rows.length) setEmpId(rows[0].emp_id)
  }

  async function loadDocuments(targetEmpId) {
    try {
      setError('')
      const data = await apiGetEmployeeDocuments({ token, emp_id: targetEmpId })
      setDocuments(data.documents || [])
    } catch (err) {
      setError(err.message || 'Failed to load documents')
    }
  }

  async function addDocument(e) {
    e.preventDefault()
    try {
      setError('')
      await apiAddEmployeeDocument({ token, emp_id: empId, payload: form })
      setForm({ doc_type: '', doc_number: '', doc_link: '', remarks: '' })
      await loadDocuments(empId)
    } catch (err) {
      setError(err.message || 'Failed to add document')
    }
  }

  async function setStatus(docId, status) {
    await apiUpdateDocumentStatus({ token, emp_id: empId, doc_id: docId, payload: { status } })
    await loadDocuments(empId)
  }

  return (
    <div className="task-shell">
      <div className="task-container">
        <div className="task-header">
          <div>
            <h1>Document Upload & Verification</h1>
            <p>Add compliance documents and update verification status.</p>
            <div className="schema-snippet">
              table: <span className="key">emp_compliance_master</span><br />
              emp_compliance_tracker_id int UN PK | emp_id int UN | comp_type varchar(60) | status varchar(20) | doc_url varchar(255)
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
            <div className="task-muted">Secure link storage uses document links mapped to employee records.</div>
          </div>

          <form onSubmit={addDocument} className="task-grid">
            <input className="task-input" placeholder="Doc type (PAN/AADHAAR/BANK_PROOF)" value={form.doc_type} onChange={(e) => setForm({ ...form, doc_type: e.target.value })} required />
            <input className="task-input" placeholder="Document number" value={form.doc_number} onChange={(e) => setForm({ ...form, doc_number: e.target.value })} />
            <input className="task-input" placeholder="Secure link (URL/path)" value={form.doc_link} onChange={(e) => setForm({ ...form, doc_link: e.target.value })} required />
            <input className="task-input" placeholder="Remarks" value={form.remarks} onChange={(e) => setForm({ ...form, remarks: e.target.value })} />
            <div><button type="submit" className="task-btn">Add/Update Document</button></div>
          </form>
        </div>

        <div className="task-card">
          <h3>Employee Documents</h3>
          <table className="task-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Number</th>
                <th>Link</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((d) => (
                <tr key={d.id}>
                  <td>{d.doc_type}</td>
                  <td>{d.doc_number || '-'}</td>
                  <td>{d.doc_link}</td>
                  <td>{d.status}</td>
                  <td>
                    <button className="task-btn secondary" onClick={() => setStatus(d.id, 'pending')}>Pending</button>{' '}
                    <button className="task-btn success" onClick={() => setStatus(d.id, 'verified')}>Verify</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default DocumentVerificationPage
