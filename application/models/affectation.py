from application.config import Base
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship


class Affectation(Base):
    __tablename__ = "affectations"

    id_affectation = Column(Integer, primary_key=True, autoincrement=True)
    id_conducteur = Column(Integer, ForeignKey("conducteurs.id_conducteur"))
    immatriculation_vehicule = Column(String(255), ForeignKey("vehicules.immatriculation"))
    id_tournee = Column(Integer, ForeignKey("tournees.id_tournee"))
    date_affectation = Column(DateTime)
conducteur = relationship("Conducteur", back_populates="affectations")
vehicule = relationship("Vehicule", back_populates="affectations")
tournee = relationship("Tournee", back_populates="affectations")


