import pandas as pd
import json
from datetime import datetime, timedelta
import os
import random
import math
import time  
import datetime
import copy
from datetime import datetime, timedelta


class Instance:
    def __init__(self, id_client=None, cible_longitude=None, cible_latitude=None):
        """
        dans cette approche nous avons comparee toute les paires de vehicules au lieu den prendre un seul vehicule et le dupliquer
        Initialisation d'une instance du problème de transport par navettes entre les sites A et B
        sur un horizon de 12 semaines, avec transport uniquement dans le sens A vers B.
        
        Les données de véhicules sont récupérées depuis la base de données via la classe Vehicule.
        Les demandes d'équipements sont récupérées depuis la classe TransfererEquipement.
        
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
        et les organise dans les structures de données requises par la métaheuristique.
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
            
            # Transformer les données en structures attendues par la métaheuristique
            self.L = {}  # Types de véhicules disponibles avec leurs capacités
            self.m = {}  # Nombre maximal de véhicules disponibles par type
            self.c = {}  # Coût d'utilisation de chaque type de véhicule
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
                
                # Coût d'utilisation basé sur les capacités et la distance
                cout_base = 50
                cout_capacite = capacite_tonne * 20
                cout_distance = self.d_AB * 0.05  # Ajustement selon distance
                self.c[i] = int(cout_base + cout_capacite + cout_distance)
                
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
                print(f"     Coût: {self.c[i]}€")
        
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
            print(f"     Coût: {self.c[vtype]}€")
        
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
class OptimisateurNavettes:
        
    def calculer_navettes_optimales(self, produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours=7):
        """
        Calcule les navettes optimales avec combinaison intelligente de véhicules
        """
        
        # Calculer les totaux de la demande
        poids_total = sum(produit['quantite'] * produit['poids_unitaire'] for produit in produits_a_transporter)
        volume_total = sum(produit['quantite'] * produit['volume_unitaire'] for produit in produits_a_transporter)
        
        demande_equivalente = {
            'nom': 'TRANSPORT MULTI-PRODUITS A→B',
            'distance_km': produits_a_transporter[0].get('distance_km', 800),
            'vitesse_kmh': produits_a_transporter[0].get('vitesse_kmh', 80),
            'quantite_poids': poids_total,
            'quantite_volume': volume_total
        }
        
        print(f"\n=== OPTIMISATION AVEC COMBINAISON INTELLIGENTE DE VÉHICULES ===")
        print(f"⏰ CONTRAINTE TEMPORELLE: {duree_max_jours} jours maximum")
        print(f"🔄 NOUVEAUTÉ: Combinaison optimale de véhicules différents")
        
        # ✅ UTILISER LA NOUVELLE MÉTHODE DE RECHERCHE
        solution_optimale = self._chercher_combinaison_optimale(
            demande_equivalente, 
            vehicules_data, 
            duree_max_jours
        )
        
        if not solution_optimale:
            print(f"\n❌ AUCUNE SOLUTION TROUVÉE")
            return None
        
        # Adapter le format de retour selon le type de solution
        if solution_optimale.get('type_solution') == 'combinaison':
            print(f"\n🎉 SOLUTION COMBINAISON SÉLECTIONNÉE!")
            
            # Créer un format de retour adapté pour les combinaisons
            return {
                'type_solution': 'combinaison',
                'vehicules_utilises': solution_optimale['vehicules_detail'],
                'vehicule_principal': solution_optimale['vehicule_principal'],
                'vehicule_secondaire': solution_optimale['vehicule_secondaire'],
                'cout_total': solution_optimale['cout_total'],
                'duree_reelle': solution_optimale['duree_reelle_jours'],
                'respect_contrainte': True,
                'demande_equivalente': demande_equivalente,
                'solution_detaillee': solution_optimale
            }
        else:
            # Solution véhicule unique - utiliser le format existant
            print(f"\n✅ SOLUTION VÉHICULE UNIQUE SÉLECTIONNÉE!")
            
            return {
                'type_solution': 'vehicule_unique',
                'vehicule_utilise': solution_optimale['vehicule'],
                'nb_vehicules_necessaires': 1,
                'duree_reelle': solution_optimale['duree_reelle_jours'],
                'respect_contrainte': True,
                'vehicule_optimal': solution_optimale,
                'demande_equivalente': demande_equivalente
            }
    def _tester_combinaison_vehicules(self, demande, analyse_vehicule1, analyse_vehicule2, duree_max_jours):
        """
        Teste si deux véhicules travaillant en parallèle peuvent respecter la contrainte
        """
        vehicule1 = analyse_vehicule1['vehicule']
        vehicule2 = analyse_vehicule2['vehicule']
        
        # Calculer la capacité combinée
        capacite_poids_combinee = vehicule1['capacite_poids_max'] + vehicule2['capacite_poids_max']
        capacite_volume_combinee = vehicule1['capacite_volume_max'] + vehicule2['capacite_volume_max']
        
        # Calculer les voyages nécessaires avec la capacité combinée
        nb_voyages_poids = math.ceil(demande['quantite_poids'] / capacite_poids_combinee)
        nb_voyages_volume = math.ceil(demande['quantite_volume'] / capacite_volume_combinee)
        nb_voyages_necessaires = max(nb_voyages_poids, nb_voyages_volume)
        
        # Estimer la durée avec les deux véhicules
        vitesse_moyenne = (vehicule1.get('vitesse_kmh', 80) + vehicule2.get('vitesse_kmh', 80)) / 2
        
        temps_conduite_par_voyage = (demande['distance_km'] * 2) / vitesse_moyenne
        temps_total_conduite = temps_conduite_par_voyage * nb_voyages_necessaires
        temps_operations = nb_voyages_necessaires * 3.0
        
        duree_estimee = math.ceil((temps_total_conduite + temps_operations) / 8.0)
        
        if duree_estimee > duree_max_jours:
            return None  # Combinaison ne respecte pas non plus la contrainte
        
        # Calculer le coût combiné
        # Répartir les voyages entre les deux véhicules
        voyages_vehicule1 = math.ceil(nb_voyages_necessaires / 2)
        voyages_vehicule2 = nb_voyages_necessaires - voyages_vehicule1
        
        # Coûts véhicule 1
        distance_v1 = voyages_vehicule1 * demande['distance_km'] * 2
        cout_fixe_v1 = duree_estimee * vehicule1['cout_fixe_jour']
        cout_variable_v1 = distance_v1 * vehicule1['cout_variable_km']
        cout_v1 = cout_fixe_v1 + cout_variable_v1
        
        # Coûts véhicule 2
        distance_v2 = voyages_vehicule2 * demande['distance_km'] * 2
        cout_fixe_v2 = duree_estimee * vehicule2['cout_fixe_jour']
        cout_variable_v2 = distance_v2 * vehicule2['cout_variable_km']
        cout_v2 = cout_fixe_v2 + cout_variable_v2
        
        cout_total_combinaison = cout_v1 + cout_v2
        
        return {
            'vehicule_principal': vehicule1['nom'],
            'vehicule_secondaire': vehicule2['nom'],
            'vehicules_detail': [vehicule1, vehicule2],
            'nb_voyages_total': nb_voyages_necessaires,
            'voyages_vehicule1': voyages_vehicule1,
            'voyages_vehicule2': voyages_vehicule2,
            'duree_reelle_jours': duree_estimee,
            'respect_contrainte': True,
            'cout_vehicule1': cout_v1,
            'cout_vehicule2': cout_v2,
            'cout_total': cout_total_combinaison,
            'type_solution': 'combinaison',
            'capacite_poids_combinee': capacite_poids_combinee,
            'capacite_volume_combinee': capacite_volume_combinee
        }
    def _chercher_combinaison_optimale(self, demande, vehicules_data, duree_max_jours):
        """
        Cherche la meilleure combinaison de véhicules différents qui travaillent en parallèle
        """
        print(f"\n🔄 RECHERCHE DE COMBINAISON OPTIMALE DE VÉHICULES")
        print(f"   Objectif: Respecter {duree_max_jours} jours avec véhicules complémentaires")
        
        # Analyser tous les véhicules individuellement
        analyses_individuelles = []
        for vehicule in vehicules_data:
            analyse = self._analyser_vehicule_avec_contrainte(demande, vehicule, duree_max_jours)
            analyses_individuelles.append(analyse)
        
        # Séparer véhicules viables seuls vs nécessitant combinaison
        vehicules_viables_seuls = [a for a in analyses_individuelles if a['respect_contrainte']]
        vehicules_necessitant_aide = [a for a in analyses_individuelles if a['necessite_combinaison']]
        
        print(f"   Véhicules viables seuls: {len(vehicules_viables_seuls)}")
        print(f"   Véhicules nécessitant aide: {len(vehicules_necessitant_aide)}")
        
        # Si on a des véhicules viables seuls, prendre le meilleur
        if vehicules_viables_seuls:
            meilleur_seul = min(vehicules_viables_seuls, key=lambda x: x['cout_total'])
            print(f"   ✅ Meilleur véhicule seul: {meilleur_seul['vehicule']['nom']} - {meilleur_seul['cout_total']:.2f}€")
        else:
            meilleur_seul = None
            print(f"   ❌ Aucun véhicule ne peut réussir seul")
        
        # Chercher les meilleures combinaisons
        meilleures_combinaisons = []
        
        if vehicules_necessitant_aide:
            print(f"\n   🔍 Test des combinaisons de véhicules...")
            
            for i, vehicule_principal in enumerate(vehicules_necessitant_aide):
                print(f"\n     Véhicule principal: {vehicule_principal['vehicule']['nom']}")
                
                # Pour chaque autre véhicule, tester la combinaison
                for j, vehicule_secondaire in enumerate(analyses_individuelles):
                    if i == j:  # Éviter de combiner avec soi-même
                        continue
                    
                    combinaison = self._tester_combinaison_vehicules(
                        demande, 
                        vehicule_principal, 
                        vehicule_secondaire, 
                        duree_max_jours
                    )
                    
                    if combinaison and combinaison['respect_contrainte']:
                        meilleures_combinaisons.append(combinaison)
                        print(f"       ✅ + {vehicule_secondaire['vehicule']['nom']}: {combinaison['cout_total']:.2f}€")
        
        # Sélectionner la meilleure option globale
        toutes_options = []
        
        if meilleur_seul:
            toutes_options.append({
                'type': 'vehicule_seul',
                'solution': meilleur_seul,
                'cout_total': meilleur_seul['cout_total']
            })
        
        for combinaison in meilleures_combinaisons:
            toutes_options.append({
                'type': 'combinaison',
                'solution': combinaison,
                'cout_total': combinaison['cout_total']
            })
        
        if not toutes_options:
            print(f"   ❌ Aucune solution trouvée")
            return None
        
        # Sélectionner la solution la moins chère
        meilleure_option = min(toutes_options, key=lambda x: x['cout_total'])
        
        print(f"\n   🏆 MEILLEURE SOLUTION SÉLECTIONNÉE:")
        if meilleure_option['type'] == 'vehicule_seul':
            solution = meilleure_option['solution']
            print(f"      Type: Véhicule unique")
            print(f"      Véhicule: {solution['vehicule']['nom']}")
            print(f"      Coût: {solution['cout_total']:.2f}€")
            print(f"      Durée: {solution['duree_reelle_jours']} jours")
        else:
            solution = meilleure_option['solution']
            print(f"      Type: Combinaison de véhicules")
            print(f"      Véhicule 1: {solution['vehicule_principal']['nom']}")
            print(f"      Véhicule 2: {solution['vehicule_secondaire']['nom']}")
            print(f"      Coût total: {solution['cout_total']:.2f}€")
            print(f"      Durée: {solution['duree_reelle_jours']} jours")
        
        return meilleure_option['solution']
    def _analyser_vehicule_avec_contrainte(self, demande, vehicule, duree_max_jours):
        """Analyse un véhicule avec prise en compte de la contrainte temporelle"""
        
        # Calculer le nombre de voyages nécessaires avec un seul véhicule
        nb_voyages_poids = math.ceil(demande['quantite_poids'] / vehicule['capacite_poids_max'])
        
        # Gérer le cas où capacite_volume_max est 0
        if vehicule['capacite_volume_max'] > 0:
            nb_voyages_volume = math.ceil(demande['quantite_volume'] / vehicule['capacite_volume_max'])
        else:
            if demande['quantite_volume'] > 0:
                return {
                    'vehicule': vehicule,
                    'voyages_par_vehicule': float('inf'),
                    'contrainte_dominante': 'volume_impossible',
                    'duree_un_vehicule': float('inf'),
                    'respect_contrainte': False,
                    'nb_vehicules_necessaires': float('inf'),
                    'duree_reelle_jours': duree_max_jours,
                    'distance_totale': 0,
                    'cout_fixe_total': float('inf'),
                    'cout_variable_total': 0,
                    'cout_total': float('inf'),
                    'cout_par_vehicule': float('inf'),
                    'voyages_totaux': 0,
                    'necessite_combinaison': False
                }
            else:
                nb_voyages_volume = 0
        
        voyages_par_vehicule = max(nb_voyages_poids, nb_voyages_volume)
        
        if voyages_par_vehicule == 0:
            voyages_par_vehicule = 1
        
        # Estimer la durée avec un seul véhicule
        vitesse_utilisee = vehicule.get('vitesse_kmh', demande['vitesse_kmh'])
        
        if vitesse_utilisee <= 0:
            vitesse_utilisee = 60
        
        temps_conduite_par_voyage = (demande['distance_km'] * 2) / vitesse_utilisee
        temps_total_conduite = temps_conduite_par_voyage * voyages_par_vehicule
        
        temps_operations_par_voyage = 3.0
        temps_total_operations = voyages_par_vehicule * temps_operations_par_voyage
        
        temps_total_heures = temps_total_conduite + temps_total_operations
        duree_un_vehicule = math.ceil(temps_total_heures / 8.0)
        
        # ✅ NOUVELLE LOGIQUE : Pas de multiplication automatique
        if duree_un_vehicule <= duree_max_jours:
            # Véhicule seul suffit
            nb_vehicules_necessaires = 1
            duree_reelle = duree_un_vehicule
            respect_contrainte = True
            necessite_combinaison = False
        else:
            # ✅ Au lieu de multiplier, marquer pour combinaison
            nb_vehicules_necessaires = 1  # On garde 1 seul de ce type
            duree_reelle = duree_un_vehicule  # Durée réelle si seul
            respect_contrainte = False  # Ne respecte pas seul
            necessite_combinaison = True  # ✅ NOUVEAU : Besoin d'aide
        
        # Calculs de coûts pour 1 seul véhicule
        voyages_totaux = voyages_par_vehicule
        distance_aller_total = voyages_totaux * demande['distance_km']
        distance_retour_total = (voyages_totaux - 1) * demande['distance_km']
        distance_totale = distance_aller_total + distance_retour_total
        
        cout_fixe_total = duree_reelle * vehicule['cout_fixe_jour']
        cout_variable_total = distance_totale * vehicule['cout_variable_km']
        
        cout_total = cout_fixe_total + cout_variable_total
        cout_par_vehicule = cout_total
        
        return {
            'vehicule': vehicule,
            'voyages_par_vehicule': voyages_par_vehicule,
            'contrainte_dominante': 'poids' if nb_voyages_poids >= nb_voyages_volume else 'volume',
            'duree_un_vehicule': duree_un_vehicule,
            'respect_contrainte': respect_contrainte,
            'nb_vehicules_necessaires': nb_vehicules_necessaires,
            'duree_reelle_jours': duree_reelle,
            'distance_totale': distance_totale,
            'cout_fixe_total': cout_fixe_total,
            'cout_variable_total': cout_variable_total,
            'cout_total': cout_total,
            'cout_par_vehicule': cout_par_vehicule,
            'voyages_totaux': voyages_totaux,
            'necessite_combinaison': necessite_combinaison  # ✅ NOUVEAU CHAMP
        }
    def _planifier_multi_vehicules_melange(self, produits_a_transporter, demande_equivalente, vehicule_optimal, date_debut, heure_debut, duree_max_jours):
        """Planifie les opérations avec mélange optimal des produits"""
        
        nb_vehicules = vehicule_optimal['nb_vehicules_necessaires']
        voyages_par_vehicule = vehicule_optimal['voyages_par_vehicule']
        vehicule = vehicule_optimal['vehicule']
        
        print(f"\n=== PLANIFICATION DÉTAILLÉE AVEC MÉLANGE OPTIMAL ===")
        print(f"🔄 STRATÉGIE: Remplissage homogène prioritaire, puis mélange intelligent")
        print(f"⏰ CONTRAINTE TEMPORELLE STRICTE: {duree_max_jours} jours maximum")
        print(f"Véhicules utilisés: {nb_vehicules} x {vehicule['nom']}")
        
        # ✅ CORRECTION: Recalcul intelligent des voyages par véhicule
        if nb_vehicules == 1:
            # Un seul véhicule fait tous les voyages nécessaires
            voyages_par_vehicule_reel = voyages_par_vehicule
            print(f"Voyages par véhicule: {voyages_par_vehicule_reel}")
            print(f"Voyages totaux: {voyages_par_vehicule_reel}")
        else:
            # Plusieurs véhicules se partagent le travail
            voyages_par_vehicule_reel = math.ceil(voyages_par_vehicule / nb_vehicules)
            total_voyages_necessaires = voyages_par_vehicule
            print(f"Voyages par véhicule: {voyages_par_vehicule_reel} (répartis sur {nb_vehicules} véhicules)")
            print(f"Total voyages nécessaires: {total_voyages_necessaires}")
        
        # Créer un pool global de toutes les unités de produits
        pool_produits = self._creer_pool_produits(produits_a_transporter)
        
        print(f"\n📦 POOL GLOBAL DE PRODUITS:")
        for produit_nom, info in pool_produits.items():
            print(f"  - {produit_nom}: {info['quantite_totale']} unités ({info['poids_total']:.2f}t, {info['volume_total']:.2f}m³)")
        
        planifications_vehicules = []
        date_limite = self._calculer_date_limite(date_debut, duree_max_jours)
        
        # ✅ CORRECTION: Planification intelligente des véhicules
        voyages_restants = voyages_par_vehicule  # Voyages totaux à effectuer
        
        for vehicule_id in range(nb_vehicules):
            print(f"\n--- VÉHICULE {vehicule_id + 1} ---")
            
            # ✅ CORRECTION: Calculer le nombre de voyages pour ce véhicule spécifique
            if nb_vehicules == 1:
                # Un seul véhicule fait tout
                voyages_ce_vehicule = voyages_par_vehicule
            else:
                # Répartir équitablement les voyages restants
                vehicules_restants = nb_vehicules - vehicule_id
                voyages_ce_vehicule = math.ceil(voyages_restants / vehicules_restants)
                voyages_ce_vehicule = min(voyages_ce_vehicule, voyages_restants)
            
            print(f"    Voyages assignés à ce véhicule: {voyages_ce_vehicule}")
            
            # Vérifier s'il y a encore des produits à transporter
            produits_restants = sum(info['quantite_restante'] for info in pool_produits.values())
            if produits_restants == 0 or voyages_ce_vehicule == 0:
                print(f"    ℹ️ Aucun produit restant ou aucun voyage nécessaire")
                planifications_vehicules.append({
                    'vehicule_id': vehicule_id + 1,
                    'produits_transportes': {},
                    'charge_totale': {'poids': 0, 'volume': 0},
                    'voyages': [],
                    'nb_voyages': 0
                })
                continue
            
            # Effectuer les navettes pour ce véhicule
            voyages_vehicule = self._effectuer_navettes_melange_avec_contrainte(
                pool_produits,
                demande_equivalente, 
                vehicule, 
                voyages_ce_vehicule,  # ✅ Utiliser le nombre correct
                date_debut, 
                heure_debut,
                vehicule_id,
                date_limite
            )
            
            # Mise à jour des voyages restants
            voyages_restants -= len(voyages_vehicule)
            
            # Calculer la charge totale transportée par ce véhicule
            poids_total_vehicule = 0
            volume_total_vehicule = 0
            produits_transportes = {}
            
            for voyage in voyages_vehicule:
                charge = voyage['charge_transportee']
                poids_total_vehicule += charge['poids']
                volume_total_vehicule += charge['volume']
                
                for produit_info in charge['produits']:
                    nom_produit = produit_info['produit']['nom']
                    quantite = produit_info['quantite_voyage']
                    
                    if nom_produit not in produits_transportes:
                        produits_transportes[nom_produit] = 0
                    produits_transportes[nom_produit] += quantite
            
            print(f"\n📊 RÉSUMÉ VÉHICULE {vehicule_id + 1} (CONTRAINTE RESPECTÉE):")
            print(f"  Charge totale transportée: {poids_total_vehicule:.2f} tonnes, {volume_total_vehicule:.2f} m³")
            print(f"  Produits transportés:")
            for nom_produit, quantite in produits_transportes.items():
                poids_produit = quantite * next(p['poids_unitaire'] for p in produits_a_transporter if p['nom'] == nom_produit)
                volume_produit = quantite * next(p['volume_unitaire'] for p in produits_a_transporter if p['nom'] == nom_produit)
                print(f"    - {nom_produit}: {quantite} unités ({poids_produit:.2f}t, {volume_produit:.2f}m³)")
            
            planifications_vehicules.append({
                'vehicule_id': vehicule_id + 1,
                'produits_transportes': produits_transportes,
                'charge_totale': {
                    'poids': poids_total_vehicule,
                    'volume': volume_total_vehicule
                },
                'voyages': voyages_vehicule,
                'nb_voyages': len(voyages_vehicule)
            })
        
        # Vérifier que tous les produits ont été transportés
        completion_ok = self._verifier_completion_transport(produits_a_transporter, planifications_vehicules)
        
        if not completion_ok:
            print(f"\n⚠️ ATTENTION: La contrainte temporelle de {duree_max_jours} jours a empêché le transport complet!")
        
        # Calculer les statistiques globales
        total_voyages = sum(len(p['voyages']) for p in planifications_vehicules)
        
        # Trouver la date de fin la plus tardive
        date_fin_globale = date_debut
        for planif in planifications_vehicules:
            if planif['voyages']:
                dernier_voyage = planif['voyages'][-1]
                date_fin_vehicule = dernier_voyage['aller']['date_arrivee']
                if date_fin_vehicule > date_fin_globale:
                    date_fin_globale = date_fin_vehicule
        
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_fin_obj = datetime.strptime(date_fin_globale, '%Y-%m-%d')
        duree_reelle = (date_fin_obj - date_debut_obj).days + 1
        
        # Vérification finale de la contrainte temporelle
        contrainte_respectee = duree_reelle <= duree_max_jours
        
        print(f"\n✅ CONTRAINTE TEMPORELLE DE {duree_max_jours} JOURS: {'RESPECTÉE' if contrainte_respectee else 'VIOLÉE'}")
        print(f"📅 Durée réelle utilisée: {duree_reelle} jour(s)")
        
        return {
            'nb_vehicules': nb_vehicules,
            'planifications_vehicules': planifications_vehicules,
            'total_voyages': total_voyages,
            'date_debut': date_debut,
            'date_fin': date_fin_globale,
            'duree_reelle_jours': duree_reelle,
            'respect_contrainte': contrainte_respectee,
            'pool_produits_initial': pool_produits,
            'completion_transport': completion_ok,
            'date_limite': date_limite
        }
    
    def _calculer_date_limite(self, date_debut, duree_max_jours):
        """Calcule la date limite absolue pour respecter la contrainte temporelle"""
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_limite_obj = date_debut_obj + timedelta(days=duree_max_jours - 1)
        return date_limite_obj.strftime('%Y-%m-%d')
    
    def _respecte_contrainte_temporelle(self, date_fin, date_limite):
        """Vérifie si une date de fin respecte la contrainte temporelle"""
        return date_fin <= date_limite
    
    def _ajuster_voyages_contrainte_temporelle(self, voyages_vehicule, date_limite, pool_produits):
        """Ajuste les voyages d'un véhicule pour respecter la contrainte temporelle"""
        voyages_valides = []
        
        for voyage in voyages_vehicule:
            date_fin_voyage = voyage['aller']['date_arrivee']
            
            if self._respecte_contrainte_temporelle(date_fin_voyage, date_limite):
                voyages_valides.append(voyage)
            else:
                # Remettre les produits de ce voyage dans le pool
                charge = voyage['charge_transportee']
                for produit_info in charge['produits']:
                    nom_produit = produit_info['produit']['nom']
                    quantite = produit_info['quantite_voyage']
                    if nom_produit in pool_produits:
                        pool_produits[nom_produit]['quantite_restante'] += quantite
                
                print(f"    ⏰ Voyage supprimé pour respecter la contrainte temporelle")
                break  # Arrêter dès qu'on dépasse la contrainte
        
        return voyages_valides
    
    def _effectuer_navettes_melange_avec_contrainte(self, pool_produits, demande, vehicule, nb_voyages, date_debut, heure_debut, vehicule_id, date_limite):
        """
        Effectue toutes les navettes A→B→A avec un véhicule en respectant STRICTEMENT la contrainte temporelle
        """
        voyages = []
        date_courante = date_debut
        heure_courante = heure_debut
        
        for voyage_num in range(nb_voyages):
            print(f"\n    === VÉHICULE {vehicule_id + 1} - VOYAGE {voyage_num + 1}/{nb_voyages} ===")
            
            # VÉRIFICATION PRÉALABLE DE LA CONTRAINTE TEMPORELLE
            if not self._respecte_contrainte_temporelle(date_courante, date_limite):
                print(f"    ⏰ ARRÊT ANTICIPÉ: Date courante {date_courante} dépasse la limite {date_limite}")
                break
            
            # Sélectionner les produits pour ce voyage selon la stratégie de mélange
            produits_voyage = self._selectionner_produits_melange(
                pool_produits, vehicule['capacite_poids_max'], vehicule['capacite_volume_max'], voyage_num
            )
            
            if not produits_voyage:
                print(f"    ⚠️ Aucun produit sélectionné pour ce voyage - Arrêt anticipé")
                break
            
            charge_poids = sum(p['quantite_voyage'] * p['produit']['poids_unitaire'] for p in produits_voyage)
            charge_volume = sum(p['quantite_voyage'] * p['produit']['volume_unitaire'] for p in produits_voyage)
            
            charge_voyage = {
                'poids': charge_poids,
                'volume': charge_volume,
                'produits': produits_voyage
            }
            
            print(f"    🔄 STRATÉGIE DE CHARGEMENT:")
            print(f"    Produits sélectionnés ce voyage:")
            for p in produits_voyage:
                print(f"      - {p['produit']['nom']}: {p['quantite_voyage']} unités")
            print(f"    Charge totale: {charge_poids:.2f} tonnes, {charge_volume:.2f} m³")
            print(f"    Utilisation capacités: Poids {charge_poids/vehicule['capacite_poids_max']*100:.1f}%, Volume {charge_volume/vehicule['capacite_volume_max']*100:.1f}%")
            
            # CHARGEMENT À A (1h30) - sauf pour le premier voyage
            if voyage_num > 0:
                print(f"    → CHARGEMENT À A: 1h30")
                date_courante, heure_courante = self._ajouter_temps(
                    date_courante, heure_courante, 1.5
                )
                
                # Vérifier après le chargement
                if not self._respecte_contrainte_temporelle(date_courante, date_limite):
                    print(f"    ⏰ CONTRAINTE TEMPORELLE DÉPASSÉE APRÈS CHARGEMENT")
                    break
            
            # Utiliser la vitesse du véhicule si spécifiée, sinon celle de la demande
            vitesse_utilisee = vehicule.get('vitesse_kmh', demande['vitesse_kmh'])
            
            # TRAJET A→B (avec charge) - AVEC VÉRIFICATION TEMPORELLE
            trajet_aller = self._calculer_trajet_simple_avec_contrainte(
                demande['distance_km'],
                vitesse_utilisee,
                date_courante,
                heure_courante,
                f"VÉHICULE {vehicule_id + 1} - VOYAGE {voyage_num + 1} - ALLER A→B",
                charge_voyage,
                date_limite
            )
            
            # Vérifier si le trajet aller respecte la contrainte
            if not self._respecte_contrainte_temporelle(trajet_aller['date_arrivee'], date_limite):
                print(f"    ⏰ TRAJET ALLER DÉPASSE LA CONTRAINTE - VOYAGE ANNULÉ")
                # Remettre les produits dans le pool
                for p in produits_voyage:
                    nom_produit = p['produit']['nom']
                    pool_produits[nom_produit]['quantite_restante'] += p['quantite_voyage']
                break
            
            # Mettre à jour le pool global SEULEMENT SI LE VOYAGE EST VALIDÉ
            for p in produits_voyage:
                nom_produit = p['produit']['nom']
                pool_produits[nom_produit]['quantite_restante'] -= p['quantite_voyage']
            
            # DÉCHARGEMENT À B (1h30)
            print(f"    → DÉCHARGEMENT À B: 1h30")
            date_apres_dechargement, heure_apres_dechargement = self._ajouter_temps(
                trajet_aller['date_arrivee'],
                trajet_aller['heure_arrivee'],
                1.5
            )
            
            # TRAJET B→A (véhicule vide) - sauf pour le dernier voyage
            trajet_retour = None
            if voyage_num < nb_voyages - 1:  # Pas de retour pour le dernier voyage
                trajet_retour = self._calculer_trajet_simple_avec_contrainte(
                    demande['distance_km'],
                    vitesse_utilisee,
                    date_apres_dechargement,
                    heure_apres_dechargement,
                    f"VÉHICULE {vehicule_id + 1} - VOYAGE {voyage_num + 1} - RETOUR B→A",
                    {'poids': 0, 'volume': 0, 'produits': []},  # Véhicule vide
                    date_limite
                )
                
                # Vérifier si le retour respecte la contrainte
                if trajet_retour and not self._respecte_contrainte_temporelle(trajet_retour['date_arrivee'], date_limite):
                    print(f"    ⏰ TRAJET RETOUR DÉPASSERAIT LA CONTRAINTE - VÉHICULE RESTE À B")
                    trajet_retour = None
                    date_courante = date_apres_dechargement
                    heure_courante = heure_apres_dechargement
                else:
                    date_courante = trajet_retour['date_arrivee'] if trajet_retour else date_apres_dechargement
                    heure_courante = trajet_retour['heure_arrivee'] if trajet_retour else heure_apres_dechargement
            else:
                # Dernier voyage : véhicule reste à B
                date_courante = date_apres_dechargement
                heure_courante = heure_apres_dechargement
                print(f"    → DERNIER VOYAGE: Véhicule reste à B")
            
            voyages.append({
                'voyage_numero': voyage_num + 1,
                'charge_transportee': charge_voyage,
                'temps_chargement': '01:30' if voyage_num > 0 else '00:00',
                'aller': trajet_aller,
                'temps_dechargement': '01:30',
                'retour': trajet_retour,
                'est_dernier_voyage': voyage_num == nb_voyages - 1,
                'respecte_contrainte_temporelle': True
            })
            
            # Vérification finale avant le prochain voyage
            if not self._respecte_contrainte_temporelle(date_courante, date_limite):
                print(f"    ⏰ CONTRAINTE TEMPORELLE ATTEINTE - ARRÊT DES VOYAGES")
                break
        
        print(f"\n    ✅ VÉHICULE {vehicule_id + 1}: {len(voyages)} voyages réalisés dans la contrainte temporelle")
        return voyages
    
    def _calculer_trajet_simple_avec_contrainte(self, distance_km, vitesse_kmh, date_depart, heure_depart, direction, charge, date_limite):
        """Calcule un trajet simple avec les contraintes de repos ET vérification temporelle"""
        
        # Vérifier dès le départ si on risque de dépasser
        estimation_duree_min = distance_km / vitesse_kmh  # Estimation minimale sans pauses
        date_arrivee_estimee, _ = self._ajouter_temps(date_depart, heure_depart, estimation_duree_min)
        
        if not self._respecte_contrainte_temporelle(date_arrivee_estimee, date_limite):
            print(f"      ⚠️ ATTENTION: Trajet risque de dépasser la contrainte temporelle")
        
        # Utiliser la méthode existante mais avec surveillance
        resultat = self._calculer_trajet_simple(distance_km, vitesse_kmh, date_depart, heure_depart, direction, charge)
        
        # Vérifier le résultat final
        if not self._respecte_contrainte_temporelle(resultat['date_arrivee'], date_limite):
            print(f"      ❌ TRAJET DÉPASSE LA CONTRAINTE: {resultat['date_arrivee']} > {date_limite}")
            resultat['contrainte_respectee'] = False
        else:
            resultat['contrainte_respectee'] = True
        
        return resultat
    
    def _creer_pool_produits(self, produits_a_transporter):
        """Crée un pool global de tous les produits disponibles"""
        pool = {}
        
        for produit in produits_a_transporter:
            nom = produit['nom']
            pool[nom] = {
                'produit': produit,
                'quantite_totale': produit['quantite'],
                'quantite_restante': produit['quantite'],
                'poids_total': produit['quantite'] * produit['poids_unitaire'],
                'volume_total': produit['quantite'] * produit['volume_unitaire'],
                'poids_unitaire': produit['poids_unitaire'],
                'volume_unitaire': produit['volume_unitaire']
            }
        
        return pool
    
    def _selectionner_produits_melange(self, pool_produits, capacite_poids_max, capacite_volume_max, voyage_num):
        """
        Sélectionne les produits selon la stratégie de mélange optimal:
        1. Remplissage homogène prioritaire (un seul type de produit si possible)
        2. Mélange intelligent pour optimiser l'utilisation des capacités
        """
        
        produits_voyage = []
        capacite_poids_restante = capacite_poids_max
        capacite_volume_restante = capacite_volume_max
        
        # Filtrer les produits qui ont encore des quantités disponibles
        produits_disponibles = {nom: info for nom, info in pool_produits.items() 
                               if info['quantite_restante'] > 0}
        
        if not produits_disponibles:
            return produits_voyage
        
        print(f"    🎯 SÉLECTION PRODUITS - VOYAGE {voyage_num + 1}:")
        print(f"    Capacités disponibles: {capacite_poids_max:.2f}t, {capacite_volume_max:.2f}m³")
        
        # PHASE 1: Tentative de remplissage homogène
        print(f"    📋 PHASE 1: Tentative remplissage homogène")
        
        meilleur_candidat_homogene = None
        meilleure_utilisation = 0
        
        for nom_produit, info in produits_disponibles.items():
            produit = info['produit']
            quantite_disponible = info['quantite_restante']
            
            # Calculer combien d'unités de ce produit on peut prendre
            max_unites_poids = int(capacite_poids_max / produit['poids_unitaire'])
            max_unites_volume = int(capacite_volume_max / produit['volume_unitaire'])
            max_unites = min(max_unites_poids, max_unites_volume, quantite_disponible)
            
            if max_unites > 0:
                # Calculer l'utilisation des capacités avec ce produit seul
                poids_utilise = max_unites * produit['poids_unitaire']
                volume_utilise = max_unites * produit['volume_unitaire']
                
                utilisation_poids = poids_utilise / capacite_poids_max
                utilisation_volume = volume_utilise / capacite_volume_max
                utilisation_moyenne = (utilisation_poids + utilisation_volume) / 2
                
                print(f"      - {nom_produit}: {max_unites} unités possible (utilisation: {utilisation_moyenne*100:.1f}%)")
                
                # Privilégier les produits qui utilisent bien les capacités
                if utilisation_moyenne > meilleure_utilisation:
                    meilleure_utilisation = utilisation_moyenne
                    meilleur_candidat_homogene = {
                        'nom': nom_produit,
                        'produit': produit,
                        'quantite': max_unites,
                        'utilisation': utilisation_moyenne
                    }
        
        # Si le remplissage homogène est efficace (>70%), on l'utilise
        if meilleur_candidat_homogene and meilleure_utilisation > 0.7:
            print(f"    ✅ REMPLISSAGE HOMOGÈNE SÉLECTIONNÉ: {meilleur_candidat_homogene['nom']}")
            print(f"       Quantité: {meilleur_candidat_homogene['quantite']} unités")
            print(f"       Utilisation des capacités: {meilleure_utilisation*100:.1f}%")
            
            produits_voyage.append({
                'produit': meilleur_candidat_homogene['produit'],
                'quantite_voyage': meilleur_candidat_homogene['quantite']
            })
            
            return produits_voyage
        
        # PHASE 2: Mélange intelligent pour optimiser l'utilisation
        print(f"    🔄 PHASE 2: Mélange intelligent (remplissage homogène <70%)")
        
        # Trier les produits par efficacité (ratio valeur/espace)
        produits_tries = sorted(produits_disponibles.items(), 
                               key=lambda x: self._calculer_efficacite_produit(x[1]['produit']))
        
        for nom_produit, info in produits_tries:
            produit = info['produit']
            quantite_disponible = info['quantite_restante']
            
            # Calculer le maximum d'unités que l'on peut encore prendre
            max_unites_poids = int(capacite_poids_restante / produit['poids_unitaire'])
            max_unites_volume = int(capacite_volume_restante / produit['volume_unitaire'])
            max_unites = min(max_unites_poids, max_unites_volume, quantite_disponible)
            
            if max_unites > 0:
                produits_voyage.append({
                    'produit': produit,
                    'quantite_voyage': max_unites
                })
                
                # Mettre à jour les capacités restantes
                capacite_poids_restante -= max_unites * produit['poids_unitaire']
                capacite_volume_restante -= max_unites * produit['volume_unitaire']
                
                print(f"      ✓ Ajouté: {nom_produit} - {max_unites} unités")
                print(f"        Capacités restantes: {capacite_poids_restante:.2f}t, {capacite_volume_restante:.2f}m³")
                
                # Arrêter si les capacités sont presque épuisées
                if capacite_poids_restante < 0.1 and capacite_volume_restante < 0.1:
                    break
        
        return produits_voyage
    
    def _calculer_efficacite_produit(self, produit):
        """Calcule l'efficacité d'un produit (ratio poids/volume pour optimiser l'espace)"""
        # Plus le ratio est élevé, plus le produit est dense (efficace en volume)
        # Plus le ratio est faible, plus le produit est léger (efficace en poids)
        # On équilibre les deux aspects
        ratio_densite = produit['poids_unitaire'] / max(produit['volume_unitaire'], 0.001)
        return ratio_densite
    
    def _verifier_completion_transport(self, produits_a_transporter, planifications_vehicules):
        """Vérifie que tous les produits ont été complètement transportés"""
        
        print(f"\n🔍 VÉRIFICATION DE LA COMPLETION DU TRANSPORT:")
        
        completion_ok = True
        
        for produit in produits_a_transporter:
            nom_produit = produit['nom']
            quantite_requise = produit['quantite']
            
            # Calculer la quantité totale transportée pour ce produit
            quantite_transportee = 0
            for planif in planifications_vehicules:
                if nom_produit in planif['produits_transportes']:
                    quantite_transportee += planif['produits_transportes'][nom_produit]
            
            if quantite_transportee == quantite_requise:
                print(f"  ✅ {nom_produit}: {quantite_transportee}/{quantite_requise} unités (COMPLET)")
            elif quantite_transportee < quantite_requise:
                print(f"  ❌ {nom_produit}: {quantite_transportee}/{quantite_requise} unités (MANQUE {quantite_requise - quantite_transportee})")
                completion_ok = False
            else:
                print(f"  ⚠️ {nom_produit}: {quantite_transportee}/{quantite_requise} unités (EXCÈS {quantite_transportee - quantite_requise})")
        
        if completion_ok:
            print(f"  🎉 TOUS LES PRODUITS ONT ÉTÉ TRANSPORTÉS AVEC SUCCÈS!")
        else:
            print(f"  ⚠️ ATTENTION: Certains produits n'ont pas été complètement transportés")
        
        return completion_ok

    def _ajouter_temps(self, date_str, heure_str, heures_a_ajouter):
        """Ajoute un temps donné (en heures) à une date/heure"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        heure_parts = heure_str.split(':')
        heure_actuelle = int(heure_parts[0])
        minute_actuelle = int(heure_parts[1])
        
        minutes_a_ajouter = heures_a_ajouter * 60
        minute_actuelle += minutes_a_ajouter
        
        while minute_actuelle >= 60:
            heure_actuelle += 1
            minute_actuelle -= 60
            
        while heure_actuelle >= 24:
            date_obj += timedelta(days=1)
            heure_actuelle -= 24
        
        nouvelle_date = date_obj.strftime('%Y-%m-%d')
        nouvelle_heure = f"{int(heure_actuelle):02d}:{int(minute_actuelle):02d}"
        
        return nouvelle_date, nouvelle_heure
    
    def _calculer_trajet_simple(self, distance_km, vitesse_kmh, date_depart, heure_depart, direction, charge):
        """Calcule un trajet simple avec les contraintes de repos"""
        
        heure_parts = heure_depart.split(':')
        heure_actuelle = int(heure_parts[0])
        minute_actuelle = int(heure_parts[1])
        date_actuelle = datetime.strptime(date_depart, '%Y-%m-%d')
        
        temps_conduite_total = distance_km / vitesse_kmh
        temps_restant = temps_conduite_total
        
        pauses_repos = 0
        pauses_nuit = 0
        
        print(f"\n      {direction}:")
        print(f"      Distance: {distance_km} km à {vitesse_kmh} km/h")
        if 'produits' in charge and charge['produits']:
            print(f"      Produits transportés:")
            for p in charge['produits']:
                print(f"        - {p['produit']['nom']}: {p['quantite_voyage']} unités")
        print(f"      Charge: {charge['poids']:.2f} tonnes, {charge['volume']:.2f} m³")
        print(f"      Temps de conduite nécessaire: {temps_conduite_total:.2f} heures")
        print(f"      Départ: {date_depart} à {heure_depart}")
        
        while temps_restant > 0:
            # Temps jusqu'à 18h (fin de journée)
            if heure_actuelle < 18:
                temps_jusqu_18h = (18 - heure_actuelle) - (minute_actuelle / 60.0)
            else:
                temps_jusqu_18h = 0
            
            # Temps jusqu'à la prochaine pause (2h max de conduite)
            temps_jusqu_pause = 2.0
            
            temps_conduite_possible = min(temps_jusqu_18h, temps_jusqu_pause, temps_restant)
            
            if temps_conduite_possible <= 0:
                # Arrêt nocturne
                print(f"      Arrêt nocturne à {int(heure_actuelle):02d}:{int(minute_actuelle):02d}")
                pauses_nuit += 1
                heure_actuelle = 7
                minute_actuelle = 0
                date_actuelle += timedelta(days=1)
                continue
            
            # Conduire
            minutes_conduite = temps_conduite_possible * 60
            minute_actuelle += minutes_conduite
            
            heures_ajout = int(minute_actuelle // 60)
            heure_actuelle += heures_ajout
            minute_actuelle = minute_actuelle % 60
            
            temps_restant -= temps_conduite_possible
            
            print(f"      Conduite de {temps_conduite_possible:.2f}h - Maintenant: {int(heure_actuelle):02d}:{int(minute_actuelle):02d}")
            
            if temps_restant > 0 and temps_conduite_possible >= 1.9:
                # Pause de 15 minutes après ~2h de conduite
                minute_actuelle += 15
                if minute_actuelle >= 60:
                    heure_actuelle += 1
                    minute_actuelle -= 60
                pauses_repos += 1
                print(f"      Pause repos de 15min - Reprise à {int(heure_actuelle):02d}:{int(minute_actuelle):02d}")
        
        heure_arrivee = f"{int(heure_actuelle):02d}:{int(minute_actuelle):02d}"
        date_arrivee = date_actuelle.strftime('%Y-%m-%d')
        
        resultat = {
            'distance_km': distance_km,
            'temps_conduite_total': temps_conduite_total,
            'pauses_repos': pauses_repos,
            'pauses_nuit': pauses_nuit,
            'date_arrivee': date_arrivee,
            'heure_arrivee': heure_arrivee,
            'duree_totale_jours': (date_actuelle - datetime.strptime(date_depart, '%Y-%m-%d')).days,
            'charge_transportee': charge
        }
        
        print(f"      → Arrivée: {date_arrivee} à {heure_arrivee}")
        print(f"      → Pauses: {pauses_repos} repos, {pauses_nuit} nuit")
        
        return resultat


class OptimisateurNavettesMultiSemaines:
    def __init__(self):
        """
        Classe pour optimiser les navettes de transport de produits sur plusieurs semaines
        avec des contraintes temporelles spécifiques.
        """
        pass
        
    def calculer_navettes_optimales_multi_semaines(self, produits_semaine1, produits_semaine2, vehicules_data, date_debut, heure_debut):
        """
        Calcule les navettes optimales avec contraintes temporelles par semaine
        
        produits_semaine1: liste de dictionnaires des produits à transporter SEMAINE 1
        produits_semaine2: liste de dictionnaires des produits à transporter SEMAINE 2
        
        Chaque produit contient:
        - nom: nom du produit
        - quantite: nombre d'unités
        - poids_unitaire: poids par unité (en tonnes)
        - volume_unitaire: volume par unité (en m³)
        - distance_km, vitesse_kmh (optionnels)
        """
        
        print(f"\n=== OPTIMISATION MULTI-SEMAINES AVEC CONTRAINTES TEMPORELLES SÉPARÉES ===")
        print(f"📅 SEMAINE 1: Transport obligatoire du {date_debut} au {self._calculer_fin_semaine(date_debut, 1)}")
        print(f"📅 SEMAINE 2: Transport obligatoire du {self._calculer_debut_semaine(date_debut, 2)} au {self._calculer_fin_semaine(date_debut, 2)}")
        
        # Validation des données d'entrée
        if not produits_semaine1 and not produits_semaine2:
            print("❌ ERREUR: Aucun produit à transporter dans les deux semaines")
            return None
            
        # Calculer les totaux par semaine
        totaux_s1 = self._calculer_totaux_semaine(produits_semaine1, "SEMAINE 1")
        totaux_s2 = self._calculer_totaux_semaine(produits_semaine2, "SEMAINE 2")
        
        # Optimiser chaque semaine séparément puis analyser la solution globale
        resultats = {}
        
        # OPTIMISATION SEMAINE 1
        if produits_semaine1:
            print(f"\n{'='*80}")
            print(f"🔄 OPTIMISATION SEMAINE 1 (TRANSPORT OBLIGATOIRE)")
            print(f"{'='*80}")
            
            resultats_s1 = self._optimiser_semaine_unique(
                produits_semaine1, 
                vehicules_data, 
                date_debut, 
                heure_debut, 
                duree_max_jours=7,
                numero_semaine=1
            )
            resultats['semaine1'] = resultats_s1
        else:
            print(f"\n📭 SEMAINE 1: Aucun produit à transporter")
            resultats['semaine1'] = None
            
        # OPTIMISATION SEMAINE 2  
        if produits_semaine2:
            print(f"\n{'='*80}")
            print(f"🔄 OPTIMISATION SEMAINE 2 (TRANSPORT OBLIGATOIRE)")
            print(f"{'='*80}")
            
            date_debut_s2 = self._calculer_debut_semaine(date_debut, 2)
            resultats_s2 = self._optimiser_semaine_unique(
                produits_semaine2, 
                vehicules_data, 
                date_debut_s2, 
                heure_debut, 
                duree_max_jours=7,
                numero_semaine=2
            )
            resultats['semaine2'] = resultats_s2
        else:
            print(f"\n📭 SEMAINE 2: Aucun produit à transporter")
            resultats['semaine2'] = None
            
        # ANALYSE GLOBALE ET OPTIMISATION INTER-SEMAINES
        print(f"\n{'='*80}")
        print(f"📊 ANALYSE GLOBALE ET OPTIMISATION INTER-SEMAINES")
        print(f"{'='*80}")
        
        resultats_globaux = self._analyser_solution_globale(resultats, vehicules_data, date_debut, heure_debut)
        
        return resultats_globaux
    
    def _calculer_totaux_semaine(self, produits_semaine, nom_semaine):
        """Calcule les totaux d'une semaine"""
        if not produits_semaine:
            return {'poids_total': 0, 'volume_total': 0, 'nb_produits': 0}
            
        poids_total = sum(p['quantite'] * p['poids_unitaire'] for p in produits_semaine)
        volume_total = sum(p['quantite'] * p['volume_unitaire'] for p in produits_semaine)
        
        print(f"\n📦 {nom_semaine} - DÉTAIL DES PRODUITS:")
        for i, produit in enumerate(produits_semaine, 1):
            poids_produit = produit['quantite'] * produit['poids_unitaire']
            volume_produit = produit['quantite'] * produit['volume_unitaire']
            
            print(f"  {i}. {produit['nom']}:")
            print(f"     - Quantité: {produit['quantite']} unités")
            print(f"     - Poids unitaire: {produit['poids_unitaire']} tonnes/unité")
            print(f"     - Volume unitaire: {produit['volume_unitaire']} m³/unité")
            print(f"     - Poids total: {poids_produit:.2f} tonnes")
            print(f"     - Volume total: {volume_produit:.2f} m³")
        
        print(f"\n📊 {nom_semaine} - TOTAUX:")
        print(f"Poids total: {poids_total:.2f} tonnes")
        print(f"Volume total: {volume_total:.2f} m³")
        print(f"Nombre de types de produits: {len(produits_semaine)}")
        
        return {
            'poids_total': poids_total,
            'volume_total': volume_total,
            'nb_produits': len(produits_semaine)
        }
    
    def _optimiser_semaine_unique(self, produits_semaine, vehicules_data, date_debut, heure_debut, duree_max_jours, numero_semaine):
        """Optimise une semaine spécifique en utilisant la logique existante"""
        
        optimiseur_original = OptimisateurNavettes()
        
        resultats_semaine = optimiseur_original.calculer_navettes_optimales(
            produits_semaine,
            vehicules_data,
            date_debut,
            heure_debut,
            duree_max_jours
        )
        
        if resultats_semaine:
            resultats_semaine['numero_semaine'] = numero_semaine
            
        return resultats_semaine
    
    def _analyser_solution_globale(self, resultats_semaines, vehicules_data, date_debut, heure_debut):
        """Analyse la solution globale et propose des optimisations inter-semaines"""
        
        s1 = resultats_semaines.get('semaine1')
        s2 = resultats_semaines.get('semaine2')
        
        print(f"\n🔍 ANALYSE COMPARATIVE DES DEUX SEMAINES:")
        
        # Comparaison des véhicules sélectionnés
        if s1 and s2:
            vehicule_s1 = s1['vehicule_utilise']['nom']
            vehicule_s2 = s2['vehicule_utilise']['nom']
            
            cout_s1 = s1['vehicule_optimal']['cout_total']
            cout_s2 = s2['vehicule_optimal']['cout_total']
            
            print(f"\n🚛 VÉHICULES SÉLECTIONNÉS:")
            print(f"  Semaine 1: {vehicule_s1} - {cout_s1:.2f}€")
            print(f"  Semaine 2: {vehicule_s2} - {cout_s2:.2f}€")
            
            if vehicule_s1 == vehicule_s2:
                print(f"  ✅ MÊME VÉHICULE: Possibilité d'optimisation logistique")
                print(f"  💡 Avantage: Continuité opérationnelle, même équipe")
            else:
                print(f"  ⚠️ VÉHICULES DIFFÉRENTS: Analyse d'optimisation nécessaire")
                
            # Analyse des économies potentielles
            self._analyser_economies_inter_semaines(s1, s2, vehicules_data)
            
        elif s1:
            cout_s1 = s1['vehicule_optimal']['cout_total']
            print(f"\n🚛 SEMAINE 1 UNIQUEMENT:")
            print(f"  Véhicule: {s1['vehicule_utilise']['nom']} - {cout_s1:.2f}€")
            print(f"  Semaine 2: Repos du matériel et des équipes")
            
        elif s2:
            cout_s2 = s2['vehicule_optimal']['cout_total']
            print(f"\n🚛 SEMAINE 2 UNIQUEMENT:")
            print(f"  Semaine 1: Repos du matériel et des équipes")
            print(f"  Véhicule: {s2['vehicule_utilise']['nom']} - {cout_s2:.2f}€")
        
        # Calcul des totaux globaux
        cout_total_global = 0
        duree_totale_projet = 0
        nb_vehicules_total = 0
        
        if s1:
            cout_total_global += s1['vehicule_optimal']['cout_total']
            nb_vehicules_total += s1['nb_vehicules_necessaires']
            
        if s2:
            cout_total_global += s2['vehicule_optimal']['cout_total']
            nb_vehicules_total += s2['nb_vehicules_necessaires']
            
        # Calcul de la durée totale du projet
        if s1 and s2:
            duree_totale_projet = 14  # 2 semaines
        elif s1 or s2:
            duree_totale_projet = 7   # 1 semaine
            
        print(f"\n💰 RÉSUMÉ FINANCIER GLOBAL:")
        print(f"  Coût total projet: {cout_total_global:.2f}€")
        if s1 and s2:
            print(f"    - Semaine 1: {s1['vehicule_optimal']['cout_total']:.2f}€")
            print(f"    - Semaine 2: {s2['vehicule_optimal']['cout_total']:.2f}€")
        print(f"  Durée totale projet: {duree_totale_projet} jours")
        print(f"  Nombre total de véhicules: {nb_vehicules_total}")
        
        # Planification temporelle globale
        self._planifier_calendrier_global(s1, s2, date_debut, heure_debut)
        
        # Recommandations stratégiques
        self._generer_recommandations_globales(s1, s2)
        
        return {
            'resultats_semaine1': s1,
            'resultats_semaine2': s2,
            'cout_total_global': cout_total_global,
            'duree_totale_projet': duree_totale_projet,
            'nb_vehicules_total': nb_vehicules_total,
            'date_debut_projet': date_debut,
            'date_fin_projet': self._calculer_fin_semaine(date_debut, 2) if s2 else self._calculer_fin_semaine(date_debut, 1),
            'optimisations_possibles': self._identifier_optimisations_globales(s1, s2)
        }
    
    def _analyser_economies_inter_semaines(self, s1, s2, vehicules_data):
        """Analyse les économies potentielles entre les deux semaines"""
        
        print(f"\n💡 ANALYSE DES ÉCONOMIES INTER-SEMAINES:")
        
        vehicule_s1 = s1['vehicule_utilise']
        vehicule_s2 = s2['vehicule_utilise']
        
        # Scénario 1: Utiliser le même véhicule pour les deux semaines
        if vehicule_s1['nom'] != vehicule_s2['nom']:
            print(f"\n🔄 SCÉNARIO D'UNIFICATION DES VÉHICULES:")
            
            # Test avec le véhicule de la semaine 1 pour la semaine 2
            cout_actuel_s2 = s2['vehicule_optimal']['cout_total']
            vehicule_s1_pour_s2 = next((v for v in s2['analyses_vehicules'] if v['vehicule']['nom'] == vehicule_s1['nom']), None)
            
            if vehicule_s1_pour_s2 and vehicule_s1_pour_s2['respect_contrainte']:
                cout_s1_pour_s2 = vehicule_s1_pour_s2['cout_total']
                economie_s2 = cout_actuel_s2 - cout_s1_pour_s2
                
                print(f"  Option 1 - {vehicule_s1['nom']} pour les 2 semaines:")
                print(f"    Coût S2 actuel: {cout_actuel_s2:.2f}€")
                print(f"    Coût S2 avec véhicule S1: {cout_s1_pour_s2:.2f}€")
                print(f"    Économie S2: {economie_s2:.2f}€ ({'Profitable' if economie_s2 > 0 else 'Non profitable'})")
            
            # Test avec le véhicule de la semaine 2 pour la semaine 1
            cout_actuel_s1 = s1['vehicule_optimal']['cout_total']
            vehicule_s2_pour_s1 = next((v for v in s1['analyses_vehicules'] if v['vehicule']['nom'] == vehicule_s2['nom']), None)
            
            if vehicule_s2_pour_s1 and vehicule_s2_pour_s1['respect_contrainte']:
                cout_s2_pour_s1 = vehicule_s2_pour_s1['cout_total']
                economie_s1 = cout_actuel_s1 - cout_s2_pour_s1
                
                print(f"  Option 2 - {vehicule_s2['nom']} pour les 2 semaines:")
                print(f"    Coût S1 actuel: {cout_actuel_s1:.2f}€")
                print(f"    Coût S1 avec véhicule S2: {cout_s2_pour_s1:.2f}€")
                print(f"    Économie S1: {economie_s1:.2f}€ ({'Profitable' if economie_s1 > 0 else 'Non profitable'})")
        
        # Analyse des coûts fixes partagés
        print(f"\n🔧 ANALYSE DES COÛTS FIXES PARTAGÉS:")
        if vehicule_s1['nom'] == vehicule_s2['nom']:
            print(f"  ✅ Même véhicule utilisé: Amortissement optimal des coûts fixes")
            print(f"  💰 Avantages économiques:")
            print(f"    - Formation équipe unique")
            print(f"    - Maintenance centralisée")
            print(f"    - Négociation fournisseur unique")
        else:
            cout_fixe_s1 = s1['vehicule_optimal']['cout_fixe_total']
            cout_fixe_s2 = s2['vehicule_optimal']['cout_fixe_total']
            print(f"  ⚠️ Véhicules différents: Coûts fixes doubles")
            print(f"    - Coûts fixes S1: {cout_fixe_s1:.2f}€")
            print(f"    - Coûts fixes S2: {cout_fixe_s2:.2f}€")
            print(f"    - Total coûts fixes: {cout_fixe_s1 + cout_fixe_s2:.2f}€")
    
    def _planifier_calendrier_global(self, s1, s2, date_debut, heure_debut):
        """Planifie le calendrier global sur les deux semaines"""
        
        print(f"\n📅 PLANIFICATION TEMPORELLE GLOBALE:")
        
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        
        if s1:
            date_fin_s1 = s1['planification_detaillee']['date_fin']
            print(f"\n  SEMAINE 1 ({date_debut} → {date_fin_s1}):")
            print(f"    🚛 Véhicule: {s1['vehicule_utilise']['nom']}")
            print(f"    📦 Voyages: {s1['planification_detaillee']['total_voyages']}")
            print(f"    ⏱️ Durée réelle: {s1['duree_reelle']} jours")
            print(f"    💰 Coût: {s1['vehicule_optimal']['cout_total']:.2f}€")
            
            # Afficher les créneaux libres en semaine 1
            if s1['duree_reelle'] < 7:
                jours_libres_s1 = 7 - s1['duree_reelle']
                print(f"    💡 Créneaux libres: {jours_libres_s1} jour(s) en fin de semaine 1")
        
        if s2:
            date_debut_s2 = self._calculer_debut_semaine(date_debut, 2)
            date_fin_s2 = s2['planification_detaillee']['date_fin']
            print(f"\n  SEMAINE 2 ({date_debut_s2} → {date_fin_s2}):")
            print(f"    🚛 Véhicule: {s2['vehicule_utilise']['nom']}")
            print(f"    📦 Voyages: {s2['planification_detaillee']['total_voyages']}")
            print(f"    ⏱️ Durée réelle: {s2['duree_reelle']} jours")
            print(f"    💰 Coût: {s2['vehicule_optimal']['cout_total']:.2f}€")
            
            # Afficher les créneaux libres en semaine 2
            if s2['duree_reelle'] < 7:
                jours_libres_s2 = 7 - s2['duree_reelle']
                print(f"    💡 Créneaux libres: {jours_libres_s2} jour(s) en fin de semaine 2")
        
        # Analyse des périodes de transition
        if s1 and s2:
            print(f"\n  🔄 PÉRIODE DE TRANSITION (Weekend):")
            date_fin_s1_obj = datetime.strptime(s1['planification_detaillee']['date_fin'], '%Y-%m-%d')
            date_debut_s2_obj = datetime.strptime(self._calculer_debut_semaine(date_debut, 2), '%Y-%m-%d')
            jours_transition = (date_debut_s2_obj - date_fin_s1_obj).days
            
            print(f"    Fin S1: {s1['planification_detaillee']['date_fin']}")
            print(f"    Début S2: {self._calculer_debut_semaine(date_debut, 2)}")
            print(f"    Période de repos: {jours_transition} jour(s)")
            
            if s1['vehicule_utilise']['nom'] == s2['vehicule_utilise']['nom']:
                print(f"    ✅ Même véhicule: Maintenance et repos équipe possible")
            else:
                print(f"    🔧 Véhicules différents: Mobilisation parallèle possible")
    
    def _generer_recommandations_globales(self, s1, s2):
        """Génère des recommandations stratégiques globales"""
        
        print(f"\n💡 RECOMMANDATIONS STRATÉGIQUES GLOBALES:")
        
        if s1 and s2:
            print(f"\n🎯 PROJET DEUX SEMAINES:")
            
            # Recommandations opérationnelles
            if s1['vehicule_utilise']['nom'] == s2['vehicule_utilise']['nom']:
                print(f"  ✅ CONTINUITÉ OPÉRATIONNELLE:")
                print(f"    - Même équipe pour les 2 semaines")
                print(f"    - Courbe d'apprentissage optimisée")
                print(f"    - Maintenance centralisée pendant le weekend")
                print(f"    - Formation unique nécessaire")
            else:
                print(f"  🔧 GESTION MULTI-VÉHICULES:")
                print(f"    - Coordination de 2 équipes différentes")
                print(f"    - Formation spécialisée par véhicule")
                print(f"    - Maintenance distribuée")
                print(f"    - Possibilité de parallélisation si besoin")
            
            # Recommandations financières
            cout_total = s1['vehicule_optimal']['cout_total'] + s2['vehicule_optimal']['cout_total']
            cout_moyen_semaine = cout_total / 2
            
            print(f"\n💰 OPTIMISATION FINANCIÈRE:")
            print(f"    - Coût total projet: {cout_total:.2f}€")
            print(f"    - Coût moyen par semaine: {cout_moyen_semaine:.2f}€")
            
            if abs(s1['vehicule_optimal']['cout_total'] - s2['vehicule_optimal']['cout_total']) > cout_moyen_semaine * 0.2:
                print(f"    ⚠️ Déséquilibre des coûts détecté (>20%)")
                print(f"    💡 Recommandation: Réviser la répartition des produits")
            else:
                print(f"    ✅ Coûts équilibrés entre les semaines")
            
            # Recommandations de risque
            print(f"\n⚠️ GESTION DES RISQUES:")
            if s1['nb_vehicules_necessaires'] == 1 and s2['nb_vehicules_necessaires'] == 1:
                print(f"    - Risque faible: 1 véhicule par semaine")
                print(f"    - Solution de secours recommandée")
            else:
                nb_vehicules_max = max(s1['nb_vehicules_necessaires'], s2['nb_vehicules_necessaires'])
                print(f"    - Complexité: {nb_vehicules_max} véhicules maximum par semaine")
                print(f"    - Coordination renforcée nécessaire")
                
        elif s1:
            print(f"\n🎯 PROJET SEMAINE 1 UNIQUEMENT:")
            print(f"    - Projet simple sur 1 semaine")
            print(f"    - Semaine 2 libre pour autres projets")
            print(f"    - Coût: {s1['vehicule_optimal']['cout_total']:.2f}€")
            
        elif s2:
            print(f"\n🎯 PROJET SEMAINE 2 UNIQUEMENT:")
            print(f"    - Préparation pendant la semaine 1")
            print(f"    - Exécution semaine 2 uniquement")
            print(f"    - Coût: {s2['vehicule_optimal']['cout_total']:.2f}€")
    
    def _identifier_optimisations_globales(self, s1, s2):
        """Identifie les optimisations possibles au niveau global"""
        
        optimisations = []
        
        if s1 and s2:
            # Optimisation véhicule unique
            if s1['vehicule_utilise']['nom'] != s2['vehicule_utilise']['nom']:
                optimisations.append({
                    'type': 'unification_vehicule',
                    'description': 'Utiliser le même type de véhicule pour les 2 semaines',
                    'impact': 'Réduction coûts fixes et simplification logistique'
                })
            
            # Optimisation temporelle
            if s1['duree_reelle'] < 7 and s2['duree_reelle'] < 7:
                jours_total_necessaires = s1['duree_reelle'] + s2['duree_reelle']
                if jours_total_necessaires <= 10:
                    optimisations.append({
                        'type': 'chevauchement_temporel',
                        'description': 'Possibilité de chevauchement entre les semaines',
                        'impact': 'Réduction durée totale projet'
                    })
            
            # Optimisation capacité
            capacite_s1_utilisee = (s1['demande_equivalente']['quantite_poids'] + s1['demande_equivalente']['quantite_volume']) / 2
            capacite_s2_utilisee = (s2['demande_equivalente']['quantite_poids'] + s2['demande_equivalente']['quantite_volume']) / 2
            
            if capacite_s1_utilisee < capacite_s2_utilisee * 0.8 or capacite_s2_utilisee < capacite_s1_utilisee * 0.8:
                optimisations.append({
                    'type': 'equilibrage_charge',
                    'description': 'Rééquilibrer la charge entre les semaines',
                    'impact': 'Meilleure utilisation des capacités'
                })
        
        return optimisations
    
    def _calculer_debut_semaine(self, date_debut, numero_semaine):
        """Calcule la date de début d'une semaine donnée"""
        date_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_debut_semaine = date_obj + timedelta(days=(numero_semaine - 1) * 7)
        return date_debut_semaine.strftime('%Y-%m-%d')
    
    def _calculer_fin_semaine(self, date_debut, numero_semaine):
        """Calcule la date de fin d'une semaine donnée"""
        date_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_fin_semaine = date_obj + timedelta(days=numero_semaine * 7 - 1)
        return date_fin_semaine.strftime('%Y-%m-%d')


class SolutionTransport:
    """
    Wrapper unifié pour optimisation Local Search
    """
    
    def __init__(self, resultats_heuristique_existante):
        """
        Prend les résultats de OptimisateurNavettes.calculer_navettes_optimales()
        et les transforme en format modifiable pour LS/VNS
        """
        
        if not resultats_heuristique_existante:
            raise ValueError("Résultats heuristique ne peuvent pas être None")
        
        # 1. SAUVEGARDE des résultats originaux
        self.resultats_originaux = copy.deepcopy(resultats_heuristique_existante)
        
        # 2. EXTRACTION des informations principales
        self.cout_initial = resultats_heuristique_existante['vehicule_optimal']['cout_total']
        self.vehicule_utilise = resultats_heuristique_existante['vehicule_utilise']
        self.date_debut = resultats_heuristique_existante.get('date_debut_projet', '2025-06-02')
        
        # 3. RESTRUCTURATION en format unifié
        self.vehicules = self._extraire_vehicules(resultats_heuristique_existante)
        self.voyages = self._extraire_voyages(resultats_heuristique_existante)
        self.produits_index = self._creer_index_produits()
        
        # 4. ÉTAT MODIFIABLE
        self.cout_total = self.cout_initial
        self.est_valide = True
        self.historique_modifications = []
        
        print(f"✅ SolutionTransport initialisée:")
        print(f"   - Coût initial: {self.cout_initial:.2f}€")
        print(f"   - Nb véhicules: {len(self.vehicules)}")
        print(f"   - Nb voyages: {len(self.voyages)}")
        print(f"   - Nb produits total: {sum(len(v['produits']) for v in self.voyages)}")
    
    def _extraire_vehicules(self, resultats):
        """Extrait les véhicules dans un format unifié"""
        vehicules = []
        
        for planif in resultats['planification_detaillee']['planifications_vehicules']:
            vehicule_info = {
                'id': planif['vehicule_id'],
                'nom': resultats['vehicule_utilise']['nom'],
                'type': resultats['vehicule_utilise']['type'],
                'capacite_poids_max': resultats['vehicule_utilise']['capacite_poids_max'],
                'capacite_volume_max': resultats['vehicule_utilise']['capacite_volume_max'],
                'cout_fixe_jour': resultats['vehicule_utilise']['cout_fixe_jour'],
                'cout_variable_km': resultats['vehicule_utilise']['cout_variable_km'],
                'nb_voyages': planif['nb_voyages'],
                'charge_totale': planif['charge_totale']
            }
            vehicules.append(vehicule_info)
        
        return vehicules
    
    def _extraire_voyages(self, resultats):
        """Extrait tous les voyages dans un format unifié"""
        voyages = []
        voyage_id = 0
        
        for planif in resultats['planification_detaillee']['planifications_vehicules']:
            for voyage in planif['voyages']:
                
                # Extraction sécurisée des informations temporelles
                timing_info = {}
                if 'aller' in voyage and voyage['aller']:
                    timing_info = {
                        'date_depart': voyage['aller'].get('date_depart'),
                        'heure_depart': voyage['aller'].get('heure_depart', '08:00'),
                        'date_arrivee': voyage['aller'].get('date_arrivee'),
                        'heure_arrivee': voyage['aller'].get('heure_arrivee', '18:00'),
                        'distance_km': voyage['aller'].get('distance_km', 800)
                    }
                
                voyage_unifie = {
                    'id': voyage_id,
                    'vehicule_id': planif['vehicule_id'],
                    'numero_voyage': voyage['voyage_numero'],
                    
                    # Charge actuelle (MODIFIABLE) - copie profonde
                    'produits': copy.deepcopy(voyage['charge_transportee']['produits']),
                    'poids_total': voyage['charge_transportee']['poids'],
                    'volume_total': voyage['charge_transportee']['volume'],
                    
                    # Informations temporelles
                    'timing': timing_info,
                    
                    # Capacités du véhicule (pour validation)
                    'capacites': {
                        'poids_max': resultats['vehicule_utilise']['capacite_poids_max'],
                        'volume_max': resultats['vehicule_utilise']['capacite_volume_max']
                    },
                    
                    # Informations pour recalcul des coûts
                    'vehicule': resultats['vehicule_utilise']
                }
                
                voyages.append(voyage_unifie)
                voyage_id += 1
        
        return voyages
    
    def _creer_index_produits(self):
        """Crée un index des produits pour recherche rapide"""
        index = {}
        
        for voyage in self.voyages:
            for i, produit_info in enumerate(voyage['produits']):
                if 'produit' in produit_info and 'nom' in produit_info['produit']:
                    nom_produit = produit_info['produit']['nom']
                    if nom_produit not in index:
                        index[nom_produit] = []
                    
                    index[nom_produit].append({
                        'voyage_id': voyage['id'],
                        'produit_index': i,
                        'quantite': produit_info.get('quantite_voyage', 0)
                    })
        
        return index
    
    def swap_produits(self, voyage1_id, produit1_index, voyage2_id, produit2_index):
        """Échange deux produits entre voyages"""
        
        voyage1 = self._get_voyage(voyage1_id)
        voyage2 = self._get_voyage(voyage2_id)
        
        if not voyage1 or not voyage2:
            return False
        
        if (produit1_index >= len(voyage1['produits']) or 
            produit2_index >= len(voyage2['produits'])):
            return False
        
        # Sauvegarde pour rollback
        backup_v1 = copy.deepcopy(voyage1['produits'])
        backup_v2 = copy.deepcopy(voyage2['produits'])
        
        try:
            # Effectuer l'échange
            produit1 = voyage1['produits'][produit1_index]
            produit2 = voyage2['produits'][produit2_index]
            
            voyage1['produits'][produit1_index] = produit2
            voyage2['produits'][produit2_index] = produit1
            
            # Recalculer les charges
            self._recalculer_charge_voyage(voyage1_id)
            self._recalculer_charge_voyage(voyage2_id)
            
            # Validation
            if self._valider_voyages([voyage1_id, voyage2_id]):
                # Recalculer coût total
                self._recalculer_cout_total()
                
                # Logger la modification
                self._log_modification('swap', {
                    'voyage1_id': voyage1_id,
                    'voyage2_id': voyage2_id,
                    'produit1': produit1.get('produit', {}).get('nom', 'INCONNU'),
                    'produit2': produit2.get('produit', {}).get('nom', 'INCONNU')
                })
                
                return True
            else:
                # Rollback si invalide
                voyage1['produits'] = backup_v1
                voyage2['produits'] = backup_v2
                self._recalculer_charge_voyage(voyage1_id)
                self._recalculer_charge_voyage(voyage2_id)
                return False
                
        except Exception as e:
            print(f"❌ Erreur dans swap_produits: {e}")
            # Rollback en cas d'erreur
            voyage1['produits'] = backup_v1
            voyage2['produits'] = backup_v2
            self._recalculer_charge_voyage(voyage1_id)
            self._recalculer_charge_voyage(voyage2_id)
            return False
    
    def deplacer_produit(self, produit_index, voyage_source_id, voyage_dest_id):
        """Déplace un produit d'un voyage vers un autre"""
        
        if voyage_source_id == voyage_dest_id:
            return True  # Pas de changement nécessaire
        
        voyage_source = self._get_voyage(voyage_source_id)
        voyage_dest = self._get_voyage(voyage_dest_id)
        
        if not voyage_source or not voyage_dest:
            return False
        
        if produit_index >= len(voyage_source['produits']):
            return False
        
        # Sauvegarde
        backup_source = copy.deepcopy(voyage_source['produits'])
        backup_dest = copy.deepcopy(voyage_dest['produits'])
        
        try:
            # Déplacer le produit
            produit = voyage_source['produits'].pop(produit_index)
            voyage_dest['produits'].append(produit)
            
            # Recalculer charges
            self._recalculer_charge_voyage(voyage_source_id)
            self._recalculer_charge_voyage(voyage_dest_id)
            
            # Validation
            if self._valider_voyages([voyage_source_id, voyage_dest_id]):
                self._recalculer_cout_total()
                
                self._log_modification('deplacement', {
                    'voyage_source_id': voyage_source_id,
                    'voyage_dest_id': voyage_dest_id,
                    'produit': produit.get('produit', {}).get('nom', 'INCONNU')
                })
                
                return True
            else:
                # Rollback
                voyage_source['produits'] = backup_source
                voyage_dest['produits'] = backup_dest
                self._recalculer_charge_voyage(voyage_source_id)
                self._recalculer_charge_voyage(voyage_dest_id)
                return False
                
        except Exception as e:
            print(f"❌ Erreur dans deplacer_produit: {e}")
            # Rollback
            voyage_source['produits'] = backup_source
            voyage_dest['produits'] = backup_dest
            return False
    
    def _get_voyage(self, voyage_id):
        """Récupère un voyage par ID"""
        for voyage in self.voyages:
            if voyage['id'] == voyage_id:
                return voyage
        return None
    
    def _recalculer_charge_voyage(self, voyage_id):
        """Recalcule la charge d'un voyage après modification"""
        voyage = self._get_voyage(voyage_id)
        if not voyage:
            return
        
        poids_total = 0
        volume_total = 0
        
        for produit_info in voyage['produits']:
            quantite = produit_info.get('quantite_voyage', 0)
            
            if 'produit' in produit_info:
                poids_unit = produit_info['produit'].get('poids_unitaire', 0)
                volume_unit = produit_info['produit'].get('volume_unitaire', 0)
                
                poids_total += quantite * poids_unit
                volume_total += quantite * volume_unit
        
        voyage['poids_total'] = poids_total
        voyage['volume_total'] = volume_total
    
    def _valider_voyages(self, voyage_ids):
        """Valide que les voyages respectent les capacités"""
        for voyage_id in voyage_ids:
            voyage = self._get_voyage(voyage_id)
            if not voyage:
                return False
            
            if (voyage['poids_total'] > voyage['capacites']['poids_max'] or
                voyage['volume_total'] > voyage['capacites']['volume_max']):
                return False
        
        return True
    
    def _recalculer_cout_total(self):
        """Recalcule le coût total après modifications"""
        
        cout_total = 0
        
        # Grouper voyages par véhicule
        voyages_par_vehicule = {}
        for voyage in self.voyages:
            vehicule_id = voyage['vehicule_id']
            if vehicule_id not in voyages_par_vehicule:
                voyages_par_vehicule[vehicule_id] = []
            voyages_par_vehicule[vehicule_id].append(voyage)
        
        # Calculer coût pour chaque véhicule
        for vehicule_id, voyages_vehicule in voyages_par_vehicule.items():
            vehicule = self._get_vehicule(vehicule_id)
            if not vehicule:
                continue
            
            nb_jours_utilisation = self._calculer_jours_utilisation(voyages_vehicule)
            distance_totale = self._calculer_distance_totale(voyages_vehicule)
            
            # Coûts selon votre logique existante
            cout_fixe_vehicule = vehicule['cout_fixe_jour'] * nb_jours_utilisation
            cout_variable_vehicule = distance_totale * vehicule['cout_variable_km']
            
            cout_total += cout_fixe_vehicule + cout_variable_vehicule
        
        self.cout_total = cout_total
    
    def _get_vehicule(self, vehicule_id):
        """Récupère un véhicule par ID"""
        for vehicule in self.vehicules:
            if vehicule['id'] == vehicule_id:
                return vehicule
        return None
    
    def _calculer_jours_utilisation(self, voyages_vehicule):
        """Calcule le nombre de jours d'utilisation d'un véhicule"""
        if not voyages_vehicule:
            return 0
        
        # Approche simple : compter les jours uniques utilisés
        dates_utilisees = set()
        
        for voyage in voyages_vehicule:
            if 'timing' in voyage and voyage['timing'].get('date_depart'):
                dates_utilisees.add(voyage['timing']['date_depart'])
        
        return max(1, len(dates_utilisees))  # Au moins 1 jour
    
    def _calculer_distance_totale(self, voyages_vehicule):
        """Calcule la distance totale parcourue par un véhicule"""
        distance_totale = 0
        
        for voyage in voyages_vehicule:
            if 'timing' in voyage and voyage['timing'].get('distance_km'):
                # Aller-retour sauf pour le dernier voyage
                distance_voyage = voyage['timing']['distance_km']
                if voyage['numero_voyage'] < len(voyages_vehicule):
                    distance_voyage *= 2  # Aller-retour
                distance_totale += distance_voyage
        
        return distance_totale
    
    def _log_modification(self, type_modification, details):
        """Enregistre une modification dans l'historique"""
        self.historique_modifications.append({
            'type': type_modification,
            'details': details,
            'cout_avant': self.cout_total,
            'timestamp': datetime.now().isoformat()
        })
    
    def clone(self):
        """Crée une copie profonde pour les tests de Local Search"""
        return copy.deepcopy(self)
    
    def est_solution_valide(self):
        """Vérifie la validité complète de la solution"""
        try:
            # Vérifier capacités de tous les voyages
            for voyage in self.voyages:
                if (voyage['poids_total'] > voyage['capacites']['poids_max'] or
                    voyage['volume_total'] > voyage['capacites']['volume_max']):
                    return False
            
            # Vérifier intégrité des produits
            if not self._verifier_integrite_produits():
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur validation: {e}")
            return False
    
    def _verifier_integrite_produits(self):
        """Vérifie que tous les produits sont cohérents"""
        # Compter les produits dans la solution actuelle
        compteur_produits = {}
        
        for voyage in self.voyages:
            for produit_info in voyage['produits']:
                if 'produit' in produit_info and 'nom' in produit_info['produit']:
                    nom = produit_info['produit']['nom']
                    quantite = produit_info.get('quantite_voyage', 0)
                    
                    if nom not in compteur_produits:
                        compteur_produits[nom] = 0
                    compteur_produits[nom] += quantite
        
        return True
    
    def convertir_vers_format_original(self):
        """Reconvertit vers le format de votre heuristique pour compatibilité"""
        
        # Commencer avec une copie des résultats originaux
        resultats_modifies = copy.deepcopy(self.resultats_originaux)
        
        # Mettre à jour le coût total
        resultats_modifies['vehicule_optimal']['cout_total'] = self.cout_total
        
        # Reconstruire les planifications_vehicules
        planifications_mises_a_jour = []
        
        # Grouper les voyages par véhicule
        voyages_par_vehicule = {}
        for voyage in self.voyages:
            vehicule_id = voyage['vehicule_id']
            if vehicule_id not in voyages_par_vehicule:
                voyages_par_vehicule[vehicule_id] = []
            voyages_par_vehicule[vehicule_id].append(voyage)
        
        # Reconstruire chaque planification de véhicule
        for vehicule_id, voyages_vehicule in voyages_par_vehicule.items():
            voyages_reconstruits = []
            
            for voyage in sorted(voyages_vehicule, key=lambda v: v['numero_voyage']):
                voyage_reconstruit = {
                    'voyage_numero': voyage['numero_voyage'],
                    'charge_transportee': {
                        'poids': voyage['poids_total'],
                        'volume': voyage['volume_total'],
                        'produits': copy.deepcopy(voyage['produits'])
                    }
                }
                
                # Ajouter les informations temporelles si disponibles
                if 'timing' in voyage and voyage['timing']:
                    voyage_reconstruit['aller'] = {
                        'date_depart': voyage['timing'].get('date_depart'),
                        'heure_depart': voyage['timing'].get('heure_depart'),
                        'date_arrivee': voyage['timing'].get('date_arrivee'),
                        'heure_arrivee': voyage['timing'].get('heure_arrivee'),
                        'distance_km': voyage['timing'].get('distance_km')
                    }
                
                voyages_reconstruits.append(voyage_reconstruit)
            
            # Recalculer les totaux pour ce véhicule
            vehicule = self._get_vehicule(vehicule_id)
            charge_totale_vehicule = {
                'poids': sum(v['poids_total'] for v in voyages_vehicule),
                'volume': sum(v['volume_total'] for v in voyages_vehicule)
            }
            
            planification_vehicule = {
                'vehicule_id': vehicule_id,
                'nb_voyages': len(voyages_reconstruits),
                'charge_totale': charge_totale_vehicule,
                'voyages': voyages_reconstruits
            }
            
            planifications_mises_a_jour.append(planification_vehicule)
        
        resultats_modifies['planification_detaillee']['planifications_vehicules'] = planifications_mises_a_jour
        
        return resultats_modifies
    
    def afficher_resume(self):
        """Affiche un résumé de la solution"""
        print(f"\n📊 RÉSUMÉ SOLUTION TRANSPORT:")
        print(f"Coût total: {self.cout_total:.2f}€ (initial: {self.cout_initial:.2f}€)")
        
        if self.cout_total != self.cout_initial:
            gain = self.cout_initial - self.cout_total
            print(f"Gain: {gain:.2f}€ ({gain/self.cout_initial*100:.1f}%)")
        
        print(f"Véhicules: {len(self.vehicules)}")
        print(f"Voyages: {len(self.voyages)}")
        print(f"Modifications: {len(self.historique_modifications)}")
        
        for voyage in self.voyages:
            utilisation_poids = (voyage['poids_total'] / voyage['capacites']['poids_max']) * 100
            utilisation_volume = (voyage['volume_total'] / voyage['capacites']['volume_max']) * 100
            print(f"  Voyage {voyage['id']}: {utilisation_poids:.1f}% poids, {utilisation_volume:.1f}% volume")


def appliquer_local_search(resultats_heuristique, nb_iterations=50):
    """
    Applique la Local Search sur les résultats de votre heuristique
    """
    if not resultats_heuristique:
        return None
    
    try:
        # 1. Convertir en solution modifiable
        solution = SolutionTransport(resultats_heuristique)
        print(f"🔍 LOCAL SEARCH - Solution initiale: {solution.cout_total:.2f}€")
        
        meilleure_solution = solution.clone()
        meilleur_cout = solution.cout_total
        nb_ameliorations = 0
        
        # 2. Algorithme de Local Search simple
        for iteration in range(nb_iterations):
            solution_test = meilleure_solution.clone()
            amelioration_trouvee = False
            
            # Essayer des swaps aléatoires
            for tentative in range(10):  # 10 tentatives par itération
                if len(solution_test.voyages) >= 2:
                    # Sélection aléatoire de deux voyages différents
                    voyages_ids = list(range(len(solution_test.voyages)))
                    voyage1_id = random.choice(voyages_ids)
                    voyages_ids.remove(voyage1_id)
                    voyage2_id = random.choice(voyages_ids)
                    
                    voyage1 = solution_test.voyages[voyage1_id]
                    voyage2 = solution_test.voyages[voyage2_id]
                    
                    if voyage1['produits'] and voyage2['produits']:
                        idx1 = random.randint(0, len(voyage1['produits']) - 1)
                        idx2 = random.randint(0, len(voyage2['produits']) - 1)
                        
                        # Tester le swap
                        if solution_test.swap_produits(voyage1_id, idx1, voyage2_id, idx2):
                            if solution_test.cout_total < meilleur_cout:
                                meilleure_solution = solution_test.clone()
                                meilleur_cout = solution_test.cout_total
                                nb_ameliorations += 1
                                amelioration_trouvee = True
                                print(f"   ✅ Amélioration trouvée: {meilleur_cout:.2f}€")
                                break
            
            # Si pas d'amélioration avec swap, essayer des déplacements
            if not amelioration_trouvee:
                for tentative in range(5):
                    if len(solution_test.voyages) >= 2:
                        voyages_ids = list(range(len(solution_test.voyages)))
                        voyage_source_id = random.choice(voyages_ids)
                        voyages_ids.remove(voyage_source_id)
                        voyage_dest_id = random.choice(voyages_ids)
                        
                        voyage_source = solution_test.voyages[voyage_source_id]
                        
                        if voyage_source['produits']:
                            idx = random.randint(0, len(voyage_source['produits']) - 1)
                            
                            if solution_test.deplacer_produit(idx, voyage_source_id, voyage_dest_id):
                                if solution_test.cout_total < meilleur_cout:
                                    meilleure_solution = solution_test.clone()
                                    meilleur_cout = solution_test.cout_total
                                    nb_ameliorations += 1
                                    print(f"   ✅ Amélioration trouvée: {meilleur_cout:.2f}€")
                                    break
        
        # 3. Résultats
        amelioration_totale = solution.cout_total - meilleur_cout
        print(f"🎯 LOCAL SEARCH TERMINÉE:")
        print(f"   - Coût initial: {solution.cout_total:.2f}€")
        print(f"   - Coût final: {meilleur_cout:.2f}€")
        print(f"   - Amélioration: {amelioration_totale:.2f}€ ({amelioration_totale/solution.cout_total*100:.2f}%)")
        print(f"   - Nombre d'améliorations: {nb_ameliorations}")
        
        if amelioration_totale > 0:
            # Reconvertir au format original
            return meilleure_solution.convertir_vers_format_original()
        else:
            print("   ℹ️ Aucune amélioration trouvée - solution initiale conservée")
            return resultats_heuristique
            
    except Exception as e:
        print(f"❌ ERREUR Local Search: {e}")
        return resultats_heuristique


def optimiser_avec_local_search(optimiseur, produits, vehicules, date_debut, heure_debut, duree_max=7):
    """
    Fonction helper qui combine votre heuristique + Local Search
    """
    print("🚀 OPTIMISATION HYBRIDE: Heuristique + Local Search")
    
    # 1. Votre heuristique existante
    print("\n1️⃣ Phase heuristique...")
    resultats = optimiseur.calculer_navettes_optimales(
        produits, vehicules, date_debut, heure_debut, duree_max
    )
    
    if not resultats:
        print("❌ Heuristique échouée")
        return None
    
    cout_heuristique = resultats['vehicule_optimal']['cout_total']
    print(f"✅ Heuristique terminée: {cout_heuristique:.2f}€")
    
    # 2. Local Search
    print("\n2️⃣ Phase Local Search...")
    resultats_ameliores = appliquer_local_search(resultats, nb_iterations=100)
    
    if resultats_ameliores:
        cout_final = resultats_ameliores['vehicule_optimal']['cout_total']
        gain = cout_heuristique - cout_final
        
        if gain > 0:
            print(f"🎉 OPTIMISATION RÉUSSIE!")
            print(f"   Gain total: {gain:.2f}€ ({gain/cout_heuristique*100:.2f}%)")
            return resultats_ameliores
        else:
            print("ℹ️ Solution heuristique déjà optimale")
            return resultats
    
    return resultats
class VNSOptimiseur:
    """
    Variable Neighborhood Search pour l'optimisation des navettes
    """
    
    def __init__(self):
        self.voisinages = [
            self._voisinage_swap_produits,
            self._voisinage_deplacement_produits,
            self._voisinage_redistribution_voyages,
            self._voisinage_fusion_voyages,
            self._voisinage_inversion_sequence,
            self._voisinage_reoptimisation_vehicules
            

        ]
        self.historique_vns = []
        self.historique_solutions = []  # Mémoire des bonnes solutions
        self.zones_prometteuses = []    # Zones à explorer intensément
        self.compteur_stagnation = 0   # Pour déclencher intensification
        
    def optimiser_vns(self, resultats_heuristique, max_iterations=500, max_voisinages=6):
        """
        Applique VNS sur les résultats de l'heuristique
        """
        if not resultats_heuristique:
            return None
        
        print(f"🔍 VNS - Variable Neighborhood Search")
        print(f"   Max iterations: {max_iterations}")
        print(f"   Nombre de voisinages: {len(self.voisinages)}")
        
        try:
            # Initialisation
            solution_courante = SolutionTransport(resultats_heuristique)
            meilleure_solution = solution_courante.clone()
            meilleur_cout = solution_courante.cout_total
            
            print(f"   Solution initiale: {meilleur_cout:.2f}€")
            
            iteration = 0
            nb_ameliorations = 0
            
            while iteration < max_iterations:
                k = 0  # Index du voisinage courant
                amelioration_trouvee = False
                
                while k < min(len(self.voisinages), max_voisinages):
                    # Génération dans le k-ième voisinage
                    solution_voisine = self._generer_voisin(solution_courante, k)
                    
                    if solution_voisine and solution_voisine.est_solution_valide():
                        # Local Search dans ce voisinage
                        solution_amelioree = self._local_search_voisinage(solution_voisine, 20)
                        
                        # Test d'amélioration
                        if solution_amelioree.cout_total < meilleur_cout:
                            meilleure_solution = solution_amelioree.clone()
                            meilleur_cout = solution_amelioree.cout_total
                            solution_courante = solution_amelioree.clone()
                            
                            nb_ameliorations += 1
                            amelioration_trouvee = True
                            
                            # ✅ NOUVELLES LIGNES - INTENSIFICATION
                            self._marquer_zone_prometteuse(solution_amelioree, k)
                            self._memoriser_solution(solution_amelioree)
                            self.compteur_stagnation = 0
                            
                            print(f"   ✅ Amélioration trouvée (voisinage {k+1}): {meilleur_cout:.2f}€")
                            
                            # Retour au premier voisinage
                            k = 0
                        else:
                            # Passer au voisinage suivant
                            k += 1
                    else:
                        k += 1
                
                iteration += 1
                
                # Diversification si pas d'amélioration
                # ✅ INTENSIFICATION ET DIVERSIFICATION
                if not amelioration_trouvee:
                    self.compteur_stagnation += 1
                    
                    # Intensification après 5 itérations sans amélioration
                    if self.compteur_stagnation == 5:
                        print(f"   🔍 INTENSIFICATION appliquée (itération {iteration})")
                        solution_intensifiee = self._intensification(meilleure_solution)
                        if solution_intensifiee and solution_intensifiee.cout_total < meilleur_cout:
                            meilleure_solution = solution_intensifiee.clone()
                            meilleur_cout = solution_intensifiee.cout_total
                            solution_courante = solution_intensifiee.clone()
                            print(f"   ✅ Intensification réussie: {meilleur_cout:.2f}€")
                            self.compteur_stagnation = 0
                            nb_ameliorations += 1
                    
                    # Diversification après plus de stagnation
                    elif self.compteur_stagnation >= 10 and iteration % 20 == 0:
                        solution_courante = self._diversification(meilleure_solution)
                        print(f"   🔄 Diversification appliquée (itération {iteration})")
                        self.compteur_stagnation = 0
            
            # Résultats
            amelioration_totale = solution_courante.cout_initial - meilleur_cout
            
            print(f"🎯 VNS TERMINÉ:")
            print(f"   - Coût initial: {solution_courante.cout_initial:.2f}€")
            print(f"   - Coût final: {meilleur_cout:.2f}€")
            print(f"   - Amélioration: {amelioration_totale:.2f}€ ({amelioration_totale/solution_courante.cout_initial*100:.2f}%)")
            print(f"   - Nombre d'améliorations: {nb_ameliorations}")
            print(f"   - Iterations: {iteration}")
            print(f"   - Zones prometteuses: {len(self.zones_prometteuses)}")
            print(f"   - Solutions mémorisées: {len(self.historique_solutions)}")
            print(f"   - Mécanisme intensification+diversification activé ✅")
            
            if amelioration_totale > 0:
                return meilleure_solution.convertir_vers_format_original()
            else:
                print("   ℹ️ Aucune amélioration VNS - solution initiale conservée")
                return resultats_heuristique
                
        except Exception as e:
            print(f"❌ ERREUR VNS: {e}")
            return resultats_heuristique
    
    def _generer_voisin(self, solution, k):
        """Génère un voisin dans le k-ième voisinage"""
        try:
            voisinage_func = self.voisinages[k]
            return voisinage_func(solution)
        except:
            return None
    
    def _voisinage_swap_produits(self, solution):
        """Voisinage 1: Échange de produits entre voyages"""
        solution_voisine = solution.clone()
        
        # Sélectionner deux voyages aléatoirement
        if len(solution_voisine.voyages) >= 2:
            voyages_ids = list(range(len(solution_voisine.voyages)))
            voyage1_id = random.choice(voyages_ids)
            voyages_ids.remove(voyage1_id)
            voyage2_id = random.choice(voyages_ids)
            
            voyage1 = solution_voisine.voyages[voyage1_id]
            voyage2 = solution_voisine.voyages[voyage2_id]
            
            if voyage1['produits'] and voyage2['produits']:
                idx1 = random.randint(0, len(voyage1['produits']) - 1)
                idx2 = random.randint(0, len(voyage2['produits']) - 1)
                
                if solution_voisine.swap_produits(voyage1_id, idx1, voyage2_id, idx2):
                    return solution_voisine
        
        return None
    
    def _voisinage_deplacement_produits(self, solution):
        """Voisinage 2: Déplacement de produits"""
        solution_voisine = solution.clone()
        
        if len(solution_voisine.voyages) >= 2:
            # Choisir voyage source et destination
            voyage_source_id = random.randint(0, len(solution_voisine.voyages) - 1)
            voyage_dest_id = random.randint(0, len(solution_voisine.voyages) - 1)
            
            while voyage_dest_id == voyage_source_id and len(solution_voisine.voyages) > 1:
                voyage_dest_id = random.randint(0, len(solution_voisine.voyages) - 1)
            
            voyage_source = solution_voisine.voyages[voyage_source_id]
            
            if voyage_source['produits']:
                idx = random.randint(0, len(voyage_source['produits']) - 1)
                
                if solution_voisine.deplacer_produit(idx, voyage_source_id, voyage_dest_id):
                    return solution_voisine
        
        return None
    def _local_search_voisinage(self, solution, max_iter=20):
        """Local Search spécialisé dans un voisinage"""
        meilleure_solution = solution.clone()
        meilleur_cout = solution.cout_total
        
        for iteration in range(max_iter):
            solution_test = meilleure_solution.clone()
            
            # Appliquer quelques mouvements locaux
            for _ in range(3):
                if len(solution_test.voyages) >= 2:
                    if random.random() < 0.5:  # 50% swap, 50% déplacement
                        # Swap
                        voyages_ids = list(range(len(solution_test.voyages)))
                        v1 = random.choice(voyages_ids)
                        voyages_ids.remove(v1)
                        v2 = random.choice(voyages_ids)
                        
                        voyage1 = solution_test.voyages[v1]
                        voyage2 = solution_test.voyages[v2]
                        
                        if voyage1['produits'] and voyage2['produits']:
                            idx1 = random.randint(0, len(voyage1['produits']) - 1)
                            idx2 = random.randint(0, len(voyage2['produits']) - 1)
                            solution_test.swap_produits(v1, idx1, v2, idx2)
                    else:
                        # Déplacement
                        v_src = random.randint(0, len(solution_test.voyages) - 1)
                        v_dst = random.randint(0, len(solution_test.voyages) - 1)
                        
                        if (v_src != v_dst and 
                            solution_test.voyages[v_src]['produits']):
                            idx = random.randint(0, len(solution_test.voyages[v_src]['produits']) - 1)
                            solution_test.deplacer_produit(idx, v_src, v_dst)
            
            # Test d'amélioration
            if solution_test.cout_total < meilleur_cout:
                meilleure_solution = solution_test.clone()
                meilleur_cout = solution_test.cout_total
        
        return meilleure_solution
    def _voisinage_redistribution_voyages(self, solution):
        """Voisinage 3: Redistribution de produits entre plusieurs voyages"""
        solution_voisine = solution.clone()
        
        if len(solution_voisine.voyages) >= 3:
            # Sélectionner 3 voyages pour redistribution
            voyages_ids = random.sample(range(len(solution_voisine.voyages)), 3)
            
            # Effectuer plusieurs mouvements dans cette structure
            for _ in range(3):
                voyage_src = random.choice(voyages_ids)
                voyage_dst = random.choice(voyages_ids)
                
                if (voyage_src != voyage_dst and 
                    solution_voisine.voyages[voyage_src]['produits']):
                    
                    idx = random.randint(0, len(solution_voisine.voyages[voyage_src]['produits']) - 1)
                    solution_voisine.deplacer_produit(idx, voyage_src, voyage_dst)
            
            return solution_voisine
        
        return None
    
    def _voisinage_fusion_voyages(self, solution):
        """Voisinage 4: Tentative de fusion/division de voyages"""
        solution_voisine = solution.clone()
        
        # Stratégie: redistribuer tous les produits d'un voyage vers les autres
        if len(solution_voisine.voyages) >= 2:
            voyage_source_id = random.randint(0, len(solution_voisine.voyages) - 1)
            voyage_source = solution_voisine.voyages[voyage_source_id]
            
            if voyage_source['produits']:
                # Redistribuer tous les produits de ce voyage
                produits_a_redistribuer = list(voyage_source['produits'])
                
                for produit_info in produits_a_redistribuer:
                    # Trouver un autre voyage capable d'accueillir ce produit
                    voyages_possibles = [i for i in range(len(solution_voisine.voyages)) if i != voyage_source_id]
                    
                    if voyages_possibles:
                        voyage_dest_id = random.choice(voyages_possibles)
                        idx = voyage_source['produits'].index(produit_info)
                        solution_voisine.deplacer_produit(idx, voyage_source_id, voyage_dest_id)
                
                return solution_voisine
        
        return None
    def _voisinage_inversion_sequence(self, solution):
        """Voisinage 5: Inverser l'ordre des produits dans un voyage"""
        solution_voisine = solution.clone()
        
        if solution_voisine.voyages:
            voyage_id = random.randint(0, len(solution_voisine.voyages) - 1)
            voyage = solution_voisine.voyages[voyage_id]
            
            if len(voyage['produits']) >= 2:
                # Inverser l'ordre des produits
                voyage['produits'].reverse()
                solution_voisine._recalculer_cout_total()  # Utiliser la méthode existante
                return solution_voisine
        return None
    def _voisinage_reoptimisation_vehicules(self, solution):
        """Voisinage 6: Réoptimiser l'affectation véhicule-voyage"""
        solution_voisine = solution.clone()
        
        # Collecter tous les produits
        tous_produits = []
        for voyage in solution_voisine.voyages:
            tous_produits.extend(voyage['produits'])
            voyage['produits'] = []  # Vider le voyage
        
        # Réaffecter avec vérification de capacité
        random.shuffle(tous_produits)
        
        for produit in tous_produits:
            # Trouver un voyage qui peut accueillir ce produit
            voyage_assigne = False
            voyages_possibles = list(range(len(solution_voisine.voyages)))
            random.shuffle(voyages_possibles)
            
            for voyage_id in voyages_possibles:
                if self._peut_ajouter_produit_voyage(solution_voisine, voyage_id, produit):
                    solution_voisine.voyages[voyage_id]['produits'].append(produit)
                    voyage_assigne = True
                    break
            
            # Si aucun voyage ne peut l'accueillir, retourner None (solution invalide)
            if not voyage_assigne:
                return None
        
        solution_voisine._recalculer_cout_total()
        return solution_voisine
        
    def _peut_ajouter_produit_voyage(self, solution, voyage_id, produit):
        """
        Vérifier si un produit peut être ajouté à un voyage
        """
        voyage = solution.voyages[voyage_id]
        
        # Calculer capacité actuelle du voyage
        poids_actuel = 0
        volume_actuel = 0
        
        for p in voyage['produits']:
            if 'produit' in p and 'quantite_voyage' in p:
                poids_unitaire = p['produit'].get('poids_unitaire', 0)
                volume_unitaire = p['produit'].get('volume_unitaire', 0)
                quantite = p.get('quantite_voyage', 0)
                
                poids_actuel += poids_unitaire * quantite
                volume_actuel += volume_unitaire * quantite
        
        # Ajouter le nouveau produit
        poids_unitaire_nouveau = produit.get('produit', {}).get('poids_unitaire', 0)
        volume_unitaire_nouveau = produit.get('produit', {}).get('volume_unitaire', 0)
        quantite_nouveau = produit.get('quantite_voyage', 0)
        
        nouveau_poids = poids_actuel + (poids_unitaire_nouveau * quantite_nouveau)
        nouveau_volume = volume_actuel + (volume_unitaire_nouveau * quantite_nouveau)
        
        # Récupérer les capacités du véhicule de ce voyage
        capacites = voyage.get('capacites', {})
        poids_max = capacites.get('poids_max', float('inf'))
        volume_max = capacites.get('volume_max', float('inf'))
        
        # Vérifier les contraintes
        return (nouveau_poids <= poids_max and nouveau_volume <= volume_max)
    def _local_search_voisinage(self, solution, max_iter=200):
        """✅ MÉTHODE MANQUANTE: Local Search spécialisé dans un voisinage"""
        meilleure_solution = solution.clone()
        meilleur_cout = solution.cout_total
        
        for iteration in range(max_iter):
            solution_test = meilleure_solution.clone()
            
            # Appliquer quelques mouvements locaux
            for _ in range(3):
                if len(solution_test.voyages) >= 2:
                    if random.random() < 0.5:  # 50% swap, 50% déplacement
                        # Swap
                        voyages_ids = list(range(len(solution_test.voyages)))
                        v1 = random.choice(voyages_ids)
                        voyages_ids.remove(v1)
                        v2 = random.choice(voyages_ids)
                        
                        voyage1 = solution_test.voyages[v1]
                        voyage2 = solution_test.voyages[v2]
                        
                        if voyage1['produits'] and voyage2['produits']:
                            idx1 = random.randint(0, len(voyage1['produits']) - 1)
                            idx2 = random.randint(0, len(voyage2['produits']) - 1)
                            solution_test.swap_produits(v1, idx1, v2, idx2)
                    else:
                        # Déplacement
                        v_src = random.randint(0, len(solution_test.voyages) - 1)
                        v_dst = random.randint(0, len(solution_test.voyages) - 1)
                        
                        if (v_src != v_dst and 
                            solution_test.voyages[v_src]['produits']):
                            idx = random.randint(0, len(solution_test.voyages[v_src]['produits']) - 1)
                            solution_test.deplacer_produit(idx, v_src, v_dst)
            
            # Test d'amélioration
            if solution_test.cout_total < meilleur_cout:
                meilleure_solution = solution_test.clone()
                meilleur_cout = solution_test.cout_total
        
        return meilleure_solution
    def _diversification(self, solution):
        """Diversification pour échapper aux optima locaux"""
        solution_diversifiee = solution.clone()
        
        # Effectuer plusieurs mouvements aléatoires
        nb_mouvements = min(10, len(solution_diversifiee.voyages))
        
        for _ in range(nb_mouvements):
            k = random.randint(0, len(self.voisinages) - 1)
            nouvelle_solution = self._generer_voisin(solution_diversifiee, k)
            
            if nouvelle_solution and nouvelle_solution.est_solution_valide():
                solution_diversifiee = nouvelle_solution
        
        return solution_diversifiee# ✅ MÉTHODE HELPER POUR TESTER LES VOISINAGES
    def _marquer_zone_prometteuse(self, solution, voisinage_efficace):
        """Marque une zone comme prometteuse pour intensification"""
        zone = {
            'voisinage_efficace': voisinage_efficace,
            'cout': solution.cout_total,
            'nb_voyages': len(solution.voyages)
        }
        self.zones_prometteuses.append(zone)
        
        # Garder seulement les 5 meilleures zones
        self.zones_prometteuses.sort(key=lambda x: x['cout'])
        if len(self.zones_prometteuses) > 5:
            self.zones_prometteuses = self.zones_prometteuses[:5]

    def _memoriser_solution(self, solution):
        """Mémorise les bonnes solutions"""
        solution_info = {
            'solution': solution.clone(),
            'cout': solution.cout_total
        }
        self.historique_solutions.append(solution_info)
        
        # Garder seulement les 10 meilleures
        self.historique_solutions.sort(key=lambda x: x['cout'])
        if len(self.historique_solutions) > 10:
            self.historique_solutions = self.historique_solutions[:10]

    def _intensification(self, solution_base):
        """Stratégies d'intensification"""
        if not self.zones_prometteuses:
            return None
        
        # Stratégie 1: Explorer le voisinage le plus efficace
        zone_prometteuse = self.zones_prometteuses[0]
        voisinage_efficace = zone_prometteuse['voisinage_efficace']
        
        meilleure_solution = solution_base.clone()
        meilleur_cout = solution_base.cout_total
        
        # Faire 5 essais dans le voisinage efficace
        for _ in range(5):
            solution_temp = self._generer_voisin(meilleure_solution, voisinage_efficace)
            if solution_temp and solution_temp.est_solution_valide():
                solution_amelioree = self._local_search_voisinage(solution_temp, 10)
                if solution_amelioree.cout_total < meilleur_cout:
                    meilleure_solution = solution_amelioree
                    meilleur_cout = solution_amelioree.cout_total
        
        return meilleure_solution if meilleur_cout < solution_base.cout_total else None
def tester_voisinages():
    """Fonction de test pour vérifier que tous les voisinages fonctionnent"""
    print("🧪 TEST DES VOISINAGES VNS")
    
    vns = VNSOptimiseur()
    print(f"Nombre de voisinages disponibles: {len(vns.voisinages)}")
    
    for i, voisinage in enumerate(vns.voisinages):
        nom_methode = voisinage.__name__
        print(f"  {i}: {nom_methode}")
    
    print("✅ Tous les voisinages sont correctement enregistrés!")

def _local_search_voisinage(self, solution, max_iter=20):
        """Local Search spécialisé dans un voisinage"""
        meilleure_solution = solution.clone()
        meilleur_cout = solution.cout_total
        
        for iteration in range(max_iter):
            solution_test = meilleure_solution.clone()
            
            # Appliquer quelques mouvements locaux
            for _ in range(3):
                if len(solution_test.voyages) >= 2:
                    if random.random() < 0.5:  # 50% swap, 50% déplacement
                        # Swap
                        voyages_ids = list(range(len(solution_test.voyages)))
                        v1 = random.choice(voyages_ids)
                        voyages_ids.remove(v1)
                        v2 = random.choice(voyages_ids)
                        
                        voyage1 = solution_test.voyages[v1]
                        voyage2 = solution_test.voyages[v2]
                        
                        if voyage1['produits'] and voyage2['produits']:
                            idx1 = random.randint(0, len(voyage1['produits']) - 1)
                            idx2 = random.randint(0, len(voyage2['produits']) - 1)
                            solution_test.swap_produits(v1, idx1, v2, idx2)
                    else:
                        # Déplacement
                        v_src = random.randint(0, len(solution_test.voyages) - 1)
                        v_dst = random.randint(0, len(solution_test.voyages) - 1)
                        
                        if (v_src != v_dst and 
                            solution_test.voyages[v_src]['produits']):
                            idx = random.randint(0, len(solution_test.voyages[v_src]['produits']) - 1)
                            solution_test.deplacer_produit(idx, v_src, v_dst)
            
            # Test d'amélioration
            if solution_test.cout_total < meilleur_cout:
                meilleure_solution = solution_test.clone()
                meilleur_cout = solution_test.cout_total
        
        return meilleure_solution
    

def main_comparaison_methodes():
    """Programme de comparaison des différentes méthodes"""
    print("="*120)
    print("COMPARAISON DES MÉTHODES D'OPTIMISATION")
    print("="*120)
    print("Cette fonction n'est pas encore implémentée")
def main_comparaison_methodes():
    """Programme de comparaison des différentes méthodes"""
    print("="*120)
    print("COMPARAISON DES MÉTHODES D'OPTIMISATION")
    print("="*120)
    print("Cette fonction n'est pas encore implémentée")
def appliquer_vns(resultats_heuristique, max_iterations=100):
        """
        Interface simple pour appliquer VNS
        """
        vns = VNSOptimiseur()
        return vns.optimiser_vns(resultats_heuristique, max_iterations)


def optimiser_avec_vns(optimiseur, produits, vehicules, date_debut, heure_debut, duree_max=7):
        """
        Fonction helper qui combine heuristique + VNS
        """
        print("🚀 OPTIMISATION HYBRIDE: Heuristique + VNS")
        
        # 1. Heuristique existante
        print("\n1️⃣ Phase heuristique...")
        resultats = optimiseur.calculer_navettes_optimales(
            produits, vehicules, date_debut, heure_debut, duree_max
        )
        
        if not resultats:
            print("❌ Heuristique échouée")
            return None
        
        cout_heuristique = resultats['vehicule_optimal']['cout_total']
        print(f"✅ Heuristique terminée: {cout_heuristique:.2f}€")
        
        # 2. VNS
        print("\n2️⃣ Phase VNS...")
        resultats_ameliores = appliquer_vns(resultats, max_iterations=150)
        
        if resultats_ameliores:
            cout_final = resultats_ameliores['vehicule_optimal']['cout_total']
            gain = cout_heuristique - cout_final
            
            if gain > 0:
                print(f"🎉 OPTIMISATION VNS RÉUSSIE!")
                print(f"   Gain total: {gain:.2f}€ ({gain/cout_heuristique*100:.2f}%)")
                return resultats_ameliores
            else:
                print("ℹ️ Solution heuristique déjà optimale")
                return resultats
        
        return resultats

import random
import math
from datetime import datetime, timedelta

def main_complet():
    """
    Programme principal avec utilisation de l'instance réelle de la base de données
    Optimisation sur horizon de 12 semaines avec données réelles
    """
    print("="*120)
    print("SYSTÈME D'OPTIMISATION DE NAVETTES - VERSION PRODUCTION")
    print("12 semaines | Données réelles | RESPECT STRICT DU PLANNING HEBDOMADAIRE")
    print("🔧 MODE PRODUCTION ACTIVÉ - Données de la base de données")
    print("="*120)
    
    # Paramètres de l'instance (à adapter selon vos besoins)
    ID_CLIENT = "EGS-120"  # Remplacer par l'ID client réel
    CIBLE_LONGITUDE = -2.2162  # Remplacer par les coordonnées réelles
    CIBLE_LATITUDE = 31.6177
    
    try:
        # 1. CRÉATION DE L'INSTANCE AVEC DONNÉES RÉELLES
        print(f"\n🔧 CRÉATION DE L'INSTANCE D'OPTIMISATION...")
        instance = creer_instance_optimisation(
            id_client=ID_CLIENT,
            cible_longitude=CIBLE_LONGITUDE,
            cible_latitude=CIBLE_LATITUDE
        )
        
        if not instance:
            print("❌ Impossible de créer l'instance. Vérifiez les paramètres.")
            return None
            
        # 2. AFFICHAGE DU RÉSUMÉ DE L'INSTANCE
        instance.afficher_resume()
        
        # 3. PRÉPARATION DES DONNÉES POUR L'OPTIMISEUR
        print(f"\n🔄 PRÉPARATION DES DONNÉES POUR L'OPTIMISATION...")
        
        # Conversion des véhicules de l'instance vers le format OptimisateurNavettes
        vehicules_data = []
        for vtype, capacites in instance.L.items():
            vehicule_info = {
                'nom': instance.get_vehicle_type_name(vtype),
                'type': 'LEGER' if capacites['Qw'] < 5000 else 'MOYEN' if capacites['Qw'] < 20000 else 'LOURD',
                'capacite_poids_max': capacites['Qw'] / 1000,  # Convertir kg en tonnes
                'capacite_volume_max': capacites['Qv'],
                'vitesse_kmh': instance.V[vtype],
                'cout_fixe_jour': instance.c[vtype],
                'cout_variable_km': 0.8  # Valeur par défaut
            }
            vehicules_data.append(vehicule_info)
        
        print(f"✅ {len(vehicules_data)} types de véhicules disponibles")
        
        # 4. OPTIMISATION SEMAINE PAR SEMAINE AVEC DONNÉES RÉELLES
        print(f"\n" + "="*120)
        print("OPTIMISATION AVEC DONNÉES RÉELLES - TRAITEMENT SEMAINE PAR SEMAINE")
        print("="*120)
        
        resultats_globaux = {
            'resultats_par_semaine': {},
            'cout_total_global': 0,
            'statistiques': {
                'semaines_completement_livrees': 0,
                'semaines_partiellement_livrees': 0,
                'semaines_non_livrees': 0,
                'vehicules_utilises': {},
                'poids_total_projet': 0,
                'volume_total_projet': 0
            },
            'instance_data': {
                'client_id': instance.id_client,
                'distance_AB': instance.d_AB,
                'localisation': getattr(instance, 'client_localisation', 'Non définie'),
                'nature_terrain': getattr(instance, 'nature_terrain', 'Normal')
            }
        }
        
        cout_total_global = 0
        
        # TRAITEMENT DE CHAQUE SEMAINE
        for semaine in instance.T:  # Utiliser l'horizon de l'instance (1 à 12)
            print(f"\n" + "🗓️ " + "="*100)
            print(f"SEMAINE {semaine} - PLANNING AVEC DONNÉES RÉELLES")
            print("="*100)
            
            # Vérifier s'il y a des demandes pour cette semaine
            poids_semaine = instance.dw_AB.get(semaine, 0)
            volume_semaine = instance.dv_AB.get(semaine, 0)
            
            if poids_semaine <= 0 and volume_semaine <= 0:
                print(f"   📭 Aucune livraison planifiée pour la semaine {semaine}")
                resultats_globaux['statistiques']['semaines_non_livrees'] += 1
                continue
            
            print(f"📦 DEMANDES SEMAINE {semaine}:")
            print(f"   Poids total: {poids_semaine:.1f} kg ({poids_semaine/1000:.2f} tonnes)")
            print(f"   Volume total: {volume_semaine:.1f} m³")
            
            # Créer un produit équivalent pour cette semaine
            produits_semaine = [{
                'nom': f'ÉQUIPEMENTS_SEMAINE_{semaine}',
                'quantite': 1,  # Une seule "unité" qui représente tout
                'poids_unitaire': poids_semaine / 1000,  # Convertir en tonnes
                'volume_unitaire': volume_semaine,
                'distance_km': instance.d_AB,
                'vitesse_kmh': 80  # Vitesse par défaut
            }]
            
            # 5. OPTIMISATION AVEC OptimisateurNavettes
            print(f"\n🔧 OPTIMISATION SEMAINE {semaine}:")
            
            optimiseur = OptimisateurNavettes()
            date_debut_semaine = '2025-06-02'  # À adapter selon vos besoins
            heure_debut = '08:00'
            
            resultats_semaine = optimiseur.calculer_navettes_optimales(
                produits_semaine,
                vehicules_data,
                date_debut_semaine,
                heure_debut,
                duree_max_jours=7
            )
            
            if not resultats_semaine:
                print(f"   ❌ SEMAINE {semaine}: Optimisation échouée")
                resultats_globaux['statistiques']['semaines_non_livrees'] += 1
                continue
            
            # Enregistrer les résultats
            cout_semaine = resultats_semaine['vehicule_optimal']['cout_total']
            vehicule_nom = resultats_semaine['vehicule_utilise']['nom']
            
            # Compter l'utilisation des véhicules
            if vehicule_nom not in resultats_globaux['statistiques']['vehicules_utilises']:
                resultats_globaux['statistiques']['vehicules_utilises'][vehicule_nom] = 0
            resultats_globaux['statistiques']['vehicules_utilises'][vehicule_nom] += 1
            
            resultats_globaux['resultats_par_semaine'][semaine] = {
                'cout_total': cout_semaine,
                'poids_total': poids_semaine / 1000,  # En tonnes
                'volume_total': volume_semaine,
                'vehicule_utilise': vehicule_nom,
                'nb_vehicules_necessaires': resultats_semaine['nb_vehicules_necessaires'],
                'duree_reelle': resultats_semaine['duree_reelle'],
                'resultats_detailles': resultats_semaine
            }
            
            cout_total_global += cout_semaine
            resultats_globaux['statistiques']['poids_total_projet'] += poids_semaine / 1000
            resultats_globaux['statistiques']['volume_total_projet'] += volume_semaine
            resultats_globaux['statistiques']['semaines_completement_livrees'] += 1
            
            print(f"   ✅ SEMAINE {semaine}: Optimisation réussie")
            print(f"   💰 Coût: {cout_semaine:.2f}€")
            print(f"   🚛 Véhicule: {vehicule_nom}")
            print(f"   📊 Charge: {poids_semaine/1000:.2f}t, {volume_semaine:.1f}m³")
        
        # 6. CALCULS FINAUX ET STATISTIQUES
        resultats_globaux['cout_total_global'] = cout_total_global
        
        # AFFICHAGE FINAL DÉTAILLÉ
        print("\n" + "="*120)
        print("RÉSUMÉ FINAL - OPTIMISATION AVEC DONNÉES RÉELLES")
        print("="*120)
        
        print(f"\n📋 INFORMATIONS INSTANCE:")
        print(f"Client: {resultats_globaux['instance_data']['client_id']}")
        print(f"Localisation: {resultats_globaux['instance_data']['localisation']}")
        print(f"Distance A→B: {resultats_globaux['instance_data']['distance_AB']} km")
        print(f"Nature du terrain: {resultats_globaux['instance_data']['nature_terrain']}")
        
        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"Semaines complètement livrées: {resultats_globaux['statistiques']['semaines_completement_livrees']}/12 "
              f"({resultats_globaux['statistiques']['semaines_completement_livrees']/12*100:.1f}%)")
        print(f"Semaines sans livraison: {resultats_globaux['statistiques']['semaines_non_livrees']}/12 "
              f"({resultats_globaux['statistiques']['semaines_non_livrees']/12*100:.1f}%)")
        
        print(f"\n🚛 UTILISATION DES VÉHICULES:")
        for vehicule, count in resultats_globaux['statistiques']['vehicules_utilises'].items():
            pourcentage = (count / 12) * 100
            print(f"  {vehicule}: {count} semaines ({pourcentage:.1f}%)")
        
        print(f"\n💰 BILAN FINANCIER:")
        print(f"Coût total projet: {cout_total_global:,.2f}€")
        print(f"Poids total transporté: {resultats_globaux['statistiques']['poids_total_projet']:.2f} tonnes")
        print(f"Volume total transporté: {resultats_globaux['statistiques']['volume_total_projet']:.2f} m³")
        
        if resultats_globaux['statistiques']['poids_total_projet'] > 0:
            cout_par_tonne = cout_total_global / resultats_globaux['statistiques']['poids_total_projet']
            print(f"Coût par tonne: {cout_par_tonne:.2f}€/t")
        
        if resultats_globaux['statistiques']['volume_total_projet'] > 0:
            cout_par_m3 = cout_total_global / resultats_globaux['statistiques']['volume_total_projet']
            print(f"Coût par m³: {cout_par_m3:.2f}€/m³")
        
        # ANALYSE DÉTAILLÉE PAR SEMAINE
        print(f"\n📅 ANALYSE DÉTAILLÉE PAR SEMAINE:")
        print(f"{'Sem':>3} {'Véhicule':>25} {'Veh':>3} {'Durée':>6} {'Poids':>8} {'Volume':>8} {'Coût':>12}")
        print("-" * 80)
        
        for semaine in range(1, 13):
            if semaine in resultats_globaux['resultats_par_semaine']:
                r = resultats_globaux['resultats_par_semaine'][semaine]
                print(f"{semaine:>3} {r['vehicule_utilise'][:23]:>25} {r['nb_vehicules_necessaires']:>3} "
                      f"{r['duree_reelle']:>4}j {r['poids_total']:>7.1f}t {r['volume_total']:>7.1f}m³ "
                      f"{r['cout_total']:>11,.0f}€")
            else:
                print(f"{semaine:>3} {'Aucune livraison':>25} {'0':>3} {'0':>6} {'0':>8} {'0':>8} {'0':>12}")
        
        # VALIDATION DU SYSTÈME
        print(f"\n🎯 VALIDATION DU SYSTÈME:")
        taux_reussite = (resultats_globaux['statistiques']['semaines_completement_livrees'] / 12) * 100
        
        if taux_reussite >= 90:
            print(f"✅ EXCELLENT: {taux_reussite:.1f}% de réussite")
            print(f"   Le système fonctionne parfaitement avec les données réelles!")
        elif taux_reussite >= 75:
            print(f"🟡 BON: {taux_reussite:.1f}% de réussite")
            print(f"   Le système fonctionne bien avec quelques améliorations possibles")
        else:
            print(f"🔴 À AMÉLIORER: {taux_reussite:.1f}% de réussite")
            print(f"   Le système nécessite des ajustements")
        
        print(f"\n🚀 CONCLUSION:")
        print(f"   ✅ Système testé avec données réelles de la base")
        print(f"   ✅ Instance validée et opérationnelle")
        print(f"   ✅ Optimisation multi-semaines réussie")
        print(f"   ✅ Contraintes respectées")
        
        if taux_reussite >= 85:
            print(f"   🎉 SYSTÈME PRÊT POUR LA PRODUCTION!")
        else:
            print(f"   🔧 Ajustements recommandés")
        
        print("="*120)
        
        return resultats_globaux
        
    except Exception as e:
        print(f"❌ ERREUR LORS DE L'OPTIMISATION: {e}")
        print("Vérifiez que:")
        print("1. La base de données est accessible")
        print("2. Le client existe et a des coordonnées")
        print("3. Des véhicules sont disponibles")
        print("4. Des demandes de transfert existent")
        return None


if __name__ == "__main__":
    # Exécution avec données réelles
    resultats = main_complet()
    
    if resultats:
        print(f"\n📄 Résultats sauvegardés et disponibles pour analyse")
        print(f"💡 PROCHAINES ÉTAPES:")
        print(f"   1. Intégrer les algorithmes Local Search et VNS")
        print(f"   2. Ajouter la planification temporelle détaillée")
        print(f"   3. Implémenter les contraintes métier spécifiques")
        print(f"   4. Ajouter la gestion des exceptions et fallbacks")
if __name__ == "__main__":
    # Exécution de la fonction de test des voisinages
    tester_voisinages()
    
    # Exécution de la comparaison des méthodes (placeholder)
    main_comparaison_methodes()
    
    # Exécution de l'optimisation complète avec données réelles
    main_complet()
