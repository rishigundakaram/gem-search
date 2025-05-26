"""Simplify to basic documents schema

Revision ID: simple_schema  
Revises: c36570b1cdd3
Create Date: 2025-05-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'simple_schema'
down_revision: Union[str, None] = 'c36570b1cdd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade to simple schema."""
    conn = op.get_bind()
    
    # Drop existing FTS5 table
    conn.execute(text("DROP TABLE IF EXISTS document_content"))
    
    # Drop existing tables  
    op.drop_table('documents')
    op.drop_table('links')
    op.drop_table('sources')
    
    # Create new simple documents table
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )
    
    # Create FTS5 virtual table
    conn.execute(text("""
    CREATE VIRTUAL TABLE document_content USING fts5(
        content,
        document_id UNINDEXED,
        tokenize='porter unicode61'
    )
    """))


def downgrade() -> None:
    """Downgrade from simple schema."""
    conn = op.get_bind()
    
    # Drop the FTS5 table
    conn.execute(text("DROP TABLE IF EXISTS document_content"))
    
    # Drop simple table
    op.drop_table('documents')
    
    # Recreate complex schema (from previous migration)
    op.create_table('sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('base_url', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('base_url')
    )

    op.create_table('links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('discovered_at', sa.DateTime(), nullable=True),
        sa.Column('last_processed_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )

    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('link_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['link_id'], ['links.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('link_id')
    )
    
    conn.execute(text("""
    CREATE VIRTUAL TABLE document_content USING fts5(
        content,
        document_id UNINDEXED,
        tokenize='porter unicode61'
    )
    """))