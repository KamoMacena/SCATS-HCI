from django.contrib import admin
from .models import Case, Detective, InvestigationUpdate, Evidence, Message, CaseLifecycleStage, LIFECYCLE_STAGES


class CaseLifecycleStageInline(admin.TabularInline):
    model = CaseLifecycleStage
    extra = 0
    can_delete = False
    max_num = len(LIFECYCLE_STAGES)
    fields = ("stage_key", "status", "note")
    readonly_fields = ("stage_key",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("cas_number", "crime_category", "victim_name", "assigned_to", "status", "created_at")
    list_filter = ("status", "crime_category")
    search_fields = ("cas_number", "victim_name", "assigned_to__first_name", "assigned_to__last_name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Case Details", {
            "fields": ("cas_number", "crime_category", "victim_name", "status")
        }),
        ("Assignment", {
            "fields": ("assigned_to", "created_by")
        }),
        ("Closure", {
            "fields": ("closure_reason", "closure_summary"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    inlines = [CaseLifecycleStageInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Removed `if not change` — get_or_create is safe on both new and existing cases
        for key, _ in LIFECYCLE_STAGES:
            CaseLifecycleStage.objects.get_or_create(case=obj, stage_key=key)


@admin.register(Detective)
class DetectiveAdmin(admin.ModelAdmin):
    list_display = ("__str__", "rank", "personnel_number")
    search_fields = ("user__first_name", "user__last_name", "personnel_number")


@admin.register(InvestigationUpdate)
class InvestigationUpdateAdmin(admin.ModelAdmin):
    list_display = ("case", "action_type", "created_by", "created_at")
    list_filter = ("action_type",)
    search_fields = ("case__cas_number",)
    readonly_fields = ("created_at",)


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("case", "document_type", "uploaded_at")
    list_filter = ("document_type",)
    search_fields = ("case__cas_number",)
    readonly_fields = ("uploaded_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("case", "sender", "created_at")
    search_fields = ("case__cas_number", "sender__username")
    readonly_fields = ("created_at",)