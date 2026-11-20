"""initial schema: users, cases, chats, documents, chunks

Revision ID: 0001
Revises:
Create Date: 2026-11-20
"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from app.config import get_settings

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = get_settings().embedding_dim

document_status = postgresql.ENUM(
    "pending", "embedded", "failed", "skipped", name="document_status", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    document_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("google_sub", sa.Text, nullable=False, unique=True),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("name", sa.Text),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("notice_number", sa.Text, nullable=False, unique=True),
        sa.Column("title", sa.Text),
        sa.Column("sector", sa.Text),
        sa.Column("proceeding_type", sa.Text),
        sa.Column("status", sa.Text),
        sa.Column("posted_date", sa.DateTime(timezone=True)),
        sa.Column("source_url", sa.Text),
        sa.Column("last_listed_at", sa.DateTime(timezone=True)),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("record_fingerprint", sa.Text),
    )

    op.create_table(
        "chats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_chats_user_id_updated_at", "chats", ["user_id", "updated_at"])

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_url", sa.Text, nullable=False, unique=True),
        sa.Column("title", sa.Text),
        sa.Column("filer", sa.Text),
        sa.Column("filed_date", sa.DateTime(timezone=True)),
        sa.Column("mime", sa.Text),
        sa.Column("sha256", sa.Text),
        sa.Column("status", document_status, nullable=False, server_default="pending"),
        sa.Column("error", sa.Text),
        sa.Column("n_paragraphs", sa.Integer),
        sa.Column("fetched_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("para_start", sa.Integer, nullable=False),
        sa.Column("para_end", sa.Integer, nullable=False),
        sa.Column("page", sa.Integer),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        sa.Column(
            "tsv",
            postgresql.TSVECTOR,
            sa.Computed("to_tsvector('english', text)", persisted=True),
        ),
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index("ix_chunks_case_id", "chunks", ["case_id"])
    op.create_index(
        "ix_chunks_embedding_hnsw",
        "chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index("ix_chunks_tsv", "chunks", ["tsv"], postgresql_using="gin")


def downgrade() -> None:
    op.drop_table("chunks")
    op.drop_table("documents")
    op.drop_table("chats")
    op.drop_table("cases")
    op.drop_table("users")
    document_status.drop(op.get_bind(), checkfirst=True)
