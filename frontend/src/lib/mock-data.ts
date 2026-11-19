import type {
  Framework,
  FrameworkVersion,
  ControlWithStatus,
  Risk,
  Evidence,
  Policy,
  Vendor,
} from "@/types/grc";

// --- Frameworks ---

const frameworks: Framework[] = [
  {
    id: "fw-soc2",
    key: "soc2",
    name: "SOC 2 Type II",
    description: "Service Organization Control 2 — Trust Services Criteria for security, availability, processing integrity, confidentiality, and privacy.",
    organization: "AICPA",
  },
  {
    id: "fw-iso27001",
    key: "iso27001",
    name: "ISO 27001:2022",
    description: "Information security management systems — Requirements. International standard for establishing, implementing, maintaining, and continually improving an ISMS.",
    organization: "ISO/IEC",
  },
];

const frameworkVersions: FrameworkVersion[] = [
  { id: "fv-soc2-2017", framework_id: "fw-soc2", version: "2017", is_current: true },
  { id: "fv-iso27001-2022", framework_id: "fw-iso27001", version: "2022", is_current: true },
];

// --- SOC 2 Controls ---

const soc2Controls: ControlWithStatus[] = [
  { id: "c-cc1.1", framework_version_id: "fv-soc2-2017", code: "CC1.1", title: "COSO Principle 1: Demonstrates commitment to integrity and ethical values", description: "The entity demonstrates a commitment to integrity and ethical values.", category: "Control Environment", parent_id: null, sort_order: 1, tenant_status: { id: "ts-1", control_id: "c-cc1.1", status: "implemented", effectiveness: "full", owner_id: "u-1", owner_name: "Sarah Chen", notes: null, last_assessed_at: "2024-10-15", evidence_count: 3 } },
  { id: "c-cc1.2", framework_version_id: "fv-soc2-2017", code: "CC1.2", title: "COSO Principle 2: Board exercises oversight responsibility", description: "The board of directors demonstrates independence from management and exercises oversight.", category: "Control Environment", parent_id: null, sort_order: 2, tenant_status: { id: "ts-2", control_id: "c-cc1.2", status: "implemented", effectiveness: "partial", owner_id: "u-1", owner_name: "Sarah Chen", notes: null, last_assessed_at: "2024-10-15", evidence_count: 2 } },
  { id: "c-cc1.3", framework_version_id: "fv-soc2-2017", code: "CC1.3", title: "COSO Principle 3: Establishes structure, authority, and responsibility", description: "Management establishes structures, reporting lines, and appropriate authorities and responsibilities.", category: "Control Environment", parent_id: null, sort_order: 3, tenant_status: { id: "ts-3", control_id: "c-cc1.3", status: "in_progress", effectiveness: null, owner_id: "u-2", owner_name: "James Wilson", notes: "Org chart update pending", last_assessed_at: null, evidence_count: 1 } },
  { id: "c-cc2.1", framework_version_id: "fv-soc2-2017", code: "CC2.1", title: "COSO Principle 13: Obtains or generates relevant quality information", description: "The entity obtains or generates and uses relevant, quality information.", category: "Communication & Information", parent_id: null, sort_order: 4, tenant_status: { id: "ts-4", control_id: "c-cc2.1", status: "not_started", effectiveness: null, owner_id: null, owner_name: null, notes: null, last_assessed_at: null, evidence_count: 0 } },
  { id: "c-cc3.1", framework_version_id: "fv-soc2-2017", code: "CC3.1", title: "COSO Principle 6: Specifies suitable objectives", description: "The entity specifies objectives with sufficient clarity.", category: "Risk Assessment", parent_id: null, sort_order: 5, tenant_status: { id: "ts-5", control_id: "c-cc3.1", status: "implemented", effectiveness: "full", owner_id: "u-1", owner_name: "Sarah Chen", notes: null, last_assessed_at: "2024-09-20", evidence_count: 2 } },
  { id: "c-cc3.2", framework_version_id: "fv-soc2-2017", code: "CC3.2", title: "COSO Principle 7: Identifies and analyzes risk", description: "The entity identifies risks to the achievement of its objectives.", category: "Risk Assessment", parent_id: null, sort_order: 6, tenant_status: { id: "ts-6", control_id: "c-cc3.2", status: "in_progress", effectiveness: null, owner_id: "u-2", owner_name: "James Wilson", notes: "Risk register in progress", last_assessed_at: null, evidence_count: 0 } },
  { id: "c-cc5.1", framework_version_id: "fv-soc2-2017", code: "CC5.1", title: "COSO Principle 10: Selects and develops control activities", description: "The entity selects and develops control activities that mitigate risks.", category: "Control Activities", parent_id: null, sort_order: 7, tenant_status: { id: "ts-7", control_id: "c-cc5.1", status: "implemented", effectiveness: "partial", owner_id: "u-3", owner_name: "Maria Garcia", notes: null, last_assessed_at: "2024-10-01", evidence_count: 4 } },
  { id: "c-cc6.1", framework_version_id: "fv-soc2-2017", code: "CC6.1", title: "Logical and physical access controls", description: "The entity implements logical access security software, infrastructure, and architectures.", category: "Logical & Physical Access Controls", parent_id: null, sort_order: 8, tenant_status: { id: "ts-8", control_id: "c-cc6.1", status: "implemented", effectiveness: "full", owner_id: "u-3", owner_name: "Maria Garcia", notes: null, last_assessed_at: "2024-11-01", evidence_count: 5 } },
  { id: "c-cc6.2", framework_version_id: "fv-soc2-2017", code: "CC6.2", title: "Prior to issuing system credentials and granting system access", description: "Prior to issuing credentials, the entity registers and authorizes new users.", category: "Logical & Physical Access Controls", parent_id: null, sort_order: 9, tenant_status: { id: "ts-9", control_id: "c-cc6.2", status: "implemented", effectiveness: "full", owner_id: "u-3", owner_name: "Maria Garcia", notes: null, last_assessed_at: "2024-11-01", evidence_count: 3 } },
  { id: "c-cc6.3", framework_version_id: "fv-soc2-2017", code: "CC6.3", title: "Role-based access and least privilege", description: "The entity authorizes, modifies, or removes access based on roles.", category: "Logical & Physical Access Controls", parent_id: null, sort_order: 10, tenant_status: { id: "ts-10", control_id: "c-cc6.3", status: "in_progress", effectiveness: null, owner_id: "u-3", owner_name: "Maria Garcia", notes: "RBAC rollout in progress", last_assessed_at: null, evidence_count: 1 } },
  { id: "c-cc7.1", framework_version_id: "fv-soc2-2017", code: "CC7.1", title: "Detects changes to infrastructure and software", description: "The entity uses detection and monitoring procedures to identify changes.", category: "System Operations", parent_id: null, sort_order: 11, tenant_status: { id: "ts-11", control_id: "c-cc7.1", status: "not_started", effectiveness: null, owner_id: null, owner_name: null, notes: null, last_assessed_at: null, evidence_count: 0 } },
  { id: "c-cc7.2", framework_version_id: "fv-soc2-2017", code: "CC7.2", title: "Monitors system components for anomalies", description: "The entity monitors system components for anomalies that are indicative of threats.", category: "System Operations", parent_id: null, sort_order: 12, tenant_status: { id: "ts-12", control_id: "c-cc7.2", status: "failed", effectiveness: "none", owner_id: "u-2", owner_name: "James Wilson", notes: "Monitoring gaps identified in last review", last_assessed_at: "2024-09-15", evidence_count: 1 } },
  { id: "c-cc8.1", framework_version_id: "fv-soc2-2017", code: "CC8.1", title: "Change management processes", description: "The entity authorizes, designs, develops, configures, documents, tests, approves, and implements changes.", category: "Change Management", parent_id: null, sort_order: 13, tenant_status: { id: "ts-13", control_id: "c-cc8.1", status: "implemented", effectiveness: "partial", owner_id: "u-2", owner_name: "James Wilson", notes: null, last_assessed_at: "2024-10-20", evidence_count: 2 } },
  { id: "c-cc9.1", framework_version_id: "fv-soc2-2017", code: "CC9.1", title: "Risk mitigation", description: "The entity identifies, selects, and develops risk mitigation activities.", category: "Risk Mitigation", parent_id: null, sort_order: 14, tenant_status: { id: "ts-14", control_id: "c-cc9.1", status: "not_applicable", effectiveness: null, owner_id: null, owner_name: null, notes: "Covered under CC3.2", last_assessed_at: null, evidence_count: 0 } },
  { id: "c-a1.1", framework_version_id: "fv-soc2-2017", code: "A1.1", title: "Availability commitments and requirements", description: "The entity maintains, monitors, and evaluates current processing capacity.", category: "Availability", parent_id: null, sort_order: 15, tenant_status: { id: "ts-15", control_id: "c-a1.1", status: "in_progress", effectiveness: null, owner_id: "u-2", owner_name: "James Wilson", notes: "SLA metrics being defined", last_assessed_at: null, evidence_count: 0 } },
];

// --- ISO 27001 Controls ---

const iso27001Controls: ControlWithStatus[] = [
  { id: "c-a5.1", framework_version_id: "fv-iso27001-2022", code: "A.5.1", title: "Policies for information security", description: "Information security policy and topic-specific policies shall be defined.", category: "Organizational Controls", parent_id: null, sort_order: 1, tenant_status: { id: "ts-101", control_id: "c-a5.1", status: "implemented", effectiveness: "full", owner_id: "u-1", owner_name: "Sarah Chen", notes: null, last_assessed_at: "2024-10-10", evidence_count: 2 } },
  { id: "c-a5.2", framework_version_id: "fv-iso27001-2022", code: "A.5.2", title: "Information security roles and responsibilities", description: "Information security roles and responsibilities shall be defined and allocated.", category: "Organizational Controls", parent_id: null, sort_order: 2, tenant_status: { id: "ts-102", control_id: "c-a5.2", status: "implemented", effectiveness: "partial", owner_id: "u-1", owner_name: "Sarah Chen", notes: null, last_assessed_at: "2024-10-10", evidence_count: 1 } },
  { id: "c-a5.3", framework_version_id: "fv-iso27001-2022", code: "A.5.3", title: "Segregation of duties", description: "Conflicting duties and conflicting areas of responsibility shall be segregated.", category: "Organizational Controls", parent_id: null, sort_order: 3, tenant_status: { id: "ts-103", control_id: "c-a5.3", status: "not_started", effectiveness: null, owner_id: null, owner_name: null, notes: null, last_assessed_at: null, evidence_count: 0 } },
  { id: "c-a6.1", framework_version_id: "fv-iso27001-2022", code: "A.6.1", title: "Screening", description: "Background verification checks on all candidates for employment shall be carried out.", category: "People Controls", parent_id: null, sort_order: 4, tenant_status: { id: "ts-104", control_id: "c-a6.1", status: "implemented", effectiveness: "full", owner_id: "u-1", owner_name: "Sarah Chen", notes: null, last_assessed_at: "2024-09-01", evidence_count: 3 } },
  { id: "c-a6.2", framework_version_id: "fv-iso27001-2022", code: "A.6.2", title: "Terms and conditions of employment", description: "Employment contractual agreements shall state responsibilities for information security.", category: "People Controls", parent_id: null, sort_order: 5, tenant_status: { id: "ts-105", control_id: "c-a6.2", status: "implemented", effectiveness: "full", owner_id: "u-1", owner_name: "Sarah Chen", notes: null, last_assessed_at: "2024-09-01", evidence_count: 2 } },
  { id: "c-a7.1", framework_version_id: "fv-iso27001-2022", code: "A.7.1", title: "Physical security perimeters", description: "Security perimeters shall be defined and used to protect areas containing information.", category: "Physical Controls", parent_id: null, sort_order: 6, tenant_status: { id: "ts-106", control_id: "c-a7.1", status: "not_applicable", effectiveness: null, owner_id: null, owner_name: null, notes: "Fully cloud-based, no physical premises", last_assessed_at: null, evidence_count: 0 } },
  { id: "c-a8.1", framework_version_id: "fv-iso27001-2022", code: "A.8.1", title: "User endpoint devices", description: "Information stored on, processed by, or accessible via user endpoint devices shall be protected.", category: "Technological Controls", parent_id: null, sort_order: 7, tenant_status: { id: "ts-107", control_id: "c-a8.1", status: "in_progress", effectiveness: null, owner_id: "u-3", owner_name: "Maria Garcia", notes: "MDM rollout in progress", last_assessed_at: null, evidence_count: 1 } },
  { id: "c-a8.2", framework_version_id: "fv-iso27001-2022", code: "A.8.2", title: "Privileged access rights", description: "The allocation and use of privileged access rights shall be restricted and managed.", category: "Technological Controls", parent_id: null, sort_order: 8, tenant_status: { id: "ts-108", control_id: "c-a8.2", status: "implemented", effectiveness: "partial", owner_id: "u-3", owner_name: "Maria Garcia", notes: null, last_assessed_at: "2024-10-15", evidence_count: 2 } },
  { id: "c-a8.3", framework_version_id: "fv-iso27001-2022", code: "A.8.3", title: "Information access restriction", description: "Access to information shall be restricted in accordance with the access control policy.", category: "Technological Controls", parent_id: null, sort_order: 9, tenant_status: { id: "ts-109", control_id: "c-a8.3", status: "implemented", effectiveness: "full", owner_id: "u-3", owner_name: "Maria Garcia", notes: null, last_assessed_at: "2024-10-15", evidence_count: 3 } },
  { id: "c-a8.7", framework_version_id: "fv-iso27001-2022", code: "A.8.7", title: "Protection against malware", description: "Protection against malware shall be implemented and supported by user awareness.", category: "Technological Controls", parent_id: null, sort_order: 10, tenant_status: { id: "ts-110", control_id: "c-a8.7", status: "in_progress", effectiveness: null, owner_id: "u-2", owner_name: "James Wilson", notes: "EDR evaluation underway", last_assessed_at: null, evidence_count: 0 } },
  { id: "c-a8.9", framework_version_id: "fv-iso27001-2022", code: "A.8.9", title: "Configuration management", description: "Configurations including security configurations shall be established, documented, and managed.", category: "Technological Controls", parent_id: null, sort_order: 11, tenant_status: { id: "ts-111", control_id: "c-a8.9", status: "failed", effectiveness: "none", owner_id: "u-2", owner_name: "James Wilson", notes: "Baseline configs not documented", last_assessed_at: "2024-09-20", evidence_count: 0 } },
  { id: "c-a8.15", framework_version_id: "fv-iso27001-2022", code: "A.8.15", title: "Logging", description: "Logs that record activities, exceptions, faults shall be produced, stored, protected, and analysed.", category: "Technological Controls", parent_id: null, sort_order: 12, tenant_status: { id: "ts-112", control_id: "c-a8.15", status: "implemented", effectiveness: "partial", owner_id: "u-2", owner_name: "James Wilson", notes: null, last_assessed_at: "2024-10-01", evidence_count: 2 } },
  { id: "c-a8.24", framework_version_id: "fv-iso27001-2022", code: "A.8.24", title: "Use of cryptography", description: "Rules for the effective use of cryptography shall be defined and implemented.", category: "Technological Controls", parent_id: null, sort_order: 13, tenant_status: { id: "ts-113", control_id: "c-a8.24", status: "implemented", effectiveness: "full", owner_id: "u-3", owner_name: "Maria Garcia", notes: null, last_assessed_at: "2024-10-20", evidence_count: 1 } },
  { id: "c-a8.25", framework_version_id: "fv-iso27001-2022", code: "A.8.25", title: "Secure development life cycle", description: "Rules for the secure development of software shall be established and applied.", category: "Technological Controls", parent_id: null, sort_order: 14, tenant_status: { id: "ts-114", control_id: "c-a8.25", status: "not_started", effectiveness: null, owner_id: null, owner_name: null, notes: null, last_assessed_at: null, evidence_count: 0 } },
  { id: "c-a5.23", framework_version_id: "fv-iso27001-2022", code: "A.5.23", title: "Information security for use of cloud services", description: "Processes for acquisition, use, management, and exit from cloud services shall be established.", category: "Organizational Controls", parent_id: null, sort_order: 15, tenant_status: { id: "ts-115", control_id: "c-a5.23", status: "in_progress", effectiveness: null, owner_id: "u-1", owner_name: "Sarah Chen", notes: "Cloud policy drafted", last_assessed_at: null, evidence_count: 1 } },
];

// --- Risks ---

const risks: Risk[] = [
  { id: "r-1", title: "Unauthorized cross-tenant data access", description: "A vulnerability in tenant isolation could allow one tenant to access another tenant's data, leading to a severe data breach and loss of customer trust.", category: "technical", likelihood: "low", impact: "very_high", inherent_score: 20, treatment: "mitigate", residual_score: 5, status: "mitigating", owner_id: "u-3", owner_name: "Maria Garcia", due_date: "2025-01-15", created_at: "2024-08-01T10:00:00Z", updated_at: "2024-11-01T14:00:00Z" },
  { id: "r-2", title: "Cloud credential compromise", description: "Stored cloud credentials (AWS/Azure) could be exfiltrated through application vulnerability or insider threat, allowing unauthorized access to customer cloud environments.", category: "technical", likelihood: "low", impact: "very_high", inherent_score: 20, treatment: "mitigate", residual_score: 8, status: "mitigating", owner_id: "u-3", owner_name: "Maria Garcia", due_date: "2025-02-01", created_at: "2024-08-05T09:00:00Z", updated_at: "2024-10-15T11:00:00Z" },
  { id: "r-3", title: "Compliance framework data inaccuracy", description: "Incorrect mapping of controls to compliance frameworks could mislead customers about their compliance posture, resulting in failed audits.", category: "compliance", likelihood: "medium", impact: "high", inherent_score: 16, treatment: "mitigate", residual_score: 6, status: "mitigating", owner_id: "u-1", owner_name: "Sarah Chen", due_date: "2025-01-30", created_at: "2024-08-10T08:00:00Z", updated_at: "2024-10-20T09:00:00Z" },
  { id: "r-4", title: "Service availability disruption", description: "Infrastructure failure or DDoS attack could make the platform unavailable, impacting customers preparing for audits with tight deadlines.", category: "operational", likelihood: "medium", impact: "high", inherent_score: 16, treatment: "mitigate", residual_score: 8, status: "open", owner_id: "u-2", owner_name: "James Wilson", due_date: "2025-03-01", created_at: "2024-08-15T10:00:00Z", updated_at: "2024-11-05T10:00:00Z" },
  { id: "r-5", title: "Evidence tampering or loss", description: "Audit evidence could be modified or deleted without detection, undermining the integrity of compliance assessments.", category: "compliance", likelihood: "low", impact: "high", inherent_score: 12, treatment: "mitigate", residual_score: 4, status: "mitigating", owner_id: "u-1", owner_name: "Sarah Chen", due_date: "2025-01-15", created_at: "2024-09-01T11:00:00Z", updated_at: "2024-10-25T15:00:00Z" },
  { id: "r-6", title: "Third-party dependency vulnerability", description: "Critical vulnerability in an open-source dependency (Prowler, Trivy, or application libraries) could be exploited before patching.", category: "technical", likelihood: "medium", impact: "medium", inherent_score: 12, treatment: "mitigate", residual_score: 6, status: "open", owner_id: "u-2", owner_name: "James Wilson", due_date: null, created_at: "2024-09-05T09:00:00Z", updated_at: "2024-09-05T09:00:00Z" },
  { id: "r-7", title: "Regulatory non-compliance (GDPR)", description: "Failure to properly handle EU customer data per GDPR requirements could result in regulatory fines and loss of EU market access.", category: "compliance", likelihood: "medium", impact: "high", inherent_score: 16, treatment: "accept", residual_score: 16, status: "accepted", owner_id: "u-1", owner_name: "Sarah Chen", due_date: null, created_at: "2024-09-10T10:00:00Z", updated_at: "2024-10-01T10:00:00Z" },
  { id: "r-8", title: "Scanner resource exhaustion", description: "Concurrent security scans could exhaust system resources, degrading service for all tenants.", category: "operational", likelihood: "high", impact: "medium", inherent_score: 16, treatment: "mitigate", residual_score: 6, status: "mitigating", owner_id: "u-2", owner_name: "James Wilson", due_date: "2024-12-31", created_at: "2024-09-15T14:00:00Z", updated_at: "2024-11-10T08:00:00Z" },
  { id: "r-9", title: "Key personnel dependency", description: "Loss of key engineering personnel could delay critical security features and compliance milestones.", category: "strategic", likelihood: "medium", impact: "medium", inherent_score: 12, treatment: "mitigate", residual_score: 8, status: "open", owner_id: "u-1", owner_name: "Sarah Chen", due_date: null, created_at: "2024-09-20T09:00:00Z", updated_at: "2024-09-20T09:00:00Z" },
  { id: "r-10", title: "Vendor data breach (subprocessor)", description: "A data breach at a third-party vendor or cloud subprocessor could expose customer data.", category: "reputational", likelihood: "low", impact: "high", inherent_score: 12, treatment: "transfer", residual_score: 8, status: "open", owner_id: "u-1", owner_name: "Sarah Chen", due_date: null, created_at: "2024-10-01T08:00:00Z", updated_at: "2024-10-01T08:00:00Z" },
  { id: "r-11", title: "Inadequate backup and recovery", description: "Failure to properly back up or restore customer data could result in permanent data loss during an incident.", category: "operational", likelihood: "low", impact: "very_high", inherent_score: 20, treatment: "mitigate", residual_score: 5, status: "mitigating", owner_id: "u-2", owner_name: "James Wilson", due_date: "2025-01-15", created_at: "2024-10-05T11:00:00Z", updated_at: "2024-11-01T16:00:00Z" },
  { id: "r-12", title: "API rate limit abuse", description: "Insufficient rate limiting on API endpoints could allow denial-of-service or brute-force attacks.", category: "technical", likelihood: "high", impact: "low", inherent_score: 8, treatment: "mitigate", residual_score: 3, status: "closed", owner_id: "u-3", owner_name: "Maria Garcia", due_date: null, created_at: "2024-10-10T09:00:00Z", updated_at: "2024-11-15T10:00:00Z" },
];

// --- Evidence ---

const evidence: Evidence[] = [
  { id: "e-1", title: "Access Control Policy v2.1", description: "Organization-wide access control policy covering user provisioning, deprovisioning, and review procedures.", file_name: "access-control-policy-v2.1.pdf", file_size: 245760, content_type: "application/pdf", sha256_hash: "a3f2b8c1d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1", version: 2, status: "approved", uploaded_by: "u-1", uploaded_by_name: "Sarah Chen", approved_by: "u-1", expires_at: "2025-10-15T00:00:00Z", tags: ["policy", "access-control"], created_at: "2024-10-15T10:30:00Z" },
  { id: "e-2", title: "AWS Security Scan Report — October 2024", description: "Prowler scan results for production AWS account covering all CIS benchmarks.", file_name: "aws-prowler-scan-oct2024.json", file_size: 1048576, content_type: "application/json", sha256_hash: "b4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5", version: 1, status: "approved", uploaded_by: "u-2", uploaded_by_name: "James Wilson", approved_by: "u-1", expires_at: "2025-04-15T00:00:00Z", tags: ["scan", "aws", "cloud-security"], created_at: "2024-10-20T14:00:00Z" },
  { id: "e-3", title: "Employee Background Check Completion Log", description: "Consolidated log of background check completions for all current employees.", file_name: "background-checks-q3-2024.xlsx", file_size: 51200, content_type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", sha256_hash: "c5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6", version: 1, status: "approved", uploaded_by: "u-1", uploaded_by_name: "Sarah Chen", approved_by: "u-1", expires_at: "2025-09-01T00:00:00Z", tags: ["hr", "background-check"], created_at: "2024-09-01T09:00:00Z" },
  { id: "e-4", title: "Incident Response Plan", description: "Documented incident response procedures including escalation paths and communication templates.", file_name: "incident-response-plan-v1.3.pdf", file_size: 184320, content_type: "application/pdf", sha256_hash: "d6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7", version: 3, status: "approved", uploaded_by: "u-1", uploaded_by_name: "Sarah Chen", approved_by: "u-1", expires_at: "2025-06-01T00:00:00Z", tags: ["policy", "incident-response"], created_at: "2024-06-01T11:00:00Z" },
  { id: "e-5", title: "Q3 2024 Access Review", description: "Quarterly user access review for all production systems and cloud accounts.", file_name: "access-review-q3-2024.pdf", file_size: 102400, content_type: "application/pdf", sha256_hash: "e7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8", version: 1, status: "approved", uploaded_by: "u-3", uploaded_by_name: "Maria Garcia", approved_by: "u-1", expires_at: "2025-07-01T00:00:00Z", tags: ["review", "access-control"], created_at: "2024-10-01T16:00:00Z" },
  { id: "e-6", title: "Encryption Configuration Verification", description: "Evidence of encryption at rest and in transit configuration for all data stores.", file_name: "encryption-config-audit.pdf", file_size: 76800, content_type: "application/pdf", sha256_hash: "f8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9", version: 1, status: "pending", uploaded_by: "u-2", uploaded_by_name: "James Wilson", approved_by: null, expires_at: null, tags: ["encryption", "infrastructure"], created_at: "2024-11-10T10:00:00Z" },
  { id: "e-7", title: "Vendor Risk Assessment — AWS", description: "Annual vendor risk assessment for Amazon Web Services as primary cloud provider.", file_name: "vendor-risk-aws-2024.pdf", file_size: 153600, content_type: "application/pdf", sha256_hash: "a9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0", version: 1, status: "pending", uploaded_by: "u-1", uploaded_by_name: "Sarah Chen", approved_by: null, expires_at: null, tags: ["vendor", "risk-assessment"], created_at: "2024-11-12T09:00:00Z" },
  { id: "e-8", title: "Change Management Log — October 2024", description: "Log of all production changes with approval records and rollback plans.", file_name: "change-log-oct-2024.csv", file_size: 35840, content_type: "text/csv", sha256_hash: "b0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1", version: 1, status: "approved", uploaded_by: "u-2", uploaded_by_name: "James Wilson", approved_by: "u-1", expires_at: "2025-04-30T00:00:00Z", tags: ["change-management"], created_at: "2024-11-01T15:00:00Z" },
  { id: "e-9", title: "Security Awareness Training Completion", description: "Records of annual security awareness training completion for all employees.", file_name: "security-training-2024.xlsx", file_size: 40960, content_type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", sha256_hash: "c1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2", version: 1, status: "expired", uploaded_by: "u-1", uploaded_by_name: "Sarah Chen", approved_by: "u-1", expires_at: "2024-10-31T00:00:00Z", tags: ["training", "awareness"], created_at: "2024-04-15T10:00:00Z" },
  { id: "e-10", title: "Vulnerability Scan Report — November 2024", description: "Trivy scan of production container images and dependencies.", file_name: "trivy-scan-nov-2024.json", file_size: 819200, content_type: "application/json", sha256_hash: "d2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3", version: 1, status: "rejected", uploaded_by: "u-2", uploaded_by_name: "James Wilson", approved_by: null, expires_at: null, tags: ["scan", "vulnerability"], created_at: "2024-11-15T08:00:00Z" },
];

// --- Policies ---

const policies: Policy[] = [
  { id: "p-1", title: "Information Security Policy", content: "This policy establishes the framework for managing information security across the organization...", category: "Security", version: 3, status: "published", owner_name: "Sarah Chen", effective_date: "2024-01-15", review_date: "2025-01-15", created_at: "2023-01-15T09:00:00Z" },
  { id: "p-2", title: "Access Control Policy", content: "This policy defines the requirements for controlling access to information systems and data...", category: "Access Control", version: 2, status: "published", owner_name: "Maria Garcia", effective_date: "2024-03-01", review_date: "2025-03-01", created_at: "2023-03-01T10:00:00Z" },
  { id: "p-3", title: "Incident Response Policy", content: "This policy establishes procedures for detecting, responding to, and recovering from security incidents...", category: "Operations", version: 1, status: "published", owner_name: "James Wilson", effective_date: "2024-06-01", review_date: "2025-06-01", created_at: "2024-06-01T08:00:00Z" },
  { id: "p-4", title: "Data Classification Policy", content: "This policy defines the classification levels for organizational data and the handling requirements for each level...", category: "Data Protection", version: 1, status: "draft", owner_name: "Sarah Chen", effective_date: null, review_date: null, created_at: "2024-11-01T11:00:00Z" },
  { id: "p-5", title: "Acceptable Use Policy", content: "This policy sets forth the acceptable use of organization information systems and technology resources...", category: "General", version: 2, status: "published", owner_name: "Sarah Chen", effective_date: "2024-02-01", review_date: "2025-02-01", created_at: "2023-02-01T09:00:00Z" },
];

// --- Vendors ---

const vendors: Vendor[] = [
  { id: "v-1", name: "Amazon Web Services", description: "Primary cloud infrastructure provider for production workloads.", category: "Cloud Infrastructure", risk_level: "medium", status: "active", contact_name: "AWS Enterprise Support", contact_email: null, contract_end: "2025-12-31", last_assessment_at: "2024-10-15T00:00:00Z", created_at: "2024-01-01T00:00:00Z" },
  { id: "v-2", name: "Microsoft Azure", description: "Secondary cloud provider and Microsoft 365 services.", category: "Cloud Infrastructure", risk_level: "medium", status: "active", contact_name: "Azure Support", contact_email: null, contract_end: "2025-06-30", last_assessment_at: "2024-09-01T00:00:00Z", created_at: "2024-01-01T00:00:00Z" },
  { id: "v-3", name: "Datadog", description: "Application performance monitoring and observability platform.", category: "Monitoring", risk_level: "low", status: "active", contact_name: "Account Manager", contact_email: null, contract_end: "2025-03-31", last_assessment_at: "2024-08-15T00:00:00Z", created_at: "2024-02-01T00:00:00Z" },
  { id: "v-4", name: "Okta", description: "Identity provider for SSO and workforce identity management.", category: "Identity & Access", risk_level: "high", status: "active", contact_name: "Okta Support", contact_email: null, contract_end: "2025-09-30", last_assessment_at: "2024-07-01T00:00:00Z", created_at: "2024-01-15T00:00:00Z" },
  { id: "v-5", name: "PagerDuty", description: "Incident management and on-call scheduling.", category: "Operations", risk_level: "low", status: "active", contact_name: null, contact_email: null, contract_end: "2025-04-30", last_assessment_at: "2024-06-01T00:00:00Z", created_at: "2024-03-01T00:00:00Z" },
  { id: "v-6", name: "Acme Consulting", description: "Former IT consulting partner. Contract terminated.", category: "Professional Services", risk_level: "critical", status: "terminated", contact_name: null, contact_email: null, contract_end: "2024-06-30", last_assessment_at: "2024-06-15T00:00:00Z", created_at: "2023-06-01T00:00:00Z" },
];

// --- Helpers ---

export function getFrameworks(): Framework[] {
  return frameworks;
}

export function getFramework(id: string): Framework | undefined {
  return frameworks.find((f) => f.id === id);
}

export function getFrameworkVersions(frameworkId: string): FrameworkVersion[] {
  return frameworkVersions.filter((fv) => fv.framework_id === frameworkId);
}

export function getControls(frameworkVersionId: string): ControlWithStatus[] {
  if (frameworkVersionId === "fv-soc2-2017") return soc2Controls;
  if (frameworkVersionId === "fv-iso27001-2022") return iso27001Controls;
  return [];
}

export function getAllControls(): ControlWithStatus[] {
  return [...soc2Controls, ...iso27001Controls];
}

export function getControlCategories(controls: ControlWithStatus[]): string[] {
  return [...new Set(controls.map((c) => c.category))];
}

export function getFrameworkComplianceScore(frameworkVersionId: string): number {
  const controls = getControls(frameworkVersionId);
  const applicable = controls.filter(
    (c) => c.tenant_status?.status !== "not_applicable"
  );
  if (applicable.length === 0) return 0;
  const implemented = applicable.filter(
    (c) => c.tenant_status?.status === "implemented"
  );
  return Math.round((implemented.length / applicable.length) * 100);
}

export function getRisks(): Risk[] {
  return risks;
}

export function getRisk(id: string): Risk | undefined {
  return risks.find((r) => r.id === id);
}

export function getEvidence(): Evidence[] {
  return evidence;
}

export function getPolicies(): Policy[] {
  return policies;
}

export function getVendors(): Vendor[] {
  return vendors;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}
