from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from application.config import Base

class EtapeRotation(Base):
    __tablename__ = "etapes_rotation"

    id_etape = Column(Integer, primary_key=True, autoincrement=True)
    id_tournee = Column(Integer, ForeignKey("tournees.id_tournee"))
    lieu_chargement = Column(String(255))
    lieu_dechargement = Column(String(255))
    date_heure_depart = Column(DateTime)
    date_heure_arrivee = Column(DateTime)
    duree = Column(String(255))
    type = Column(String(255))

    # Relation avec la tournée
    tournees = relationship("Tournee", back_populates="etapes") # Relation avec Tournee