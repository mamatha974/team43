import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import { apiGetEmployeeProfile } from '../api/employeeApi.js'
import '../styles/EmployeeProfile.css'

function Field({ label, value }) {
  return (
    <div className="profile-field">
      <div className="profile-label">{label}</div>
      <div className="profile-value">{value || 'Not available'}</div>
    </div>
  )
}

function EmployeeProfilePage() {
  const { empId } = useParams()
  const { token } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [profile, setProfile] = useState(null)

  useEffect(() => {
    loadProfile()
  }, [empId])

  async function loadProfile() {
    setLoading(true)
    setError(null)
    try {
      const data = await apiGetEmployeeProfile({ token, emp_id: empId })
      setProfile(data.profile)
    } catch (err) {
      setError(err.message || 'Failed to load employee profile')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="profile-shell"><div className="profile-card">Loading employee profile...</div></div>
  }

  if (error) {
    return (
      <div className="profile-shell">
        <div className="profile-card">
          <div className="profile-error">{error}</div>
          <Link to="/employees" className="profile-link">Back to Employees</Link>
        </div>
      </div>
    )
  }

  const employee = profile?.employee || {}
  const bank = profile?.bank
  const compliance = profile?.compliance
  const ctcTimeline = profile?.ctc_timeline || []

  return (
    <div className="profile-shell">
      <div className="profile-container">
        <div className="profile-header">
          <div>
            <h1>{employee.full_name || 'Employee Profile'}</h1>
            <p>{employee.emp_id} · {employee.position} · {employee.department}</p>
          </div>
          <Link to="/employees" className="profile-link">Back to Employees</Link>
        </div>

        <div className="profile-grid">
          <section className="profile-card">
            <h2>Personal Details</h2>
            <Field label="Email" value={employee.email} />
            <Field label="Phone" value={employee.phone} />
            <Field label="Status" value={employee.status} />
            <Field label="Start Date" value={employee.start_date} />
            <Field label="End Date" value={employee.end_date} />
          </section>

          <section className="profile-card">
            <h2>Bank Details</h2>
            {bank ? (
              <>
                <Field label="Bank Name" value={bank.bank_name} />
                <Field label="Account Holder" value={bank.account_holder_name} />
                <Field label="Account Number" value={bank.account_number} />
                <Field label="IFSC" value={bank.ifsc_code} />
                <Field label="Branch" value={bank.branch_name} />
              </>
            ) : (
              <p className="profile-empty">Bank details are not available.</p>
            )}
          </section>

          <section className="profile-card">
            <h2>Compliance IDs</h2>
            {compliance ? (
              <>
                <Field label="PAN" value={compliance.pan_number} />
                <Field label="Aadhaar" value={compliance.aadhaar_number} />
                <Field label="UAN" value={compliance.uan_number} />
                <Field label="ESI" value={compliance.esi_number} />
              </>
            ) : (
              <p className="profile-empty">Compliance details are not available.</p>
            )}
          </section>

          <section className="profile-card profile-card-wide">
            <h2>CTC Timeline</h2>
            {ctcTimeline.length ? (
              <div className="timeline">
                {ctcTimeline.map((row, idx) => (
                  <div key={`${row.effective_from}-${idx}`} className="timeline-row">
                    <div className="timeline-date">{row.effective_from}</div>
                    <div className="timeline-ctc">CTC: INR {Number(row.annual_ctc || 0).toLocaleString()}</div>
                    <div className="timeline-var">Variable: INR {Number(row.variable_pay || 0).toLocaleString()}</div>
                    <div className="timeline-note">{row.notes || 'No notes'}</div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="profile-empty">CTC history is not available.</p>
            )}
          </section>
        </div>
      </div>
    </div>
  )
}

export default EmployeeProfilePage
