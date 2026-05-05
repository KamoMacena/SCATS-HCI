from django.urls import path
from . import views

urlpatterns = [
    # Main Commander Pages
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('alerts/', views.alerts_center, name='alerts_center'),
    path('flagged/', views.flagged_cases, name='flagged_cases'),
    path('complaints/', views.complaints_view, name='complaints'),
    path('transfers/', views.transfers_view, name='transfers'),
    path('audit/<str:case_number>/', views.audit_trail, name='audit_trail'),
    
    # Sign Out
    path('signout/', views.sign_out, name='sign_out'),
    
    # Export to Excel
    path('export/cases/', views.export_cases_excel, name='export_cases_excel'),
    path('export/alerts/', views.export_alerts_excel, name='export_alerts_excel'),
    path('export/transfers/', views.export_transfers_excel, name='export_transfers_excel'),
    path('export/complaints/', views.export_complaints_excel, name='export_complaints_excel'),
    
    # Commander Actions - ALL WORKING
    path('api/assign-detective/', views.assign_detective, name='assign_detective'),
    path('api/approve-transfer/<str:transfer_number>/', views.approve_transfer, name='approve_transfer'),
    path('api/approve-backward/<str:case_number>/', views.approve_backward_stage, name='approve_backward_stage'),
    path('api/escalate/<str:case_number>/', views.escalate_case, name='escalate_case'),
    path('api/add-note/<str:case_number>/', views.add_note, name='add_note'),
    path('api/initiate-transfer/', views.initiate_transfer, name='initiate_transfer'),
    path('api/update-request/<str:case_number>/', views.send_update_request, name='send_update_request'),
    
    # Detective Cases API
    path('api/detective-cases/<str:detective_name>/', views.detective_cases_api, name='detective_cases_api'),
    
    # Pending Assignments API (Real-time notifications)
    path('api/pending-assignments/', views.pending_assignments_api, name='pending_assignments_api'),
    
    # Complaint API Endpoints
    path('api/complaint/update-status/<int:complaint_id>/', views.update_complaint_status, name='update_complaint_status'),
    path('api/complaint/add-note/<int:complaint_id>/', views.add_complaint_note, name='add_complaint_note'),
    path('api/complaint/forward/<int:complaint_id>/', views.forward_complaint, name='forward_complaint'),
    path('api/complaint/resolve/<int:complaint_id>/', views.resolve_complaint, name='resolve_complaint'),
    path('api/complaint/send-response/<int:complaint_id>/', views.send_complaint_response, name='send_complaint_response'),
    
    # API Endpoints for Acknowledge & Resolve
    path('api/alerts/acknowledge/', views.acknowledge_alert_api, name='acknowledge_alert_api'),
    path('api/alerts/resolve/', views.resolve_alert_api, name='resolve_alert_api'),
    
    # Bulk Actions
    path('api/bulk-approve-transfers/', views.bulk_approve_transfers, name='bulk_approve_transfers'),
    path('api/bulk-reject-transfers/', views.bulk_reject_transfers, name='bulk_reject_transfers'),
]