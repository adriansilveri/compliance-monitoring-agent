"""
Database configuration and session management
Following SOLID principles - Single Responsibility for database operations
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

settings = get_settings()

# Database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Validate connections before use
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


async def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered
        from app.models import transaction, compliance, user  # noqa
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


def get_db() -> Session:
    """
    Database session dependency
    Following Dependency Inversion Principle
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseManager:
    """
    Database operations manager
    Following Single Responsibility Principle
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def commit_transaction(self):
        """Commit current transaction"""
        try:
            self.session.commit()
            logger.info("Database transaction committed")
        except Exception as e:
            self.session.rollback()
            logger.error("Database transaction failed", error=str(e))
            raise
    
    def rollback_transaction(self):
        """Rollback current transaction"""
        self.session.rollback()
        logger.info("Database transaction rolled back")
    
    def close_session(self):
        """Close database session"""
        self.session.close()
