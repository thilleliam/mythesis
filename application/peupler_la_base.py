from sqlalchemy.orm import sessionmaker
from application.models import Vehicule
from application.database import engine

# Dictionnaire des capacités estimées
capacites_vehicules = {
    "Tracteur (6X4) Mercedes - Année 2023": (35, None),
    "Tracteur (6X6) Iveco - Année 2008": (35, None),
    "Tracteur (6X6) (Astra) - Année 2012": (40, None),
    "Tracteur (6X6) (Astra) - Année 2016": (40, None),
    "Tracteur (6X4) - Fiat Année 2008": (35, None),
    "Camions Plateaux (6X6) à Grue": (20, None),
    "Camions Plateaux (4X2)": (7, None),
    "Camions Plateaux (6X6)": (12, None),
    "Camions Ateliers (6X6)": (None, None),
    "Camion Plateau 10 tonnes (4X2) - (Sonacom)": (10, None),
    "Camion Plateau 10 tonnes (4X2) - Ouled Fayet - FIAT": (10, None),
    "Camion Plateau 10 tonnes (4X2) - Ouled Fayet - RENAULT": (10, None),
    "Camion 2,5 tonnes à Benne (4X2)": (2.5, 3),
    "Camions Frigo (6X6)": (7, 25),
    "Camion Citerne à Eau (4X2)": (8, 8000),
    "Camion Citerne (Hydro cureur)": (12, 12000),
    "Camion Citerne Astra (Hydro cureur Neuf)": (12, 18000)
}

# Connexion à la base de données
Session = sessionmaker(bind=engine)
session = Session()

# Récupérer tous les véhicules et mettre à jour leurs capacités
vehicules = session.query(Vehicule).all()

for vehicule in vehicules:
    if vehicule.type_vehicule in capacites_vehicules:
        vehicule.capacite_tonne, vehicule.capacite_volume = capacites_vehicules[vehicule.type_vehicule]

# Appliquer les modifications
session.commit()
session.close()

print("Mise à jour des capacités terminée.")
