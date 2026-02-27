import json
from datetime import date

from django.test import TestCase

from .models import (
    Employee,
    EmployeeBankDetail,
    EmployeeComplianceDetail,
    EmployeeCTCHistory,
    OnboardingChecklistItem,
    RoleChangeHistory,
    ComplianceDocument,
)


class EmployeeApiTests(TestCase):
    def test_create_employee_with_mandatory_fields(self):
        payload = {
            'emp_id': 'EMP100',
            'first_name': 'Alice',
            'last_name': 'Wong',
            'email': 'alice.wong@example.com',
            'department': 'Engineering',
            'position': 'Developer',
            'start_date': '2024-01-10',
        }

        response = self.client.post(
            '/api/employees/create',
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Employee.objects.count(), 1)
        self.assertEqual(Employee.objects.first().emp_id, 'EMP100')

    def test_unique_emp_id_validation(self):
        Employee.objects.create(
            emp_id='EMP101',
            first_name='Bob',
            last_name='Lee',
            email='bob.lee@example.com',
            department='Finance',
            position='Analyst',
            start_date=date(2023, 5, 1),
        )

        duplicate_payload = {
            'emp_id': 'EMP101',
            'first_name': 'Robert',
            'last_name': 'Lee',
            'email': 'robert.lee@example.com',
            'department': 'Finance',
            'position': 'Analyst',
            'start_date': '2023-05-01',
        }

        response = self.client.post(
            '/api/employees/create',
            data=json.dumps(duplicate_payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Employee ID already exists', response.json()['error'])

    def test_update_employee_details(self):
        employee = Employee.objects.create(
            emp_id='EMP102',
            first_name='Carol',
            last_name='Ng',
            email='carol.ng@example.com',
            department='Product',
            position='PM',
            start_date=date(2022, 7, 15),
        )

        response = self.client.put(
            f'/api/employees/{employee.emp_id}',
            data=json.dumps({'department': 'Operations', 'position': 'Program Manager'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        employee.refresh_from_db()
        self.assertEqual(employee.department, 'Operations')
        self.assertEqual(employee.position, 'Program Manager')

    def test_exit_employee_with_end_date(self):
        employee = Employee.objects.create(
            emp_id='EMP103',
            first_name='David',
            last_name='Kim',
            email='david.kim@example.com',
            department='Support',
            position='Specialist',
            start_date=date(2021, 2, 20),
        )

        response = self.client.post(
            f'/api/employees/{employee.emp_id}/exit',
            data=json.dumps({'end_date': '2025-01-31'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        employee.refresh_from_db()
        self.assertEqual(employee.status, 'exited')
        self.assertEqual(str(employee.end_date), '2025-01-31')

    def test_exit_date_must_not_be_before_start_date(self):
        employee = Employee.objects.create(
            emp_id='EMP104',
            first_name='Eve',
            last_name='Patel',
            email='eve.patel@example.com',
            department='HR',
            position='Generalist',
            start_date=date(2024, 3, 1),
        )

        response = self.client.post(
            f'/api/employees/{employee.emp_id}/exit',
            data=json.dumps({'end_date': '2024-02-28'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('End date cannot be earlier than start date', response.json()['error'])

    def test_profile_loads_from_multiple_linked_tables(self):
        employee = Employee.objects.create(
            emp_id='EMP200',
            first_name='Priya',
            last_name='Nair',
            email='priya.nair@example.com',
            department='Engineering',
            position='Lead Engineer',
            start_date=date(2021, 4, 1),
        )
        EmployeeBankDetail.objects.create(
            employee=employee,
            bank_name='State Bank',
            account_holder_name='Priya Nair',
            account_number='123456789012',
            ifsc_code='SBIN0001234',
            branch_name='MG Road',
        )
        EmployeeComplianceDetail.objects.create(
            employee=employee,
            pan_number='ABCDE1234F',
            aadhaar_number='123412341234',
            uan_number='100200300400',
            esi_number='ESI1234567',
        )
        EmployeeCTCHistory.objects.create(
            employee=employee,
            effective_from=date(2023, 1, 1),
            annual_ctc='1200000.00',
            variable_pay='150000.00',
            notes='Promotion cycle',
        )

        response = self.client.get(f'/api/employees/{employee.emp_id}/profile')
        payload = response.json()['profile']

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload['employee']['emp_id'], 'EMP200')
        self.assertEqual(payload['bank']['bank_name'], 'State Bank')
        self.assertEqual(payload['compliance']['pan_number'], 'ABCDE1234F')
        self.assertEqual(len(payload['ctc_timeline']), 1)
        self.assertEqual(payload['missing_sections'], [])

    def test_profile_handles_missing_linked_data(self):
        employee = Employee.objects.create(
            emp_id='EMP201',
            first_name='Ravi',
            last_name='Kumar',
            email='ravi.kumar@example.com',
            department='Operations',
            position='Analyst',
            start_date=date(2022, 8, 15),
        )

        response = self.client.get(f'/api/employees/{employee.emp_id}/profile')
        payload = response.json()['profile']

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(payload['bank'])
        self.assertIsNone(payload['compliance'])
        self.assertEqual(payload['ctc_timeline'], [])
        self.assertEqual(set(payload['missing_sections']), {'bank', 'compliance', 'ctc_timeline'})

    def test_onboarding_progress_endpoint(self):
        employee = Employee.objects.create(
            emp_id='EMP300',
            first_name='Test',
            last_name='User',
            email='test.user@example.com',
            department='QA',
            position='Tester',
            start_date=date(2024, 1, 1),
        )
        OnboardingChecklistItem.objects.create(employee=employee, item_name='ID Proof', is_completed=True)
        OnboardingChecklistItem.objects.create(employee=employee, item_name='Address Proof', is_completed=False)

        response = self.client.get('/api/onboarding/progress')
        self.assertEqual(response.status_code, 200)
        row = next((x for x in response.json()['progress'] if x['emp_id'] == 'EMP300'), None)
        self.assertIsNotNone(row)
        self.assertEqual(row['progress_percentage'], 50.0)

    def test_role_change_overlap_is_rejected(self):
        employee = Employee.objects.create(
            emp_id='EMP301',
            first_name='Role',
            last_name='Test',
            email='role.test@example.com',
            department='Eng',
            position='Dev',
            start_date=date(2024, 1, 1),
        )
        RoleChangeHistory.objects.create(
            employee=employee,
            role_title='Dev',
            role_level='L1',
            annual_ctc='500000.00',
            effective_from=date(2024, 1, 1),
            effective_to=date(2024, 12, 31),
        )

        response = self.client.post(
            f'/api/employees/{employee.emp_id}/role-changes',
            data=json.dumps(
                {
                    'role_title': 'Senior Dev',
                    'role_level': 'L2',
                    'annual_ctc': '700000.00',
                    'effective_from': '2024-06-01',
                    'effective_to': '2025-05-31',
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('overlap', response.json()['error'].lower())

    def test_document_upload_and_status_update(self):
        employee = Employee.objects.create(
            emp_id='EMP400',
            first_name='Doc',
            last_name='User',
            email='doc.user@example.com',
            department='HR',
            position='Executive',
            start_date=date(2024, 2, 1),
        )
        create_res = self.client.post(
            f'/api/employees/{employee.emp_id}/documents',
            data=json.dumps({'doc_type': 'PAN', 'doc_link': 'secure://pan.pdf', 'doc_number': 'ABCDE1234F'}),
            content_type='application/json',
        )
        self.assertEqual(create_res.status_code, 201)
        doc_id = create_res.json()['document']['id']

        status_res = self.client.post(
            f'/api/employees/{employee.emp_id}/documents/{doc_id}/status',
            data=json.dumps({'status': 'verified'}),
            content_type='application/json',
        )
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()['document']['status'], 'verified')

    def test_headcount_report_counts(self):
        Employee.objects.create(
            emp_id='EMP401',
            first_name='A',
            last_name='A',
            email='a.a@example.com',
            department='Ops',
            position='Analyst',
            start_date=date(2024, 1, 1),
            status='active',
        )
        Employee.objects.create(
            emp_id='EMP402',
            first_name='B',
            last_name='B',
            email='b.b@example.com',
            department='Ops',
            position='Analyst',
            start_date=date(2024, 1, 1),
            status='exited',
            end_date=date(2024, 12, 31),
        )
        res = self.client.get('/api/reports/headcount')
        self.assertEqual(res.status_code, 200)
        summary = res.json()['summary']
        self.assertGreaterEqual(summary['total_employees'], 2)
        self.assertGreaterEqual(summary['active_employees'], 1)
        self.assertGreaterEqual(summary['exited_employees'], 1)

    def test_joiners_leavers_report_returns_monthly_rows(self):
        Employee.objects.create(
            emp_id='EMP500',
            first_name='Join',
            last_name='One',
            email='join.one@example.com',
            department='Ops',
            position='Exec',
            start_date=date(2025, 1, 15),
        )
        Employee.objects.create(
            emp_id='EMP501',
            first_name='Leave',
            last_name='One',
            email='leave.one@example.com',
            department='Ops',
            position='Exec',
            start_date=date(2025, 2, 10),
            status='exited',
            end_date=date(2025, 3, 20),
        )
        res = self.client.get('/api/reports/joiners-leavers?start=2025-01-01&end=2025-03-31')
        self.assertEqual(res.status_code, 200)
        rows = res.json()['monthly']
        self.assertEqual(len(rows), 3)

    def test_compliance_status_filter(self):
        employee = Employee.objects.create(
            emp_id='EMP502',
            first_name='Comp',
            last_name='User',
            email='comp.user@example.com',
            department='Ops',
            position='Exec',
            start_date=date(2025, 1, 1),
        )
        ComplianceDocument.objects.create(
            employee=employee,
            doc_type='PAN',
            doc_link='secure://pan',
            status='pending',
        )
        res = self.client.get('/api/reports/compliance-status?status=pending')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(any(row['status'] == 'pending' for row in res.json()['rows']))
