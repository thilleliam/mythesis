import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import pymysql  # Ensure pymysql is imported

# Reconfigure stdout encoding
sys.stdout.reconfigure(encoding='utf-8')

# Define the database URL using an environment variable for better security
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:thilleli1900@localhost/tms_db")

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)

# Create the session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for model creation
class Base(DeclarativeBase):
    pass

# Test the database connection
def test_connection():
    try:
        with engine.connect() as connection:
            print("Connexion réussie à MySQL !")
    except Exception as e:
        print(f"Erreur de connexion : {e}")

# Run the connection test
test_connection()
