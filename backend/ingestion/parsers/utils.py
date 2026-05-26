import math
import pandas as pd

def sanitize_json_dict(d):
    """
    Recursively replaces NaN, infinity, and NaT values in a dict/list/value
    with None, so that they are serialized as JSON null and don't violate
    database constraints (SQLite JSON_VALID).
    """
    if isinstance(d, dict):
        return {k: sanitize_json_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [sanitize_json_dict(x) for x in d]
    elif isinstance(d, float):
        if math.isnan(d) or math.isinf(d):
            return None
        return d
    elif pd.isna(d):
        return None
    return d
