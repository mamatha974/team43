import { useState, useEffect } from 'react'
import { useAuth } from '../auth/AuthContext'

const EmployeeDirectory = () => {
  const { token } = useAuth()
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Search and filter states
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortBy, setSortBy] = useState('-created_at')
  
  const fetchEmployees = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      
      if (searchTerm) params.append('search', searchTerm)
      if (statusFilter !== 'all') params.append('status', statusFilter)
      params.append('sort_by', sortBy)
      
      const response = await fetch(`http://localhost:8000/api/employees?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch employees')
      }
      
      const data = await response.json()
      setEmployees(data.employees || [])
      setError('')
    } catch (err) {
      setError(err.message)
      setEmployees([])
    } finally {
      setLoading(false)
    }
  }
  
  useEffect(() => {
    if (token) {
      fetchEmployees()
    }
  }, [token, searchTerm, statusFilter, sortBy])
  
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString()
  }
  
  const getStatusBadge = (status) => {
    const baseClasses = 'px-3 py-1 rounded-full text-xs font-semibold'
    return status === 'active' 
      ? `${baseClasses} bg-emerald-100 text-emerald-800 border border-emerald-200`
      : `${baseClasses} bg-slate-100 text-slate-700 border border-slate-200`
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50" style={{ fontSize: '14px' }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 tracking-tight" style={{ fontSize: '1.8rem' }}>Employee Directory</h1>
              <p className="mt-1 text-base text-slate-600" style={{ fontSize: '0.95rem' }}>Search and filter employee information</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="bg-white px-4 py-2 rounded-lg shadow-sm border border-slate-200">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-slate-700">
                    {employees.length} {employees.length === 1 ? 'Employee' : 'Employees'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Search and Filters */}
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <label htmlFor="search" className="block text-sm font-semibold text-slate-700 mb-2">
                Search Employees
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-slate-400" width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  id="search"
                  placeholder="Search by name, ID, or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-slate-50 hover:bg-white"
                />
              </div>
            </div>
            
            {/* Status Filter */}
            <div>
              <label htmlFor="status" className="block text-sm font-semibold text-slate-700 mb-2">
                Status Filter
              </label>
              <select
                id="status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-slate-50 hover:bg-white appearance-none cursor-pointer"
              >
                <option value="all">All Employees</option>
                <option value="active">Active Only</option>
                <option value="exited">Exited Only</option>
              </select>
            </div>
            
            {/* Sort */}
            <div>
              <label htmlFor="sort" className="block text-sm font-semibold text-slate-700 mb-2">
                Sort By
              </label>
              <select
                id="sort"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 bg-slate-50 hover:bg-white appearance-none cursor-pointer"
              >
                <option value="-created_at">Recently Added</option>
                <option value="created_at">Oldest First</option>
                <option value="name">Name (A-Z)</option>
                <option value="-name">Name (Z-A)</option>
                <option value="start_date">Start Date (Oldest)</option>
                <option value="-start_date">Start Date (Newest)</option>
              </select>
            </div>
          </div>
        </div>
        
        {/* Loading State */}
        {loading && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-full shadow-lg mb-4">
              <div className="animate-spin rounded-full h-8 w-8 border-4 border-blue-600 border-t-transparent"></div>
            </div>
            <p className="text-lg font-medium text-slate-700">Loading employees...</p>
            <p className="text-sm text-slate-500 mt-1">Please wait while we fetch the data</p>
          </div>
        )}
        
        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 mb-8">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-600" width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Unable to load employees</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}
        
        {/* Empty State */}
        {!loading && !error && employees.length === 0 && (
          <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-12 text-center">
            <div className="mx-auto w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
              <svg className="h-8 w-8 text-slate-400" width="24" height="24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-slate-900 mb-2">No employees found</h3>
            <p className="text-slate-600">Try adjusting your search or filter criteria</p>
          </div>
        )}
        
        {/* Employee List */}
        {!loading && !error && employees.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
            {employees.map((employee) => (
              <div key={employee.id} className="bg-white rounded-lg shadow-md border border-slate-200 hover:shadow-lg transition-all duration-300 hover:scale-[1.01]">
                <div className="p-3">
                  {/* Employee Header */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-semibold text-[10px]" style={{ width: '24px', height: '24px', fontSize: '10px' }}>
                        {employee.first_name.charAt(0)}{employee.last_name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900 text-xs">{employee.full_name}</h3>
                        <p className="text-xs text-slate-500 font-mono">{employee.emp_id}</p>
                      </div>
                    </div>
                    <span className={getStatusBadge(employee.status)}>
                      {employee.status.charAt(0).toUpperCase() + employee.status.slice(1)}
                    </span>
                  </div>
                  
                  {/* Employee Details */}
                  <div className="space-y-1">
                    <div className="flex items-center space-x-1 text-xs">
                      <svg className="h-2 w-2 text-slate-400" width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-slate-700 truncate">{employee.email}</span>
                    </div>
                    
                    {employee.phone && (
                      <div className="flex items-center space-x-1 text-xs">
                        <svg className="h-2 w-2 text-slate-400" width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                        </svg>
                        <span className="text-slate-700">{employee.phone}</span>
                      </div>
                    )}
                    
                    <div className="flex items-center space-x-1 text-xs">
                      <svg className="h-2 w-2 text-slate-400" width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2V16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1V5m-4 0h4" />
                      </svg>
                      <div>
                        <p className="text-slate-900 font-medium text-xs">{employee.position}</p>
                        <p className="text-slate-500 text-xs">{employee.department}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-1 text-xs">
                      <svg className="h-2 w-2 text-slate-400" width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span className="text-slate-700">Started {formatDate(employee.start_date)}</span>
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="mt-2 pt-2 border-t border-slate-100 flex space-x-1">
                    <button className="flex-1 bg-blue-50 text-blue-700 px-2 py-1 rounded text-xs font-medium hover:bg-blue-100 transition-colors">
                      View Profile
                    </button>
                    <button className="flex-1 bg-slate-50 text-slate-700 px-2 py-1 rounded text-xs font-medium hover:bg-slate-100 transition-colors">
                      Edit
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default EmployeeDirectory
