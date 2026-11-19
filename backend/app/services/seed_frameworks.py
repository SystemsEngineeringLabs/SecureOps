"""
Seed data for compliance frameworks: SOC 2 Type II and ISO 27001:2022.

Run via: python -m app.services.seed_frameworks
Requires an active database connection. Idempotent — skips if frameworks already exist.
"""

import asyncio
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import async_session_factory
from app.models.control import Control, ControlMapping
from app.models.enums import ControlMappingType
from app.models.framework import Framework, FrameworkVersion

SOC2_FRAMEWORK = {
    "key": "soc2",
    "name": "SOC 2 Type II",
    "description": "Service Organization Control 2 — Trust Services Criteria for security, availability, processing integrity, confidentiality, and privacy.",
    "organization": "AICPA",
}

SOC2_VERSION = {
    "version": "2017",
    "effective_date": date(2017, 12, 15),
    "is_current": True,
    "metadata": {"revision": "2017 Trust Services Criteria"},
}

SOC2_CONTROLS = [
    # CC1 — Control Environment
    {"code": "CC1.1", "title": "COSO Principle 1: Demonstrates Commitment to Integrity and Ethical Values", "category": "CC1 - Control Environment", "sort_order": 1},
    {"code": "CC1.2", "title": "COSO Principle 2: Board of Directors Demonstrates Independence from Management", "category": "CC1 - Control Environment", "sort_order": 2},
    {"code": "CC1.3", "title": "COSO Principle 3: Management Establishes Structures, Reporting Lines, and Authorities", "category": "CC1 - Control Environment", "sort_order": 3},
    {"code": "CC1.4", "title": "COSO Principle 4: Demonstrates Commitment to Competence", "category": "CC1 - Control Environment", "sort_order": 4},
    {"code": "CC1.5", "title": "COSO Principle 5: Enforces Accountability", "category": "CC1 - Control Environment", "sort_order": 5},
    # CC2 — Communication and Information
    {"code": "CC2.1", "title": "COSO Principle 13: Obtains or Generates Relevant, Quality Information", "category": "CC2 - Communication and Information", "sort_order": 10},
    {"code": "CC2.2", "title": "COSO Principle 14: Internally Communicates Information", "category": "CC2 - Communication and Information", "sort_order": 11},
    {"code": "CC2.3", "title": "COSO Principle 15: Externally Communicates Information", "category": "CC2 - Communication and Information", "sort_order": 12},
    # CC3 — Risk Assessment
    {"code": "CC3.1", "title": "COSO Principle 6: Specifies Suitable Objectives", "category": "CC3 - Risk Assessment", "sort_order": 20},
    {"code": "CC3.2", "title": "COSO Principle 7: Identifies and Analyzes Risk", "category": "CC3 - Risk Assessment", "sort_order": 21},
    {"code": "CC3.3", "title": "COSO Principle 8: Assesses Fraud Risk", "category": "CC3 - Risk Assessment", "sort_order": 22},
    {"code": "CC3.4", "title": "COSO Principle 9: Identifies and Analyzes Significant Change", "category": "CC3 - Risk Assessment", "sort_order": 23},
    # CC4 — Monitoring Activities
    {"code": "CC4.1", "title": "COSO Principle 16: Selects, Develops, and Performs Ongoing and/or Separate Evaluations", "category": "CC4 - Monitoring Activities", "sort_order": 30},
    {"code": "CC4.2", "title": "COSO Principle 17: Evaluates and Communicates Deficiencies", "category": "CC4 - Monitoring Activities", "sort_order": 31},
    # CC5 — Control Activities
    {"code": "CC5.1", "title": "COSO Principle 10: Selects and Develops Control Activities", "category": "CC5 - Control Activities", "sort_order": 40},
    {"code": "CC5.2", "title": "COSO Principle 11: Selects and Develops General Controls over Technology", "category": "CC5 - Control Activities", "sort_order": 41},
    {"code": "CC5.3", "title": "COSO Principle 12: Deploys through Policies and Procedures", "category": "CC5 - Control Activities", "sort_order": 42},
    # CC6 — Logical and Physical Access Controls
    {"code": "CC6.1", "title": "Logical Access Security Software, Infrastructure, and Architectures", "category": "CC6 - Logical and Physical Access", "sort_order": 50},
    {"code": "CC6.2", "title": "Prior to Issuing System Credentials and Granting System Access", "category": "CC6 - Logical and Physical Access", "sort_order": 51},
    {"code": "CC6.3", "title": "Role-Based Access and Least Privilege", "category": "CC6 - Logical and Physical Access", "sort_order": 52},
    {"code": "CC6.4", "title": "Physical Access to Facilities and Protected Information Assets", "category": "CC6 - Logical and Physical Access", "sort_order": 53},
    {"code": "CC6.5", "title": "Disposition of Physical and Logical Assets", "category": "CC6 - Logical and Physical Access", "sort_order": 54},
    {"code": "CC6.6", "title": "Logical Access Security Measures against Threats from Sources Outside Its System Boundaries", "category": "CC6 - Logical and Physical Access", "sort_order": 55},
    {"code": "CC6.7", "title": "Restriction and Management of Transmission, Movement, and Removal of Information", "category": "CC6 - Logical and Physical Access", "sort_order": 56},
    {"code": "CC6.8", "title": "Controls to Prevent or Detect and Act Upon Introduction of Unauthorized or Malicious Software", "category": "CC6 - Logical and Physical Access", "sort_order": 57},
    # CC7 — System Operations
    {"code": "CC7.1", "title": "Detection and Monitoring Procedures", "category": "CC7 - System Operations", "sort_order": 60},
    {"code": "CC7.2", "title": "Monitoring of System Components for Anomalies", "category": "CC7 - System Operations", "sort_order": 61},
    {"code": "CC7.3", "title": "Evaluation of Identified Security Events", "category": "CC7 - System Operations", "sort_order": 62},
    {"code": "CC7.4", "title": "Response to Identified Security Incidents", "category": "CC7 - System Operations", "sort_order": 63},
    {"code": "CC7.5", "title": "Identification of and Recovery from Identified Security Incidents", "category": "CC7 - System Operations", "sort_order": 64},
    # CC8 — Change Management
    {"code": "CC8.1", "title": "Changes to Infrastructure, Data, Software, and Procedures", "category": "CC8 - Change Management", "sort_order": 70},
    # CC9 — Risk Mitigation
    {"code": "CC9.1", "title": "Identification and Management of Risks from Business Partners and Vendors", "category": "CC9 - Risk Mitigation", "sort_order": 80},
    {"code": "CC9.2", "title": "Risk Assessment and Insurance", "category": "CC9 - Risk Mitigation", "sort_order": 81},
    # Availability
    {"code": "A1.1", "title": "Availability Commitments and System Requirements", "category": "Availability", "sort_order": 90},
    {"code": "A1.2", "title": "Environmental Protections, Software, Data Backup and Recovery", "category": "Availability", "sort_order": 91},
    {"code": "A1.3", "title": "Recovery Plan Testing", "category": "Availability", "sort_order": 92},
    # Confidentiality
    {"code": "C1.1", "title": "Confidential Information Identification and Maintenance Procedures", "category": "Confidentiality", "sort_order": 100},
    {"code": "C1.2", "title": "Disposal of Confidential Information", "category": "Confidentiality", "sort_order": 101},
    # Processing Integrity
    {"code": "PI1.1", "title": "Processing Integrity Commitments and System Requirements", "category": "Processing Integrity", "sort_order": 110},
    {"code": "PI1.2", "title": "System Inputs are Complete, Accurate, and Timely", "category": "Processing Integrity", "sort_order": 111},
    {"code": "PI1.3", "title": "System Processing is Complete, Accurate, Timely, and Authorized", "category": "Processing Integrity", "sort_order": 112},
    {"code": "PI1.4", "title": "System Outputs are Complete, Accurate, and Timely", "category": "Processing Integrity", "sort_order": 113},
    {"code": "PI1.5", "title": "Storage of Inputs, Items in Processing, and Outputs", "category": "Processing Integrity", "sort_order": 114},
    # Privacy (optional but common)
    {"code": "P1.1", "title": "Privacy Commitments and System Requirements", "category": "Privacy", "sort_order": 120},
    {"code": "P1.2", "title": "Consistent Privacy Practices with Commitments", "category": "Privacy", "sort_order": 121},
]

ISO27001_FRAMEWORK = {
    "key": "iso27001",
    "name": "ISO/IEC 27001:2022",
    "description": "Information security, cybersecurity and privacy protection — Information security management systems — Requirements. Annex A reference controls.",
    "organization": "ISO/IEC",
}

ISO27001_VERSION = {
    "version": "2022",
    "effective_date": date(2022, 10, 25),
    "is_current": True,
    "metadata": {"revision": "ISO/IEC 27001:2022 Annex A"},
}

ISO27001_CONTROLS = [
    # A.5 — Organizational Controls
    {"code": "A.5.1", "title": "Policies for information security", "category": "A.5 - Organizational Controls", "sort_order": 1},
    {"code": "A.5.2", "title": "Information security roles and responsibilities", "category": "A.5 - Organizational Controls", "sort_order": 2},
    {"code": "A.5.3", "title": "Segregation of duties", "category": "A.5 - Organizational Controls", "sort_order": 3},
    {"code": "A.5.4", "title": "Management responsibilities", "category": "A.5 - Organizational Controls", "sort_order": 4},
    {"code": "A.5.5", "title": "Contact with authorities", "category": "A.5 - Organizational Controls", "sort_order": 5},
    {"code": "A.5.6", "title": "Contact with special interest groups", "category": "A.5 - Organizational Controls", "sort_order": 6},
    {"code": "A.5.7", "title": "Threat intelligence", "category": "A.5 - Organizational Controls", "sort_order": 7},
    {"code": "A.5.8", "title": "Information security in project management", "category": "A.5 - Organizational Controls", "sort_order": 8},
    {"code": "A.5.9", "title": "Inventory of information and other associated assets", "category": "A.5 - Organizational Controls", "sort_order": 9},
    {"code": "A.5.10", "title": "Acceptable use of information and other associated assets", "category": "A.5 - Organizational Controls", "sort_order": 10},
    {"code": "A.5.11", "title": "Return of assets", "category": "A.5 - Organizational Controls", "sort_order": 11},
    {"code": "A.5.12", "title": "Classification of information", "category": "A.5 - Organizational Controls", "sort_order": 12},
    {"code": "A.5.13", "title": "Labelling of information", "category": "A.5 - Organizational Controls", "sort_order": 13},
    {"code": "A.5.14", "title": "Information transfer", "category": "A.5 - Organizational Controls", "sort_order": 14},
    {"code": "A.5.15", "title": "Access control", "category": "A.5 - Organizational Controls", "sort_order": 15},
    {"code": "A.5.16", "title": "Identity management", "category": "A.5 - Organizational Controls", "sort_order": 16},
    {"code": "A.5.17", "title": "Authentication information", "category": "A.5 - Organizational Controls", "sort_order": 17},
    {"code": "A.5.18", "title": "Access rights", "category": "A.5 - Organizational Controls", "sort_order": 18},
    {"code": "A.5.19", "title": "Information security in supplier relationships", "category": "A.5 - Organizational Controls", "sort_order": 19},
    {"code": "A.5.20", "title": "Addressing information security within supplier agreements", "category": "A.5 - Organizational Controls", "sort_order": 20},
    {"code": "A.5.21", "title": "Managing information security in the ICT supply chain", "category": "A.5 - Organizational Controls", "sort_order": 21},
    {"code": "A.5.22", "title": "Monitoring, review and change management of supplier services", "category": "A.5 - Organizational Controls", "sort_order": 22},
    {"code": "A.5.23", "title": "Information security for use of cloud services", "category": "A.5 - Organizational Controls", "sort_order": 23},
    {"code": "A.5.24", "title": "Information security incident management planning and preparation", "category": "A.5 - Organizational Controls", "sort_order": 24},
    {"code": "A.5.25", "title": "Assessment and decision on information security events", "category": "A.5 - Organizational Controls", "sort_order": 25},
    {"code": "A.5.26", "title": "Response to information security incidents", "category": "A.5 - Organizational Controls", "sort_order": 26},
    {"code": "A.5.27", "title": "Learning from information security incidents", "category": "A.5 - Organizational Controls", "sort_order": 27},
    {"code": "A.5.28", "title": "Collection of evidence", "category": "A.5 - Organizational Controls", "sort_order": 28},
    {"code": "A.5.29", "title": "Information security during disruption", "category": "A.5 - Organizational Controls", "sort_order": 29},
    {"code": "A.5.30", "title": "ICT readiness for business continuity", "category": "A.5 - Organizational Controls", "sort_order": 30},
    {"code": "A.5.31", "title": "Legal, statutory, regulatory and contractual requirements", "category": "A.5 - Organizational Controls", "sort_order": 31},
    {"code": "A.5.32", "title": "Intellectual property rights", "category": "A.5 - Organizational Controls", "sort_order": 32},
    {"code": "A.5.33", "title": "Protection of records", "category": "A.5 - Organizational Controls", "sort_order": 33},
    {"code": "A.5.34", "title": "Privacy and protection of PII", "category": "A.5 - Organizational Controls", "sort_order": 34},
    {"code": "A.5.35", "title": "Independent review of information security", "category": "A.5 - Organizational Controls", "sort_order": 35},
    {"code": "A.5.36", "title": "Compliance with policies, rules and standards for information security", "category": "A.5 - Organizational Controls", "sort_order": 36},
    {"code": "A.5.37", "title": "Documented operating procedures", "category": "A.5 - Organizational Controls", "sort_order": 37},
    # A.6 — People Controls
    {"code": "A.6.1", "title": "Screening", "category": "A.6 - People Controls", "sort_order": 40},
    {"code": "A.6.2", "title": "Terms and conditions of employment", "category": "A.6 - People Controls", "sort_order": 41},
    {"code": "A.6.3", "title": "Information security awareness, education and training", "category": "A.6 - People Controls", "sort_order": 42},
    {"code": "A.6.4", "title": "Disciplinary process", "category": "A.6 - People Controls", "sort_order": 43},
    {"code": "A.6.5", "title": "Responsibilities after termination or change of employment", "category": "A.6 - People Controls", "sort_order": 44},
    {"code": "A.6.6", "title": "Confidentiality or non-disclosure agreements", "category": "A.6 - People Controls", "sort_order": 45},
    {"code": "A.6.7", "title": "Remote working", "category": "A.6 - People Controls", "sort_order": 46},
    {"code": "A.6.8", "title": "Information security event reporting", "category": "A.6 - People Controls", "sort_order": 47},
    # A.7 — Physical Controls
    {"code": "A.7.1", "title": "Physical security perimeters", "category": "A.7 - Physical Controls", "sort_order": 50},
    {"code": "A.7.2", "title": "Physical entry", "category": "A.7 - Physical Controls", "sort_order": 51},
    {"code": "A.7.3", "title": "Securing offices, rooms and facilities", "category": "A.7 - Physical Controls", "sort_order": 52},
    {"code": "A.7.4", "title": "Physical security monitoring", "category": "A.7 - Physical Controls", "sort_order": 53},
    {"code": "A.7.5", "title": "Protecting against physical and environmental threats", "category": "A.7 - Physical Controls", "sort_order": 54},
    {"code": "A.7.6", "title": "Working in secure areas", "category": "A.7 - Physical Controls", "sort_order": 55},
    {"code": "A.7.7", "title": "Clear desk and clear screen", "category": "A.7 - Physical Controls", "sort_order": 56},
    {"code": "A.7.8", "title": "Equipment siting and protection", "category": "A.7 - Physical Controls", "sort_order": 57},
    {"code": "A.7.9", "title": "Security of assets off-premises", "category": "A.7 - Physical Controls", "sort_order": 58},
    {"code": "A.7.10", "title": "Storage media", "category": "A.7 - Physical Controls", "sort_order": 59},
    {"code": "A.7.11", "title": "Supporting utilities", "category": "A.7 - Physical Controls", "sort_order": 60},
    {"code": "A.7.12", "title": "Cabling security", "category": "A.7 - Physical Controls", "sort_order": 61},
    {"code": "A.7.13", "title": "Equipment maintenance", "category": "A.7 - Physical Controls", "sort_order": 62},
    {"code": "A.7.14", "title": "Secure disposal or re-use of equipment", "category": "A.7 - Physical Controls", "sort_order": 63},
    # A.8 — Technological Controls
    {"code": "A.8.1", "title": "User endpoint devices", "category": "A.8 - Technological Controls", "sort_order": 70},
    {"code": "A.8.2", "title": "Privileged access rights", "category": "A.8 - Technological Controls", "sort_order": 71},
    {"code": "A.8.3", "title": "Information access restriction", "category": "A.8 - Technological Controls", "sort_order": 72},
    {"code": "A.8.4", "title": "Access to source code", "category": "A.8 - Technological Controls", "sort_order": 73},
    {"code": "A.8.5", "title": "Secure authentication", "category": "A.8 - Technological Controls", "sort_order": 74},
    {"code": "A.8.6", "title": "Capacity management", "category": "A.8 - Technological Controls", "sort_order": 75},
    {"code": "A.8.7", "title": "Protection against malware", "category": "A.8 - Technological Controls", "sort_order": 76},
    {"code": "A.8.8", "title": "Management of technical vulnerabilities", "category": "A.8 - Technological Controls", "sort_order": 77},
    {"code": "A.8.9", "title": "Configuration management", "category": "A.8 - Technological Controls", "sort_order": 78},
    {"code": "A.8.10", "title": "Information deletion", "category": "A.8 - Technological Controls", "sort_order": 79},
    {"code": "A.8.11", "title": "Data masking", "category": "A.8 - Technological Controls", "sort_order": 80},
    {"code": "A.8.12", "title": "Data leakage prevention", "category": "A.8 - Technological Controls", "sort_order": 81},
    {"code": "A.8.13", "title": "Information backup", "category": "A.8 - Technological Controls", "sort_order": 82},
    {"code": "A.8.14", "title": "Redundancy of information processing facilities", "category": "A.8 - Technological Controls", "sort_order": 83},
    {"code": "A.8.15", "title": "Logging", "category": "A.8 - Technological Controls", "sort_order": 84},
    {"code": "A.8.16", "title": "Monitoring activities", "category": "A.8 - Technological Controls", "sort_order": 85},
    {"code": "A.8.17", "title": "Clock synchronization", "category": "A.8 - Technological Controls", "sort_order": 86},
    {"code": "A.8.18", "title": "Use of privileged utility programs", "category": "A.8 - Technological Controls", "sort_order": 87},
    {"code": "A.8.19", "title": "Installation of software on operational systems", "category": "A.8 - Technological Controls", "sort_order": 88},
    {"code": "A.8.20", "title": "Networks security", "category": "A.8 - Technological Controls", "sort_order": 89},
    {"code": "A.8.21", "title": "Security of network services", "category": "A.8 - Technological Controls", "sort_order": 90},
    {"code": "A.8.22", "title": "Segregation of networks", "category": "A.8 - Technological Controls", "sort_order": 91},
    {"code": "A.8.23", "title": "Web filtering", "category": "A.8 - Technological Controls", "sort_order": 92},
    {"code": "A.8.24", "title": "Use of cryptography", "category": "A.8 - Technological Controls", "sort_order": 93},
    {"code": "A.8.25", "title": "Secure development life cycle", "category": "A.8 - Technological Controls", "sort_order": 94},
    {"code": "A.8.26", "title": "Application security requirements", "category": "A.8 - Technological Controls", "sort_order": 95},
    {"code": "A.8.27", "title": "Secure system architecture and engineering principles", "category": "A.8 - Technological Controls", "sort_order": 96},
    {"code": "A.8.28", "title": "Secure coding", "category": "A.8 - Technological Controls", "sort_order": 97},
    {"code": "A.8.29", "title": "Security testing in development and acceptance", "category": "A.8 - Technological Controls", "sort_order": 98},
    {"code": "A.8.30", "title": "Outsourced development", "category": "A.8 - Technological Controls", "sort_order": 99},
    {"code": "A.8.31", "title": "Separation of development, test and production environments", "category": "A.8 - Technological Controls", "sort_order": 100},
    {"code": "A.8.32", "title": "Change management", "category": "A.8 - Technological Controls", "sort_order": 101},
    {"code": "A.8.33", "title": "Test information", "category": "A.8 - Technological Controls", "sort_order": 102},
    {"code": "A.8.34", "title": "Protection of information systems during audit testing", "category": "A.8 - Technological Controls", "sort_order": 103},
]

# Cross-framework mappings: SOC 2 code -> ISO 27001 code, with mapping type
CROSS_MAPPINGS = [
    ("CC1.1", "A.5.1", ControlMappingType.PARTIAL, "Both address governance and policy framework"),
    ("CC1.3", "A.5.2", ControlMappingType.EQUIVALENT, "Both define security roles and responsibilities"),
    ("CC1.4", "A.6.3", ControlMappingType.PARTIAL, "Competence/training alignment"),
    ("CC2.1", "A.5.12", ControlMappingType.PARTIAL, "Information quality and classification"),
    ("CC2.2", "A.5.14", ControlMappingType.PARTIAL, "Internal communication and information transfer"),
    ("CC3.2", "A.5.7", ControlMappingType.PARTIAL, "Risk identification and threat intelligence"),
    ("CC4.1", "A.8.16", ControlMappingType.EQUIVALENT, "Monitoring activities"),
    ("CC4.2", "A.5.35", ControlMappingType.PARTIAL, "Independent review and deficiency evaluation"),
    ("CC5.3", "A.5.37", ControlMappingType.EQUIVALENT, "Policies/procedures and documented operating procedures"),
    ("CC6.1", "A.5.15", ControlMappingType.EQUIVALENT, "Logical access controls"),
    ("CC6.2", "A.5.16", ControlMappingType.EQUIVALENT, "Identity management and credential issuance"),
    ("CC6.3", "A.8.2", ControlMappingType.EQUIVALENT, "RBAC/least privilege and privileged access rights"),
    ("CC6.4", "A.7.1", ControlMappingType.EQUIVALENT, "Physical access and physical security perimeters"),
    ("CC6.5", "A.7.14", ControlMappingType.EQUIVALENT, "Asset disposition and secure disposal"),
    ("CC6.6", "A.8.20", ControlMappingType.PARTIAL, "External threat protection and network security"),
    ("CC6.7", "A.5.14", ControlMappingType.PARTIAL, "Information transfer restrictions"),
    ("CC6.8", "A.8.7", ControlMappingType.EQUIVALENT, "Malware protection"),
    ("CC7.1", "A.8.15", ControlMappingType.EQUIVALENT, "Detection/monitoring and logging"),
    ("CC7.2", "A.8.16", ControlMappingType.EQUIVALENT, "Anomaly monitoring"),
    ("CC7.3", "A.5.25", ControlMappingType.EQUIVALENT, "Security event evaluation and assessment"),
    ("CC7.4", "A.5.26", ControlMappingType.EQUIVALENT, "Incident response"),
    ("CC7.5", "A.5.29", ControlMappingType.PARTIAL, "Recovery and business continuity"),
    ("CC8.1", "A.8.32", ControlMappingType.EQUIVALENT, "Change management"),
    ("CC9.1", "A.5.19", ControlMappingType.EQUIVALENT, "Vendor/supplier risk management"),
    ("A1.2", "A.8.13", ControlMappingType.EQUIVALENT, "Backup and recovery"),
    ("A1.3", "A.5.30", ControlMappingType.PARTIAL, "Recovery testing and ICT readiness"),
    ("C1.1", "A.5.12", ControlMappingType.EQUIVALENT, "Confidential information and classification"),
    ("C1.2", "A.8.10", ControlMappingType.EQUIVALENT, "Confidential data disposal and deletion"),
    ("P1.1", "A.5.34", ControlMappingType.EQUIVALENT, "Privacy commitments and PII protection"),
]


async def seed_frameworks(db: AsyncSession) -> dict[str, int]:
    results: dict[str, int] = {}

    existing = await db.execute(select(Framework.key))
    existing_keys = {row[0] for row in existing.all()}

    soc2_control_map: dict[str, uuid.UUID] = {}
    iso_control_map: dict[str, uuid.UUID] = {}

    if "soc2" not in existing_keys:
        framework = Framework(**SOC2_FRAMEWORK)
        db.add(framework)
        await db.flush()

        version = FrameworkVersion(framework_id=framework.id, **SOC2_VERSION)
        db.add(version)
        await db.flush()

        for c in SOC2_CONTROLS:
            control = Control(framework_version_id=version.id, **c)
            db.add(control)
            await db.flush()
            soc2_control_map[c["code"]] = control.id

        results["soc2_controls"] = len(SOC2_CONTROLS)
    else:
        stmt = (
            select(Control.code, Control.id)
            .join(FrameworkVersion, Control.framework_version_id == FrameworkVersion.id)
            .join(Framework, FrameworkVersion.framework_id == Framework.id)
            .where(Framework.key == "soc2")
        )
        rows = await db.execute(stmt)
        soc2_control_map = {row[0]: row[1] for row in rows.all()}
        results["soc2_controls"] = 0

    if "iso27001" not in existing_keys:
        framework = Framework(**ISO27001_FRAMEWORK)
        db.add(framework)
        await db.flush()

        version = FrameworkVersion(framework_id=framework.id, **ISO27001_VERSION)
        db.add(version)
        await db.flush()

        for c in ISO27001_CONTROLS:
            control = Control(framework_version_id=version.id, **c)
            db.add(control)
            await db.flush()
            iso_control_map[c["code"]] = control.id

        results["iso27001_controls"] = len(ISO27001_CONTROLS)
    else:
        stmt = (
            select(Control.code, Control.id)
            .join(FrameworkVersion, Control.framework_version_id == FrameworkVersion.id)
            .join(Framework, FrameworkVersion.framework_id == Framework.id)
            .where(Framework.key == "iso27001")
        )
        rows = await db.execute(stmt)
        iso_control_map = {row[0]: row[1] for row in rows.all()}
        results["iso27001_controls"] = 0

    mapping_count = 0
    if soc2_control_map and iso_control_map:
        for soc2_code, iso_code, mapping_type, notes in CROSS_MAPPINGS:
            src_id = soc2_control_map.get(soc2_code)
            tgt_id = iso_control_map.get(iso_code)
            if src_id and tgt_id:
                existing_mapping = await db.execute(
                    select(ControlMapping).where(
                        ControlMapping.source_control_id == src_id,
                        ControlMapping.target_control_id == tgt_id,
                    )
                )
                if existing_mapping.scalar_one_or_none() is None:
                    mapping = ControlMapping(
                        source_control_id=src_id,
                        target_control_id=tgt_id,
                        mapping_type=mapping_type,
                        notes=notes,
                    )
                    db.add(mapping)
                    mapping_count += 1

        if mapping_count:
            await db.flush()

    results["cross_mappings"] = mapping_count
    await db.commit()
    return results


async def main() -> None:
    async with async_session_factory() as session:
        results = await seed_frameworks(session)
        print(f"Seed complete: {results}")


if __name__ == "__main__":
    asyncio.run(main())
