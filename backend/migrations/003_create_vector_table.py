"""
Create vector table with sqlite-vec extension.
This migration loads the sqlite-vec extension and creates the virtual table.
"""

import sqlite_vec
from yoyo import step


def apply_vector_table(conn):
    """Apply: Create vector table with sqlite-vec extension."""
    # Enable extension loading
    conn.enable_load_extension(True)

    # Load sqlite-vec extension
    sqlite_vec.load(conn)

    # Disable extension loading for security
    conn.enable_load_extension(False)

    cursor = conn.cursor()

    # Create vector virtual table
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS document_vectors USING vec0(
            embedding float[1024],
            document_id INTEGER
        )
    """)

    conn.commit()


def rollback_vector_table(conn):
    """Rollback: Drop vector table."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS document_vectors")
    conn.commit()


# Define the migration step
steps = [
    step(apply_vector_table, rollback_vector_table)
]
