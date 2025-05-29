from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Document(Base):  # type: ignore[misc,valid-type]
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    content = Column(Text)

    def __repr__(self) -> str:
        return f"<Document(title='{self.title}', url='{self.url}')>"


# Note: FTS5 virtual tables cannot be represented directly in SQLAlchemy's ORM
# We'll need to handle this table with raw SQL operations
