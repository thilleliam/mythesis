# database.py
import sys
import os
from sqlalchemy import create_engine, text  # IMPORTANT: Import text function
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import OperationalError
import pymysql
import logging
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reconfigure stdout encoding
sys.stdout.reconfigure(encoding='utf-8')

# Database configuration
class DatabaseConfig:
    def __init__(self):
        # Use environment variables for production, fallback for development
        self.DB_HOST = os.getenv("DB_HOST", "sql8.freesqldatabase.com")
        self.DB_USER = os.getenv("DB_USER", "sql8781735")
        self.DB_PASSWORD = os.getenv("DB_PASSWORD", "YQ8d2QdLqV")
        self.DB_NAME = os.getenv("DB_NAME", "sql8781735")
        self.DB_PORT = int(os.getenv("DB_PORT", "3306"))
        
        # Construct database URL
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        
        logger.info(f"Database configuration: {self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")

# Base for model creation
class Base(DeclarativeBase):
    pass

# Database manager class
class DatabaseManager:
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine with robust configuration"""
        try:
            # Connection arguments optimized for FreeSQLDatabase
            connect_args = {
                "connect_timeout": 30,
                "read_timeout": 30,
                "write_timeout": 30,
                "charset": "utf8mb4",
                "autocommit": False,
                "ssl_disabled": True,  # FreeSQLDatabase doesn't support SSL
                "init_command": "SET SESSION sql_mode='STRICT_TRANS_TABLES'"
            }
            
            self.engine = create_engine(
                self.config.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=2,                    # Small pool for free tier
                max_overflow=3,                 # Limited overflow
                pool_pre_ping=True,             # Verify connections
                pool_recycle=1800,              # 30 minutes
                connect_args=connect_args,
                echo=False  # Set to True for SQL debugging
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def test_connection(self, max_retries=3):
        """Test database connection with retry logic - FIXED VERSION"""
        for attempt in range(max_retries):
            try:
                with self.engine.connect() as connection:
                    # FIX: Use text() to wrap the SQL string
                    result = connection.execute(text("SELECT 1 as test"))
                    row = result.fetchone()
                    if row and row[0] == 1:
                        logger.info("✅ Database connection successful!")
                        return True
                        
            except OperationalError as e:
                if "many connection errors" in str(e):
                    logger.warning(f"Connection blocked due to many errors: {e}")
                    if attempt < max_retries - 1:
                        import time
                        wait_time = (attempt + 1) * 10
                        logger.info(f"Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Database connection error: {e}")
                    if attempt == max_retries - 1:
                        return False
                        
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(5)
                else:
                    return False
        
        return False
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions - FIXED VERSION"""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
        
        session = self.SessionLocal()
        try:
            # FIX: Use text() to wrap the SQL string
            session.execute(text("SELECT 1"))
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def init_db(self):
        """Initialize database tables"""
        try:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")

# Create global database manager instance
try:
    db_manager = DatabaseManager()
    
    # Export for backward compatibility
    engine = db_manager.engine
    SessionLocal = db_manager.SessionLocal
    
    # Test connection on import
    if not db_manager.test_connection():
        logger.warning("Database connection test failed during initialization")
        
except Exception as e:
    logger.error(f"Failed to initialize database manager: {e}")
    # Create dummy objects to prevent import errors
    engine = None
    SessionLocal = None
    db_manager = None

# Backward compatibility functions
def test_connection():
    """Legacy function for testing connection"""
    if db_manager:
        return db_manager.test_connection()
    return False

def get_session():
    """Legacy session getter"""
    if db_manager:
        return db_manager.get_session()
    else:
        raise Exception("Database manager not initialized")

def init_db():
    """Legacy database initialization"""
    if db_manager:
        return db_manager.init_db()
    else:
        raise Exception("Database manager not initialized")

# For debugging - run this file directly to test connection
if __name__ == "__main__":
    if db_manager:
        success = db_manager.test_connection()
        if success:
            print("✅ Database connection test passed!")
        else:
            print("❌ Database connection test failed!")
    else:
        print("❌ Database manager initialization failed!")