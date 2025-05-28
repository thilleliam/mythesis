# application/database.py - Clean version without any AWS references
import sys
import os
from sqlalchemy import create_engine, text
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
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass  # Skip if not available
class DatabaseConfig:
    def __init__(self):
        # CONFIGURATION RAILWAY
        self.DB_HOST = os.environ.get("DB_HOST", "shortline.proxy.rlwy.net")
        self.DB_USER = os.environ.get("DB_USER", "root")
        self.DB_PASSWORD = os.environ.get("DB_PASSWORD", "lxdQZVBnFXQivTLxGUMbupHbObfiaAbW")
        self.DB_NAME = os.environ.get("DB_NAME", "railway")
        self.DB_PORT = int(os.environ.get("DB_PORT", "12194"))  # Port spécial Railway
        
        # Construct database URL
        self.DATABASE_URL = os.environ.get(
            "DATABASE_URL", 
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        
        # Supprimez la vérification AWS (plus nécessaire)
        logger.info(f"Database configuration: {self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}")
# Base for model creation
class Base(DeclarativeBase):
    pass

class DatabaseManager:
    def __init__(self):
        self.config = DatabaseConfig()
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine"""
        try:
            # Connection arguments for FreeSQLDatabase
            connect_args = {
                "connect_timeout": 30,
                "read_timeout": 30,
                "write_timeout": 30,
                "charset": "utf8mb4",
                "autocommit": False,
                "ssl_disabled": True,
                "init_command": "SET SESSION sql_mode='STRICT_TRANS_TABLES'"
            }
            
            self.engine = create_engine(
                self.config.DATABASE_URL,
                poolclass=QueuePool,
                pool_size=2,
                max_overflow=3,
                pool_pre_ping=True,
                pool_recycle=1800,
                connect_args=connect_args,
                echo=False
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def test_connection(self, max_retries=2):  # Reduced retries for faster startup
        """Test database connection"""
        for attempt in range(max_retries):
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text("SELECT 1 as test"))
                    row = result.fetchone()
                    if row and row[0] == 1:
                        logger.info("✅ Database connection successful!")
                        return True
                        
            except Exception as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(5)
                else:
                    logger.error("All database connection attempts failed")
                    return False
        
        return False
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
        
        session = self.SessionLocal()
        try:
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
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            return False

# Initialize database manager
try:
    db_manager = DatabaseManager()
    engine = db_manager.engine
    SessionLocal = db_manager.SessionLocal
except Exception as e:
    logger.error(f"Failed to initialize database manager: {e}")
    db_manager = None
    engine = None
    SessionLocal = None

# Backward compatibility functions
def test_connection():
    if db_manager:
        return db_manager.test_connection()
    return False

def get_session():
    if db_manager:
        return db_manager.get_session()
    else:
        raise Exception("Database manager not initialized")

def init_db():
    if db_manager:
        return db_manager.init_db()
    else:
        raise Exception("Database manager not initialized")

# Test connection on import (non-blocking)
if db_manager and __name__ != "__main__":
    try:
        db_manager.test_connection()
    except:
        pass  # Don't block startup

if __name__ == "__main__":
    if db_manager:
        success = db_manager.test_connection()
        print("✅ Database test passed!" if success else "❌ Database test failed!")
    else:
        print("❌ Database manager not initialized!")