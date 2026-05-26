import pandas as pd
import numpy as np
from datetime import datetime
from django.core.exceptions import ValidationError
from ingestion.emission_factors import EMISSION_FACTORS, get_airport_distance
from ingestion.parsers.utils import sanitize_json_dict

def parse_travel_csv(file_wrapper):
    """
    Parses a Corporate Travel CSV file from a file object.
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
            'transaction_id', 'employee_id', 'travel_date', 
            'category', 'origin', 'destination', 'distance_km', 
            'nights', 'amount_usd', 'vendor_name'
        ]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValidationError(f"Missing required Travel columns: {', '.join(missing_cols)}")
            
        records = []
        for index, row in df.iterrows():
            raw_row = row.to_dict()
            
            # Map raw fields
            tx_id = str(raw_row.get('transaction_id', '')).strip()
            category = str(raw_row.get('category', '')).strip().lower()
            origin = str(raw_row.get('origin', '')).strip().upper()
            destination = str(raw_row.get('destination', '')).strip().upper()
            
            # Distance
            dist_val = raw_row.get('distance_km')
            try:
                # Handle blank/NaN/None values
                if pd.isna(dist_val) or str(dist_val).strip() == '' or dist_val is None:
                    distance_km = None
                else:
                    distance_km = float(dist_val)
            except Exception:
                distance_km = None
                
            # Nights
            nights_val = raw_row.get('nights')
            try:
                if pd.isna(nights_val) or str(nights_val).strip() == '' or nights_val is None:
                    nights = 0
                else:
                    nights = int(float(nights_val))
            except Exception:
                nights = 0
                
            # Parse Date (MM/DD/YYYY)
            date_str = str(raw_row.get('travel_date', '')).strip()
            try:
                travel_date = datetime.strptime(date_str, '%m/%d/%Y').date()
            except ValueError:
                try:
                    travel_date = pd.to_datetime(date_str).date()
                except Exception:
                    raise ValidationError(f"Invalid travel_date at row {index+1}: {date_str}")
                    
            activity_type = 'ground_transport'
            raw_value = 0.0
            raw_unit = 'km'
            normalized_value = 0.0
            normalized_unit = 'km'
            factor = 0.0
            factor_src = 'No factor found'
            co2e_kg = 0.0
            flags_to_create = []
            
            # Category classifications
            if category in ['air', 'flight', 'flight short haul', 'flight long haul']:
                activity_type = 'flight'
                raw_unit = 'km'
                normalized_unit = 'km'
                
                # Check origin == destination
                if origin == destination and origin != '':
                    flags_to_create.append({
                        'flag_type': 'OUTLIER',
                        'message': f"Flight origin matches destination: '{origin}'."
                    })
                
                # Calculate distance if missing
                if distance_km is None:
                    lookup_dist = get_airport_distance(origin, destination)
                    if lookup_dist is not None:
                        distance_km = float(lookup_dist)
                        # We still keep raw_value as empty/0 because it was empty, but normalized_value gets the lookup
                        raw_value = 0.0
                        normalized_value = distance_km
                    else:
                        # Cannot resolve distance
                        raw_value = 0.0
                        normalized_value = 0.0
                        flags_to_create.append({
                            'flag_type': 'MISSING_FACTOR',
                            'message': f"Flight route distance between '{origin}' and '{destination}' could not be resolved, and no distance was provided."
                        })
                else:
                    raw_value = distance_km
                    normalized_value = distance_km
                    
                # Unrealistic distance (>20,000 km)
                if normalized_value > 20000:
                    flags_to_create.append({
                        'flag_type': 'OUTLIER',
                        'message': f"Flight distance of {normalized_value:.2f} km is unrealistic (>20,000 km)."
                    })
                    
                # Emission factor selection
                if normalized_value > 0:
                    if normalized_value < 3700:
                        factor_info = EMISSION_FACTORS['flight_short_haul']
                        factor = factor_info['factor']
                        factor_src = factor_info['source']
                    else:
                        factor_info = EMISSION_FACTORS['flight_long_haul']
                        factor = factor_info['factor']
                        factor_src = factor_info['source']
                    co2e_kg = normalized_value * factor
                    
            elif category in ['hotel', 'stay', 'accommodation']:
                activity_type = 'hotel'
                raw_value = float(nights)
                raw_unit = 'nights'
                normalized_value = float(nights)
                normalized_unit = 'nights'
                
                factor_info = EMISSION_FACTORS['hotel']
                factor = factor_info['factor']
                factor_src = factor_info['source']
                
                if nights <= 0:
                    flags_to_create.append({
                        'flag_type': 'ZERO_VALUE',
                        'message': f"Hotel stay has zero or negative nights: {nights}."
                    })
                    
                co2e_kg = normalized_value * factor
                
            elif category in ['car', 'car rental', 'rail', 'ground', 'train']:
                raw_unit = 'km'
                normalized_unit = 'km'
                
                if distance_km is None or distance_km <= 0:
                    raw_value = 0.0
                    normalized_value = 0.0
                    flags_to_create.append({
                        'flag_type': 'MISSING_FACTOR',
                        'message': f"Ground transport distance is missing or zero for category '{category}'."
                    })
                else:
                    raw_value = distance_km
                    normalized_value = distance_km
                    
                if normalized_value > 20000:
                    flags_to_create.append({
                        'flag_type': 'OUTLIER',
                        'message': f"Ground transport distance of {normalized_value:.2f} km is unrealistic (>20,000 km)."
                    })
                    
                # Factor
                if category in ['rail', 'train']:
                    activity_type = 'ground_transport'
                    factor_info = EMISSION_FACTORS['rail']
                else:
                    activity_type = 'ground_transport'
                    factor_info = EMISSION_FACTORS['car_rental']
                    
                factor = factor_info['factor']
                factor_src = factor_info['source']
                co2e_kg = normalized_value * factor
            else:
                # Catch-all category
                activity_type = 'ground_transport'
                raw_unit = 'km'
                normalized_unit = 'km'
                raw_value = distance_km or 0.0
                normalized_value = raw_value
                flags_to_create.append({
                    'flag_type': 'MISSING_FACTOR',
                    'message': f"Unknown travel category '{category}'. Treated as ground transport without standard factor."
                })
                
            records.append({
                'source_type': 'TRAVEL',
                'scope': 3,
                'activity_type': activity_type,
                'raw_value': raw_value,
                'raw_unit': raw_unit,
                'raw_data': sanitize_json_dict(raw_row),
                'normalized_value': normalized_value,
                'normalized_unit': normalized_unit,
                'emission_factor': factor,
                'emission_factor_source': factor_src,
                'co2e_kg': co2e_kg,
                'period_start': travel_date,
                'period_end': travel_date,
                'tx_id': tx_id,  # for duplicate check
                'flags': flags_to_create
            })
            
        return records
    except Exception as e:
        if isinstance(e, ValidationError):
            raise e
        raise ValidationError(f"Error parsing Travel CSV: {str(e)}")
