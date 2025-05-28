from sqlalchemy import Column, ForeignKey, Integer, String
from application.database import Base
from sqlalchemy.orm import relationship, backref



class TransfererEquipement(Base):
    __tablename__ = "transferer_equipement"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    volet = Column(String(255), nullable=True)  
    nom_equipement = Column(String(255), nullable=False)  # Renommé pour correspondre à nomEquipement
    id_equipement = Column(Integer, ForeignKey("equipements.ID_equipement"), nullable=False)
    modalite_transport = Column(String(255), nullable=True)  
    total_equipements = Column(Integer, nullable=False)
    id_client = Column(String(255), ForeignKey("chantiers.id_client"), nullable=False) 
    douze_semaines_avant = Column("12_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    onze_semaines_avant = Column("11_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    dix_semaines_avant = Column("10_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    neuf_semaines_avant = Column("9_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    huit_semaines_avant = Column("8_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    sept_semaines_avant = Column("7_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    six_semaines_avant = Column("6_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    cinq_semaines_avant = Column("5_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    quatre_semaines_avant = Column("4_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    trois_semaines_avant = Column("3_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    deux_semaines_avant = Column("2_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    un_semaines_avant = Column("1_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    zero_semaines_avant = Column("0_semaines_avant_la_fin_de_l'ancien_projet", Integer, nullable=True)
    
    client = relationship("Chantier", backref="equipements_transferes")
