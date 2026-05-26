# Architectural Trade-offs & Deliberate Cuts — Breathe ESG

Building enterprise software requires making calculated choices between product scope, system robustness, and implementation timelines. To deliver a highly stable, audit-ready platform within our sprint deadline, we made three deliberate architectural cuts.

---

## The Three Deliberate Cuts

### 1. No PDF Ingestion/Parsing for Utility Invoices
- **What was cut**: An automated PDF parser that accepts bill scans and uses optical character recognition (OCR) or document models to extract billing periods and kWh consumption.
- **Alternative implemented**: Direct ingestion of structured portal CSV dumps (`utility_sample.csv`).
- **Rationale**: Building a robust PDF parser requires integrating third-party AI models (e.g. AWS Textract, Azure Form Recognizer) which introduces significant cloud licensing costs, security risks (PII exposure on bill scans), and fragile parsing logic. A single pixel shift on an invoice could cause severe accounting errors. Accepting structured CSV exports guarantees **near-100% data reliability** and zero data loss, satisfying strict financial audit standards without expensive OCR overhead.

### 2. No Live API Integrations (SAP OData, Concur, or Utility APIs)
- **What was cut**: Real-time background syncs with active corporate SAP ERP ledgers, Concur travel systems, or Utility providers (e.g. UtilityAPI).
- **Alternative implemented**: Scalable file upload controllers (`/api/upload/sap/`, `/api/upload/utility/`, `/api/upload/travel/`).
- **Rationale**: Direct enterprise API integrations require extensive coordination with corporate IT departments to open firewall ports, manage OAuth credentials, and handle custom data mappings. Implementing live syncs during an initial pilot is counter-productive. By offering file ingestion, Breathe ESG remains **instantly compatible** with any enterprise system globally. Clients simply export standard reports and upload them in seconds.

### 3. No Multi-User Role System (Just Single Analyst / Admin Access)
- **What was cut**: Granular Role-Based Access Control (RBAC) that restricts certain users to upload-only, and limits approval permissions to specific managers.
- **Alternative implemented**: A single administrative analyst session (`admin` seeded account) with full ingestion, review, and approval permissions.
- **Rationale**: Designing custom role matrix middleware adds database complexity and slows down core audit review development. For our pilot launch, a single lead analyst role ensures the platform is highly usable and simple, while maintaining **accountability** through automatically generated `AuditLog` records. Future sprints can easily layer Django's built-in groups and permissions over the existing database models.
