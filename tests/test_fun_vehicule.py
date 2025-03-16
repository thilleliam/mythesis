from datetime import datetime 
from sqlalchemy.orm import Session 
from sqlalchemy import func 
from application.database import SessionLocal 
from sqlalchemy.orm import configure_mappers

# Configuration initiale 
configure_mappers() 
import logging 
logging.basicConfig() 
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# Import des classes nécessaires



# Vérifier la distance parcourue du véhicule DEF456 
def verifier_distance_vehicule(immatriculation):
    with SessionLocal() as session:
        try:
            from application.models.vehicule import Vehicule
            vehicule = session.query(Vehicule).filter_by(immatriculation=immatriculation).first()
            if vehicule:
                distance = vehicule.calculer_total_parcouru(session)
                print(f"Distance totale parcourue par {immatriculation}: {distance} km")
                return distance
            else:
                print(f"Véhicule {immatriculation} introuvable.")
                return None
        except Exception as e:
            session.rollback()
            print(f"Erreur lors de la vérification du véhicule {immatriculation}: {str(e)}")
            return None

# Affectation d'une tournée au véhicule 
def affecter_tournee(immatriculation, id_conducteur, id_commande, objectif, lieu_depart,
                     destination, itineraire, date_heure_depart):
    with SessionLocal() as session:
        try:
            from application.models.tournee import Tournee
            vehicule = session.query(Vehicule).filter_by(immatriculation=immatriculation).first()
            if not vehicule:
                print(f"Véhicule {immatriculation} introuvable.")
                return None
                
            # Vérifier si le véhicule est en état de fonctionnement
            if hasattr(vehicule, 'etat') and vehicule.etat not in ["Disponible", "En service"]:
                print(f"Le véhicule {immatriculation} n'est pas disponible (état: {vehicule.etat})")
                return None
                
            tournee = vehicule.affecter_a_tournee(
                session,
                id_conducteur=id_conducteur,
                id_commande=id_commande,
                objectif=objectif,
                lieu_depart=lieu_depart,
                destination=destination,
                itineraire=itineraire,
                date_heure_depart=date_heure_depart
            )
                
            if tournee:
                session.commit()
                session.refresh(tournee)
                print(f"Tournée affectée avec succès: {tournee}")
                return tournee
            else:
                print("Échec de l'affectation: le véhicule n'est pas disponible.")
                return None
                
        except Exception as e:
            session.rollback()
            print(f"Erreur lors de l'affectation de la tournée: {str(e)}")
            return None

# Fonctions pour tester la classe Conducteur
def verifier_total_parcouru_conducteur(id_conducteur):
    """Vérifie le total des kilomètres parcourus par un conducteur"""
    with SessionLocal() as session:
        try:
            from application.models.conducteurs import Conducteur
            conducteur = session.query(Conducteur).filter_by(id_conducteur=id_conducteur).first()
            if conducteur:
                total_km = conducteur.total_parcouru()
                print(f"Distance totale parcourue par le conducteur {conducteur.nom} {conducteur.prenom}: {total_km} km")
                return total_km
            else:
                print(f"Conducteur avec ID {id_conducteur} introuvable.")
                return None
        except Exception as e:
            print(f"Erreur lors de la vérification du kilométrage du conducteur: {str(e)}")
            return None

def affecter_conducteur_a_tournee(id_conducteur, id_commande, objectif, lieu_depart, 
                                destination, itineraire, date_heure_depart):
    """Affecte un conducteur à une nouvelle tournée"""
    with SessionLocal() as session:
        try:
            from application.models.conducteurs import Conducteur
            conducteur = session.query(Conducteur).filter_by(id_conducteur=id_conducteur).first()
            if not conducteur:
                print(f"Conducteur avec ID {id_conducteur} introuvable.")
                return None
            
            if conducteur.disponibilite != "disponible":
                print(f"Le conducteur {conducteur.nom} {conducteur.prenom} n'est pas disponible (statut: {conducteur.disponibilite}).")
                return None
            
            nouvelle_tournee = conducteur.affecter_a_tournee(
                id_commande=id_commande,
                objectif=objectif,
                lieu_depart=lieu_depart,
                destination=destination,
                itineraire=itineraire,
                date_heure_depart=date_heure_depart
            )
            
            print(f"Tournée créée avec succès pour le conducteur {conducteur.nom} {conducteur.prenom}.")
            print(f"Détails: De {nouvelle_tournee.lieu_depart} à {nouvelle_tournee.destination}")
            print(f"Date de départ: {nouvelle_tournee.date_heure_depart}")
            
            return nouvelle_tournee
            
        except Exception as e:
            print(f"Erreur lors de l'affectation du conducteur à une tournée: {str(e)}")
            return None

def affecter_conducteur_a_vehicule(id_conducteur, immatriculation):
    """Affecte un conducteur à un véhicule"""
    with SessionLocal() as session:
        try:
            from application.models.vehicule import Vehicule
            from application.models.conducteurs import Conducteur
            conducteur = session.query(Conducteur).filter_by(id_conducteur=id_conducteur).first()
            if not conducteur:
                print(f"Conducteur avec ID {id_conducteur} introuvable.")
                return None
            
            message = conducteur.affecter_a_vehicule(immatriculation)
            print(message)
            return message
            
        except ValueError as e:
            print(f"Erreur: {str(e)}")
            return None
        except Exception as e:
            print(f"Erreur lors de l'affectation du conducteur au véhicule: {str(e)}")
            return None

# Exécution du code 
if __name__ == "__main__":
    # Code original
    # Vérifier la distance du véhicule DEF456
    verifier_distance_vehicule("DEF456")
    
    # Affecter une tournée au véhicule 3
    date_heure_depart = datetime(2025, 3, 16, 8, 0, 0)
    affecter_tournee(
        immatriculation="3",
        id_conducteur="COND001",
        id_commande=1,
        objectif="Livraison",
        lieu_depart="Entrepôt A",
        destination="Chantier B",
        itineraire="Route X",
        date_heure_depart=date_heure_depart
    )
    
    print("\n--- Tests des fonctions de la classe Conducteur ---")
    
    # Test 1: Vérifier le total parcouru d'un conducteur
    print("\nTest 1: Vérification du kilométrage total parcouru")
    verifier_total_parcouru_conducteur("COND001")
    
    # Test 2: Affecter un conducteur à une tournée
    print("\nTest 2: Affectation d'un conducteur à une tournée")
    date_tournee = datetime(2025, 3, 20, 9, 0, 0)
    affecter_conducteur_a_tournee(
        id_conducteur="COND001",
        id_commande="1",
        objectif="Livraison prioritaire",
        lieu_depart="Paris",
        destination="Bordeaux",
        itineraire="A10",
        date_heure_depart=date_tournee
    )
    
    # Test 3: Affecter un conducteur à un véhicule
    print("\nTest 3: Affectation d'un conducteur à un véhicule")
    affecter_conducteur_a_vehicule("COND001", "vvv")
    
    # Test 4: Vérifier à nouveau le kilométrage après la nouvelle tournée
    print("\nTest 4: Vérification du kilométrage après la nouvelle tournée")
    verifier_total_parcouru_conducteur("COND001")
    
    # Test 5: Essayer d'affecter un conducteur à un véhicule inexistant
    print("\nTest 5: Tentative d'affectation à un véhicule inexistant")
    affecter_conducteur_a_vehicule("COND001", "vvv")