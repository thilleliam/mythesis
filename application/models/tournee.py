# tournee.py
from application.config import Base 
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date
from sqlalchemy.orm import relationship, backref

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
    
    conducteur = relationship("Conducteur", backref=backref("tournees", uselist=True))
    # Utilisez backref au lieu de back_populates
    commande = relationship("Commande", backref=backref("tournees", uselist=True))
    vehicule = relationship("Vehicule", backref=backref("tournees", uselist=True))
    affectations = relationship("Affectation", backref=backref("tournee", uselist=False))
    etapes_rotation = relationship("EtapeRotation", backref=backref("tournee", uselist=False))