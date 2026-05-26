import pandas as pd
from datetime import datetime
from django.core.exceptions import ValidationError
from ingestion.emission_factors import EMISSION_FACTORS
from ingestion.parsers.utils import sanitize_json_dict

GERMAN_TO_ENGLISH = {
    'Werk': 'plant_code',
    'Buchungsdatum': 'booking_date',
    'Menge': 'quantity',
    'Mengeneinheit': 'unit',
    'Materialgruppe': 'material_group',
    'Kostenstelle': 'cost_center',
    'Belegnum': 'document_number'
}

def parse_sap_csv(file_wrapper):
    """
    Parses a SAP CSV file from a file object.
    Returns a list of dicts suitable for creating EmissionRecords and Flag data.
    """
    try:
        # Read CSV with pandas. Handling potential semicolon separator common in SAP exports.
        try:
            df = pd.read_csv(file_wrapper, sep=',')
            # If pandas read a single column, try semicolon
            if len(df.columns) <= 1:
                file_wrapper.seek(0)
                df = pd.read_csv(file_wrapper, sep=';')
        except Exception:
            file_wrapper.seek(0)
            df = pd.read_csv(file_wrapper)
            
        # Strip whitespaces from column names
        df.columns = [c.strip() for c in df.columns]
        
        # Check required columns
        missing_cols = [c for c in GERMAN_TO_ENGLISH.keys() if c not in df.columns]
        if missing_cols:
            raise ValidationError(f"Missing required SAP columns: {', '.join(missing_cols)}")
            
        # Rename columns to English
        df = df.rename(columns=GERMAN_TO_ENGLISH)
        
        records = []
        for index, row in df.iterrows():
            raw_row = row.to_dict()
            
            # Map raw fields safely
            raw_val = float(raw_row.get('quantity', 0))
            raw_unit = str(raw_row.get('unit', '')).strip().upper()
            material = str(raw_row.get('material_group', '')).strip().upper()
            doc_num = str(raw_row.get('document_number', '')).strip()
            
            # Parse Date
            raw_date_str = str(raw_row.get('booking_date', '')).strip()
            try:
                # Format: YYYYMMDD e.g. 20240131
                parsed_date = datetime.strptime(raw_date_str, '%Y%m%d').date()
            except ValueError:
                # Fallback if already formatted
                try:
                    parsed_date = pd.to_datetime(raw_date_str).date()
                except Exception:
                    raise ValidationError(f"Invalid date format for Buchungsdatum at row {index+1}: {raw_date_str}")
            
            # Map material group to activity type & factors
            # DIESEL, PETROL, NATGAS
            activity_type = 'diesel'
            if 'PETROL' in material or 'GASOLINE' in material:
                activity_type = 'petrol'
            elif 'NATGAS' in material or 'NATURAL' in material or 'GAS' in material:
                activity_type = 'natural_gas'
            elif 'DIESEL' in material:
                activity_type = 'diesel'
            else:
                # Default fallback
                activity_type = material.lower().replace(' ', '_')
                
            # Normalize units
            # L, GAL, KG, M3
            normalized_value = raw_val
            normalized_unit = raw_unit
            flags_to_create = []
            
            recognized_units = ['L', 'GAL', 'KG', 'M3']
            if raw_unit not in recognized_units:
                flags_to_create.append({
                    'flag_type': 'UNIT_MISMATCH',
                    'message': f"Unit '{raw_unit}' is unrecognized for SAP. Expected L, GAL, KG, M3."
                })
                
            if raw_unit == 'GAL':
                # 1 US Gallon = 3.78541 Liters
                normalized_value = raw_val * 3.78541
                normalized_unit = 'L'
            elif raw_unit == 'L':
                normalized_value = raw_val
                normalized_unit = 'L'
            elif raw_unit == 'KG':
                normalized_value = raw_val
                normalized_unit = 'KG'
            elif raw_unit == 'M3':
                normalized_value = raw_val
                normalized_unit = 'M3'
                
            # Retrieve factor
            factor_info = EMISSION_FACTORS.get(activity_type)
            if factor_info:
                factor = factor_info['factor']
                factor_src = factor_info['source']
                # co2e_kg calculation
                co2e_kg = normalized_value * factor
            else:
                factor = 0.0
                factor_src = "No factor found"
                co2e_kg = 0.0
                flags_to_create.append({
                    'flag_type': 'MISSING_FACTOR',
                    'message': f"No emission factor found for activity type '{activity_type}'."
                })
                
            records.append({
                'source_type': 'SAP',
                'scope': 1,
                'activity_type': activity_type,
                'raw_value': raw_val,
                'raw_unit': raw_unit,
                'raw_data': sanitize_json_dict(raw_row),
                'normalized_value': normalized_value,
                'normalized_unit': normalized_unit,
                'emission_factor': factor,
                'emission_factor_source': factor_src,
                'co2e_kg': co2e_kg,
                'period_start': parsed_date,
                'period_end': parsed_date,
                'doc_num': doc_num,  # for duplicate check in flagging
                'flags': flags_to_create
            })
            
        return records
    except Exception as e:
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"Error parsing SAP CSV: {str(e)}")
