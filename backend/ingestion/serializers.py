from rest_framework import serializers
from django.contrib.auth.models import User
from ingestion.models import Client, DataUpload, EmissionRecord, Flag, AuditLog

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('id', 'name', 'slug', 'created_at')

class DataUploadSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    uploaded_by_username = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = DataUpload
        fields = (
            'id', 'client', 'client_name', 'source_type', 'uploaded_file', 
            'uploaded_by', 'uploaded_by_username', 'uploaded_at', 
            'row_count', 'status'
        )

class FlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flag
        fields = ('id', 'record', 'flag_type', 'message', 'created_at')

class AuditLogSerializer(serializers.ModelSerializer):
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = (
            'id', 'record', 'action', 'performed_by', 'performed_by_username', 
            'performed_at', 'previous_value', 'new_value', 'note'
        )

class EmissionRecordSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.name', read_only=True)
    flags = FlagSerializer(many=True, read_only=True)
    audit_logs = AuditLogSerializer(many=True, read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = EmissionRecord
        fields = (
            'id', 'client', 'client_name', 'upload', 'source_type', 'scope', 
            'activity_type', 'raw_value', 'raw_unit', 'raw_data', 
            'normalized_value', 'normalized_unit', 'emission_factor', 
            'emission_factor_source', 'co2e_kg', 'period_start', 'period_end', 
            'status', 'approved_by', 'approved_by_username', 'approved_at', 
            'analyst_note', 'flags', 'audit_logs'
        )
