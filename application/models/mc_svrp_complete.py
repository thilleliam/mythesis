# FILE: application/models/mc_svrp_complete.py
# REMPLACEMENT COMPLET DE VOTRE MÉTAHEURISTIQUE PAR MC-SVRP-TC

# ========================================
# IMPORTS ET CONFIGURATION DE BASE
# ========================================
import numpy as np
import random
import copy
import time
import json
import math
import sys
from collections import defaultdict
from sqlalchemy import func
from application.config import Base
from application.database import SessionLocal
from datetime import date

sys.stdout.reconfigure(encoding='utf-8')


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
    """Véhicule individuel avec capacités hétérogènes selon le modèle MC-SVRP-TC"""
    
    def __init__(self, vehicle_type, vehicle_idx, weight_capacity, volume_capacity, instance=None):
        self.type = vehicle_type  # ℓ
        self.idx = vehicle_idx    # k  
        self.weight_capacity = weight_capacity  # C^w_{ℓ,k}
        self.volume_capacity = volume_capacity  # C^v_{ℓ,k}
        self.weeks_used = set()
        self.num_units_used = 0  # n_{ℓ,k}
        self.num_trips = 0       # m_{ℓ,k}
        self.duration = 0.0      # τ_{ℓ,k}
        self.total_time_accumulated = 0.0
        
        # Informations additionnelles
        self.plate = None
        self.type_name = None
        if instance is not None:
            self.plate = instance.get_vehicle_plate(vehicle_type, vehicle_idx)
            self.type_name = instance.get_vehicle_type_name(vehicle_type)
    
    def is_used(self):
        return len(self.weeks_used) > 0
    
    def reset_usage(self):
        self.weeks_used.clear()
        self.num_units_used = 0
        self.num_trips = 0
        self.duration = 0.0
        self.total_time_accumulated = 0.0

class MC_Transport:
    """Transport avec variables temporelles complètes du modèle MC-SVRP-TC"""
    
    def __init__(self, week, vehicle_idx, vehicle_type, weight_transported=0, volume_transported=0,
                 products_transported=None, trip_sequence=1, instance=None):
        self.week = week
        self.vehicle_idx = vehicle_idx
        self.vehicle_type = vehicle_type
        self.trip_sequence = trip_sequence
        
        # Quantités transportées
        self.weight_transported = weight_transported
        self.volume_transported = volume_transported
        self.products_transported = products_transported or {}
        
        # Variables temporelles du modèle (34-38)
        self.T_conduite = 0.0    # T^conduite_{ℓ,k,t}
        self.T_pauses = 0.0      # T^pauses_{ℓ,k,t}
        self.T_nuit = 0.0        # T^nuit_{ℓ,k,t}
        self.N_pauses = 0        # N^pauses_{ℓ,k,t}
        self.N_nuits = 0         # N^nuits_{ℓ,k,t}
        self.T_total = 0.0       # Temps total du voyage
        
        # Variables de contrainte
        self.delta = True        # δ_{ℓ,k}
        
        # Informations véhicule
        self.vehicle_plate = None
        self.vehicle_type_name = None
        if instance is not None:
            self.vehicle_plate = instance.get_vehicle_plate(vehicle_type, vehicle_idx)
            self.vehicle_type_name = instance.get_vehicle_type_name(vehicle_type)
    
    def total_weight(self, instance=None):
        return self.weight_transported
    
    def total_volume(self, instance=None):
        return self.volume_transported

class MC_TemporalConstraints:
    """Contraintes temporelles exactes selon équations (49-58)"""
    
    @staticmethod
    def calculate_exact_temporal_variables(transport, vehicle, instance):
        """Calcule toutes les variables temporelles selon les équations exactes"""
        
        vtype = transport.vehicle_type
        
        # Paramètres du modèle
        D = instance.d_AB        # Distance A-B (17)
        Tload = 1.5             # Temps chargement (18)
        Tunload = 1.5           # Temps déchargement (19)
        Twork = 8.0             # Temps travail/jour (20)
        Tbreak = 0.25           # Durée pause (21)
        Tnight = 13.0           # Durée arrêt nocturne (22)
        
        # Vitesse du véhicule
        S_lk = instance.V[vtype] if instance.V[vtype] > 0 else 75
        
        # Équation (49): Temps de conduite
        transport.T_conduite = (2 * D) / S_lk
        
        # Équation (50): Nombre de pauses
        if transport.T_conduite > 2:
            transport.N_pauses = max(0, math.floor((transport.T_conduite - 2) / 2.0) + 1)
        else:
            transport.N_pauses = 0
        
        # Équation (51): Temps de pauses
        transport.T_pauses = transport.N_pauses * Tbreak
        
        # Équation (52): Détection arrêts nocturnes
        total_operation_time = transport.T_conduite + transport.T_pauses + Tload + Tunload
        if total_operation_time > 11:
            transport.N_nuits = math.floor((total_operation_time - 11) / 24) + 1
        else:
            transport.N_nuits = 0
        
        # Équation (53): Temps d'arrêt nocturne
        transport.T_nuit = transport.N_nuits * Tnight
        
        # Équation (54): Temps total
        transport.T_total = (transport.T_conduite + transport.T_pauses + 
                           transport.T_nuit + Tload + Tunload)
        
        # Équation (55): Durée véhicule
        if not hasattr(vehicle, 'total_time_accumulated'):
            vehicle.total_time_accumulated = 0
        
        vehicle.total_time_accumulated += transport.T_total
        vehicle.duration = math.ceil(vehicle.total_time_accumulated / Twork)
        
        return transport

class MC_ProductMixingStrategy:
    """Stratégie de mélange des produits selon équations (64-87)"""
    
    def __init__(self, instance):
        self.instance = instance
        self.product_pool = {}
        self.initialize_product_pools()
    def update_product_pool(self, week, weight_transported, volume_transported):
        """Équations (65, 78): Mise à jour du pool"""
        self.product_pool[week]['weight_remaining'] -= weight_transported
        self.product_pool[week]['volume_remaining'] -= volume_transported
        
        self.product_pool[week]['weight_remaining'] = max(0, self.product_pool[week]['weight_remaining'])
        self.product_pool[week]['volume_remaining'] = max(0, self.product_pool[week]['volume_remaining'])
        
        print(f"    Pool mis à jour: {self.product_pool[week]['weight_remaining']:.1f}kg, "
            f"{self.product_pool[week]['volume_remaining']:.1f}m³ restants")
    def initialize_product_pools(self):
        """Équations (64, 77): Pool^initial_p = q_p"""
        for week in self.instance.T:
            self.product_pool[week] = {
                'weight_initial': self.instance.dw_AB[week],
                'volume_initial': self.instance.dv_AB[week],
                'weight_remaining': self.instance.dw_AB[week],
                'volume_remaining': self.instance.dv_AB[week]
            }
    
    def select_optimal_mixing_strategy(self, vehicle, week):
        """Équations (79-81): Sélection automatique de stratégie"""
        
        # Capacités individuelles (12-13)
        C_w_lk = vehicle.weight_capacity
        C_v_lk = vehicle.volume_capacity
        
        # Pool restant
        pool_weight = self.product_pool[week]['weight_remaining']
        pool_volume = self.product_pool[week]['volume_remaining']
        
        if pool_weight == 0 and pool_volume == 0:
            return 'homogeneous'
        
        # Équation (79-80): Taux d'utilisation
        cap_max_weight = C_w_lk if pool_weight > 0 else 0
        cap_max_volume = C_v_lk if pool_volume > 0 else 0
        
        util_weight = cap_max_weight / pool_weight if pool_weight > 0 else 0
        util_volume = cap_max_volume / pool_volume if pool_volume > 0 else 0
        
        # Équation (81): Règle de sélection
        max_util = max(util_weight, util_volume)
        
        if max_util > 0.7:
            print(f"  Stratégie HOMOGÈNE (Util={max_util:.2f})")
            return 'homogeneous'
        else:
            print(f"  Stratégie MÉLANGE INTELLIGENT (Util={max_util:.2f})")
            return 'intelligent_mixing'
    
    def apply_homogeneous_priority_strategy(self, vehicle, week):
        """CORRIGÉ: Transporte POIDS ET VOLUMES selon capacités"""
        pool = self.product_pool[week]
        
        # Calcul des ratios de transport selon les capacités
        weight_capacity_ratio = min(1.0, vehicle.weight_capacity / pool['weight_remaining']) if pool['weight_remaining'] > 0 else 1.0
        volume_capacity_ratio = min(1.0, vehicle.volume_capacity / pool['volume_remaining']) if pool['volume_remaining'] > 0 else 1.0
        
        # Prendre le ratio le plus restrictif pour équilibrer
        transport_ratio = min(weight_capacity_ratio, volume_capacity_ratio)
        
        # Quantités à transporter selon le ratio
        weight_to_transport = pool['weight_remaining'] * transport_ratio
        volume_to_transport = pool['volume_remaining'] * transport_ratio
        
        # S'assurer de ne pas dépasser les capacités
        weight_to_transport = min(weight_to_transport, vehicle.weight_capacity)
        volume_to_transport = min(volume_to_transport, vehicle.volume_capacity)
        
        print(f"    Homogène: {weight_to_transport:.1f}kg, {volume_to_transport:.1f}m³")
        
        return weight_to_transport, volume_to_transport
    
    def apply_intelligent_mixing_strategy(self, vehicle, week):
        """CORRIGÉ: Mélange intelligent avec transport poids ET volumes"""
        pool = self.product_pool[week]
        
        # Stratégies de mélange avec ratios équilibrés
        strategies = []
        
        # Stratégie 1: Priorité équilibrée
        if pool['weight_remaining'] > 0 and pool['volume_remaining'] > 0:
            weight_ratio = min(1.0, vehicle.weight_capacity / pool['weight_remaining'])
            volume_ratio = min(1.0, vehicle.volume_capacity / pool['volume_remaining'])
            balanced_ratio = min(weight_ratio, volume_ratio)
            
            strategies.append({
                'name': 'balanced',
                'weight': pool['weight_remaining'] * balanced_ratio,
                'volume': pool['volume_remaining'] * balanced_ratio,
                'utilization': (balanced_ratio * pool['weight_remaining'] / vehicle.weight_capacity + 
                            balanced_ratio * pool['volume_remaining'] / vehicle.volume_capacity)
            })
        
        # Stratégie 2: Priorité poids avec volume proportionnel
        if pool['weight_remaining'] > 0:
            weight_transport = min(pool['weight_remaining'], vehicle.weight_capacity)
            weight_ratio = weight_transport / pool['weight_remaining']
            volume_transport = min(pool['volume_remaining'] * weight_ratio, vehicle.volume_capacity)
            
            strategies.append({
                'name': 'weight_priority',
                'weight': weight_transport,
                'volume': volume_transport,
                'utilization': (weight_transport / vehicle.weight_capacity + 
                            volume_transport / vehicle.volume_capacity)
            })
        
        # Stratégie 3: Priorité volume avec poids proportionnel
        if pool['volume_remaining'] > 0:
            volume_transport = min(pool['volume_remaining'], vehicle.volume_capacity)
            volume_ratio = volume_transport / pool['volume_remaining']
            weight_transport = min(pool['weight_remaining'] * volume_ratio, vehicle.weight_capacity)
            
            strategies.append({
                'name': 'volume_priority',
                'weight': weight_transport,
                'volume': volume_transport,
                'utilization': (weight_transport / vehicle.weight_capacity + 
                            volume_transport / vehicle.volume_capacity)
            })
        
        # Sélectionner la meilleure stratégie
        if strategies:
            best_strategy = max(strategies, key=lambda s: s['utilization'])
            
            print(f"    Intelligent ({best_strategy['name']}): "
                f"{best_strategy['weight']:.1f}kg, {best_strategy['volume']:.1f}m³ "
                f"(Util: {best_strategy['utilization']:.2f})")
            
            return best_strategy['weight'], best_strategy['volume']
        
        return 0, 0

class MC_Solution:
    """Solution complète MC-SVRP-TC avec toutes les contraintes"""
    
    def __init__(self, instance):
        self.instance = instance
        self.vehicles = {}
        self.transports = []
        self.fitness = float('inf')
        self.feasible = False
        
        # Variables du modèle mathématique
        self.u_types = {}      # u_ℓ (25)
        self.x_vehicles = {}   # x_{ℓ,k} (24)
        self.n_units = {}      # n_{ℓ,k} (26)
        self.m_trips = {}      # m_{ℓ,k} (27)
        self.tau_duration = {} # τ_{ℓ,k} (32)
        self.delta_constraint = {} # δ_{ℓ,k} (33)
        
        self.total_cost = 0.0
        self.product_mixing = MC_ProductMixingStrategy(instance)
        
        self._initialize_vehicles()
    
    def _initialize_vehicles(self):
        """Initialise véhicules avec capacités individuelles"""
        for vtype, count in self.instance.m.items():
            for i in range(1, count + 1):
                base_weight = self.instance.L[vtype]["Qw"]
                base_volume = self.instance.L[vtype]["Qv"]
                
                # Variation individuelle (±5%)
                weight_variation = 1.0 + random.uniform(-0.05, 0.05)
                volume_variation = 1.0 + random.uniform(-0.05, 0.05)
                
                vehicle = MC_Vehicle(
                    vehicle_type=vtype,
                    vehicle_idx=i,
                    weight_capacity=max(0, base_weight * weight_variation),
                    volume_capacity=max(0, base_volume * volume_variation),
                    instance=self.instance
                )
                
                self.vehicles[(vtype, i)] = vehicle
                
                # Variables de décision initiales
                self.x_vehicles[(vtype, i)] = 0
                self.n_units[(vtype, i)] = 0
                self.m_trips[(vtype, i)] = 0
                self.tau_duration[(vtype, i)] = 0.0
                self.delta_constraint[(vtype, i)] = True
            
            self.u_types[vtype] = 0
    
    def create_optimized_transport(self, week, vehicle_key):
        """Crée transport optimisé avec stratégie de mélange"""
        vtype, k = vehicle_key
        vehicle = self.vehicles[vehicle_key]
        
        # Sélectionner stratégie
        strategy = self.product_mixing.select_optimal_mixing_strategy(vehicle, week)
        
        # Appliquer stratégie
        if strategy == 'homogeneous':
            weight, volume = self.product_mixing.apply_homogeneous_priority_strategy(vehicle, week)
        else:
            weight, volume = self.product_mixing.apply_intelligent_mixing_strategy(vehicle, week)
        
        if weight > 0 or volume > 0:
            transport = MC_Transport(
                week=week,
                vehicle_idx=k,
                vehicle_type=vtype,
                weight_transported=weight,
                volume_transported=volume,
                trip_sequence=len([t for t in self.transports 
                                 if t.week == week and t.vehicle_type == vtype and t.vehicle_idx == k]) + 1,
                instance=self.instance
            )
            
            # Mettre à jour pool
            self.product_mixing.update_product_pool(week, weight, volume)
            return transport
        
        return None
    
    def evaluate(self):
        """Évaluation complète avec toutes les contraintes"""
        self._reset_all_variables()
        self._calculate_all_variables()
        self.feasible = self._check_all_constraints()
        
        if self.feasible:
            self.fitness = self._calculate_objective_function()
        else:
            self.fitness = float('inf')
        
        return self.fitness
    
    def _reset_all_variables(self):
        """Reset toutes les variables"""
        for (vtype, k) in self.vehicles.keys():
            self.x_vehicles[(vtype, k)] = 0
            self.n_units[(vtype, k)] = 0
            self.m_trips[(vtype, k)] = 0
            self.tau_duration[(vtype, k)] = 0.0
            self.delta_constraint[(vtype, k)] = True
            self.vehicles[(vtype, k)].reset_usage()
        
        for vtype in self.instance.L.keys():
            self.u_types[vtype] = 0
    
    def _calculate_all_variables(self):
        """Calcule toutes les variables du modèle"""
        for transport in self.transports:
            vehicle_key = (transport.vehicle_type, transport.vehicle_idx)
            vehicle = self.vehicles[vehicle_key]
            
            # Variables de sélection
            self.x_vehicles[vehicle_key] = 1
            self.u_types[transport.vehicle_type] = 1
            self.m_trips[vehicle_key] += 1
            
            # Contraintes temporelles exactes
            MC_TemporalConstraints.calculate_exact_temporal_variables(transport, vehicle, self.instance)
            vehicle.weeks_used.add(transport.week)
        
        # Calcul final des durées et unités
        Hmax = 7.0
        for (vtype, k), vehicle in self.vehicles.items():
            if self.x_vehicles[(vtype, k)] == 1:
                self.tau_duration[(vtype, k)] = vehicle.duration
                
                # Équations (56-58)
                if vehicle.duration <= Hmax:
                    self.delta_constraint[(vtype, k)] = True
                    self.n_units[(vtype, k)] = 1
                else:
                    self.delta_constraint[(vtype, k)] = False
                    self.n_units[(vtype, k)] = math.ceil(vehicle.duration / Hmax)
                
                vehicle.duration = min(vehicle.duration, Hmax)
    
    def _check_all_constraints(self):
        """Vérifie toutes les contraintes du modèle"""
        
        # Contraintes de cohérence (28-30)
        M = 1000
        for vtype in self.instance.L.keys():
            for k in range(1, self.instance.m[vtype] + 1):
                if self.x_vehicles[(vtype, k)] > self.u_types[vtype]:
                    return False
            
            sum_x = sum(self.x_vehicles[(vtype, k)] for k in range(1, self.instance.m[vtype] + 1))
            if self.u_types[vtype] > sum_x:
                return False
            
            for k in range(1, self.instance.m[vtype] + 1):
                if self.n_units[(vtype, k)] > M * self.x_vehicles[(vtype, k)]:
                    return False
        
        # Contraintes de capacité (43-44)
        for transport in self.transports:
            vehicle_key = (transport.vehicle_type, transport.vehicle_idx)
            vehicle = self.vehicles[vehicle_key]
            
            if (transport.weight_transported > vehicle.weight_capacity or
                transport.volume_transported > vehicle.volume_capacity):
                return False
        
        # Contrainte de demande (45)
        for week in self.instance.T:
            week_transports = [t for t in self.transports if t.week == week]
            
            transported_weight = sum(t.weight_transported for t in week_transports)
            transported_volume = sum(t.volume_transported for t in week_transports)
            
            required_weight = self.instance.dw_AB[week]
            required_volume = self.instance.dv_AB[week]
            
            tolerance = 0.01
            if (transported_weight < required_weight * (1 - tolerance) or
                transported_volume < required_volume * (1 - tolerance)):
                return False
        
        # Contrainte (59): Au moins un type utilisé
        if sum(self.u_types.values()) < 1:
            return False
        
        return True
    
    def _calculate_objective_function(self):
        """Équation (39): Fonction objectif exacte"""
        total_cost = 0.0
        
        for vtype in self.instance.L.keys():
            for k in range(1, self.instance.m[vtype] + 1):
                if self.x_vehicles[(vtype, k)] == 1:
                    
                    n_lk = self.n_units[(vtype, k)]
                    tau_lk = self.tau_duration[(vtype, k)]
                    m_lk = self.m_trips[(vtype, k)]
                    
                    F_l = self.instance.c[vtype]
                    G_l = self.instance.dc
                    D = self.instance.d_AB
                    
                    # Équation (39)
                    fixed_cost = n_lk * tau_lk * F_l
                    
                    if n_lk > 0:
                        variable_cost = m_lk * n_lk * (2 * D - D / n_lk) * G_l
                    else:
                        variable_cost = 0
                    
                    total_cost += fixed_cost + variable_cost
        
        self.total_cost = total_cost
        return total_cost
    
    def __str__(self):
        vehicles_used = sum(1 for v in self.vehicles.values() if v.is_used())
        return f"MC_Solution(transports={len(self.transports)}, véhicules={vehicles_used}, " \
               f"coût={self.total_cost:.2f}, faisable={self.feasible})"

# ========================================
# ALGORITHME PRINCIPAL COMPLET
# ========================================

def mc_complete_greedy_algorithm(instance):
    """CORRIGÉ: Algorithme glouton qui transporte poids ET volumes"""
    
    solution = MC_Solution(instance)
    
    print("🚀 Génération MC-SVRP-TC (poids + volumes)...")
    
    for week in instance.T:
        print_week_header(week)
        print(f"📅 Traitement Semaine {week}:")
        
        initial_weight = solution.product_mixing.product_pool[week]['weight_initial']
        initial_volume = solution.product_mixing.product_pool[week]['volume_initial']
        print(f"  Pool initial: {initial_weight:.1f}kg, {initial_volume:.1f}m³")
        
        iteration = 0
        max_iterations = 20  # Éviter les boucles infinies
        
        while ((solution.product_mixing.product_pool[week]['weight_remaining'] > 0.1 or 
                solution.product_mixing.product_pool[week]['volume_remaining'] > 0.1) and 
               iteration < max_iterations):
            
            iteration += 1
            
            # Afficher l'état actuel du pool
            remaining_w = solution.product_mixing.product_pool[week]['weight_remaining']
            remaining_v = solution.product_mixing.product_pool[week]['volume_remaining']
            print(f"  Restant: {remaining_w:.1f}kg, {remaining_v:.1f}m³")
            # NOU
            best_vehicle = None
            best_efficiency = 0
            
            for (vtype, k), vehicle in solution.vehicles.items():
                if week not in vehicle.weeks_used:
                    # Calculer efficacité pour transport poids ET volumes
                    weight_efficiency = vehicle.weight_capacity / max(remaining_w, 1)
                    volume_efficiency = vehicle.volume_capacity / max(remaining_v, 1)
                    combined_efficiency = min(weight_efficiency, volume_efficiency)
                    
                    cost = instance.c[vtype] if instance.c[vtype] > 0 else 1
                    total_efficiency = combined_efficiency / cost
                    
                    if total_efficiency > best_efficiency:
                        best_efficiency = total_efficiency
                        best_vehicle = (vtype, k)
            
            if best_vehicle is None:
                print(f"  ❌ Aucun véhicule disponible")
                break
            
            # Création transport optimisé
            transport = solution.create_optimized_transport(week, best_vehicle)
            
            if transport is None or (transport.weight_transported <= 0.1 and transport.volume_transported <= 0.1):
                print(f"  Rien à transporter, arrêt")
                break
            # Calculer pools avant/après pour les prints détaillés
            pool_before = {
                'weight': solution.product_mixing.product_pool[week]['weight_remaining'] + transport.weight_transported,
                'volume': solution.product_mixing.product_pool[week]['volume_remaining'] + transport.volume_transported
            }

            # Ajouter à la solution
            solution.transports.append(transport)
            solution.vehicles[best_vehicle].weeks_used.add(week)

            vtype, k = best_vehicle
            vehicle = solution.vehicles[best_vehicle]
            print(f"  ✅ {vehicle.plate}: {transport.weight_transported:.1f}kg, {transport.volume_transported:.1f}m³")

            # NOUVEAU: Print ultra-détaillé
            pool_after = {
                'weight': solution.product_mixing.product_pool[week]['weight_remaining'],
                'volume': solution.product_mixing.product_pool[week]['volume_remaining']
            }

            print_detailed_transport_info(
                transport, 
                vehicle, 
                week, 
                len([t for t in solution.transports if t.week == week]), 
                pool_before, 
                pool_after
            )
        
        # NOUVEAU: Récapitulatif détaillé de la semaine
        week_transports = [t for t in solution.transports if t.week == week]
        print_week_summary_detailed(week, week_transports, instance, solution.product_mixing)
                     

    # Évaluation finale
    solution.evaluate()
    
    print(f"\nSOLUTION FINALE:")
    print(f"- Transports: {len(solution.transports)}")
    print(f"- Coût total: {solution.total_cost:.2f}")
    print(f"- Faisable: {'✅' if solution.feasible else '❌'}")
    
    return solution

# ========================================
# FONCTIONS D'AFFICHAGE POUR LA METAHEURISTIQUE
# ========================================
def format_time_detailed(hours):
    """Convertit les heures décimales en format HH:MM"""
    if hours is None:
        return "N/A"
    
    total_minutes = int(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60
    
    # Gérer les heures > 24 (jour suivant)
    if h >= 24:
        days = h // 24
        h = h % 24
        return f"J+{days} {h:02d}:{m:02d}"
    else:
        return f"{h:02d}:{m:02d}"

def print_transport_separator():
    """Séparateur visuel pour les transports"""
    print("    " + "─" * 80)

def print_week_header(week):
    """En-tête détaillé pour chaque semaine"""
    print("\n" + "═" * 90)
    print(f"📅 SEMAINE {week} - ANALYSE DÉTAILLÉE DES TRANSPORTS")
    print("═" * 90)

def print_detailed_transport_info(transport, vehicle, week_number, transport_number, pool_before, pool_after):
    """
    Print ultra-détaillé pour chaque transport
    À ajouter après la création de chaque transport
    """
    print_transport_separator()
    print(f"    🚛 TRANSPORT #{transport_number} - SEMAINE {week_number}")
    print_transport_separator()
    
    # Informations véhicule
    print(f"    📋 VÉHICULE:")
    print(f"       • Immatriculation: {vehicle.plate or 'N/A'}")
    print(f"       • Type: {vehicle.type_name or f'Type {vehicle.type}'}")
    print(f"       • Capacité poids: {vehicle.weight_capacity:.1f} kg")
    print(f"       • Capacité volume: {vehicle.volume_capacity:.1f} m³")
    print(f"       • Utilisation poids: {(transport.weight_transported/vehicle.weight_capacity*100):.1f}%")
    print(f"       • Utilisation volume: {(transport.volume_transported/vehicle.volume_capacity*100):.1f}%")
    
    # Charge transportée
    print(f"    📦 CHARGE TRANSPORTÉE:")
    print(f"       • Poids: {transport.weight_transported:.2f} kg")
    print(f"       • Volume: {transport.volume_transported:.2f} m³")
    print(f"       • Séquence voyage: {transport.trip_sequence}")
    
    # Détails temporels (variables du modèle équations 49-58)
    print(f"    ⏱️  ANALYSE TEMPORELLE DÉTAILLÉE:")
    print(f"       • Temps conduite (T^conduite): {transport.T_conduite:.2f}h ({format_time_detailed(transport.T_conduite)})")
    print(f"       • Nombre pauses (N^pauses): {transport.N_pauses}")
    print(f"       • Temps pauses (T^pauses): {transport.T_pauses:.2f}h ({format_time_detailed(transport.T_pauses)})")
    print(f"       • Nombre nuits (N^nuits): {transport.N_nuits}")
    print(f"       • Temps nuits (T^nuit): {transport.T_nuit:.2f}h ({format_time_detailed(transport.T_nuit)})")
    print(f"       • Temps total (T^total): {transport.T_total:.2f}h ({format_time_detailed(transport.T_total)})")
    
    # Horaires détaillés (simulation)
    print(f"    🕐 PLANNING HORAIRE SIMULÉ:")
    heure_debut = 7.0  # 07:00 début journée
    heure_chargement_fin = heure_debut + 1.5  # Temps chargement
    heure_depart_A = heure_chargement_fin
    heure_arrivee_B = heure_depart_A + (transport.T_conduite / 2) + (transport.T_pauses / 2)
    heure_dechargement_fin = heure_arrivee_B + 1.5  # Temps déchargement
    heure_depart_B = heure_dechargement_fin
    heure_retour_A = heure_depart_B + (transport.T_conduite / 2) + (transport.T_pauses / 2)
    
    print(f"       • Début chargement A: {format_time_detailed(heure_debut)}")
    print(f"       • Fin chargement A: {format_time_detailed(heure_chargement_fin)}")
    print(f"       • Départ site A: {format_time_detailed(heure_depart_A)}")
    print(f"       • Arrivée site B: {format_time_detailed(heure_arrivee_B)}")
    print(f"       • Fin déchargement B: {format_time_detailed(heure_dechargement_fin)}")
    print(f"       • Départ retour B: {format_time_detailed(heure_depart_B)}")
    print(f"       • Retour site A: {format_time_detailed(heure_retour_A)}")
    
    if transport.N_nuits > 0:
        print(f"       • ⚠️  ARRÊT NOCTURNE REQUIS ({transport.N_nuits} nuit(s))")
    
    # État des pools avant/après
    print(f"    📊 ÉTAT DES POOLS DE PRODUITS:")
    print(f"       • AVANT transport:")
    print(f"         - Poids restant: {pool_before['weight']:.2f} kg")
    print(f"         - Volume restant: {pool_before['volume']:.2f} m³")
    print(f"       • APRÈS transport:")
    print(f"         - Poids restant: {pool_after['weight']:.2f} kg")
    print(f"         - Volume restant: {pool_after['volume']:.2f} m³")
    print(f"       • TRANSPORTÉ:")
    print(f"         - Poids: -{transport.weight_transported:.2f} kg ({(transport.weight_transported/pool_before['weight']*100):.1f}% du restant)")
    print(f"         - Volume: -{transport.volume_transported:.2f} kg ({(transport.volume_transported/pool_before['volume']*100):.1f}% du restant)")

def print_week_summary_detailed(week, transports, instance, product_mixing):
    """
    Récapitulatif ultra-détaillé par semaine
    À ajouter à la fin du traitement de chaque semaine
    """
    if not transports:
        print(f"\n📅 SEMAINE {week}: Aucun transport nécessaire")
        return
    
    print(f"\n" + "╔" + "═" * 88 + "╗")
    print(f"║{f' RÉCAPITULATIF DÉTAILLÉ SEMAINE {week} ':^88}║")
    print(f"╚" + "═" * 88 + "╝")
    
    # Statistiques générales
    total_weight = sum(t.weight_transported for t in transports)
    total_volume = sum(t.volume_transported for t in transports)
    total_time = sum(t.T_total for t in transports)
    vehicles_used = set((t.vehicle_type, t.vehicle_idx) for t in transports)
    
    print(f"📈 STATISTIQUES GÉNÉRALES:")
    print(f"   • Nombre de transports: {len(transports)}")
    print(f"   • Véhicules différents utilisés: {len(vehicles_used)}")
    print(f"   • Poids total transporté: {total_weight:.2f} kg")
    print(f"   • Volume total transporté: {total_volume:.2f} m³")
    print(f"   • Temps cumulé des transports: {total_time:.2f}h ({format_time_detailed(total_time)})")
    
    # Demandes vs transporté
    demand_weight = instance.dw_AB[week]
    demand_volume = instance.dv_AB[week]
    remaining_weight = product_mixing.product_pool[week]['weight_remaining']
    remaining_volume = product_mixing.product_pool[week]['volume_remaining']
    
    print(f"\n📊 SATISFACTION DES DEMANDES:")
    print(f"   • Demande poids: {demand_weight:.2f} kg")
    print(f"   • Transporté poids: {total_weight:.2f} kg")
    print(f"   • Restant poids: {remaining_weight:.2f} kg")
    print(f"   • Taux satisfaction poids: {((demand_weight-remaining_weight)/demand_weight*100):.1f}%")
    print(f"   • Demande volume: {demand_volume:.2f} m³")
    print(f"   • Transporté volume: {total_volume:.2f} m³")
    print(f"   • Restant volume: {remaining_volume:.2f} m³")
    print(f"   • Taux satisfaction volume: {((demand_volume-remaining_volume)/demand_volume*100):.1f}%")
    
    # Détail par véhicule
    print(f"\n🚛 UTILISATION PAR VÉHICULE:")
    vehicle_stats = {}
    for transport in transports:
        key = (transport.vehicle_type, transport.vehicle_idx)
        if key not in vehicle_stats:
            vehicle_stats[key] = {
                'transports': 0,
                'weight': 0,
                'volume': 0,
                'time': 0,
                'vehicle': None
            }
        
        vehicle_stats[key]['transports'] += 1
        vehicle_stats[key]['weight'] += transport.weight_transported
        vehicle_stats[key]['volume'] += transport.volume_transported
        vehicle_stats[key]['time'] += transport.T_total
        
        # Trouver l'objet véhicule pour les infos
        for vehicles in [transports]:  # Récupérer de la solution si possible
            vehicle_stats[key]['vehicle'] = transport
            break
    
    for (vtype, vidx), stats in vehicle_stats.items():
        print(f"   • Véhicule {vidx} (Type {vtype}):")
        print(f"     - Transports: {stats['transports']}")
        print(f"     - Poids transporté: {stats['weight']:.2f} kg")
        print(f"     - Volume transporté: {stats['volume']:.2f} m³")
        print(f"     - Temps total: {stats['time']:.2f}h ({format_time_detailed(stats['time'])})")
    
    # Analyse temporelle
    print(f"\n⏱️  ANALYSE TEMPORELLE DÉTAILLÉE:")
    total_driving = sum(t.T_conduite for t in transports)
    total_breaks = sum(t.T_pauses for t in transports)
    total_nights = sum(t.T_nuit for t in transports)
    total_pauses_count = sum(t.N_pauses for t in transports)
    total_nights_count = sum(t.N_nuits for t in transports)
    
    print(f"   • Temps conduite total: {total_driving:.2f}h ({format_time_detailed(total_driving)})")
    print(f"   • Temps pauses total: {total_breaks:.2f}h ({format_time_detailed(total_breaks)})")
    print(f"   • Temps nuits total: {total_nights:.2f}h ({format_time_detailed(total_nights)})")
    print(f"   • Nombre total pauses: {total_pauses_count}")
    print(f"   • Nombre total nuits: {total_nights_count}")
    
    # Efficacité
    print(f"\n📈 INDICATEURS D'EFFICACITÉ:")
    if len(vehicles_used) > 0:
        avg_weight_per_vehicle = total_weight / len(vehicles_used)
        avg_volume_per_vehicle = total_volume / len(vehicles_used)
        avg_time_per_transport = total_time / len(transports)
        
        print(f"   • Poids moyen par véhicule: {avg_weight_per_vehicle:.2f} kg")
        print(f"   • Volume moyen par véhicule: {avg_volume_per_vehicle:.2f} m³")
        print(f"   • Temps moyen par transport: {avg_time_per_transport:.2f}h ({format_time_detailed(avg_time_per_transport)})")

def run_complete_mc_svrp_algorithm(id_client, cible_longitude, cible_latitude):
    """FONCTION PRINCIPALE - Remplace votre métaheuristique actuelle"""
    
    try:
        print("="*90)
        print("🧠 ALGORITHME MC-SVRP-TC COMPLET")
        print("Multi-Commodity Shuttle VRP with Time Constraints")
        print("="*90)
        
        # Créer instance avec VOS données
        instance = Instance(id_client, cible_longitude, cible_latitude)
        
        print(f"📋 PARAMÈTRES:")
        print(f"- Client: {id_client}")
        print(f"- Distance A-B: {instance.d_AB} km")
        print(f"- Types véhicules: {len(instance.L)}")
        print(f"- Véhicules total: {sum(instance.m.values())}")
        
        total_weight = sum(instance.dw_AB.values())
        total_volume = sum(instance.dv_AB.values())
        print(f"- Demande totale: {total_weight:.1f}kg, {total_volume:.1f}m³")
        
        if total_weight == 0 and total_volume == 0:
            print("❌ Aucune demande trouvée")
            return None
        
        # Exécution algorithme
        start_time = time.time()
        solution = mc_complete_greedy_algorithm(instance)
        print(f"\n🔍 VÉRIFICATION DÉTAILLÉE:")
        all_satisfied = True
        for week in instance.T:
            if instance.dw_AB[week] > 0 or instance.dv_AB[week] > 0:
                remaining_w = solution.product_mixing.product_pool[week]['weight_remaining']
                remaining_v = solution.product_mixing.product_pool[week]['volume_remaining']
                
                initial_w = solution.product_mixing.product_pool[week]['weight_initial']
                initial_v = solution.product_mixing.product_pool[week]['volume_initial']
                
                weight_ok = remaining_w <= 0.1
                volume_ok = remaining_v <= 0.1
                
                print(f"Sem.{week}: "
                      f"Poids {initial_w:.1f}→{remaining_w:.1f}kg {'✅' if weight_ok else '❌'}, "
                      f"Volume {initial_v:.1f}→{remaining_v:.1f}m³ {'✅' if volume_ok else '❌'}")
                
                if not (weight_ok and volume_ok):
                    all_satisfied = False
        
        if all_satisfied:
            print("🎉 TOUTES LES DEMANDES SATISFAITES!")
        else:
            print("⚠️ Certaines demandes non satisfaites")

        end_time = time.time()
        
        print(f"\n{'='*60}")
        print("🎯 RÉSULTATS FINAUX")
        print(f"{'='*60}")
        print(f"⏱️  Temps: {end_time - start_time:.2f}s")
        print(f"💰 Coût: {solution.total_cost:.2f}")
        print(f"🚛 Véhicules: {sum(1 for v in solution.vehicles.values() if v.is_used())}")
        print(f"📦 Transports: {len(solution.transports)}")
        print(f"✅ Faisable: {'OUI' if solution.feasible else 'NON'}")
        
        # Vérification pools
        print(f"\n🔍 VÉRIFICATION DEMANDES:")
        all_satisfied = True
        for week in instance.T:
            remaining_w = solution.product_mixing.product_pool[week]['weight_remaining']
            remaining_v = solution.product_mixing.product_pool[week]['volume_remaining']
            
            if remaining_w > 0.1 or remaining_v > 0.1:
                print(f"⚠️  Semaine {week}: {remaining_w:.1f}kg, {remaining_v:.1f}m³ restants")
                all_satisfied = False
            else:
                print(f"✅ Semaine {week}: Satisfaite")
        
        if all_satisfied:
            print("🎉 TOUTES LES DEMANDES SATISFAITES!")
        
        return solution
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None

# ========================================
# FONCTIONS D'EXPORT COMPATIBLES
# ========================================

def save_mc_solution(solution, instance, filename="mc_svrp_solution.json"):
    """Sauvegarde compatible avec votre interface"""
    try:
        solution_data = {
            "metadata": {
                "client_id": instance.id_client,
                "distance_AB": instance.d_AB,
                "total_cost": solution.total_cost,
                "feasible": solution.feasible,
                "vehicles_used": sum(1 for v in solution.vehicles.values() if v.is_used()),
                "total_transports": len(solution.transports),
                "algorithm": "MC-SVRP-TC Complete"
            },
            "vehicles": [],
            "transports": [],
            "weekly_summary": {}
        }
        
        # Véhicules utilisés
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
        
        # Transports
        for transport in solution.transports:
            transport_data = {
                "week": transport.week,
                "vehicle_type": transport.vehicle_type,
                "vehicle_index": transport.vehicle_idx,
                "trip_sequence": transport.trip_sequence,
                "weight_transported": transport.weight_transported,
                "volume_transported": transport.volume_transported,
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
                total_weight = sum(t.weight_transported for t in week_transports)
                total_volume = sum(t.volume_transported for t in week_transports)
                
                solution_data["weekly_summary"][str(week)] = {
                    "transports": len(week_transports),
                    "vehicles": len(vehicles_used),
                    "total_weight": total_weight,
                    "total_volume": total_volume,
                    "demand_weight": instance.dw_AB[week],
                    "demand_volume": instance.dv_AB[week],
                    "weight_remaining": solution.product_mixing.product_pool[week]['weight_remaining'],
                    "volume_remaining": solution.product_mixing.product_pool[week]['volume_remaining']
                }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(solution_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Solution sauvegardée: {filename}")
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")

def export_to_excel_mc(solution, instance, filename="mc_svrp_planning.xlsx"):
    """Export Excel compatible avec votre interface"""
    try:
        import pandas as pd
        
        # Données véhicules
        vehicles_data = []
        for (vtype, idx), vehicle in solution.vehicles.items():
            if vehicle.is_used():
                vehicles_data.append({
                    'Type_ID': vtype,
                    'Vehicle_Index': idx,
                    'Immatriculation': vehicle.plate or f'V{idx}',
                    'Type_Name': vehicle.type_name or f'Type {vtype}',
                    'Weight_Capacity_kg': vehicle.weight_capacity,
                    'Volume_Capacity_m3': vehicle.volume_capacity,
                    'Weeks_Used': len(vehicle.weeks_used),
                    'Total_Trips': vehicle.num_trips,
                    'Duration_Days': vehicle.duration,
                    'Units_Used': vehicle.num_units_used
                })
        
        # Données transports
        transports_data = []
        for transport in solution.transports:
            vehicle = solution.vehicles[(transport.vehicle_type, transport.vehicle_idx)]
            transports_data.append({
                'Week': transport.week,
                'Vehicle_Type': transport.vehicle_type,
                'Vehicle_Index': transport.vehicle_idx,
                'Immatriculation': vehicle.plate or f'V{transport.vehicle_idx}',
                'Trip_Sequence': transport.trip_sequence,
                'Weight_Transported_kg': transport.weight_transported,
                'Volume_Transported_m3': transport.volume_transported,
                'Driving_Time_h': transport.T_conduite,
                'Break_Time_h': transport.T_pauses,
                'Night_Time_h': transport.T_nuit,
                'Total_Time_h': transport.T_total,
                'Number_Breaks': transport.N_pauses,
                'Number_Nights': transport.N_nuits
            })
        
        # Résumé hebdomadaire
        weekly_data = []
        for week in instance.T:
            week_transports = [t for t in solution.transports if t.week == week]
            vehicles_used = set((t.vehicle_type, t.vehicle_idx) for t in week_transports)
            
            total_weight = sum(t.weight_transported for t in week_transports)
            total_volume = sum(t.volume_transported for t in week_transports)
            
            weekly_data.append({
                'Week': week,
                'Transports_Count': len(week_transports),
                'Vehicles_Count': len(vehicles_used),
                'Weight_Transported_kg': total_weight,
                'Volume_Transported_m3': total_volume,
                'Weight_Demand_kg': instance.dw_AB[week],
                'Volume_Demand_m3': instance.dv_AB[week],
                'Weight_Satisfaction': total_weight >= instance.dw_AB[week],
                'Volume_Satisfaction': total_volume >= instance.dv_AB[week],
                'Weight_Remaining_kg': solution.product_mixing.product_pool[week]['weight_remaining'],
                'Volume_Remaining_m3': solution.product_mixing.product_pool[week]['volume_remaining']
            })
        
        # Création fichier Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            pd.DataFrame(vehicles_data).to_excel(writer, sheet_name='Vehicles', index=False)
            pd.DataFrame(transports_data).to_excel(writer, sheet_name='Transports', index=False)
            pd.DataFrame(weekly_data).to_excel(writer, sheet_name='Weekly_Summary', index=False)
            
            # Feuille récapitulatif
            summary_data = [{
                'Metric': 'Total_Cost',
                'Value': solution.total_cost
            }, {
                'Metric': 'Vehicles_Used',
                'Value': sum(1 for v in solution.vehicles.values() if v.is_used())
            }, {
                'Metric': 'Total_Transports',
                'Value': len(solution.transports)
            }, {
                'Metric': 'Feasible_Solution',
                'Value': 'Yes' if solution.feasible else 'No'
            }, {
                'Metric': 'Distance_AB_km',
                'Value': instance.d_AB
            }, {
                'Metric': 'Client_ID',
                'Value': instance.id_client
            }, {
                'Metric': 'Algorithm',
                'Value': 'MC-SVRP-TC Complete'
            }]
            
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"📊 Export Excel: {filename}")
        
    except ImportError:
        print("⚠️  Pandas non disponible pour export Excel")
    except Exception as e:
        print(f"❌ Erreur export Excel: {e}")

# ========================================
# FONCTIONS POUR INTERFACE GRAPHIQUE
# ========================================

def print_detailed_solution_mc(solution, instance):
    """Affichage détaillé compatible avec votre interface"""
    
    print(f"\n📊 ANALYSE DÉTAILLÉE MC-SVRP-TC")
    print("-" * 50)
    
    # Statistiques générales
    vehicles_used = sum(1 for v in solution.vehicles.values() if v.is_used())
    print(f"Véhicules utilisés: {vehicles_used}")
    print(f"Coût total (Équation 39): {solution.total_cost:.2f}")
    print(f"Nombre de transports: {len(solution.transports)}")
    print(f"Solution faisable: {'✅ OUI' if solution.feasible else '❌ NON'}")
    
    # Répartition par type
    print(f"\n🚛 FLOTTE UTILISÉE:")
    print("-" * 30)
    vehicles_by_type = {}
    for (vtype, idx), vehicle in solution.vehicles.items():
        if vehicle.is_used():
            type_name = vehicle.type_name or f"Type {vtype}"
            if type_name not in vehicles_by_type:
                vehicles_by_type[type_name] = []
            vehicles_by_type[type_name].append(vehicle)
    
    for type_name, vehicles in vehicles_by_type.items():
        print(f"{type_name}: {len(vehicles)} véhicule(s)")
        for vehicle in vehicles[:3]:  # Limiter l'affichage
            plate = vehicle.plate or f"V{vehicle.idx}"
            print(f"  - {plate}: {len(vehicle.weeks_used)} semaines, "
                  f"{vehicle.num_trips} voyages, {vehicle.duration:.1f}j")
        if len(vehicles) > 3:
            print(f"  ... et {len(vehicles) - 3} autres")
    
    # Planning condensé
    print(f"\n📅 PLANNING CONDENSÉ:")
    print("-" * 30)
    for week in sorted(instance.T):
        week_transports = [t for t in solution.transports if t.week == week]
        if week_transports:
            total_weight = sum(t.weight_transported for t in week_transports)
            total_volume = sum(t.volume_transported for t in week_transports)
            vehicles_count = len(set((t.vehicle_type, t.vehicle_idx) for t in week_transports))
            
            print(f"Semaine {week}: {len(week_transports)} transports, "
                  f"{vehicles_count} véhicules, "
                  f"{total_weight:.0f}kg/{total_volume:.0f}m³")
    
    # Vérification demandes
    print(f"\n✅ SATISFACTION DEMANDES:")
    print("-" * 30)
    for week in instance.T:
        if instance.dw_AB[week] > 0 or instance.dv_AB[week] > 0:
            remaining_w = solution.product_mixing.product_pool[week]['weight_remaining']
            remaining_v = solution.product_mixing.product_pool[week]['volume_remaining']
            
            weight_status = "✅" if remaining_w <= 0.1 else "❌"
            volume_status = "✅" if remaining_v <= 0.1 else "❌"
            
            print(f"Semaine {week}: Poids {weight_status} Volume {volume_status}")

# ========================================
# INSTRUCTIONS DE REMPLACEMENT
# ========================================

"""
🔄 INSTRUCTIONS DE REMPLACEMENT COMPLET:

1. SAUVEGARDE:
   mv application/models/metaheuristique.py application/models/metaheuristique_backup.py

2. NOUVEAU FICHIER:
   Créez application/models/mc_svrp_complete.py avec ce code

3. COPIEZ VOTRE CLASSE INSTANCE:
   Dans mc_svrp_complete.py, remplacez la classe Instance vide par 
   EXACTEMENT votre classe Instance existante (avec toutes ses méthodes)

4. MODIFIEZ VOTRE INTERFACE:
   Remplacez dans votre interface:
   
   ANCIEN:
   from application.models.metaheuristique import Instance, greedy_initial_solution
   solution = greedy_initial_solution(instance)
   
   NOUVEAU:
   from application.models.mc_svrp_complete import run_complete_mc_svrp_algorithm
   solution = run_complete_mc_svrp_algorithm(id_client, longitude, latitude)

5. FONCTIONS COMPATIBLES:
   - save_mc_solution() remplace save_solution()
   - export_to_excel_mc() remplace export_to_excel()
   - print_detailed_solution_mc() pour affichage détaillé

6. TESTEZ:
   Votre interface existante fonctionnera avec les mêmes données
   mais avec l'algorithme MC-SVRP-TC complet !

✅ AVANTAGES DU REMPLACEMENT:
- Contraintes temporelles exactes (Équations 49-58)
- Stratégie de mélange intelligente (Équations 64-87)
- Fonction objectif mathématique exacte (Équation 39)
- Toutes les contraintes du modèle respectées
- Compatible avec vos données existantes
- Interface graphique inchangée
"""