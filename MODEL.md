# Database Model Documentation — Breathe ESG

Breathe ESG relies on a highly structured, relational database designed to balance **immutable audit completeness** with **dynamic analyst interaction**. The system is built on PostgreSQL (hosted on Supabase) and managed using Django’s Object-Relational Mapper (ORM).

---

## Entity-Relationship Diagram & Schema Breakdown

### 1. Client (Multi-Tenancy Root)
- **Fields**:
  - `id`: BigAutoField (Primary Key)
  - `name`: CharField (e.g. "Acme Corporation")
  - `slug`: SlugField (Unique, URL-safe corporate identifier)
  - `created_at`: DateTimeField (Timestamp of client onboarding)
- **Purpose**: Acts as the root tenant for all data. Breathe ESG isolates uploads, records, flags, and audit logs by this key to enforce data privacy and security in multi-enterprise setups.

### 2. DataUpload (Ingestion Tracker)
- **Fields**:
  - `id`: BigAutoField (Primary Key)
  - `client`: ForeignKey -> `Client`
  - `source_type`: CharField (`SAP`, `UTILITY`, `TRAVEL`)
  - `uploaded_file`: FileField (Path to standard CSV export on disk or S3)
  - `uploaded_by`: ForeignKey -> Django `User`
  - `uploaded_at`: DateTimeField
  - `row_count`: IntegerField (Total rows successfully parsed)
  - `status`: CharField (`PROCESSING`, `DONE`, `FAILED`)
- **Purpose**: Tracks data lineage. Every record must lead back to a specific file upload event, detailing **who**, **when**, and **what file** introduced it.

### 3. EmissionRecord (Core Fact Table)
- **Fields**:
  - `id`: BigAutoField (Primary Key)
  - `client`: ForeignKey -> `Client`
  - `upload`: ForeignKey -> `DataUpload`
  - `source_type`: CharField (`SAP`, `UTILITY`, `TRAVEL`)
  - `scope`: IntegerField (`1`, `2`, `3`)
  - `activity_type`: CharField (`diesel`, `electricity`, `flight`, `hotel`, `ground_transport`)
  - `raw_value`: FloatField (Immutable raw number from CSV)
  - `raw_unit`: CharField (Immutable raw unit)
  - `raw_data`: JSONField (Full, unmodified key-value dictionary of the original CSV row)
  - `normalized_value`: FloatField (Standardized metric value)
  - `normalized_unit`: CharField (Standardized unit e.g. `L`, `kWh`, `km`, `nights`)
  - `emission_factor`: FloatField (Standard multiplier)
  - `emission_factor_source`: CharField (e.g. "DEFRA 2023")
  - `co2e_kg`: FloatField (Calculated carbon total in kilograms)
  - `period_start` / `period_end`: DateFields (Duration of the carbon emitting activity)
  - `status`: CharField (`PENDING`, `FLAGGED`, `APPROVED`, `REJECTED`)
  - `approved_by`: ForeignKey -> `User` (Nullable)
  - `approved_at`: DateTimeField (Nullable)
  - `analyst_note`: TextField (Note justifying modifications/approvals/rejections)
- **Purpose**: The central table containing all normalized carbon metrics. Represents the auditable system of record.

### 4. Flag (Automated Compliance Warnings)
- **Fields**:
  - `id`: BigAutoField (Primary Key)
  - `record`: ForeignKey -> `EmissionRecord`
  - `flag_type`: CharField (`UNIT_MISMATCH`, `OUTLIER`, `MISSING_FACTOR`, `DATE_GAP`, `DUPLICATE`, `ZERO_VALUE`)
  - `message`: TextField (Descriptive explanation of the warning)
  - `created_at`: DateTimeField
- **Purpose**: Tracks anomalies discovered during automatic rule checking. Allows analysts to quickly filter for suspicious records.

### 5. AuditLog (Immutable Revision Trail)
- **Fields**:
  - `id`: BigAutoField (Primary Key)
  - `record`: ForeignKey -> `EmissionRecord`
  - `action`: CharField (`APPROVED`, `REJECTED`, `EDITED`, `UPLOADED`)
  - `performed_by`: ForeignKey -> `User`
  - `performed_at`: DateTimeField
  - `previous_value` / `new_value`: JSONField (Snapshots of state during change)
  - `note`: TextField (Reasoning given by analyst)
- **Purpose**: Enforces accountability. Any change in state (especially transition to APPROVED or REJECTED) writes a permanent row documenting the transition.

---

## Architectural & Design Choices

### Multi-Tenancy Strategy
Every operational table contains a direct ForeignKey referencing the `Client`. Rather than relying on separate schemas (which adds database maintenance overhead), we employ a **shared database, shared schema** architecture. Queries are strictly scoped to the tenant ID by filtering via the API ViewSets. This enables low-cost enterprise scaling while maintaining strong logical isolation.

### Scope Classification Logic
- **Scope 1 (Direct Fuel)**: Fuel parsed from SAP (Diesel, Petrol, Natural Gas) represents fuel owned or controlled directly by the client organization.
- **Scope 2 (Indirect Electricity)**: Utility power consumption. Represents indirect emissions from purchased electricity.
- **Scope 3 (Value Chain)**: Employee travel (Flights, Hotel stays, Car rentals, Rail trips) representing value chain activities.

### Source-of-Truth & Unit Normalization
Raw metrics (e.g. quantities in gallons, MWh, miles) are preserved *exactly* as they arrived in `raw_value` and `raw_unit`. They are never altered. Normalization rules translate them to standard metric units:
- Gallons (GAL) $\rightarrow$ Liters (L) (Multiplied by 3.78541)
- Megawatt-hours (MWh) $\rightarrow$ Kilowatt-hours (kWh) (Multiplied by 1000.0)
- Missing distances for flights are calculated using coordinates/distances lookups.
This guarantees that auditors can trace the normalization calculations from the original source file.

### Why Storing `raw_data` as a JSONField is Critical
CSV columns frequently drift: suppliers may add additional descriptive columns, or change column ordering. Rather than creating endless schema migrations for auxiliary supplier fields (e.g. `Kostenstelle` cost centers or `tariff_code`), we capture the **entire row dictionary** in the `raw_data` JSONField.
This guarantees:
1. **No Data Loss**: Additional context (such as employee name, vehicle type) is retained for analyst inspection without cluttering the structured relational schema.
2. **Auditable Completeness**: Financial auditors can cross-examine the database row and verify it matches the raw CSV file on a character-by-character basis.
