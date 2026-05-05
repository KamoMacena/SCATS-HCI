from django.contrib import admin
from .models import Case, Complaint, CaseTransfer, AuditLog

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ['case_number', 'crime_category', 'status', 'assigned_detective', 'days_inactive', 'acknowledged']
    list_filter = ['status', 'crime_category', 'acknowledged']
    search_fields = ['case_number', 'complainant_name', 'assigned_detective']
    readonly_fields = ['created_at', 'updated_at', 'days_inactive']

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['complaint_number', 'case', 'complainant_name', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['complaint_number', 'complainant_name']

@admin.register(CaseTransfer)
class CaseTransferAdmin(admin.ModelAdmin):
    # FIXED: 'request_date' instead of 'transfer_date'
    list_display = ['transfer_number', 'case', 'from_detective', 'to_detective', 'request_date']
    search_fields = ['transfer_number', 'case__case_number']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['case', 'action_type', 'performed_by', 'timestamp']
    list_filter = ['action_type', 'performed_by_role']
    readonly_fields = ['case', 'action_type', 'action_description', 'performed_by', 'performed_by_role', 'timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False