#!/usr/bin/env python
"""
Demo script for employee master records and lifecycle flow.
"""
import os
from datetime import date

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from hackathon.models import (
    Employee,
    EmployeeBankDetail,
    EmployeeComplianceDetail,
    EmployeeCTCHistory,
    OnboardingChecklistItem,
    RoleChangeHistory,
    ExitWorkflow,
    ComplianceDocument,
)


def create_demo_employees():
    """Create minimum 3 employee records if table is empty."""
    if Employee.objects.count() > 0:
        print(f"Database already has {Employee.objects.count()} employees. Skipping seed.")
        return

    employees_data = [
        {
            'emp_id': 'EMP001',
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@company.com',
            'phone': '+1 (555) 123-4567',
            'department': 'Engineering',
            'position': 'Senior Software Engineer',
            'start_date': date(2021, 3, 15),
        },
        {
            'emp_id': 'EMP002',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'email': 'sarah.johnson@company.com',
            'phone': '+1 (555) 234-5678',
            'department': 'Product',
            'position': 'Product Manager',
            'start_date': date(2020, 6, 1),
        },
        {
            'emp_id': 'EMP003',
            'first_name': 'Michael',
            'last_name': 'Chen',
            'email': 'michael.chen@company.com',
            'phone': '+1 (555) 345-6789',
            'department': 'Design',
            'position': 'UX Designer',
            'start_date': date(2022, 1, 10),
        },
    ]

    created_count = 0
    for emp_data in employees_data:
        try:
            employee = Employee.objects.create(**emp_data)
            created_count += 1
            print(f"[OK] Created: {employee.emp_id} - {employee.full_name}")
        except Exception as exc:
            print(f"[ERR] Error creating {emp_data['emp_id']}: {exc}")

    print(f"Successfully created {created_count} demo employees.")


def run_create_update_exit_demo():
    """Demonstrate create -> update -> exit flow."""
    print("Running lifecycle demo: create -> update -> exit")

    emp_id = 'EMP_DEMO_FLOW'
    Employee.objects.filter(emp_id=emp_id).delete()

    employee = Employee.objects.create(
        emp_id=emp_id,
        first_name='Flow',
        last_name='Demo',
        email='flow.demo@company.com',
        phone='+1 (555) 999-0000',
        department='Operations',
        position='Coordinator',
        start_date=date(2024, 1, 1),
    )
    print(f"[CREATE] {employee.emp_id} {employee.full_name} status={employee.status}")

    employee.position = 'Senior Coordinator'
    employee.department = 'Operations Excellence'
    employee.save()
    print(f"[UPDATE] {employee.emp_id} position={employee.position}, department={employee.department}")

    employee.exit_employee(date(2025, 12, 31))
    print(f"[EXIT] {employee.emp_id} status={employee.status}, end_date={employee.end_date}")


def seed_unified_profile_demo():
    """Create one complete employee profile across linked tables."""
    employee, _ = Employee.objects.get_or_create(
        emp_id='EMP001',
        defaults={
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john.smith@company.com',
            'phone': '+1 (555) 123-4567',
            'department': 'Engineering',
            'position': 'Senior Software Engineer',
            'start_date': date(2021, 3, 15),
        },
    )

    EmployeeBankDetail.objects.update_or_create(
        employee=employee,
        defaults={
            'bank_name': 'HDFC Bank',
            'account_holder_name': 'John Smith',
            'account_number': '109876543210',
            'ifsc_code': 'HDFC0000199',
            'branch_name': 'Bengaluru Central',
        },
    )

    EmployeeComplianceDetail.objects.update_or_create(
        employee=employee,
        defaults={
            'pan_number': 'ABCDE1234F',
            'aadhaar_number': '123412341234',
            'uan_number': '100200300400',
            'esi_number': 'ESI7788990',
        },
    )

    EmployeeCTCHistory.objects.filter(employee=employee).delete()
    EmployeeCTCHistory.objects.bulk_create(
        [
            EmployeeCTCHistory(
                employee=employee,
                effective_from=date(2021, 3, 15),
                annual_ctc='900000.00',
                variable_pay='100000.00',
                notes='Initial offer',
            ),
            EmployeeCTCHistory(
                employee=employee,
                effective_from=date(2023, 4, 1),
                annual_ctc='1200000.00',
                variable_pay='160000.00',
                notes='Promotion to Senior Engineer',
            ),
            EmployeeCTCHistory(
                employee=employee,
                effective_from=date(2025, 4, 1),
                annual_ctc='1450000.00',
                variable_pay='210000.00',
                notes='Annual revision',
            ),
        ]
    )

    print(f"[PROFILE] Seeded unified profile for {employee.emp_id}")


def seed_onboarding_demo():
    employee = Employee.objects.get(emp_id='EMP001')
    items = [
        ('ID Proof Submitted', True, 'passport_emp001.pdf'),
        ('Address Proof Submitted', True, 'utility_bill_emp001.pdf'),
        ('Signed Offer Letter', False, ''),
    ]
    for name, done, doc in items:
        item, _ = OnboardingChecklistItem.objects.update_or_create(
            employee=employee,
            item_name=name,
            defaults={'is_completed': done, 'document_ref': doc},
        )
        if done and not item.completed_at:
            from django.utils import timezone
            item.completed_at = timezone.now()
            item.save(update_fields=['completed_at'])
    print(f"[ONBOARDING] Seeded checklist for {employee.emp_id}")


def seed_role_change_demo():
    employee = Employee.objects.get(emp_id='EMP001')
    RoleChangeHistory.objects.filter(employee=employee).delete()
    RoleChangeHistory.objects.create(
        employee=employee,
        role_title='Software Engineer',
        role_level='L2',
        annual_ctc='900000.00',
        effective_from=date(2021, 3, 15),
        effective_to=date(2023, 3, 31),
        notes='Initial joining role',
    )
    RoleChangeHistory.objects.create(
        employee=employee,
        role_title='Senior Software Engineer',
        role_level='L3',
        annual_ctc='1200000.00',
        effective_from=date(2023, 4, 1),
        effective_to=None,
        notes='Promotion cycle',
    )
    print(f"[ROLE-CHANGE] Seeded 2 role/CTC records for {employee.emp_id}")


def seed_exit_workflow_demo():
    employee = Employee.objects.get(emp_id='EMP003')
    ExitWorkflow.objects.update_or_create(
        employee=employee,
        defaults={
            'last_working_day': date(2026, 1, 31),
            'reason': 'Pursuing higher studies',
            'it_clearance': True,
            'hr_clearance': True,
            'finance_clearance': False,
            'remarks': 'Finance NOC pending',
        },
    )
    if employee.status != 'exited':
        employee.exit_employee(date(2026, 1, 31))
    print(f"[EXIT] Seeded exit workflow for {employee.emp_id}")


def seed_compliance_documents_demo():
    emp1 = Employee.objects.get(emp_id='EMP001')
    emp2 = Employee.objects.get(emp_id='EMP002')

    for employee, docs in [
        (
            emp1,
            [
                ('PAN', 'ABCDE1234F', 'secure://docs/emp001/pan.pdf', 'verified'),
                ('AADHAAR', '123412341234', 'secure://docs/emp001/aadhaar.pdf', 'pending'),
                ('BANK_PROOF', '109876543210', 'secure://docs/emp001/bank.pdf', 'verified'),
            ],
        ),
        (
            emp2,
            [
                ('PAN', 'PQRSX6789Z', 'secure://docs/emp002/pan.pdf', 'pending'),
            ],
        ),
    ]:
        for doc_type, number, link, status in docs:
            doc, _ = ComplianceDocument.objects.update_or_create(
                employee=employee,
                doc_type=doc_type,
                defaults={
                    'doc_number': number,
                    'doc_link': link,
                    'status': status,
                    'remarks': 'Demo data',
                },
            )
            if status == 'verified' and not doc.verified_at:
                from django.utils import timezone
                doc.verified_at = timezone.now()
                doc.save(update_fields=['verified_at'])
            if status == 'pending' and doc.verified_at is not None:
                doc.verified_at = None
                doc.save(update_fields=['verified_at'])

    print("[COMPLIANCE] Seeded document verification demo data")


def seed_report_sample_data():
    """Ensure at least 3 months of joiner/leaver samples for reports."""
    monthly_samples = [
        ('EMP_RPT_01', '2025-01-05', None),
        ('EMP_RPT_02', '2025-02-10', '2025-05-20'),
        ('EMP_RPT_03', '2025-03-15', None),
        ('EMP_RPT_04', '2025-04-01', '2025-06-30'),
    ]
    for idx, (emp_id, start_raw, end_raw) in enumerate(monthly_samples, start=1):
        start_dt = date.fromisoformat(start_raw)
        end_dt = date.fromisoformat(end_raw) if end_raw else None
        status = 'exited' if end_dt else 'active'

        employee, created = Employee.objects.update_or_create(
            emp_id=emp_id,
            defaults={
                'first_name': f'Report{idx}',
                'last_name': 'Sample',
                'email': f'report.sample{idx}@company.com',
                'phone': f'+1 (555) 600-00{idx}',
                'department': 'Analytics',
                'position': 'Analyst',
                'start_date': start_dt,
                'status': status,
                'end_date': end_dt,
            },
        )
        if not created and status == 'exited' and employee.end_date != end_dt:
            employee.end_date = end_dt
            employee.status = 'exited'
            employee.save()

    print("[REPORT] Seeded joiners/leavers sample data across multiple months")


if __name__ == '__main__':
    create_demo_employees()
    seed_unified_profile_demo()
    seed_onboarding_demo()
    seed_role_change_demo()
    seed_exit_workflow_demo()
    seed_compliance_documents_demo()
    seed_report_sample_data()
    run_create_update_exit_demo()
