# etape.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from application.config import Base

class EtapeRotation(Base):
    __tablename__ = "etapes_rotation"
    
    # Vos colonnes...
    id_etape = Column(Integer, primary_key=True, autoincrement=True)
    id_tournee = Column(Integer, ForeignKey("tournees.id_tournee"))
    # autres colonnes...
    
    # Utilisez back_populates au lieu de backref pour être cohérent
    