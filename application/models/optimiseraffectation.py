from pulp import LpProblem, LpVariable, LpMinimize, LpBinary, lpSum
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple
from application.models.vehicule import Vehicule
from application.models.transferer_equipement import TransfererEquipement
from application.models.chantiers import Chantier
from application.database import SessionLocal

class OptimisationAffectation:
    
    def __init__(self):
        # Dictionnaire des types de véhicules et leurs capacités
        self.types_vehicules = {
            "Porte engin": 1,
            "Semi remorque simple": 2,
            "Plateau 6×2": 3,
            "Semi remorque Triple": 4,
            "Camions plateaux 6×6": 5,
            "Camions plateaux 4×2": 6
        }
        
        # Matrice d'occupation des équipements selon le type de véhicule
        # Format: {id_equipement: {type_vehicule: unites_occupees}}
        self.matrice_occupation = self._initialiser_matrice_occupation()
        
        # Capacités par défaut pour chaque type de véhicule au cas où elles ne seraient pas définies
        self.capacites_par_defaut = {
            1: 1000,  # Porte engin
            2: 5000,  # Semi remorque simple
            3: 3000,  # Plateau 6×2
            4: 8000,  # Semi remorque Triple
            5: 4000,  # Camions plateaux 6×6
            6: 2000   # Camions plateaux 4×2
        }
    
    def _initialiser_matrice_occupation(self) -> Dict:
        """
        Initialise la matrice d'occupation des équipements selon le type de véhicule
        basée sur la matrice fournie dans les contraintes mathématiques
        """
        return {
            "E_1": {1: 100, 2: 100, 3: 200, 4: 200, 5: 10, 6: 20},
            "E_2": {1: 0, 2: 0, 3: 1, 4: 3, 5: 0, 6: 0},
            "E_3": {1: 0, 2: 1, 3: 0, 4: 0, 5: 1, 6: 1},
            "E_4": {1: 0, 2: 1, 3: 2, 4: 6, 5: 0, 6: 0},
            "E_5": {1: 0, 2: 1, 3: 1, 4: 3, 5: 0, 6: 0},
            "E_6": {1: 0, 2: 50, 3: 24, 4: 72, 5: 0, 6: 0},
            "E_7": {1: 0, 2: 100, 3: 30, 4: 90, 5: 0, 6: 0},
            "E_8": {1: 1, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
            "E_9": {1: 1, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
            "E_10": {1: 2, 2: 2, 3: 0, 4: 0, 5: 0, 6: 0},
            "E_11": {1: 0, 2: 0, 3: 1, 4: 3, 5: 0, 6: 0},
            "E_12": {1: 1, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
            "E_13": {1: 0, 2: 4000, 3: 800, 4: 2400, 5: 0, 6: 0},
            "E_14": {1: 0, 2: 1400, 3: 800, 4: 2400, 5: 0, 6: 0},
            "E_15": {1: 0, 2: 400, 3: 800, 4: 2400, 5: 0, 6: 0},
            "E_16": {1: 0, 2: 12000, 3: 800, 4: 2400, 5: 0, 6: 0},
            "E_17": {1: 0, 2: 2000, 3: 800, 4: 2400, 5: 0, 6: 0},
            "E_18": {1: 0, 2: 2000, 3: 800, 4: 2400, 5: 0, 6: 0},
            "E_19": {1: 0, 2: 1, 3: 1, 4: 3, 5: 0, 6: 0},
            "E_20": {1: 1, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0},
            "E_21": {1: 2, 2: 2, 3: 0, 4: 0, 5: 0, 6: 0},
            "E_22": {1: 1, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0},
            "E_23": {1: 0, 2: 100, 3: 40, 4: 120, 5: 0, 6: 0},
            "E_24": {1: 0, 2: 1000, 3: 400, 4: 1200, 5: 0, 6: 0},
            "E_25": {1: 0, 2: 300, 3: 150, 4: 450, 5: 0, 6: 0},
            "E_26": {1: 0, 2: 150, 3: 70, 4: 210, 5: 0, 6: 0},
            "E_27": {1: 0, 2: 500, 3: 250, 4: 750, 5: 0, 6: 0}
        }
    
    def _get_equipements_from_db(self, id_client: str, session: Session) -> List[TransfererEquipement]:
        """Récupère les équipements à transférer pour un client donné"""
        return session.query(TransfererEquipement).filter(
            TransfererEquipement.id_client == id_client
        ).all()
    
    def _get_vehicules_disponibles(self, session: Session) -> List[Vehicule]:
        """Récupère les véhicules disponibles"""
        vehicules_disponibles = []
        for vehicule in session.query(Vehicule).all():
            if vehicule.est_disponible():
                vehicules_disponibles.append(vehicule)
        return vehicules_disponibles
    
    def _map_vehicule_type(self, vehicule: Vehicule) -> int:
        """Mappe le type de véhicule à son index dans la matrice d'occupation"""
        return self.types_vehicules.get(vehicule.type_vehicule, 0)
    
    def _get_vehicule_capacite(self, vehicule: Vehicule) -> float:
        """Retourne la capacité du véhicule en fonction de son type"""
        # Correction du bug: vérifier si capacite_volume est None
        if not hasattr(vehicule, 'capacite_volume') or vehicule.capacite_volume is None:
            # Utiliser une capacité par défaut basée sur le type de véhicule
            vehicule_type = self._map_vehicule_type(vehicule)
            return self.capacites_par_defaut.get(vehicule_type, 1000)  # Valeur par défaut générique: 1000
        return vehicule.capacite_volume
    
    def optimiser_affectation(self, id_client: str) -> Dict:
        """
        Optimise l'affectation des équipements aux véhicules pour un client donné
        
        Args:
            id_client: Identifiant du client/chantier
            
        Returns:
            Dict contenant le plan d'affectation des équipements aux véhicules
        """
        session = SessionLocal()
        try:
            # Récupérer les données nécessaires
            equipements = self._get_equipements_from_db(id_client, session)
            vehicules = self._get_vehicules_disponibles(session)
            
            # Vérification des données
            if not equipements:
                return {"status": "error", "message": "Aucun équipement à transférer pour ce client"}
            
            if not vehicules:
                return {"status": "error", "message": "Aucun véhicule disponible"}
            
            # Créer le problème PuLP
            prob = LpProblem("OptimisationAffectationEquipements", LpMinimize)
            
            # Indices pour les équipements et véhicules
            I = range(len(equipements))  # Équipements
            J = range(len(vehicules))    # Véhicules
            
            # Variables de décision
            x = {}
            for i in I:
                for j in J:
                    x[i, j] = LpVariable(f"x_{i}_{j}", cat=LpBinary)
            
            # Variable y_j = 1 si le véhicule j est utilisé, 0 sinon
            y = {}
            for j in J:
                y[j] = LpVariable(f"y_{j}", cat=LpBinary)
            
            # Fonction objectif: minimiser le nombre de véhicules utilisés
            prob += lpSum(y[j] for j in J)
            
            # Contrainte 1: Chaque équipement est affecté à un seul camion au maximum
            for i in I:
                prob += lpSum(x[i, j] for j in J) <= 1
            
            # Contrainte 2: Respect des capacités des véhicules
            for j in J:
                vehicule = vehicules[j]
                vehicule_type = self._map_vehicule_type(vehicule)
                capacite = self._get_vehicule_capacite(vehicule)
                
                # Vérification supplémentaire pour s'assurer que la capacité est un nombre
                if capacite is None:
                    capacite = self.capacites_par_defaut.get(vehicule_type, 1000)
                
                total_occupation = 0
                for i in I:
                    equipement = equipements[i]
                    # Obtenir l'identifiant standard de l'équipement pour la matrice d'occupation
                    equipement_id = equipement.designation_equipement
                    
                    # Si l'équipement n'est pas dans la matrice, on le traite comme un cas particulier
                    if equipement_id not in self.matrice_occupation:
                        # Valeur par défaut ou comportement alternatif
                        occupation = 1  # Valeur par défaut
                    else:
                        occupation = self.matrice_occupation[equipement_id].get(vehicule_type, 0)
                    
                    # Multiplier par le nombre total d'équipements de ce type
                    # Vérifier que total_equipements est un nombre
                    if not hasattr(equipement, 'total_equipements') or equipement.total_equipements is None:
                        equipement_total = 1  # Valeur par défaut
                    else:
                        equipement_total = equipement.total_equipements
                    
                    occupation *= equipement_total
                    total_occupation += x[i, j] * occupation
                
                # S'assurer que capacite est un nombre valide avant de l'utiliser
                prob += total_occupation <= capacite * y[j]
            
            # Contrainte 3: Un équipement ne peut être affecté à un camion que si ce camion est utilisé
            for i in I:
                for j in J:
                    prob += x[i, j] <= y[j]
            
            # Résolution du problème
            prob.solve()
            
            # Extraction des résultats
            statut = prob.status
            
            if statut != 1:  # 1 signifie "Optimal"
                return {"status": "error", "message": "Pas de solution optimale trouvée"}
            
            # Construire le plan d'affectation
            plan_affectation = {
                "status": "success",
                "nombre_vehicules": sum(y[j].value() for j in J),
                "affectations": []
            }
            
            for j in J:
                if y[j].value() > 0.5:  # Le véhicule est utilisé
                    vehicule_info = {
                        "immatriculation": vehicules[j].immatriculation,
                        "type": vehicules[j].type_vehicule,
                        "equipements": []
                    }
                    
                    for i in I:
                        if x[i, j].value() > 0.5:  # L'équipement est affecté à ce véhicule
                            vehicule_info["equipements"].append({
                                "designation": equipements[i].designation_equipement,
                                "quantite": equipements[i].total_equipements
                            })
                    
                    plan_affectation["affectations"].append(vehicule_info)
            
            return plan_affectation
            
        finally:
            session.close()
    
    def executer_optimisation_pour_tous_clients(self):
        """
        Exécute l'optimisation pour tous les clients ayant des équipements à transférer
        """
        session = SessionLocal()
        try:
            # Récupérer tous les clients avec des équipements à transférer
            clients_avec_equipements = session.query(Chantier.id_client).join(
                TransfererEquipement, Chantier.id_client == TransfererEquipement.id_client
            ).distinct().all()
            
            resultats = {}
            for (id_client,) in clients_avec_equipements:
                resultats[id_client] = self.optimiser_affectation(id_client)
            
            return resultats
            
        finally:
            session.close()


# Exemple d'utilisation
if __name__ == "__main__":
    optimiseur = OptimisationAffectation()
    
    # Option 1: Optimiser pour un client spécifique
    resultat = optimiseur.optimiser_affectation("EGS 100")
    print(resultat)
    
    # Option 2: Optimiser pour tous les clients
    resultats_globaux = optimiseur.executer_optimisation_pour_tous_clients()
    print(resultats_globaux)