"""Initial schema

Revision ID: c36570b1cdd3
Revises: 
Create Date: 2025-05-19 23:31:25.767132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'c36570b1cdd3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create 'sources' table
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

    # Create 'links' table
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

    # Create 'documents' table
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
    
    # Create FTS5 virtual table
    conn = op.get_bind()
    conn.execute(text("""
    CREATE VIRTUAL TABLE document_content USING fts5(
        content,
        document_id UNINDEXED,
        tokenize='porter unicode61'
    )
    """))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    
    # Drop the FTS5 table
    conn.execute(text("DROP TABLE IF EXISTS document_content"))
    
    # Drop standard tables
    op.drop_table('documents')
    op.drop_table('links')
    op.drop_table('sources')