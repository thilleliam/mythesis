from sqlalchemy import Column, ForeignKey, Integer, String
from application.config import Base
from sqlalchemy.orm import relationship , backref
class Equipement(Base):
    __tablename__ = "equipements"

    ID_equipement = Column(Integer, primary_key=True, autoincrement=True)
    quantite = Column(Integer)
    nomEquipement = Column(String(255))
    typeEquipement = Column(String(255))
    etat = Column(String(255))
commandes = relationship("CommandeEquipement")
transferer_equipements = relationship("TransfererEquipement", backref=backref("equipement", lazy="joined"))