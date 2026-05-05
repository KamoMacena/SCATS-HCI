from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.utils import timezone
from .models import Case, Complaint, CaseTransfer, AuditLog
import json
from datetime import datetime, timedelta
import csv


# ==================== HELPER FUNCTION ====================

def get_commander_info(request):
    return {
        'name': 'Col. Zanele Mthembu',
        'rank': 'Station Commander',
        'station': 'Johannesburg Central',
        'email': 'zanele.mthembu@saps.gov.za',
    }


# ==================== NO MOCK DATA - ONLY REAL DATASET ====================

# ==================== SIGN OUT ====================

def sign_out(request):
    logout(request)
    return redirect('/login/')


# ==================== EXPORT FUNCTIONS ====================

def export_cases_excel(request):
    cases = Case.objects.filter(status__in=['AT_RISK', 'STALLED'])
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="flagged_cases_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['CAS Number', 'Crime Category', 'Status', 'Days Inactive', 'Assigned Detective', 'Reported Date', 'Acknowledged'])
    for case in cases:
        writer.writerow([case.case_number, case.crime_category, case.status, case.days_inactive, case.assigned_detective or 'Unassigned', case.reported_date.strftime('%Y-%m-%d'), 'Yes' if case.acknowledged else 'No'])
    return response

def export_alerts_excel(request):
    cases = Case.objects.filter(status__in=['AT_RISK', 'STALLED'], acknowledged=False)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alerts_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['CAS Number', 'Crime Category', 'Status', 'Days Inactive', 'Alert Created'])
    for case in cases:
        writer.writerow([case.case_number, case.crime_category, case.status, case.days_inactive, case.created_at.strftime('%Y-%m-%d %H:%M')])
    return response

def export_transfers_excel(request):
    transfers = CaseTransfer.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transfers_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Transfer Number', 'Case Number', 'From Detective', 'To Detective', 'From Station', 'To Station', 'Reason', 'Status', 'Request Date'])
    for transfer in transfers:
        writer.writerow([transfer.transfer_number, transfer.case.case_number, transfer.from_detective, transfer.to_detective, transfer.from_station, transfer.to_station, transfer.reason, transfer.status, transfer.request_date.strftime('%Y-%m-%d %H:%M')])
    return response

def export_complaints_excel(request):
    complaints = Complaint.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="complaints_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['Complaint Number', 'Case Number', 'Complainant Name', 'Complaint', 'Status', 'Created At'])
    for complaint in complaints:
        writer.writerow([complaint.complaint_number, complaint.case.case_number if complaint.case else 'N/A', complaint.complainant_name, complaint.complaint_text, complaint.status, complaint.created_at.strftime('%Y-%m-%d %H:%M')])
    return response


# ==================== API ENDPOINT FOR PENDING ASSIGNMENTS ====================

@csrf_exempt
@require_http_methods(["GET"])
def pending_assignments_api(request):
    """Get count of new cases needing assignment for real-time notifications"""
    try:
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        unassigned_cases = Case.objects.filter(
            assigned_detective__isnull=True
        ) | Case.objects.filter(assigned_detective='') | Case.objects.filter(assigned_detective='Unassigned')
        
        today_new_cases = unassigned_cases.filter(reported_date__gte=today_start)
        
        return JsonResponse({
            'success': True,
            'new_cases_count': today_new_cases.count(),
            'total_pending': unassigned_cases.count()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ==================== MAIN VIEWS ====================

def dashboard(request):
    commander = get_commander_info(request)
    cases = Case.objects.all()
    
    # Statistics
    total_cases = cases.count()
    active_cases = cases.filter(status='ACTIVE').count()
    at_risk_cases = cases.filter(status='AT_RISK').count()
    stalled_cases = cases.filter(status='STALLED').count()
    solved_cases = cases.filter(status='CASE_CLOSED').count()
    alert_count = cases.filter(status__in=['AT_RISK', 'STALLED'], acknowledged=False).count()
    
    # Get crime categories directly from your database
    crime_categories = list(cases.values_list('crime_category', flat=True).distinct())
    
    # If no categories found, use defaults (this will only show if database is empty)
    if not crime_categories:
        crime_categories = ['Robbery', 'Theft', 'Fraud', 'Assault', 'Burglary']
    
    crime_data = []
    for crime in crime_categories:
        crime_data.append(cases.filter(crime_category=crime).count())
    
    # Detective workload
    detectives = ['Det. Molefe', 'Det. Nkosi', 'Det. Dlamini', 'Det. Cele', 'Det. van Zyl', 'Det. Botha', 'Unassigned']
    detective_workload = []
    for detective in detectives:
        count = cases.filter(assigned_detective=detective).count()
        percentage = round((count / total_cases) * 100, 1) if total_cases > 0 else 0
        detective_workload.append({'name': detective, 'case_count': count, 'percentage': percentage})
    
    # Chart data
    chart_labels = ['Active', 'At Risk', 'Stalled', 'Solved']
    chart_data = [active_cases, at_risk_cases, stalled_cases, solved_cases]
    recent_activities = cases.order_by('-updated_at')[:5]
    
    # Unassigned cases
    all_unassigned = cases.filter(assigned_detective__isnull=True) | cases.filter(assigned_detective='') | cases.filter(assigned_detective='Unassigned')
    today_start = timezone.make_aware(datetime.combine(timezone.now().date(), datetime.min.time()))
    today_unassigned_cases = all_unassigned.filter(reported_date__gte=today_start)
    
    context = {
        'commander': commander,
        'total_cases': total_cases,
        'active_cases': active_cases,
        'at_risk_cases': at_risk_cases,
        'stalled_cases': stalled_cases,
        'solved_cases': solved_cases,
        'alert_count': alert_count,
        'crime_labels': crime_categories,
        'crime_data': crime_data,
        'detective_workload': detective_workload,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'recent_activities': recent_activities,
        'unassigned_cases': all_unassigned,
        'today_unassigned_cases': today_unassigned_cases,
    }
    return render(request, 'commander/dashboard.html', context)

def alerts_center(request):
    commander = get_commander_info(request)
    # Only unacknowledged At Risk and Stalled cases from YOUR DATASET
    cases = Case.objects.filter(status__in=['AT_RISK', 'STALLED'], acknowledged=False)
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    if search_query:
        cases = cases.filter(case_number__icontains=search_query)
    if status_filter:
        cases = cases.filter(status=status_filter)
    alert_list = []
    for case in cases:
        alert_list.append({
            'cas_number': case.case_number,
            'crime_category': case.crime_category,
            'stall_status': case.status,
            'days_inactive': case.days_inactive,
            'acknowledged': case.acknowledged,
            'assigned_detective': case.assigned_detective or 'Unassigned',
            'created_at': case.created_at.strftime('%d %b %Y, %H:%M') if case.created_at else None,
        })
    detective_list = ['Det. Molefe', 'Det. Nkosi', 'Det. Dlamini', 'Det. Cele', 'Det. van Zyl', 'Det. Botha']
    context = {
        'commander': commander,
        'alerts': alert_list,
        'unacknowledged_count': len(alert_list),
        'alert_count': len(alert_list),
        'detective_list': detective_list,
        'search_query': search_query,
        'selected_status': status_filter,
    }
    return render(request, 'commander/alerts.html', context)

def flagged_cases(request):
    commander = get_commander_info(request)
    # All At Risk and Stalled cases from YOUR DATASET
    cases = Case.objects.filter(status__in=['AT_RISK', 'STALLED'])
    status_filter = request.GET.get('status')
    crime_filter = request.GET.get('crime')
    search_query = request.GET.get('search')
    if status_filter and status_filter != "ALL":
        cases = cases.filter(status=status_filter)
    if crime_filter and crime_filter != "ALL":
        cases = cases.filter(crime_category=crime_filter)
    if search_query:
        cases = cases.filter(case_number__icontains=search_query)
    detective_list = ['Unassigned', 'Det. Molefe', 'Det. Nkosi', 'Det. Dlamini', 'Det. Cele', 'Det. van Zyl', 'Det. Botha']
    context = {
        'cases': cases,
        'commander': commander,
        'total_flagged': cases.count(),
        'at_risk_count': cases.filter(status='AT_RISK').count(),
        'stalled_count': cases.filter(status='STALLED').count(),
        'alert_count': Case.objects.filter(status__in=['AT_RISK', 'STALLED']).count(),
        'detective_list': detective_list,
        'selected_status': status_filter if status_filter else "ALL",
        'selected_crime': crime_filter if crime_filter else "ALL",
        'search_query': search_query or "",
    }
    return render(request, 'commander/flagged_cases.html', context)

def complaints_view(request):
    commander = get_commander_info(request)
    complaints = Complaint.objects.all()
    total_count = complaints.count()
    pending_count = complaints.filter(status='PENDING').count()
    review_count = complaints.filter(status='IN_REVIEW').count()
    resolved_count = complaints.filter(status='RESOLVED').count()
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    case_filter = request.GET.get('case', '')
    if search_query:
        complaints = complaints.filter(complainant_name__icontains=search_query)
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    if case_filter:
        complaints = complaints.filter(case__case_number__icontains=case_filter)
    alert_count = Case.objects.filter(status__in=['AT_RISK', 'STALLED'], acknowledged=False).count()
    context = {
        'commander': commander,
        'complaints': complaints,
        'alert_count': alert_count,
        'total_count': total_count,
        'pending_count': pending_count,
        'review_count': review_count,
        'resolved_count': resolved_count,
        'search_query': search_query,
        'selected_status': status_filter,
        'case_filter': case_filter,
    }
    return render(request, 'commander/complaints.html', context)

def transfers_view(request):
    commander = get_commander_info(request)
    pending_transfers = CaseTransfer.objects.filter(status='PENDING')
    completed_transfers = CaseTransfer.objects.exclude(status='PENDING')
    approved_count = CaseTransfer.objects.filter(status='APPROVED').count()
    rejected_count = CaseTransfer.objects.filter(status='REJECTED').count()
    initiated_count = CaseTransfer.objects.filter(initiated_by=commander['name']).count()
    avg_approval_days = 0
    approved_transfers = CaseTransfer.objects.filter(status='APPROVED', approved_at__isnull=False)
    if approved_transfers.exists():
        total_days = 0
        for transfer in approved_transfers:
            if transfer.approved_at and transfer.request_date:
                total_days += (transfer.approved_at - transfer.request_date).days
        avg_approval_days = round(total_days / approved_transfers.count(), 1)
    alert_count = Case.objects.filter(status__in=['AT_RISK', 'STALLED'], acknowledged=False).count()
    context = {
        'commander': commander,
        'pending_transfers': pending_transfers,
        'completed_transfers': completed_transfers,
        'alert_count': alert_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'initiated_count': initiated_count,
        'avg_approval_days': avg_approval_days,
    }
    return render(request, 'commander/transfers.html', context)

def audit_trail(request, case_number):
    commander = get_commander_info(request)
    case = get_object_or_404(Case, case_number=case_number)
    audit_logs = AuditLog.objects.filter(case=case).order_by('-timestamp')
    alert_count = Case.objects.filter(status__in=['AT_RISK', 'STALLED'], acknowledged=False).count()
    return render(request, 'commander/audit_trail.html', {'commander': commander, 'case': case, 'audit_logs': audit_logs, 'alert_count': alert_count})


# ==================== API ENDPOINTS ====================

@csrf_exempt
@require_http_methods(["POST"])
def assign_detective(request):
    try:
        data = json.loads(request.body)
        case = Case.objects.get(case_number=data.get('case_number'))
        old = case.assigned_detective
        case.assigned_detective = data.get('detective_name')
        case.save()
        AuditLog.objects.create(case=case, action_type='UPDATED', action_description=f"Detective assigned: {old or 'Unassigned'} → {case.assigned_detective}", performed_by=get_commander_info(request)['name'], performed_by_role="COMMANDER")
        return JsonResponse({'success': True, 'message': f'Detective assigned'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def approve_transfer(request, transfer_number):
    try:
        data = json.loads(request.body)
        transfer = CaseTransfer.objects.get(transfer_number=transfer_number)
        if data.get('action') == 'approve':
            transfer.status = 'APPROVED'
            transfer.approved_by = get_commander_info(request)['name']
            transfer.approved_at = timezone.now()
        else:
            transfer.status = 'REJECTED'
        transfer.save()
        if transfer.status == 'APPROVED':
            case = transfer.case
            case.assigned_detective = transfer.to_detective
            case.save()
        AuditLog.objects.create(case=transfer.case, action_type='TRANSFER_UPDATED', action_description=f"Transfer {transfer_number} {transfer.status}", performed_by=get_commander_info(request)['name'], performed_by_role="COMMANDER")
        return JsonResponse({'success': True, 'message': f'Transfer {transfer_number} {transfer.status}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def approve_backward_stage(request, case_number):
    try:
        data = json.loads(request.body)
        case = Case.objects.get(case_number=case_number)
        old_stage = case.status
        case.status = data.get('new_stage')
        case.save()
        AuditLog.objects.create(case=case, action_type='STAGE_CHANGED', action_description=f"Backward transition: {old_stage} → {case.status}. Reason: {data.get('reason', '')}", performed_by=get_commander_info(request)['name'], performed_by_role="COMMANDER")
        return JsonResponse({'success': True, 'message': f'Case moved to {case.status}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def acknowledge_alert_api(request):
    try:
        data = json.loads(request.body)
        case = Case.objects.get(case_number=data.get('cas_number'))
        case.acknowledged = True
        case.acknowledged_at = timezone.now()
        case.acknowledged_by = get_commander_info(request)['name']
        case.action_note = data.get('action_note', '')
        case.save()
        AuditLog.objects.create(case=case, action_type='ALERT_ACKNOWLEDGED', action_description=f"Alert acknowledged: {case.action_note[:100]}", performed_by=case.acknowledged_by, performed_by_role="COMMANDER")
        return JsonResponse({'success': True, 'message': 'Alert acknowledged'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def resolve_alert_api(request):
    try:
        data = json.loads(request.body)
        case = Case.objects.get(case_number=data.get('cas_number'))
        case.status = 'CASE_CLOSED'
        case.closed_date = timezone.now()
        case.save()
        AuditLog.objects.create(case=case, action_type='CASE_CLOSED', action_description=f"Case resolved", performed_by=get_commander_info(request)['name'], performed_by_role="COMMANDER")
        return JsonResponse({'success': True, 'message': 'Case resolved'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_complaint_status(request, complaint_id):
    try:
        data = json.loads(request.body)
        complaint = Complaint.objects.get(id=complaint_id)
        complaint.status = data.get('status')
        if data.get('resolution'):
            complaint.resolution_notes = data.get('resolution')
            complaint.resolved_at = timezone.now()
            complaint.resolved_by = get_commander_info(request)['name']
        complaint.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def resolve_complaint(request, complaint_id):
    try:
        data = json.loads(request.body)
        complaint = Complaint.objects.get(id=complaint_id)
        complaint.status = 'RESOLVED'
        complaint.resolved_at = timezone.now()
        complaint.resolved_by = get_commander_info(request)['name']
        complaint.resolution_notes = data.get('resolution_notes', '')
        complaint.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def forward_complaint(request, complaint_id):
    try:
        data = json.loads(request.body)
        complaint = Complaint.objects.get(id=complaint_id)
        return JsonResponse({'success': True, 'message': f'Forwarded to {data.get("to")}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def escalate_case(request, case_number):
    try:
        data = json.loads(request.body)
        case = Case.objects.get(case_number=case_number)
        case.escalated = True
        case.escalation_reason = data.get('reason', '')
        case.escalation_date = timezone.now()
        case.save()
        AuditLog.objects.create(case=case, action_type='ESCALATED', action_description=f"Case escalated to {data.get('level', 'Higher Authority')}. Reason: {data.get('reason', '')}", performed_by=get_commander_info(request)['name'], performed_by_role="COMMANDER")
        return JsonResponse({'success': True, 'message': f'Case {case_number} escalated'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_note(request, case_number):
    try:
        data = json.loads(request.body)
        case = Case.objects.get(case_number=case_number)
        note = data.get('note', '')
        existing_note = case.action_note or ''
        case.action_note = existing_note + f"\n\n[COMMANDER NOTE - {timezone.now().strftime('%Y-%m-%d %H:%M')}]: {note}"
        case.save()
        AuditLog.objects.create(case=case, action_type='NOTE_ADDED', action_description=f"Commander added note: {note[:100]}", performed_by=get_commander_info(request)['name'], performed_by_role="COMMANDER")
        return JsonResponse({'success': True, 'message': 'Note added'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_complaint_note(request, complaint_id):
    try:
        data = json.loads(request.body)
        complaint = Complaint.objects.get(id=complaint_id)
        existing_notes = complaint.resolution_notes or ''
        complaint.resolution_notes = existing_notes + f"\n[COMMANDER NOTE - {timezone.now().strftime('%Y-%m-%d %H:%M')}]: {data.get('note')}"
        complaint.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def send_complaint_response(request, complaint_id):
    try:
        data = json.loads(request.body)
        complaint = Complaint.objects.get(id=complaint_id)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def initiate_transfer(request):
    try:
        data = json.loads(request.body)
        case_number = data.get('case_number')
        from_station = data.get('from_station')
        to_station = data.get('to_station')
        assigned_detective = data.get('assigned_detective')
        reason = data.get('reason')
        case = Case.objects.get(case_number=case_number)
        transfer_count = CaseTransfer.objects.count() + 1
        transfer_number = f"TRF-{timezone.now().year}-{str(transfer_count).zfill(4)}"
        transfer = CaseTransfer.objects.create(
            transfer_number=transfer_number,
            case=case,
            from_detective=case.assigned_detective or 'Unassigned',
            to_detective=assigned_detective,
            from_station=from_station,
            to_station=to_station,
            reason=reason,
            status='PENDING',
            initiated_by=get_commander_info(request)['name']
        )
        AuditLog.objects.create(case=case, action_type='TRANSFER_INITIATED', action_description=f"Transfer initiated: {from_station} → {to_station}", performed_by=get_commander_info(request)['name'], performed_by_role="COMMANDER")
        return JsonResponse({'success': True, 'message': f'Transfer {transfer_number} initiated'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def detective_cases_api(request, detective_name):
    try:
        cases = Case.objects.filter(assigned_detective=detective_name)
        case_list = []
        for case in cases:
            case_list.append({
                'case_number': case.case_number,
                'crime_category': case.crime_category,
                'status': case.status,
                'days_inactive': case.days_inactive,
                'last_updated': case.updated_at.strftime('%d %b %Y, %H:%M') if case.updated_at else None,
            })
        return JsonResponse({'success': True, 'cases': case_list})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def send_update_request(request, case_number):
    """Send an update request to the detective assigned to a case"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        case = Case.objects.get(case_number=case_number)
        
        AuditLog.objects.create(
            case=case,
            action_type='UPDATE_REQUESTED',
            action_description=f"Commander requested case update: {message[:100]}",
            performed_by=get_commander_info(request)['name'],
            performed_by_role="COMMANDER"
        )
        
        return JsonResponse({'success': True, 'message': f'Update request sent for case {case_number}'})
    except Case.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Case not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def bulk_approve_transfers(request):
    """Approve multiple transfers at once"""
    try:
        data = json.loads(request.body)
        transfer_ids = data.get('transfer_ids', [])
        notes = data.get('notes', '')
        approved_count = 0
        for transfer_id in transfer_ids:
            transfer = CaseTransfer.objects.get(id=transfer_id)
            if transfer.status == 'PENDING':
                transfer.status = 'APPROVED'
                transfer.approved_by = get_commander_info(request)['name']
                transfer.approved_at = timezone.now()
                transfer.save()
                case = transfer.case
                case.assigned_detective = transfer.to_detective
                case.save()
                AuditLog.objects.create(
                    case=transfer.case,
                    action_type='TRANSFER_APPROVED',
                    action_description=f"Transfer {transfer.transfer_number} approved in bulk. {notes}",
                    performed_by=get_commander_info(request)['name'],
                    performed_by_role="COMMANDER"
                )
                approved_count += 1
        return JsonResponse({'success': True, 'message': f'{approved_count} transfers approved'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def bulk_reject_transfers(request):
    """Reject multiple transfers at once"""
    try:
        data = json.loads(request.body)
        transfer_ids = data.get('transfer_ids', [])
        reason = data.get('reason', '')
        rejected_count = 0
        for transfer_id in transfer_ids:
            transfer = CaseTransfer.objects.get(id=transfer_id)
            if transfer.status == 'PENDING':
                transfer.status = 'REJECTED'
                transfer.save()
                AuditLog.objects.create(
                    case=transfer.case,
                    action_type='TRANSFER_REJECTED',
                    action_description=f"Transfer {transfer.transfer_number} rejected in bulk. Reason: {reason}",
                    performed_by=get_commander_info(request)['name'],
                    performed_by_role="COMMANDER"
                )
                rejected_count += 1
        return JsonResponse({'success': True, 'message': f'{rejected_count} transfers rejected'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)