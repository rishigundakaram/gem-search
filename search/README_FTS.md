# SQLite FTS5 Implementation

This implementation uses SQLite's built-in FTS5 (Full Text Search) extension instead of relying on external ranking libraries like rank_bm25.

## Advantages

1. **Native Full-Text Search**: Uses SQLite's optimized FTS5 engine
2. **No External Dependencies**: Eliminates dependency on rank_bm25
3. **Better Performance**: FTS5 is highly optimized for search operations
4. **Rich Query Syntax**: Supports advanced query operators
5. **Stemming Support**: Uses Porter stemming algorithm for better matches

## Database Schema

The implementation uses two tables:

1. **documents**: Stores document metadata
   - `id`: Primary key
   - `url`: Unique URL of the document
   - `title`: Document title

2. **document_content**: FTS5 virtual table for content
   - `content`: The searchable text content
   - `document_id`: Reference to the documents table (unindexed)

## Setup and Usage

1. Initialize the database with FTS5:
   ```
   python init_sqlite_db_fts.py
   ```

2. Run the FastAPI server:
   ```
   uvicorn main_fts:app --reload
   ```

3. To add new content:
   ```
   python scrapers/util_fts.py scrapers/links.json search.db
   ```

## Example Queries

In SQLite, you can use various FTS5 query formats:

1. Simple search:
   ```sql
   SELECT * FROM document_content WHERE content MATCH 'keyword'
   ```

2. Phrase search:
   ```sql
   SELECT * FROM document_content WHERE content MATCH '"exact phrase"'
   ```

3. Multiple terms (AND):
   ```sql
   SELECT * FROM document_content WHERE content MATCH 'first second'
   ```

4. OR search:
   ```sql
   SELECT * FROM document_content WHERE content MATCH 'first OR second'
   ```

5. Prefix search:
   ```sql
   SELECT * FROM document_content WHERE content MATCH 'prefix*'
   ```

The API exposes simpler query functionality, but the database supports these advanced queries if needed in the future.