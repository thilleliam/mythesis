from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import des classes nécessaires
from application.models.tournee import Tournee
from application.config import Base

def test_calculer_duree():
    # Créer une connexion à une base de données en mémoire pour les tests
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    
    # Créer une session
    with SessionLocal() as session:
        try:
            # Créer une instance de Tournee avec des dates
            # Cas 1: Durée de moins de 8 heures
            now = datetime.now()
            tournee1 = Tournee(
                id_conducteur="33345",
                immatriculation_vehicule="vvv",
                id_commande=1,
                objectif="Test",
                lieu_depart="Départ Test",
                destination="Destination Test",
                date_heure_depart=now,
                date_heure_arrivee=now + timedelta(hours=5)
            )
            
            # Vérifier le calcul de la durée pour moins de 8 heures
            duree1 = tournee1.calculer_duree()
            print(f"Durée calculée (moins de 8h): {duree1}")
            assert "heures" in duree1
            assert float(duree1.split()[0]) == 5.0
            
            # Cas 2: Durée de plus de 8 heures
            tournee2 = Tournee(
                id_conducteur="COND001",
                immatriculation_vehicule="3",
                id_commande=1,
                objectif="Test longue durée",
                lieu_depart="Départ Test",
                destination="Destination Test",
                date_heure_depart=now,
                date_heure_arrivee=now + timedelta(hours=20)
            )
            
            # Vérifier le calcul de la durée pour plus de 8 heures
            duree2 = tournee2.calculer_duree()
            print(f"Durée calculée (plus de 8h): {duree2}")
            assert "jours" in duree2
            assert float(duree2.split()[0]) == 2.5
            
            # Cas 3: Dates manquantes
            tournee3 = Tournee(
                id_conducteur="COND001",
                immatriculation_vehicule="vvv",
                id_commande=1,
                objectif="Test sans dates",
                lieu_depart="Départ Test",
                destination="Destination Test"
            )
            
            # Vérifier le calcul de la durée quand les dates sont manquantes
            duree3 = tournee3.calculer_duree()
            print(f"Durée calculée (dates manquantes): {duree3}")
            assert duree3 == "Durée inconnue"
            
            print("Tous les tests ont réussi!")
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Erreur lors du test: {str(e)}")
            return False

if __name__ == "__main__":
    # Exécuter le test
    resultat = test_calculer_duree()
    print(f"Résultat du test: {'Succès' if resultat else 'Échec'}")