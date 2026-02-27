from django.db import models
from django.core.exceptions import ValidationError
from datetime import date


class Employee(models.Model):
    """Employee model for managing employee records and lifecycle."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('exited', 'Exited'),
    ]
    
    # Unique employee ID
    emp_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique employee identifier"
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Employment Information
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    # Status and Tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['emp_id']),
        ]
    
    def __str__(self):
        return f"{self.emp_id} - {self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Return full name of employee."""
        return f"{self.first_name} {self.last_name}"
    
    def exit_employee(self, end_date):
        """Mark employee as exited with end date."""
        if self.status == 'exited':
            raise ValidationError("Employee is already marked as exited.")

        if isinstance(end_date, str):
            try:
                end_date = date.fromisoformat(end_date)
            except ValueError as exc:
                raise ValidationError("Invalid end_date format. Use YYYY-MM-DD.") from exc

        if end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

        self.status = 'exited'
        self.end_date = end_date
        self.full_clean()
        self.save()

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")
        if self.status == 'exited' and not self.end_date:
            raise ValidationError("Exited employee must have an end date.")
    
    def to_dict(self):
        """Convert employee data to dictionary."""
        return {
            'id': self.id,
            'emp_id': self.emp_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'position': self.position,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class EmployeeBankDetail(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='bank_detail')
    bank_name = models.CharField(max_length=120)
    account_holder_name = models.CharField(max_length=120)
    account_number = models.CharField(max_length=40)
    ifsc_code = models.CharField(max_length=20)
    branch_name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.emp_id} - {self.bank_name}"

    def to_dict(self):
        return {
            'bank_name': self.bank_name,
            'account_holder_name': self.account_holder_name,
            'account_number': self.account_number,
            'ifsc_code': self.ifsc_code,
            'branch_name': self.branch_name,
            'updated_at': self.updated_at.isoformat(),
        }


class EmployeeComplianceDetail(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='compliance_detail')
    pan_number = models.CharField(max_length=20, blank=True)
    aadhaar_number = models.CharField(max_length=20, blank=True)
    uan_number = models.CharField(max_length=30, blank=True)
    esi_number = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.emp_id} - Compliance"

    def to_dict(self):
        return {
            'pan_number': self.pan_number or None,
            'aadhaar_number': self.aadhaar_number or None,
            'uan_number': self.uan_number or None,
            'esi_number': self.esi_number or None,
            'updated_at': self.updated_at.isoformat(),
        }


class EmployeeCTCHistory(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='ctc_history')
    effective_from = models.DateField()
    annual_ctc = models.DecimalField(max_digits=12, decimal_places=2)
    variable_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_from', '-created_at']

    def __str__(self):
        return f"{self.employee.emp_id} - {self.effective_from} - {self.annual_ctc}"

    def to_dict(self):
        return {
            'effective_from': self.effective_from.isoformat(),
            'annual_ctc': float(self.annual_ctc),
            'variable_pay': float(self.variable_pay),
            'notes': self.notes or None,
        }


class OnboardingChecklistItem(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='onboarding_items')
    item_name = models.CharField(max_length=120)
    is_completed = models.BooleanField(default=False, db_index=True)
    document_ref = models.CharField(max_length=255, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('employee', 'item_name')
        ordering = ['id']

    def __str__(self):
        return f"{self.employee.emp_id} - {self.item_name}"

    def to_dict(self):
        return {
            'id': self.id,
            'item_name': self.item_name,
            'is_completed': self.is_completed,
            'document_ref': self.document_ref or None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class RoleChangeHistory(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='role_changes')
    role_title = models.CharField(max_length=120)
    role_level = models.CharField(max_length=60)
    annual_ctc = models.DecimalField(max_digits=12, decimal_places=2)
    effective_from = models.DateField(db_index=True)
    effective_to = models.DateField(null=True, blank=True, db_index=True)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_from', '-created_at']

    def __str__(self):
        return f"{self.employee.emp_id} - {self.role_title} ({self.effective_from})"

    def clean(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValidationError("effective_to cannot be before effective_from.")

        overlaps = RoleChangeHistory.objects.filter(employee=self.employee).exclude(pk=self.pk)
        for row in overlaps:
            row_start = row.effective_from
            row_end = row.effective_to or date.max
            this_start = self.effective_from
            this_end = self.effective_to or date.max
            if row_start <= this_end and this_start <= row_end:
                raise ValidationError("Role change dates overlap with an existing record.")

    def to_dict(self):
        return {
            'id': self.id,
            'role_title': self.role_title,
            'role_level': self.role_level,
            'annual_ctc': float(self.annual_ctc),
            'effective_from': self.effective_from.isoformat(),
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'notes': self.notes or None,
        }


class ExitWorkflow(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='exit_workflow')
    last_working_day = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    it_clearance = models.BooleanField(default=False)
    hr_clearance = models.BooleanField(default=False)
    finance_clearance = models.BooleanField(default=False)
    remarks = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee.emp_id} - Exit Workflow"

    def to_dict(self):
        return {
            'last_working_day': self.last_working_day.isoformat(),
            'reason': self.reason or None,
            'it_clearance': self.it_clearance,
            'hr_clearance': self.hr_clearance,
            'finance_clearance': self.finance_clearance,
            'remarks': self.remarks or None,
            'updated_at': self.updated_at.isoformat(),
        }


class ComplianceDocument(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='compliance_documents')
    doc_type = models.CharField(max_length=80, db_index=True)
    doc_number = models.CharField(max_length=80, blank=True)
    doc_link = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        unique_together = ('employee', 'doc_type')

    def __str__(self):
        return f"{self.employee.emp_id} - {self.doc_type} ({self.status})"

    def to_dict(self):
        return {
            'id': self.id,
            'doc_type': self.doc_type,
            'doc_number': self.doc_number or None,
            'doc_link': self.doc_link,
            'status': self.status,
            'uploaded_at': self.uploaded_at.isoformat(),
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'remarks': self.remarks or None,
        }


class EmpMasterMirror(models.Model):
    """Mirror model for pre-defined MySQL table: emp_master."""

    emp_id = models.CharField(max_length=50, primary_key=True, db_column='emp_id')
    first_name = models.CharField(max_length=100, db_column='first_name')
    middle_name = models.CharField(max_length=100, blank=True, db_column='middle_name')
    last_name = models.CharField(max_length=100, db_column='last_name')
    start_date = models.DateField(db_column='start_date')
    end_date = models.DateField(null=True, blank=True, db_column='end_date')

    class Meta:
        db_table = 'emp_master'
        managed = False


class EmpBankInfoMirror(models.Model):
    """Mirror model for pre-defined MySQL table: emp_bank_info."""

    emp_bank_id = models.AutoField(primary_key=True, db_column='emp_bank_id')
    emp_id = models.CharField(max_length=50, db_column='emp_id')
    bank_acct_no = models.CharField(max_length=40, blank=True, db_column='bank_acct_no')
    ifsc_code = models.CharField(max_length=20, blank=True, db_column='ifsc_code')
    branch_name = models.CharField(max_length=120, blank=True, db_column='branch_name')
    bank_name = models.CharField(max_length=120, blank=True, db_column='bank_name')

    class Meta:
        db_table = 'emp_bank_info'
        managed = False


class EmpComplianceMasterMirror(models.Model):
    """Mirror model for pre-defined MySQL table: emp_compliance_master."""

    emp_compliance_tracker_id = models.AutoField(primary_key=True, db_column='emp_compliance_tracker_id')
    emp_id = models.CharField(max_length=50, db_column='emp_id')
    comp_type = models.CharField(max_length=80, db_column='comp_type')
    status = models.CharField(max_length=20, db_column='status')
    doc_url = models.CharField(max_length=255, blank=True, db_column='doc_url')

    class Meta:
        db_table = 'emp_compliance_master'
        managed = False


class EmpComplianceTrackerMirror(models.Model):
    """Fallback mirror for deployments using emp_compliance_tracker table name."""

    emp_compliance_tracker_id = models.AutoField(primary_key=True, db_column='emp_compliance_tracker_id')
    emp_id = models.CharField(max_length=50, db_column='emp_id')
    comp_type = models.CharField(max_length=80, db_column='comp_type')
    status = models.CharField(max_length=20, db_column='status')
    doc_url = models.CharField(max_length=255, blank=True, db_column='doc_url')

    class Meta:
        db_table = 'emp_compliance_tracker'
        managed = False


class EmpCTCMasterMirror(models.Model):
    """Mirror model for pre-defined MySQL table: emp_ctc_master."""

    emp_ctc_id = models.AutoField(primary_key=True, db_column='emp_ctc_id')
    emp_id = models.PositiveIntegerField(db_column='emp_id')
    int_title = models.CharField(max_length=30, blank=True, db_column='int_title')
    ext_title = models.CharField(max_length=60, blank=True, db_column='ext_title')
    main_level = models.PositiveSmallIntegerField(null=True, blank=True, db_column='main_level')
    sub_level = models.CharField(max_length=1, blank=True, db_column='sub_level')
    start_of_ctc = models.DateField(db_column='start_of_ctc')
    end_of_ctc = models.DateField(null=True, blank=True, db_column='end_of_ctc')
    ctc_amt = models.DecimalField(max_digits=12, decimal_places=2, db_column='ctc_amt')

    class Meta:
        db_table = 'emp_ctc_master'
        managed = False


class EmpCTCInfoMirror(models.Model):
    """Fallback mirror for deployments using emp_ctc_info table name."""

    emp_ctc_id = models.AutoField(primary_key=True, db_column='emp_ctc_id')
    emp_id = models.PositiveIntegerField(db_column='emp_id')
    int_title = models.CharField(max_length=30, blank=True, db_column='int_title')
    ext_title = models.CharField(max_length=60, blank=True, db_column='ext_title')
    main_level = models.PositiveSmallIntegerField(null=True, blank=True, db_column='main_level')
    sub_level = models.CharField(max_length=1, blank=True, db_column='sub_level')
    start_of_ctc = models.DateField(db_column='start_of_ctc')
    end_of_ctc = models.DateField(null=True, blank=True, db_column='end_of_ctc')
    ctc_amt = models.DecimalField(max_digits=12, decimal_places=2, db_column='ctc_amt')

    class Meta:
        db_table = 'emp_ctc_info'
        managed = False
