from matplotlib import colors
import numpy as np
import random
import copy
import time
import json
from collections import defaultdict
import sys
import math
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import func

# Import de votre classe Vehicule et de la session SQLAlchemy

from application.models.vehicule import Vehicule
from application.database import SessionLocal
from datetime import date

class Instance:
    def __init__(self, id_client=None, cible_longitude=None, cible_latitude=None):
        """
        Initialisation d'une instance du problème de transport par navettes entre les sites A et B
        sur un horizon de 12 semaines, avec transport uniquement dans le sens A vers B.
        
        Les données de véhicules sont récupérées depuis la base de données via la classe Vehicule.
        Les demandes d'équipements sont maintenant récupérées depuis la classe TransfererEquipement.
        
        Args:
            id_client: ID du client/chantier pour le site A
            cible_longitude: Longitude du site B
            cible_latitude: Latitude du site B
        """
        # Horizon de planification: 12 semaines
        self.T = list(range(1, 13))
        self.np = 12
        
        # Stocker les paramètres de localisation
        self.id_client = id_client
        self.cible_longitude = cible_longitude
        self.cible_latitude = cible_latitude
        
        # Récupérer les coordonnées du client et calculer la distance
        self.load_client_coordinates()
        self.calculate_distance()
        
        # Récupérer les données des véhicules depuis la base de données
        self.load_vehicles_from_database()
        
        # Coût de déplacement entre les sites (indépendant du type de véhicule)
        self.dc = 50
        
        # Charger les demandes depuis la base de données au lieu de les générer aléatoirement
        self.load_demands_from_database()
        
        # Paramètres liés aux contraintes temporelles
        self.T_start = 7      # Heure de début de la journée de travail (en heures depuis minuit)
        self.T_end = 18       # Heure de fin de la journée de travail (en heures depuis minuit)
        self.T_drive = 2      # Durée maximale de conduite continue (en heures)
        self.T_break = 0.25   # Durée d'une pause obligatoire (en heures, soit 15 minutes)
        
        # Temps de chargement et déchargement (en heures)
        self.T_load_A = 0.5    # Temps de chargement au site A
        self.T_unload_B = 0.5  # Temps de déchargement au site B
    
    def load_client_coordinates(self):
        """
        Récupère les coordonnées GPS du client/chantier (site A) depuis la base de données
        """
        from application.models.chantiers import Chantier
        
        # Vérifier que l'ID client est fourni
        if not self.id_client:
            raise ValueError("ID client non spécifié. Impossible de calculer la distance.")
        
        # Créer une session SQLAlchemy
        session = SessionLocal()
        
        try:
            # Récupérer les informations du chantier
            chantier = session.query(Chantier).filter_by(id_client=self.id_client).first()
            
            if not chantier:
                raise ValueError(f"Aucun chantier trouvé avec l'ID {self.id_client}")
            
            # Stocker les coordonnées du client (site A)
            self.client_latitude = chantier.latitude
            self.client_longitude = chantier.longitude
            
            # Stocker également d'autres informations utiles
            self.client_localisation = chantier.localisation
            self.distance_aller_goudron = chantier.distanceAllerGoudron
            self.distance_aller_piste = chantier.distanceAllerPiste
            self.temps_aller = chantier.temps_aller
            
        finally:
            session.close()
    
    def calculate_distance(self):
        """
        Calcule la distance entre le site A (client) et le site B (cible) en utilisant la formule haversine
        """
        import math
        
        # Vérifier que toutes les coordonnées sont disponibles
        if None in (self.client_latitude, self.client_longitude, self.cible_latitude, self.cible_longitude):
            raise ValueError("Coordonnées incomplètes. Impossible de calculer la distance.")
        
        # Convertir les degrés en radians
        lat1, lon1 = math.radians(self.client_latitude), math.radians(self.client_longitude)
        lat2, lon2 = math.radians(self.cible_latitude), math.radians(self.cible_longitude)
        
        # Formule haversine pour calculer la distance entre deux points sur la Terre
        R = 6371  # Rayon de la Terre en kilomètres
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        # Distance en kilomètres
        distance = R * c
        
        # Arrondir à l'entier supérieur pour plus de sécurité
        self.d_AB = math.ceil(distance)
        self.d_BA = self.d_AB  # Même distance pour le retour
        
        print(f"Distance calculée entre {self.client_localisation} et le site cible: {self.d_AB} km")
    
    def load_vehicles_from_database(self):
        """
        Récupère les informations des véhicules depuis la base de données
        et les organise dans les structures de données requises par la métaheuristique.
        """
        from application.models.vehicule import Vehicule  # Import local pour éviter les problèmes circulaires
        
        # Créer une session SQLAlchemy
        session = SessionLocal()
        
        try:
            # Récupérer tous les véhicules disponibles
            vehicles = session.query(Vehicule).filter(Vehicule.etat == "Disponible").all()
            
            # Grouper les véhicules par type
            vehicles_by_type = {}
            for vehicle in vehicles:
                vehicle_type = vehicle.type_vehicule
                if vehicle_type not in vehicles_by_type:
                    vehicles_by_type[vehicle_type] = []
                vehicles_by_type[vehicle_type].append(vehicle)
            
            # Transformer les données en structures attendues par la métaheuristique
            # L: Types de véhicules disponibles avec leurs capacités
            self.L = {}
            # m: Nombre maximal de véhicules disponibles par type
            self.m = {}
            # c: Coût d'utilisation de chaque type de véhicule
            self.c = {}
            # V: Vitesse moyenne des véhicules (km/h)
            self.V = {}
            
            # Attribuer un ID numérique à chaque type de véhicule
            for i, (vehicle_type, vehicle_list) in enumerate(vehicles_by_type.items(), 1):
                # On utilise le premier véhicule de chaque type comme référence pour les capacités
                reference_vehicle = vehicle_list[0]
                
                # Gérer les cas où les champs sont `None`
                capacite_tonne = reference_vehicle.capacite_tonne or 0  # Valeur par défaut : 0 tonnes
                capacite_volume = reference_vehicle.capacite_volume or 0  # Valeur par défaut : 0 m³
                
                # Capacités (poids en kg et volume en m³)
                self.L[i] = {
                    "Qw": capacite_tonne * 1000,  # Convertir tonnes en kg
                    "Qv": capacite_volume
                }
                
                # Nombre de véhicules disponibles pour ce type
                self.m[i] = len(vehicle_list)
                
                # Coût d'utilisation (hypothèse : proportionnel à la capacité)
                self.c[i] = int(50 + capacite_tonne * 20)
                
                # Vitesse moyenne (hypothèse : inversement proportionnelle à la taille)
                self.V[i] = int(80 - capacite_tonne * 2)
                
                # Stocker la correspondance entre ID numérique et type de véhicule pour référence
                if not hasattr(self, 'type_mapping'):
                    self.type_mapping = {}
                self.type_mapping[i] = vehicle_type
                
                # Stocker les immatriculations pour chaque type de véhicule
                if not hasattr(self, 'vehicle_plates'):
                    self.vehicle_plates = {}
                self.vehicle_plates[i] = [v.immatriculation for v in vehicle_list]
        
        finally:
            session.close()
        
        # Si aucun véhicule n'est disponible, lever une exception
        if not hasattr(self, 'L') or not self.L:
            raise ValueError("Aucun véhicule disponible dans la base de données. Impossible de continuer sans véhicules.")
    
    def load_vehicles_from_database(self):
        """
        Récupère les informations des véhicules depuis la base de données
        et les organise dans les structures de données requises par la métaheuristique.
        Filtre les véhicules en fonction de la nature du terrain du chantier.
        """
        from application.models.vehicule import Vehicule  # Import local pour éviter les problèmes circulaires
        from application.models.chantiers import Chantier
        
        # Créer une session SQLAlchemy
        session = SessionLocal()
        
        try:
            # D'abord, récupérer la nature du terrain du chantier
            nature_terrain = None
            if self.id_client:
                chantier = session.query(Chantier).filter_by(id_client=self.id_client).first()
                if chantier:
                    nature_terrain = chantier.nature_terrain
                    print(f"Nature du terrain pour le chantier {self.id_client}: {nature_terrain}")
            
            # Construire la requête de base pour les véhicules disponibles
            query = session.query(Vehicule).filter(Vehicule.etat == "Disponible")
            
            # Filtrer les véhicules selon la nature du terrain
            if nature_terrain == "Accès difficile":
                # Pour un accès difficile, on ne garde que les 4x4 ou 6x6
                query = query.filter(
                    (Vehicule.type_vehicule.like("%4x4%")) | 
                    (Vehicule.type_vehicule.like("%4*4%")) |
                    (Vehicule.type_vehicule.like("%6x6%")) |
                    (Vehicule.type_vehicule.like("%6*6%"))
                )
                print("Terrain difficile: filtrage des véhicules pour ne garder que les 4x4 et 6x6")
            else:
                print("Terrain facile ou non spécifié: tous les véhicules disponibles seront considérés")
            
            # Récupérer les véhicules filtrés
            vehicles = query.all()
            
            # Afficher les véhicules retenus pour debug
            print(f"Nombre de véhicules retenus: {len(vehicles)}")
            for v in vehicles:
                print(f"  - {v.immatriculation}: {v.type_vehicule}")
            
            # Grouper les véhicules par type
            vehicles_by_type = {}
            for vehicle in vehicles:
                vehicle_type = vehicle.type_vehicule
                if vehicle_type not in vehicles_by_type:
                    vehicles_by_type[vehicle_type] = []
                vehicles_by_type[vehicle_type].append(vehicle)
            
            # Transformer les données en structures attendues par la métaheuristique
            # L: Types de véhicules disponibles avec leurs capacités
            self.L = {}
            # m: Nombre maximal de véhicules disponibles par type
            self.m = {}
            # c: Coût d'utilisation de chaque type de véhicule
            self.c = {}
            # V: Vitesse moyenne des véhicules (km/h)
            self.V = {}
            
            # Attribuer un ID numérique à chaque type de véhicule
            for i, (vehicle_type, vehicle_list) in enumerate(vehicles_by_type.items(), 1):
                # On utilise le premier véhicule de chaque type comme référence pour les capacités
                reference_vehicle = vehicle_list[0]
                
                # Gérer les cas où les champs sont `None`
                capacite_tonne = reference_vehicle.capacite_tonne or 0  # Valeur par défaut : 0 tonnes
                capacite_volume = reference_vehicle.capacite_volume or 0  # Valeur par défaut : 0 m³
                
                # Capacités (poids en kg et volume en m³)
                self.L[i] = {
                    "Qw": capacite_tonne * 1000,  # Convertir tonnes en kg
                    "Qv": capacite_volume
                }
                
                # Nombre de véhicules disponibles pour ce type
                self.m[i] = len(vehicle_list)
                
                # Coût d'utilisation (hypothèse : proportionnel à la capacité)
                self.c[i] = int(50 + capacite_tonne * 20)
                
                # Vitesse moyenne (hypothèse : inversement proportionnelle à la taille)
                # Pour les terrains difficiles, réduire la vitesse de 20%
                base_speed = int(80 - capacite_tonne * 2)
                if nature_terrain == "Accès difficile":
                    self.V[i] = int(base_speed * 0.8)  # Réduction de 20% pour terrain difficile
                else:
                    self.V[i] = base_speed
                
                # Stocker la correspondance entre ID numérique et type de véhicule pour référence
                if not hasattr(self, 'type_mapping'):
                    self.type_mapping = {}
                self.type_mapping[i] = vehicle_type
                
                # Stocker les immatriculations pour chaque type de véhicule
                if not hasattr(self, 'vehicle_plates'):
                    self.vehicle_plates = {}
                self.vehicle_plates[i] = [v.immatriculation for v in vehicle_list]
        
        finally:
            session.close()
        
        # Si aucun véhicule n'est disponible, lever une exception
        if not hasattr(self, 'L') or not self.L:
            raise ValueError("Aucun véhicule disponible avec les critères fournis. Vérifiez que des véhicules 4x4/6x6 sont disponibles pour les terrains difficiles.")
    def load_demands_from_database(self):
        """
        Récupère les demandes d'équipements depuis la classe TransfererEquipement
        et calcule le poids et le volume correspondants à partir de la classe Equipement.
        Filtre par ID client si spécifié.
        """
        from application.models.transferer_equipement import TransfererEquipement
        from application.models.equipements import Equipement
        from sqlalchemy import func
        from collections import defaultdict
        
        # Initialiser les dictionnaires pour stocker les demandes en poids et volume
        self.dw_AB = {t: 0 for t in self.T}  # Demandes en poids de A vers B
        self.dv_AB = {t: 0 for t in self.T}  # Demandes en volume de A vers B
        
        print(f"Récupération des demandes réelles pour le client ID: {self.id_client}")
        
        # Créer une session SQLAlchemy
        session = SessionLocal()
        
        try:
            # Récupérer les entrées de transfert d'équipements pour ce client spécifique
            query = session.query(TransfererEquipement)
            if self.id_client:
                query = query.filter_by(id_client=self.id_client)
            
            transfers = query.all()
            
            print(f"Nombre de transferts trouvés: {len(transfers)}")
            
            # Pour chaque transfert d'équipement
            for transfer in transfers:
                # Récupérer l'équipement correspondant
                equipement = session.query(Equipement).filter_by(ID_equipement=transfer.id_equipement).first()
                
                print(f"Traitement de l'équipement: {transfer.nom_equipement} (ID: {transfer.id_equipement})")
                
                if equipement:
                    # Récupérer le poids et le volume unitaires (valeurs par défaut si None)
                    poids_unitaire = equipement.poids or 0  # en kg
                    volume_unitaire = equipement.volume or 0  # en m³
                    
                    print(f"  - Poids unitaire: {poids_unitaire}kg, Volume unitaire: {volume_unitaire}m³")
                    
                    # Mappings des colonnes de semaines
                    semaines_mapping = {
                        12: transfer.douze_semaines_avant,
                        11: transfer.onze_semaines_avant,
                        10: transfer.dix_semaines_avant,
                        9: transfer.neuf_semaines_avant,
                        8: transfer.huit_semaines_avant,
                        7: transfer.sept_semaines_avant,
                        6: transfer.six_semaines_avant,
                        5: transfer.cinq_semaines_avant,
                        4: transfer.quatre_semaines_avant,
                        3: transfer.trois_semaines_avant,
                        2: transfer.deux_semaines_avant,
                        1: transfer.un_semaines_avant,
                        0: transfer.zero_semaines_avant
                    }
                    
                    # Pour chaque semaine dans notre horizon (1 à 12)
                    for semaine in self.T:
                        # La semaine dans la DB est inversée (12 = première semaine)
                        db_semaine = 13 - semaine
                        
                        # Récupérer la quantité à transférer pour cette semaine
                        quantite = semaines_mapping.get(db_semaine, 0) or 0
                        
                        if quantite > 0:
                            # Calculer le poids et le volume total pour cette quantité
                            poids_total = poids_unitaire * quantite
                            volume_total = volume_unitaire * quantite
                            
                            # Ajouter aux demandes totales pour cette semaine
                            self.dw_AB[semaine] += poids_total
                            self.dv_AB[semaine] += volume_total
                            
                            print(f"  - Semaine {semaine}: {quantite} unités = {poids_total}kg, {volume_total}m³")
                
            # Vérifier si des demandes ont été trouvées
            if all(self.dw_AB[t] == 0 for t in self.T) and all(self.dv_AB[t] == 0 for t in self.T):
                print("ERREUR: Aucune demande de transfert trouvée dans la base de données.")
                print("Veuillez ajouter des demandes de transfert pour ce client avant d'exécuter la métaheuristique.")
                raise ValueError("Aucune demande de transfert trouvée. Impossible de continuer sans données réelles.")
        
        except Exception as e:
            print(f"Erreur lors de la récupération des demandes: {e}")
            raise ValueError(f"Impossible de récupérer les demandes réelles: {e}")
                
        finally:
            session.close()
        
        # Afficher les demandes récupérées pour debug
        print("Demandes récupérées de la base de données:")
        for t in self.T:
            print(f"Semaine {t}: {self.dw_AB[t]} kg, {self.dv_AB[t]} m³")


    def get_vehicle_plate(self, vtype, idx):
        """
        Récupère l'immatriculation d'un véhicule spécifique
        
        Args:
            vtype: Type de véhicule (entier)
            idx: Indice du véhicule dans ce type (entier)
            
        Returns:
            str: Immatriculation du véhicule ou None si non trouvé
        """
        if hasattr(self, 'vehicle_plates') and vtype in self.vehicle_plates:
            if 1 <= idx <= len(self.vehicle_plates[vtype]):
                return self.vehicle_plates[vtype][idx-1]
        return None
        
    def get_vehicle_type_name(self, vtype):
        """
        Récupère le nom réel du type de véhicule à partir de l'ID numérique
        
        Args:
            vtype: ID numérique du type de véhicule
            
        Returns:
            str: Nom du type de véhicule ou "Type {vtype}" si non trouvé
        """
        if hasattr(self, 'type_mapping') and vtype in self.type_mapping:
            return self.type_mapping[vtype]
        return f"Type {vtype}"
class MC_Vehicle:
    """
    Représente un véhicule individuel dans le modèle MC-SVRP-TC
    Chaque véhicule a ses propres capacités individuelles
    """
    def __init__(self, vehicle_type, vehicle_idx, weight_capacity, volume_capacity, instance=None):
        self.type = vehicle_type  # ℓ dans le modèle
        self.idx = vehicle_idx    # k dans le modèle
        self.weight_capacity = weight_capacity  # C^w_{ℓ,k}
        self.volume_capacity = volume_capacity  # C^v_{ℓ,k}
        self.weeks_used = set()  # Semaines où ce véhicule est utilisé
        self.num_units_used = 0  # n_{ℓ,k} - nombre d'unités de ce véhicule utilisées
        self.num_trips = 0       # m_{ℓ,k} - nombre de voyages assignés
        self.duration = 0.0      # τ_{ℓ,k} - durée d'utilisation en jours
        
        # Informations additionnelles
        self.plate = None
        self.type_name = None
        if instance is not None:
            self.plate = instance.get_vehicle_plate(vehicle_type, vehicle_idx)
            self.type_name = instance.get_vehicle_type_name(vehicle_type)
    
    def is_used(self):
        """Vérifie si le véhicule est utilisé (x_{ℓ,k} = 1)"""
        return len(self.weeks_used) > 0
    
    def reset_usage(self):
        """Remet à zéro l'utilisation du véhicule"""
        self.weeks_used.clear()
        self.num_units_used = 0
        self.num_trips = 0
        self.duration = 0.0

class MC_Transport:
    """
    Représente un transport dans le modèle MC-SVRP-TC
    Inclut les variables y_{p,t,k,ℓ} et les contraintes temporelles
    """
    def __init__(self, week, vehicle_idx, vehicle_type, products_transported=None, 
                 trip_sequence=1, instance=None):
        self.week = week                    # Semaine t
        self.vehicle_idx = vehicle_idx      # Véhicule k
        self.vehicle_type = vehicle_type    # Type ℓ
        self.trip_sequence = trip_sequence  # Séquence du voyage dans la semaine
        
        # Products transported: dict {product_id: quantity}
        self.products_transported = products_transported or {}
        
        # Variables temporelles détaillées du modèle
        self.T_conduite = 0.0      # T^conduite_{ℓ,k,t}
        self.T_pauses = 0.0        # T^pauses_{ℓ,k,t}
        self.T_nuit = 0.0          # T^nuit_{ℓ,k,t}
        self.N_pauses = 0          # N^pauses_{ℓ,k,t}
        self.N_nuits = 0           # N^nuits_{ℓ,k,t}
        self.T_total = 0.0         # Temps total du voyage
        
        # Variables de respect des contraintes
        self.delta = True          # δ_{ℓ,k} - respect contrainte temporelle
        
        # Informations sur le véhicule
        self.vehicle_plate = None
        self.vehicle_type_name = None
        if instance is not None:
            self.vehicle_plate = instance.get_vehicle_plate(vehicle_type, vehicle_idx)
            self.vehicle_type_name = instance.get_vehicle_type_name(vehicle_type)
    
    def total_weight(self, instance):
        """Calcule le poids total transporté"""
        total = 0
        for product_id, quantity in self.products_transported.items():
            # Utiliser les données de poids de l'instance ou par défaut
            if hasattr(instance, 'product_weights') and product_id in instance.product_weights:
                total += quantity * instance.product_weights[product_id]
        return total
    
    def total_volume(self, instance):
        """Calcule le volume total transporté"""
        total = 0
        for product_id, quantity in self.products_transported.items():
            # Utiliser les données de volume de l'instance ou par défaut
            if hasattr(instance, 'product_volumes') and product_id in instance.product_volumes:
                total += quantity * instance.product_volumes[product_id]
        return total

class MC_Solution:
    """
    Solution pour le problème MC-SVRP-TC
    Implémente la fonction objectif (39) et toutes les contraintes
    """
    def __init__(self, instance):
        self.instance = instance
        self.vehicles = {}  # Dict: (type_ℓ, idx_k) -> MC_Vehicle
        self.transports = []  # Liste des MC_Transport
        self.fitness = float('inf')
        self.feasible = False
        
        # Variables du modèle
        self.u_types = {}      # u_ℓ - types de véhicules utilisés
        self.total_cost = 0.0  # Fonction objectif Z
        
        # Initialiser les véhicules avec leurs capacités individuelles
        self._initialize_vehicles()
    
    def _initialize_vehicles(self):
        """Initialise les véhicules avec leurs capacités individuelles"""
        for vtype, count in self.instance.m.items():
            for i in range(1, count + 1):
                # Récupérer les capacités de base du type
                base_weight = self.instance.L[vtype]["Qw"]
                base_volume = self.instance.L[vtype]["Qv"]
                
                # Ajouter une variation individuelle (±10% pour simuler l'hétérogénéité)
                weight_variation = 1.0 + random.uniform(-0.1, 0.1)
                volume_variation = 1.0 + random.uniform(-0.1, 0.1)
                
                individual_weight = base_weight * weight_variation
                individual_volume = base_volume * volume_variation
                
                vehicle = MC_Vehicle(
                    vehicle_type=vtype,
                    vehicle_idx=i,
                    weight_capacity=individual_weight,
                    volume_capacity=individual_volume,
                    instance=self.instance
                )
                
                self.vehicles[(vtype, i)] = vehicle
    
    def evaluate(self):
        """
        Évalue la solution selon la fonction objectif (39) du modèle MC-SVRP-TC
        """
        # Réinitialiser les véhicules
        for vehicle in self.vehicles.values():
            vehicle.reset_usage()
        
        # Calculer l'utilisation des véhicules à partir des transports
        self._update_vehicle_usage()
        
        # Calculer les variables u_ℓ (types utilisés)
        self._update_type_usage()
        
        # Vérifier la faisabilité
        self.feasible = self._check_feasibility()
        
        # Calculer la fonction objectif (39)
        if self.feasible:
            self.fitness = self._calculate_objective()
        else:
            self.fitness = float('inf')
        
        return self.fitness
    
    def _update_vehicle_usage(self):
        """Met à jour l'utilisation des véhicules à partir des transports"""
        for transport in self.transports:
            vehicle_key = (transport.vehicle_type, transport.vehicle_idx)
            vehicle = self.vehicles[vehicle_key]
            
            # Marquer la semaine comme utilisée
            vehicle.weeks_used.add(transport.week)
            
            # Compter les voyages
            vehicle.num_trips += 1
            
            # Calculer la durée (simplifié pour l'instant)
            self._calculate_transport_times(transport, vehicle)
    
    def _calculate_transport_times(self, transport, vehicle):
        """
        Calcule les temps pour un transport selon les équations (49-58)
        """
        vtype = transport.vehicle_type
        
        # Distance et vitesse
        D = self.instance.d_AB
        S = self.instance.V[vtype]
        
        # Temps de conduite (49)
        transport.T_conduite = (2 * D) / S
        
        # Nombre de pauses (50) - approximation
        transport.N_pauses = max(0, math.floor((transport.T_conduite - 2) / 2.0) + 1)
        
        # Temps de pauses (51)
        transport.T_pauses = transport.N_pauses * self.instance.T_break
        
        # Détection des nuits (52) - simplifiée
        total_operation_time = (transport.T_conduite + transport.T_pauses + 
                               self.instance.T_load_A + self.instance.T_unload_B)
        transport.N_nuits = math.floor((total_operation_time - 11) / 24) + 1 if total_operation_time > 11 else 0
        
        # Temps de nuit (53)
        transport.T_nuit = transport.N_nuits * 13.0  # 13h d'arrêt nocturne
        
        # Temps total (54)
        transport.T_total = (transport.T_conduite + transport.T_pauses + 
                            transport.T_nuit + self.instance.T_load_A + self.instance.T_unload_B)
        
        # Mettre à jour la durée du véhicule (55)
        vehicle.duration = max(vehicle.duration, math.ceil(transport.T_total / 8.0))  # 8h de travail par jour
    
    def _update_type_usage(self):
        """Met à jour les variables u_ℓ"""
        self.u_types = {}
        for vtype in self.instance.L.keys():
            self.u_types[vtype] = any(
                self.vehicles[(vtype, i)].is_used() 
                for i in range(1, self.instance.m[vtype] + 1)
            )
    
    def _check_feasibility(self):
        """Vérifie toutes les contraintes du modèle"""
        
        # 1. Contraintes de capacité (43-44)
        if not self._check_capacity_constraints():
            return False
        
        # 2. Contraintes de satisfaction de la demande (45)
        if not self._check_demand_satisfaction():
            return False
        
        # 3. Contraintes temporelles (56-58)
        if not self._check_temporal_constraints():
            return False
        
        # 4. Contraintes de cohérence (28-30)
        if not self._check_coherence_constraints():
            return False
        
        return True
    
    def _check_capacity_constraints(self):
        """Vérifie les contraintes de capacité (43-44)"""
        for transport in self.transports:
            vehicle_key = (transport.vehicle_type, transport.vehicle_idx)
            vehicle = self.vehicles[vehicle_key]
            
            # Contrainte de poids (43)
            total_weight = transport.total_weight(self.instance)
            if total_weight > vehicle.weight_capacity:
                return False
            
            # Contrainte de volume (44)
            total_volume = transport.total_volume(self.instance)
            if total_volume > vehicle.volume_capacity:
                return False
        
        return True
    
    def _check_demand_satisfaction(self):
        """Vérifie la satisfaction de la demande (45)"""
        # Calculer les quantités transportées par semaine
        transported_by_week = defaultdict(lambda: defaultdict(float))
        
        for transport in self.transports:
            week = transport.week
            for product_id, quantity in transport.products_transported.items():
                transported_by_week[week][product_id] += quantity
        
        # Vérifier contre les demandes de l'instance
        for week in self.instance.T:
            # Convertir les demandes poids/volume en quantités de produits
            # (simplification pour l'instant - utilise les demandes en poids/volume directement)
            required_weight = self.instance.dw_AB[week]
            required_volume = self.instance.dv_AB[week]
            
            transported_weight = sum(
                quantity * getattr(self.instance, 'product_weights', {}).get(pid, 1.0)
                for pid, quantity in transported_by_week[week].items()
            )
            
            transported_volume = sum(
                quantity * getattr(self.instance, 'product_volumes', {}).get(pid, 1.0)
                for pid, quantity in transported_by_week[week].items()
            )
            
            if transported_weight < required_weight or transported_volume < required_volume:
                return False
        
        return True
    
    def _check_temporal_constraints(self):
        """Vérifie les contraintes temporelles (56-58)"""
        Hmax = 7.0  # 7 jours par semaine maximum
        
        for vehicle in self.vehicles.values():
            if vehicle.is_used():
                # Contrainte (56): δ = 1 ⟺ τ ≤ Hmax
                vehicle.delta = vehicle.duration <= Hmax
                
                # Calcul du nombre de véhicules nécessaires (57)
                if vehicle.delta:
                    vehicle.num_units_used = 1
                else:
                    vehicle.num_units_used = math.ceil(vehicle.duration / Hmax)
                
                # Durée réelle ajustée (58)
                vehicle.duration = min(vehicle.duration, Hmax)
        
        return True
    
    def _check_coherence_constraints(self):
        """Vérifie les contraintes de cohérence (28-30)"""
        M = 1000  # Grande constante
        
        for vtype in self.instance.L.keys():
            vehicles_of_type = [self.vehicles[(vtype, i)] for i in range(1, self.instance.m[vtype] + 1)]
            
            # Contrainte (28): u_ℓ ≥ x_{ℓ,k}
            type_used = self.u_types[vtype]
            for vehicle in vehicles_of_type:
                if vehicle.is_used() and not type_used:
                    return False
            
            # Contrainte (29): u_ℓ ≤ Σ x_{ℓ,k}
            if type_used and not any(v.is_used() for v in vehicles_of_type):
                return False
            
            # Contrainte (30): n_{ℓ,k} ≤ M × x_{ℓ,k}
            for vehicle in vehicles_of_type:
                if vehicle.num_units_used > M and not vehicle.is_used():
                    return False
        
        return True
    
    def _calculate_objective(self):
        """
        Calcule la fonction objectif (39): coûts fixes + coûts variables
        """
        total_cost = 0.0
        
        for vehicle in self.vehicles.values():
            if vehicle.is_used():
                vtype = vehicle.type
                
                # Coût fixe: n_{ℓ,k} × τ_{ℓ,k} × F_ℓ
                fixed_cost = (vehicle.num_units_used * vehicle.duration * 
                             self.instance.c[vtype])
                
                # Coût variable: m_{ℓ,k} × n_{ℓ,k} × (2D - D/n_{ℓ,k}) × G_ℓ
                # Pour simplifier, on utilise G_ℓ = dc (coût de déplacement)
                if vehicle.num_units_used > 0:
                    variable_cost = (vehicle.num_trips * vehicle.num_units_used * 
                                   (2 * self.instance.d_AB - self.instance.d_AB / vehicle.num_units_used) * 
                                   self.instance.dc)
                else:
                    variable_cost = 0
                
                total_cost += fixed_cost + variable_cost
        
        self.total_cost = total_cost
        return total_cost
    
    def __str__(self):
        vehicles_used = sum(1 for v in self.vehicles.values() if v.is_used())
        return f"MC_Solution(transports={len(self.transports)}, véhicules={vehicles_used}, " \
               f"coût={self.total_cost:.2f}, faisable={self.feasible})"

def mc_greedy_initial_solution(instance):
    """
    Génère une solution initiale gloutonne pour MC-SVRP-TC
    Adapte l'approche existante au nouveau modèle
    """
    solution = MC_Solution(instance)
    
    # Pour chaque semaine
    for week in instance.T:
        # Demandes restantes (simplification: utilise poids/volume global)
        remaining_weight = instance.dw_AB[week]
        remaining_volume = instance.dv_AB[week]
        
        # Tant qu'il reste des demandes
        while remaining_weight > 0 or remaining_volume > 0:
            # Sélectionner le meilleur véhicule disponible
            best_vehicle = None
            best_efficiency = 0
            
            for (vtype, idx), vehicle in solution.vehicles.items():
                if week not in vehicle.weeks_used:
                    # Calculer l'efficacité (capacité / coût)
                    capacity = vehicle.weight_capacity + vehicle.volume_capacity
                    cost = instance.c[vtype]
                    efficiency = capacity / cost if cost > 0 else 0
                    
                    # Vérifier si le véhicule peut satisfaire une partie des demandes
                    can_handle_weight = vehicle.weight_capacity >= min(remaining_weight, vehicle.weight_capacity)
                    can_handle_volume = vehicle.volume_capacity >= min(remaining_volume, vehicle.volume_capacity)
                    
                    if (can_handle_weight or can_handle_volume) and efficiency > best_efficiency:
                        best_efficiency = efficiency
                        best_vehicle = (vtype, idx)
            
            if best_vehicle is None:
                # Aucun véhicule disponible - utiliser le premier disponible
                for (vtype, idx), vehicle in solution.vehicles.items():
                    if week not in vehicle.weeks_used:
                        best_vehicle = (vtype, idx)
                        break
            
            if best_vehicle is None:
                # Aucun véhicule disponible du tout - forcer l'utilisation
                best_vehicle = list(solution.vehicles.keys())[0]
            
            # Créer un transport avec ce véhicule
            vtype, idx = best_vehicle
            vehicle = solution.vehicles[best_vehicle]
            
            # Calculer les quantités à transporter
            weight_to_transport = min(remaining_weight, vehicle.weight_capacity)
            volume_to_transport = min(remaining_volume, vehicle.volume_capacity)
            
            # Créer un transport simplifié (sans produits détaillés pour l'instant)
            transport = MC_Transport(
                week=week,
                vehicle_idx=idx,
                vehicle_type=vtype,
                products_transported={"generic": max(weight_to_transport, volume_to_transport)},
                trip_sequence=len([t for t in solution.transports 
                                 if t.week == week and t.vehicle_type == vtype and t.vehicle_idx == idx]) + 1,
                instance=instance
            )
            
            # Ajouter le transport
            solution.transports.append(transport)
            vehicle.weeks_used.add(week)
            
            # Mettre à jour les demandes restantes
            remaining_weight = max(0, remaining_weight - weight_to_transport)
            remaining_volume = max(0, remaining_volume - volume_to_transport)
    
    # Évaluer la solution
    solution.evaluate()
    return solution

def mc_crossover(parent1, parent2, instance):
    """
    Croisement adapté pour MC-SVRP-TC
    Combine les affectations de véhicules des deux parents
    """
    child = MC_Solution(instance)
    
    # Pour chaque semaine, choisir les transports d'un parent
    for week in instance.T:
        source_parent = parent1 if random.random() < 0.5 else parent2
        
        # Copier les transports de cette semaine
        week_transports = [t for t in source_parent.transports if t.week == week]
        for transport in week_transports:
            new_transport = MC_Transport(
                week=transport.week,
                vehicle_idx=transport.vehicle_idx,
                vehicle_type=transport.vehicle_type,
                products_transported=copy.deepcopy(transport.products_transported),
                trip_sequence=transport.trip_sequence,
                instance=instance
            )
            child.transports.append(new_transport)
    
    # Évaluer et réparer si nécessaire
    child.evaluate()
    if not child.feasible:
        mc_repair_solution(child, instance)
    
    return child

def mc_repair_solution(solution, instance):
    """
    Répare une solution infaisable selon les contraintes MC-SVRP-TC
    """
    # Implémenter la réparation selon les contraintes spécifiques
    for week in instance.T:
        # Vérifier les demandes non satisfaites
        week_transports = [t for t in solution.transports if t.week == week]
        
        # Calculer les quantités transportées
        total_weight = sum(t.total_weight(instance) for t in week_transports)
        total_volume = sum(t.total_volume(instance) for t in week_transports)
        
        # Si déficit, ajouter des transports
        remaining_weight = max(0, instance.dw_AB[week] - total_weight)
        remaining_volume = max(0, instance.dv_AB[week] - total_volume)
        
        if remaining_weight > 0 or remaining_volume > 0:
            # Trouver un véhicule disponible
            for (vtype, idx), vehicle in solution.vehicles.items():
                if week not in vehicle.weeks_used:
                    # Créer un transport de réparation
                    repair_transport = MC_Transport(
                        week=week,
                        vehicle_idx=idx,
                        vehicle_type=vtype,
                        products_transported={"repair": max(remaining_weight, remaining_volume)},
                        instance=instance
                    )
                    solution.transports.append(repair_transport)
                    break
    
    solution.evaluate()

def mc_mutate(solution, instance, mutation_rate=0.3):
    """
    Mutation adaptée pour MC-SVRP-TC
    """
    mutated = copy.deepcopy(solution)
    
    for week in instance.T:
        if random.random() < mutation_rate:
            week_transports = [t for t in mutated.transports if t.week == week]
            
            if week_transports:
                # Choisir une opération de mutation
                operations = ["reassign_vehicle", "split_transport", "merge_transports"]
                operation = random.choice(operations)
                
                if operation == "reassign_vehicle":
                    # Réaffecter un transport à un autre véhicule
                    transport = random.choice(week_transports)
                    
                    # Trouver un véhicule alternatif
                    available_vehicles = [
                        (vtype, idx) for (vtype, idx), vehicle in mutated.vehicles.items()
                        if week not in vehicle.weeks_used and (vtype, idx) != (transport.vehicle_type, transport.vehicle_idx)
                    ]
                    
                    if available_vehicles:
                        new_vtype, new_idx = random.choice(available_vehicles)
                        new_vehicle = mutated.vehicles[(new_vtype, new_idx)]
                        
                        # Vérifier la capacité
                        if (transport.total_weight(instance) <= new_vehicle.weight_capacity and
                            transport.total_volume(instance) <= new_vehicle.volume_capacity):
                            
                            # Effectuer la réaffectation
                            transport.vehicle_type = new_vtype
                            transport.vehicle_idx = new_idx
    
    mutated.evaluate()
    if not mutated.feasible:
        mc_repair_solution(mutated, instance)
    
    return mutated

def mc_local_search(solution, instance, max_iterations=50):
    """
    Recherche locale adaptée pour MC-SVRP-TC
    """
    current = copy.deepcopy(solution)
    best = copy.deepcopy(solution)
    
    for iteration in range(max_iterations):
        improved = False
        
        # Essayer différentes améliorations locales
        # 1. Consolidation de véhicules
        consolidated = mc_consolidate_vehicles(current, instance)
        if consolidated and consolidated.fitness < current.fitness:
            current = consolidated
            if current.fitness < best.fitness:
                best = copy.deepcopy(current)
            improved = True
        
        # 2. Optimisation des affectations
        optimized = mc_optimize_assignments(current, instance)
        if optimized and optimized.fitness < current.fitness:
            current = optimized
            if current.fitness < best.fitness:
                best = copy.deepcopy(current)
            improved = True
        
        if not improved:
            break
    
    return best

def mc_consolidate_vehicles(solution, instance):
    """
    Consolide les véhicules pour réduire les coûts
    """
    improved = copy.deepcopy(solution)
    
    # Logique de consolidation spécifique au modèle MC-SVRP-TC
    # (À implémenter selon les besoins spécifiques)
    
    improved.evaluate()
    return improved if improved.fitness < solution.fitness else None

def mc_optimize_assignments(solution, instance):
    """
    Optimise les affectations de produits aux véhicules
    """
    improved = copy.deepcopy(solution)
    
    # Logique d'optimisation des affectations
    # (À implémenter selon les besoins spécifiques)
    
    improved.evaluate()
    return improved if improved.fitness < solution.fitness else None

def mc_memetic_algorithm(instance, population_size=20, generations=100, mutation_rate=0.3, 
                        local_search_freq=5):
    """
    Algorithme mémétique principal pour MC-SVRP-TC
    """
    print("Démarrage de l'algorithme mémétique MC-SVRP-TC...")
    
    # Générer la population initiale
    population = []
    for i in range(population_size):
        if i % 5 == 0:
            print(f"Génération solution initiale {i+1}/{population_size}")
        solution = mc_greedy_initial_solution(instance)
        population.append(solution)
    
    # Trouver la meilleure solution initiale
    best_solution = min(population, key=lambda s: s.fitness)
    print(f"Meilleure solution initiale: {best_solution}")
    
    # Boucle principale
    for gen in range(generations):
        if gen % 10 == 0:
            print(f"Génération {gen}/{generations}, meilleur coût: {best_solution.fitness:.2f}")
        
        # Recherche locale périodique
        if gen % local_search_freq == 0:
            for i in range(min(3, population_size)):
                improved = mc_local_search(population[i], instance)
                if improved.fitness < population[i].fitness:
                    population[i] = improved
                    if improved.fitness < best_solution.fitness:
                        best_solution = copy.deepcopy(improved)
        
        # Nouvelle génération
        new_population = []
        
        # Élitisme
        sorted_pop = sorted(population, key=lambda s: s.fitness)
        new_population.extend([copy.deepcopy(s) for s in sorted_pop[:2]])
        
        # Génération d'enfants
        while len(new_population) < population_size:
            parent1 = tournament_selection(population)
            parent2 = tournament_selection(population)
            
            child = mc_crossover(parent1, parent2, instance)
            
            if random.random() < mutation_rate:
                child = mc_mutate(child, instance)
            
            new_population.append(child)
        
        population = new_population
        
        # Mise à jour de la meilleure solution
        current_best = min(population, key=lambda s: s.fitness)
        if current_best.fitness < best_solution.fitness:
            best_solution = copy.deepcopy(current_best)
    
    # Recherche locale finale
    final_solution = mc_local_search(best_solution, instance, max_iterations=100)
    if final_solution.fitness < best_solution.fitness:
        best_solution = final_solution
    
    print(f"Solution finale: {best_solution}")
    return best_solution

def tournament_selection(population, tournament_size=3):
    """Sélection par tournoi"""
    tournament = random.sample(population, min(tournament_size, len(population)))
    return min(tournament, key=lambda s: s.fitness)

# Fonction principale d'exécution
def run_mc_svrp_algorithm(id_client, cible_longitude, cible_latitude):
    """
    Exécute l'algorithme mémétique MC-SVRP-TC avec les données de la base
    
    Args:
        id_client: ID du client
        cible_longitude: Longitude de destination
        cible_latitude: Latitude de destination
    
    Returns:
        MC_Solution: Meilleure solution trouvée
    """
    try:
        print("="*60)
        print("ALGORITHME MÉMÉTIQUE MC-SVRP-TC")
        print("="*60)
        
        # Créer l'instance avec vos données existantes
        print("Chargement des données...")
        instance = Instance(id_client, cible_longitude, cible_latitude)
        
        print(f"Instance créée:")
        print(f"- Client ID: {id_client}")
        print(f"- Distance A-B: {instance.d_AB} km")
        print(f"- Types de véhicules: {len(instance.L)}")
        print(f"- Véhicules disponibles: {sum(instance.m.values())}")
        print(f"- Horizon: {len(instance.T)} semaines")
        
        # Affichage des demandes
        total_weight = sum(instance.dw_AB.values())
        total_volume = sum(instance.dv_AB.values())
        print(f"- Demande totale: {total_weight:.1f} kg, {total_volume:.1f} m³")
        
        # Exécuter l'algorithme mémétique
        start_time = time.time()
        best_solution = mc_memetic_algorithm(
            instance=instance,
            population_size=15,  # Taille réduite pour plus de rapidité
            generations=50,      # Nombre de générations adapté
            mutation_rate=0.25,
            local_search_freq=5
        )
        end_time = time.time()
        
        print("\n" + "="*60)
        print("RÉSULTATS FINAUX")
        print("="*60)
        print(f"Temps d'exécution: {end_time - start_time:.2f} secondes")
        print(f"Solution: {best_solution}")
        
        if best_solution.feasible:
            print("\n✅ SOLUTION FAISABLE TROUVÉE")
            print_detailed_solution(best_solution, instance)
        else:
            print("\n❌ Aucune solution faisable trouvée")
            print("Vérifiez les contraintes et les capacités des véhicules")
        
        return best_solution
        
    except Exception as e:
        print(f"Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        return None

def print_detailed_solution(solution, instance):
    """
    Affiche les détails de la solution trouvée
    
    Args:
        solution: Solution MC-SVRP-TC
        instance: Instance du problème
    """
    print(f"\n📊 ANALYSE DE LA SOLUTION")
    print("-" * 40)
    
    # Statistiques générales
    vehicles_used = sum(1 for v in solution.vehicles.values() if v.is_used())
    print(f"Nombre de véhicules utilisés: {vehicles_used}")
    print(f"Coût total: {solution.total_cost:.2f}")
    print(f"Nombre de transports: {len(solution.transports)}")
    
    # Répartition par type de véhicule
    print(f"\n🚛 VÉHICULES PAR TYPE")
    print("-" * 40)
    vehicles_by_type = {}
    for (vtype, idx), vehicle in solution.vehicles.items():
        if vehicle.is_used():
            type_name = vehicle.type_name or f"Type {vtype}"
            if type_name not in vehicles_by_type:
                vehicles_by_type[type_name] = []
            vehicles_by_type[type_name].append(vehicle)
    
    for type_name, vehicles in vehicles_by_type.items():
        print(f"{type_name}: {len(vehicles)} véhicule(s)")
        for vehicle in vehicles:
            plate = vehicle.plate or f"V{vehicle.idx}"
            print(f"  - {plate}: {len(vehicle.weeks_used)} semaines, "
                  f"{vehicle.num_trips} voyages, {vehicle.duration:.1f}j")
    
    # Planning par semaine
    print(f"\n📅 PLANNING PAR SEMAINE")
    print("-" * 40)
    for week in sorted(instance.T):
        week_transports = [t for t in solution.transports if t.week == week]
        if week_transports:
            print(f"\nSemaine {week}: {len(week_transports)} transport(s)")
            
            # Grouper par véhicule
            transports_by_vehicle = {}
            for transport in week_transports:
                vehicle_key = (transport.vehicle_type, transport.vehicle_idx)
                if vehicle_key not in transports_by_vehicle:
                    transports_by_vehicle[vehicle_key] = []
                transports_by_vehicle[vehicle_key].append(transport)
            
            for (vtype, vidx), transports in transports_by_vehicle.items():
                vehicle = solution.vehicles[(vtype, vidx)]
                vehicle_name = vehicle.plate or f"V{vidx} ({vehicle.type_name})"
                
                total_weight = sum(t.total_weight(instance) for t in transports)
                total_volume = sum(t.total_volume(instance) for t in transports)
                
                print(f"  {vehicle_name}: {len(transports)} voyage(s)")
                print(f"    Charge: {total_weight:.1f}kg / {total_volume:.1f}m³")
                print(f"    Capacité: {vehicle.weight_capacity:.1f}kg / {vehicle.volume_capacity:.1f}m³")
                
                # Détails temporels
                total_time = sum(t.T_total for t in transports)
                print(f"    Temps total: {total_time:.1f}h")
    
    # Vérification des demandes
    print(f"\n✅ VÉRIFICATION DES DEMANDES")
    print("-" * 40)
    for week in instance.T:
        required_weight = instance.dw_AB[week]
        required_volume = instance.dv_AB[week]
        
        if required_weight > 0 or required_volume > 0:
            week_transports = [t for t in solution.transports if t.week == week]
            transported_weight = sum(t.total_weight(instance) for t in week_transports)
            transported_volume = sum(t.total_volume(instance) for t in week_transports)
            
            weight_status = "✅" if transported_weight >= required_weight else "❌"
            volume_status = "✅" if transported_volume >= required_volume else "❌"
            
            print(f"Semaine {week}:")
            print(f"  Poids: {transported_weight:.1f}/{required_weight:.1f}kg {weight_status}")
            print(f"  Volume: {transported_volume:.1f}/{required_volume:.1f}m³ {volume_status}")

def save_mc_solution(solution, instance, filename="mc_svrp_solution.json"):
    """
    Sauvegarde la solution MC-SVRP-TC dans un fichier JSON
    
    Args:
        solution: Solution à sauvegarder
        instance: Instance du problème
        filename: Nom du fichier
    """
    solution_data = {
        "metadata": {
            "client_id": instance.id_client,
            "distance_AB": instance.d_AB,
            "total_cost": solution.total_cost,
            "feasible": solution.feasible,
            "vehicles_used": sum(1 for v in solution.vehicles.values() if v.is_used()),
            "total_transports": len(solution.transports)
        },
        "vehicles": [],
        "transports": [],
        "weekly_summary": {}
    }
    
    # Sauvegarder les véhicules utilisés
    for (vtype, idx), vehicle in solution.vehicles.items():
        if vehicle.is_used():
            vehicle_data = {
                "type": vtype,
                "index": idx,
                "plate": vehicle.plate,
                "type_name": vehicle.type_name,
                "weight_capacity": vehicle.weight_capacity,
                "volume_capacity": vehicle.volume_capacity,
                "weeks_used": list(vehicle.weeks_used),
                "num_trips": vehicle.num_trips,
                "duration": vehicle.duration,
                "num_units_used": vehicle.num_units_used
            }
            solution_data["vehicles"].append(vehicle_data)
    
    # Sauvegarder les transports
    for transport in solution.transports:
        transport_data = {
            "week": transport.week,
            "vehicle_type": transport.vehicle_type,
            "vehicle_index": transport.vehicle_idx,
            "trip_sequence": transport.trip_sequence,
            "products_transported": transport.products_transported,
            "total_weight": transport.total_weight(instance),
            "total_volume": transport.total_volume(instance),
            "T_conduite": transport.T_conduite,
            "T_pauses": transport.T_pauses,
            "T_nuit": transport.T_nuit,
            "T_total": transport.T_total,
            "N_pauses": transport.N_pauses,
            "N_nuits": transport.N_nuits
        }
        solution_data["transports"].append(transport_data)
    
    # Résumé par semaine
    for week in instance.T:
        week_transports = [t for t in solution.transports if t.week == week]
        if week_transports:
            vehicles_used = set((t.vehicle_type, t.vehicle_idx) for t in week_transports)
            total_weight = sum(t.total_weight(instance) for t in week_transports)
            total_volume = sum(t.total_volume(instance) for t in week_transports)
            
            solution_data["weekly_summary"][str(week)] = {
                "transports": len(week_transports),
                "vehicles": len(vehicles_used),
                "total_weight": total_weight,
                "total_volume": total_volume,
                "demand_weight": instance.dw_AB[week],
                "demand_volume": instance.dv_AB[week]
            }
    
    # Écrire le fichier
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(solution_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Solution sauvegardée dans: {filename}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde: {e}")

def export_to_excel(solution, instance, filename="mc_svrp_planning.xlsx"):
    """
    Exporte la solution vers un fichier Excel pour analyse
    
    Args:
        solution: Solution MC-SVRP-TC
        instance: Instance du problème
        filename: Nom du fichier Excel
    """
    try:
        import pandas as pd
        
        # Données des véhicules
        vehicles_data = []
        for (vtype, idx), vehicle in solution.vehicles.items():
            if vehicle.is_used():
                vehicles_data.append({
                    'Type': vtype,
                    'Index': idx,
                    'Immatriculation': vehicle.plate or f'V{idx}',
                    'Type_Nom': vehicle.type_name or f'Type {vtype}',
                    'Capacité_Poids': vehicle.weight_capacity,
                    'Capacité_Volume': vehicle.volume_capacity,
                    'Semaines_Utilisées': len(vehicle.weeks_used),
                    'Nombre_Voyages': vehicle.num_trips,
                    'Durée_Jours': vehicle.duration,
                    'Unités_Utilisées': vehicle.num_units_used
                })
        
        # Données des transports
        transports_data = []
        for transport in solution.transports:
            vehicle = solution.vehicles[(transport.vehicle_type, transport.vehicle_idx)]
            transports_data.append({
                'Semaine': transport.week,
                'Véhicule_Type': transport.vehicle_type,
                'Véhicule_Index': transport.vehicle_idx,
                'Immatriculation': vehicle.plate or f'V{transport.vehicle_idx}',
                'Séquence': transport.trip_sequence,
                'Poids_Total': transport.total_weight(instance),
                'Volume_Total': transport.total_volume(instance),
                'Temps_Conduite': transport.T_conduite,
                'Temps_Pauses': transport.T_pauses,
                'Temps_Nuit': transport.T_nuit,
                'Temps_Total': transport.T_total,
                'Nombre_Pauses': transport.N_pauses,
                'Nombre_Nuits': transport.N_nuits
            })
        
        # Résumé par semaine
        weekly_data = []
        for week in instance.T:
            week_transports = [t for t in solution.transports if t.week == week]
            vehicles_used = set((t.vehicle_type, t.vehicle_idx) for t in week_transports)
            
            total_weight = sum(t.total_weight(instance) for t in week_transports)
            total_volume = sum(t.total_volume(instance) for t in week_transports)
            
            weekly_data.append({
                'Semaine': week,
                'Nombre_Transports': len(week_transports),
                'Nombre_Véhicules': len(vehicles_used),
                'Poids_Transporté': total_weight,
                'Volume_Transporté': total_volume,
                'Demande_Poids': instance.dw_AB[week],
                'Demande_Volume': instance.dv_AB[week],
                'Satisfaction_Poids': total_weight >= instance.dw_AB[week],
                'Satisfaction_Volume': total_volume >= instance.dv_AB[week]
            })
        
        # Création du fichier Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Feuille véhicules
            pd.DataFrame(vehicles_data).to_excel(
                writer, sheet_name='Véhicules', index=False
            )
            
            # Feuille transports
            pd.DataFrame(transports_data).to_excel(
                writer, sheet_name='Transports', index=False
            )
            
            # Feuille résumé hebdomadaire
            pd.DataFrame(weekly_data).to_excel(
                writer, sheet_name='Résumé_Hebdomadaire', index=False
            )
            
            # Feuille récapitulatif
            summary_data = [{
                'Métrique': 'Coût Total',
                'Valeur': solution.total_cost
            }, {
                'Métrique': 'Véhicules Utilisés',
                'Valeur': sum(1 for v in solution.vehicles.values() if v.is_used())
            }, {
                'Métrique': 'Nombre de Transports',
                'Valeur': len(solution.transports)
            }, {
                'Métrique': 'Solution Faisable',
                'Valeur': 'Oui' if solution.feasible else 'Non'
            }, {
                'Métrique': 'Distance A-B (km)',
                'Valeur': instance.d_AB
            }, {
                'Métrique': 'Client ID',
                'Valeur': instance.id_client
            }]
            
            pd.DataFrame(summary_data).to_excel(
                writer, sheet_name='Récapitulatif', index=False
            )
        
        print(f"📊 Données exportées vers: {filename}")
        
    except ImportError:
        print("⚠️  Pandas non disponible pour l'export Excel")
    except Exception as e:
        print(f"Erreur lors de l'export Excel: {e}")

# Test et démonstration
if __name__ == "__main__":
    print("🧪 Test de l'algorithme MC-SVRP-TC")
    
    # Exemple d'utilisation (remplacez par vos vraies données)
    test_client_id = 1
    test_longitude = 3.0
    test_latitude = 36.0
    
    try:
        solution = run_mc_svrp_algorithm(test_client_id, test_longitude, test_latitude)
        
        if solution and solution.feasible:
            # Sauvegarder les résultats
            save_mc_solution(solution, solution.instance)
            export_to_excel(solution, solution.instance)
            
            print("\n🎉 Algorithme exécuté avec succès!")
        else:
            print("❌ Échec de l'exécution ou solution non faisable")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()