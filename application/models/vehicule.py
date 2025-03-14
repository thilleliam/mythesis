from sqlalchemy import Column, String, Float
from application.config import Base
from sqlalchemy.orm import relationship
class Vehicule(Base):
    __tablename__ = "vehicules"

    immatriculation = Column(String(255), primary_key=True)
    numero_chassis = Column(String(255))
    numero_interne = Column(String(255))
    marque_modele = Column(String(255))
    type_vehicule = Column(String(255))
    capacite_tonne = Column(Float)
    capacite_volume = Column(Float)
tournees = relationship("Tournee", back_populates="vehicule")
affectations = relationship("Affectation", back_populates="vehicule")