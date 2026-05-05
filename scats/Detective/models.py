from django.db import models
from django.contrib.auth.models import User


class Detective(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    personnel_number = models.CharField(max_length=50, unique=True)
    rank = models.CharField(max_length=50, default="Detective")

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.personnel_number})"


class Case(models.Model):
    cas_number = models.CharField(max_length=50)
    crime_category = models.CharField(max_length=100)
    status = models.CharField(max_length=50)

    victim_name = models.CharField(max_length=255, null=True, blank=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_cases",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_cases",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closure_reason = models.CharField(max_length=255, null=True, blank=True)
    closure_summary = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.cas_number


# ── LIFECYCLE ────────────────────────────────────────────────────────────────

LIFECYCLE_STAGES = [
    ("reported",          "Reported"),
    ("awaiting_assigned", "Awaiting to be Assigned a Detective"),
    ("assigned",          "Assigned"),
    ("under_investigation","Under Investigation"),
    ("evidence_collected","Evidence Collected"),
    ("npa_referred",      "Referred to NPA"),
    ("court_processing",  "Case is in Court Processing"),
    ("closed",            "Case Closed"),
]

STAGE_STATUS = [
    ("done",    "Done"),
    ("current", "Current"),
    ("pending", "Pending"),
]


class CaseLifecycleStage(models.Model):
    """
    One row per lifecycle stage per case.
    Populate via the management command or admin after running migrations.
    """
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="lifecycle_stages")
    stage_key = models.CharField(max_length=50, choices=LIFECYCLE_STAGES)
    status = models.CharField(max_length=10, choices=STAGE_STATUS, default="pending")
    note = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("case", "stage_key")
        ordering = ["id"]

    def __str__(self):
        return f"{self.case.cas_number} — {self.get_stage_key_display()} [{self.status}]"


class InvestigationUpdate(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="updates")
    action_type = models.CharField(max_length=100)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Evidence(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="evidence")
    file = models.FileField(upload_to="evidence/")
    document_type = models.CharField(max_length=100)
    description = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} - {self.case.cas_number}"