from datetime import datetime
from sqlalchemy.orm import Session
from application.models import (
    Chantier, Equipement, Commande, Conducteur, Vehicule, Tournee, Affectation, EtapeRotation
)
from application.database import SessionLocal
from sqlalchemy.orm import configure_mappers

configure_mappers()

# Utiliser une session avec un contexte pour garantir une bonne fermeture
with SessionLocal() as session:
    vehicule = session.query(Vehicule).filter_by(immatriculation="DEF456").first()
    
    if vehicule:
        distance = vehicule.calculer_total_parcouru(session)
        print(f"Distance totale parcourue : {distance} km")