from django.contrib import admin
from ingestion.models import Client, DataUpload, EmissionRecord, Flag, AuditLog

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')

@admin.register(DataUpload)
class DataUploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'source_type', 'uploaded_by', 'uploaded_at', 'row_count', 'status')
    list_filter = ('source_type', 'status', 'client')
    search_fields = ('uploaded_file', 'uploaded_by__username')

class FlagInline(admin.TabularInline):
    model = Flag
    extra = 0

class AuditLogInline(admin.TabularInline):
    model = AuditLog
    extra = 0
    readonly_fields = ('action', 'performed_by', 'performed_at', 'previous_value', 'new_value', 'note')

@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'client', 'source_type', 'scope', 'activity_type', 
        'normalized_value', 'normalized_unit', 'co2e_kg', 
        'period_start', 'period_end', 'status'
    )
    list_filter = ('source_type', 'scope', 'status', 'client', 'activity_type')
    search_fields = ('activity_type', 'raw_unit', 'analyst_note')
    inlines = [FlagInline, AuditLogInline]

@admin.register(Flag)
class FlagAdmin(admin.ModelAdmin):
    list_display = ('id', 'record', 'flag_type', 'message', 'created_at')
    list_filter = ('flag_type', 'created_at')
    search_fields = ('message', 'record__id')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'record', 'action', 'performed_by', 'performed_at')
    list_filter = ('action', 'performed_at')
    search_fields = ('note', 'record__id', 'performed_by__username')
