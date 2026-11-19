"""GRC models — frameworks, controls, risks, evidence, policies, vendors

Revision ID: 002
Revises: 001
Create Date: 2024-11-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ts_cols() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    ]


def _tenant_pk_cols() -> list[sa.Column]:
    return [
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
    ]


def _enable_rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table} "
        f"USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)"
    )
    op.execute(
        f"CREATE POLICY tenant_isolation_insert ON {table} "
        f"FOR INSERT WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid)"
    )


# --- Enum types ---

control_status = sa.Enum(
    "not_started", "in_progress", "implemented", "not_applicable", "failed",
    name="control_status",
)
control_effectiveness = sa.Enum("none", "partial", "full", name="control_effectiveness")
control_mapping_type = sa.Enum("equivalent", "partial", "related", name="control_mapping_type")

risk_category = sa.Enum(
    "operational", "technical", "compliance", "strategic", "financial", "reputational",
    name="risk_category",
)
risk_likelihood = sa.Enum("very_low", "low", "medium", "high", "very_high", name="risk_likelihood")
risk_impact = sa.Enum("very_low", "low", "medium", "high", "very_high", name="risk_impact")
risk_treatment = sa.Enum("accept", "mitigate", "transfer", "avoid", name="risk_treatment")
risk_status = sa.Enum("open", "mitigating", "closed", "accepted", name="risk_status")

evidence_status = sa.Enum("pending", "approved", "rejected", "expired", name="evidence_status")
evidence_collection_method = sa.Enum("manual", "automated", name="evidence_collection_method")
collection_run_status = sa.Enum("pending", "running", "completed", "failed", name="collection_run_status")

policy_status = sa.Enum("draft", "published", "archived", name="policy_status")

vendor_risk_level = sa.Enum("low", "medium", "high", "critical", name="vendor_risk_level")
vendor_status = sa.Enum("active", "under_review", "inactive", "terminated", name="vendor_status")

_TENANT_RLS_TABLES = [
    "tenant_control_statuses",
    "risks",
    "evidence",
    "control_evidence",
    "evidence_collection_runs",
    "policies",
    "vendors",
]


def upgrade() -> None:
    bind = op.get_bind()
    for e in [
        control_status, control_effectiveness, control_mapping_type,
        risk_category, risk_likelihood, risk_impact, risk_treatment, risk_status,
        evidence_status, evidence_collection_method, collection_run_status,
        policy_status, vendor_risk_level, vendor_status,
    ]:
        e.create(bind, checkfirst=True)

    # --- frameworks (system-wide, not tenant-scoped) ---
    op.create_table(
        "frameworks",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("key", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        *_ts_cols(),
    )

    # --- framework_versions ---
    op.create_table(
        "framework_versions",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("framework_id", UUID(as_uuid=True), sa.ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("metadata", JSON, nullable=True),
        *_ts_cols(),
        sa.UniqueConstraint("framework_id", "version", name="uq_framework_version"),
    )
    op.create_index("ix_framework_versions_framework_id", "framework_versions", ["framework_id"])

    # --- controls ---
    op.create_table(
        "controls",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("framework_version_id", UUID(as_uuid=True), sa.ForeignKey("framework_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("controls.id", ondelete="SET NULL"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        *_ts_cols(),
        sa.UniqueConstraint("framework_version_id", "code", name="uq_control_framework_code"),
    )
    op.create_index("ix_controls_framework_version_id", "controls", ["framework_version_id"])
    op.create_index("ix_controls_category", "controls", ["category"])

    # --- control_mappings ---
    op.create_table(
        "control_mappings",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("source_control_id", UUID(as_uuid=True), sa.ForeignKey("controls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_control_id", UUID(as_uuid=True), sa.ForeignKey("controls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mapping_type", control_mapping_type, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_control_id", "target_control_id", name="uq_control_mapping_src_tgt"),
    )
    op.create_index("ix_control_mappings_source", "control_mappings", ["source_control_id"])
    op.create_index("ix_control_mappings_target", "control_mappings", ["target_control_id"])

    # --- tenant_control_statuses (tenant-scoped) ---
    op.create_table(
        "tenant_control_statuses",
        *_tenant_pk_cols(),
        sa.Column("control_id", UUID(as_uuid=True), sa.ForeignKey("controls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", control_status, nullable=False, server_default=sa.text("'not_started'")),
        sa.Column("effectiveness", control_effectiveness, nullable=True),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_assessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        *_ts_cols(),
        sa.UniqueConstraint("tenant_id", "control_id", name="uq_tenant_control_status"),
    )
    op.create_index("ix_tenant_control_statuses_tenant_id", "tenant_control_statuses", ["tenant_id"])
    op.create_index("ix_tenant_control_statuses_control_id", "tenant_control_statuses", ["control_id"])
    op.create_index("ix_tenant_control_statuses_tenant_status", "tenant_control_statuses", ["tenant_id", "status"])

    # --- risks (tenant-scoped) ---
    op.create_table(
        "risks",
        *_tenant_pk_cols(),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", risk_category, nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("likelihood", risk_likelihood, nullable=False),
        sa.Column("impact", risk_impact, nullable=False),
        sa.Column("inherent_score", sa.Float(), nullable=False),
        sa.Column("treatment", risk_treatment, nullable=True),
        sa.Column("treatment_plan", sa.Text(), nullable=True),
        sa.Column("residual_likelihood", risk_likelihood, nullable=True),
        sa.Column("residual_impact", risk_impact, nullable=True),
        sa.Column("residual_score", sa.Float(), nullable=True),
        sa.Column("status", risk_status, nullable=False, server_default=sa.text("'open'")),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("related_control_ids", JSON, nullable=True),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_review_at", sa.DateTime(timezone=True), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_risks_tenant_id", "risks", ["tenant_id"])
    op.create_index("ix_risks_tenant_status", "risks", ["tenant_id", "status"])
    op.create_index("ix_risks_tenant_category", "risks", ["tenant_id", "category"])

    # --- evidence (tenant-scoped) ---
    op.create_table(
        "evidence",
        *_tenant_pk_cols(),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("storage_backend", sa.String(50), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("previous_version_id", UUID(as_uuid=True), sa.ForeignKey("evidence.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", evidence_status, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collection_method", evidence_collection_method, nullable=False, server_default=sa.text("'manual'")),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("tags", JSON, nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_evidence_tenant_id", "evidence", ["tenant_id"])
    op.create_index("ix_evidence_tenant_status", "evidence", ["tenant_id", "status"])
    op.create_index("ix_evidence_sha256", "evidence", ["sha256_hash"])

    # --- control_evidence (tenant-scoped join table) ---
    op.create_table(
        "control_evidence",
        *_tenant_pk_cols(),
        sa.Column("control_id", UUID(as_uuid=True), sa.ForeignKey("controls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_id", UUID(as_uuid=True), sa.ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.UniqueConstraint("tenant_id", "control_id", "evidence_id", name="uq_control_evidence"),
    )
    op.create_index("ix_control_evidence_tenant_id", "control_evidence", ["tenant_id"])
    op.create_index("ix_control_evidence_control_id", "control_evidence", ["control_id"])
    op.create_index("ix_control_evidence_evidence_id", "control_evidence", ["evidence_id"])

    # --- evidence_collection_runs (tenant-scoped) ---
    op.create_table(
        "evidence_collection_runs",
        *_tenant_pk_cols(),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("status", collection_run_status, nullable=False, server_default=sa.text("'pending'")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_evidence_collection_runs_tenant_id", "evidence_collection_runs", ["tenant_id"])

    # --- policies (tenant-scoped) ---
    op.create_table(
        "policies",
        *_tenant_pk_cols(),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", policy_status, nullable=False, server_default=sa.text("'draft'")),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("review_date", sa.Date(), nullable=True),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tags", JSON, nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_policies_tenant_id", "policies", ["tenant_id"])
    op.create_index("ix_policies_tenant_status", "policies", ["tenant_id", "status"])

    # --- vendors (tenant-scoped) ---
    op.create_table(
        "vendors",
        *_tenant_pk_cols(),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("risk_level", vendor_risk_level, nullable=True),
        sa.Column("status", vendor_status, nullable=False, server_default=sa.text("'active'")),
        sa.Column("contract_start", sa.Date(), nullable=True),
        sa.Column("contract_end", sa.Date(), nullable=True),
        sa.Column("last_assessment_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_assessment_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("owner_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        *_ts_cols(),
    )
    op.create_index("ix_vendors_tenant_id", "vendors", ["tenant_id"])
    op.create_index("ix_vendors_tenant_status", "vendors", ["tenant_id", "status"])

    # --- RLS on all tenant-scoped tables ---
    for table in _TENANT_RLS_TABLES:
        _enable_rls(table)


def downgrade() -> None:
    for table in reversed(_TENANT_RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_insert ON {table}")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.drop_table("vendors")
    op.drop_table("policies")
    op.drop_table("evidence_collection_runs")
    op.drop_table("control_evidence")
    op.drop_table("evidence")
    op.drop_table("risks")
    op.drop_table("tenant_control_statuses")
    op.drop_table("control_mappings")
    op.drop_table("controls")
    op.drop_table("framework_versions")
    op.drop_table("frameworks")

    bind = op.get_bind()
    for e in [
        vendor_status, vendor_risk_level,
        policy_status,
        collection_run_status, evidence_collection_method, evidence_status,
        risk_status, risk_treatment, risk_impact, risk_likelihood, risk_category,
        control_mapping_type, control_effectiveness, control_status,
    ]:
        e.drop(bind, checkfirst=True)
