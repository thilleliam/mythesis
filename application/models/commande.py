from application.config import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
class Commande(Base):
    __tablename__ = "commandes"

    id_commande = Column(Integer, primary_key=True, autoincrement=True)
    id_client = Column(Integer, ForeignKey("chantiers.id_client"))
    nature_service = Column(String(255))
    type_vehicule = Column(String(255))
    ID_equipement = Column(Integer, ForeignKey("equipements.ID_equipement"))
    quantite_requise = Column(Float)
    lieu_chargement = Column(String(255))
    date_commande = Column(DateTime)
    date_livraison = Column(DateTime)
client = relationship("Chantier", back_populates="commandes")  # Relation avec Chantier
equipements = relationship("CommandeEquipement", back_populates="commandes") 
tournees = relationship("Tournee", back_populates="commandes")   # Relation avec Tournee
