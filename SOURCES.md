# Data Source Ingestion Research — Breathe ESG

This document details the real-world research behind our three data source formats and explains why our sample files represent realistic enterprise data.

---

## 1. SAP — Fuel & Procurement (Scope 1)

### Real-World Format Research
In production environments, SAP ERP systems track materials using the **MM (Materials Management)** and **FI (Financial Accounting)** modules. Organizations pull flat reports listing internal ledger movements for specific material groups (e.g. diesel fuels, motor gasoline, compressed natural gas).
Key characteristics of SAP exports:
- **German Column Headers**: SAP has deep German roots, and standard default report headers frequently retain German terms (e.g., `Werk` for Plant, `Mengeneinheit` for Unit, `Belegnum` for Document Number, `Menge` for Quantity).
- **Plant Codes**: Corporate sites are represented by specific alphanumeric strings (e.g. `PL-0042`).

### Why Our Sample Data Looks This Way
- `sap_sample.csv` utilizes the exact German headers (`Werk`, `Buchungsdatum`, `Menge`, `Mengeneinheit`, `Materialgruppe`, `Kostenstelle`, `Belegnum`) to mimic real-world financial outputs.
- We included a **duplicate Belegnum** (`SAP-10001`) to simulate common data export overlaps where the same transaction is logged in multiple accounting cycles.
- We added an **invalid unit** `LBS` to trigger our `UNIT_MISMATCH` compliance flag.

---

## 2. Utility — Electricity (Scope 2)

### Real-World Format Research
Commercial utility providers (e.g. PG&E, ConEd) allow facility managers to download CSV files containing meter readings directly from their customer portals.
Key characteristics of utility portal exports:
- **Meter Identifiers**: Every building or sub-station is identified by a unique `meter_id`.
- **Billing Cycles**: Billing periods rarely align with standard calendar months (e.g., billing may run from Jan 5 to Feb 4).
- **Mixed Units**: Larger industrial sites consume electricity measured in Megawatt-hours (MWh), while smaller commercial offices consume Kilowatt-hours (kWh).

### Why Our Sample Data Looks This Way
- `utility_sample.csv` spans three distinct meters across two corporate physical locations.
- We included a **MWh to kWh conversion** case (`15.2 MWh` on `MTR-88001`) to test the normalization calculations.
- We introduced an **overlapping billing period** on `MTR-88001` (Feb 15 to Mar 15, which overlaps with the Feb 1 to Feb 28 record) to trigger our `DUPLICATE` overlap flag.
- We introduced a **zero-consumption entry** (`0.0 kWh`) to trigger our `ZERO_VALUE` flag, which helps analysts identify faulty meters.

---

## 3. Corporate Travel — Flights, Hotels, Ground (Scope 3)

### Real-World Format Research
Global corporate travel managers (such as SAP Concur or Navan) provide travel coordinators with structured monthly CSV ledger dumps outlining employee bookings.
Key characteristics of travel exports:
- **Transaction Identifiers**: Unique booking receipts map to a `transaction_id`.
- **Missing Geolocation Data**: Travel logs frequently lack actual route distances for air travel, providing only the origin and destination airport codes (e.g., `DEL` to `LHR`).
- **Mixed Modes**: Stays are logged in `nights` (hotel accommodation), while flight and rail segments are measured in miles or kilometers.

### Why Our Sample Data Looks This Way
- `travel_sample.csv` mixes `Air`, `Hotel`, `Car`, and `Rail` rows to validate the classification engine.
- We left the **distance column blank** on major routes (e.g. `DEL-LHR`, `DEL-DXB`, `BOM-SIN`) to trigger our automated airport route distance lookups.
- We added an **origin == destination** case (`DEL` to `DEL`) to trigger our duplicate location travel flag.
- We included an **unrealistic distance** (`24,000 km`) to trigger our `OUTLIER` flag, letting the analyst know that the employee travel details are highly suspicious.

---

## What Would Break in a Real Deployment

1. **Date Formats**: In real-world data, date formats are highly inconsistent (e.g., `YYYY-MM-DD`, `DD/MM/YYYY`, `MM-DD-YY`). Standardizing date parsing would require a fallback parsing chain using `dateutil.parser`.
2. **Missing Air Routing Codes**: If an employee books a flight containing a regional airport (e.g. a small charter strip), it will fail our hardcoded lookup table. A production system must integrate with a live airport coordinates database (e.g. OpenFlights) to calculate distance using the Haversine equation.
3. **Data Encoding Issues**: CSV files exported from legacy windows systems are frequently encoded in `UTF-16` or `ISO-8859-1` rather than standard `UTF-8`. Ingesting these files directly would trigger unicode decoding crashes.
