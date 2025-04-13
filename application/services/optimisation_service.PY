# Import des modules nécessaires
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Import des classes du projet
from application.models.vehicule import Vehicule  # Remplacez par le chemin réel
from application.models.transferer_equipement import TransfererEquipement  # Remplacez par le chemin réel
from application.models.chantiers import Chantier  # Remplacez par le chemin réel
from application.services.optimisation_service import OptimisationService  # Remplacez par le chemin réel

# Configuration de la base de données en mémoire
DATABASE_URL = "sqlite:///:memory:"  # Base de données SQLite en mémoire
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Création des tables dans la base de données simulée
from application.config import Base  # Importez la classe Base pour créer les tables
Base.metadata.create_all(bind=engine)

# Classe de test
class VerificationOptimisation:
    def __init__(self):
        # Création d'une session SQLAlchemy simulée
        self.db_session = SessionLocal()

        # Insertion de données de test
        self.creer_donnees_test()

    def creer_donnees_test(self):
        """Insère des données de test dans la base de données simulée"""

        # Clients (Chantiers)
        client1 = Chantier(
            id_client="CLIENT123",
            localisation="Site A",
            latitude=48.8566,
            longitude=2.3522,
            nature_terrain="Terrain plat",
            distanceAllerGoudron=100.0,
            distanceAllerPiste=50.0
        )
        client2 = Chantier(
            id_client="CLIENT456",
            localisation="Site B",
            latitude=48.8600,
            longitude=2.3600,
            nature_terrain="Terrain vallonné",
            distanceAllerGoudron=120.0,
            distanceAllerPiste=30.0
        )

        # Véhicules
        vehicule1 = Vehicule(
            immatriculation="VEH001",
            numero_chassis="CHASSIS001",
            marque_modele="Porteur XYZ",
            type_vehicule="porte engin",
            capacite_tonne=10.0,
            capacite_volume=20.0,
            etat="Disponible"
        )
        vehicule2 = Vehicule(
            immatriculation="VEH002",
            numero_chassis="CHASSIS002",
            marque_modele="Semi-remorque ABC",
            type_vehicule="semi remorque simple",
            capacite_tonne=15.0,
            capacite_volume=30.0,
            etat="Disponible"
        )

        # Transferts d'équipements
        transfert1 = TransfererEquipement(
            designation_equipement="Équipement E1",
            modalite_transport="Route",
            total_equipements=5,
            id_client="CLIENT123",
            cinq_semaines_avant_la_fin_de_l_ancien_projet=2
        )
        transfert2 = TransfererEquipement(
            designation_equipement="Équipement E5",
            modalite_transport="Route",
            total_equipements=3,
            id_client="CLIENT456",
            cinq_semaines_avant_la_fin_de_l_ancien_projet=1
        )

        # Ajouter les données à la session
        self.db_session.add_all([client1, client2, vehicule1, vehicule2, transfert1, transfert2])
        self.db_session.commit()

    def executer_verification(self):
        """Exécute le processus de vérification complet"""
        print("=== VÉRIFICATION DE L'ALGORITHME D'OPTIMISATION ===")

        # Initialisation du service d'optimisation
        optimisation_service = OptimisationService(self.db_session)

        # Planifier les transferts pour la semaine 5
        numero_semaine = 5
        resultat = optimisation_service.planifier_transferts_semaine(numero_semaine=numero_semaine)

        # Afficher les résultats
        print("\n=== RÉSULTATS DE LA PLANIFICATION ===")
        if resultat["status"] == "Succès":
            print(f"Nombre de véhicules utilisés: {resultat['nombre_vehicules_utilises']}")
            print("Détails des affectations:")
            for affectation in resultat["affectations"]:
                vehicule = affectation["vehicule"]
                print(f"\nVéhicule: {vehicule['immatriculation']} (Type: {vehicule['type']}, Capacité: {vehicule['capacite']} tonnes)")
                print("Équipements affectés:")
                for equip in affectation["equipements"]:
                    print(f"- {equip['nom_equipement']} (ID: {equip['id_equipement']}) - Client: {equip['client_destination']}")
        else:
            print(f"Échec de la planification: {resultat.get('message', 'Raison inconnue')}")

        return resultat


# Exécution de la vérification
if __name__ == "__main__":
    verification = VerificationOptimisation()
    resultat = verification.executer_verification()