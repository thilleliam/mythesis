from application.config import Base
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import validates
from sqlalchemy.event import listens_for

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
    date_heure_arrivee = Column(DateTime)
    duree = Column(String(255))
    
    conducteur = relationship("Conducteur", backref=backref("tournees", uselist=True))
    commande = relationship("Commande", backref=backref("tournees", uselist=True))
    vehicule = relationship("Vehicule", backref=backref("tournees", uselist=True))
    affectations = relationship("Affectation", backref=backref("tournee", uselist=False))
    etapes_rotation = relationship("EtapeRotation", backref=backref("tournee", uselist=False))

    def calculer_duree(self) -> str:
        """ Calcule la durée en heures si ≤ 8h, sinon en jours. """
        if self.date_heure_depart and self.date_heure_arrivee:
            duree_heures = (self.date_heure_arrivee - self.date_heure_depart).total_seconds() / 3600
            return f"{round(duree_heures, 2)} heures" if duree_heures <= 8 else f"{round(duree_heures / 8, 2)} jours"
        return "Durée inconnue"

@listens_for(Tournee, "before_insert")
@listens_for(Tournee, "before_update")
def set_duree(mapper, connection, target):
    """ Met à jour automatiquement la durée avant d'insérer ou de mettre à jour une tournée. """
    target.duree = target.calculer_duree()