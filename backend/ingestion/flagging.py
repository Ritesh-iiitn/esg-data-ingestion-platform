import numpy as np
from datetime import timedelta
from django.db.models import Q
from ingestion.models import EmissionRecord, Flag

def run_flagging_rules(client, parsed_records):
    """
    Takes a client and a list of parsed record dictionaries.
    Applies automatic flagging rules:
    1. OUTLIER (normalized_value > 3x median for activity_type in client)
    2. DUPLICATE (same doc_num/meter_id+period/tx_id exists in DB or upload)
    3. DATE_GAP (for utility, gap between billing periods for same meter)
    4. Overlaps for utility (flagged as DUPLICATE or DATE_GAP)
    
    Appends Flag dictionaries to each record's 'flags' list.
    """
    # 1. Prepare to check duplicates within the upload itself
    sap_doc_nums_in_upload = {}
    travel_tx_ids_in_upload = {}
    utility_periods_in_upload = {} # meter_id -> list of (start, end)
    
    # 2. Fetch existing records from DB to check client-wide rules
    existing_records = EmissionRecord.objects.filter(client=client)
    
    # Fetch existing unique identifiers for duplicate checks
    existing_sap_docs = set(
        existing_records.filter(source_type='SAP')
        .values_list('raw_data__Belegnum', flat=True)
    )
    existing_travel_txs = set(
        existing_records.filter(source_type='TRAVEL')
        .values_list('raw_data__transaction_id', flat=True)
    )
    
    # Existing utility periods by meter_id
    existing_utility_records = existing_records.filter(source_type='UTILITY')
    # meter_id -> list of dicts: {'start': date, 'end': date, 'id': id}
    meter_history = {}
    for r in existing_utility_records:
        m_id = r.raw_data.get('meter_id')
        if m_id:
            m_id = str(m_id).strip()
            if m_id not in meter_history:
                meter_history[m_id] = []
            meter_history[m_id].append({
                'start': r.period_start,
                'end': r.period_end
            })

    # Fetch client-wide median cache for outlier detection
    # activity_type -> list of values
    client_activity_values = {}
    for r in existing_records:
        act = r.activity_type
        if act not in client_activity_values:
            client_activity_values[act] = []
        client_activity_values[act].append(r.normalized_value)
        
    # Calculate median for each activity type in client
    client_activity_medians = {}
    for act, vals in client_activity_values.items():
        if len(vals) > 0:
            client_activity_medians[act] = np.median(vals)

    # 3. Iterate through parsed records and apply checks
    for idx, rec in enumerate(parsed_records):
        source = rec['source_type']
        flags = rec.get('flags', [])
        
        # --- ZERO VALUE check ---
        # (Some parsers already add this, but let's double check)
        if rec['normalized_value'] <= 0 and rec['activity_type'] not in ['flight', 'ground_transport']:
            # For flights/ground transport, if distance is 0 it is already flagged as MISSING_FACTOR
            if not any(f['flag_type'] == 'ZERO_VALUE' for f in flags):
                flags.append({
                    'flag_type': 'ZERO_VALUE',
                    'message': f"Value is zero or negative: {rec['raw_value']} {rec['raw_unit']}."
                })
        
        # --- DUPLICATE CHECKS ---
        if source == 'SAP':
            doc_num = rec.get('doc_num')
            if doc_num:
                # Check within upload
                if doc_num in sap_doc_nums_in_upload:
                    flags.append({
                        'flag_type': 'DUPLICATE',
                        'message': f"Duplicate document number '{doc_num}' found multiple times in this upload."
                    })
                    # Also flag the earlier one if not already flagged
                    prev_idx = sap_doc_nums_in_upload[doc_num]
                    prev_flags = parsed_records[prev_idx].get('flags', [])
                    if not any(f['flag_type'] == 'DUPLICATE' and doc_num in f['message'] for f in prev_flags):
                        prev_flags.append({
                            'flag_type': 'DUPLICATE',
                            'message': f"Duplicate document number '{doc_num}' found multiple times in this upload."
                        })
                else:
                    sap_doc_nums_in_upload[doc_num] = idx
                    
                # Check DB
                if doc_num in existing_sap_docs:
                    flags.append({
                        'flag_type': 'DUPLICATE',
                        'message': f"Document number '{doc_num}' already exists in database."
                    })
                    
        elif source == 'TRAVEL':
            tx_id = rec.get('tx_id')
            if tx_id:
                # Check within upload
                if tx_id in travel_tx_ids_in_upload:
                    flags.append({
                        'flag_type': 'DUPLICATE',
                        'message': f"Duplicate transaction ID '{tx_id}' found multiple times in this upload."
                    })
                    prev_idx = travel_tx_ids_in_upload[tx_id]
                    prev_flags = parsed_records[prev_idx].get('flags', [])
                    if not any(f['flag_type'] == 'DUPLICATE' and tx_id in f['message'] for f in prev_flags):
                        prev_flags.append({
                            'flag_type': 'DUPLICATE',
                            'message': f"Duplicate transaction ID '{tx_id}' found multiple times in this upload."
                        })
                else:
                    travel_tx_ids_in_upload[tx_id] = idx
                    
                # Check DB
                if tx_id in existing_travel_txs:
                    flags.append({
                        'flag_type': 'DUPLICATE',
                        'message': f"Transaction ID '{tx_id}' already exists in database."
                    })
                    
        elif source == 'UTILITY':
            m_id = rec.get('meter_id')
            p_start = rec['period_start']
            p_end = rec['period_end']
            
            if m_id:
                # Check overlaps in same upload
                if m_id not in utility_periods_in_upload:
                    utility_periods_in_upload[m_id] = []
                    
                for prev_idx, prev_start, prev_end in utility_periods_in_upload[m_id]:
                    # Overlap if: StartA < EndB and EndA > StartB
                    if p_start <= prev_end and p_end >= prev_start:
                        flags.append({
                            'flag_type': 'DUPLICATE',
                            'message': f"Billing period ({p_start} to {p_end}) overlaps with another period ({prev_start} to {prev_end}) for meter '{m_id}' in this upload."
                        })
                        # Flag the other one too
                        prev_flags = parsed_records[prev_idx].get('flags', [])
                        if not any(f['flag_type'] == 'DUPLICATE' and 'overlaps' in f['message'] for f in prev_flags):
                            prev_flags.append({
                                'flag_type': 'DUPLICATE',
                                'message': f"Billing period ({prev_start} to {prev_end}) overlaps with another period ({p_start} to {p_end}) for meter '{m_id}' in this upload."
                            })
                
                utility_periods_in_upload[m_id].append((idx, p_start, p_end))
                
                # Check overlaps in DB
                if m_id in meter_history:
                    for prev in meter_history[m_id]:
                        if p_start <= prev['end'] and p_end >= prev['start']:
                            flags.append({
                                'flag_type': 'DUPLICATE',
                                'message': f"Billing period ({p_start} to {p_end}) overlaps with an existing record ({prev['start']} to {prev['end']}) for meter '{m_id}' in DB."
                            })
                            
                # DATE GAP check:
                # Let's collect all start/end dates for this meter (both DB history and new upload)
                all_periods = []
                if m_id in meter_history:
                    all_periods.extend(meter_history[m_id])
                # Add all periods in this upload up to current one
                for up_idx, up_start, up_end in utility_periods_in_upload[m_id]:
                    all_periods.append({'start': up_start, 'end': up_end})
                    
                # Sort periods by start date
                all_periods = sorted(all_periods, key=lambda x: x['start'])
                
                # Find where this record sits and if there is a gap with the prior one
                for k in range(1, len(all_periods)):
                    curr = all_periods[k]
                    prev = all_periods[k-1]
                    # If this is our record, check gap with the previous one
                    if curr['start'] == p_start and curr['end'] == p_end:
                        gap_days = (curr['start'] - prev['end']).days
                        # A gap is when start date > end date + 1 day
                        if gap_days > 1:
                            flags.append({
                                'flag_type': 'DATE_GAP',
                                'message': f"Billing gap of {gap_days} days detected between period starting {curr['start']} and previous period ending {prev['end']} for meter '{m_id}'."
                            })

        # --- OUTLIER DETECTION ---
        act_type = rec['activity_type']
        val = rec['normalized_value']
        
        # Calculate median of values in this upload for same activity type to help if database has no records
        upload_vals = [r['normalized_value'] for r in parsed_records if r['activity_type'] == act_type]
        
        # Combine DB values with upload values to form local client-wide median
        combined_vals = []
        if act_type in client_activity_values:
            combined_vals.extend(client_activity_values[act_type])
        combined_vals.extend(upload_vals)
        
        if len(combined_vals) > 0:
            median_val = np.median(combined_vals)
            # OUTLIER if > 3x median
            # Avoid divide by zero / division on small median
            if median_val > 0 and val > 3 * median_val:
                flags.append({
                    'flag_type': 'OUTLIER',
                    'message': f"Value {val:.2f} is an outlier (> 3x median of {median_val:.2f} for activity '{act_type}')."
                })
        
        # Save updated flags list
        rec['flags'] = flags
        
    return parsed_records
