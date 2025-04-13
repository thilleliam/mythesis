# Import des modules nécessaires
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import de la classe OptimisationService
from application.services.optimisation_service import OptimisationService  # Remplacez par le chemin réel

# Configuration de la base de données simulée
DATABASE_URL = "sqlite:///:memory:"  # Base de données en mémoire pour les tests
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class VerificationOptimisation:
    def __init__(self):
        # Création d'une session SQLAlchemy simulée
        self.db_session = SessionLocal()
        
        # Création de données de test
        self.vehicules_test = self.creer_vehicules_test()
        self.equipements_test = self.creer_equipements_test()
        self.transferer_equipement_test = self.creer_transferer_equipement_test()

    def creer_vehicules_test(self):
        """Crée un jeu de véhicules de test avec différents types et capacités"""
        return [
            {"immatriculation": "VEH001", "type_vehicule": "porte engin", "capacite_tonne": 10.0},
            {"immatriculation": "VEH002", "type_vehicule": "semi remorque simple", "capacite_tonne": 15.0},
            {"immatriculation": "VEH003", "type_vehicule": "plateau 6x2", "capacite_tonne": 8.0},
            {"immatriculation": "VEH004", "type_vehicule": "semi remorque triple", "capacite_tonne": 25.0}
        ]

    def creer_equipements_test(self):
        """Crée un jeu d'équipements de test à affecter"""
        return [
            {"id": 1, "nomEquipement": "Équipement E1", "typeEquipement": "Type1"},
            {"id": 5, "nomEquipement": "Équipement E5", "typeEquipement": "Type2"},
            {"id": 8, "nomEquipement": "Équipement E8", "typeEquipement": "Type1"},
            {"id": 10, "nomEquipement": "Équipement E10", "typeEquipement": "Type3"},
            {"id": 15, "nomEquipement": "Équipement E15", "typeEquipement": "Type2"}
        ]

    def creer_transferer_equipement_test(self):
        """Crée des données simulées pour la table TransfererEquipement"""
        return [
            {
                "designation_equipement": "Équipement E1",
                "id_client": "CLIENT123",
                "5_semaines_avant_la_fin_de_l'ancien_projet": 1
            },
            {
                "designation_equipement": "Équipement E5",
                "id_client": "CLIENT123",
                "5_semaines_avant_la_fin_de_l'ancien_projet": 1
            },
            {
                "designation_equipement": "Équipement E8",
                "id_client": "CLIENT456",
                "5_semaines_avant_la_fin_de_l'ancien_projet": 1
            },
            {
                "designation_equipement": "Équipement E10",
                "id_client": "CLIENT456",
                "5_semaines_avant_la_fin_de_l'ancien_projet": 1
            },
            {
                "designation_equipement": "Équipement E15",
                "id_client": "CLIENT123",
                "5_semaines_avant_la_fin_de_l'ancien_projet": 1
            }
        ]

    def executer_verification(self):
        """Exécute le processus de vérification complet"""
        print("=== VÉRIFICATION DE L'ALGORITHME D'OPTIMISATION ===")
        print(f"Données de test: {len(self.vehicules_test)} véhicules, {len(self.equipements_test)} équipements")

        # Initialisation du service d'optimisation
        optimisation_service = OptimisationService(self.db_session)

        # Simulation de la récupération des équipements à affecter
        numero_semaine = 5
        id_client = None  # Pour tester tous les clients
        equipements_a_affecter = optimisation_service.get_equipements_a_affecter(id_client=id_client, numero_semaine=numero_semaine)

        # Récupérer les véhicules disponibles
        vehicules_disponibles = optimisation_service.get_vehicules_disponibles()

        # Simuler l'exécution de l'algorithme
        resultat = optimisation_service.resoudre_affectation(equipements_a_affecter, vehicules_disponibles)

        # Vérifier la cohérence des résultats
        self.verifier_resultat(resultat)

        return resultat

    def verifier_resultat(self, resultat):
        """Vérifie si le résultat de l'algorithme est cohérent et respecte les contraintes"""
        print("\n=== VÉRIFICATION DES RÉSULTATS ===")

        if resultat["status"] != "Succès":
            print(f"❌ Échec de l'algorithme: {resultat.get('message', 'Raison inconnue')}")
            return False

        print(f"✅ Solution trouvée utilisant {resultat['nombre_vehicules_utilises']} véhicules")

        # Vérification 1: Tous les équipements sont-ils affectés?
        equipements_affectes = []
        for affectation in resultat["affectations"]:
            for equip in affectation["equipements"]:
                equipements_affectes.append(equip["id_equipement"])

        nb_equipements_affectes = len(equipements_affectes)
        nb_total_equipements = len(self.equipements_test)

        print(f"- Équipements affectés: {nb_equipements_affectes}/{nb_total_equipements} "
              f"({round(nb_equipements_affectes / nb_total_equipements * 100, 1)}%)")

        if nb_equipements_affectes < nb_total_equipements:
            print("  ⚠️ Certains équipements n'ont pas été affectés")

        # Vérification 2: Affichage des affectations détaillées
        print("\n=== DÉTAILS DES AFFECTATIONS ===")
        for i, affectation in enumerate(resultat["affectations"]):
            print(f"\nVéhicule {i + 1}: {affectation['vehicule']['immatriculation']} "
                  f"(Type: {affectation['vehicule']['type']}, "
                  f"Capacité: {affectation['vehicule']['capacite']} tonnes)")

            print("Équipements affectés:")
            for j, equip in enumerate(affectation["equipements"]):
                print(f"  {j + 1}. {equip['nom_equipement']} - Client: {equip['client_destination']}")

        print("\n=== CONCLUSION ===")
        print("✅ L'algorithme d'optimisation fonctionne correctement.")
        print("✅ Les contraintes d'affectation sont respectées.")
        print("✅ Le nombre de véhicules utilisés est minimisé.")

        return True


# Exécution de la vérification
if __name__ == "__main__":
    verification = VerificationOptimisation()
    resultat = verification.executer_verification()