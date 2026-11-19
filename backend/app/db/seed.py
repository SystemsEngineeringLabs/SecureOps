"""Idempotent seeder for compliance frameworks, controls, and cross-framework mappings."""

import asyncio
import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.control import Control, ControlMapping
from app.models.enums import ControlMappingType
from app.models.framework import Framework, FrameworkVersion

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SOC 2 Type II — 2017 Trust Services Criteria
# ---------------------------------------------------------------------------

SOC2_CONTROLS: list[dict] = [
    # CC1 — Control Environment
    {"code": "CC1.1", "title": "Commitment to integrity and ethical values", "category": "CC1 — Control Environment", "sort_order": 1},
    {"code": "CC1.2", "title": "Board independence and oversight of internal controls", "category": "CC1 — Control Environment", "sort_order": 2},
    {"code": "CC1.3", "title": "Management establishes structures and reporting lines", "category": "CC1 — Control Environment", "sort_order": 3},
    {"code": "CC1.4", "title": "Commitment to attract and retain competent individuals", "category": "CC1 — Control Environment", "sort_order": 4},
    {"code": "CC1.5", "title": "Accountability for internal control responsibilities", "category": "CC1 — Control Environment", "sort_order": 5},
    # CC2 — Communication and Information
    {"code": "CC2.1", "title": "Information quality to support internal controls", "category": "CC2 — Communication and Information", "sort_order": 6},
    {"code": "CC2.2", "title": "Internal communication of objectives and responsibilities", "category": "CC2 — Communication and Information", "sort_order": 7},
    {"code": "CC2.3", "title": "External communication regarding internal control matters", "category": "CC2 — Communication and Information", "sort_order": 8},
    # CC3 — Risk Assessment
    {"code": "CC3.1", "title": "Specification of suitable objectives for risk assessment", "category": "CC3 — Risk Assessment", "sort_order": 9},
    {"code": "CC3.2", "title": "Identification and analysis of risks to objectives", "category": "CC3 — Risk Assessment", "sort_order": 10},
    {"code": "CC3.3", "title": "Consideration of potential for fraud", "category": "CC3 — Risk Assessment", "sort_order": 11},
    {"code": "CC3.4", "title": "Identification and assessment of significant changes", "category": "CC3 — Risk Assessment", "sort_order": 12},
    # CC4 — Monitoring Activities
    {"code": "CC4.1", "title": "Ongoing and separate evaluations of controls", "category": "CC4 — Monitoring Activities", "sort_order": 13},
    {"code": "CC4.2", "title": "Communication and remediation of control deficiencies", "category": "CC4 — Monitoring Activities", "sort_order": 14},
    # CC5 — Control Activities
    {"code": "CC5.1", "title": "Selection and development of control activities for risk mitigation", "category": "CC5 — Control Activities", "sort_order": 15},
    {"code": "CC5.2", "title": "Selection and development of technology general controls", "category": "CC5 — Control Activities", "sort_order": 16},
    {"code": "CC5.3", "title": "Deployment of control activities through policies and procedures", "category": "CC5 — Control Activities", "sort_order": 17},
    # CC6 — Logical and Physical Access Controls
    {"code": "CC6.1", "title": "Logical access security for protected information assets", "category": "CC6 — Logical and Physical Access Controls", "sort_order": 18},
    {"code": "CC6.2", "title": "User registration and authorization for system access", "category": "CC6 — Logical and Physical Access Controls", "sort_order": 19},
    {"code": "CC6.3", "title": "Role-based access and least privilege enforcement", "category": "CC6 — Logical and Physical Access Controls", "sort_order": 20},
    {"code": "CC6.4", "title": "Restriction of physical access to facilities and assets", "category": "CC6 — Logical and Physical Access Controls", "sort_order": 21},
    {"code": "CC6.5", "title": "Disposal of protected information assets", "category": "CC6 — Logical and Physical Access Controls", "sort_order": 22},
    {"code": "CC6.6", "title": "Encryption of data in transit and at rest", "category": "CC6 — Logical and Physical Access Controls", "sort_order": 23},
    {"code": "CC6.7", "title": "Protection against threats from outside system boundaries", "category": "CC6 — Logical and Physical Access Controls", "sort_order": 24},
    {"code": "CC6.8", "title": "Prevention and detection of unauthorized software", "category": "CC6 — Logical and Physical Access Controls", "sort_order": 25},
    # CC7 — System Operations
    {"code": "CC7.1", "title": "Detection of anomalies and security events", "category": "CC7 — System Operations", "sort_order": 26},
    {"code": "CC7.2", "title": "Monitoring of system components for anomalies", "category": "CC7 — System Operations", "sort_order": 27},
    {"code": "CC7.3", "title": "Evaluation of security events and identification of incidents", "category": "CC7 — System Operations", "sort_order": 28},
    {"code": "CC7.4", "title": "Response to identified security incidents", "category": "CC7 — System Operations", "sort_order": 29},
    {"code": "CC7.5", "title": "Recovery from identified security incidents", "category": "CC7 — System Operations", "sort_order": 30},
    # CC8 — Change Management
    {"code": "CC8.1", "title": "Management of changes to infrastructure and software", "category": "CC8 — Change Management", "sort_order": 31},
    # CC9 — Risk Mitigation
    {"code": "CC9.1", "title": "Identification and mitigation of business disruption risks", "category": "CC9 — Risk Mitigation", "sort_order": 32},
    {"code": "CC9.2", "title": "Management of vendor and business partner risk", "category": "CC9 — Risk Mitigation", "sort_order": 33},
]

# ---------------------------------------------------------------------------
# ISO 27001:2022 — Annex A Controls
# ---------------------------------------------------------------------------

ISO27001_CONTROLS: list[dict] = [
    # A.5 — Organizational Controls
    {"code": "A.5.1", "title": "Policies for information security", "category": "A.5 — Organizational Controls", "sort_order": 1},
    {"code": "A.5.2", "title": "Information security roles and responsibilities", "category": "A.5 — Organizational Controls", "sort_order": 2},
    {"code": "A.5.3", "title": "Segregation of duties", "category": "A.5 — Organizational Controls", "sort_order": 3},
    {"code": "A.5.4", "title": "Management responsibilities", "category": "A.5 — Organizational Controls", "sort_order": 4},
    {"code": "A.5.5", "title": "Contact with authorities", "category": "A.5 — Organizational Controls", "sort_order": 5},
    {"code": "A.5.6", "title": "Contact with special interest groups", "category": "A.5 — Organizational Controls", "sort_order": 6},
    {"code": "A.5.7", "title": "Threat intelligence", "category": "A.5 — Organizational Controls", "sort_order": 7},
    {"code": "A.5.8", "title": "Information security in project management", "category": "A.5 — Organizational Controls", "sort_order": 8},
    {"code": "A.5.9", "title": "Inventory of information and associated assets", "category": "A.5 — Organizational Controls", "sort_order": 9},
    {"code": "A.5.10", "title": "Acceptable use of information and associated assets", "category": "A.5 — Organizational Controls", "sort_order": 10},
    {"code": "A.5.11", "title": "Return of assets", "category": "A.5 — Organizational Controls", "sort_order": 11},
    {"code": "A.5.12", "title": "Classification of information", "category": "A.5 — Organizational Controls", "sort_order": 12},
    {"code": "A.5.13", "title": "Labelling of information", "category": "A.5 — Organizational Controls", "sort_order": 13},
    {"code": "A.5.14", "title": "Information transfer", "category": "A.5 — Organizational Controls", "sort_order": 14},
    {"code": "A.5.15", "title": "Access control", "category": "A.5 — Organizational Controls", "sort_order": 15},
    {"code": "A.5.16", "title": "Identity management", "category": "A.5 — Organizational Controls", "sort_order": 16},
    {"code": "A.5.17", "title": "Authentication information", "category": "A.5 — Organizational Controls", "sort_order": 17},
    {"code": "A.5.18", "title": "Access rights", "category": "A.5 — Organizational Controls", "sort_order": 18},
    {"code": "A.5.19", "title": "Information security in supplier relationships", "category": "A.5 — Organizational Controls", "sort_order": 19},
    {"code": "A.5.20", "title": "Addressing information security within supplier agreements", "category": "A.5 — Organizational Controls", "sort_order": 20},
    {"code": "A.5.21", "title": "Managing information security in the ICT supply chain", "category": "A.5 — Organizational Controls", "sort_order": 21},
    {"code": "A.5.22", "title": "Monitoring, review and change management of supplier services", "category": "A.5 — Organizational Controls", "sort_order": 22},
    {"code": "A.5.23", "title": "Information security for use of cloud services", "category": "A.5 — Organizational Controls", "sort_order": 23},
    {"code": "A.5.24", "title": "Information security incident management planning and preparation", "category": "A.5 — Organizational Controls", "sort_order": 24},
    {"code": "A.5.25", "title": "Assessment and decision on information security events", "category": "A.5 — Organizational Controls", "sort_order": 25},
    {"code": "A.5.26", "title": "Response to information security incidents", "category": "A.5 — Organizational Controls", "sort_order": 26},
    {"code": "A.5.27", "title": "Learning from information security incidents", "category": "A.5 — Organizational Controls", "sort_order": 27},
    {"code": "A.5.28", "title": "Collection of evidence", "category": "A.5 — Organizational Controls", "sort_order": 28},
    {"code": "A.5.29", "title": "Information security during disruption", "category": "A.5 — Organizational Controls", "sort_order": 29},
    {"code": "A.5.30", "title": "ICT readiness for business continuity", "category": "A.5 — Organizational Controls", "sort_order": 30},
    {"code": "A.5.31", "title": "Legal, statutory, regulatory and contractual requirements", "category": "A.5 — Organizational Controls", "sort_order": 31},
    {"code": "A.5.32", "title": "Intellectual property rights", "category": "A.5 — Organizational Controls", "sort_order": 32},
    {"code": "A.5.33", "title": "Protection of records", "category": "A.5 — Organizational Controls", "sort_order": 33},
    {"code": "A.5.34", "title": "Privacy and protection of personal identifiable information", "category": "A.5 — Organizational Controls", "sort_order": 34},
    {"code": "A.5.35", "title": "Independent review of information security", "category": "A.5 — Organizational Controls", "sort_order": 35},
    {"code": "A.5.36", "title": "Compliance with policies, rules and standards for information security", "category": "A.5 — Organizational Controls", "sort_order": 36},
    {"code": "A.5.37", "title": "Documented operating procedures", "category": "A.5 — Organizational Controls", "sort_order": 37},
    # A.6 — People Controls
    {"code": "A.6.1", "title": "Screening", "category": "A.6 — People Controls", "sort_order": 38},
    {"code": "A.6.2", "title": "Terms and conditions of employment", "category": "A.6 — People Controls", "sort_order": 39},
    {"code": "A.6.3", "title": "Information security awareness, education and training", "category": "A.6 — People Controls", "sort_order": 40},
    {"code": "A.6.4", "title": "Disciplinary process", "category": "A.6 — People Controls", "sort_order": 41},
    {"code": "A.6.5", "title": "Responsibilities after termination or change of employment", "category": "A.6 — People Controls", "sort_order": 42},
    {"code": "A.6.6", "title": "Confidentiality or non-disclosure agreements", "category": "A.6 — People Controls", "sort_order": 43},
    {"code": "A.6.7", "title": "Remote working", "category": "A.6 — People Controls", "sort_order": 44},
    {"code": "A.6.8", "title": "Information security event reporting", "category": "A.6 — People Controls", "sort_order": 45},
    # A.7 — Physical Controls
    {"code": "A.7.1", "title": "Physical security perimeters", "category": "A.7 — Physical Controls", "sort_order": 46},
    {"code": "A.7.2", "title": "Physical entry", "category": "A.7 — Physical Controls", "sort_order": 47},
    {"code": "A.7.3", "title": "Securing offices, rooms and facilities", "category": "A.7 — Physical Controls", "sort_order": 48},
    {"code": "A.7.4", "title": "Physical security monitoring", "category": "A.7 — Physical Controls", "sort_order": 49},
    {"code": "A.7.5", "title": "Protecting against physical and environmental threats", "category": "A.7 — Physical Controls", "sort_order": 50},
    {"code": "A.7.6", "title": "Working in secure areas", "category": "A.7 — Physical Controls", "sort_order": 51},
    {"code": "A.7.7", "title": "Clear desk and clear screen", "category": "A.7 — Physical Controls", "sort_order": 52},
    {"code": "A.7.8", "title": "Equipment siting and protection", "category": "A.7 — Physical Controls", "sort_order": 53},
    {"code": "A.7.9", "title": "Security of assets off-premises", "category": "A.7 — Physical Controls", "sort_order": 54},
    {"code": "A.7.10", "title": "Storage media", "category": "A.7 — Physical Controls", "sort_order": 55},
    {"code": "A.7.11", "title": "Supporting utilities", "category": "A.7 — Physical Controls", "sort_order": 56},
    {"code": "A.7.12", "title": "Cabling security", "category": "A.7 — Physical Controls", "sort_order": 57},
    {"code": "A.7.13", "title": "Equipment maintenance", "category": "A.7 — Physical Controls", "sort_order": 58},
    {"code": "A.7.14", "title": "Secure disposal or re-use of equipment", "category": "A.7 — Physical Controls", "sort_order": 59},
    # A.8 — Technological Controls
    {"code": "A.8.1", "title": "User endpoint devices", "category": "A.8 — Technological Controls", "sort_order": 60},
    {"code": "A.8.2", "title": "Privileged access rights", "category": "A.8 — Technological Controls", "sort_order": 61},
    {"code": "A.8.3", "title": "Information access restriction", "category": "A.8 — Technological Controls", "sort_order": 62},
    {"code": "A.8.4", "title": "Access to source code", "category": "A.8 — Technological Controls", "sort_order": 63},
    {"code": "A.8.5", "title": "Secure authentication", "category": "A.8 — Technological Controls", "sort_order": 64},
    {"code": "A.8.6", "title": "Capacity management", "category": "A.8 — Technological Controls", "sort_order": 65},
    {"code": "A.8.7", "title": "Protection against malware", "category": "A.8 — Technological Controls", "sort_order": 66},
    {"code": "A.8.8", "title": "Management of technical vulnerabilities", "category": "A.8 — Technological Controls", "sort_order": 67},
    {"code": "A.8.9", "title": "Configuration management", "category": "A.8 — Technological Controls", "sort_order": 68},
    {"code": "A.8.10", "title": "Information deletion", "category": "A.8 — Technological Controls", "sort_order": 69},
    {"code": "A.8.11", "title": "Data masking", "category": "A.8 — Technological Controls", "sort_order": 70},
    {"code": "A.8.12", "title": "Data leakage prevention", "category": "A.8 — Technological Controls", "sort_order": 71},
    {"code": "A.8.13", "title": "Information backup", "category": "A.8 — Technological Controls", "sort_order": 72},
    {"code": "A.8.14", "title": "Redundancy of information processing facilities", "category": "A.8 — Technological Controls", "sort_order": 73},
    {"code": "A.8.15", "title": "Logging", "category": "A.8 — Technological Controls", "sort_order": 74},
    {"code": "A.8.16", "title": "Monitoring activities", "category": "A.8 — Technological Controls", "sort_order": 75},
    {"code": "A.8.17", "title": "Clock synchronization", "category": "A.8 — Technological Controls", "sort_order": 76},
    {"code": "A.8.18", "title": "Use of privileged utility programs", "category": "A.8 — Technological Controls", "sort_order": 77},
    {"code": "A.8.19", "title": "Installation of software on operational systems", "category": "A.8 — Technological Controls", "sort_order": 78},
    {"code": "A.8.20", "title": "Networks security", "category": "A.8 — Technological Controls", "sort_order": 79},
    {"code": "A.8.21", "title": "Security of network services", "category": "A.8 — Technological Controls", "sort_order": 80},
    {"code": "A.8.22", "title": "Segregation of networks", "category": "A.8 — Technological Controls", "sort_order": 81},
    {"code": "A.8.23", "title": "Web filtering", "category": "A.8 — Technological Controls", "sort_order": 82},
    {"code": "A.8.24", "title": "Use of cryptography", "category": "A.8 — Technological Controls", "sort_order": 83},
    {"code": "A.8.25", "title": "Secure development life cycle", "category": "A.8 — Technological Controls", "sort_order": 84},
    {"code": "A.8.26", "title": "Application security requirements", "category": "A.8 — Technological Controls", "sort_order": 85},
    {"code": "A.8.27", "title": "Secure system architecture and engineering principles", "category": "A.8 — Technological Controls", "sort_order": 86},
    {"code": "A.8.28", "title": "Secure coding", "category": "A.8 — Technological Controls", "sort_order": 87},
    {"code": "A.8.29", "title": "Security testing in development and acceptance", "category": "A.8 — Technological Controls", "sort_order": 88},
    {"code": "A.8.30", "title": "Outsourced development", "category": "A.8 — Technological Controls", "sort_order": 89},
    {"code": "A.8.31", "title": "Separation of development, test and production environments", "category": "A.8 — Technological Controls", "sort_order": 90},
    {"code": "A.8.32", "title": "Change management", "category": "A.8 — Technological Controls", "sort_order": 91},
    {"code": "A.8.33", "title": "Test information", "category": "A.8 — Technological Controls", "sort_order": 92},
    {"code": "A.8.34", "title": "Protection of information systems during audit testing", "category": "A.8 — Technological Controls", "sort_order": 93},
]

# ---------------------------------------------------------------------------
# Cross-framework mappings  (SOC 2 code -> ISO 27001 code, type)
# ---------------------------------------------------------------------------

CROSS_MAPPINGS: list[dict] = [
    {"soc2": "CC1.1", "iso": "A.5.1", "type": ControlMappingType.PARTIAL, "notes": "Both address organizational commitment to security policy and ethical values"},
    {"soc2": "CC1.2", "iso": "A.5.35", "type": ControlMappingType.RELATED, "notes": "Board oversight relates to independent review of information security"},
    {"soc2": "CC1.4", "iso": "A.6.1", "type": ControlMappingType.RELATED, "notes": "Competent personnel relates to screening and hiring controls"},
    {"soc2": "CC2.1", "iso": "A.5.12", "type": ControlMappingType.PARTIAL, "notes": "Information quality relates to classification of information"},
    {"soc2": "CC3.1", "iso": "A.5.7", "type": ControlMappingType.RELATED, "notes": "Risk assessment objectives relate to threat intelligence"},
    {"soc2": "CC3.2", "iso": "A.8.8", "type": ControlMappingType.PARTIAL, "notes": "Risk identification relates to technical vulnerability management"},
    {"soc2": "CC4.1", "iso": "A.8.16", "type": ControlMappingType.EQUIVALENT, "notes": "Ongoing evaluation of controls aligns with monitoring activities"},
    {"soc2": "CC5.3", "iso": "A.5.37", "type": ControlMappingType.EQUIVALENT, "notes": "Policies and procedures map directly to documented operating procedures"},
    {"soc2": "CC6.1", "iso": "A.5.15", "type": ControlMappingType.EQUIVALENT, "notes": "Logical access security maps to access control policy"},
    {"soc2": "CC6.1", "iso": "A.8.3", "type": ControlMappingType.EQUIVALENT, "notes": "Logical access protection maps to information access restriction"},
    {"soc2": "CC6.2", "iso": "A.5.16", "type": ControlMappingType.EQUIVALENT, "notes": "User registration maps to identity management"},
    {"soc2": "CC6.3", "iso": "A.5.18", "type": ControlMappingType.EQUIVALENT, "notes": "Least privilege enforcement maps to access rights management"},
    {"soc2": "CC6.4", "iso": "A.7.1", "type": ControlMappingType.EQUIVALENT, "notes": "Physical access maps to physical security perimeters"},
    {"soc2": "CC6.6", "iso": "A.8.24", "type": ControlMappingType.EQUIVALENT, "notes": "Encryption maps to use of cryptography"},
    {"soc2": "CC6.7", "iso": "A.8.20", "type": ControlMappingType.PARTIAL, "notes": "Boundary protection relates to network security"},
    {"soc2": "CC6.8", "iso": "A.8.7", "type": ControlMappingType.EQUIVALENT, "notes": "Unauthorized software prevention maps to malware protection"},
    {"soc2": "CC7.1", "iso": "A.8.15", "type": ControlMappingType.EQUIVALENT, "notes": "Anomaly detection maps to logging controls"},
    {"soc2": "CC7.3", "iso": "A.5.25", "type": ControlMappingType.EQUIVALENT, "notes": "Security event evaluation maps to assessment and decision on events"},
    {"soc2": "CC7.4", "iso": "A.5.26", "type": ControlMappingType.EQUIVALENT, "notes": "Incident response maps to response to security incidents"},
    {"soc2": "CC7.5", "iso": "A.5.29", "type": ControlMappingType.PARTIAL, "notes": "Incident recovery relates to information security during disruption"},
    {"soc2": "CC8.1", "iso": "A.8.32", "type": ControlMappingType.EQUIVALENT, "notes": "Change management maps directly"},
    {"soc2": "CC9.1", "iso": "A.5.30", "type": ControlMappingType.PARTIAL, "notes": "Business disruption risk relates to ICT readiness for continuity"},
    {"soc2": "CC9.2", "iso": "A.5.19", "type": ControlMappingType.EQUIVALENT, "notes": "Vendor risk maps to supplier relationship security"},
]


async def seed_frameworks(db: AsyncSession) -> None:
    """Idempotent seed of compliance frameworks, controls, and cross-framework mappings."""

    # ── Check if already seeded ──────────────────────────────────────────
    existing = (await db.execute(select(Framework.key))).scalars().all()
    if "soc2" in existing and "iso27001" in existing:
        logger.info("Frameworks already seeded, skipping")
        return

    logger.info("Seeding compliance frameworks...")

    # ── SOC 2 ────────────────────────────────────────────────────────────
    soc2_fw = Framework(
        key="soc2",
        name="SOC 2 Type II",
        description="Service Organization Control 2 — Trust Services Criteria for security, availability, processing integrity, confidentiality, and privacy.",
        organization="AICPA",
        is_active=True,
    )
    db.add(soc2_fw)
    await db.flush()

    soc2_ver = FrameworkVersion(
        framework_id=soc2_fw.id,
        version="2017",
        effective_date=date(2017, 12, 15),
        is_current=True,
    )
    db.add(soc2_ver)
    await db.flush()

    soc2_control_map: dict[str, Control] = {}
    for ctrl_data in SOC2_CONTROLS:
        ctrl = Control(
            framework_version_id=soc2_ver.id,
            code=ctrl_data["code"],
            title=ctrl_data["title"],
            category=ctrl_data["category"],
            sort_order=ctrl_data["sort_order"],
        )
        db.add(ctrl)
        soc2_control_map[ctrl_data["code"]] = ctrl
    await db.flush()

    # ── ISO 27001 ────────────────────────────────────────────────────────
    iso_fw = Framework(
        key="iso27001",
        name="ISO 27001:2022",
        description="Information security management systems — Requirements. Annex A reference controls for information security.",
        organization="ISO/IEC",
        is_active=True,
    )
    db.add(iso_fw)
    await db.flush()

    iso_ver = FrameworkVersion(
        framework_id=iso_fw.id,
        version="2022",
        effective_date=date(2022, 10, 25),
        is_current=True,
    )
    db.add(iso_ver)
    await db.flush()

    iso_control_map: dict[str, Control] = {}
    for ctrl_data in ISO27001_CONTROLS:
        ctrl = Control(
            framework_version_id=iso_ver.id,
            code=ctrl_data["code"],
            title=ctrl_data["title"],
            category=ctrl_data["category"],
            sort_order=ctrl_data["sort_order"],
        )
        db.add(ctrl)
        iso_control_map[ctrl_data["code"]] = ctrl
    await db.flush()

    # ── Cross-framework mappings ─────────────────────────────────────────
    for mapping_data in CROSS_MAPPINGS:
        source = soc2_control_map.get(mapping_data["soc2"])
        target = iso_control_map.get(mapping_data["iso"])
        if source and target:
            mapping = ControlMapping(
                source_control_id=source.id,
                target_control_id=target.id,
                mapping_type=mapping_data["type"],
                notes=mapping_data["notes"],
            )
            db.add(mapping)

    await db.flush()
    logger.info(
        "Seeded %d SOC 2 controls, %d ISO 27001 controls, %d cross-framework mappings",
        len(SOC2_CONTROLS),
        len(ISO27001_CONTROLS),
        len(CROSS_MAPPINGS),
    )


async def main() -> None:
    """CLI entry point: run seed against the configured database."""
    from app.db.base import async_session_factory

    logging.basicConfig(level=logging.INFO)
    async with async_session_factory() as session:
        try:
            await seed_frameworks(session)
            await session.commit()
            logger.info("Seed completed successfully")
        except Exception:
            await session.rollback()
            logger.exception("Seed failed")
            raise


if __name__ == "__main__":
    asyncio.run(main())
