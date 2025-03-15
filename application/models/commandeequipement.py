from sqlalchemy import Column, ForeignKey, Integer, String
from application.config import Base
from sqlalchemy.orm import relationship
class CommandeEquipement(Base):
    __tablename__ = "commandes_equipements"

    id_commande = Column(Integer, ForeignKey("commandes.id_commande"), primary_key=True)
    ID_equipement = Column(Integer, ForeignKey("equipements.ID_equipement"), primary_key=True)

    commande = relationship("Commande")
    equipement = relationship("Equipement")