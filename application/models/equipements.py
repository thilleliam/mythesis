from sqlalchemy import Column, ForeignKey, Integer, String
from application.config import Base
from sqlalchemy.orm import relationship
class Equipement(Base):
    __tablename__ = "equipements"

    ID_equipement = Column(Integer, primary_key=True, autoincrement=True)
    quantite = Column(Integer)
    id_commande = Column(Integer, ForeignKey("commandes.id_commande"))
    nomEquipement = Column(String(255))
    typeEquipement = Column(String(255))
    etat = Column(String(255))
commande = relationship("Commande", back_populates="equipements")
