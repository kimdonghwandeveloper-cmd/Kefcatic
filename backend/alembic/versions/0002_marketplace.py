"""Phase 4: add marketplace_templates and template_reviews tables.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TEXT as PGTEXT

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_superuser to users and rename name → display_name
    op.add_column("users", sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"))
    op.alter_column("users", "name", new_column_name="display_name")

    op.create_table(
        "marketplace_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("author_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("role_type", sa.String),
        sa.Column("required_connectors", sa.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("required_permissions", sa.ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("default_config", JSONB),
        sa.Column("version", sa.String, nullable=False, server_default="1.0.0"),
        sa.Column("install_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("avg_rating", sa.Float),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("is_official", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_marketplace_templates_status", "marketplace_templates", ["status"])
    op.create_index("ix_marketplace_templates_role_type", "marketplace_templates", ["role_type"])
    op.create_index("ix_marketplace_templates_install_count", "marketplace_templates", ["install_count"])

    op.create_table(
        "template_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("marketplace_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer, nullable=False),
        sa.Column("comment", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_template_reviews_template_id", "template_reviews", ["template_id"])
    # Prevent duplicate reviews per user per template
    op.create_unique_constraint("uq_template_reviews_user_template", "template_reviews", ["template_id", "user_id"])


def downgrade() -> None:
    op.drop_table("template_reviews")
    op.drop_table("marketplace_templates")
    op.alter_column("users", "display_name", new_column_name="name")
    op.drop_column("users", "is_superuser")
