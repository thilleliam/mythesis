from application.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
class Tournee(Base):
    __tablename__ = "tournees"

    id_tournee = Column(Integer, primary_key=True, autoincrement=True)
    id_conducteur = Column(String(255), ForeignKey("conducteurs.id_conducteur"))
    immatriculation_vehicule = Column(String(255), ForeignKey("vehicules.immatriculation"))
    id_commande = Column(Integer, ForeignKey("commandes.id_commande"))
    objectif = Column(String(255))
    lieu_depart = Column(String(255))
    destination = Column(String(255))
    itineraire = Column(String(255))
    km_parcouru = Column(Float)
    date_heure_depart = Column(DateTime)
    date_heure_reception = Column(DateTime)
    date_heure_retour = Column(DateTime)
conducteur = relationship("Conducteur", back_populates="tournees")
commande = relationship("Commande", back_populates="tournees")
vehicule = relationship("Vehicule", back_populates="tournees")
affectations = relationship("Affectation", back_populates="tournee")
etapes_rotation = relationship("EtapeRotation", backref="tournee")