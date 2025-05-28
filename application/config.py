# config.py
import os
import sys
from sqlalchemy import create_engine, text  # Add text import
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
import pymysql
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reconfigure stdout encoding
sys.stdout.reconfigure(encoding='utf-8')

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    
    # Database configuration with environment variable fallback
    DB_HOST = os.getenv("DB_HOST", "sql8.freesqldatabase.com")
    DB_USER = os.getenv("DB_USER", "sql8781735")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "YQ8d2QdLqV")
    DB_NAME = os.getenv("DB_NAME", "sql8781735")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    
    # Construct database URL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", 
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Base for model creation
class Base(DeclarativeBase):
    pass

# Database connection with retry logic and better error handling
def create_database_engine():
    """Create database engine with robust configuration"""
    config = Config()
    
    # Enhanced connection arguments for FreeSQLDatabase
    connect_args = {
        "connect_timeout": 60,
        "read_timeout": 60,
        "write_timeout": 60,
        "charset": "utf8mb4",
        "autocommit": False,
        "init_command": "SET SESSION sql_mode='STRICT_TRANS_TABLES'",
        # Add SSL settings if needed
        "ssl_disabled": True,  # FreeSQLDatabase might not support SSL
    }
    
    try:
        engine = create_engine(
            config.SQLALCHEMY_DATABASE_URI,
            poolclass=QueuePool,
            pool_size=3,                    # Smaller pool for free tier
            max_overflow=5,                 # Limited overflow for free tier
            pool_pre_ping=True,             # Verify connections before use
            pool_recycle=1800,              # Recycle connections after 30 minutes
            connect_args=connect_args,
            echo=False  # Set to True for debugging
        )
        
        logger.info(f"Database engine created for: {config.DB_HOST}")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise

# Create engine and session
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Connection test with retry logic - FIXED VERSION
def test_connection(max_retries=3):
    """Test database connection with retry logic"""
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                # FIX: Wrap SQL string in text() function
                result = connection.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                if row and row[0] == 1:
                    logger.info("✅ Connexion réussie à MySQL !")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Tentative {attempt + 1}/{max_retries} - Erreur de connexion : {e}")
            
            if attempt < max_retries - 1:
                import time
                wait_time = (attempt + 1) * 5  # Progressive wait
                logger.info(f"Attente de {wait_time} secondes avant nouvelle tentative...")
                time.sleep(wait_time)
            else:
                logger.error("Échec de toutes les tentatives de connexion")
                return False
    
    return False

# Context manager for database sessions
from contextlib import contextmanager

@contextmanager
def get_db_session():
    """Context manager for database sessions with proper error handling"""
    session = SessionLocal()
    try:
        # Test the session - FIXED VERSION
        session.execute(text("SELECT 1"))
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

# Initialize database tables
def init_db():
    """Initialize database tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise

# Legacy function for backward compatibility
def get_session():
    """Legacy session getter - use get_db_session() context manager instead"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# Run connection test when module is imported
if __name__ == "__main__":
    test_connection()
else:
    # Test connection when imported (but don't block if it fails)
    try:
        test_connection()
    except Exception as e:
        logger.warning(f"Database connection test failed during import: {e}")
        logger.warning("Application will continue, but database operations may fail")