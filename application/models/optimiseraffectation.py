from pulp import LpMaximize, LpMinimize, LpProblem, LpStatus, lpSum, LpVariable, LpBinary
import pandas as pd
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy.inspection import inspect
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import text

import logging

from application.database import engine
from application.models.chantiers import Chantier
from application.models.vehicule import Vehicule
from application.models.transferer_equipement import TransfererEquipement

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='vehicle_assignment.log'
)
logger = logging.getLogger('vehicle_assignment')

# Configuration des mappeurs SQLAlchemy
configure_mappers()

def get_colonnes_semaine_transferer_equipement():
    """
    Retourne dynamiquement la liste des colonnes semaine dans TransfererEquipement
    Exemple : ['12_semaines_avant_la_fin_de_l\'ancien_projet', ..., '0_semaines_avant_la_fin_de_l\'ancien_projet']
    """
    colonnes = inspect(TransfererEquipement).columns
    colonnes_semaine = [col.name for col in colonnes if "semaines_avant_la_fin_de_l'ancien_projet" in col.name]
    
    # Trier dans l'ordre décroissant (de la semaine 12 à 0)
    colonnes_semaine.sort(key=lambda x: int(x.split('_')[0]), reverse=True)
    
    return colonnes_semaine

def get_equipements_a_transferer(session, semaine_actuelle=None):
    """
    Version finale corrigée
    """
    # Mapping correct des semaines
    semaine_to_column = {
        0: 'zero_semaines_avant',
        1: 'un_semaines_avant',
        2: 'deux_semaines_avant',
        3: 'trois_semaines_avant',
        4: 'quatre_semaines_avant',
        5: 'cinq_semaines_avant',
        6: 'six_semaines_avant',
        7: 'sept_semaines_avant',
        8: 'huit_semaines_avant',
        9: 'neuf_semaines_avant',
        10: 'dix_semaines_avant',
        11: 'onze_semaines_avant',
        12: 'douze_semaines_avant'
    }

    if semaine_actuelle is None:
        # Chercher dans toutes les semaines
        equipements = []
        for semaine, col_name in semaine_to_column.items():
            column_attr = getattr(TransfererEquipement, col_name)
            transferts = session.query(TransfererEquipement).filter(
                column_attr.isnot(None),
                column_attr > 0
            ).all()
            
            for transfert in transferts:
                quantite = getattr(transfert, col_name)
                for i in range(int(quantite)):
                    equipements.append({
                        'id': f"{transfert.id}_{semaine}_{i}",
                        'designation': transfert.designation_equipement,
                        'id_client': transfert.id_client,
                        'modalite_transport': transfert.modalite_transport,
                        'semaine': semaine
                    })
        return equipements
    
    # Vérification de la semaine demandée
    if semaine_actuelle not in semaine_to_column:
        logger.error(f"Semaine {semaine_actuelle} invalide. Doit être entre 0 et 12")
        return []

    column_name = semaine_to_column[semaine_actuelle]
    logger.info(f"Recherche des équipements pour la semaine {semaine_actuelle} (colonne: {column_name})")

    try:
        column_attr = getattr(TransfererEquipement, column_name)
        transferts = session.query(TransfererEquipement).filter(
            column_attr.isnot(None),
            column_attr > 0
        ).all()

        equipements_a_transferer = []
        
        for transfert in transferts:
            quantite = getattr(transfert, column_name)
            for i in range(int(quantite)):
                equipements_a_transferer.append({
                    'id': f"{transfert.id}_{i}",
                    'designation': transfert.designation_equipement,
                    'id_client': transfert.id_client,
                    'modalite_transport': transfert.modalite_transport,
                    'semaine': semaine_actuelle
                })

        logger.info(f"Nombre d'équipements trouvés: {len(equipements_a_transferer)}")
        return equipements_a_transferer

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des équipements: {str(e)}", exc_info=True)
        return []

def solve_vehicle_assignment(semaine_actuelle=None):
    """
    Version adaptée pour interpréter la matrice correctement comme une matrice de capacités
    """
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Récupération des données de base
        chantiers = session.query(Chantier).all()
        vehicules = session.query(Vehicule).filter(Vehicule.etat == "Disponible").all()
        
        # Récupération des équipements (toutes semaines si non spécifié)
        equipements_a_transferer = get_equipements_a_transferer(session, semaine_actuelle)
        
        if not equipements_a_transferer:
            # Debug: afficher les semaines qui ont des données
            debug_info = {}
            for semaine in range(13):
                col_name = f"{semaine}_semaines_avant_la_fin_de_l'ancien_projet"
                count = session.query(TransfererEquipement).filter(
                    getattr(TransfererEquipement, col_name) > 0
                ).count()
                debug_info[semaine] = count
            
            return {
                "status": "No Equipment",
                "message": f"Aucun équipement à transférer pour la semaine {semaine_actuelle}",
                "debug": debug_info,
                "affectations": [],
                "vehicules_utilises": []
            }
            
        if not vehicules:
            return {
                "status": "No Vehicles",
                "message": "Aucun véhicule disponible pour le transport",
                "affectations": [],
                "vehicules_utilises": []
            }
        
        # 2. Données pour le modèle
        # Types de véhicules disponibles
        types_vehicules = [
            "Porte-engin", "Semi-remorque simple", "Plateau 6×2", 
            "Semi-remorque Triple", "Camions plateaux 6×6", "Camions plateaux 4×2"
        ]
        # Normaliser les types dans le tableau de référence (majuscules/minuscules, espaces, etc.)
        types_vehicules_normalized = [t.lower().strip() for t in types_vehicules]

                
        # Dictionnaire pour mapper les désignations d'équipements à leur indice dans la matrice de capacités
        equipement_designation_to_index = {
            "baraque": 0,                      # E1 - Excavateur
            "Baraque (Unité)": 1,              # E2 - Compresseur
            "Baraque (Unité)": 2,              # E3 - Chargeuse
            "Tente (Unité)": 3,                # E4 - Bull
            "Clim-Humidificateur (Unité)": 4,  # E5 - Niveleuse
            "Groupe électrogène": 5,           # E6 - Groupe électrogène
            "Module bureau": 6,                # E7 - Module bureau
            "Rouleau compacteur": 7,           # E8 - Rouleau compacteur
            "Camion-citerne": 8,               # E9 - Camion-citerne
            "Foreuse": 9,                      # E10 - Foreuse
            "Tombereau": 10,                   # E11 - Tombereau
            "Grue": 11,                        # E12 - Grue
            "Tentes": 12,                      # E13 - Tentes
            "Éclairage": 13,                   # E14 - Éclairage
            "Outillage": 14,                   # E15 - Outillage
            "Matériaux de construction": 15,   # E16 - Matériaux de construction
            "Pièces détachées": 16,            # E17 - Pièces détachées
            "Carburant": 17,                   # E18 - Carburant
            "Conteneur": 18,                   # E19 - Conteneur
            "Bétonnière": 19,                  # E20 - Bétonnière
            "Échafaudage": 20,                 # E21 - Échafaudage
            "Concasseur": 21,                  # E22 - Concasseur
            "Treuil": 22,                      # E23 - Treuil
            "Pompe à béton": 23,               # E24 - Pompe à béton
            "Échelle": 24,                     # E25 - Échelle
            "Scie à béton": 25,                # E26 - Scie à béton
            "Perceuse industrielle": 26        # E27 - Perceuse industrielle
        }
        
        # Matrice de capacités d'équipements par type de véhicule
        # Chaque ligne correspond à un équipement, chaque colonne à un type de véhicule
        # Les valeurs indiquent combien d'unités de cet équipement peut transporter chaque type de véhicule
        capacites_matrix = [
            # Porte-engin, Semi-remorque simple, Plateau 6×2, Semi-remorque Triple, Camions plateaux 6×6, Camions plateaux 4×2
            [1, 1, 0, 0, 0, 0],  # E1 - Excavateur
            [0, 0, 1, 3, 0, 0],  # E2 - Compresseur
            [0, 1, 0, 0, 1, 1],  # E3 - Chargeuse
            [0, 1, 2, 6, 0, 0],  # E4 - Bull
            [0, 1, 1, 3, 0, 0],  # E5 - Niveleuse
            [0, 50, 24, 72, 0, 0],  # E6 - Groupe électrogène
            [0, 100, 30, 90, 0, 0],  # E7 - Module bureau
            [1, 0, 0, 0, 0, 0],  # E8 - Rouleau compacteur
            [1, 0, 0, 0, 0, 0],  # E9 - Camion-citerne
            [2, 2, 0, 0, 0, 0],  # E10 - Foreuse
            [0, 0, 1, 3, 0, 0],  # E11 - Tombereau
            [1, 0, 0, 0, 0, 0],  # E12 - Grue
            [0, 40, 8, 24, 0, 0],  # E13 - Tentes
            [0, 14, 8, 24, 0, 0],  # E14 - Éclairage
            [0, 4, 8, 24, 0, 0],  # E15 - Outillage
            [0, 120, 8, 24, 0, 0],  # E16 - Matériaux de construction
            [0, 20, 8, 24, 0, 0],  # E17 - Pièces détachées
            [0, 20, 8, 24, 0, 0],  # E18 - Carburant
            [0, 1, 1, 3, 0, 0],  # E19 - Conteneur
            [1, 0, 0, 0, 0, 0],  # E20 - Bétonnière
            [2, 2, 0, 0, 0, 0],  # E21 - Échafaudage
            [1, 1, 0, 0, 0, 0],  # E22 - Concasseur
            [0, 10, 4, 12, 0, 0],  # E23 - Treuil
            [0, 10, 4, 12, 0, 0],  # E24 - Pompe à béton
            [0, 3, 1.5, 4.5, 0, 0],  # E25 - Échelle
            [0, 1.5, 0.7, 2.1, 0, 0],  # E26 - Scie à béton
            [0, 5, 2.5, 7.5, 0, 0]  # E27 - Perceuse industrielle
        ]
        
        # 3. Création du modèle PuLP
        model = LpProblem(name="affectation_vehicules", sense=LpMinimize)
        
        # Indices
        I = range(len(equipements_a_transferer))  # Équipements à transférer
        J = range(len(vehicules))                 # Véhicules disponibles
        
        if not I:
            logger.warning("Aucun équipement à transférer trouvé")
            return {
                "status": "No Equipment",
                "message": "Aucun équipement à transférer pour cette semaine",
                "affectations": [],
                "vehicules_utilises": []
            }
        
        # Variables de décision
        x = {}  # x[i][j] = 1 si l'équipement i est affecté au véhicule j
        for i in I:
            for j in J:
                x[i, j] = LpVariable(f"x_{i}_{j}", cat=LpBinary)
        
        y = {}  # y[j] = 1 si le véhicule j est utilisé
        for j in J:
            y[j] = LpVariable(f"y_{j}", cat=LpBinary)
        
        # Fonction objectif: minimiser le nombre de véhicules utilisés
        model += lpSum(y[j] for j in J)
        
        # Contrainte 1: Chaque équipement est affecté à un seul véhicule au maximum
        for i in I:
            model += lpSum(x[i, j] for j in J) <= 1, f"equipment_{i}_assignment"
        
        # Contrainte 2: Capacités des véhicules
        # Pour chaque type d'équipement et chaque véhicule, vérifier que le nombre d'unités
        # ne dépasse pas la capacité du véhicule pour ce type d'équipement
        
        # Regrouper les équipements par type
        equipements_par_type = {}
        for i in I:
            designation = equipements_a_transferer[i]['designation']
            if designation in equipement_designation_to_index:
                type_index = equipement_designation_to_index[designation]
                if type_index not in equipements_par_type:
                    equipements_par_type[type_index] = []
                equipements_par_type[type_index].append(i)
        
        # Pour chaque type de véhicule et chaque type d'équipement, appliquer la contrainte de capacité
        for j in J:
            type_vehicule = vehicules[j].type_vehicule
            if type_vehicule in types_vehicules:
                type_vehicule_index = types_vehicules.index(type_vehicule)
                
                for type_equip_index, equips in equipements_par_type.items():
                    capacite = capacites_matrix[type_equip_index][type_vehicule_index]
                    
                    # Si la capacité est 0, le véhicule ne peut pas transporter ce type d'équipement
                    if capacite == 0:
                        for i in equips:
                            model += x[i, j] == 0, f"incompatible_equip_{i}_vehicle_{j}"
                    else:
                        # La somme des équipements de ce type ne doit pas dépasser la capacité
                        model += (lpSum(x[i, j] for i in equips) <= capacite * y[j], 
                                f"capacity_{type_equip_index}_vehicle_{j}")
        
        # Contrainte 3: Activation d'un véhicule
        for i in I:
            for j in J:
                model += x[i, j] <= y[j], f"vehicle_{j}_activation_for_equipment_{i}"
        
        # Contrainte 4: Distance maximale par jour (400 km par exemple)
        D_max = 400  # Distance maximale en km par jour
        
        # Calculer les distances pour chaque destination client
        distances_clients = {}
        for client_id in set(e['id_client'] for e in equipements_a_transferer):
            chantier = next((c for c in chantiers if c.id_client == client_id), None)
            if chantier:
                distance_totale = (chantier.distanceAllerGoudron or 0) + (chantier.distanceAllerPiste or 0)
                distances_clients[client_id] = distance_totale
        
        # Appliquer les contraintes de distance pour chaque véhicule
        for j in J:
            distance_totale_vehicule = lpSum(
                distances_clients.get(equipements_a_transferer[i]['id_client'], 0) * x[i, j]
                for i in I
            )
            model += distance_totale_vehicule <= D_max * y[j], f"vehicle_{j}_max_distance"
        
        
        # 4. Résolution du modèle
        solver_status = model.solve()
        
        # 5. Analyse des résultats
        resultat = {
            "status": LpStatus[model.status],
            "objectif": model.objective.value() if model.status == 1 else None,
            "affectations": [],
            "vehicules_utilises": [],
            "equipements_non_affectes": []
        }
        
        if model.status == 1:  # Optimal
            logger.info("Solution optimale trouvée")
            
            # Parcourir les affectations
            for i in I:
                equipement_affecte = False
                for j in J:
                    if x[i, j].value() == 1:
                        equipement_affecte = True
                        resultat["affectations"].append({
                            "equipement": equipements_a_transferer[i]['designation'],
                            "id_equipement": equipements_a_transferer[i]['id'],
                            "id_client": equipements_a_transferer[i]['id_client'],
                            "vehicule": vehicules[j].immatriculation,
                            "type_vehicule": vehicules[j].type_vehicule
                        })
                
                # Identifier les équipements non affectés
                if not equipement_affecte:
                    resultat["equipements_non_affectes"].append({
                        "equipement": equipements_a_transferer[i]['designation'],
                        "id_equipement": equipements_a_transferer[i]['id'],
                        "id_client": equipements_a_transferer[i]['id_client']
                    })
            
            # Parcourir les véhicules utilisés
            for j in J:
                if y[j].value() == 1:
                    type_vehicule = vehicules[j].type_vehicule
                    if type_vehicule in types_vehicules:
                        type_vehicule_index = types_vehicules.index(type_vehicule)
                        
                        # Calculer le taux d'utilisation pour chaque type d'équipement dans ce véhicule
                        equipements_assignes = {}
                        for i in I:
                            if x[i, j].value() == 1:
                                designation = equipements_a_transferer[i]['designation']
                                if designation in equipement_designation_to_index:
                                    type_equip_index = equipement_designation_to_index[designation]
                                    if type_equip_index not in equipements_assignes:
                                        equipements_assignes[type_equip_index] = 0
                                    equipements_assignes[type_equip_index] += 1
                        
                        # Calculer le taux d'occupation global du véhicule
                        taux_occupation_total = 0
                        capacite_totale = 0
                        
                        for type_equip_index, quantite in equipements_assignes.items():
                            capacite_max = capacites_matrix[type_equip_index][type_vehicule_index]
                            if capacite_max > 0:  # Éviter division par zéro
                                taux_occupation_total += quantite / capacite_max
                                capacite_totale += 1
                        
                        # Taux d'occupation moyen (sur tous les types d'équipements compatibles)
                        taux_occupation = (taux_occupation_total / capacite_totale * 100) if capacite_totale > 0 else 0
                        
                        # Calculer la distance totale parcourue par ce véhicule
                        distance_totale = sum(
                            distances_clients.get(equipements_a_transferer[i]['id_client'], 0)
                            for i in I if x[i, j].value() == 1
                        )
                        
                        resultat["vehicules_utilises"].append({
                            "immatriculation": vehicules[j].immatriculation,
                            "type": vehicules[j].type_vehicule,
                            "taux_occupation": round(taux_occupation, 2),
                            "distance_totale": distance_totale,
                            "equipements": [equipements_a_transferer[i]['designation'] 
                                           for i in I if x[i, j].value() == 1]
                        })
                        resultat["vehicules_disponibles"] = [{
                            "immatriculation": v.immatriculation,
                            "type": v.type_vehicule
                        } for v in vehicules]

                        resultat["statistiques_vehicules"] = {
                            "total_disponibles": len(vehicules),
                            "types_disponibles": {v.type_vehicule: sum(1 for veh in vehicules if veh.type_vehicule == v.type_vehicule) for v in vehicules}
                        }

                return resultat
        else:
            logger.warning(f"Pas de solution optimale trouvée. Statut: {LpStatus[model.status]}")
        
        return resultat
    
    except Exception as e:
        logger.error(f"Erreur lors de l'affectation des véhicules: {str(e)}", exc_info=True)
        return {
            "status": "Error",
            "message": f"Une erreur est survenue: {str(e)}",
            "affectations": [],
            "vehicules_utilises": []
        }
    
    finally:
        session.close()
        
    

def debug_equipements_par_semaine():
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        print("Répartition des équipements par semaine:")
        
        # Mapping correct entre les numéros de semaine et les noms de colonnes dans le modèle
        semaine_to_column = {
            0: 'zero_semaines_avant',
            1: 'un_semaines_avant',
            2: 'deux_semaines_avant',
            3: 'trois_semaines_avant',
            4: 'quatre_semaines_avant',
            5: 'cinq_semaines_avant',
            6: 'six_semaines_avant',
            7: 'sept_semaines_avant',
            8: 'huit_semaines_avant',
            9: 'neuf_semaines_avant',
            10: 'dix_semaines_avant',
            11: 'onze_semaines_avant',
            12: 'douze_semaines_avant'
        }
        
        for semaine, col_name in semaine_to_column.items():
            try:
                column_attr = getattr(TransfererEquipement, col_name)
                equipements = session.query(TransfererEquipement).filter(
                    column_attr.isnot(None),
                    column_attr > 0
                ).all()
                
                print(f"\nSemaine {semaine}:")
                for eq in equipements:
                    qte = getattr(eq, col_name)
                    print(f"  - {eq.designation_equipement}: {qte} unité(s) (ID: {eq.id})")
                    
                if not equipements:
                    print("  Aucun équipement à transférer")
                    
            except Exception as e:
                print(f"Erreur pour la semaine {semaine}: {str(e)}")
                continue
                
    finally:
        session.close()

# Exemple d'utilisation
if __name__ == "__main__":
    resultat = solve_vehicle_assignment(semaine_actuelle=11)
    
    print(f"\nStatut de l'optimisation: {resultat['status']}")

    if resultat['status'] == "Optimal":
        print(f"Nombre de véhicules utilisés: {resultat['objectif']}")
        
        print("\nAffectations des équipements aux véhicules:")
        for affectation in resultat["affectations"]:
            print(f"Équipement '{affectation['equipement']}' → Véhicule {affectation['vehicule']} ({affectation['type_vehicule']})")
        
        print("\nVéhicules utilisés:")
        for vehicule in resultat["vehicules_utilises"]:
            print(f"Véhicule {vehicule['immatriculation']} ({vehicule['type']}):")
            print(f"  Taux d'occupation: {vehicule['taux_occupation']}%")
            print(f"  Distance totale: {vehicule['distance_totale']} km")
            print("  Équipements:")
            for equip in vehicule['equipements']:
                print(f"    - {equip}")
        
        if resultat["equipements_non_affectes"]:
            print("\nÉquipements non affectés:")
            for equip in resultat["equipements_non_affectes"]:
                print(f"  - {equip['equipement']} (ID: {equip['id_equipement']})")
    else:
        print(f"Message: {resultat.get('message', 'Aucun message')}")