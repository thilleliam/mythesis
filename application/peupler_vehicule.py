from sqlalchemy.orm import sessionmaker
import random
from application.models.vehicule import Vehicule
from application.database import engine

# Connexion à la base de données
Session = sessionmaker(bind=engine)
session = Session()

# Types de véhicules disponibles
types_vehicules = [
    "Porte-engin", 
    "Semi-remorque simple", 
    "Plateau 6×2", 
    "Semi-remorque Triple", 
    "Camions plateaux 6×6", 
    "Camions plateaux 4×2"
]

# Marques de véhicules pour la génération aléatoire
marques_modeles = [
    "Volvo FH16", 
    "Scania R500", 
    "Mercedes Actros", 
    "MAN TGX", 
    "Renault T High", 
    "DAF XF", 
    "Iveco S-Way", 
    "Kenworth W990", 
    "Peterbilt 389",
    "Freightliner Cascadia"
]

# Fonction pour générer une immatriculation aléatoire
def generer_immatriculation():
    numero = random.randint(10000, 99999)
    wilaya = random.randint(1, 48)
    return f"{numero}-{wilaya:02d}"

# Fonction pour générer un numéro de châssis aléatoire
def generer_numero_chassis():
    chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"  # Sans I, O et Q pour éviter la confusion
    return ''.join(random.choice(chars) for _ in range(17))

# Fonction pour générer un numéro interne aléatoire
def generer_numero_interne():
    return f"VEH-{random.randint(1000, 9999)}"

# Capacités typiques par type de véhicule (en tonnes et m³)
capacites_par_type = {
    "Porte-engin": (25, 0),  # Capacité en tonnes, pas de volume spécifique
    "Semi-remorque simple": (24, 90),
    "Plateau 6×2": (15, 45),
    "Semi-remorque Triple": (36, 120),
    "Camions plateaux 6×6": (20, 60),
    "Camions plateaux 4×2": (10, 30)
}

# Création des données pour 20 véhicules
vehicules_data = []
for i in range(20):
    # Sélection aléatoire du type de véhicule
    type_vehicule = random.choice(types_vehicules)
    
    # Récupération des capacités typiques pour ce type
    capacite_tonne_base, capacite_volume_base = capacites_par_type[type_vehicule]
    
    # Ajout d'une légère variation aux capacités
    capacite_tonne = round(capacite_tonne_base * (0.9 + random.random() * 0.2), 1)  # ±10%
    capacite_volume = round(capacite_volume_base * (0.9 + random.random() * 0.2), 1) if capacite_volume_base > 0 else 0
    
    vehicule = {
        "immatriculation": generer_immatriculation(),
        "numero_chassis": generer_numero_chassis(),
        "numero_interne": generer_numero_interne(),
        "marque_modele": random.choice(marques_modeles),
        "type_vehicule": type_vehicule,
        "capacite_tonne": capacite_tonne,
        "capacite_volume": capacite_volume,
        "etat": "Disponible"  # Tous disponibles comme demandé
    }
    
    vehicules_data.append(vehicule)

try:
    # Ajouter les véhicules à la base de données
    vehicules = [Vehicule(**vehicule) for vehicule in vehicules_data]
    session.bulk_save_objects(vehicules)
    
    # Appliquer les modifications
    session.commit()
    
    print(f"Mise à jour terminée : {len(vehicules_data)} véhicules ajoutés.")
    
    # Afficher les détails des véhicules créés
    print("\nDétails des véhicules créés:")
    for v in vehicules_data:
        print(f"Immatriculation: {v['immatriculation']}, Type: {v['type_vehicule']}, Modèle: {v['marque_modele']}")
    
    # Afficher la répartition par type
    types_count = {}
    for v in vehicules_data:
        if v['type_vehicule'] not in types_count:
            types_count[v['type_vehicule']] = 0
        types_count[v['type_vehicule']] += 1
    
    print("\nRépartition par type de véhicule:")
    for type_v, count in types_count.items():
        print(f"{type_v}: {count} véhicule(s)")
    
except Exception as e:
    session.rollback()
    print(f"Erreur lors de l'ajout des véhicules : {e}")
finally:
    session.close()