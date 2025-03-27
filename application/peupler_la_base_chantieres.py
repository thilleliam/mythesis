from sqlalchemy.orm import sessionmaker
from application.models import Chantier
from application.database import engine

# Connexion à la base de données
Session = sessionmaker(bind=engine)
session = Session()

# Données des chantiers
chantiers_data = [
    {"id_client": "EGS 60", "localisation": "Hassi R'Mel - Laghouat", "latitude": 33.1, "longitude": 3.2, "distanceAllerGoudron": 393, "distanceAllerPiste": 72, "temps_aller": 2},
    {"id_client": "EGS 120", "localisation": "TFT - OHANET", "latitude": 32.9, "longitude": 5.7, "distanceAllerGoudron": 603, "distanceAllerPiste": 1, "temps_aller": 2},
    {"id_client": "EGS 150", "localisation": "BIR LAHRACHE (G: 860 Km - P: 04 Km)", "latitude": 34.2, "longitude": 2.5, "distanceAllerGoudron": 1155, "distanceAllerPiste": 7, "temps_aller": 2},
    {"id_client": "EGS 170", "localisation": "Nouveau camp - Zone Sbaa (G: 170 km - P: ...)", "latitude": 32.5, "longitude": 3.0, "distanceAllerGoudron": 232, "distanceAllerPiste": 80, "temps_aller": 1},
    {"id_client": "EGS 190", "localisation": "Tinirkouk - W. Adrar", "latitude": 28.9, "longitude": -1.3, "distanceAllerGoudron": 961, "distanceAllerPiste": 75, "temps_aller": 2},
]

try:
    # Ajouter les chantiers à la base de données
    chantiers = [Chantier(**chantier) for chantier in chantiers_data]
    session.bulk_save_objects(chantiers)
    
    # Appliquer les modifications
    session.commit()
    
    print(f"Mise à jour terminée : {len(chantiers_data)} chantiers ajoutés.")
except Exception as e:
    session.rollback()
    print(f"Erreur lors de l'ajout des chantiers : {e}")
finally:
    session.close() 
 
