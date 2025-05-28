from sqlalchemy import Column, String, Float, Enum, Date, func
from sqlalchemy.orm import relationship
from application.database import Base
from application.database import SessionLocal
from datetime import date

class Vehicule(Base):
    __tablename__ = "vehicules"  # Ajoute cette ligne
    table_args = {"extend_existing": True}  

    immatriculation = Column(String(255), primary_key=True)
    numero_chassis = Column(String(255))
    numero_interne = Column(String(255))
    marque_modele = Column(String(255))
    type_vehicule = Column(String(255))
    capacite_tonne = Column(Float)
    capacite_volume = Column(Float)
    etat = Column(Enum("Disponible", "En panne", "En service", name="etat_vehicule_enum"))

    def est_disponible(self):
        """ Vérifie si le véhicule est disponible aujourd'hui """
        if self.etat in ["En panne", "En service"]:
            return False

        aujourd_hui = date.today()
        session = SessionLocal()

        try:
            # Importer localement pour éviter les références circulaires
            from application.models.tournee import Tournee
            from application.models.affectation import Affectation

            # Vérifier les tournées du jour
            tournee_en_cours = (
                session.query(Tournee)
                .filter(
                    Tournee.immatriculation_vehicule == self.immatriculation,
                    func.date(Tournee.date_heure_depart) == aujourd_hui  # Extraction correcte de la date
                )
                .first()
            )
            if tournee_en_cours:
                return False

            # Vérifier les affectations du jour
            affectation_en_cours = (
                session.query(Affectation)
                .filter(
                    Affectation.immatriculation_vehicule == self.immatriculation,
                    Affectation.date_affectation == aujourd_hui
                )
                .first()
            )
            if affectation_en_cours:
                return False

            return True
        finally:
            session.close()

    def calculer_total_parcouru(self, session):
        """ Calcule la distance totale parcourue par le véhicule en utilisant une session existante """
        from application.models.tournee import Tournee  # Import local pour éviter les références circulaires

        # Calcul de la somme des kilomètres parcourus dans toutes les tournées
        total_km = session.query(func.sum(Tournee.km_parcouru)).filter(
            Tournee.immatriculation_vehicule == self.immatriculation
        ).scalar()

        # Si aucune tournée n'a été trouvée, retourne 0
        return total_km or 0
    def affecter_a_tournee(self, session, id_conducteur, id_commande, objectif, lieu_depart, destination, itineraire, date_heure_depart):
        """ Affecte le véhicule à une nouvelle tournée si disponible """
        if not self.est_disponible():
            raise ValueError(f"Le véhicule {self.immatriculation} n'est pas disponible.")

        try:
            from application.models.tournee import Tournee

            nouvelle_tournee = Tournee(
                id_conducteur=id_conducteur,
                immatriculation_vehicule=self.immatriculation,
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

        except SQLAlchemyError as e: # type: ignore
            session.rollback()
            raise RuntimeError(f"Erreur lors de l'affectation du véhicule : {str(e)}")
