from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class Client(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class DataUpload(models.Model):
    STATUS_CHOICES = (
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    )
    SOURCE_CHOICES = (
        ('SAP', 'SAP Fuel & Procurement'),
        ('UTILITY', 'Utility Electricity'),
        ('TRAVEL', 'Corporate Travel'),
    )
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='uploads')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    uploaded_file = models.FileField(upload_to='uploads/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PROCESSING')

    def __str__(self):
        return f"{self.source_type} upload for {self.client.name} at {self.uploaded_at}"

class EmissionRecord(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Review'),
        ('FLAGGED', 'Flagged'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    SOURCE_CHOICES = (
        ('SAP', 'SAP'),
        ('UTILITY', 'Utility'),
        ('TRAVEL', 'Travel'),
    )
    ACTIVITY_CHOICES = (
        ('diesel', 'Diesel'),
        ('petrol', 'Petrol'),
        ('natural_gas', 'Natural Gas'),
        ('electricity', 'Electricity'),
        ('flight', 'Flight'),
        ('hotel', 'Hotel'),
        ('ground_transport', 'Ground Transport'),
    )
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='records')
    upload = models.ForeignKey(DataUpload, on_delete=models.CASCADE, related_name='records')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    scope = models.IntegerField(choices=((1, 'Scope 1'), (2, 'Scope 2'), (3, 'Scope 3')))
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    
    raw_value = models.FloatField()
    raw_unit = models.CharField(max_length=20)
    raw_data = models.JSONField(help_text="Entire original row raw fields")
    
    normalized_value = models.FloatField()
    normalized_unit = models.CharField(max_length=20)
    
    emission_factor = models.FloatField()
    emission_factor_source = models.CharField(max_length=150)
    co2e_kg = models.FloatField()
    
    period_start = models.DateField()
    period_end = models.DateField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_records')
    approved_at = models.DateTimeField(null=True, blank=True)
    analyst_note = models.TextField(blank=True, default='')

    def clean(self):
        # Enforce lock on APPROVED records
        if self.pk:
            original = EmissionRecord.objects.get(pk=self.pk)
            if original.status == 'APPROVED':
                # Block updates to approved records
                raise ValidationError("Approved records are locked and cannot be modified.")

    def save(self, *args, **kwargs):
        self.full_clean()
        
        # Capture status change before saving to create audit logs
        is_new = self.pk is None
        old_status = None
        old_note = ""
        old_data_json = {}
        
        if not is_new:
            original = EmissionRecord.objects.get(pk=self.pk)
            old_status = original.status
            old_note = original.analyst_note
            old_data_json = {
                "status": original.status,
                "analyst_note": original.analyst_note,
                "normalized_value": original.normalized_value,
                "co2e_kg": original.co2e_kg
            }
            
        super().save(*args, **kwargs)
        
        # Audit logging on transitions or updates
        new_data_json = {
            "status": self.status,
            "analyst_note": self.analyst_note,
            "normalized_value": self.normalized_value,
            "co2e_kg": self.co2e_kg
        }
        
        if is_new:
            AuditLog.objects.create(
                record=self,
                action='UPLOADED',
                performed_by=self.upload.uploaded_by,
                new_value=new_data_json,
                note="Record ingested from file upload."
            )
        elif old_status != self.status or old_note != self.analyst_note:
            action = 'EDITED'
            if self.status == 'APPROVED':
                action = 'APPROVED'
            elif self.status == 'REJECTED':
                action = 'REJECTED'
                
            AuditLog.objects.create(
                record=self,
                action=action,
                performed_by=self.approved_by if action == 'APPROVED' else (self.upload.uploaded_by if self.upload else None),
                previous_value=old_data_json,
                new_value=new_data_json,
                note=self.analyst_note or f"Status changed from {old_status} to {self.status}."
            )

    def delete(self, *args, **kwargs):
        if self.status == 'APPROVED':
            raise ValidationError("Approved records are locked and cannot be deleted.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.activity_type} ({self.co2e_kg:.2f} kg CO2e) - {self.status}"

class Flag(models.Model):
    FLAG_CHOICES = (
        ('UNIT_MISMATCH', 'Unit Mismatch'),
        ('OUTLIER', 'Outlier'),
        ('MISSING_FACTOR', 'Missing Factor'),
        ('DATE_GAP', 'Date Gap'),
        ('DUPLICATE', 'Duplicate'),
        ('ZERO_VALUE', 'Zero or Negative Value'),
    )
    record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='flags')
    flag_type = models.CharField(max_length=30, choices=FLAG_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.flag_type} flag on Record {self.record.id}"

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EDITED', 'Edited'),
        ('UPLOADED', 'Uploaded'),
    )
    record = models.ForeignKey(EmissionRecord, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    previous_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    note = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.action} on Record {self.record.id} by {self.performed_by} at {self.performed_at}"
