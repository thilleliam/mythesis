from sqlalchemy import Column, ForeignKey , Float, Integer, String
from application.config import Base
from sqlalchemy.orm import relationship , backref
class Equipement(Base):
    __tablename__ = "equipements"

    ID_equipement = Column(Integer, primary_key=True, autoincrement=True)
    quantite = Column(Integer)
    nomEquipement = Column(String(255))
    typeEquipement = Column(String(255))
    etat = Column(String(255))
    poids = Column(Float, nullable=True, comment="Poids de l'équipement en kilogrammes")
    volume = Column(Float, nullable=True, comment="Volume de l'équipement en mètres cubes")
commandes = relationship("CommandeEquipement")
transferer_equipements = relationship("TransfererEquipement", backref=backref("equipement", lazy="joined"))