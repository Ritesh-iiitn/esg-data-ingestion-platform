import os
from datetime import date
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from ingestion.models import Client, DataUpload, EmissionRecord, Flag, AuditLog
from ingestion.parsers.sap_parser import parse_sap_csv
from ingestion.parsers.utility_parser import parse_utility_csv
from ingestion.parsers.travel_parser import parse_travel_csv
from ingestion.flagging import run_flagging_rules

class IngestionTestCase(TestCase):
    def setUp(self):
        # Create standard seed data
        self.user = User.objects.create_superuser(username='testadmin', email='t@t.com', password='p')
        self.client_obj = Client.objects.create(name="Acme Solutions", slug="acme")
        
    def test_sap_parser_conversions(self):
        # Create a mock CSV wrapper matching SAP specification
        from django.core.files.base import ContentFile
        csv_content = (
            "Werk,Buchungsdatum,Menge,Mengeneinheit,Materialgruppe,Kostenstelle,Belegnum\n"
            "PL-0042,20240115,100.0,GAL,DIESEL,CC-CORP-01,SAP-10001\n"
            "PL-0107,20240120,500.0,L,PETROL,CC-OPS-02,SAP-10002\n"
            "PL-0107,20240125,50.0,M3,NATGAS,CC-PLANT-07,SAP-10003\n"
        )
        file_obj = ContentFile(csv_content, name="sap_test.csv")
        
        parsed = parse_sap_csv(file_obj)
        self.assertEqual(len(parsed), 3)
        
        # Test GAL to L conversion
        # 100 GAL * 3.78541 = 378.541 L
        self.assertAlmostEqual(parsed[0]['normalized_value'], 378.541)
        self.assertEqual(parsed[0]['normalized_unit'], 'L')
        self.assertEqual(parsed[0]['activity_type'], 'diesel')
        self.assertEqual(parsed[0]['scope'], 1)
        self.assertEqual(parsed[0]['co2e_kg'], 378.541 * 2.68)
        
        # Test standard L petrol
        self.assertEqual(parsed[1]['normalized_value'], 500.0)
        self.assertEqual(parsed[1]['normalized_unit'], 'L')
        self.assertEqual(parsed[1]['activity_type'], 'petrol')
        self.assertEqual(parsed[1]['co2e_kg'], 500.0 * 2.31)
        
    def test_utility_parser_zero_consumption_flag(self):
        from django.core.files.base import ContentFile
        csv_content = (
            "meter_id,site_name,billing_period_start,billing_period_end,consumption_kwh,consumption_unit,tariff_code,supplier_name\n"
            "MTR-88001,HQ Site,01/01/2024,31/01/2024,0.0,kWh,COMM-T1,Apex\n"
        )
        file_obj = ContentFile(csv_content, name="util_test.csv")
        parsed = parse_utility_csv(file_obj)
        
        # Should flag zero consumption
        self.assertEqual(len(parsed), 1)
        flags = parsed[0]['flags']
        self.assertTrue(any(f['flag_type'] == 'ZERO_VALUE' for f in flags))

    def test_travel_parser_missing_distance_lookup(self):
        from django.core.files.base import ContentFile
        # DEL to LHR empty distance_km
        csv_content = (
            "transaction_id,employee_id,travel_date,category,origin,destination,distance_km,nights,amount_usd,vendor_name\n"
            "TX-90001,EMP-100,01/12/2024,Air,DEL,LHR,,0,1200.0,BA\n"
            "TX-90002,EMP-100,01/12/2024,Hotel,London,London,0,4,800.0,Hilton\n"
        )
        file_obj = ContentFile(csv_content, name="travel_test.csv")
        parsed = parse_travel_csv(file_obj)
        self.assertEqual(len(parsed), 2)
        
        # Flight lookup verification (DEL-LHR = 6710 km)
        self.assertEqual(parsed[0]['normalized_value'], 6710.0)
        self.assertEqual(parsed[0]['activity_type'], 'flight')
        self.assertEqual(parsed[0]['co2e_kg'], 6710.0 * 0.195) # long haul factor since >3700km
        
        # Hotel stay nights check (4 nights * 31.2 kg CO2e)
        self.assertEqual(parsed[1]['normalized_value'], 4.0)
        self.assertEqual(parsed[1]['activity_type'], 'hotel')
        self.assertEqual(parsed[1]['co2e_kg'], 4 * 31.2)
        
    def test_record_locked_when_approved(self):
        # Create DataUpload
        from django.core.files.base import ContentFile
        upload = DataUpload.objects.create(
            client=self.client_obj,
            source_type='SAP',
            uploaded_file=ContentFile(" Werk,Menge\nPL-0042,100", name="test.csv"),
            uploaded_by=self.user,
            status='DONE'
        )
        # Create record
        rec = EmissionRecord.objects.create(
            client=self.client_obj,
            upload=upload,
            source_type='SAP',
            scope=1,
            activity_type='diesel',
            raw_value=100.0,
            raw_unit='L',
            raw_data={'Menge': '100', 'Mengeneinheit': 'L', 'Belegnum': 'SAP-10001'},
            normalized_value=100.0,
            normalized_unit='L',
            emission_factor=2.68,
            emission_factor_source='DEFRA 2023',
            co2e_kg=268.0,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 1),
            status='PENDING'
        )
        
        # Approve it
        rec.status = 'APPROVED'
        rec.approved_by = self.user
        rec.approved_at = timezone.now()
        rec.save()
        
        # Attempt to edit approved record should throw ValidationError
        rec.normalized_value = 200.0
        with self.assertRaises(ValidationError):
            rec.save()
            
        # Attempt to delete approved record should throw ValidationError
        with self.assertRaises(ValidationError):
            rec.delete()

    def test_nan_sanitization(self):
        from django.core.files.base import ContentFile
        # We simulate a Travel CSV where some fields are empty (which parses to NaN)
        # and test that the raw_data stored does not trigger SQLite error and converts successfully.
        csv_content = (
            "transaction_id,employee_id,travel_date,category,origin,destination,distance_km,nights,amount_usd,vendor_name\n"
            "TX-90001,EMP-100,01/12/2024,Air,DEL,LHR,,0,1200.0,BA\n"
            "TX-90002,EMP-100,01/12/2024,Air,DEL,DEL,,0,200.0,SpiceJet\n"
            "TX-90003,EMP-100,01/12/2024,UnknownCategory,DEL,LHR,100,0,100.0,Other\n"
        )
        file_obj = ContentFile(csv_content, name="travel_nan_test.csv")
        parsed = parse_travel_csv(file_obj)
        self.assertEqual(len(parsed), 3)
        
        # Verify raw_data field contains None instead of NaN
        self.assertIsNone(parsed[0]['raw_data']['distance_km'])
        self.assertIsNone(parsed[1]['raw_data']['distance_km'])
        
        # Test saving to DB works without SQLite JSON_VALID CHECK constraint failure or blankChar fields
        upload = DataUpload.objects.create(
            client=self.client_obj,
            source_type='TRAVEL',
            uploaded_file=file_obj,
            uploaded_by=self.user,
            status='DONE'
        )
        
        # Create records
        created_records = []
        for p in parsed:
            rec = EmissionRecord.objects.create(
                client=self.client_obj,
                upload=upload,
                source_type=p['source_type'],
                scope=p['scope'],
                activity_type=p['activity_type'],
                raw_value=p['raw_value'],
                raw_unit=p['raw_unit'],
                raw_data=p['raw_data'],
                normalized_value=p['normalized_value'],
                normalized_unit=p['normalized_unit'],
                emission_factor=p['emission_factor'],
                emission_factor_source=p['emission_factor_source'],
                co2e_kg=p['co2e_kg'],
                period_start=p['period_start'],
                period_end=p['period_end'],
                status='PENDING'
            )
            created_records.append(rec)
        
        # Check it successfully persisted to the DB and distance_km is None
        db_rec = EmissionRecord.objects.get(id=created_records[0].id)
        self.assertIsNone(db_rec.raw_data['distance_km'])
        self.assertEqual(EmissionRecord.objects.filter(upload=upload).count(), 3)

    def test_reject_api(self):
        from rest_framework.test import APIClient
        from django.core.files.base import ContentFile
        
        upload = DataUpload.objects.create(
            client=self.client_obj,
            source_type='SAP',
            uploaded_file=ContentFile(" Werk,Menge\nPL-0042,100", name="test.csv"),
            uploaded_by=self.user,
            status='DONE'
        )
        rec = EmissionRecord.objects.create(
            client=self.client_obj,
            upload=upload,
            source_type='SAP',
            scope=1,
            activity_type='diesel',
            raw_value=100.0,
            raw_unit='L',
            raw_data={'Menge': '100', 'Mengeneinheit': 'L', 'Belegnum': 'SAP-10001'},
            normalized_value=100.0,
            normalized_unit='L',
            emission_factor=2.68,
            emission_factor_source='DEFRA 2023',
            co2e_kg=268.0,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 1),
            status='PENDING'
        )
        
        api_client = APIClient()
        response = api_client.post(f'/api/records/{rec.id}/reject/', {'note': 'Unusual high value'})
        self.assertEqual(response.status_code, 200)
        
        rec.refresh_from_db()
        self.assertEqual(rec.status, 'REJECTED')
        self.assertEqual(rec.analyst_note, 'Unusual high value')
        
        logs = AuditLog.objects.filter(record=rec, action='REJECTED')
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().note, 'Unusual high value')
