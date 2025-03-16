from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from application.config import Base
from application.database import SessionLocal
from sqlalchemy import func

class Conducteur(Base):
    __tablename__ = 'conducteurs'

    id_conducteur = Column(String(255), primary_key=True)
    nom = Column(String(255), nullable=False)
    prenom = Column(String(255), nullable=False)
    numero_telephone = Column(String(255), nullable=False)
    categorie = Column(String(255), nullable=False)
    disponibilite = Column(Enum("disponible", "conge", "autres", name="disponibilite_enum"), nullable=False, default="disponible")
    commentaire_disponibilite = Column(String(255), nullable=True)  # Pour spécifier "autres"
    def total_parcouru(self):
            from application.models.tournee import Tournee
            session = SessionLocal()
            """ Calcule le total des kilomètres parcourus par le conducteur """
            total = session.query(func.sum(Tournee.km_parcouru)).filter(Tournee.id_conducteur == self.id_conducteur).scalar()
            return total or 0  # Retourne 0 si aucune donnée n'existe
    def affecter_a_tournee(self, id_commande, objectif, lieu_depart, destination, itineraire, date_heure_depart):
        from application.models.tournee import Tournee
        """ Affecte le conducteur à une tournée """
        session = SessionLocal()
        nouvelle_tournee = Tournee(
            id_conducteur=self.id_conducteur,
            id_commande=id_commande,
            objectif=objectif,
            lieu_depart=lieu_depart,
            destination=destination,
            itineraire=itineraire,
            date_heure_depart=date_heure_depart
        )
        session.add(nouvelle_tournee)
        session.commit()
        return nouvelle_tournee
    
    def affecter_a_vehicule(self, immatriculation):
        from application.models.vehicule import Vehicule
        session = SessionLocal()
        """ Affecte le conducteur à un camion """
        camion = session.query(Vehicule).filter(Vehicule.immatriculation == immatriculation).first()
        if camion is None:
            raise ValueError("Le camion spécifié n'existe pas.")
        return f"Le conducteur {self.nom} {self.prenom} est affecté au camion {camion.immatriculation}."
