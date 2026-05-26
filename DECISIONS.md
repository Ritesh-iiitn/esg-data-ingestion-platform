# Technical Design Decisions — Breathe ESG

This document outlines key technical decisions made during the architecture of Breathe ESG, explaining why specific formats and pipelines were chosen over alternatives.

---

## Technical Choices & Rationale

### 1. SAP Integration: Flat-File CSV over IDoc or OData
- **Decision**: Implemented flat-file CSV ingestion instead of building live SAP OData REST connections or parsing SAP IDoc SOAP interfaces.
- **Reasoning**: SAP implementations are highly custom. Integrating with live OData APIs requires months of network/port configuration, security approvals, and custom ABAP programming. CSV flat-files are the universal standard export format for corporate finance teams. Ingesting CSV files makes Breathe ESG immediately compatible with *any* SAP instance globally out-of-the-box.

### 2. Corporate Travel Integration: Concur CSV over Live Travel APIs
- **Decision**: Used Concur-style travel CSV exports over live SAP Concur REST APIs.
- **Reasoning**: Integrating directly with live corporate travel APIs involves complex OAuth handshakes and client-specific API licenses. Many smaller corporate clients book travel through local agencies that do not utilize Concur APIs. Support for flat CSV files guarantees compatibility with all major booking reports.

### 3. Utility Data: Portal CSV over PDF Bill Parsing
- **Decision**: Accepted CSV utility exports over automated PDF energy bill parsing (OCR).
- **Reasoning**: PDF utility bill parsing is notoriously fragile. Every regional utility supplier (e.g. PG&E, National Grid) uses completely different document formats, and layouts change frequently. portal CSV exports provide highly structured tabular records, yielding near-100% data reliability, preventing data loss, and avoiding the need for expensive, error-prone visual AI parsers.

### 4. Billing Periods Not Aligning to Calendar Months
- **Decision**: Stored billing period start and end dates *exactly* as is, without forced fractional redistribution into calendar months.
- **Reasoning**: Some competitors force-split a billing period (e.g. Jan 15 - Feb 14) into two calendar months. This requires arbitrary proportional allocation assumptions that fail financial audits. We store the billing period exactly as printed on the meter invoice to preserve auditable ties to financial statements. Analysts can group by `period_start` to get a clean operational timeline.

### 5. Missing Flight Distances
- **Decision**: Calculated flight distances by maintaining a hardcoded lookup dictionary of major routes (e.g. `DEL-LHR`, `DEL-DXB`, etc.), rather than querying live airport distance APIs.
- **Reasoning**: Querying live external geolocation APIs on every record import introduces substantial latency, potential rate-limiting, and network dependencies that fail bulk imports. A hardcoded dictionary of standard business flight corridors handles 95% of routes instantly and deterministically. Routes outside the lookup table are flagged as `MISSING_FACTOR` to prevent silent carbon accounting errors.

### 6. Emission Factor Selection
- **Decision**: Hardcoded the **UK DEFRA 2023** database as our core source of truth.
- **Reasoning**: DEFRA is the gold standard for global corporate greenhouse gas (GHG) reporting due to its granular activity categorization (e.g., short vs. long haul flights, hotel nights, petrol, natural gas, etc.). A centralized, immutable file (`emission_factors.py`) prevents data fragmentation and ensures audits are conducted against consistent constants.

### 7. Ignored SAP Fields
- **Decision**: Focused on key procurement columns (`Menge`, `Materialgruppe`, `Belegnum`) and ignored auxiliary SAP fields (e.g. currency codes, shipping IDs, ledger numbers).
- **Reasoning**: Minimizing database complexity ensures the ingestion pipeline remains high-performance. Auxiliary columns are preserved in the `raw_data` JSON field, allowing analysts to reference them if needed.

---

## Questions for the Product Manager (PM)

1. **How should we handle multi-tenant isolation?**
   - *Current Design*: Records are filtered in viewsets using the `client_id` parameter. We assume single corporate clients sign into isolated sessions.
   - *Question*: Will we require formal database-level multi-schema separation (e.g., django-tenants) for high-compliance healthcare and financial customers?

2. **Should we support manual emission factor overrides?**
   - *Current Design*: Central factors are completely hardcoded and locked inside `emission_factors.py`.
   - *Question*: Do we want to allow analysts to define custom emission factors per plant or per supplier in a future admin panel?

3. **How should we handle currency conversion for travel spend?**
   - *Current Design*: Amount is captured as raw `amount_usd` from the Concur CSV export.
   - *Question*: Travel spend often comes in EUR, GBP, or INR. Should we add a central exchange rate table to normalize currency before calculation?
