# Employee CRUD Management System

## Overview
This is a full-stack Employee Management application built with Django (backend) and React (frontend). It allows organizations to create, read, update, and manage employee records while maintaining data consistency and tracking employee lifecycle (active/exited).

## Problem Solved
Organizations struggle to maintain accurate and up-to-date employee records. Manual tracking leads to:
- Inconsistent data across systems
- Poor visibility into employee lifecycle
- Difficulty tracking employee exit dates and reasons

This system provides a centralized solution for employee record management with:
- ✅ Create employees with mandatory fields
- ✅ Update employee details successfully
- ✅ Exit/deactivate employees using end date
- ✅ Unique Employee ID validation
- ✅ Employee lifecycle tracking (active/exited)
- ✅ Demo with 3 employee records

---

## Architecture

### Backend (Django)
**Location**: `backend/`
- **Models**: Employee model with status tracking
- **Views**: RESTful API endpoints for CRUD operations
- **URLs**: Employee API routes
- **Database**: SQLite (persistent file-based)

### Frontend (React)
**Location**: `frontend/`
- **Pages**: Employee management page with forms and table
- **API Client**: Employee API service
- **Styles**: Responsive CSS with modern design
- **Routes**: Employee page accessible from authenticated users

---

## Database Schema

### Employee Model
```python
class Employee(models.Model):
    # Unique Identifiers
    emp_id: CharField (unique, indexed)
    
    # Personal Information
    first_name: CharField
    last_name: CharField
    email: EmailField (unique, indexed)
    phone: CharField (optional)
    
    # Employment Information
    department: CharField
    position: CharField
    start_date: DateField
    end_date: DateField (nullable - for exit date)
    
    # Status & Timestamps
    status: CharField (choices: 'active', 'exited', default: 'active')
    created_at: DateTimeField (auto)
    updated_at: DateTimeField (auto)
```

---

## API Endpoints

### 1. List Employees
**Endpoint**: `GET /api/employees`
**Query Parameters**:
- `status` (optional): 'active', 'exited', or empty for all
- `search` (optional): Search by emp_id, name, or email

**Example**:
```bash
GET /api/employees?status=active&search=Smith
```

**Response**:
```json
{
  "employees": [
    {
      "id": 1,
      "emp_id": "EMP001",
      "first_name": "John",
      "last_name": "Smith",
      "full_name": "John Smith",
      "email": "john.smith@company.com",
      "phone": "+1 (555) 123-4567",
      "department": "Engineering",
      "position": "Senior Software Engineer",
      "start_date": "2021-03-15",
      "end_date": null,
      "status": "active",
      "created_at": "2026-02-26T10:30:00Z",
      "updated_at": "2026-02-26T10:30:00Z"
    }
  ]
}
```

### 2. Create Employee
**Endpoint**: `POST /api/employees/create`

**Required Fields**:
- `emp_id` - Unique employee identifier
- `first_name` - Employee first name
- `last_name` - Employee last name
- `email` - Unique email address
- `department` - Department name
- `position` - Job position
- `start_date` - Employment start date (YYYY-MM-DD)

**Optional Fields**:
- `phone` - Phone number

**Example Request**:
```json
{
  "emp_id": "EMP004",
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane.doe@company.com",
  "phone": "+1 (555) 456-7890",
  "department": "Marketing",
  "position": "Marketing Manager",
  "start_date": "2023-01-15"
}
```

**Response** (201 Created):
```json
{
  "employee": { /* employee data */ }
}
```

### 3. Get Employee Details
**Endpoint**: `GET /api/employees/<emp_id>`

**Example**:
```bash
GET /api/employees/EMP001
```

**Response**:
```json
{
  "employee": { /* employee data */ }
}
```

### 4. Update Employee
**Endpoint**: `PUT /api/employees/<emp_id>`

**Updateable Fields**:
- `first_name`, `last_name`
- `email` (must be unique if changed)
- `phone`
- `department`, `position`
- `start_date`

**Example Request**:
```json
{
  "position": "Senior Marketing Manager",
  "department": "Marketing & Growth"
}
```

**Response**:
```json
{
  "employee": { /* updated employee data */ }
}
```

### 5. Exit Employee
**Endpoint**: `POST /api/employees/<emp_id>/exit`

**Required Fields**:
- `end_date` - Employee exit date (YYYY-MM-DD)

**Example Request**:
```json
{
  "end_date": "2026-03-31"
}
```

**Response**:
```json
{
  "employee": {
    /* employee data with status: "exited" and end_date populated */
  }
}
```

---

## Authentication
All API endpoints require authentication. Include the bearer token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## Frontend Features

### Employee Management Page (`/employees`)

#### Features
1. **View All Employees**
   - Displays all employees in a responsive table
   - Shows: Emp ID, Name, Email, Department, Position, Start Date, Status
   - Color-coded status badges (green for active, red for exited)

2. **Filter & Search**
   - Filter by status (All, Active, Exited)
   - Search by Employee ID, Name, or Email
   - Real-time search and filter

3. **Create Employee**
   - Click "Add Employee" button
   - Fill all required fields in modal
   - Emp ID must be unique
   - Email must be unique

4. **Edit Employee**
   - Click "Edit" button on any employee row
   - Emp ID field is disabled (cannot change)
   - Update any other field
   - Changes are saved immediately

5. **Exit Employee**
   - Click "Exit" button on active employee
   - Specify exit date
   - Employee status changes to "exited"
   - Cannot be reversed from the UI (can be done via API if needed)

#### User Experience
- Loading indicators for async operations
- Success and error messages with clear feedback
- Modal confirmations for destructive actions
- Responsive design for mobile/tablet/desktop
- Modern gradient background with clean card layout

---

## Demo Data

The system comes with 3 pre-loaded demo employees:

1. **John Smith** (EMP001)
   - Email: john.smith@company.com
   - Department: Engineering
   - Position: Senior Software Engineer
   - Start Date: 2021-03-15
   - Status: Active

2. **Sarah Johnson** (EMP002)
   - Email: sarah.johnson@company.com
   - Department: Product
   - Position: Product Manager
   - Start Date: 2020-06-01
   - Status: Active

3. **Michael Chen** (EMP003)
   - Email: michael.chen@company.com
   - Department: Design
   - Position: UX Designer
   - Start Date: 2022-01-10
   - Status: Active

---

## Demo Workflow

### Step 1: Create Employee
1. Navigate to `/employees`
2. Click "Add Employee"
3. Fill in details for a new employee
4. Click "Create"
5. New employee appears in the table

### Step 2: Update Employee
1. Click "Edit" on an employee row
2. Modify the employee's department or position
3. Click "Update"
4. Changes are reflected immediately in the table

### Step 3: Exit Employee
1. Click "Exit" on an active employee
2. Select the exit date
3. Click "Confirm Exit"
4. Employee status changes to "Exited" (shown in red badge)
5. Exit button is no longer available for exited employees

---

## Installation & Setup

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install requirements
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create demo data
python demo_employees.py

# Start development server
python manage.py runserver
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set environment variables
# Create .env.local with:
# VITE_BACKEND_URL=http://localhost:8000

# Start development server
npm run dev
```

---

## Deployment Considerations

### Database
- Currently using SQLite (`db.sqlite3`) for development
- For production, configure MySQL using environment variables:
  - `DB_ENGINE=django.db.backends.mysql`
  - `DB_NAME=hackathon_db`
  - `DB_USER=db_user`
  - `DB_PASSWORD=password`
  - `DB_HOST=localhost`
  - `DB_PORT=3306`

### Security
- Implement CORS restrictions
- Use HTTPS in production
- Implement role-based access control
- Add audit logging for employee record changes
- Encrypt sensitive data

### Performance
- Add database indexing on frequently searched fields
- Implement pagination for large employee lists
- Cache frequently accessed data
- Use CDN for static files

---

## Minimum Acceptance Criteria (MAC) ✅

- ✅ Create employee with mandatory fields (emp_id, name, email, department, position, start_date)
- ✅ Update employee details successfully
- ✅ Exit/deactivate employee using end date
- ✅ Unique Emp ID validation enforced
- ✅ Demo showing create → update → exit flow
- ✅ Demo with minimum 3 employee records (John Smith, Sarah Johnson, Michael Chen)
- ✅ Search by name or ID, filter by status, sort by name or start date (directory features)

---

## File Structure

```
backend/
├── hackathon/
│   ├── models.py           # Employee model
│   ├── views.py            # API views (CRUD endpoints)
│   ├── urls.py             # URL routing
│   ├── migrations/
│   │   ├── 0002_initial.py # Employee model migration
│   │   └── ...
│   └── ...
├── backend/
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL config
│   └── ...
├── demo_employees.py       # Demo data script
├── manage.py
└── db.sqlite3              # Database file

frontend/
├── src/
│   ├── pages/
│   │   ├── employee.jsx    # Employee management page
│   │   ├── auth.jsx
│   │   └── home.jsx
│   ├── api/
│   │   ├── employeeApi.js  # Employee API client
│   │   ├── authApi.js
│   │   └── http.js
│   ├── styles/
│   │   ├── Employee.css    # Employee page styles
│   │   ├── Home.css
│   │   └── ...
│   ├── App.jsx             # Main app with routes
│   └── ...
├── package.json
└── ...
```

---

## Technologies Used

### Backend
- **Framework**: Django 5.2
- **Database**: SQLite (development), MySQL (production)
- **API**: RESTful JSON endpoints
- **Language**: Python 3.13

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: CSS3 with flexbox/grid
- **HTTP Client**: Fetch API
- **Router**: React Router

---

## Future Enhancements

1. **Advanced Reporting**
   - Export employee data to CSV/Excel
   - Generate headcount reports
   - Track turnover metrics

2. **Employee Documents**
   - Upload and store employee documents
   - Track certifications
   - Manage attachments

3. **Notifications**
   - Email notifications for employee updates
   - Reminders for upcoming exit dates
   - Alerts for duplicate emails

4. **Bulk Operations**
   - Bulk import employees from CSV
   - Batch update operations
   - Mass delete (with soft delete)

5. **User Roles & Permissions**
   - Admin: Full CRUD access
   - Manager: View and update own team
   - HR: Limited CRUD access
   - Employee: View-only limited data

6. **Audit Trail**
   - Track all changes to employee records
   - Log who made changes and when
   - View change history

---

## Support & Troubleshooting

### Common Issues

**Issue**: "No such table: hackathon_employee"
**Solution**: Run `python manage.py migrate` to create database tables

**Issue**: CORS error accessing API
**Solution**: Check `ALLOWED_HOSTS` in `backend/settings.py`

**Issue**: 401 Unauthorized on employee endpoints
**Solution**: Ensure you're passing a valid authentication token in the Authorization header

**Issue**: Employee ID already exists
**Solution**: Use a unique emp_id that hasn't been used before

---

## License
This project is part of a hackathon and is provided as-is.

---

**Last Updated**: February 26, 2026
