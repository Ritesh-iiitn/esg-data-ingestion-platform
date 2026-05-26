# central emission factors (DEFRA 2023)

EMISSION_FACTORS = {
    # Fuel (Scope 1) - per unit (L, M3)
    "diesel": {
        "factor": 2.68,
        "unit": "L",
        "source": "DEFRA 2023"
    },
    "petrol": {
        "factor": 2.31,
        "unit": "L",
        "source": "DEFRA 2023"
    },
    "natural_gas": {
        "factor": 2.02,
        "unit": "M3",
        "source": "DEFRA 2023"
    },
    
    # Electricity (Scope 2) - per kWh
    "electricity": {
        "factor": 0.233,
        "unit": "kWh",
        "source": "UK grid, DEFRA 2023"
    },
    
    # Travel & Accommodation (Scope 3)
    "flight_short_haul": {
        "factor": 0.255,
        "unit": "km",
        "source": "DEFRA 2023"  # < 3700 km
    },
    "flight_long_haul": {
        "factor": 0.195,
        "unit": "km",
        "source": "DEFRA 2023"  # >= 3700 km
    },
    "hotel": {
        "factor": 31.2,
        "unit": "night",
        "source": "DEFRA 2023"
    },
    "car_rental": {
        "factor": 0.168,
        "unit": "km",
        "source": "DEFRA 2023"
    },
    "rail": {
        "factor": 0.041,
        "unit": "km",
        "source": "DEFRA 2023"
    }
}

# Major airport routes lookup table (distance in km)
AIRPORT_ROUTES = {
    # Sorted route keys for easy lookup
    "DEL-LHR": 6710,
    "DEL-DXB": 2200,
    "BOM-SIN": 3900,
    "DEL-BOM": 1140,
    "DEL-SIN": 4150,
    "BOM-LHR": 7190,
    "JFK-LHR": 5570,
    "CDG-LHR": 350,
    "CDG-JFK": 5840,
    "DXB-LHR": 5470,
    "BOM-DXB": 1930,
    "DXB-SIN": 5850,
    "JFK-SIN": 15340,
    "BOM-JFK": 12540,
    "CDG-DEL": 6570,
    "CDG-DXB": 5240,
    "CDG-SIN": 10400,
}

def get_airport_distance(origin, destination):
    """
    Calculate distance in km between two airports using lookup table.
    Returns None if route is not in lookup table.
    """
    if not origin or not destination:
        return None
    
    org = origin.strip().upper()
    dest = destination.strip().upper()
    
    # Sort key alphabetically to support bidirectional lookups
    route_key = "-".join(sorted([org, dest]))
    return AIRPORT_ROUTES.get(route_key, None)
