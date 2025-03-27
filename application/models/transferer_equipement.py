from sqlalchemy import Column, ForeignKey, Integer, String, event
from application.config import Base
from sqlalchemy.orm import relationship, backref



class TransfererEquipement(Base):
    __tablename__ = "transferer_equipement"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    volet = Column(String(255), nullable=True)  # Changé en nullable=True
    designation_equipement = Column(String(255), nullable=False)
    modalite_transport = Column(String(255), nullable=True)  # Ajouté cette colonne
    total_equipements = Column(Integer, nullable=False)
    id_client = Column(String(255), ForeignKey("chantiers.id_client"), nullable=False) 
    
    client = relationship("Chantier", backref="equipements_transferes")
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
# Utilisation d'un événement pour synchroniser les valeurs lors de l'insertion ou de la mise à jour
@event.listens_for(TransfererEquipement, 'before_insert')
@event.listens_for(TransfererEquipement, 'before_update')
def synchronize_equipement_details(mapper, connection, target):
    from application.models.equipements import Equipement
    # Synchroniser les caractéristiques de l'équipement
    equipement = connection.execute(
        Equipement.__table__.select().where(Equipement.ID_equipement == target.id_equipement)
    ).fetchone()

    if equipement:
        target.designation_equipement = equipement.nomEquipement
        # Vous pouvez également synchroniser d'autres caractéristiques si nécessaire