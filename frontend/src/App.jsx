import { Navigate, Route, Routes } from 'react-router-dom'
import AuthPage from './pages/auth.jsx'
import HomePage from './pages/home.jsx'
import EmployeePage from './pages/employee.jsx'
import EmployeeProfilePage from './pages/EmployeeProfile.jsx'
import OnboardingChecklistPage from './pages/OnboardingChecklist.jsx'
import RoleChangeTrackingPage from './pages/RoleChangeTracking.jsx'
import ExitWorkflowPage from './pages/ExitWorkflow.jsx'
import DocumentVerificationPage from './pages/DocumentVerification.jsx'
import ComplianceDashboardPage from './pages/ComplianceDashboard.jsx'
import ComplianceAlertsPage from './pages/ComplianceAlerts.jsx'
import HeadcountReportPage from './pages/HeadcountReport.jsx'
import JoinersLeaversReportPage from './pages/JoinersLeaversReport.jsx'
import CTCLevelDistributionPage from './pages/CTCLevelDistribution.jsx'
import ComplianceStatusReportPage from './pages/ComplianceStatusReport.jsx'
import RequireAuth from './auth/RequireAuth.jsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/auth" replace />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/home"
        element={
          <RequireAuth>
            <HomePage />
          </RequireAuth>
        }
      />
      <Route
        path="/employees"
        element={
          <RequireAuth>
            <EmployeePage />
          </RequireAuth>
        }
      />
      <Route
        path="/employees/manage"
        element={
          <RequireAuth>
            <EmployeePage />
          </RequireAuth>
        }
      />
      <Route
        path="/employees/:empId/profile"
        element={
          <RequireAuth>
            <EmployeeProfilePage />
          </RequireAuth>
        }
      />
      <Route
        path="/onboarding"
        element={
          <RequireAuth>
            <OnboardingChecklistPage />
          </RequireAuth>
        }
      />
      <Route
        path="/role-changes"
        element={
          <RequireAuth>
            <RoleChangeTrackingPage />
          </RequireAuth>
        }
      />
      <Route
        path="/exit-workflow"
        element={
          <RequireAuth>
            <ExitWorkflowPage />
          </RequireAuth>
        }
      />
      <Route
        path="/document-verification"
        element={
          <RequireAuth>
            <DocumentVerificationPage />
          </RequireAuth>
        }
      />
      <Route
        path="/compliance-dashboard"
        element={
          <RequireAuth>
            <ComplianceDashboardPage />
          </RequireAuth>
        }
      />
      <Route
        path="/alerts-reminders"
        element={
          <RequireAuth>
            <ComplianceAlertsPage />
          </RequireAuth>
        }
      />
      <Route
        path="/headcount-report"
        element={
          <RequireAuth>
            <HeadcountReportPage />
          </RequireAuth>
        }
      />
      <Route
        path="/joiners-leavers-report"
        element={
          <RequireAuth>
            <JoinersLeaversReportPage />
          </RequireAuth>
        }
      />
      <Route
        path="/ctc-level-distribution"
        element={
          <RequireAuth>
            <CTCLevelDistributionPage />
          </RequireAuth>
        }
      />
      <Route
        path="/compliance-status-report"
        element={
          <RequireAuth>
            <ComplianceStatusReportPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/auth" replace />} />
    </Routes>
  )
}

export default App
