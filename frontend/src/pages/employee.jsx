import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import {
  apiGetEmployees,
  apiCreateEmployee,
  apiUpdateEmployee,
  apiExitEmployee,
} from '../api/employeeApi.js'
import '../styles/Employee.css'

function EmployeePage() {
  const navigate = useNavigate()
  const { token } = useAuth()
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState('create') // create or edit
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [statusFilter, setStatusFilter] = useState('active')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortField, setSortField] = useState('') // "name" or "start_date"
  const [sortOrder, setSortOrder] = useState('asc')

  // Form state
  const [formData, setFormData] = useState({
    emp_id: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    department: '',
    position: '',
    start_date: '',
  })

  const [exitData, setExitData] = useState({
    emp_id: '',
    end_date: '',
  })
  const [showExitModal, setShowExitModal] = useState(false)

  // Fetch employees on mount and when filters change
  useEffect(() => {
    fetchEmployees()
  }, [statusFilter, searchTerm, sortField, sortOrder])

  async function fetchEmployees() {
    try {
      setLoading(true)
      setError(null)
      const result = await apiGetEmployees({
        token,
        status: statusFilter,
        search: searchTerm,
        sortBy: sortField,
        order: sortOrder,
      })
      setEmployees(result.employees || [])
    } catch (err) {
      setError(err.message || 'Failed to fetch employees')
    } finally {
      setLoading(false)
    }
  }

  function resetForm() {
    setFormData({
      emp_id: '',
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      department: '',
      position: '',
      start_date: '',
    })
  }

  function openCreateModal() {
    resetForm()
    setModalMode('create')
    setSelectedEmployee(null)
    setShowModal(true)
  }

  function openEditModal(employee) {
    setFormData({
      emp_id: employee.emp_id,
      first_name: employee.first_name,
      last_name: employee.last_name,
      email: employee.email,
      phone: employee.phone,
      department: employee.department,
      position: employee.position,
      start_date: employee.start_date,
    })
    setSelectedEmployee(employee)
    setModalMode('edit')
    setShowModal(true)
  }

  function openExitModal(employee) {
    setExitData({
      emp_id: employee.emp_id,
      end_date: '',
    })
    setSelectedEmployee(employee)
    setShowExitModal(true)
  }

  function handleFormChange(e) {
    const { name, value } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    
    try {
      setError(null)
      setSuccess(null)

      // Validate required fields
      if (
        !formData.emp_id ||
        !formData.first_name ||
        !formData.last_name ||
        !formData.email ||
        !formData.department ||
        !formData.position ||
        !formData.start_date
      ) {
        setError('All required fields must be filled')
        return
      }

      if (modalMode === 'create') {
        await apiCreateEmployee({
          token,
          ...formData,
        })
        setSuccess('Employee created successfully!')
      } else {
        // Update only changed fields
        const updates = {}
        Object.keys(formData).forEach((key) => {
          if (formData[key] !== selectedEmployee[key]) {
            updates[key] = formData[key]
          }
        })
        
        if (Object.keys(updates).length > 0) {
          await apiUpdateEmployee({
            token,
            emp_id: selectedEmployee.emp_id,
            ...updates,
          })
          setSuccess('Employee updated successfully!')
        } else {
          setSuccess('No changes made')
        }
      }

      setShowModal(false)
      resetForm()
      await fetchEmployees()
    } catch (err) {
      setError(err.message || 'Failed to save employee')
    }
  }

  async function handleExit(e) {
    e.preventDefault()

    try {
      setError(null)
      setSuccess(null)

      if (!exitData.end_date) {
        setError('End date is required')
        return
      }

      await apiExitEmployee({
        token,
        emp_id: exitData.emp_id,
        end_date: exitData.end_date,
      })

      setSuccess('Employee exited successfully!')
      setShowExitModal(false)
      await fetchEmployees()
    } catch (err) {
      setError(err.message || 'Failed to exit employee')
    }
  }

  return (
    <div className="employee-shell">
      <div className="employee-container">
        {/* Header */}
        <div className="employee-header">
          <h1>Employee Management</h1>
          <button className="btn-primary" onClick={openCreateModal}>
            <i className="bi bi-plus-lg" /> Add Employee
          </button>
        </div>

        {/* Alerts */}
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {/* Filters */}
        <div className="employee-filters">
          <div className="filter-group">
            <label>Status:</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="exited">Exited</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Search:</label>
            <input
              type="text"
              placeholder="Emp ID, Name, Email..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label>Sort by:</label>
            <select
              value={sortField}
              onChange={(e) => setSortField(e.target.value)}
            >
              <option value="">None</option>
              <option value="name">Name</option>
              <option value="start_date">Start Date</option>
            </select>
            {sortField && (
              <button
                className="btn-sort-order"
                type="button"
                onClick={() => setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'))}
                title="Toggle ascending/descending"
              >
                {sortOrder === 'asc' ? '↑' : '↓'}
              </button>
            )}
          </div>
        </div>

        {/* Employees Table */}
        {loading ? (
          <div className="loading">Loading employees...</div>
        ) : employees.length === 0 ? (
          <div className="empty-state">
            <p>No employees found</p>
          </div>
        ) : (
          <table className="employee-table">
            <thead>
              <tr>
                <th>Emp ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Department</th>
                <th>Position</th>
                <th>Start Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((emp) => (
                <tr key={emp.id}>
                  <td>{emp.emp_id}</td>
                  <td>{emp.full_name}</td>
                  <td>{emp.email}</td>
                  <td>{emp.department}</td>
                  <td>{emp.position}</td>
                  <td>{emp.start_date}</td>
                  <td>
                    <span className={`status-badge status-${emp.status}`}>
                      {emp.status}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <button
                      className="btn-sm btn-secondary"
                      onClick={() => navigate(`/employees/${emp.emp_id}/profile`)}
                    >
                      Profile
                    </button>
                    <button
                      className="btn-sm btn-edit"
                      onClick={() => openEditModal(emp)}
                    >
                      Edit
                    </button>
                    {emp.status === 'active' && (
                      <button
                        className="btn-sm btn-exit"
                        onClick={() => openExitModal(emp)}
                      >
                        Exit
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{modalMode === 'create' ? 'Add Employee' : 'Edit Employee'}</h2>
              <button
                type="button"
                className="modal-close"
                onClick={() => setShowModal(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSubmit} className="employee-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="emp_id">Employee ID *</label>
                  <input
                    type="text"
                    id="emp_id"
                    name="emp_id"
                    value={formData.emp_id}
                    onChange={handleFormChange}
                    disabled={modalMode === 'edit'}
                    placeholder="EMP001"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="first_name">First Name *</label>
                  <input
                    type="text"
                    id="first_name"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handleFormChange}
                    placeholder="John"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="last_name">Last Name *</label>
                  <input
                    type="text"
                    id="last_name"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handleFormChange}
                    placeholder="Doe"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="email">Email *</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleFormChange}
                    placeholder="john.doe@company.com"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="phone">Phone</label>
                  <input
                    type="tel"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleFormChange}
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="department">Department *</label>
                  <input
                    type="text"
                    id="department"
                    name="department"
                    value={formData.department}
                    onChange={handleFormChange}
                    placeholder="Engineering"
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="position">Position *</label>
                  <input
                    type="text"
                    id="position"
                    name="position"
                    value={formData.position}
                    onChange={handleFormChange}
                    placeholder="Senior Developer"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="start_date">Start Date *</label>
                  <input
                    type="date"
                    id="start_date"
                    name="start_date"
                    value={formData.start_date}
                    onChange={handleFormChange}
                    required
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {modalMode === 'create' ? 'Create' : 'Update'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Exit Modal */}
      {showExitModal && (
        <div className="modal-overlay" onClick={() => setShowExitModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Exit Employee</h2>
              <button
                type="button"
                className="modal-close"
                onClick={() => setShowExitModal(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleExit} className="employee-form">
              <p className="confirmation-text">
                Are you sure you want to mark <strong>{selectedEmployee?.full_name}</strong> as exited?
              </p>

              <div className="form-group">
                <label htmlFor="end_date">Exit Date *</label>
                <input
                  type="date"
                  id="end_date"
                  value={exitData.end_date}
                  onChange={(e) =>
                    setExitData({
                      ...exitData,
                      end_date: e.target.value,
                    })
                  }
                  required
                />
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowExitModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-danger">
                  Confirm Exit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default EmployeePage
