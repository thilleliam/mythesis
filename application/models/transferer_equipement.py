from sqlalchemy import Column, ForeignKey, Integer, String
from application.config import Base
from sqlalchemy.orm import relationship

class TransfererEquipement(Base):
    __tablename__ = "transferer_equipement"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    volet = Column(String(255), nullable=True)  # Changé en nullable=True
    designation_equipement = Column(String(255), nullable=False)
    modalite_transport = Column(String(255), nullable=True)  # Ajouté cette colonne
    total_equipements = Column(Integer, nullable=False)
    
    # Relation avec la table des semaines
    semaines = relationship("SemaineTransfert", back_populates="equipement", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TransfererEquipement(id={self.id}, designation={self.designation_equipement}, total={self.total_equipements})>"

class SemaineTransfert(Base):
    __tablename__ = "semaine_transfert"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    id_equipement = Column(Integer, ForeignKey("transferer_equipement.id"), nullable=False)  # Renommé pour correspondre à l'application
    numero_semaine = Column(Integer, nullable=False)
    quantite = Column(Integer, nullable=True)
    
    # Relation avec la table principale
    equipement = relationship("TransfererEquipement", back_populates="semaines")
    
    def __repr__(self):
        return f"<SemaineTransfert(id={self.id}, id_equipement={self.id_equipement}, semaine={self.numero_semaine}, quantite={self.quantite})>"