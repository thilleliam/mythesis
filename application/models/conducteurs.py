from sqlalchemy import Column, Integer, String
from application.config import Base
from sqlalchemy.orm import relationship
class Conducteur(Base):
    __tablename__ = "conducteurs"

    id_conducteur = Column(String(255), primary_key=True)
    nom = Column(String(255))
    prenom = Column(String(255))
    numero_telephone = Column(String(255))
    categorie = Column(String(255))
