from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ingestion.views import (
    ClientViewSet, DataUploadViewSet, EmissionRecordViewSet,
    upload_sap, upload_utility, upload_travel, dashboard_stats
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet, basename='client')
router.register(r'uploads', DataUploadViewSet, basename='upload')
router.register(r'records', EmissionRecordViewSet, basename='record')

urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),
    
    # Custom endpoints
    path('upload/sap/', upload_sap, name='upload-sap'),
    path('upload/utility/', upload_utility, name='upload-utility'),
    path('upload/travel/', upload_travel, name='upload-travel'),
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
]
