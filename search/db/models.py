from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class Source(Base):
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    base_url = Column(String, unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Source(name='{self.name}', base_url='{self.base_url}')>"

class Link(Base):
    __tablename__ = 'links'
    
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=True)
    status = Column(String, default='pending')  # pending, processed, failed
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_processed_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Link(url='{self.url}', status='{self.status}')>"
    
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.datetime.utcnow()

class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey('links.id'), unique=True, nullable=False)
    title = Column(String)
    content = Column(Text)
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Document(title='{self.title}', link_id={self.link_id})>"

# Note: FTS5 virtual tables cannot be represented directly in SQLAlchemy's ORM
# We'll need to handle this table with raw SQL operations