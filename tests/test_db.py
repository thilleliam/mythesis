from datetime import datetime
from sqlalchemy.orm import Session
from application.models import (
    Chantier, Equipement, Commande, Conducteur, Vehicule, Tournee, Affectation, EtapeRotation
)
from application.database import SessionLocal
from sqlalchemy.orm import configure_mappers
configure_mappers()

# Fonctions CRUD pour Chantier
def create_chantier(session: Session, localisation: str, latitude: float, longitude: float, nature_terrain: str, distanceAllerGoudron: float, distanceAllerPiste: float):
    chantier = Chantier(
        localisation=localisation,
        latitude=latitude,
        longitude=longitude,
        nature_terrain=nature_terrain,
        distanceAllerGoudron=distanceAllerGoudron,
        distanceAllerPiste=distanceAllerPiste
    )
    session.add(chantier)
    session.commit()
    session.refresh(chantier)
    return chantier

def get_chantier(session: Session, id_client: int):
    return session.query(Chantier).filter(Chantier.id_client == id_client).first()

def update_chantier(session: Session, id_client: int, **kwargs):
    chantier = session.query(Chantier).filter(Chantier.id_client == id_client).first()
    if chantier:
        for key, value in kwargs.items():
            setattr(chantier, key, value)
        session.commit()
        session.refresh(chantier)
    return chantier

def delete_chantier(session: Session, id_client: int):
    chantier = session.query(Chantier).filter(Chantier.id_client == id_client).first()
    if chantier:
        session.delete(chantier)
        session.commit()

# Fonctions CRUD pour Conducteur avec vérification d'existence
def create_conducteur(session: Session, id_conducteur: str, nom: str, prenom: str, numero_telephone: str, categorie: str):
    # Vérifier si le conducteur existe déjà
    conducteur_existant = get_conducteur(session, id_conducteur)
    if conducteur_existant:
        print(f"Le conducteur {id_conducteur} existe déjà")
        return conducteur_existant
    
    conducteur = Conducteur(
        id_conducteur=id_conducteur,
        nom=nom,
        prenom=prenom,
        numero_telephone=numero_telephone,
        categorie=categorie
    )
    session.add(conducteur)
    session.commit()
    session.refresh(conducteur)
    return conducteur

def get_conducteur(session: Session, id_conducteur: str):
    return session.query(Conducteur).filter(Conducteur.id_conducteur == id_conducteur).first()

# Fonctions CRUD pour Vehicule avec vérification d'existence
def create_vehicule(session: Session, immatriculation: str, numero_chassis: str, numero_interne: str, marque_modele: str, type_vehicule: str, capacite_tonne: float, capacite_volume: float):
    # Vérifier si le véhicule existe déjà
    vehicule_existant = get_vehicule(session, immatriculation)
    if vehicule_existant:
        print(f"Le véhicule {immatriculation} existe déjà")
        return vehicule_existant
    
    vehicule = Vehicule(
        immatriculation=immatriculation,
        numero_chassis=numero_chassis,
        numero_interne=numero_interne,
        marque_modele=marque_modele,
        type_vehicule=type_vehicule,
        capacite_tonne=capacite_tonne,
        capacite_volume=capacite_volume
    )
    session.add(vehicule)
    session.commit()
    session.refresh(vehicule)
    return vehicule

def get_vehicule(session: Session, immatriculation: str):
    return session.query(Vehicule).filter(Vehicule.immatriculation == immatriculation).first()

# Fonctions CRUD pour Commande
# Fonctions CRUD pour Commande
def create_commande(session: Session, id_client: int, date_commande: datetime, nature_service: str, 
                    type_vehicule: str, ID_equipement: int = None, quantite_requise: float = None, 
                    lieu_chargement: str = None, date_livraison: datetime = None, details: str = None):
    commande = Commande(
        id_client=id_client,
        date_commande=date_commande,
        nature_service=nature_service,
        type_vehicule=type_vehicule,
        ID_equipement=ID_equipement,
        quantite_requise=quantite_requise,
        lieu_chargement=lieu_chargement,
        date_livraison=date_livraison
        # Notez que 'details' n'est pas dans le modèle, donc à retirer ou à ajouter dans le modèle
    )
    session.add(commande)
    session.commit()
    session.refresh(commande)
    return commande

def get_commande(session: Session, id_commande: int):
    return session.query(Commande).filter(Commande.id_commande == id_commande).first()

# Fonctions CRUD pour Tournee
def create_tournee(session: Session, id_conducteur: str, immatriculation_vehicule: str, id_commande: int, objectif: str, lieu_depart: str, destination: str, itineraire: str, km_parcouru: float, date_heure_depart: datetime):
    tournee = Tournee(
        id_conducteur=id_conducteur,
        immatriculation_vehicule=immatriculation_vehicule,
        id_commande=id_commande,
        objectif=objectif,
        lieu_depart=lieu_depart,
        destination=destination,
        itineraire=itineraire,
        km_parcouru=km_parcouru,
        date_heure_depart=date_heure_depart
    )
    session.add(tournee)
    session.commit()
    session.refresh(tournee)
    return tournee

def get_tournee(session: Session, id_tournee: int):
    return session.query(Tournee).filter(Tournee.id_tournee == id_tournee).first()

# Fonction pour créer ou récupérer une étape de rotation
def create_etape_rotation(session: Session, id_tournee: int, lieu_chargement: str, lieu_dechargement: str, 
                          date_heure_depart: datetime, date_heure_arrivee: datetime, duree: str, type: str):
    etape = EtapeRotation(
        id_tournee=id_tournee,
        lieu_chargement=lieu_chargement,
        lieu_dechargement=lieu_dechargement,
        date_heure_depart=date_heure_depart,
        date_heure_arrivee=date_heure_arrivee,
        duree=duree,
        type=type
    )
    session.add(etape)
    session.commit()
    session.refresh(etape)
    return etape

# Exemple d'utilisation
if __name__ == "__main__":
    db = SessionLocal()
    
    try:
        print("Début des tests CRUD...")
        
        # Création d'un chantier
        chantier = create_chantier(
            db,
            localisation="Paris",
            latitude=48.8566,
            longitude=2.3522,
            nature_terrain="Urbain",
            distanceAllerGoudron=10.5,
            distanceAllerPiste=5.0
        )
        print(f"Chantier créé ou récupéré : {chantier.id_client}")
        
        # Lecture d'un chantier
        chantier_lu = get_chantier(db, chantier.id_client)
        print(f"Chantier lu : {chantier_lu.localisation}")
        
        # Mise à jour d'un chantier
        chantier_mis_a_jour = update_chantier(db, chantier.id_client, localisation="Lyon")
        print(f"Chantier mis à jour : {chantier_mis_a_jour.localisation}")
        
        # Création ou récupération d'un conducteur
        # Utiliser un ID différent pour éviter les conflits
        conducteur = create_conducteur(
            db,
            id_conducteur="COND002",  # ID modifié
            nom="Martin",
            prenom="Pierre",
            numero_telephone="0123456790",
            categorie="B"
        )
        print(f"Conducteur créé ou récupéré : {conducteur.id_conducteur}")
        
        # Création ou récupération d'un véhicule
        # Utiliser une immatriculation différente pour éviter les conflits
        vehicule = create_vehicule(
            db,
            immatriculation="DEF456",  # Immatriculation modifiée
            numero_chassis="987654321",
            numero_interne="V002",
            marque_modele="Peugeot Partner",
            type_vehicule="Fourgon",
            capacite_tonne=2.5,
            capacite_volume=8.0
        )
        print(f"Véhicule créé ou récupéré : {vehicule.immatriculation}")
        
        # Création d'une commande
        # Création d'une commande
        # Création d'une commande
        # Création d'une commande
        # Création d'une commande
        commande = create_commande(
            db,
            id_client=chantier.id_client,
            date_commande=datetime.now(),
            nature_service="Livraison de matériaux de construction",
            type_vehicule="Fourgon",
            ID_equipement=None,  # ou un ID valide si nécessaire
            quantite_requise=2.0,  # ou une quantité appropriée
            lieu_chargement="Entrepôt Paris",
            date_livraison=datetime.now()  # ou une date future appropriée
        )
        print(f"Commande créée : {commande.id_commande}")
        # Création d'une tournée
        tournee = create_tournee(
            db,
            id_conducteur=conducteur.id_conducteur,
            immatriculation_vehicule=vehicule.immatriculation,
            id_commande=commande.id_commande,
            objectif="Livraison de matériel",
            lieu_depart="Paris",
            destination="Lyon",
            itineraire="A6",
            km_parcouru=450.0,
            date_heure_depart=datetime.now()
        )
        print(f"Tournée créée : {tournee.id_tournee}")
        
        # Création d'une étape de rotation
        etape = create_etape_rotation(
            db,
            id_tournee=tournee.id_tournee,
            lieu_chargement="Entrepôt Paris",
            lieu_dechargement="Dépôt Lyon",
            date_heure_depart=datetime.now(),
            date_heure_arrivee=datetime.now(),
            duree="3h30",
            type="Livraison"
        )
        print(f"Étape de rotation créée : {etape.id_etape}")
        
        print("Tests CRUD terminés avec succès!")
        
    except Exception as e:
        print(f"Erreur : {e}")
        db.rollback()
    finally:
        db.close()