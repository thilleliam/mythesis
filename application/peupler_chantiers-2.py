from sqlalchemy.orm import sessionmaker
from application.models import Chantier
from application.database import engine

# Connexion à la base de données
Session = sessionmaker(bind=engine)
session = Session()

# Données des chantiers
chantiers_data = [
    
    {"id_client": "EGS 210", "localisation": "El Oued", "latitude": 33.35, "longitude": 6.85, "distanceAllerGoudron": 290, "distanceAllerPiste": 0, "temps_aller": 1},
    {"id_client": "EGS 220", "localisation": "BEZIM DAHRAOUI", "latitude": 32.85, "longitude": 5.65, "distanceAllerGoudron": 15, "distanceAllerPiste": 0, "temps_aller": 0.5},
    {"id_client": "EGS 250", "localisation": "El Menia", "latitude": 30.57, "longitude": 2.88, "distanceAllerGoudron": 475, "distanceAllerPiste": 65, "temps_aller": 1},
    {"id_client": "EGS 260", "localisation": "Hassi El Fehal - El Menia", "latitude": 30.47, "longitude": 3.23, "distanceAllerGoudron": 343, "distanceAllerPiste": 3, "temps_aller": 1},
    {"id_client": "EGS 270", "localisation": "HASSI AGRAB", "latitude": 29.15, "longitude": -1.45, "distanceAllerGoudron": 94, "distanceAllerPiste": 2, "temps_aller": 0.5}


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
 
