import pandas as pd
import json
from datetime import datetime, timedelta
import os
import random
import pandas as pd
import math
import time  
import datetime
import copy
from datetime import datetime, timedelta   


class Instance:
    def __init__(self, id_client=None, cible_longitude=None, cible_latitude=None):
        """
        Initialisation d'une instance du problème de transport par navettes entre les sites A et B
        sur un horizon de 12 semaines, avec transport uniquement dans le sens A vers B.
        """
        # Horizon de planification: 12 semaines
        self.T = list(range(1, 13))
        self.np = 12
        
        # Stocker les paramètres de localisation
        self.id_client = id_client
        self.cible_longitude = cible_longitude
        self.cible_latitude = cible_latitude
        
        # Vérifier que les paramètres obligatoires sont fournis
        if not all([id_client, cible_longitude, cible_latitude]):
            raise ValueError("Tous les paramètres (id_client, cible_longitude, cible_latitude) sont obligatoires")
        
        # Récupérer les coordonnées du client et calculer la distance
        self.load_client_coordinates()
        self.calculate_distance()
        
        # Récupérer les données des véhicules depuis la base de données
        self.load_vehicles_from_database()
        
        # Coût de déplacement entre les sites (peut être ajusté selon la distance réelle)
        self.dc = max(50, self.d_AB * 0.1)  # Coût basé sur la distance
        
        # Charger les demandes depuis la base de données
        self.load_demands_from_database()
        
        # Paramètres liés aux contraintes temporelles
        self.T_start = 7      # Heure de début de la journée de travail (en heures depuis minuit)
        self.T_end = 18       # Heure de fin de la journée de travail (en heures depuis minuit)
        self.T_drive = 2      # Durée maximale de conduite continue (en heures)
        self.T_break = 0.25   # Durée d'une pause obligatoire (en heures, soit 15 minutes)
        
        # Temps de chargement et déchargement (en heures)
        self.T_load_A = 0.5    # Temps de chargement au site A
        self.T_unload_B = 0.5  # Temps de déchargement au site B
        
        # Valider l'instance créée
        self.validate_instance()
    
    def load_client_coordinates(self):
        """
        Récupère les coordonnées GPS du client/chantier (site A) depuis la base de données
        """
        try:
            from application.models.chantiers import Chantier
            from application.database import SessionLocal
        except ImportError:
            raise ImportError("Impossible d'importer les modèles de base de données. Vérifiez votre configuration.")
        
        # Créer une session SQLAlchemy
        session = SessionLocal()
        
        try:
            # Récupérer les informations du chantier
            chantier = session.query(Chantier).filter_by(id_client=self.id_client).first()
            
            if not chantier:
                raise ValueError(f"Aucun chantier trouvé avec l'ID client {self.id_client}")
            
            # Vérifier que les coordonnées sont valides
            if chantier.latitude is None or chantier.longitude is None:
                raise ValueError(f"Coordonnées GPS manquantes pour le chantier {self.id_client}")
            
            # Stocker les coordonnées du client (site A)
            self.client_latitude = float(chantier.latitude)
            self.client_longitude = float(chantier.longitude)
            
            # Stocker également d'autres informations utiles
            self.client_localisation = chantier.localisation or f"Chantier {self.id_client}"
            self.distance_aller_goudron = chantier.distanceAllerGoudron or 0
            self.distance_aller_piste = chantier.distanceAllerPiste or 0
            self.temps_aller = chantier.temps_aller or 0
            self.nature_terrain = getattr(chantier, 'nature_terrain', 'Normal')
            
            print(f"✅ Chargement du chantier: {self.client_localisation}")
            print(f"   Coordonnées: {self.client_latitude:.4f}, {self.client_longitude:.4f}")
            print(f"   Nature du terrain: {self.nature_terrain}")
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement des coordonnées client: {e}")
        finally:
            session.close()
    
    def calculate_distance(self):
        """
        Calcule la distance entre le site A (client) et le site B (cible) en utilisant la formule haversine
        """
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
        
        print(f"✅ Distance calculée: {self.d_AB} km")
        print(f"   Entre {self.client_localisation} et le site cible")
    
    def load_vehicles_from_database(self):
        """
        Récupère les informations des véhicules depuis la base de données
        et les organise dans les structures de données requises.
        Filtre les véhicules en fonction de la nature du terrain du chantier.
        """
        try:
            from application.models.vehicule import Vehicule
            from application.database import SessionLocal
        except ImportError:
            raise ImportError("Impossible d'importer les modèles de véhicules. Vérifiez votre configuration.")
        
        # Créer une session SQLAlchemy
        session = SessionLocal()
        
        try:
            # Construire la requête de base pour les véhicules disponibles
            query = session.query(Vehicule).filter(Vehicule.etat == "Disponible")
            
            # Filtrer les véhicules selon la nature du terrain
            if hasattr(self, 'nature_terrain') and self.nature_terrain == "Accès difficile":
                # Pour un accès difficile, on ne garde que les 4x4 ou 6x6
                query = query.filter(
                    (Vehicule.type_vehicule.like("%4x4%")) | 
                    (Vehicule.type_vehicule.like("%4*4%")) |
                    (Vehicule.type_vehicule.like("%6x6%")) |
                    (Vehicule.type_vehicule.like("%6*6%"))
                )
                print(f"🔍 Filtrage pour terrain difficile: véhicules 4x4/6x6 uniquement")
            else:
                print(f"🔍 Terrain normal: tous les véhicules disponibles")
            
            # Récupérer les véhicules filtrés
            vehicles = query.all()
            
            if not vehicles:
                raise ValueError("Aucun véhicule disponible avec les critères spécifiés")
            
            print(f"✅ Véhicules disponibles: {len(vehicles)}")
            
            # Grouper les véhicules par type
            vehicles_by_type = {}
            for vehicle in vehicles:
                vehicle_type = vehicle.type_vehicule
                if vehicle_type not in vehicles_by_type:
                    vehicles_by_type[vehicle_type] = []
                vehicles_by_type[vehicle_type].append(vehicle)
            
            # Transformer les données en structures attendues
            self.L = {}  # Types de véhicules disponibles avec leurs capacités
            self.m = {}  # Nombre maximal de véhicules disponibles par type
            self.c = {}  # Coût variable par kilomètre selon le type
            self.V = {}  # Vitesse moyenne des véhicules (km/h)
            
            # Attribuer un ID numérique à chaque type de véhicule
            for i, (vehicle_type, vehicle_list) in enumerate(vehicles_by_type.items(), 1):
                # Utiliser le premier véhicule de chaque type comme référence
                reference_vehicle = vehicle_list[0]
                
                # Gérer les cas où les champs sont `None`
                capacite_tonne = reference_vehicle.capacite_tonne or 0
                capacite_volume = reference_vehicle.capacite_volume or 0
                
                # Validation des capacités
                if capacite_tonne <= 0 and capacite_volume <= 0:
                    print(f"⚠️ Véhicule {vehicle_type} ignoré: capacités nulles")
                    continue
                
                # Capacités (poids en kg et volume en m³)
                self.L[i] = {
                    "Qw": capacite_tonne * 1000,  # Convertir tonnes en kg
                    "Qv": capacite_volume
                }
                
                # Nombre de véhicules disponibles pour ce type
                self.m[i] = len(vehicle_list)
                
                # COÛT VARIABLE PAR KILOMÈTRE SELON LE TYPE DE VÉHICULE
                cout_variable_km = 280.0  # Valeur par défaut pour 4*2
                
                vehicle_type_lower = vehicle_type.lower()
                if "4x4" in vehicle_type_lower or "4*4" in vehicle_type_lower:
                    cout_variable_km = 260.0
                elif "6x6" in vehicle_type_lower or "6*6" in vehicle_type_lower:
                    cout_variable_km = 400.0
                elif "4x2" in vehicle_type_lower or "4*2" in vehicle_type_lower:
                    cout_variable_km = 280.0
                elif "6x4" in vehicle_type_lower or "6*4" in vehicle_type_lower:
                    cout_variable_km = 260.0
                
                # Stocker le coût variable par km (UNIQUEMENT COÛT VARIABLE)
                self.c[i] = cout_variable_km
                
                # Vitesse moyenne adaptée au terrain
                vitesse_base = max(60, 90 - capacite_tonne * 2)  # Plus lourd = plus lent
                if hasattr(self, 'nature_terrain') and self.nature_terrain == "Accès difficile":
                    self.V[i] = int(vitesse_base * 0.7)  # Réduction de 30% pour terrain difficile
                else:
                    self.V[i] = int(vitesse_base)
                
                # Stocker les correspondances pour référence
                if not hasattr(self, 'type_mapping'):
                    self.type_mapping = {}
                self.type_mapping[i] = vehicle_type
                
                # Stocker les immatriculations
                if not hasattr(self, 'vehicle_plates'):
                    self.vehicle_plates = {}
                self.vehicle_plates[i] = [v.immatriculation for v in vehicle_list]
                
                print(f"   Type {i}: {vehicle_type}")
                print(f"     Capacités: {capacite_tonne}t, {capacite_volume}m³")
                print(f"     Véhicules: {len(vehicle_list)}")
                print(f"     Vitesse: {self.V[i]} km/h")
                print(f"     Coût variable/km: {self.c[i]:.2f} DA")
        
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement des véhicules: {e}")
        finally:
            session.close()
        
        # Vérifier qu'au moins un type de véhicule est disponible
        if not hasattr(self, 'L') or not self.L:
            raise ValueError("Aucun véhicule utilisable trouvé. Vérifiez la disponibilité et les capacités.")
    def load_demands_from_database(self):
        """
        Récupère les demandes d'équipements depuis la classe TransfererEquipement
        et calcule le poids et le volume correspondants à partir de la classe Equipement.
        """
        try:
            from application.models.transferer_equipement import TransfererEquipement
            from application.models.equipements import Equipement
            from application.database import SessionLocal
        except ImportError:
            raise ImportError("Impossible d'importer les modèles de transfert. Vérifiez votre configuration.")
        
        # Initialiser les dictionnaires pour stocker les demandes
        self.dw_AB = {t: 0 for t in self.T}  # Demandes en poids de A vers B (kg)
        self.dv_AB = {t: 0 for t in self.T}  # Demandes en volume de A vers B (m³)
        
        print(f"🔍 Récupération des demandes pour le client {self.id_client}")
        
        # Créer une session SQLAlchemy
        session = SessionLocal()
        
        try:
            # Récupérer les transferts d'équipements pour ce client
            query = session.query(TransfererEquipement)
            if self.id_client:
                query = query.filter_by(id_client=self.id_client)
            
            transfers = query.all()
            
            if not transfers:
                print(f"⚠️ Aucune demande de transfert trouvée pour le client {self.id_client}")
                # Créer des demandes minimales pour éviter les erreurs
                self.dw_AB[1] = 100  # 100 kg minimum en semaine 1
                self.dv_AB[1] = 1    # 1 m³ minimum en semaine 1
                return
            
            print(f"✅ {len(transfers)} demandes de transfert trouvées")
            
            # Mappings des colonnes de semaines (inversé car les colonnes sont "avant")
            semaines_mapping = {
                12: 'douze_semaines_avant',
                11: 'onze_semaines_avant', 
                10: 'dix_semaines_avant',
                9: 'neuf_semaines_avant',
                8: 'huit_semaines_avant',
                7: 'sept_semaines_avant',
                6: 'six_semaines_avant',
                5: 'cinq_semaines_avant',
                4: 'quatre_semaines_avant',
                3: 'trois_semaines_avant',
                2: 'deux_semaines_avant',
                1: 'un_semaines_avant',
                0: 'zero_semaines_avant'
            }
            
            # Traiter chaque demande de transfert
            for transfer in transfers:
                print(f"\n   🔍 ANALYSE TRANSFERT:")
                print(f"      ID transfert: {transfer.id}")
                print(f"      ID équipement: {transfer.id_equipement}")
                print(f"      Nom équipement: {getattr(transfer, 'nom_equipement', 'N/A')}")
                
                # Récupérer l'équipement correspondant
                equipement = session.query(Equipement).filter_by(
                    ID_equipement=transfer.id_equipement
                ).first()
                
                if not equipement:
                    print(f"      ❌ Équipement {transfer.id_equipement} non trouvé dans la base")
                    continue
                
                print(f"      ✅ Équipement trouvé:")
                print(f"         - ID: {equipement.ID_equipement}")
                print(f"         - Nom: {equipement.nomEquipement}")
                print(f"         - Type: {equipement.typeEquipement}")
                print(f"         - État: {equipement.etat}")
                print(f"         - Quantité en stock: {equipement.quantite}")
                print(f"         - Poids (kg): {equipement.poids}")
                print(f"         - Volume (m³): {equipement.volume}")
                
                # Récupérer les caractéristiques physiques de l'équipement
                poids_unitaire = equipement.poids or 0  # en kg
                volume_unitaire = equipement.volume or 0  # en m³
                
                print(f"      📊 Caractéristiques utilisées:")
                print(f"         - Poids unitaire: {poids_unitaire} kg")
                print(f"         - Volume unitaire: {volume_unitaire} m³")
                
                if poids_unitaire <= 0 and volume_unitaire <= 0:
                    print(f"      ❌ Équipement ignoré: aucune donnée physique valide")
                    continue  # Ignorer cet équipement car pas de données physiques
                
                print(f"      ✅ Équipement retenu pour l'optimisation")
                
                # Analyser les demandes par semaine
                print(f"      📅 DEMANDES PAR SEMAINE:")
                demandes_trouvees = False
                
                # Pour chaque semaine dans notre horizon (1 à 12)
                for semaine in self.T:
                    # Calculer la semaine correspondante dans la DB (inversée)
                    db_semaine = 13 - semaine
                    
                    # Récupérer la quantité pour cette semaine
                    if db_semaine in semaines_mapping:
                        column_name = semaines_mapping[db_semaine]
                        quantite = getattr(transfer, column_name, 0) or 0
                        
                        if quantite > 0:
                            # Calculer poids et volume total pour cette quantité
                            poids_total = poids_unitaire * quantite
                            volume_total = volume_unitaire * quantite
                            
                            # Ajouter aux demandes totales
                            self.dw_AB[semaine] += poids_total
                            self.dv_AB[semaine] += volume_total
                            demandes_trouvees = True
                            
                            print(f"         S{semaine:2d}: {quantite:3d} unités → {poids_total:8.1f} kg, {volume_total:6.2f} m³")
                
                if not demandes_trouvees:
                    print(f"      ⚠️ Aucune demande trouvée pour cet équipement sur les 12 semaines")
            
            # Vérifier que des demandes ont été trouvées
            total_poids = sum(self.dw_AB.values())
            total_volume = sum(self.dv_AB.values())
            
            if total_poids == 0 and total_volume == 0:
                raise ValueError("Aucune demande valide trouvée. Vérifiez les données d'équipements.")
            
            print(f"✅ Demandes totales chargées:")
            print(f"   Poids total: {total_poids:.1f} kg sur 12 semaines")
            print(f"   Volume total: {total_volume:.1f} m³ sur 12 semaines")
            
        except Exception as e:
            raise RuntimeError(f"Erreur lors du chargement des demandes: {e}")
        finally:
            session.close()
    
    def validate_instance(self):
        """Valide que l'instance est correctement configurée"""
        errors = []
        
        # Vérifier les paramètres de base
        if not hasattr(self, 'd_AB') or self.d_AB <= 0:
            errors.append("Distance A-B non calculée ou invalide")
        
        # Vérifier les véhicules
        if not hasattr(self, 'L') or not self.L:
            errors.append("Aucun véhicule disponible")
        
        # Vérifier les demandes
        if not hasattr(self, 'dw_AB') or not hasattr(self, 'dv_AB'):
            errors.append("Demandes non chargées")
        elif sum(self.dw_AB.values()) == 0 and sum(self.dv_AB.values()) == 0:
            errors.append("Toutes les demandes sont nulles")
        
        if errors:
            raise ValueError(f"Instance invalide: {'; '.join(errors)}")
        
        print(f"✅ Instance validée avec succès")
        print(f"   Distance: {self.d_AB} km")
        print(f"   Types de véhicules: {len(self.L)}")
        print(f"   Semaines avec demandes: {sum(1 for t in self.T if self.dw_AB[t] > 0 or self.dv_AB[t] > 0)}")
    
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
    
    def afficher_resume(self):
        """Affiche un résumé de l'instance créée"""
        print(f"\n📋 RÉSUMÉ DE L'INSTANCE")
        print(f"="*50)
        print(f"Client: {self.id_client}")
        print(f"Localisation: {getattr(self, 'client_localisation', 'Non définie')}")
        print(f"Distance A→B: {self.d_AB} km")
        print(f"Nature du terrain: {getattr(self, 'nature_terrain', 'Normal')}")
        
        print(f"\n🚛 VÉHICULES DISPONIBLES ({len(self.L)} types):")
        for vtype, capacites in self.L.items():
            nom = self.get_vehicle_type_name(vtype)
            print(f"  {vtype}. {nom}")
            print(f"     Capacité: {capacites['Qw']/1000:.1f}t, {capacites['Qv']:.1f}m³")
            print(f"     Quantité: {self.m[vtype]} véhicule(s)")
            print(f"     Vitesse: {self.V[vtype]} km/h")
            print(f"     Coût: {self.c[vtype]}DA")
        
        print(f"\n📦 DEMANDES PAR SEMAINE:")
        total_poids = 0
        total_volume = 0
        semaines_actives = 0
        
        for t in self.T:
            if self.dw_AB[t] > 0 or self.dv_AB[t] > 0:
                print(f"  Semaine {t:2d}: {self.dw_AB[t]:6.1f} kg, {self.dv_AB[t]:5.1f} m³")
                total_poids += self.dw_AB[t]
                total_volume += self.dv_AB[t]
                semaines_actives += 1
        
        print(f"\n📊 STATISTIQUES:")
        print(f"  Total sur 12 semaines: {total_poids:.1f} kg, {total_volume:.1f} m³")
        print(f"  Semaines actives: {semaines_actives}/12")
        print(f"  Moyenne par semaine active: {total_poids/max(semaines_actives,1):.1f} kg, {total_volume/max(semaines_actives,1):.1f} m³")
        
        # Estimation du défi logistique
        if total_poids > 50000 or total_volume > 500:
            print(f"  🔴 Défi logistique: ÉLEVÉ")
        elif total_poids > 20000 or total_volume > 200:
            print(f"  🟡 Défi logistique: MOYEN")
        else:
            print(f"  🟢 Défi logistique: FAIBLE")
        
        print(f"="*50)




# Fonction utilitaire pour créer une instance
def creer_instance_optimisation(id_client, cible_longitude, cible_latitude):
    """
    Fonction utilitaire pour créer une instance d'optimisation
    
    Args:
        id_client: ID du client dans la base de données
        cible_longitude: Longitude du site de destination
        cible_latitude: Latitude du site de destination
    
    Returns:
        Instance: Instance configurée et validée
    """
    try:
        print(f"🔧 Création de l'instance d'optimisation...")
        print(f"   Client: {id_client}")
        print(f"   Destination: {cible_latitude:.4f}, {cible_longitude:.4f}")
        
        instance = Instance(
            id_client=id_client,
            cible_longitude=cible_longitude,
            cible_latitude=cible_latitude
        )
        
        instance.afficher_resume()
        return instance
        
    except Exception as e:
        print(f"❌ Erreur lors de la création de l'instance: {e}")
        raise

class OptimisateurNavettesAmeliore:
    """
    Optimisateur de navettes - Version améliorée fidèle à la modélisation mathématique
    Intègre la gestion individuelle des véhicules, contraintes temporelles sophistiquées,
    et stratégie de mélange intelligente des produits
    """
    
    def __init__(self):
        # Paramètres temporels et logistiques (selon modélisation)
        self.T_load = 1.5      # Temps de chargement (heures)
        self.T_unload = 1.5    # Temps de déchargement (heures)  
        self.T_work = 8.0      # Temps de travail effectif par jour (heures)
        self.T_break = 0.25    # Durée d'une pause obligatoire (heures)
        self.T_night = 13.0    # Durée d'un arrêt nocturne (heures)
        self.V_m = 75          # Vitesse moyenne par défaut (km/h)
        
    def calculer_navettes_optimales(self, produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours=7):
        """
        Calcule les navettes optimales avec modélisation mathématique complète
        """
        print(f"\n=== OPTIMISATION AVEC MODÉLISATION MATHÉMATIQUE COMPLÈTE ===")
        print(f"⏰ CONTRAINTE TEMPORELLE: {duree_max_jours} jours maximum")
        
        # Calculer distance (supposée identique pour tous les produits)
        distance_km = produits_a_transporter[0].get('distance_km', 800)
        
        # Préparer les données selon la modélisation
        produits_modelisation = self._preparer_produits_modelisation(produits_a_transporter)
        vehicules_modelisation = self._preparer_vehicules_modelisation(vehicules_data, distance_km)
        
        print(f"📦 PRODUITS À TRANSPORTER: {len(produits_modelisation)}")
        for p_id, produit in produits_modelisation.items():
            print(f"   P{p_id}: {produit['q_p']} unités, {produit['w_p']:.2f}kg/unité, {produit['v_p']:.2f}m³/unité")
            print(f"        Total: {produit['W_p']:.2f}kg, {produit['V_p']:.2f}m³")
        
        print(f"🚛 VÉHICULES DISPONIBLES: {len(vehicules_modelisation)} types")
        for l_type, vehicules in vehicules_modelisation.items():
            print(f"   Type {l_type}: {len(vehicules['vehicules_individuels'])} véhicules")
            for k_id, vehicule in vehicules['vehicules_individuels'].items():
                print(f"      V{k_id}: {vehicule['C_w']:.0f}kg, {vehicule['C_v']:.1f}m³, {vehicule['vitesse']}km/h")
        
        try:
            # Recherche de solution optimale
            solution_optimale = self._chercher_solution_optimale_complete(
                produits_modelisation,
                vehicules_modelisation,
                distance_km,
                duree_max_jours
            )
            
            if not solution_optimale:
                print(f"\n❌ AUCUNE SOLUTION TROUVÉE")
                return None
            
            # Conversion vers format de retour
            return self._convertir_solution_vers_format_retour(
                solution_optimale, produits_a_transporter, date_debut, heure_debut, duree_max_jours
            )
            
        except Exception as e:
            print(f"❌ ERREUR dans calculer_navettes_optimales: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _preparer_produits_modelisation(self, produits_a_transporter):
        """
        Prépare les produits selon la notation de la modélisation mathématique
        """
        produits_modelisation = {}
        
        for p_id, produit in enumerate(produits_a_transporter, 1):
            quantite = produit.get('quantite', 1)
            poids_unitaire = produit.get('poids_unitaire', 0) * 1000  # Convertir tonnes en kg
            volume_unitaire = produit.get('volume_unitaire', 0)
            
            produits_modelisation[p_id] = {
                'nom': produit.get('nom', f'Produit_{p_id}'),
                'q_p': quantite,                           # quantité totale
                'w_p': poids_unitaire,                     # poids unitaire (kg)
                'v_p': volume_unitaire,                    # volume unitaire (m³)
                'W_p': quantite * poids_unitaire,          # poids total (kg)
                'V_p': quantite * volume_unitaire          # volume total (m³)
            }
        
        return produits_modelisation
    
    def _preparer_vehicules_modelisation(self, vehicules_data, distance_km):
        """
        Prépare les véhicules selon la notation de la modélisation mathématique
        """
        vehicules_modelisation = {}
        
        for l_type, vehicule_type in enumerate(vehicules_data, 1):
            nom_type = vehicule_type.get('nom', f'Type_{l_type}')
            quantite_disponible = vehicule_type.get('quantite', 1)
            
            # Paramètres communs par type
            G_l = vehicule_type.get('cout_variable_km', 280.0)  # Coût variable par km
            vitesse_base = vehicule_type.get('vitesse_kmh', self.V_m)
            
            # Créer les véhicules individuels avec leurs capacités réelles
            vehicules_individuels = {}
            capacite_poids_type = vehicule_type.get('capacite_poids_max', 0) * 1000  # Convertir tonnes en kg
            capacite_volume_type = vehicule_type.get('capacite_volume_max', 0)
            
            for k_id in range(1, quantite_disponible + 1):
                vehicules_individuels[k_id] = {
                    'nom': f"{nom_type}_{k_id}",
                    'type_parent': l_type,
                    'C_w': capacite_poids_type,      # Capacité poids réelle du type
                    'C_v': capacite_volume_type,     # Capacité volume réelle du type
                    'vitesse': vitesse_base,          # Vitesse du type
                    'x_lk': 0,                        # Variable de sélection
                    'n_lk': 0,                        # Nombre d'utilisations
                    'm_lk': 0,                        # Nombre de voyages assignés
                    'tau_lk': 0.0                     # Durée réelle d'utilisation
                }
            
            vehicules_modelisation[l_type] = {
                'nom_type': nom_type,
                'G_l': G_l,                                 # Coût variable commun au type
                'vehicules_individuels': vehicules_individuels,
                'm_l': quantite_disponible                  # Nombre total de véhicules de ce type
            }
        
        return vehicules_modelisation
    
    def _chercher_solution_optimale_complete(self, produits, vehicules, distance_km, duree_max_jours):
        """
        Recherche solution optimale avec modélisation mathématique complète
        """
        print(f"\n🔄 RECHERCHE SOLUTION OPTIMALE COMPLÈTE")
        print(f"   Stratégie: Véhicule unique → Combinaisons multiples")
        
        # Calculer demande totale
        poids_total = sum(p['W_p'] for p in produits.values())
        volume_total = sum(p['V_p'] for p in produits.values())
        
        print(f"   Demande totale: {poids_total:.0f}kg, {volume_total:.1f}m³")
        
        solutions_candidates = []
        
        # 1. Test véhicules individuels
        print(f"\n🔍 ÉTAPE 1: TEST VÉHICULES INDIVIDUELS")
        
        for l_type, type_data in vehicules.items():
            for k_id, vehicule in type_data['vehicules_individuels'].items():
                print(f"\n   Test {vehicule['nom']}")
                
                # Calculer solution pour ce véhicule seul
                solution_individuelle = self._evaluer_vehicule_individuel(
                    vehicule, l_type, k_id, produits, distance_km, duree_max_jours, type_data['G_l']
                )
                
                if solution_individuelle['faisable']:
                    solutions_candidates.append(solution_individuelle)
                    print(f"      ✅ SOLUTION INDIVIDUELLE: {solution_individuelle['cout_total']:.0f}DA")
                else:
                    print(f"      ❌ Non viable seul")
        
        # 2. Test combinaisons multiples si aucune solution individuelle
        if not solutions_candidates:
            print(f"\n🔍 ÉTAPE 2: TEST COMBINAISONS MULTIPLES")
            solutions_candidates = self._chercher_combinaisons_multiples(
                produits, vehicules, distance_km, duree_max_jours
            )
        
        # 3. Sélectionner la meilleure solution
        if solutions_candidates:
            solutions_candidates.sort(key=lambda x: x['cout_total'])
            meilleure_solution = solutions_candidates[0]
            
            print(f"\n🎯 SOLUTION OPTIMALE SÉLECTIONNÉE:")
            print(f"   Type: {meilleure_solution['type_solution']}")
            print(f"   Coût: {meilleure_solution['cout_total']:.0f}DA")
            print(f"   Véhicules: {len(meilleure_solution['vehicules_utilises'])}")
            
            return meilleure_solution
        
        return None
    
    def _calculer_voyages_necessaires(self, vehicule, produits):
        """
        Calcule le nombre de voyages en optimisant le mélange des produits
        SANS hardcode - utilise les paramètres de la classe
        """
        chargements = []
        stock_restant = {p_id: p['q_p'] for p_id, p in produits.items()}
        
        # Protection contre boucle infinie
        max_iterations = 50
        iteration = 0
        
        while any(qty > 0 for qty in stock_restant.values()) and iteration < max_iterations:
            iteration += 1
            
            # Créer un chargement optimal pour ce voyage
            chargement = self._creer_chargement_optimal(vehicule, produits, stock_restant)
            
            # Vérifier si on peut charger quelque chose
            if not chargement or sum(chargement.values()) == 0:
                print(f"      ⚠️ Impossible de charger plus - arrêt")
                break
            
            chargements.append(chargement)
            
            # Mettre à jour le stock restant
            for p_id, qty_chargee in chargement.items():
                if p_id in stock_restant:
                    stock_restant[p_id] = max(0, stock_restant[p_id] - qty_chargee)
        
        nombre_voyages = len(chargements)
        print(f"      ✅ Chargement optimisé: {nombre_voyages} voyage(s)")
        
        return max(1, nombre_voyages)
    def _calculer_contraintes_temporelles_detaillees(self, m_voyages, distance_km, vitesse_kmh):
        """
        Calcule les contraintes temporelles en utilisant les paramètres de la classe
        SANS hardcode
        """
        resultats_par_voyage = []
        temps_total_heures = 0
        
        for voyage_num in range(1, m_voyages + 1):
            # Temps de conduite aller-retour
            temps_conduite = (2 * distance_km) / vitesse_kmh
            
            # Temps de chargement/déchargement (paramètres de la classe)
            temps_operations = self.T_load + self.T_unload
            
            # Calcul des pauses selon la modélisation
            nombre_pauses = 0
            temps_pauses = 0
            if temps_conduite > 2.0:  # Si plus de 2h de conduite
                nombre_pauses = max(0, math.floor((temps_conduite - 2.0) / 2.0) + 1)
                temps_pauses = nombre_pauses * self.T_break
            
            # Calcul des arrêts nocturnes
            duree_activite = temps_conduite + temps_pauses + temps_operations
            nombre_nuits = 0
            temps_nuit = 0
            if duree_activite > 11:  # Si plus de 11h d'activité
                nombre_nuits = max(0, math.floor((duree_activite - 11) / 24) + 1)
                temps_nuit = nombre_nuits * self.T_night
            
            # Temps total pour ce voyage
            temps_total_voyage = temps_conduite + temps_pauses + temps_nuit + temps_operations
            
            resultats_par_voyage.append({
                'voyage': voyage_num,
                'temps_conduite': temps_conduite,
                'nombre_pauses': nombre_pauses,
                'temps_pauses': temps_pauses,
                'nombre_nuits': nombre_nuits,
                'temps_nuit': temps_nuit,
                'temps_total': temps_total_voyage
            })
            
            temps_total_heures += temps_total_voyage
        
        # Conversion en jours de travail (paramètre de la classe)
        tau_total_jours = math.ceil(temps_total_heures / self.T_work)
        
        return {
            'resultats_par_voyage': resultats_par_voyage,
            'temps_total_heures': temps_total_heures,
            'tau_total_jours': tau_total_jours,
            'm_voyages': m_voyages
        }

    def _evaluer_vehicule_individuel(self, vehicule, l_type, k_id, produits, distance_km, duree_max_jours, G_l):
        """
        Évalue un véhicule avec la logique de mélange et sans hardcode
        """
        try:
            # Calculer le nombre de voyages avec optimisation du mélange
            m_lk_necessaires = self._calculer_voyages_necessaires(vehicule, produits)
            
            if m_lk_necessaires <= 0:
                return self._creer_solution_vide()
            
            # Calculer les contraintes temporelles avec les vrais paramètres
            contraintes_temporelles = self._calculer_contraintes_temporelles_detaillees(
                m_lk_necessaires, distance_km, vehicule['vitesse']
            )
            
            tau_lk = contraintes_temporelles['tau_total_jours']
            faisable = tau_lk <= duree_max_jours
            
            # Calcul du coût selon la formule de la modélisation
            cout_total = 0
            if faisable and m_lk_necessaires > 0:
                if m_lk_necessaires == 1:
                    distance_totale = 2 * distance_km
                else:
                    # Formule optimisée : économie sur le dernier trajet
                    distance_totale = m_lk_necessaires * 2 * distance_km - distance_km
                
                cout_total = distance_totale * G_l
            
            return {
                'faisable': faisable,
                'type_solution': 'vehicule_unique',
                'vehicules_utilises': {
                    (l_type, k_id): {
                        'vehicule': vehicule,
                        'x_lk': 1,
                        'n_lk': 1,
                        'm_lk': m_lk_necessaires,
                        'tau_lk': tau_lk
                    }
                },
                'cout_total': cout_total,
                'm_total': m_lk_necessaires,
                'tau_max': tau_lk,
                'contraintes_temporelles': contraintes_temporelles
            }
            
        except Exception as e:
            print(f"      ❌ Erreur dans l'évaluation: {e}")
            return self._creer_solution_vide()

    def _creer_solution_vide(self):
        """
        Crée une solution vide en cas d'échec
        """
        return {
            'faisable': False,
            'type_solution': 'vehicule_unique',
            'vehicules_utilises': {},
            'cout_total': 0,
            'm_total': 0,
            'tau_max': 0,
            'contraintes_temporelles': {}
        }

    def _repartir_produits_equitablement(self, produits, vehicule_index, nombre_total_vehicules):
        """
        Répartit les produits entre véhicules de manière équitable
        """
        produits_vehicule = {}
        
        for p_id, produit in produits.items():
            if produit['q_p'] <= 0:
                continue
            
            # Répartition équitable avec gestion du reste
            quantite_base = produit['q_p'] // nombre_total_vehicules
            reste = produit['q_p'] % nombre_total_vehicules
            
            # Les premiers véhicules prennent le reste
            quantite_vehicule = quantite_base
            if vehicule_index <= reste:
                quantite_vehicule += 1
            
            if quantite_vehicule > 0:
                produits_vehicule[p_id] = {
                    'nom': produit['nom'],
                    'q_p': quantite_vehicule,
                    'w_p': produit['w_p'],
                    'v_p': produit['v_p'],
                    'W_p': quantite_vehicule * produit['w_p'],
                    'V_p': quantite_vehicule * produit['v_p']
                }
        
        return produits_vehicule
    def _creer_chargement_optimal(self, vehicule, produits, stock_restant):
        """
        Crée un chargement optimal pour un voyage en mélangeant les produits
        Utilise un algorithme de sac à dos simplifié
        """
        chargement = {p_id: 0 for p_id in produits.keys()}
        capacite_poids_restante = float(vehicule['C_w'])
        capacite_volume_restante = float(vehicule['C_v'])
        
        # Trier les produits par ratio efficacité/volume (densité)
        produits_tries = []
        for p_id, produit in produits.items():
            if stock_restant.get(p_id, 0) > 0:
                # Calcul de la densité (poids/volume) pour prioriser
                densite = produit['w_p'] / max(produit['v_p'], 0.001)
                produits_tries.append((p_id, densite, produit))
        
        # Trier par densité décroissante (plus dense = priorité)
        produits_tries.sort(key=lambda x: x[1], reverse=True)
        
        # Algorithme de chargement optimisé
        for p_id, _, produit in produits_tries:
            stock_disponible = stock_restant.get(p_id, 0)
            
            if stock_disponible <= 0:
                continue
            
            # Calculer la quantité maximale transportable
            qty_max_poids = float('inf')
            qty_max_volume = float('inf')
            
            if produit['w_p'] > 0:
                qty_max_poids = capacite_poids_restante / produit['w_p']
            
            if produit['v_p'] > 0:
                qty_max_volume = capacite_volume_restante / produit['v_p']
            
            # La contrainte la plus restrictive
            qty_max = min(qty_max_poids, qty_max_volume, stock_disponible)
            qty_max = int(max(0, qty_max))
            
            if qty_max > 0:
                chargement[p_id] = qty_max
                
                # Mettre à jour les capacités restantes
                capacite_poids_restante -= qty_max * produit['w_p']
                capacite_volume_restante -= qty_max * produit['v_p']
                
                # Sécurité pour éviter les valeurs négatives
                capacite_poids_restante = max(0, capacite_poids_restante)
                capacite_volume_restante = max(0, capacite_volume_restante)
        
        return chargement
    

    # Modification de la méthode _evaluer_vehicule_individuel pour gérer le cas de division par zéro
    def _evaluer_vehicule_individuel(self, vehicule, l_type, k_id, produits, distance_km, duree_max_jours, G_l):
        """
        Évalue si un véhicule individuel peut accomplir la mission seul
        Version corrigée avec gestion d'erreur robuste
        """
        try:
            # Calculer nombre de voyages nécessaires
            m_lk_necessaires = self._calculer_voyages_necessaires(vehicule, produits)
            
            # Vérification de sécurité
            if m_lk_necessaires <= 0:
                return {
                    'faisable': False,
                    'type_solution': 'vehicule_unique',
                    'vehicules_utilises': {},
                    'cout_total': 0,
                    'm_total': 0,
                    'tau_max': 0,
                    'contraintes_temporelles': {}
                }
            
            # Calculer contraintes temporelles détaillées
            contraintes_temporelles = self._calculer_contraintes_temporelles_detaillees(
                m_lk_necessaires, distance_km, vehicule['vitesse']
            )
            
            tau_lk = contraintes_temporelles['tau_total_jours']
            
            # Vérifier faisabilité temporelle
            faisable = tau_lk <= duree_max_jours
            
            cout_total = 0
            if faisable and m_lk_necessaires > 0:
                # CORRECTION: Calcul du coût avec protection contre division par zéro
                if m_lk_necessaires == 1:
                    distance_totale = 2 * distance_km  # Aller-retour simple
                else:
                    # Utiliser la formule corrigée
                    distance_totale = m_lk_necessaires * 2 * distance_km * (1 - 1/(2*m_lk_necessaires))
                
                cout_total = distance_totale * G_l
                
                # Validation du coût
                if cout_total <= 0:
                    cout_total = m_lk_necessaires * 2 * distance_km * G_l  # Calcul de base
            
            return {
                'faisable': faisable,
                'type_solution': 'vehicule_unique',
                'vehicules_utilises': {
                    (l_type, k_id): {
                        'vehicule': vehicule,
                        'x_lk': 1,
                        'n_lk': 1,
                        'm_lk': m_lk_necessaires,
                        'tau_lk': tau_lk
                    }
                },
                'cout_total': cout_total,
                'm_total': m_lk_necessaires,
                'tau_max': tau_lk,
                'contraintes_temporelles': contraintes_temporelles
            }
            
        except Exception as e:
            print(f"      ❌ Erreur dans l'évaluation du véhicule: {e}")
            return {
                'faisable': False,
                'type_solution': 'vehicule_unique',
                'vehicules_utilises': {},
                'cout_total': 0,
                'm_total': 0,
                'tau_max': 0,
                'contraintes_temporelles': {}
            }
        
    
    def _calculer_contraintes_temporelles_detaillees(self, m_voyages, distance_km, vitesse_kmh):
        """
        Calcule les contraintes temporelles détaillées selon la modélisation
        """
        resultats_par_voyage = []
        temps_total_heures = 0
        
        for t in range(1, m_voyages + 1):
            # Temps de conduite par voyage (aller-retour)
            T_conduite = (2 * distance_km) / vitesse_kmh
            
            # Calcul des pauses selon la formule exacte de la modélisation
            N_pauses = max(0, math.floor((T_conduite - 2.0) / 2.0) + 1) if T_conduite > 2.0 else 0
            T_pauses = N_pauses * self.T_break
            
            # Détection des arrêts nocturnes
            duree_activite = T_conduite + T_pauses + self.T_load + self.T_unload
            N_nuits = max(0, math.floor((duree_activite - 11) / 24) + 1) if duree_activite > 11 else 0
            T_nuit = N_nuits * self.T_night
            
            # Temps total par voyage
            T_total_voyage = T_conduite + T_pauses + T_nuit + self.T_load + self.T_unload
            
            resultats_par_voyage.append({
                'voyage': t,
                'T_conduite': T_conduite,
                'N_pauses': N_pauses,
                'T_pauses': T_pauses,
                'N_nuits': N_nuits,
                'T_nuit': T_nuit,
                'T_total': T_total_voyage
            })
            
            temps_total_heures += T_total_voyage
        
        # Durée totale en jours (arrondie au jour supérieur)
        tau_total_jours = math.ceil(temps_total_heures / self.T_work)
        
        return {
            'resultats_par_voyage': resultats_par_voyage,
            'temps_total_heures': temps_total_heures,
            'tau_total_jours': tau_total_jours,
            'm_voyages': m_voyages
        }
    
    def _chercher_combinaisons_multiples(self, produits, vehicules, distance_km, duree_max_jours):
        """
        Cherche les meilleures combinaisons de véhicules multiples
        """
        print(f"\n   🔄 COMBINAISONS MULTIPLES NÉCESSAIRES")
        
        solutions_candidates = []
        
        # Tester toutes les combinaisons possibles (approche heuristique)
        for l_type1, type_data1 in vehicules.items():
            for k_id1, vehicule1 in type_data1['vehicules_individuels'].items():
                
                # Solution avec 2 véhicules du même type
                solution_homogene = self._tester_solution_homogene(
                    vehicule1, l_type1, type_data1, produits, distance_km, duree_max_jours, 2
                )
                if solution_homogene and solution_homogene['faisable']:
                    solutions_candidates.append(solution_homogene)
                
                # Solution avec 3 véhicules du même type
                solution_homogene_3 = self._tester_solution_homogene(
                    vehicule1, l_type1, type_data1, produits, distance_km, duree_max_jours, 3
                )
                if solution_homogene_3 and solution_homogene_3['faisable']:
                    solutions_candidates.append(solution_homogene_3)
                
                # Solutions hétérogènes
                for l_type2, type_data2 in vehicules.items():
                    if l_type2 <= l_type1:  # Éviter les doublons
                        continue
                        
                    for k_id2, vehicule2 in type_data2['vehicules_individuels'].items():
                        solution_heterogene = self._tester_solution_heterogene(
                            vehicule1, l_type1, k_id1, type_data1,
                            vehicule2, l_type2, k_id2, type_data2,
                            produits, distance_km, duree_max_jours
                        )
                        
                        if solution_heterogene and solution_heterogene['faisable']:
                            solutions_candidates.append(solution_heterogene)
        
        return solutions_candidates
    
    def _tester_solution_homogene(self, vehicule_reference, l_type, type_data, produits, distance_km, duree_max_jours, nb_vehicules):
        """
        Teste une solution avec plusieurs véhicules du même type
        """
        if nb_vehicules > type_data['m_l']:  # Plus de véhicules que disponibles
            return None
        
        # Répartir la charge entre les véhicules
        charge_totale_poids = sum(p['W_p'] for p in produits.values())
        charge_totale_volume = sum(p['V_p'] for p in produits.values())
        
        # Vérifier si la capacité totale est suffisante
        capacite_totale_poids = nb_vehicules * vehicule_reference['C_w']
        capacite_totale_volume = nb_vehicules * vehicule_reference['C_v']
        
        if (capacite_totale_poids < charge_totale_poids or 
            capacite_totale_volume < charge_totale_volume):
            return None
        
        # Répartir intelligemment la charge
        vehicules_utilises = {}
        cout_total = 0
        tau_max = 0
        
        # Répartition équitable par véhicule
        for k_idx in range(1, nb_vehicules + 1):
            vehicule_k = type_data['vehicules_individuels'][k_idx]
            
            # Calculer la part de ce véhicule (répartition équitable)
            produits_vehicule = self._repartir_produits_equitablement(
                produits, k_idx, nb_vehicules
            )
            
            m_lk = self._calculer_voyages_necessaires(vehicule_k, produits_vehicule)
            contraintes_temp = self._calculer_contraintes_temporelles_detaillees(
                m_lk, distance_km, vehicule_k['vitesse']
            )
            
            tau_lk = contraintes_temp['tau_total_jours']
            tau_max = max(tau_max, tau_lk)
            
            # Coût pour ce véhicule
            distance_totale = m_lk * (2 * distance_km - distance_km / m_lk) if m_lk > 0 else 0
            cout_vehicule = distance_totale * type_data['G_l']
            cout_total += cout_vehicule
            
            vehicules_utilises[(l_type, k_idx)] = {
                'vehicule': vehicule_k,
                'x_lk': 1,
                'n_lk': 1,
                'm_lk': m_lk,
                'tau_lk': tau_lk
            }
        
        faisable = tau_max <= duree_max_jours
        
        return {
            'faisable': faisable,
            'type_solution': 'flotte_homogene',
            'vehicules_utilises': vehicules_utilises,
            'cout_total': cout_total,
            'tau_max': tau_max,
            'nb_vehicules': nb_vehicules
        }
    
    def _tester_solution_heterogene(self, vehicule1, l_type1, k_id1, type_data1,
                                   vehicule2, l_type2, k_id2, type_data2,
                                   produits, distance_km, duree_max_jours):
        """
        Teste une solution avec deux véhicules de types différents
        """
        # Répartir intelligemment les produits entre les deux véhicules
        repartition = self._repartir_produits_entre_vehicules(
            vehicule1, vehicule2, produits
        )
        
        vehicules_utilises = {}
        cout_total = 0
        tau_max = 0
        
        # Véhicule 1
        m_lk1 = self._calculer_voyages_necessaires(vehicule1, repartition['vehicule1'])
        contraintes_temp1 = self._calculer_contraintes_temporelles_detaillees(
            m_lk1, distance_km, vehicule1['vitesse']
        )
        tau_lk1 = contraintes_temp1['tau_total_jours']
        
        distance_totale1 = m_lk1 * (2 * distance_km - distance_km / m_lk1) if m_lk1 > 0 else 0
        cout1 = distance_totale1 * type_data1['G_l']
        
        vehicules_utilises[(l_type1, k_id1)] = {
            'vehicule': vehicule1,
            'x_lk': 1,
            'n_lk': 1,
            'm_lk': m_lk1,
            'tau_lk': tau_lk1
        }
        
        # Véhicule 2
        m_lk2 = self._calculer_voyages_necessaires(vehicule2, repartition['vehicule2'])
        contraintes_temp2 = self._calculer_contraintes_temporelles_detaillees(
            m_lk2, distance_km, vehicule2['vitesse']
        )
        tau_lk2 = contraintes_temp2['tau_total_jours']
        
        distance_totale2 = m_lk2 * (2 * distance_km - distance_km / m_lk2) if m_lk2 > 0 else 0
        cout2 = distance_totale2 * type_data2['G_l']
        
        vehicules_utilises[(l_type2, k_id2)] = {
            'vehicule': vehicule2,
            'x_lk': 1,
            'n_lk': 1,
            'm_lk': m_lk2,
            'tau_lk': tau_lk2
        }
        
        cout_total = cout1 + cout2
        tau_max = max(tau_lk1, tau_lk2)
        faisable = tau_max <= duree_max_jours
        
        return {
            'faisable': faisable,
            'type_solution': 'flotte_heterogene',
            'vehicules_utilises': vehicules_utilises,
            'cout_total': cout_total,
            'tau_max': tau_max,
            'nb_vehicules': 2
        }
    
    def _repartir_produits_equitablement(self, produits, k_idx, nb_vehicules_total):
        """
        Répartit les produits équitablement entre les véhicules d'un même type
        """
        produits_vehicule = {}
        
        for p_id, produit in produits.items():
            # Répartition équitable avec gestion du reste
            quantite_base = produit['q_p'] // nb_vehicules_total
            reste = produit['q_p'] % nb_vehicules_total
            
            # Les premiers véhicules prennent une unité de plus si il y a un reste
            quantite_vehicule = quantite_base + (1 if k_idx <= reste else 0)
            
            if quantite_vehicule > 0:
                produits_vehicule[p_id] = {
                    'nom': produit['nom'],
                    'q_p': quantite_vehicule,
                    'w_p': produit['w_p'],
                    'v_p': produit['v_p'],
                    'W_p': quantite_vehicule * produit['w_p'],
                    'V_p': quantite_vehicule * produit['v_p']
                }
        
        return produits_vehicule
    
    
    
    def _convertir_solution_vers_format_retour(self, solution, produits_originaux, date_debut, heure_debut, duree_max_jours):
        """
        Convertit la solution optimale vers le format de retour attendu
        """
        # Extraire informations principales
        vehicules_utilises = solution['vehicules_utilises']
        cout_total = solution['cout_total']
        type_solution = solution['type_solution']
        
        # Construire description des véhicules
        vehicules_descriptions = []
        vehicules_details = []
        nb_vehicules_total = len(vehicules_utilises)
        
        for (l_type, k_id), vehicule_data in vehicules_utilises.items():
            nom_vehicule = vehicule_data['vehicule']['nom']
            vehicules_descriptions.append(nom_vehicule)
            vehicules_details.append({
                'nom': nom_vehicule,
                'type': l_type,
                'voyages': vehicule_data['m_lk'],
                'duree_jours': vehicule_data['tau_lk']
            })
        
        # Nom combiné pour l'affichage
        if nb_vehicules_total == 1:
            nom_vehicule_affichage = vehicules_descriptions[0]
            vehicule_principal = vehicules_descriptions[0]
            vehicule_secondaire = None
            nb_vehicules_principal = 1
            nb_vehicules_secondaire = 0
        else:
            nom_vehicule_affichage = " + ".join(vehicules_descriptions)
            vehicule_principal = vehicules_descriptions[0]
            vehicule_secondaire = vehicules_descriptions[1] if len(vehicules_descriptions) > 1 else None
            nb_vehicules_principal = 1
            nb_vehicules_secondaire = nb_vehicules_total - 1
        
        # Calculer demande équivalente
        poids_total = sum(p['poids_unitaire'] for p in produits_originaux) * 1000  # en kg
        volume_total = sum(p['volume_unitaire'] for p in produits_originaux)
        distance_km = produits_originaux[0].get('distance_km', 800)
        
        demande_equivalente = {
            'nom': 'TRANSPORT OPTIMISÉ MULTI-PRODUITS',
            'distance_km': distance_km,
            'vitesse_kmh': produits_originaux[0].get('vitesse_kmh', 80),
            'quantite_poids': poids_total / 1000,  # en tonnes
            'quantite_volume': volume_total
        }
        
        # Format de retour unifié
        return {
            'type_solution': type_solution,
            'vehicule_principal': vehicule_principal,
            'vehicule_secondaire': vehicule_secondaire,
            'nb_vehicules_principal': nb_vehicules_principal,
            'nb_vehicules_secondaire': nb_vehicules_secondaire,
            'cout_total': cout_total,
            'duree_reelle': solution['tau_max'],
            'respect_contrainte': solution['faisable'],
            'demande_equivalente': demande_equivalente,
            'vehicule_optimal': {
                'cout_total': cout_total
            },
            'vehicule_utilise': {
                'nom': nom_vehicule_affichage,
                'type': 'OPTIMISE_MODELISATION',
                'details': vehicules_details
            },
            'nb_vehicules_necessaires': nb_vehicules_total,
            'solution_detaillee': {
                'vehicules_utilises': vehicules_utilises,
                'contraintes_respectees': solution['faisable'],
                'optimisation_complete': True
            }
        }


class OptimisateurNavettes:
    """
    Version intégrée qui combine l'ancienne heuristique et la nouvelle optimisation
    """
    
    def __init__(self):
        self.optimisateur_ameliore = OptimisateurNavettesAmeliore()
        # Conserver l'ancien optimisateur comme fallback si nécessaire
        
    def calculer_navettes_optimales(self, produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours=7):
        """
        Point d'entrée principal qui utilise la nouvelle optimisation
        """
        print(f"\n🚀 OPTIMISATION INTÉGRÉE - MODÉLISATION MATHÉMATIQUE COMPLÈTE")
        print(f"🔧 Utilisation de l'algorithme amélioré avec contraintes détaillées")
        
        try:
            # Utiliser directement la nouvelle optimisation
            resultat = self.optimisateur_ameliore.calculer_navettes_optimales(
                produits_a_transporter, 
                vehicules_data, 
                date_debut, 
                heure_debut, 
                duree_max_jours
            )
            
            if resultat:
                print(f"\n✅ OPTIMISATION RÉUSSIE!")
                print(f"   Type de solution: {resultat['type_solution']}")
                print(f"   Véhicule(s): {resultat['vehicule_utilise']['nom']}")
                print(f"   Coût total: {resultat['cout_total']:.0f} DA")
                print(f"   Durée réelle: {resultat['duree_reelle']:.1f} jours")
                print(f"   Contraintes respectées: {resultat['respect_contrainte']}")
                
                return resultat
            else:
                print(f"\n❌ AUCUNE SOLUTION TROUVÉE")
                return None
                
        except Exception as e:
            print(f"❌ ERREUR dans l'optimisation intégrée: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def afficher_details_solution(self, solution):
        """
        Affiche les détails complets d'une solution
        """
        if not solution:
            print("Aucune solution à afficher")
            return
        
        print(f"\n" + "="*80)
        print("DÉTAILS DE LA SOLUTION OPTIMALE")
        print("="*80)
        
        print(f"📊 INFORMATIONS GÉNÉRALES:")
        print(f"   Type de solution: {solution['type_solution']}")
        print(f"   Coût total: {solution['cout_total']:.2f} DA")
        print(f"   Durée réelle: {solution['duree_reelle']:.1f} jours")
        print(f"   Respect des contraintes: {'✅ OUI' if solution['respect_contrainte'] else '❌ NON'}")
        print(f"   Nombre de véhicules: {solution['nb_vehicules_necessaires']}")
        
        print(f"\n🚛 VÉHICULES UTILISÉS:")
        if solution['vehicule_principal']:
            print(f"   Principal: {solution['vehicule_principal']} (×{solution['nb_vehicules_principal']})")
        if solution.get('vehicule_secondaire'):
            print(f"   Secondaire: {solution['vehicule_secondaire']} (×{solution['nb_vehicules_secondaire']})")
        
        print(f"\n📦 DEMANDE TRAITÉE:")
        demande = solution['demande_equivalente']
        print(f"   Poids: {demande['quantite_poids']:.2f} tonnes")
        print(f"   Volume: {demande['quantite_volume']:.2f} m³")
        print(f"   Distance: {demande['distance_km']} km")
        
        # Détails techniques si disponibles
        if 'solution_detaillee' in solution and solution['solution_detaillee'].get('vehicules_utilises'):
            print(f"\n🔧 DÉTAILS TECHNIQUES:")
            for (l_type, k_id), vehicule_data in solution['solution_detaillee']['vehicules_utilises'].items():
                print(f"   Véhicule {vehicule_data['vehicule']['nom']}:")
                print(f"      Voyages assignés: {vehicule_data['m_lk']}")
                print(f"      Durée d'utilisation: {vehicule_data['tau_lk']:.1f} jours")
                print(f"      Capacités: {vehicule_data['vehicule']['C_w']:.0f}kg, {vehicule_data['vehicule']['C_v']:.1f}m³")
        
        print(f"\n💰 ANALYSE ÉCONOMIQUE:")
        if solution['demande_equivalente']['quantite_poids'] > 0:
            cout_par_tonne = solution['cout_total'] / solution['demande_equivalente']['quantite_poids']
            print(f"   Coût par tonne: {cout_par_tonne:.2f} DA/t")
        
        if solution['demande_equivalente']['quantite_volume'] > 0:
            cout_par_m3 = solution['cout_total'] / solution['demande_equivalente']['quantite_volume']
            print(f"   Coût par m³: {cout_par_m3:.2f} DA/m³")
        
        print(f"="*80)

    # Exécuter l'heuristique détaillée
    
def executer_heuristique_detaillee():
    """
    Fonction principale pour exécuter uniquement l'heuristique détaillée
    Version complètement corrigée avec extraction de noms et nouvelle logique de capacité
    """
    print("="*80)
    print("SYSTÈME D'OPTIMISATION DE NAVETTES - HEURISTIQUE DÉTAILLÉE")
    print("="*80)
    
    # Paramètres de configuration
    ID_CLIENT = "EGS-150"
    CIBLE_LONGITUDE = -2.2162
    CIBLE_LATITUDE = 31.6177
    
    try:
        # 1. Créer l'instance d'optimisation
        print(f"\n🔧 CRÉATION DE L'INSTANCE D'OPTIMISATION...")
        instance = creer_instance_optimisation(
            id_client=ID_CLIENT,
            cible_longitude=CIBLE_LONGITUDE,
            cible_latitude=CIBLE_LATITUDE
        )
        
        if not instance:
            print("❌ Impossible de créer l'instance.")
            return None
        
        instance.afficher_resume()
        
        # 2. Préparation des données véhicules
        print(f"\n🔄 PRÉPARATION DES DONNÉES VÉHICULES...")
        vehicules_data = []
        for vtype, capacites in instance.L.items():
            vehicule_info = {
                'nom': instance.get_vehicle_type_name(vtype),
                'type': 'LEGER' if capacites['Qw'] < 5000 else 'MOYEN' if capacites['Qw'] < 20000 else 'LOURD',
                'capacite_poids_max': capacites['Qw'] / 1000,  # Convertir en tonnes
                'capacite_volume_max': capacites['Qv'],
                'vitesse_kmh': instance.V[vtype],
                'cout_variable_km': instance.c[vtype],  # Coût variable par km en DA
                'quantite': instance.m[vtype]
            }
            vehicules_data.append(vehicule_info)
        
        print(f"✅ {len(vehicules_data)} types de véhicules préparés")
        
        # Affichage détaillé des véhicules préparés
        print(f"\n📋 VÉHICULES PRÉPARÉS POUR L'OPTIMISATION:")
        for i, vehicule in enumerate(vehicules_data, 1):
            print(f"   {i}. {vehicule['nom']}")
            print(f"      Capacités: {vehicule['capacite_poids_max']:.1f}t, {vehicule['capacite_volume_max']:.1f}m³")
            print(f"      Vitesse: {vehicule['vitesse_kmh']} km/h")
            print(f"      Coût variable: {vehicule['cout_variable_km']:.0f} DA/km")
            print(f"      Quantité: {vehicule['quantite']}")
        
        # Variables pour statistiques globales
        cout_total_projet = 0
        semaines_traitees = 0
        semaines_reussies = 0
        
        resultats_par_semaine = {}
        
        # 3. Traitement par semaine
        for semaine in instance.T:
            print(f"\n" + "="*80)
            print(f"SEMAINE {semaine} - OPTIMISATION HEURISTIQUE")
            print("="*80)
            
            # Vérifier les demandes pour cette semaine
            poids_semaine = instance.dw_AB.get(semaine, 0)
            volume_semaine = instance.dv_AB.get(semaine, 0)
            
            if poids_semaine <= 0 and volume_semaine <= 0:
                print(f"   📭 Aucune livraison planifiée pour la semaine {semaine}")
                continue
            
            semaines_traitees += 1
            
            print(f"📦 DEMANDES SEMAINE {semaine}:")
            print(f"   Poids total: {poids_semaine:.1f} kg ({poids_semaine/1000:.2f} tonnes)")
            print(f"   Volume total: {volume_semaine:.1f} m³")
            
            # Créer produit équivalent pour cette semaine
            produits_semaine = [{
                'nom': f'ÉQUIPEMENTS_SEMAINE_{semaine}',
                'quantite': 1,
                'poids_unitaire': poids_semaine / 1000,  # Convertir en tonnes
                'volume_unitaire': volume_semaine,
                'distance_km': instance.d_AB,
                'vitesse_kmh': 80
            }]
            
            # Optimisation heuristique pour cette semaine
            optimiseur = OptimisateurNavettes()
            
            date_debut_semaine = '2025-06-02'
            heure_debut = '08:00'
            
            print(f"\n🚀 DÉBUT OPTIMISATION HEURISTIQUE SEMAINE {semaine}")
            
            resultats_semaine = optimiseur.calculer_navettes_optimales(
                produits_semaine,
                vehicules_data,
                date_debut_semaine,
                heure_debut,
                duree_max_jours=7
            )
            
            if resultats_semaine:
                # Extraction des résultats avec gestion correcte des noms
                cout_semaine = resultats_semaine.get('vehicule_optimal', {}).get('cout_total', 0)
                
                # EXTRACTION CORRECTE DU NOM DU VÉHICULE
                vehicule_utilise = "Véhicule Inconnu"  # Valeur par défaut
                
                if 'vehicule_utilise' in resultats_semaine:
                    # Cas 1: vehicule_utilise existe directement
                    vehicule_data = resultats_semaine['vehicule_utilise']
                    if isinstance(vehicule_data, dict):
                        vehicule_utilise = vehicule_data.get('nom', 'Véhicule Inconnu')
                    else:
                        vehicule_utilise = str(vehicule_data)
                        
                elif 'vehicule_principal' in resultats_semaine:
                    # Cas 2: solution avec vehicule_principal (et possiblement vehicule_secondaire)
                    vehicule_principal = resultats_semaine.get('vehicule_principal', 'V1')
                    vehicule_secondaire = resultats_semaine.get('vehicule_secondaire')
                    
                    if vehicule_secondaire:
                        # Solution hétérogène
                        vehicule_utilise = f"{vehicule_principal} + {vehicule_secondaire}"
                    else:
                        # Solution homogène
                        vehicule_utilise = str(vehicule_principal)
                
                type_solution = resultats_semaine.get('type_solution', 'inconnu')
                
                # Affichage des résultats
                print(f"\n✅ SEMAINE {semaine} - SOLUTION TROUVÉE!")
                print(f"   Type de solution: {type_solution}")
                print(f"   Véhicule(s) utilisé(s): {vehicule_utilise}")
                print(f"   Coût: {cout_semaine:.2f} DA")
                print(f"   Respect contrainte: {resultats_semaine.get('respect_contrainte', False)}")
                
                # Affichage détaillé si solution combinaison
                if 'nb_vehicules_principal' in resultats_semaine:
                    print(f"   Nb véhicules principal: {resultats_semaine.get('nb_vehicules_principal', 0)}")
                    if resultats_semaine.get('nb_vehicules_secondaire', 0) > 0:
                        print(f"   Nb véhicules secondaire: {resultats_semaine.get('nb_vehicules_secondaire', 0)}")
                
                # Stockage des résultats
                resultats_par_semaine[semaine] = {
                    'cout': cout_semaine,
                    'vehicule': vehicule_utilise,
                    'type_solution': type_solution,
                    'poids': poids_semaine / 1000,
                    'volume': volume_semaine,
                    'nb_vehicules': resultats_semaine.get('nb_vehicules_necessaires', 1),
                    'nb_vehicules_principal': resultats_semaine.get('nb_vehicules_principal', 1),
                    'nb_vehicules_secondaire': resultats_semaine.get('nb_vehicules_secondaire', 0)
                }
                
                cout_total_projet += cout_semaine
                semaines_reussies += 1
                
            else:
                print(f"\n❌ SEMAINE {semaine} - AUCUNE SOLUTION TROUVÉE")
                resultats_par_semaine[semaine] = {
                    'cout': 0,
                    'vehicule': 'AUCUN',
                    'type_solution': 'echec',
                    'poids': poids_semaine / 1000,
                    'volume': volume_semaine,
                    'nb_vehicules': 0,
                    'nb_vehicules_principal': 0,
                    'nb_vehicules_secondaire': 0
                }
        
        # 4. Résumé final détaillé
        print(f"\n" + "="*80)
        print("RÉSUMÉ FINAL HEURISTIQUE DÉTAILLÉE")
        print("="*80)
        
        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"   Semaines avec demandes: {semaines_traitees}")
        print(f"   Semaines réussies: {semaines_reussies}")
        print(f"   Taux de réussite: {(semaines_reussies/max(semaines_traitees,1)*100):.1f}%")
        print(f"   Coût total projet: {cout_total_projet:.2f} DA")
        
        if semaines_reussies > 0:
            cout_moyen = cout_total_projet / semaines_reussies
            print(f"   Coût moyen par semaine: {cout_moyen:.2f} DA")
        
        print(f"\n📋 DÉTAIL PAR SEMAINE:")
        print(f"{'Sem':<4} {'Poids(t)':<8} {'Volume(m³)':<10} {'Véhicule':<25} {'Type':<15} {'Coût(DA)':<12} {'Nb Véh':<6}")
        print("-" * 90)
        
        for semaine in sorted(resultats_par_semaine.keys()):
            result = resultats_par_semaine[semaine]
            vehicule_affiche = result['vehicule'][:23] + "..." if len(result['vehicule']) > 25 else result['vehicule']
            print(f"{semaine:<4} {result['poids']:<8.1f} {result['volume']:<10.1f} {vehicule_affiche:<25} {result['type_solution']:<15} {result['cout']:<12.0f} {result['nb_vehicules']:<6}")
        
        # Analyse des véhicules utilisés
        vehicules_count = {}
        types_solutions = {}
        nb_vehicules_total = 0
        
        for result in resultats_par_semaine.values():
            vehicule = result['vehicule']
            if vehicule != 'AUCUN':
                vehicules_count[vehicule] = vehicules_count.get(vehicule, 0) + 1
                nb_vehicules_total += result['nb_vehicules']
            
            type_sol = result['type_solution']
            types_solutions[type_sol] = types_solutions.get(type_sol, 0) + 1
        
        print(f"\n🚛 VÉHICULES LES PLUS UTILISÉS:")
        for vehicule, count in sorted(vehicules_count.items(), key=lambda x: x[1], reverse=True):
            print(f"   {vehicule}: {count} semaine(s)")
        
        print(f"\n📈 TYPES DE SOLUTIONS:")
        for type_sol, count in sorted(types_solutions.items(), key=lambda x: x[1], reverse=True):
            print(f"   {type_sol}: {count} semaine(s)")
        
        # Calcul de métriques d'efficacité
        poids_total_projet = sum(result['poids'] for result in resultats_par_semaine.values())
        volume_total_projet = sum(result['volume'] for result in resultats_par_semaine.values())
        
        print(f"\n📦 CHARGE TOTALE TRANSPORTÉE:")
        print(f"   Poids total: {poids_total_projet:.1f} tonnes")
        print(f"   Volume total: {volume_total_projet:.1f} m³")
        print(f"   Véhicules mobilisés: {nb_vehicules_total}")
        
        if cout_total_projet > 0 and poids_total_projet > 0:
            cout_par_tonne = cout_total_projet / poids_total_projet
            cout_par_m3 = cout_total_projet / max(volume_total_projet, 1)
            
            print(f"\n💰 EFFICACITÉ ÉCONOMIQUE:")
            print(f"   Coût par tonne: {cout_par_tonne:.2f} DA/t")
            print(f"   Coût par m³: {cout_par_m3:.2f} DA/m³")
        
        # Analyse des flottes utilisées
        print(f"\n🔍 ANALYSE DES FLOTTES:")
        flottes_homogenes = sum(1 for r in resultats_par_semaine.values() if r['type_solution'] == 'flotte_homogene')
        flottes_heterogenes = sum(1 for r in resultats_par_semaine.values() if r['type_solution'] == 'flotte_heterogene')
        vehicules_uniques = sum(1 for r in resultats_par_semaine.values() if r['type_solution'] == 'vehicule_unique')
        
        if flottes_homogenes > 0:
            print(f"   Flottes homogènes: {flottes_homogenes} semaine(s)")
        if flottes_heterogenes > 0:
            print(f"   Flottes hétérogènes: {flottes_heterogenes} semaine(s)")
        if vehicules_uniques > 0:
            print(f"   Véhicules uniques: {vehicules_uniques} semaine(s)")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        
        if semaines_reussies == semaines_traitees:
            print(f"   ✅ Toutes les semaines ont été optimisées avec succès")
            print(f"   ✅ L'heuristique est efficace pour ce projet")
            
            # Recommandation sur le type de véhicule le plus rentable
            if vehicules_count:
                vehicule_prefere = max(vehicules_count.items(), key=lambda x: x[1])[0]
                nb_utilisations = vehicules_count[vehicule_prefere]
                print(f"   🎯 Véhicule le plus utilisé: {vehicule_prefere} ({nb_utilisations} fois)")
                
        else:
            echecs = semaines_traitees - semaines_reussies
            print(f"   ⚠️ {echecs} semaine(s) non résolue(s)")
            print(f"   💡 Solutions possibles:")
            print(f"      - Augmenter la flotte disponible")
            print(f"      - Étaler sur plus de jours (>7 jours)")
            print(f"      - Revoir la capacité des véhicules")
            
            # Analyser les échecs
            semaines_echec = [s for s, r in resultats_par_semaine.items() if r['type_solution'] == 'echec']
            if semaines_echec:
                poids_echec = sum(resultats_par_semaine[s]['poids'] for s in semaines_echec)
                volume_echec = sum(resultats_par_semaine[s]['volume'] for s in semaines_echec)
                print(f"   📊 Charge non transportée: {poids_echec:.1f}t, {volume_echec:.1f}m³")
        
        print(f"\n" + "="*80)
        print("FIN DE L'OPTIMISATION HEURISTIQUE DÉTAILLÉE")
        print("="*80)
        
        return {
            'resultats_par_semaine': resultats_par_semaine,
            'cout_total': cout_total_projet,
            'semaines_traitees': semaines_traitees,
            'semaines_reussies': semaines_reussies,
            'taux_reussite': (semaines_reussies/max(semaines_traitees,1)*100),
            'vehicules_utilises': vehicules_count,
            'types_solutions': types_solutions,
            'poids_total': poids_total_projet,
            'volume_total': volume_total_projet,
            'nb_vehicules_total': nb_vehicules_total,
            'instance': instance,
            'efficacite_economique': {
                'cout_par_tonne': cout_total_projet / max(poids_total_projet, 1),
                'cout_par_m3': cout_total_projet / max(volume_total_projet, 1)
            } if cout_total_projet > 0 and poids_total_projet > 0 else None
        }
        
    except Exception as e:
        print(f"❌ ERREUR LORS DE L'EXÉCUTION: {e}")
        import traceback
        traceback.print_exc()
        return None


# Point d'entrée principal
if __name__ == "__main__":
    # Exécuter l'heuristique détaillée
    resultats = executer_heuristique_detaillee()
    
    if resultats:
        print(f"\n🎉 EXÉCUTION TERMINÉE AVEC SUCCÈS!")
        print(f"   Taux de réussite: {resultats['taux_reussite']:.1f}%")
        print(f"   Coût total: {resultats['cout_total']:.2f}DA")
    else:
        print(f"\n❌ ÉCHEC DE L'EXÉCUTI")


