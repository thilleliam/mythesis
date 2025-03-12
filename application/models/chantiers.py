from application.config import Base
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship

class Chantier(Base):
    __tablename__ = "chantiers"

    id_client = Column(Integer, primary_key=True)
    localisation = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    nature_terrain = Column(String(255))
    distanceAllerGoudron = Column(Float)
    distanceAllerPiste = Column(Float)
commandes = relationship("Commande", back_populates="client")

