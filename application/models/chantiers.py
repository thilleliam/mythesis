from application.config import Base
from sqlalchemy import Column, event, Integer, String, Float
from sqlalchemy.orm import relationship

class Chantier(Base):
    __tablename__ = "chantiers"
    id_client = Column(String(255), primary_key=True)
    localisation = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    nature_terrain = Column(String(255))
    distanceAllerGoudron = Column(Float)
    distanceAllerPiste = Column(Float)
    temps_aller = Column(Float)
    def calculer_temps_aller(self):
        """Calcule le temps d'aller et met à jour la colonne correspondante."""
        if self.distanceAllerGoudron is None or self.distanceAllerPiste is None:
            return None

        return (self.distanceAllerGoudron + self.distanceAllerPiste) / 400

    
    # Cet attribut doit être indenté à l'intérieur de la classe
commandes = relationship("Commande", back_populates="client")


    # Cette méthode doit être indentée à l'intérieur de la classe

# Événement SQLAlchemy pour mettre à jour `temps_aller` avant chaque commit
@event.listens_for(Chantier, "before_insert")
@event.listens_for(Chantier, "before_update")
def before_insert_or_update(mapper, connection, target):
    target.temps_aller = target.calculer_temps_aller()