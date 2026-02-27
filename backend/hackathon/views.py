import json
import re
from datetime import date

from django.http import HttpRequest, JsonResponse
from django.views import View
from django.db.models import Q
from django.db import DatabaseError, connection
from django.utils import timezone

from .auth import (
    ExternalAuthError,
    create_signed_otp_challenge,
    create_signed_session,
    is_success_response,
    load_signed_otp_challenge,
    load_signed_session,
    post_form_json,
    require_env,
)

SYSTEM_NAME = 'isl'
REGISTER_ROLE = 'isl_user'


def _normalize_phone(raw: str) -> str:
    return re.sub(r'\D+', '', (raw or '').strip())


def _get_bearer_token(request: HttpRequest) -> str | None:
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    prefix = 'Bearer '
    if not auth_header.startswith(prefix):
        return None

    token = auth_header[len(prefix) :].strip()
    return token or None


def _get_session_payload(request: HttpRequest) -> dict | None:
    token = _get_bearer_token(request)
    if not token:
        return None
    try:
        return load_signed_session(token)
    except ExternalAuthError:
        return None


def _json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return {}


def _external_error_message(result: dict, default: str) -> str:
    return result.get('error') or result.get('message') or default


def _external_success_message(result: dict) -> str | None:
    message = (result.get('message') or result.get('status') or '').strip()
    return message or None


def _parse_iso_date(value, field_name: str) -> date:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a YYYY-MM-DD string.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name} format. Use YYYY-MM-DD.") from exc


def _post_external_or_error(
    *,
    url_env: str,
    payload: dict[str, str],
    failure_status: int,
    failure_default_message: str,
) -> tuple[dict | None, JsonResponse | None]:
    try:
        url = require_env(url_env)
    except ExternalAuthError as exc:
        return None, JsonResponse({'error': str(exc)}, status=500)

    try:
        result = post_form_json(url=url, payload=payload)
    except ExternalAuthError as exc:
        return None, JsonResponse({'error': str(exc)}, status=502)

    if not is_success_response(result):
        message = _external_error_message(result, failure_default_message)
        return None, JsonResponse({'error': message}, status=failure_status)

    return result, None


DEFAULT_ONBOARDING_ITEMS = [
    'ID Proof Submitted',
    'Address Proof Submitted',
    'Signed Offer Letter',
]

REQUIRED_COMPLIANCE_DOCS = [
    'PAN',
    'AADHAAR',
    'BANK_PROOF',
]

ONBOARDING_ITEM_DEFS = [
    {'id': 1, 'item_name': 'ID Proof Submitted', 'comp_type': 'ID_PROOF_SUBMITTED'},
    {'id': 2, 'item_name': 'Address Proof Submitted', 'comp_type': 'ADDRESS_PROOF_SUBMITTED'},
    {'id': 3, 'item_name': 'Signed Offer Letter', 'comp_type': 'SIGNED_OFFER_LETTER'},
]


def _get_compliance_model():
    from .models import EmpComplianceMasterMirror, EmpComplianceTrackerMirror

    table_names = set(connection.introspection.table_names())
    if 'emp_compliance_master' in table_names:
        return EmpComplianceMasterMirror
    if 'emp_compliance_tracker' in table_names:
        return EmpComplianceTrackerMirror
    return EmpComplianceMasterMirror


def _get_ctc_model():
    from .models import EmpCTCMasterMirror, EmpCTCInfoMirror

    table_names = set(connection.introspection.table_names())
    if 'emp_ctc_master' in table_names:
        return EmpCTCMasterMirror
    if 'emp_ctc_info' in table_names:
        return EmpCTCInfoMirror
    return EmpCTCMasterMirror


def _get_emp_master(emp_id):
    from .models import EmpMasterMirror

    row = EmpMasterMirror.objects.filter(emp_id=str(emp_id)).first()
    if row is not None:
        return row
    try:
        return EmpMasterMirror.objects.filter(emp_id=int(str(emp_id))).first()
    except (TypeError, ValueError):
        return None


def _to_int_emp_id(emp_id):
    try:
        return int(str(emp_id).strip())
    except (TypeError, ValueError):
        return None


def _mirror_status(end_date):
    return 'active' if end_date is None else 'exited'


def _mirror_to_employee_dict(row):
    emp_id_str = str(row.emp_id or 'employee')
    full_name = f"{row.first_name} {row.last_name}".strip()
    synthetic_email = f"{emp_id_str.lower()}@company.com"
    status = _mirror_status(row.end_date)
    start_iso = row.start_date.isoformat() if row.start_date else None
    end_iso = row.end_date.isoformat() if row.end_date else None
    return {
        'id': emp_id_str,
        'emp_id': emp_id_str,
        'first_name': row.first_name,
        'last_name': row.last_name,
        'full_name': full_name,
        'email': synthetic_email,
        'phone': '',
        'department': 'General',
        'position': 'Employee',
        'start_date': start_iso,
        'end_date': end_iso,
        'status': status,
        'created_at': start_iso,
        'updated_at': start_iso,
    }


def _parse_role_level_parts(role_level: str) -> tuple[int | None, str]:
    raw = (role_level or '').strip().upper()
    if not raw:
        return None, ''
    digits = ''.join(ch for ch in raw if ch.isdigit())
    letters = ''.join(ch for ch in raw if ch.isalpha())
    main = int(digits) if digits else None
    sub = letters[:1] if letters else ''
    return main, sub


def _format_role_level(main_level, sub_level: str) -> str:
    if main_level is None and not sub_level:
        return 'Unknown'
    if main_level is None:
        return sub_level
    return f"L{main_level}{sub_level or ''}"


def _ctc_row_to_timeline(row):
    return {
        'id': row.emp_ctc_id,
        'role_title': row.ext_title or row.int_title or 'N/A',
        'role_level': _format_role_level(row.main_level, row.sub_level),
        'annual_ctc': float(row.ctc_amt),
        'effective_from': row.start_of_ctc.isoformat() if row.start_of_ctc else None,
        'effective_to': row.end_of_ctc.isoformat() if row.end_of_ctc else None,
        'notes': row.ext_title or row.int_title or None,
    }


def _sync_emp_master_mirror(employee) -> None:
    from .models import EmpMasterMirror

    EmpMasterMirror.objects.update_or_create(
        emp_id=employee.emp_id,
        defaults={
            'first_name': employee.first_name,
            'middle_name': '',
            'last_name': employee.last_name,
            'start_date': employee.start_date,
            'end_date': employee.end_date,
        },
    )


def _sync_emp_bank_info_mirror(employee) -> None:
    from .models import EmpBankInfoMirror

    bank = getattr(employee, 'bank_detail', None)
    existing = EmpBankInfoMirror.objects.filter(emp_id=employee.emp_id).order_by('emp_bank_id').first()
    if bank:
        values = {
            'emp_id': employee.emp_id,
            'bank_acct_no': bank.account_number,
            'ifsc_code': bank.ifsc_code,
            'branch_name': bank.branch_name,
            'bank_name': bank.bank_name,
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
            existing.save()
        else:
            EmpBankInfoMirror.objects.create(**values)
    else:
        if not existing:
            EmpBankInfoMirror.objects.create(
                emp_id=employee.emp_id,
                bank_acct_no='',
                ifsc_code='',
                branch_name='',
                bank_name='',
            )


def _sync_emp_compliance_master_mirror(employee, doc_type: str, status: str, doc_url: str) -> None:
    ComplianceModel = _get_compliance_model()

    ComplianceModel.objects.update_or_create(
        emp_id=employee.emp_id,
        comp_type=doc_type,
        defaults={
            'status': status,
            'doc_url': doc_url or '',
        },
    )


def _sync_emp_ctc_master_mirror(employee, role_row) -> None:
    CTCModel = _get_ctc_model()

    EmpIdInt = _to_int_emp_id(employee.emp_id)
    if EmpIdInt is None:
        return

    CTCModel.objects.update_or_create(
        emp_id=EmpIdInt,
        start_of_ctc=role_row.effective_from,
        defaults={
            'int_title': (role_row.role_title or '')[:30],
            'ext_title': (role_row.role_title or '')[:60],
            'main_level': None,
            'sub_level': '',
            'end_of_ctc': role_row.effective_to,
            'ctc_amt': role_row.annual_ctc,
        },
    )


class HealthView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({'status': 'ok'})


class ApiLoginView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        payload = _json_body(request)
        username_raw = (payload.get('username') or '').strip()
        password = (payload.get('password') or '').strip()

        if not username_raw or not password:
            return JsonResponse({'error': 'Please enter username and password.'}, status=400)

        result, error = _post_external_or_error(
            url_env='LOGIN_THROUGH_PASSWORD_URL',
            payload={
                'email': username_raw,
                'password': password,
                'system_name': SYSTEM_NAME,
            },
            failure_status=401,
            failure_default_message='Invalid username or password.',
        )
        if error:
            return error

        session_payload = {'email': username_raw}
        session_payload.update(result or {})
        raw_token, expires_at = create_signed_session(payload=session_payload)

        return JsonResponse(
            {
                'token': raw_token,
                'expires_at': expires_at.isoformat(),
                'user': {
                    'id': None,
                    'username': username_raw,
                },
            }
        )


class ApiForgotPasswordView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        payload = _json_body(request)
        email = (payload.get('email') or '').strip()
        password = (payload.get('password') or '').strip()

        if not email or not password:
            return JsonResponse({'error': 'Please enter email and password.'}, status=400)

        result, error = _post_external_or_error(
            url_env='FORGET_PASSWORD_URL',
            payload={
                'email': email,
                'password': password,
                'system_name': SYSTEM_NAME,
            },
            failure_status=400,
            failure_default_message='Unable to reset password.',
        )
        if error:
            return error

        return JsonResponse({'ok': True, 'message': _external_success_message(result or {})})


class ApiRegisterView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        payload = _json_body(request)
        display_name = (payload.get('display_name') or '').strip()
        email = (payload.get('email') or '').strip()
        phone_number = _normalize_phone(payload.get('phone_number') or '')
        password = (payload.get('password') or '').strip()

        if not display_name or not email or not phone_number or not password:
            return JsonResponse({'error': 'Please fill all required fields.'}, status=400)

        result, error = _post_external_or_error(
            url_env='REGISTER_URL',
            payload={
                'display_name': display_name,
                'email': email,
                'phone_number': phone_number,
                'password': password,
                'system_name': SYSTEM_NAME,
                'role': REGISTER_ROLE,
            },
            failure_status=400,
            failure_default_message='Unable to create account.',
        )
        if error:
            return error

        return JsonResponse({'ok': True, 'message': _external_success_message(result or {})})


class ApiMeView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        session_payload = _get_session_payload(request)
        if session_payload is None:
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        email = (session_payload.get('email') or '').strip() or None

        return JsonResponse(
            {
                'user': {
                    'id': None,
                    'username': email,
                },
                'member': {
                    'id': None,
                    'name': session_payload.get('display_name'),
                    'email': email,
                    'phone': session_payload.get('phone_number'),
                },
            }
        )


class ApiLogoutView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        return JsonResponse({'ok': True})


class ApiOtpRequestView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        payload = _json_body(request)
        channel = (payload.get('channel') or '').strip().lower()
        phone = _normalize_phone(payload.get('phone') or payload.get('username') or '')
        email = (payload.get('email') or payload.get('username') or '').strip()

        if channel not in {'whatsapp', 'email'}:
            return JsonResponse({'error': 'Invalid OTP channel.'}, status=400)

        if channel == 'whatsapp' and not phone:
            return JsonResponse({'error': 'Please enter mobile number.'}, status=400)
        if channel == 'email' and not email:
            return JsonResponse({'error': 'Please enter email id.'}, status=400)

        identifier = email if channel == 'email' else phone
        result, error = _post_external_or_error(
            url_env='SEND_OTP_URL',
            payload={
                'email': identifier,
                'type': channel,
                'system_name': SYSTEM_NAME,
            },
            failure_status=400,
            failure_default_message='Unable to request key',
        )
        if error:
            return error

        challenge_id, expires_at = create_signed_otp_challenge(email=identifier, channel=channel)
        return JsonResponse({'challenge_id': challenge_id, 'expires_at': expires_at.isoformat()})


class ApiOtpVerifyView(View):
    def post(self, request: HttpRequest) -> JsonResponse:
        payload = _json_body(request)
        challenge_id = payload.get('challenge_id')
        otp = (payload.get('otp') or '').strip()

        if not challenge_id or not otp:
            return JsonResponse({'error': 'Please enter OTP.'}, status=400)

        try:
            otp_payload = load_signed_otp_challenge(str(challenge_id))
        except ExternalAuthError as exc:
            return JsonResponse({'error': str(exc)}, status=401)

        email = (otp_payload.get('email') or '').strip()
        result, error = _post_external_or_error(
            url_env='VERIFY_OTP_URL',
            payload={
                'email': email,
                'otp': otp,
                'system_name': SYSTEM_NAME,
            },
            failure_status=401,
            failure_default_message='Invalid or expired OTP.',
        )
        if error:
            return error

        session_payload = {'email': email}
        session_payload.update(result or {})
        raw_token, expires_at = create_signed_session(payload=session_payload)

        return JsonResponse(
            {
                'token': raw_token,
                'expires_at': expires_at.isoformat(),
                'user': {'id': None, 'username': email},
            }
        )


# Employee Management Views

class ApiEmployeeListView(View):
    """List all employees with optional filtering and sorting."""
    
    def get(self, request: HttpRequest) -> JsonResponse:
        # TODO: Re-enable authentication after testing
        # Check if user is authenticated
        # session_payload = _get_session_payload(request)
        # if session_payload is None:
        #     return JsonResponse({'error': 'Unauthorized'}, status=401)
        
        from .models import EmpMasterMirror

        status_filter = request.GET.get('status')
        search = request.GET.get('search', '').strip()
        sort_by = request.GET.get('sort_by', '-created_at')
        order = request.GET.get('order', '').strip().lower()

        rows = EmpMasterMirror.objects.all()

        if search:
            rows = rows.filter(
                Q(emp_id__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        if sort_by in ['name', '-name']:
            prefix = '-' if sort_by.startswith('-') else ''
            if order in ['asc', 'desc']:
                prefix = '-' if order == 'desc' else ''
            rows = rows.order_by(f'{prefix}first_name', f'{prefix}last_name')
        else:
            direction = '-' if sort_by.startswith('-') else ''
            if order in ['asc', 'desc']:
                direction = '-' if order == 'desc' else ''
            rows = rows.order_by(f'{direction}start_date', f'{direction}emp_id')

        employees = [_mirror_to_employee_dict(row) for row in rows]
        if status_filter in {'active', 'exited'}:
            employees = [emp for emp in employees if emp['status'] == status_filter]

        return JsonResponse({'employees': employees})


class ApiEmployeeCreateView(View):
    """Create a new employee in emp_master."""

    def post(self, request: HttpRequest) -> JsonResponse:
        from .models import EmpMasterMirror

        payload = _json_body(request)

        emp_id = (payload.get('emp_id') or '').strip()
        first_name = (payload.get('first_name') or '').strip()
        last_name = (payload.get('last_name') or '').strip()
        start_date = payload.get('start_date')

        if not all([emp_id, first_name, last_name, start_date]):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        try:
            parsed_start_date = _parse_iso_date(start_date, 'start_date')
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        if EmpMasterMirror.objects.filter(emp_id=emp_id).exists():
            return JsonResponse({'error': 'Employee ID already exists.'}, status=400)

        try:
            employee = EmpMasterMirror.objects.create(
                emp_id=emp_id,
                first_name=first_name,
                middle_name='',
                last_name=last_name,
                start_date=parsed_start_date,
                end_date=None,
            )
            return JsonResponse({'employee': _mirror_to_employee_dict(employee)}, status=201)
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)


class ApiEmployeeDetailView(View):
    """Get or update a specific employee from emp_master."""

    def get(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        from .models import EmpMasterMirror

        try:
            employee = EmpMasterMirror.objects.get(emp_id=emp_id)
            return JsonResponse({'employee': _mirror_to_employee_dict(employee)})
        except EmpMasterMirror.DoesNotExist:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

    def put(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        from .models import EmpMasterMirror

        payload = _json_body(request)

        try:
            employee = EmpMasterMirror.objects.get(emp_id=emp_id)
        except EmpMasterMirror.DoesNotExist:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

        if 'first_name' in payload:
            first_name = (payload.get('first_name') or '').strip()
            if not first_name:
                return JsonResponse({'error': 'First name cannot be empty.'}, status=400)
            employee.first_name = first_name

        if 'last_name' in payload:
            last_name = (payload.get('last_name') or '').strip()
            if not last_name:
                return JsonResponse({'error': 'Last name cannot be empty.'}, status=400)
            employee.last_name = last_name

        if 'start_date' in payload:
            try:
                employee.start_date = _parse_iso_date(payload.get('start_date'), 'start_date')
            except ValueError as exc:
                return JsonResponse({'error': str(exc)}, status=400)

        try:
            employee.save()
            return JsonResponse({'employee': _mirror_to_employee_dict(employee)})
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)


class ApiEmployeeProfileView(View):
    """Unified employee profile response from linked tables."""

    def get(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        # TODO: Re-enable authentication after testing
        # session_payload = _get_session_payload(request)
        # if session_payload is None:
        #     return JsonResponse({'error': 'Unauthorized'}, status=401)

        from .models import EmpMasterMirror, EmpBankInfoMirror

        try:
            employee = EmpMasterMirror.objects.get(emp_id=emp_id)
        except EmpMasterMirror.DoesNotExist:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

        bank = EmpBankInfoMirror.objects.filter(emp_id=emp_id).order_by('emp_bank_id').first()
        ComplianceModel = _get_compliance_model()
        compliance_rows = list(ComplianceModel.objects.filter(emp_id=emp_id).order_by('comp_type'))
        emp_id_int = _to_int_emp_id(employee.emp_id)
        CTCModel = _get_ctc_model()
        ctc_rows = (
            list(CTCModel.objects.filter(emp_id=emp_id_int).order_by('-start_of_ctc'))
            if emp_id_int is not None
            else []
        )

        bank_payload = None
        if bank:
            bank_payload = {
                'bank_name': bank.bank_name or None,
                'account_holder_name': None,
                'account_number': bank.bank_acct_no or None,
                'ifsc_code': bank.ifsc_code or None,
                'branch_name': bank.branch_name or None,
                'updated_at': None,
            }

        compliance_payload = None
        if compliance_rows:
            compliance_payload = {
                'records': [
                    {
                        'comp_type': row.comp_type,
                        'status': row.status,
                        'doc_url': row.doc_url or None,
                    }
                    for row in compliance_rows
                ]
            }

        ctc_timeline = [
            {
                'effective_from': row.start_of_ctc.isoformat() if row.start_of_ctc else None,
                'annual_ctc': float(row.ctc_amt),
                'variable_pay': 0.0,
                'notes': row.ext_title or row.int_title or None,
            }
            for row in ctc_rows
        ]

        return JsonResponse(
            {
                'profile': {
                    'employee': _mirror_to_employee_dict(employee),
                    'bank': bank_payload,
                    'compliance': compliance_payload,
                    'ctc_timeline': ctc_timeline,
                    'missing_sections': [
                        name
                        for name, value in [
                            ('bank', bank_payload),
                            ('compliance', compliance_payload),
                            ('ctc_timeline', ctc_timeline if ctc_timeline else None),
                        ]
                        if not value
                    ],
                }
            }
        )


class ApiEmployeeOnboardingView(View):
    """Checklist tracking with completion progress per employee."""

    def get(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        from .models import EmpMasterMirror

        try:
            employee = EmpMasterMirror.objects.get(emp_id=emp_id)
        except EmpMasterMirror.DoesNotExist:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

        ComplianceModel = _get_compliance_model()
        comp_types = [item['comp_type'] for item in ONBOARDING_ITEM_DEFS]
        existing = {
            row.comp_type: row
            for row in ComplianceModel.objects.filter(emp_id=employee.emp_id, comp_type__in=comp_types)
        }

        items = []
        completed_count = 0
        for item_def in ONBOARDING_ITEM_DEFS:
            row = existing.get(item_def['comp_type'])
            is_completed = bool(row and row.status in {'verified', 'completed'})
            if is_completed:
                completed_count += 1
            items.append(
                {
                    'id': item_def['id'],
                    'item_name': item_def['item_name'],
                    'is_completed': is_completed,
                    'document_ref': (row.doc_url if row else '') or '',
                    'completed_at': None,
                }
            )

        total_count = len(items)
        progress = round((completed_count / total_count) * 100, 2) if total_count else 0

        return JsonResponse(
            {
                'employee': _mirror_to_employee_dict(employee),
                'items': items,
                'completed_count': completed_count,
                'total_count': total_count,
                'progress_percentage': progress,
            }
        )

    def post(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        from .models import EmpMasterMirror

        try:
            employee = EmpMasterMirror.objects.get(emp_id=emp_id)
        except EmpMasterMirror.DoesNotExist:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

        payload = _json_body(request)
        item_id = payload.get('item_id')
        if not item_id:
            return JsonResponse({'error': 'item_id is required.'}, status=400)

        try:
            item_id_int = int(item_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'item_id must be a number.'}, status=400)

        item_def = next((item for item in ONBOARDING_ITEM_DEFS if item['id'] == item_id_int), None)
        if item_def is None:
            return JsonResponse({'error': 'Checklist item not found.'}, status=404)

        is_completed = payload.get('is_completed')
        document_ref = payload.get('document_ref')

        defaults = {}
        if document_ref is not None:
            defaults['doc_url'] = str(document_ref).strip()
            if is_completed is None:
                is_completed = True
        if is_completed is not None:
            defaults['status'] = 'verified' if bool(is_completed) else 'pending'

        if not defaults:
            return JsonResponse({'error': 'Nothing to update.'}, status=400)

        ComplianceModel = _get_compliance_model()
        row, _ = ComplianceModel.objects.update_or_create(
            emp_id=employee.emp_id,
            comp_type=item_def['comp_type'],
            defaults=defaults,
        )

        item = {
            'id': item_def['id'],
            'item_name': item_def['item_name'],
            'is_completed': row.status in {'verified', 'completed'},
            'document_ref': row.doc_url or '',
            'completed_at': None,
        }
        return JsonResponse({'item': item})


class ApiOnboardingProgressView(View):
    """HR view of onboarding progress across employees."""

    def get(self, request: HttpRequest) -> JsonResponse:
        from .models import EmpMasterMirror

        rows = []
        ComplianceModel = _get_compliance_model()
        comp_types = [item['comp_type'] for item in ONBOARDING_ITEM_DEFS]
        total_count = len(ONBOARDING_ITEM_DEFS)
        for employee in EmpMasterMirror.objects.all().order_by('emp_id'):
            existing = {
                row.comp_type: row
                for row in ComplianceModel.objects.filter(emp_id=employee.emp_id, comp_type__in=comp_types)
            }
            completed_count = sum(
                1
                for item_def in ONBOARDING_ITEM_DEFS
                if existing.get(item_def['comp_type']) and existing[item_def['comp_type']].status in {'verified', 'completed'}
            )
            progress = round((completed_count / total_count) * 100, 2) if total_count else 0
            rows.append(
                {
                    'emp_id': str(employee.emp_id),
                    'full_name': f'{employee.first_name} {employee.last_name}'.strip(),
                    'status': _mirror_status(employee.end_date),
                    'completed_count': completed_count,
                    'total_count': total_count,
                    'progress_percentage': progress,
                }
            )

        return JsonResponse({'progress': rows})


class ApiEmployeeRoleChangeView(View):
    """Add/list role + CTC history with date-range checks."""

    def get(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        from .models import EmpMasterMirror

        employee = _get_emp_master(emp_id)
        if employee is None:
            return JsonResponse({'error': 'Employee not found.'}, status=404)
        emp_id_int = _to_int_emp_id(employee.emp_id)
        if emp_id_int is None:
            return JsonResponse({'error': 'Employee ID must be numeric for CTC records.'}, status=400)

        CTCModel = _get_ctc_model()
        timeline = [
            _ctc_row_to_timeline(row)
            for row in CTCModel.objects.filter(emp_id=emp_id_int).order_by('-start_of_ctc', '-emp_ctc_id')
        ]

        return JsonResponse(
            {
                'employee': _mirror_to_employee_dict(employee),
                'timeline': timeline,
            }
        )

    def post(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        from .models import EmpMasterMirror

        employee = _get_emp_master(emp_id)
        if employee is None:
            return JsonResponse({'error': 'Employee not found.'}, status=404)
        emp_id_int = _to_int_emp_id(employee.emp_id)
        if emp_id_int is None:
            return JsonResponse({'error': 'Employee ID must be numeric for CTC records.'}, status=400)

        payload = _json_body(request)
        role_title = (payload.get('role_title') or '').strip()
        role_level = (payload.get('role_level') or '').strip()
        annual_ctc = payload.get('annual_ctc')
        effective_from = payload.get('effective_from')
        effective_to = payload.get('effective_to')
        notes = (payload.get('notes') or '').strip()

        if not all([role_title, role_level, annual_ctc, effective_from]):
            return JsonResponse({'error': 'Missing required fields.'}, status=400)

        try:
            parsed_from = _parse_iso_date(effective_from, 'effective_from')
            parsed_to = _parse_iso_date(effective_to, 'effective_to') if effective_to else None
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        if parsed_to and parsed_to < parsed_from:
            return JsonResponse({'error': 'effective_to cannot be before effective_from.'}, status=400)

        try:
            CTCModel = _get_ctc_model()
            existing_rows = CTCModel.objects.filter(emp_id=emp_id_int)
            new_start = parsed_from
            new_end = parsed_to or date.max
            for old in existing_rows:
                old_start = old.start_of_ctc
                old_end = old.end_of_ctc or date.max
                if old_start <= new_end and new_start <= old_end:
                    return JsonResponse({'error': 'Role change dates overlap with an existing record.'}, status=400)

            main_level, sub_level = _parse_role_level_parts(role_level)
            ctc_value = int(float(annual_ctc))
            row = CTCModel.objects.create(
                emp_id=emp_id_int,
                int_title=role_title[:30],
                ext_title=(notes or role_title)[:60],
                main_level=main_level if main_level is not None else 0,
                sub_level=sub_level or '0',
                start_of_ctc=parsed_from,
                end_of_ctc=parsed_to,
                ctc_amt=ctc_value,
            )
        except Exception as exc:
            return JsonResponse({'error': f'Failed to save role change: {exc}'}, status=500)

        return JsonResponse({'record': _ctc_row_to_timeline(row)}, status=201)


class ApiEmployeeExitWorkflowView(View):
    """Capture last working day and structured clearances."""

    def get(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        employee = _get_emp_master(emp_id)
        if employee is None:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

        workflow = None
        if employee.end_date:
            workflow = {
                'last_working_day': employee.end_date.isoformat(),
                'reason': None,
                'it_clearance': False,
                'hr_clearance': False,
                'finance_clearance': False,
                'remarks': None,
                'updated_at': None,
            }
        return JsonResponse(
            {
                'employee': _mirror_to_employee_dict(employee),
                'workflow': workflow,
            }
        )

    def post(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        employee = _get_emp_master(emp_id)
        if employee is None:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

        payload = _json_body(request)
        last_working_day = payload.get('last_working_day')

        if not last_working_day:
            return JsonResponse({'error': 'last_working_day is required.'}, status=400)

        try:
            parsed_lwd = _parse_iso_date(last_working_day, 'last_working_day')
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        if employee.start_date and parsed_lwd < employee.start_date:
            return JsonResponse({'error': 'last_working_day cannot be before start_date.'}, status=400)

        employee.end_date = parsed_lwd
        employee.save()

        workflow = {
            'last_working_day': parsed_lwd.isoformat(),
            'reason': (payload.get('reason') or '').strip() or None,
            'it_clearance': bool(payload.get('it_clearance')),
            'hr_clearance': bool(payload.get('hr_clearance')),
            'finance_clearance': bool(payload.get('finance_clearance')),
            'remarks': (payload.get('remarks') or '').strip() or None,
            'updated_at': timezone.now().isoformat(),
        }
        return JsonResponse({'workflow': workflow, 'employee': _mirror_to_employee_dict(employee)})


class ApiEmployeeDocumentsView(View):
    """Upload/add compliance document entries and list by employee."""

    def get(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        employee = _get_emp_master(emp_id)
        if employee is None:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

        ComplianceModel = _get_compliance_model()
        docs = list(ComplianceModel.objects.filter(emp_id=employee.emp_id).order_by('comp_type'))

        return JsonResponse(
            {
                'employee': _mirror_to_employee_dict(employee),
                'documents': [
                    {
                        'id': doc.emp_compliance_tracker_id,
                        'doc_type': doc.comp_type,
                        'doc_number': None,
                        'doc_link': doc.doc_url,
                        'status': doc.status,
                        'uploaded_at': None,
                        'verified_at': None,
                        'remarks': None,
                    }
                    for doc in docs
                ],
            }
        )

    def post(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        employee = _get_emp_master(emp_id)
        if employee is None:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

        payload = _json_body(request)
        doc_type = (payload.get('doc_type') or '').strip().upper()
        doc_number = (payload.get('doc_number') or '').strip()
        doc_link = (payload.get('doc_link') or '').strip()
        remarks = (payload.get('remarks') or '').strip()

        if not doc_type or not doc_link:
            return JsonResponse({'error': 'doc_type and doc_link are required.'}, status=400)

        ComplianceModel = _get_compliance_model()
        document, _ = ComplianceModel.objects.update_or_create(
            emp_id=employee.emp_id,
            comp_type=doc_type,
            defaults={
                'status': 'pending',
                'doc_url': doc_link,
            },
        )
        return JsonResponse(
            {
                'document': {
                    'id': document.emp_compliance_tracker_id,
                    'doc_type': document.comp_type,
                    'doc_number': doc_number or None,
                    'doc_link': document.doc_url,
                    'status': document.status,
                    'uploaded_at': None,
                    'verified_at': None,
                    'remarks': remarks or None,
                }
            },
            status=201,
        )


class ApiEmployeeDocumentStatusView(View):
    """Update verification status for a compliance document."""

    def post(self, request: HttpRequest, emp_id: str, doc_id: int) -> JsonResponse:
        employee = _get_emp_master(emp_id)
        if employee is None:
            return JsonResponse({'error': 'Employee not found.'}, status=404)

        ComplianceModel = _get_compliance_model()
        try:
            document = ComplianceModel.objects.get(emp_compliance_tracker_id=doc_id, emp_id=employee.emp_id)
        except ComplianceModel.DoesNotExist:
            return JsonResponse({'error': 'Document not found.'}, status=404)

        payload = _json_body(request)
        status = (payload.get('status') or '').strip().lower()
        remarks = (payload.get('remarks') or '').strip()
        if status not in {'pending', 'verified'}:
            return JsonResponse({'error': 'status must be pending or verified.'}, status=400)

        document.status = status
        if remarks and not document.doc_url:
            document.doc_url = remarks[:255]
        document.save()
        return JsonResponse(
            {
                'document': {
                    'id': document.emp_compliance_tracker_id,
                    'doc_type': document.comp_type,
                    'doc_number': None,
                    'doc_link': document.doc_url,
                    'status': document.status,
                    'uploaded_at': None,
                    'verified_at': timezone.now().isoformat() if status == 'verified' else None,
                    'remarks': remarks or None,
                }
            }
        )


class ApiComplianceDashboardView(View):
    """Compliance metrics and employee gap list."""

    def get(self, request: HttpRequest) -> JsonResponse:
        from .models import EmpMasterMirror

        ComplianceModel = _get_compliance_model()
        active_employees = list(EmpMasterMirror.objects.filter(end_date__isnull=True))
        total_employees = len(active_employees)
        employees_with_missing = 0
        pending_verifications = 0
        verified_docs = 0
        gap_list = []

        for employee in active_employees:
            docs = list(ComplianceModel.objects.filter(emp_id=employee.emp_id))
            by_type = {doc.comp_type: doc for doc in docs}
            missing_types = [d for d in REQUIRED_COMPLIANCE_DOCS if d not in by_type]
            pending_docs = [doc for doc in docs if (doc.status or '').lower() == 'pending']
            verified_docs += len([doc for doc in docs if doc.status == 'verified'])
            pending_verifications += len(pending_docs)

            if missing_types or pending_docs:
                employees_with_missing += 1
                gap_list.append(
                    {
                        'emp_id': str(employee.emp_id),
                        'full_name': f'{employee.first_name} {employee.last_name}'.strip(),
                        'missing_docs': missing_types,
                        'pending_docs': [doc.comp_type for doc in pending_docs],
                    }
                )

        return JsonResponse(
            {
                'metrics': {
                    'active_employees': total_employees,
                    'employees_with_gaps': employees_with_missing,
                    'pending_verifications': pending_verifications,
                    'verified_documents': verified_docs,
                },
                'employees_with_gaps': gap_list,
                'required_doc_types': REQUIRED_COMPLIANCE_DOCS,
            }
        )


class ApiComplianceAlertsView(View):
    """Alerts for pending verifications and missing compliance docs."""

    def get(self, request: HttpRequest) -> JsonResponse:
        from .models import EmpMasterMirror

        ComplianceModel = _get_compliance_model()
        alerts = []
        for employee in EmpMasterMirror.objects.filter(end_date__isnull=True):
            docs = list(ComplianceModel.objects.filter(emp_id=employee.emp_id))
            doc_types = {doc.comp_type for doc in docs}
            missing = [d for d in REQUIRED_COMPLIANCE_DOCS if d not in doc_types]
            pending = [doc for doc in docs if (doc.status or '').lower() == 'pending']

            for doc_type in missing:
                alerts.append(
                    {
                        'type': 'missing_document',
                        'emp_id': str(employee.emp_id),
                        'employee_name': f'{employee.first_name} {employee.last_name}'.strip(),
                        'message': f'Missing required document: {doc_type}',
                    }
                )

            for doc in pending:
                alerts.append(
                    {
                        'type': 'pending_verification',
                        'emp_id': str(employee.emp_id),
                        'employee_name': f'{employee.first_name} {employee.last_name}'.strip(),
                        'message': f'Pending verification: {doc.comp_type}',
                    }
                )

        return JsonResponse({'alerts': alerts, 'count': len(alerts)})


class ApiHeadcountReportView(View):
    """Headcount summary of total, active, and exited employees."""

    def get(self, request: HttpRequest) -> JsonResponse:
        from .models import EmpMasterMirror

        total = EmpMasterMirror.objects.count()
        active = EmpMasterMirror.objects.filter(end_date__isnull=True).count()
        exited = EmpMasterMirror.objects.filter(end_date__isnull=False).count()

        return JsonResponse(
            {
                'summary': {
                    'total_employees': total,
                    'active_employees': active,
                    'exited_employees': exited,
                }
            }
        )


class ApiJoinersLeaversReportView(View):
    """Month-wise joiner and leaver counts within date range."""

    def get(self, request: HttpRequest) -> JsonResponse:
        from .models import EmpMasterMirror
        from collections import defaultdict

        start_raw = request.GET.get('start')
        end_raw = request.GET.get('end')

        try:
            start_date = _parse_iso_date(start_raw, 'start') if start_raw else date(2024, 1, 1)
            end_date = _parse_iso_date(end_raw, 'end') if end_raw else date.today()
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        if end_date < start_date:
            return JsonResponse({'error': 'end cannot be before start.'}, status=400)

        joiners = defaultdict(int)
        leavers = defaultdict(int)

        for emp in EmpMasterMirror.objects.filter(start_date__gte=start_date, start_date__lte=end_date):
            key = emp.start_date.strftime('%Y-%m')
            joiners[key] += 1

        for emp in EmpMasterMirror.objects.filter(end_date__isnull=False, end_date__gte=start_date, end_date__lte=end_date):
            key = emp.end_date.strftime('%Y-%m')
            leavers[key] += 1

        cursor = date(start_date.year, start_date.month, 1)
        end_month = date(end_date.year, end_date.month, 1)
        rows = []
        while cursor <= end_month:
            key = cursor.strftime('%Y-%m')
            rows.append({'month': key, 'joiners': joiners.get(key, 0), 'leavers': leavers.get(key, 0)})
            if cursor.month == 12:
                cursor = date(cursor.year + 1, 1, 1)
            else:
                cursor = date(cursor.year, cursor.month + 1, 1)

        return JsonResponse({'start': start_date.isoformat(), 'end': end_date.isoformat(), 'monthly': rows})


class ApiCTCLevelDistributionReportView(View):
    """Distribution across salary bands and job levels."""

    def get(self, request: HttpRequest) -> JsonResponse:
        from .models import EmpMasterMirror

        level_counts = {}
        salary_bands = {
            'Below 7L': 0,
            '7L - 12L': 0,
            'Above 12L': 0,
        }
        employees = EmpMasterMirror.objects.filter(end_date__isnull=True)
        rows = []
        CTCModel = _get_ctc_model()

        for emp in employees:
            emp_id_int = _to_int_emp_id(emp.emp_id)
            latest_ctc = (
                CTCModel.objects.filter(emp_id=emp_id_int).order_by('-start_of_ctc', '-emp_ctc_id').first()
                if emp_id_int is not None
                else None
            )
            level = _format_role_level(latest_ctc.main_level if latest_ctc else None, latest_ctc.sub_level if latest_ctc else '')
            ctc = float(latest_ctc.ctc_amt) if latest_ctc else 0.0

            level_counts[level] = level_counts.get(level, 0) + 1

            if ctc < 700000:
                salary_bands['Below 7L'] += 1
                band = 'Below 7L'
            elif ctc <= 1200000:
                salary_bands['7L - 12L'] += 1
                band = '7L - 12L'
            else:
                salary_bands['Above 12L'] += 1
                band = 'Above 12L'

            rows.append(
                {
                    'emp_id': str(emp.emp_id),
                    'full_name': f'{emp.first_name} {emp.last_name}'.strip(),
                    'level': level,
                    'annual_ctc': ctc,
                    'salary_band': band,
                }
            )

        return JsonResponse({'salary_bands': salary_bands, 'level_counts': level_counts, 'employees': rows})


class ApiComplianceStatusReportView(View):
    """Employee-wise compliance status with filters by status/type."""

    def get(self, request: HttpRequest) -> JsonResponse:
        from .models import EmpMasterMirror

        status_filter = (request.GET.get('status') or '').strip().lower()
        doc_type_filter = (request.GET.get('doc_type') or '').strip().upper()

        ComplianceModel = _get_compliance_model()
        rows = []
        for emp in EmpMasterMirror.objects.filter(end_date__isnull=True):
            docs = list(ComplianceModel.objects.filter(emp_id=emp.emp_id))
            for doc in docs:
                if status_filter and doc.status != status_filter:
                    continue
                if doc_type_filter and doc.comp_type != doc_type_filter:
                    continue
                rows.append(
                    {
                        'emp_id': str(emp.emp_id),
                        'full_name': f'{emp.first_name} {emp.last_name}'.strip(),
                        'doc_type': doc.comp_type,
                        'status': doc.status,
                        'doc_link': doc.doc_url,
                        'uploaded_at': None,
                    }
                )

            existing = {doc.comp_type for doc in docs}
            for req in REQUIRED_COMPLIANCE_DOCS:
                if req not in existing and (not doc_type_filter or doc_type_filter == req):
                    if status_filter in {'', 'missing'}:
                        rows.append(
                            {
                                'emp_id': str(emp.emp_id),
                                'full_name': f'{emp.first_name} {emp.last_name}'.strip(),
                                'doc_type': req,
                                'status': 'missing',
                                'doc_link': None,
                                'uploaded_at': None,
                            }
                        )

        return JsonResponse({'rows': rows, 'filters': {'status': status_filter or None, 'doc_type': doc_type_filter or None}})


class ApiEmployeeExitView(View):
    """Mark an employee as exited."""
    
    def post(self, request: HttpRequest, emp_id: str) -> JsonResponse:
        payload = _json_body(request)
        end_date = payload.get('end_date')
        
        if not end_date:
            return JsonResponse({'error': 'End date is required.'}, status=400)
        
        employee = _get_emp_master(emp_id)
        if employee is None:
            return JsonResponse({'error': 'Employee not found.'}, status=404)
        
        try:
            parsed_end = _parse_iso_date(end_date, 'end_date')
            if employee.start_date and parsed_end < employee.start_date:
                return JsonResponse({'error': 'End date cannot be earlier than start date.'}, status=400)
            employee.end_date = parsed_end
            employee.save()
            return JsonResponse({'employee': _mirror_to_employee_dict(employee)})
        except ValueError as exc:
            return JsonResponse({'error': str(exc)}, status=400)
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)


