import sys
sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import pymysql  # Assure que pymysql est bien importé

# Définition de l'URL de la base de données
DATABASE_URL = "mysql+pymysql://root:thilleli1900@localhost/tms_db"

# Création du moteur SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)

# Création de la session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour la création des modèles
class Base(DeclarativeBase):
    pass

# Test de connexion
try:
    connection = engine.connect()
    print("Connexion réussie à MySQL !")
    connection.close()
except Exception as e:
    print(f"Erreur de connexion : {e}")


