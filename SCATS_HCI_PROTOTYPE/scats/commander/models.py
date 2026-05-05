from django.db import models
from django.utils import timezone

class Case(models.Model):
    """
    Case Model - Stores all criminal cases in the system.
    This is the PRIMARY data source for everything the Commander sees.
    """
    
    # ========== STATUS CHOICES (What stage the case is in) ==========
    STATUS_CHOICES = [
        ('REPORTED', 'Reported'),
        ('AWAITING_ASSIGNMENT', 'Awaiting Assignment'),
        ('ASSIGNED', 'Assigned'),
        ('UNDER_INVESTIGATION', 'Under Investigation'),
        ('EVIDENCE_COLLECTED', 'Evidence Collected'),
        ('REFERRED_TO_NPA', 'Referred to NPA'),
        ('COURT_PROCESSING', 'Court Processing'),
        ('CASE_CLOSED', 'Case Closed'),
    ]
    
    # ========== PRIORITY CRIME CHOICES (For faster stall detection) ==========
    PRIORITY_CHOICES = [
        ('STANDARD', 'Standard'),
        ('PRIORITY', 'Priority Crime'),
    ]
    
    # ========== CRIME CATEGORY CHOICES ==========
    CRIME_CHOICES = [
        ('Murder', 'Murder'),
        ('Rape', 'Rape'),
        ('Aggravated Robbery', 'Aggravated Robbery'),
        ('Assault GBH', 'Assault GBH'),
        ('Business Robbery', 'Business Robbery'),
        ('Theft of Motor Vehicle', 'Theft of Motor Vehicle'),
        ('Other', 'Other'),
    ]
    
    # ========== BASIC CASE INFORMATION ==========
    case_number = models.CharField(
        max_length=50, 
        unique=True,
        help_text="SAPS CAS number - unique identifier for this case"
    )
    crime_category = models.CharField(
        max_length=50, 
        choices=CRIME_CHOICES,
        help_text="Type of crime committed"
    )
    priority_type = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='STANDARD',
        help_text="Priority crimes (Murder, Rape, Aggravated Robbery) have shorter stall thresholds"
    )
    
    # ========== COMPLAINANT INFORMATION ==========
    complainant_name = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        help_text="Name of person who reported the crime"
    )
    complainant_id = models.CharField(
        max_length=13, 
        blank=True, 
        null=True,
        help_text="South African ID number"
    )
    complainant_contact = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Phone number or email for notifications"
    )
    
    # ========== DETECTIVE ASSIGNMENT ==========
    assigned_detective = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Name of detective assigned to this case"
    )
    detective_badge = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Detective's SAPS badge number"
    )
    detective_rank = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Detective's rank (e.g., Warrant Officer, Captain)"
    )
    
    # ========== CASE STATUS TRACKING ==========
    status = models.CharField(
        max_length=30, 
        choices=STATUS_CHOICES, 
        default='REPORTED',
        help_text="Current stage in the case lifecycle"
    )
    
    # ========== DATE TRACKING (For stall detection) ==========
    reported_date = models.DateTimeField(
        default=timezone.now,
        help_text="When the case was first reported"
    )
    last_activity_date = models.DateTimeField(
        default=timezone.now,
        help_text="Last time any investigative action was taken - used for stall detection"
    )
    closed_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the case was closed (if applicable)"
    )
    
    # ========== CLOSURE INFORMATION ==========
    closure_reason = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Reason for case closure (e.g., Solved, Unsolved, Withdrawn)"
    )
    closure_summary = models.TextField(
        blank=True,
        null=True,
        help_text="Written summary of all investigative actions taken"
    )
    
    # ========== ALERT TRACKING (For Commander actions) ==========
    acknowledged = models.BooleanField(
        default=False,
        help_text="Has the Commander acknowledged this alert?"
    )
    acknowledged_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the Commander acknowledged the alert"
    )
    acknowledged_by = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Which Commander acknowledged this"
    )
    action_note = models.TextField(
        blank=True, 
        null=True,
        help_text="Commander's action plan for this case"
    )
    
    # ========== ESCALATION TRACKING ==========
    escalated = models.BooleanField(
        default=False,
        help_text="Has this case been escalated to Commander?"
    )
    escalated_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When escalation happened"
    )
    escalation_reason = models.TextField(
        blank=True, 
        null=True,
        help_text="Why this case was escalated"
    )
    
    # ========== TRANSFER TRACKING ==========
    transfer_requested = models.BooleanField(
        default=False,
        help_text="Is this case pending transfer to another station?"
    )
    transfer_to_station = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Destination station for transfer"
    )
    transfer_approved = models.BooleanField(
        default=False,
        help_text="Has the transfer been approved?"
    )
    transfer_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When transfer was approved"
    )
    transfer_confirmed = models.BooleanField(
        default=False,
        help_text="Has receiving station confirmed receipt?"
    )
    
    # ========== AUTO-UPDATE TIMESTAMPS ==========
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.case_number} - {self.get_status_display()}"
    
    @property
    def days_inactive(self):
        """Calculate days since last activity - used for stall detection"""
        if self.last_activity_date:
            delta = timezone.now() - self.last_activity_date
            return delta.days
        return 0
    
    @property
    def stall_status(self):
        """
        Determine stall status based on days inactive and priority type.
        Priority crimes: Stalled after 14 days
        Standard crimes: Stalled after 30 days
        """
        days = self.days_inactive
        
        if self.priority_type == 'PRIORITY':
            # Priority crimes (Murder, Rape, Aggravated Robbery)
            if days >= 14:
                return 'STALLED'
            elif days >= 7:
                return 'AT_RISK'
            else:
                return 'ACTIVE'
        else:
            # Standard crimes
            if days >= 30:
                return 'STALLED'
            elif days >= 14:
                return 'AT_RISK'
            else:
                return 'ACTIVE'
    
    class Meta:
        ordering = ['-last_activity_date']
        verbose_name = 'Case'
        verbose_name_plural = 'Cases'


class Complaint(models.Model):
    """
    Complaint Model - Stores formal complaints submitted by citizens.
    These are automatically forwarded to the Commander.
    """
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('INVESTIGATING', 'Under Investigation'),
        ('RESOLVED', 'Resolved'),
        ('DISMISSED', 'Dismissed'),
    ]
    
    complaint_number = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Unique identifier for this complaint"
    )
    case = models.ForeignKey(
        Case, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='complaints',
        help_text="Which case this complaint is about"
    )
    complainant_name = models.CharField(
        max_length=200,
        help_text="Name of person submitting complaint"
    )
    complaint_text = models.TextField(
        help_text="Full complaint description"
    )
    supporting_evidence = models.TextField(
        blank=True,
        null=True,
        help_text="Links to screenshots, call logs, or other evidence"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=100, blank=True, null=True)
    resolution_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.complaint_number} - {self.complainant_name}"
    
    class Meta:
        ordering = ['-created_at']


class CaseTransfer(models.Model):
    """
    Case Transfer Model - Tracks when cases move between detectives or stations.
    Commander must approve these transfers.
    """
    
    TRANSFER_STATUS = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    ]
    
    transfer_number = models.CharField(max_length=50, unique=True)
    case = models.ForeignKey(
        Case, 
        on_delete=models.CASCADE, 
        related_name='transfers'
    )
    from_detective = models.CharField(max_length=100)
    from_station = models.CharField(max_length=100)
    to_detective = models.CharField(max_length=100)
    to_station = models.CharField(max_length=100)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=TRANSFER_STATUS, default='PENDING')
    request_date = models.DateTimeField(default=timezone.now)
    approved_by = models.CharField(max_length=100, blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # ========== NEW FIELDS FOR INITIATOR TRACKING ==========
    initiated_by = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Who initiated this transfer (Commander or Detective)"
    )
    initiated_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the transfer was initiated"
    )
    
    def __str__(self):
        return f"{self.case.case_number} - {self.from_detective} to {self.to_detective}"
    
    class Meta:
        ordering = ['-request_date']


class AuditLog(models.Model):
    """
    Audit Log Model - Immutable record of all case events.
    Required for transparency and accountability.
    """
    
    ACTION_TYPES = [
        ('CASE_CREATED', 'Case Created'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('MESSAGE_SENT', 'Message Sent'),
        ('EVIDENCE_UPLOADED', 'Evidence Uploaded'),
        ('COMPLAINT_SUBMITTED', 'Complaint Submitted'),
        ('ALERT_ESCALATED', 'Alert Escalated'),
        ('ALERT_ACKNOWLEDGED', 'Alert Acknowledged'),
        ('ALERT_RESOLVED', 'Alert Resolved'),
        ('TRANSFER_REQUESTED', 'Transfer Requested'),
        ('TRANSFER_APPROVED', 'Transfer Approved'),
        ('CASE_CLOSED', 'Case Closed'),
    ]
    
    case = models.ForeignKey(
        Case, 
        on_delete=models.CASCADE, 
        related_name='audit_logs'
    )
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    action_description = models.TextField()
    performed_by = models.CharField(max_length=100)
    performed_by_role = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.case.case_number} - {self.action_type} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']
        # No user can modify audit log entries
        permissions = [
            ('can_view_audit_log', 'Can view audit log'),
        ]