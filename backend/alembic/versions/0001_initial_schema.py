"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-29

Creates all tables for TF AI-QC v0.1:
  users, reports, qc_results, qc_flags, revisions, revision_responses, rules
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE user_role AS ENUM ('appraiser', 'reviewer', 'admin')")
    op.execute("CREATE TYPE file_type AS ENUM ('xml', 'pdf')")
    op.execute("CREATE TYPE report_status AS ENUM ('submitted','qc_running','qc_complete','approved','revision_requested','resubmitted')")
    op.execute("CREATE TYPE flag_severity AS ENUM ('error', 'warning', 'info')")
    op.execute("CREATE TYPE revision_status AS ENUM ('open', 'responded', 'closed')")
    op.execute("CREATE TYPE rule_category AS ENUM ('uad_format', 'gse', 'uspap', 'quality')")
    op.execute("CREATE TYPE rule_severity AS ENUM ('error', 'warning', 'info')")

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("bubble_user_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
        sa.Column("role", sa.Enum("appraiser", "reviewer", "admin", name="user_role"), nullable=False, server_default="appraiser"),
        sa.Column("license_number", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_bubble_user_id", "users", ["bubble_user_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("category", sa.Enum("uad_format", "gse", "uspap", "quality", name="rule_category"), nullable=False),
        sa.Column("severity", sa.Enum("error", "warning", "info", name="rule_severity"), nullable=False),
        sa.Column("description", sa.String(512), nullable=False),
        sa.Column("detail", sa.Text, nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_rules_code", "rules", ["code"], unique=True)
    op.create_index("ix_rules_category", "rules", ["category"])

    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("uploader_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("file_url", sa.String(1024), nullable=False),
        sa.Column("file_type", sa.Enum("xml", "pdf", name="file_type"), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("status", sa.Enum("submitted","qc_running","qc_complete","approved","revision_requested","resubmitted", name="report_status"), nullable=False, server_default="submitted"),
        sa.Column("run_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("property_address", sa.Text, nullable=True),
        sa.Column("borrower_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reports_uploader_id", "reports", ["uploader_id"])
    op.create_index("ix_reports_status", "reports", ["status"])

    op.create_table(
        "qc_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_number", sa.Integer, nullable=False),
        sa.Column("pass_fail", sa.Boolean, nullable=False),
        sa.Column("quality_score", sa.Integer, nullable=True),
        sa.Column("score_breakdown", JSONB, nullable=True),
        sa.Column("raw_flags", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_qc_results_report_id", "qc_results", ["report_id"])

    op.create_table(
        "qc_flags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("qc_result_id", sa.String(36), sa.ForeignKey("qc_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rule_id", sa.String(36), sa.ForeignKey("rules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("severity", sa.Enum("error", "warning", "info", name="flag_severity"), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("message", sa.String(1024), nullable=False),
        sa.Column("value_found", sa.String(512), nullable=True),
        sa.Column("value_expected", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_qc_flags_qc_result_id", "qc_flags", ["qc_result_id"])

    op.create_table(
        "revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("requested_by_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("run_number", sa.Integer, nullable=False),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
        sa.Column("status", sa.Enum("open", "responded", "closed", name="revision_status"), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_revisions_report_id", "revisions", ["report_id"])

    op.create_table(
        "revision_responses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("revision_id", sa.String(36), sa.ForeignKey("revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("responder_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("response_text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_revision_responses_revision_id", "revision_responses", ["revision_id"])

    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    for table in ["users", "rules", "reports", "qc_results", "qc_flags", "revisions", "revision_responses"]:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at();
        """)


def downgrade() -> None:
    tables = ["revision_responses", "revisions", "qc_flags", "qc_results", "reports", "rules", "users"]
    for table in tables:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")
        op.drop_table(table)
    op.execute("DROP FUNCTION IF EXISTS update_updated_at()")
    for enum_name in ["user_role", "file_type", "report_status", "flag_severity",
                      "revision_status", "rule_category", "rule_severity"]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
