from pulp import LpMinimize, LpProblem, LpVariable, LpStatus, value
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Dict, List, Tuple
import numpy as np
from datetime import datetime

# Import des modèles SQLAlchemy
from application.models.transferer_equipement import SemaineTransfert, TransfererEquipement
from application.models import Vehicule, Equipement, Affectation, Tournee

class OptimisationService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
        # Mapping des types de véhicules pour la matrice d'occupation
        self.types_vehicules = {
            "porte_engin": 0,
            "semi_remorque_simple": 1,
            "plateau_6x2": 2,
            "semi_remorque_triple": 3,
            "camion_plateau_6x6": 4,
            "camion_plateau_4x2": 5
        }
        
        # Récupérer tous les véhicules
        self.tous_vehicules = self.db_session.query(Vehicule).all()
        
        # Calculer le nombre de chaque type de véhicule et stocker les véhicules par type
        self.nombre_par_type = {}
        self.vehicules_par_type = {}
        
        for type_name, index in self.types_vehicules.items():
            # Convertir le format type_name (avec underscores) en format BDD (avec espaces)
            type_db_format = type_name.replace('_', ' ')
            
            # Requête pour obtenir tous les véhicules de ce type
            vehicules_de_ce_type = self.db_session.query(Vehicule).filter(
                Vehicule.type_vehicule.ilike(f"%{type_db_format}%")
            ).all()
            
            # Stocker le nombre et la liste
            self.nombre_par_type[type_name] = len(vehicules_de_ce_type)
            self.vehicules_par_type[type_name] = vehicules_de_ce_type
        
        # Matrice d'occupation des équipements (selon votre tableau)
        self.matrice_occupation = {
            1: [1, 1, 0, 0, 0, 0],  # E1
            2: [0, 0, 1, 3, 0, 0],  # E2
            3: [0, 1, 0, 0, 1, 1],  # E3
            4: [0, 1, 2, 6, 0, 0],  # E4
            5: [0, 1, 1, 3, 0, 0],  # E5
            6: [0, 50, 24, 72, 0, 0],  # E6
            7: [0, 100, 30, 90, 0, 0],  # E7
            8: [1, 0, 0, 0, 0, 0],  # E8
            9: [1, 0, 0, 0, 0, 0],  # E9
            10: [2, 2, 0, 0, 0, 0],  # E10
            11: [0, 0, 1, 3, 0, 0],  # E11
            12: [1, 0, 0, 0, 0, 0],  # E12
            13: [0, 4000, 800, 2400, 0, 0],  # E13
            14: [0, 1400, 800, 2400, 0, 0],  # E14
            15: [0, 400, 800, 2400, 0, 0],  # E15
            16: [0, 12000, 800, 2400, 0, 0],  # E16
            17: [0, 2000, 800, 2400, 0, 0],  # E17
            18: [0, 2000, 800, 2400, 0, 0],  # E18
            19: [0, 1, 1, 3, 0, 0],  # E19
            20: [1, 0, 0, 0, 0, 0],  # E20
            21: [2, 2, 0, 0, 0, 0],  # E21
            22: [1, 1, 0, 0, 0, 0],  # E22
            23: [0, 100, 40, 120, 0, 0],  # E23
            24: [0, 1000, 400, 1200, 0, 0],  # E24
            25: [0, 300, 150, 450, 0, 0],  # E25
            26: [0, 150, 70, 210, 0, 0],  # E26
            27: [0, 500, 250, 750, 0, 0],  # E27
        }
    
    def get_vehicules_disponibles(self, date_planification=None) -> List[Vehicule]:
        """
        Récupère les véhicules disponibles à une date donnée
        Si date_planification est None, retourne tous les véhicules
        """
        if not date_planification:
            # Pour la planification préalable, retourner tous les véhicules
            return self.tous_vehicules
        
        # Si une date est spécifiée, filtrer les véhicules disponibles à cette date
        vehicules_disponibles = []
        for vehicule in self.tous_vehicules:
            # Vérifier si le véhicule est déjà prévu dans une autre tournée à cette date
            tournee_existante = self.db_session.query(Tournee).filter(
                Tournee.immatriculation_vehicule == vehicule.immatriculation,
                func.date(Tournee.date_heure_depart) == func.date(date_planification)
            ).first()
            
            if not tournee_existante:
                vehicules_disponibles.append(vehicule)
        
        return vehicules_disponibles
        
    def get_equipements_a_affecter(self, id_client=None, numero_semaine=None) -> List[dict]:
        """
        Récupère les équipements qui doivent être affectés pour une semaine donnée
        
        Args:
            id_client: ID du client/chantier (optionnel)
            numero_semaine: Numéro de la semaine pour le transfert (obligatoire)
        
        Returns:
            Liste des équipements avec leurs quantités à transférer pour la semaine
        """
        if not numero_semaine:
            raise ValueError("Le numéro de semaine est obligatoire pour récupérer les transferts d'équipements")
        
        # Base de la requête
        query = (
            self.db_session.query(
                TransfererEquipement,
                SemaineTransfert
            )
            .join(
                SemaineTransfert,
                TransfererEquipement.id == SemaineTransfert.id
            )
            .filter(
                SemaineTransfert.numero_semaine == numero_semaine,
                SemaineTransfert.quantite > 0  # S'assurer qu'il y a une quantité à transférer
            )
        )
        
        # Filtrer par client si spécifié
        if id_client:
            query = query.filter(TransfererEquipement.id_client == id_client)
        
        # Exécuter la requête
        resultats = query.all()
        
        # Transformer les résultats en liste d'équipements avec leurs quantités
        equipements_a_affecter = []
        
        for transfert_eq, semaine in resultats:
            # Pour chaque équipement, récupérer ses détails à partir de la table Equipement
            details_equipement = self.db_session.query(Equipement).filter(
                Equipement.nomEquipement == transfert_eq.designation_equipement
            ).first()
            
            if not details_equipement:
                print(f"Attention: Équipement '{transfert_eq.designation_equipement}' non trouvé dans la table Equipement")
                continue
            
            # Créer une entrée pour chaque unité de l'équipement à transférer
            for i in range(semaine.quantite):
                equipements_a_affecter.append({
                    "id": details_equipement.ID_equipement,
                    "nom": details_equipement.nomEquipement,
                    "type": details_equipement.typeEquipement,
                    "client_destination": transfert_eq.id_client,
                    "modalite_transport": transfert_eq.modalite_transport
                })
        
        return equipements_a_affecter
    
    def resoudre_affectation(self, equipements_a_affecter: List[dict], vehicules: List[Vehicule]) -> Dict:
        """
        Résout le problème d'affectation des équipements aux véhicules
        en minimisant le nombre de véhicules utilisés
        
        Args:
            equipements_a_affecter: Liste des équipements à affecter (format dict)
            vehicules: Liste des véhicules disponibles
        """
        # Création du problème d'optimisation
        prob = LpProblem("Affectation_Equipements_Vehicules", LpMinimize)
        
        # Nombre d'équipements et de véhicules
        n = len(equipements_a_affecter)
        m = len(vehicules)
        
        # Variables de décision
        # xij = 1 si l'équipement i est affecté au véhicule j, 0 sinon
        x = {}
        for i in range(n):
            for j in range(m):
                x[i, j] = LpVariable(f"x_{i}_{j}", cat="Binary")
        
        # yj = 1 si le véhicule j est utilisé, 0 sinon
        y = {}
        for j in range(m):
            y[j] = LpVariable(f"y_{j}", cat="Binary")
        
        # Fonction objectif: minimiser le nombre de véhicules utilisés
        prob += sum(y[j] for j in range(m)), "Nombre_de_vehicules_utilises"
        
        # Contrainte 1: Chaque équipement est affecté à un seul véhicule au maximum
        for i in range(n):
            prob += sum(x[i, j] for j in range(m)) <= 1, f"Affectation_unique_{i}"
        
        # Contrainte 2: La capacité de chaque véhicule ne doit pas être dépassée
        for j in range(m):
            vehicule = vehicules[j]
            type_vehicule_index = self.types_vehicules.get(vehicule.type_vehicule.lower().replace(" ", "_"), 0)
            capacite = float(vehicule.capacite_tonne)  # Capacité en tonnes
            
            # Somme des unités occupées par équipement dans ce type de véhicule
            somme_occupation = sum(
                self.matrice_occupation.get(equipements_a_affecter[i]["id"], [0, 0, 0, 0, 0, 0])[type_vehicule_index] * x[i, j]
                for i in range(n)
            )
            
            prob += somme_occupation <= capacite * y[j], f"Capacite_vehicule_{j}"
        
        # Contrainte 3: Un équipement ne peut être affecté à un véhicule que si celui-ci est utilisé
        for i in range(n):
            for j in range(m):
                prob += x[i, j] <= y[j], f"Activation_vehicule_{i}_{j}"
        
        # Résolution du problème
        prob.solve()
        
        # Vérification si une solution a été trouvée
        if LpStatus[prob.status] != "Optimal":
            return {"status": "Échec", "message": "Pas de solution optimale trouvée"}
        
        # Construction du résultat
        resultat = {
            "status": "Succès",
            "nombre_vehicules_utilises": value(sum(y[j] for j in range(m))),
            "affectations": []
        }
        
        for j in range(m):
            if value(y[j]) == 1:  # Si le véhicule j est utilisé
                equipements_affectes = []
                for i in range(n):
                    if value(x[i, j]) == 1:  # Si l'équipement i est affecté au véhicule j
                        equipements_affectes.append({
                            "id_equipement": equipements_a_affecter[i]["id"],
                            "nom_equipement": equipements_a_affecter[i]["nom"],
                            "client_destination": equipements_a_affecter[i]["client_destination"]
                        })
                
                resultat["affectations"].append({
                    "vehicule": {
                        "immatriculation": vehicules[j].immatriculation,
                        "type": vehicules[j].type_vehicule,
                        "capacite": vehicules[j].capacite_tonne
                    },
                    "equipements": equipements_affectes,
                    "client": equipements_affectes[0]["client_destination"] if equipements_affectes else None
                })
        
        return resultat
    
    def creer_affectations_en_bdd(self, resultat: Dict, id_tournee: int = None) -> bool:
        """
        Enregistre les affectations en base de données
        """
        try:
            if resultat["status"] != "Succès":
                return False
            
            for affectation in resultat["affectations"]:
                vehicule_immat = affectation["vehicule"]["immatriculation"]
                
                # Récupérer l'instance du véhicule
                vehicule = self.db_session.query(Vehicule).filter_by(immatriculation=vehicule_immat).first()
                
                if id_tournee:
                    # Affecter le véhicule à la tournée
                    vehicule.Affecter_tournee(id_tournee)
                
                # Pour chaque équipement affecté à ce véhicule
                for equip_info in affectation["equipements"]:
                    equip_id = equip_info["id_equipement"]
                    equipement = self.db_session.query(Equipement).filter_by(ID_equipement=equip_id).first()
                    
                    # Créer une nouvelle affectation
                    nouvelle_affectation = Affectation(
                        id_vehicule=vehicule.immatriculation,
                        id_equipement=equip_id,
                        id_tournee=id_tournee if id_tournee else None,
                        date_affectation=datetime.now()
                    )
                    
                    self.db_session.add(nouvelle_affectation)
            
            self.db_session.commit()
            return True
        
        except Exception as e:
            self.db_session.rollback()
            print(f"Erreur lors de l'enregistrement des affectations: {e}")
            return False
    
    def planifier_affectation_pour_tournee(self, id_tournee: int, date_planification=None):
        """
        Méthode principale pour planifier l'affectation des équipements pour une tournée
        Si date_planification est None, considère tous les véhicules pour une planification préalable
        """
        # 1. Récupérer la tournée et ses équipements associés (via commandes)
        tournee = self.db_session.query(Tournee).filter_by(id_tournee=id_tournee).first()
        if not tournee:
            return {"status": "Échec", "message": "Tournée non trouvée"}
        
        # 2. Récupérer les véhicules disponibles
        vehicules = self.get_vehicules_disponibles(date_planification)
        if not vehicules:
            return {"status": "Échec", "message": "Aucun véhicule disponible"}
        
        # 3. Récupérer les équipements à affecter pour cette tournée
        # Supposons que nous avons une relation entre Tournee et Commande
        equipements = []
        for commande in tournee.commandes:
            equipements_commande = self.get_equipements_a_affecter(commande.id_client, numero_semaine=tournee.numero_semaine)
            equipements.extend(equipements_commande)
        
        if not equipements:
            return {"status": "Échec", "message": "Aucun équipement à affecter"}
        
        # 4. Résoudre le problème d'affectation
        resultat = self.resoudre_affectation(equipements, vehicules)
        
        # 5. Enregistrer les affectations en base de données
        if resultat["status"] == "Succès":
            if self.creer_affectations_en_bdd(resultat, id_tournee):
                return resultat
            else:
                return {"status": "Échec", "message": "Erreur lors de l'enregistrement des affectations"}
        
        return resultat
    
    def planifier_transferts_semaine(self, numero_semaine, id_client=None):
        """
        Planifie les transferts d'équipements pour une semaine donnée
        
        Args:
            numero_semaine: Numéro de la semaine à planifier
            id_client: ID du client (optionnel, si on veut planifier pour un client spécifique)
        
        Returns:
            Résultat de la planification
        """
        # 1. Récupérer tous les équipements à transférer pour cette semaine
        equipements_a_affecter = self.get_equipements_a_affecter(
            id_client=id_client, 
            numero_semaine=numero_semaine
        )
        
        if not equipements_a_affecter:
            return {
                "status": "Information", 
                "message": f"Aucun équipement à transférer pour la semaine {numero_semaine}"
            }
        
        # 2. Récupérer tous les véhicules disponibles
        vehicules_disponibles = self.get_vehicules_disponibles()
        
        if not vehicules_disponibles:
            return {
                "status": "Échec", 
                "message": "Aucun véhicule disponible pour effectuer les transferts"
            }
        
        # 3. Résoudre le problème d'affectation
        resultat = self.resoudre_affectation(equipements_a_affecter, vehicules_disponibles)
        
        # 4. Si une solution a été trouvée, on peut l'enregistrer ou la renvoyer
        if resultat["status"] == "Succès":
            # Ajouter des statistiques sur les équipements planifiés
            nb_total_equipements = len(equipements_a_affecter)
            nb_equipements_affectes = sum(len(aff["equipements"]) for aff in resultat["affectations"])
            
            resultat["statistiques"] = {
                "total_equipements": nb_total_equipements,
                "equipements_affectes": nb_equipements_affectes,
                "taux_affectation": round(nb_equipements_affectes / nb_total_equipements * 100, 2) if nb_total_equipements > 0 else 0
            }
        
        return resultat


# Exemple d'utilisation du service
def example_usage(db_session):
    from datetime import datetime
    
    service = OptimisationService(db_session)
    
    # Planifier l'affectation pour une tournée spécifique
    resultat = service.planifier_affectation_pour_tournee(id_tournee=123, 
                                                         date_planification=datetime.now())
    
    print(f"Résultat de l'affectation: {resultat}")
    
    # Ou planifier manuellement
    vehicules = service.get_vehicules_disponibles()
    equipements = service.get_equipements_a_affecter(id_client=456, numero_semaine=25)
    
    if vehicules and equipements:
        resultat = service.resoudre_affectation(equipements, vehicules)
        if resultat["status"] == "Succès":
            service.creer_affectations_en_bdd(resultat)
