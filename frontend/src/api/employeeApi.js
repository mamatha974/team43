import { httpJson } from './http.js'

/**
 * Fetch list of employees with optional filters
 */
export function apiGetEmployees({ token, status, search, sortBy, order }) {
  const params = new URLSearchParams()
  if (status) params.append('status', status)
  if (search) params.append('search', search)
  if (sortBy) params.append('sort_by', sortBy)
  if (order) params.append('order', order)

  const path = `/api/employees${params.toString() ? '?' + params : ''}`
  return httpJson(path, {
    method: 'GET',
    token,
  })
}

/**
 * Create a new employee
 */
export function apiCreateEmployee({
  token,
  emp_id,
  first_name,
  last_name,
  email,
  phone,
  department,
  position,
  start_date,
}) {
  return httpJson('/api/employees/create', {
    method: 'POST',
    token,
    body: {
      emp_id,
      first_name,
      last_name,
      email,
      phone,
      department,
      position,
      start_date,
    },
  })
}

/**
 * Get employee details by emp_id
 */
export function apiGetEmployee({ token, emp_id }) {
  return httpJson(`/api/employees/${emp_id}`, {
    method: 'GET',
    token,
  })
}

/**
 * Get unified employee profile by emp_id
 */
export function apiGetEmployeeProfile({ token, emp_id }) {
  return httpJson(`/api/employees/${emp_id}/profile`, {
    method: 'GET',
    token,
  })
}

export function apiGetOnboarding({ token, emp_id }) {
  return httpJson(`/api/employees/${emp_id}/onboarding`, {
    method: 'GET',
    token,
  })
}

export function apiUpdateOnboardingItem({ token, emp_id, item_id, is_completed, document_ref }) {
  return httpJson(`/api/employees/${emp_id}/onboarding`, {
    method: 'POST',
    token,
    body: { item_id, is_completed, document_ref },
  })
}

export function apiGetOnboardingProgress({ token }) {
  return httpJson('/api/onboarding/progress', {
    method: 'GET',
    token,
  })
}

export function apiGetRoleChanges({ token, emp_id }) {
  return httpJson(`/api/employees/${emp_id}/role-changes`, {
    method: 'GET',
    token,
  })
}

export function apiAddRoleChange({ token, emp_id, payload }) {
  return httpJson(`/api/employees/${emp_id}/role-changes`, {
    method: 'POST',
    token,
    body: payload,
  })
}

export function apiGetExitWorkflow({ token, emp_id }) {
  return httpJson(`/api/employees/${emp_id}/exit-workflow`, {
    method: 'GET',
    token,
  })
}

export function apiSaveExitWorkflow({ token, emp_id, payload }) {
  return httpJson(`/api/employees/${emp_id}/exit-workflow`, {
    method: 'POST',
    token,
    body: payload,
  })
}

export function apiGetEmployeeDocuments({ token, emp_id }) {
  return httpJson(`/api/employees/${emp_id}/documents`, {
    method: 'GET',
    token,
  })
}

export function apiAddEmployeeDocument({ token, emp_id, payload }) {
  return httpJson(`/api/employees/${emp_id}/documents`, {
    method: 'POST',
    token,
    body: payload,
  })
}

export function apiUpdateDocumentStatus({ token, emp_id, doc_id, payload }) {
  return httpJson(`/api/employees/${emp_id}/documents/${doc_id}/status`, {
    method: 'POST',
    token,
    body: payload,
  })
}

export function apiGetComplianceDashboard({ token }) {
  return httpJson('/api/compliance/dashboard', {
    method: 'GET',
    token,
  })
}

export function apiGetComplianceAlerts({ token }) {
  return httpJson('/api/compliance/alerts', {
    method: 'GET',
    token,
  })
}

export function apiGetHeadcountReport({ token }) {
  return httpJson('/api/reports/headcount', {
    method: 'GET',
    token,
  })
}

export function apiGetJoinersLeaversReport({ token, start, end }) {
  const params = new URLSearchParams()
  if (start) params.append('start', start)
  if (end) params.append('end', end)
  return httpJson(`/api/reports/joiners-leavers${params.toString() ? `?${params}` : ''}`, {
    method: 'GET',
    token,
  })
}

export function apiGetCTCLevelDistribution({ token }) {
  return httpJson('/api/reports/ctc-level-distribution', {
    method: 'GET',
    token,
  })
}

export function apiGetComplianceStatusReport({ token, status, docType }) {
  const params = new URLSearchParams()
  if (status) params.append('status', status)
  if (docType) params.append('doc_type', docType)
  return httpJson(`/api/reports/compliance-status${params.toString() ? `?${params}` : ''}`, {
    method: 'GET',
    token,
  })
}

/**
 * Update employee details
 */
export function apiUpdateEmployee({ token, emp_id, ...updates }) {
  return httpJson(`/api/employees/${emp_id}`, {
    method: 'PUT',
    token,
    body: updates,
  })
}

/**
 * Exit/deactivate an employee
 */
export function apiExitEmployee({ token, emp_id, end_date }) {
  return httpJson(`/api/employees/${emp_id}/exit`, {
    method: 'POST',
    token,
    body: { end_date },
  })
}
