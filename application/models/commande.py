from application.config import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship, backref
from datetime import datetime

class Commande(Base):
    __tablename__ = "commandes"

    id_commande = Column(Integer, primary_key=True, autoincrement=True)
    id_client = Column(String(255), ForeignKey("chantiers.id_client"))
    id_equipement = Column(Integer, ForeignKey("equipements.ID_equipement"))
    nature_service = Column(String(255))
    type_vehicule = Column(String(255))
    quantite_requise = Column(Float)
    lieu_chargement = Column(String(255))
    date_commande = Column(DateTime)
    date_livraison = Column(DateTime)

    equipement = relationship("Equipement")

    def est_en_retard(self, date_actuelle: datetime) -> bool:
        """Vérifie si la commande est en retard par rapport à la date actuelle."""
        if self.date_livraison is None:
            return False
        return self.date_livraison < date_actuelle

    def associer_tournee(self, id_tournee: int):
        """Associe cette commande à une tournée."""
        self.id_tournee = id_tournee  # Mise à jour de la clé étrangère

    def calculer_delai_livraison(self, distance: float, weight: float) -> float:
        """Calcule le délai de livraison estimé en heures."""
        vitesse_moyenne = 60  # km/h
        facteur_poids = 1 + (weight / 10000)  # Facteur qui ralentit selon le poids

        return (distance / vitesse_moyenne) * facteur_poids
    
client = relationship("Chantier", back_populates="commandes")  
equipements = relationship("CommandeEquipement")  
tournee = relationship("Tournee", backref=backref("commandes", lazy="dynamic"))  # Relation avec Tournee
