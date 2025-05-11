from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from app.config import Config

# Create engine
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a shared session object
db_session = scoped_session(SessionLocal)

# Define Base class for models
Base = declarative_base()
Base.query = db_session.query_property()  # Add query property to models

# Initialize database function
def init_db():
    """Initialize the database - create tables"""
    # Import models to ensure they're registered with Base
    from app.db.models import (
        Agent,
        AuthorizationCode,
        IssuedToken,
        Scope,
        ScopeAuditLog,
        TaskAuditLog,
        TokenAuditLog,
        Tool,
        User,
        AgentAuditLog
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
