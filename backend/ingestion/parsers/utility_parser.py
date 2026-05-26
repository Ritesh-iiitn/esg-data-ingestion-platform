import pandas as pd
from datetime import datetime
from django.core.exceptions import ValidationError
from ingestion.emission_factors import EMISSION_FACTORS
from ingestion.parsers.utils import sanitize_json_dict

def parse_utility_csv(file_wrapper):
    """
    Parses a Utility Electricity CSV file from a file object.
    Returns a list of dicts suitable for creating EmissionRecords and Flag data.
    """
    try:
        try:
            df = pd.read_csv(file_wrapper, sep=',')
            if len(df.columns) <= 1:
                file_wrapper.seek(0)
                df = pd.read_csv(file_wrapper, sep=';')
        except Exception:
            file_wrapper.seek(0)
            df = pd.read_csv(file_wrapper)
            
        # Strip whitespaces from column names
        df.columns = [c.strip() for c in df.columns]
        
        # Check required columns
        required_cols = [
            'meter_id', 'site_name', 'billing_period_start', 
            'billing_period_end', 'consumption_kwh', 'consumption_unit', 
            'tariff_code', 'supplier_name'
        ]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValidationError(f"Missing required Utility columns: {', '.join(missing_cols)}")
            
        records = []
        for index, row in df.iterrows():
            raw_row = row.to_dict()
            
            raw_val = float(raw_row.get('consumption_kwh', 0))
            raw_unit = str(raw_row.get('consumption_unit', '')).strip()
            meter_id = str(raw_row.get('meter_id', '')).strip()
            
            # Parse dates (format: DD/MM/YYYY)
            date_start_str = str(raw_row.get('billing_period_start', '')).strip()
            date_end_str = str(raw_row.get('billing_period_end', '')).strip()
            
            try:
                period_start = datetime.strptime(date_start_str, '%d/%m/%i' if '%i' in date_start_str else '%d/%m/%Y').date()
            except ValueError:
                try:
                    period_start = pd.to_datetime(date_start_str, dayfirst=True).date()
                except Exception:
                    raise ValidationError(f"Invalid billing_period_start at row {index+1}: {date_start_str}")
                    
            try:
                period_end = datetime.strptime(date_end_str, '%d/%m/%i' if '%i' in date_end_str else '%d/%m/%Y').date()
            except ValueError:
                try:
                    period_end = pd.to_datetime(date_end_str, dayfirst=True).date()
                except Exception:
                    raise ValidationError(f"Invalid billing_period_end at row {index+1}: {date_end_str}")
                    
            activity_type = 'electricity'
            normalized_value = raw_val
            normalized_unit = 'kWh'
            flags_to_create = []
            
            # Check unrecognized unit
            if raw_unit not in ['kWh', 'MWh']:
                flags_to_create.append({
                    'flag_type': 'UNIT_MISMATCH',
                    'message': f"Unit '{raw_unit}' is unrecognized for Utility. Expected kWh or MWh."
                })
                normalized_unit = raw_unit
            elif raw_unit == 'MWh':
                normalized_value = raw_val * 1000.0
                normalized_unit = 'kWh'
            else:
                normalized_value = raw_val
                normalized_unit = 'kWh'
                
            # Check zero or negative value
            if normalized_value <= 0:
                flags_to_create.append({
                    'flag_type': 'ZERO_VALUE',
                    'message': f"Utility consumption is zero or negative: {raw_val} {raw_unit}."
                })
                
            # Retrieve factor
            factor_info = EMISSION_FACTORS.get('electricity')
            factor = factor_info['factor']
            factor_src = factor_info['source']
            co2e_kg = normalized_value * factor
            
            records.append({
                'source_type': 'UTILITY',
                'scope': 2,
                'activity_type': activity_type,
                'raw_value': raw_val,
                'raw_unit': raw_unit,
                'raw_data': sanitize_json_dict(raw_row),
                'normalized_value': normalized_value,
                'normalized_unit': normalized_unit,
                'emission_factor': factor,
                'emission_factor_source': factor_src,
                'co2e_kg': co2e_kg,
                'period_start': period_start,
                'period_end': period_end,
                'meter_id': meter_id,  # for overlap and gap checks
                'flags': flags_to_create
            })
            
        return records
    except Exception as e:
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"Error parsing Utility CSV: {str(e)}")
