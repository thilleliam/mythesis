import os
from sqlalchemy.orm import registry
from application.database import Base, engine, SessionLocal

# Additional configuration settings for your application
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "mysql+pymysql://root:thilleli1900@localhost/tms_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
def configure_mappers():
    reg = registry()
    reg.configure()

# Example function to initialize the database
def init_db():
    Base.metadata.create_all(bind=engine)

# Example function to get a new database session
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
