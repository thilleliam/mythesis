from sqlalchemy.orm import sessionmaker
from application.models import Equipement
from application.database import engine

# Connexion à la base de données
Session = sessionmaker(bind=engine)
session = Session()

# Données des équipements avec poids et volumes approximatifs
equipements_data = [
    {"nomEquipement": "Baraque (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 3000, "volume": 15},
    {"nomEquipement": "Baraque (Unité)", "typeEquipement": "Tractable", "quantite": 1, "etat": "Neuf", "poids": 3500, "volume": 18},
    {"nomEquipement": "Conteneur", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 2500, "volume": 12},
    {"nomEquipement": "Magasin (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 1500, "volume": 10},
    {"nomEquipement": "Ravitaillement (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 2000, "volume": 11},
    {"nomEquipement": "Tente (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 250, "volume": 5},
    {"nomEquipement": "Clim-Modificateur (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 100, "volume": 3},
    {"nomEquipement": "levage (Grue ) (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 8000, "volume": 30},
    {"nomEquipement": "levage (Clark) (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 3500, "volume": 15},
    {"nomEquipement": "Réservoir d'eau (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 1500, "volume": 7},
    {"nomEquipement": "Groupe électrogène (Unité)", "typeEquipement": "Tractage", "quantite": 1, "etat": "Bon état", "poids": 3000, "volume": 15},
    {"nomEquipement": "Sondeuse (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 500, "volume": 2},
    {"nomEquipement": "Grappes (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 300, "volume": 2},
    {"nomEquipement": "Câble (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 200, "volume": 1},
    {"nomEquipement": "Bentonite", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 1200, "volume": 6},
    {"nomEquipement": "Piquette Topo", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 100, "volume": 1},
    {"nomEquipement": "Batterie (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 40, "volume": 0.5},
    {"nomEquipement": "Palan soleille (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 500, "volume": 4},
    {"nomEquipement": "Divers matériels", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 200, "volume": 2},
    {"nomEquipement": "Camion en panne (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "En panne", "poids": 15000, "volume": 50},
    {"nomEquipement": "VLTT en panne (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "En panne", "poids": 200, "volume": 2},
    {"nomEquipement": "Citerne Carburant (Unité)", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 5000, "volume": 20},
    {"nomEquipement": "Grillage de clôture du camp", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 800, "volume": 6},
    {"nomEquipement": "La tôle métallique", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Bon état", "poids": 1200, "volume": 7},
    {"nomEquipement": "Lit de camp", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 15, "volume": 1},
    {"nomEquipement": "matelas", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 5, "volume": 0.5},
    {"nomEquipement": "Extincteur", "typeEquipement": "Chargeable", "quantite": 1, "etat": "Neuf", "poids": 10, "volume": 0.2},
]

try:
    # Ajouter les équipements à la base de données
    equipements = [Equipement(**equipement) for equipement in equipements_data]
    session.bulk_save_objects(equipements)
    
    # Appliquer les modifications
    session.commit()
    
    print(f"Mise à jour terminée : {len(equipements_data)} équipements ajoutés.")
except Exception as e:
    session.rollback()
    print(f"Erreur lors de l'ajout des équipements : {e}")
finally:
    session.close()
