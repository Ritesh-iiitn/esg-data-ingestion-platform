import traceback
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.contrib.auth.models import User
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from ingestion.models import Client, DataUpload, EmissionRecord, Flag, AuditLog
from ingestion.serializers import (
    ClientSerializer, DataUploadSerializer, EmissionRecordSerializer,
    FlagSerializer, AuditLogSerializer
)
from ingestion.parsers.sap_parser import parse_sap_csv
from ingestion.parsers.utility_parser import parse_utility_csv
from ingestion.parsers.travel_parser import parse_travel_csv
from ingestion.flagging import run_flagging_rules

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

class DataUploadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DataUpload.objects.all().order_by('-uploaded_at')
    serializer_class = DataUploadSerializer

class EmissionRecordViewSet(viewsets.ModelViewSet):
    queryset = EmissionRecord.objects.all().order_by('-period_start', '-id')
    serializer_class = EmissionRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        source_param = self.request.query_params.get('source_type')
        scope_param = self.request.query_params.get('scope')
        client_param = self.request.query_params.get('client_id')

        if status_param:
            queryset = queryset.filter(status=status_param.upper())
        if source_param:
            queryset = queryset.filter(source_type=source_param.upper())
        if scope_param:
            queryset = queryset.filter(scope=scope_param)
        if client_param:
            queryset = queryset.filter(client_id=client_param)
            
        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        record = self.get_object()
        if record.status == 'APPROVED':
            return Response({'error': 'Record is already approved.'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Get user
        user = request.user if request.user.is_authenticated else User.objects.filter(is_superuser=True).first()
        
        record.status = 'APPROVED'
        record.approved_by = user
        record.approved_at = timezone.now()
        record.analyst_note = request.data.get('note', record.analyst_note)
        record.save()
        
        return Response(EmissionRecordSerializer(record).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        record = self.get_object()
        if record.status == 'APPROVED':
            return Response({'error': 'Approved records are locked and cannot be rejected.'}, status=status.HTTP_400_BAD_REQUEST)
            
        note = request.data.get('note', '').strip()
        if not note:
            return Response({'error': 'A rejection note is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        record.status = 'REJECTED'
        record.analyst_note = note
        record.save()
        
        return Response(EmissionRecordSerializer(record).data)

    @action(detail=False, methods=['post'], url_path='bulk-approve')
    def bulk_approve(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No record IDs provided.'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = request.user if request.user.is_authenticated else User.objects.filter(is_superuser=True).first()
        records = EmissionRecord.objects.filter(id__in=ids)
        
        approved_count = 0
        errors = []
        
        with transaction.atomic():
            for rec in records:
                if rec.status == 'APPROVED':
                    continue
                try:
                    rec.status = 'APPROVED'
                    rec.approved_by = user
                    rec.approved_at = timezone.now()
                    rec.save()
                    approved_count += 1
                except Exception as e:
                    errors.append(f"Record {rec.id}: {str(e)}")
                    
        return Response({
            'message': f'Successfully approved {approved_count} records.',
            'errors': errors
        })

@api_view(['GET'])
def dashboard_stats(request):
    client_id = request.query_params.get('client_id')
    
    records = EmissionRecord.objects.all()
    if client_id:
        records = records.filter(client_id=client_id)
        
    stats = records.aggregate(
        total_records=Count('id'),
        pending=Count('id', filter=Q(status='PENDING')),
        flagged=Count('id', filter=Q(status='FLAGGED')),
        approved=Count('id', filter=Q(status='APPROVED')),
        rejected=Count('id', filter=Q(status='REJECTED')),
        approved_co2e=Sum('co2e_kg', filter=Q(status='APPROVED'))
    )
    
    # Fill defaults
    stats['approved_co2e'] = stats['approved_co2e'] or 0.0
    
    # Counts by Scope
    scope_counts = records.values('scope').annotate(count=Count('id')).order_by('scope')
    stats['scopes'] = {item['scope']: item['count'] for item in scope_counts}
    
    # Counts by Source Type
    source_counts = records.values('source_type').annotate(count=Count('id')).order_by('source_type')
    stats['sources'] = {item['source_type']: item['count'] for item in source_counts}
    
    return Response(stats)

def handle_upload(request, parser_func, source_type):
    # Retrieve active client
    client_id = request.data.get('client_id')
    if client_id:
        client = Client.objects.get(id=client_id)
    else:
        client = Client.objects.first()
        if not client:
            client = Client.objects.create(name="Acme Corporation", slug="acme")
            
    # Retrieve user
    user = request.user if request.user.is_authenticated else User.objects.filter(is_superuser=True).first()
    
    file_obj = request.FILES.get('file') or request.FILES.get('uploaded_file')
    if not file_obj:
        return Response({'error': 'No file uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        
    # 1. Create DataUpload record
    upload = DataUpload.objects.create(
        client=client,
        source_type=source_type,
        uploaded_file=file_obj,
        uploaded_by=user,
        status='PROCESSING'
    )
    
    try:
        # 2. Parse CSV
        parsed_rows = parser_func(upload.uploaded_file)
        
        # 3. Run flagging rules
        flagged_rows = run_flagging_rules(client, parsed_rows)
        
        # 4. Save rows to DB
        created_records = []
        with transaction.atomic():
            for row in flagged_rows:
                flags_data = row.pop('flags', [])
                
                # Check if there are any flags to determine status
                row_status = 'PENDING'
                if len(flags_data) > 0:
                    row_status = 'FLAGGED'
                    
                # Pop helper fields not on model
                row.pop('doc_num', None)
                row.pop('meter_id', None)
                row.pop('tx_id', None)
                
                rec = EmissionRecord.objects.create(
                    client=client,
                    upload=upload,
                    status=row_status,
                    **row
                )
                
                # Save flags
                for flag_dict in flags_data:
                    Flag.objects.create(
                        record=rec,
                        flag_type=flag_dict['flag_type'],
                        message=flag_dict['message']
                    )
                    
                # If record status was initialized as FLAGGED, we should update the audit log
                # The model save() already handles UPLOADED audit log. Let's make sure it represents flags.
                
                created_records.append(rec)
                
        # 5. Complete upload tracking
        upload.status = 'DONE'
        upload.row_count = len(created_records)
        upload.save()
        
        return Response(DataUploadSerializer(upload).data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        traceback.print_exc()
        upload.status = 'FAILED'
        upload.save()
        return Response({
            'error': f'Parsing/Ingestion failed: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def upload_sap(request):
    return handle_upload(request, parse_sap_csv, 'SAP')

@api_view(['POST'])
def upload_utility(request):
    return handle_upload(request, parse_utility_csv, 'UTILITY')

@api_view(['POST'])
def upload_travel(request):
    return handle_upload(request, parse_travel_csv, 'TRAVEL')
