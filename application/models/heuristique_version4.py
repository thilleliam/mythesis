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


class OptimisateurNavettes:
    """
    Optimisateur de navettes - Version heuristique détaillée uniquement
    """
        
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
        
        print(f"\n=== OPTIMISATION HEURISTIQUE DÉTAILLÉE ===")
        print(f"⏰ CONTRAINTE TEMPORELLE: {duree_max_jours} jours maximum")
        print(f"📦 DEMANDE TOTALE:")
        print(f"   - Poids: {poids_total:.2f} tonnes")
        print(f"   - Volume: {volume_total:.2f} m³")
        print(f"   - Distance: {demande_equivalente['distance_km']} km")
        
        try:
            solution_optimale = self._chercher_combinaison_optimale(
                demande_equivalente, 
                vehicules_data,
                date_debut,
                heure_debut, 
                duree_max_jours
            )
            
            if not solution_optimale:
                print(f"\n❌ AUCUNE SOLUTION TROUVÉE")
                return None
            
            # Gestion du type de solution
            type_solution = solution_optimale.get('type_solution', 'inconnu')
            
            if type_solution in ['flotte_heterogene', 'flotte_homogene']:
                print(f"\n🎉 SOLUTION COMBINAISON SÉLECTIONNÉE!")
                
                return {
                    'type_solution': 'combinaison',
                    'vehicule_principal': solution_optimale.get('vehicule_principal', 'Véhicule Principal'),
                    'vehicule_secondaire': solution_optimale.get('vehicule_secondaire'),
                    'nb_vehicules_principal': solution_optimale.get('nb_vehicules_principal', 1),
                    'nb_vehicules_secondaire': solution_optimale.get('nb_vehicules_secondaire', 0),
                    'cout_total': solution_optimale.get('cout_total', 0),
                    'duree_reelle': solution_optimale.get('duree_reelle', duree_max_jours),
                    'respect_contrainte': True,
                    'demande_equivalente': demande_equivalente,
                    'vehicule_optimal': {
                        'cout_total': solution_optimale.get('cout_total', 0)
                    },
                    'solution_detaillee': solution_optimale
                }
            else:
                # Solution véhicule unique
                print(f"\n✅ SOLUTION VÉHICULE UNIQUE SÉLECTIONNÉE!")
                
                return {
                    'type_solution': 'vehicule_unique',
                    'vehicule_utilise': solution_optimale.get('vehicule_utilise', {
                        'nom': 'Véhicule Standard',
                        'type': 'STANDARD'
                    }),
                    'nb_vehicules_necessaires': solution_optimale.get('nb_vehicules_necessaires', 1),
                    'duree_reelle': solution_optimale.get('duree_reelle', duree_max_jours),
                    'respect_contrainte': True,
                    'vehicule_optimal': {
                        'cout_total': solution_optimale.get('cout_total', 0)
                    },
                    'demande_equivalente': demande_equivalente
                }
                
        except Exception as e:
            print(f"❌ ERREUR dans calculer_navettes_optimales: {e}")
            
            return {
                'type_solution': 'erreur',
                'vehicule_utilise': {
                    'nom': 'Véhicule Erreur',
                    'type': 'ERREUR'
                },
                'vehicule_optimal': {
                    'cout_total': 9999
                },
                'demande_equivalente': demande_equivalente,
                'cout_total': 9999,
                'duree_reelle': duree_max_jours,
                'nb_vehicules_necessaires': 1,
                'respect_contrainte': False,
                'erreur_detail': str(e)
            }

    def _chercher_combinaison_optimale(self, demande, vehicules_data, date_debut, heure_debut, duree_max_jours=7):
        """
        NOUVELLE VERSION CORRIGÉE avec calcul de capacité sur période
        """
        
        print(f"\n🔄 RECHERCHE DE COMBINAISON OPTIMALE DE VÉHICULES")
        print(f"   Objectif: Respecter {duree_max_jours} jours avec voyages multiples")
        
        poids_demande = demande['quantite_poids'] 
        volume_demande = demande['quantite_volume']
        distance_km = demande['distance_km']
        
        print(f"\n📋 ANALYSE DE LA DEMANDE:")
        print(f"   - Poids total: {poids_demande:.2f} tonnes")
        print(f"   - Volume total: {volume_demande:.2f} m³")
        print(f"   - Distance: {distance_km} km")
        print(f"   - Durée maximale: {duree_max_jours} jours")
        
        # 1. Test véhicules individuels avec voyages multiples
        print(f"\n🔍 ÉTAPE 1: TEST DES VÉHICULES INDIVIDUELS (VOYAGES MULTIPLES)")
        print(f"=" * 70)
        
        vehicules_viables_seuls = []
        
        for i, vehicule in enumerate(vehicules_data):
            print(f"\n   Véhicule {i+1}: {vehicule['nom']}")
            print(f"   ├─ Capacité par voyage: {vehicule['capacite_poids_max']:.1f}t, {vehicule['capacite_volume_max']:.1f}m³")
            print(f"   ├─ Vitesse: {vehicule.get('vitesse_kmh', 80)} km/h")
            print(f"   └─ Quantité disponible: {vehicule.get('quantite', 1)}")
            
            # Calculer capacité sur la période avec 1 véhicule
            capacite_periode = self._calculer_capacite_sur_periode(vehicule, 1, duree_max_jours, distance_km)
            
            print(f"      📊 CAPACITÉ SUR {duree_max_jours} JOURS:")
            print(f"         Voyages possibles: {capacite_periode['voyages_par_vehicule']}")
            print(f"         Capacité totale: {capacite_periode['capacite_poids']:.1f}t, {capacite_periode['capacite_volume']:.1f}m³")
            print(f"         Temps par voyage: {capacite_periode['temps_par_voyage']:.1f}h")
            
            # Vérifier si 1 véhicule suffit
            if (capacite_periode['capacite_poids'] >= poids_demande and 
                capacite_periode['capacite_volume'] >= volume_demande):
                
                # Calculer le coût
                distance_totale = capacite_periode['voyages_par_vehicule'] * distance_km * 2
                cout_estime = distance_totale * vehicule.get('cout_variable_km', 280.0)
                
                vehicules_viables_seuls.append({
                    'vehicule': vehicule,
                    'cout': cout_estime,
                    'voyages': capacite_periode['voyages_par_vehicule']
                })
                
                print(f"      ✅ VIABLE SEUL - Coût: {cout_estime:.0f} DA")
            else:
                print(f"      ❌ INSUFFISANT SEUL")
        
        if vehicules_viables_seuls:
            print(f"\n🎯 VÉHICULE UNIQUE TROUVÉ")
            # Sélectionner le moins cher
            vehicules_viables_seuls.sort(key=lambda x: x['cout'])
            meilleur = vehicules_viables_seuls[0]
            
            return {
                'type_solution': 'vehicule_unique',
                'vehicule_utilise': meilleur['vehicule'],
                'nb_vehicules_necessaires': 1,
                'cout_total': meilleur['cout'],
                'voyages_necessaires': meilleur['voyages']
            }
        
        # 2. Test combinaisons multiples avec voyages
        print(f"\n🔍 ÉTAPE 2: TEST DES COMBINAISONS MULTIPLES (VOYAGES MULTIPLES)")
        print(f"=" * 70)
        
        solutions_candidates = []
        
        for i, vehicule_principal in enumerate(vehicules_data):
            print(f"\n   🚛 VÉHICULE PRINCIPAL: {vehicule_principal['nom']}")
            
            max_vehicules_principal = vehicule_principal.get('quantite', 9)
            
            for nb_principal in range(1, min(max_vehicules_principal + 1, 6)):
                print(f"\n      Test avec {nb_principal} véhicule(s) principal(aux)")
                
                # Calculer capacité réelle sur la période
                capacite_principale = self._calculer_capacite_sur_periode(
                    vehicule_principal, nb_principal, duree_max_jours, distance_km
                )
                
                print(f"         Capacité sur {duree_max_jours} jours: {capacite_principale['capacite_poids']:.1f}t, {capacite_principale['capacite_volume']:.1f}m³")
                print(f"         Voyages totaux: {capacite_principale['voyages_totaux']}")
                
                if (capacite_principale['capacite_poids'] >= poids_demande and 
                    capacite_principale['capacite_volume'] >= volume_demande):
                    
                    # Solution homogène trouvée
                    distance_totale = capacite_principale['voyages_totaux'] * distance_km * 2
                    cout_solution = distance_totale * vehicule_principal.get('cout_variable_km', 280.0)
                    
                    solution = {
                        'type': 'flotte_homogene',
                        'vehicule_principal': vehicule_principal,
                        'nb_vehicules_principal': nb_principal,
                        'vehicule_secondaire': None,
                        'nb_vehicules_secondaire': 0,
                        'cout_total': cout_solution,
                        'capacite_totale_poids': capacite_principale['capacite_poids'],
                        'capacite_totale_volume': capacite_principale['capacite_volume']
                    }
                    
                    solutions_candidates.append(solution)
                    print(f"         ✅ SOLUTION HOMOGÈNE: {nb_principal}× {vehicule_principal['nom']}")
                    print(f"            Coût: {cout_solution:.0f} DA")
                    break
                    
                else:
                    # Chercher véhicule secondaire
                    poids_restant = max(0, poids_demande - capacite_principale['capacite_poids'])
                    volume_restant = max(0, volume_demande - capacite_principale['capacite_volume'])
                    
                    print(f"         Manque: {poids_restant:.1f}t, {volume_restant:.1f}m³")
                    
                    if poids_restant > 0 or volume_restant > 0:
                        for vehicule_secondaire in vehicules_data:
                            if vehicule_secondaire['nom'] == vehicule_principal['nom']:
                                continue
                            
                            max_vehicules_secondaire = vehicule_secondaire.get('quantite', 9)
                            
                            # Tester différents nombres de véhicules secondaires
                            for nb_secondaire in range(1, min(max_vehicules_secondaire + 1, 10)):
                                capacite_secondaire = self._calculer_capacite_sur_periode(
                                    vehicule_secondaire, nb_secondaire, duree_max_jours, distance_km
                                )
                                
                                # Vérifier si la combinaison couvre la demande
                                capacite_totale_poids = capacite_principale['capacite_poids'] + capacite_secondaire['capacite_poids']
                                capacite_totale_volume = capacite_principale['capacite_volume'] + capacite_secondaire['capacite_volume']
                                
                                if (capacite_totale_poids >= poids_demande and 
                                    capacite_totale_volume >= volume_demande):
                                    
                                    # Calculer coût combiné
                                    distance_principale = capacite_principale['voyages_totaux'] * distance_km * 2
                                    distance_secondaire = capacite_secondaire['voyages_totaux'] * distance_km * 2
                                    
                                    cout_principal = distance_principale * vehicule_principal.get('cout_variable_km', 280.0)
                                    cout_secondaire = distance_secondaire * vehicule_secondaire.get('cout_variable_km', 280.0)
                                    cout_total = cout_principal + cout_secondaire
                                    
                                    solution = {
                                        'type': 'flotte_heterogene',
                                        'vehicule_principal': vehicule_principal,
                                        'nb_vehicules_principal': nb_principal,
                                        'vehicule_secondaire': vehicule_secondaire,
                                        'nb_vehicules_secondaire': nb_secondaire,
                                        'cout_total': cout_total,
                                        'capacite_totale_poids': capacite_totale_poids,
                                        'capacite_totale_volume': capacite_totale_volume
                                    }
                                    
                                    solutions_candidates.append(solution)
                                    print(f"         ✅ SOLUTION HÉTÉROGÈNE:")
                                    print(f"            {nb_principal}× {vehicule_principal['nom']} + {nb_secondaire}× {vehicule_secondaire['nom']}")
                                    print(f"            Coût: {cout_total:.0f} DA")
                                    break
        
        # 3. Sélectionner la meilleure solution
        print(f"\n🎯 ÉTAPE 3: SÉLECTION DE LA MEILLEURE SOLUTION")
        print(f"=" * 60)
        print(f"   Solutions candidates: {len(solutions_candidates)}")
        
        if solutions_candidates:
            # Trier par coût
            solutions_candidates.sort(key=lambda x: x['cout_total'])
            meilleure_solution = solutions_candidates[0]
            
            print(f"\n   🏆 SOLUTION OPTIMALE:")
            print(f"      Type: {meilleure_solution['type'].upper()}")
            print(f"      Coût: {meilleure_solution['cout_total']:.0f} DA")
            
            return self._convertir_solution_vers_format_standard(
                meilleure_solution, demande, date_debut, heure_debut, duree_max_jours
            )
        
        else:
            print(f"   ❌ Aucune solution trouvée")
            return None
        
    def _calculer_capacite_sur_periode(self, vehicule, nb_vehicules, duree_jours, distance_km):
        """
        Calcule la capacité réelle d'un ensemble de véhicules sur une période donnée
        en tenant compte des voyages multiples possibles.
        
        Args:
            vehicule: Dictionnaire avec les caractéristiques du véhicule
            nb_vehicules: Nombre de véhicules de ce type
            duree_jours: Durée en jours pour accomplir le transport
            distance_km: Distance à parcourir
        
        Returns:
            dict: Capacités totales sur la période (poids et volume)
        """
        
        # Capacité par véhicule pour un voyage
        capacite_poids_voyage = vehicule.get('capacite_poids_max', 0)
        capacite_volume_voyage = vehicule.get('capacite_volume_max', 0)
        
        # Calcul du nombre de voyages possibles par véhicule sur la période
        vitesse = vehicule.get('vitesse_kmh', 60)
        temps_aller_retour = (2 * distance_km) / vitesse  # heures
        temps_chargement_dechargement = 3.0  # heures (1.5h + 1.5h)
        temps_par_voyage = temps_aller_retour + temps_chargement_dechargement
        
        # Heures de travail par jour (de 7h à 18h = 11h)
        heures_travail_par_jour = 11
        heures_totales_disponibles = duree_jours * heures_travail_par_jour
        
        # Nombre maximum de voyages par véhicule sur la période
        voyages_max_par_vehicule = int(heures_totales_disponibles / temps_par_voyage)
        
        # S'assurer qu'il y a au moins 1 voyage possible
        voyages_max_par_vehicule = max(1, voyages_max_par_vehicule)
        
        # Capacité totale sur la période
        capacite_totale_poids = nb_vehicules * voyages_max_par_vehicule * capacite_poids_voyage
        capacite_totale_volume = nb_vehicules * voyages_max_par_vehicule * capacite_volume_voyage
        
        print(f"         📊 Calcul capacité période:")
        print(f"            Temps par voyage: {temps_par_voyage:.1f}h")
        print(f"            Voyages/véhicule: {voyages_max_par_vehicule}")
        print(f"            Capacité période: {capacite_totale_poids:.1f}t, {capacite_totale_volume:.1f}m³")
        
        return {
            'capacite_poids': capacite_totale_poids,
            'capacite_volume': capacite_totale_volume,
            'voyages_par_vehicule': voyages_max_par_vehicule,
            'voyages_totaux': nb_vehicules * voyages_max_par_vehicule,
            'temps_par_voyage': temps_par_voyage,
            'heures_travail_par_jour': heures_travail_par_jour,
            'heures_totales_disponibles': heures_totales_disponibles
        }
    def _vehicule_peut_reussir_seul_avec_calcul(self, vehicule, poids_demande, volume_demande, distance_km, duree_max_jours):
        """
        Vérifie si un véhicule peut réussir seul avec calcul détaillé
        Version corrigée avec coût variable uniquement
        """
        print(f"\n      🔍 ANALYSE DÉTAILLÉE:")
        
        # Nombre de voyages nécessaires
        voyages_poids = math.ceil(poids_demande / vehicule['capacite_poids_max'])
        voyages_volume = math.ceil(volume_demande / vehicule['capacite_volume_max'])
        voyages_necessaires = max(voyages_poids, voyages_volume)
        
        print(f"         Voyages pour poids: {voyages_poids} (charge: {poids_demande:.1f}t / {vehicule['capacite_poids_max']:.1f}t)")
        print(f"         Voyages pour volume: {voyages_volume} (charge: {volume_demande:.1f}m³ / {vehicule['capacite_volume_max']:.1f}m³)")
        print(f"         Voyages nécessaires: {voyages_necessaires}")
        
        # Estimation temps par voyage
        vitesse = vehicule.get('vitesse_kmh', 60)
        temps_aller_retour = (2 * distance_km) / vitesse  # heures
        temps_chargement_dechargement = 3  # 1.5h + 1.5h
        temps_par_voyage = temps_aller_retour + temps_chargement_dechargement
        
        print(f"         Temps par voyage:")
        print(f"            Aller-retour: {temps_aller_retour:.1f}h ({distance_km}km × 2 à {vitesse}km/h)")
        print(f"            Chargement+déchargement: {temps_chargement_dechargement:.1f}h")
        print(f"            Total par voyage: {temps_par_voyage:.1f}h")
        
        # Temps total nécessaire
        temps_total_heures = voyages_necessaires * temps_par_voyage
        jours_necessaires = temps_total_heures / 24
        
        print(f"         Temps total: {temps_total_heures:.1f}h = {jours_necessaires:.1f} jours")
        
        # Peut réussir si <= duree_max_jours
        peut_reussir = jours_necessaires <= duree_max_jours
        
        print(f"         Contrainte temporelle: {'✅ RESPECTÉE' if peut_reussir else '❌ DÉPASSÉE'}")
        print(f"         ({jours_necessaires:.1f} jours ≤ {duree_max_jours} jours: {peut_reussir})")
        
        # Calcul coût estimé (COÛT VARIABLE UNIQUEMENT)
        cout_estime = 0
        if peut_reussir:
            # Distance totale = distance × voyages × 2 (aller-retour) 
            distance_totale = distance_km * voyages_necessaires * 2
            cout_estime = distance_totale * vehicule.get('cout_variable_km', 280.0)
            
            print(f"         Coût estimé (VARIABLE UNIQUEMENT):")
            print(f"            Distance totale: {distance_totale:.0f}km ({distance_km}km × {voyages_necessaires} voyages × 2)")
            print(f"            Coût variable: {cout_estime:.0f} DA ({distance_totale:.0f}km × {vehicule.get('cout_variable_km', 280.0):.0f} DA/km)")
            print(f"            Total: {cout_estime:.0f} DA")
        
        return {
            'reussite': peut_reussir,
            'voyages_necessaires': voyages_necessaires,
            'jours_necessaires': jours_necessaires,
            'cout_estime': cout_estime,
            'temps_par_voyage': temps_par_voyage,
            'temps_total_heures': temps_total_heures
        }
    def _selectionner_meilleur_vehicule_unique(self, vehicules_data, demande, date_debut, heure_debut, duree_max_jours):
        """Sélectionne le meilleur véhicule unique avec analyse détaillée"""
        
        print(f"\n🔍 SÉLECTION DU MEILLEUR VÉHICULE UNIQUE")
        print(f"=" * 50)
        
        meilleur_vehicule = None
        meilleur_cout = float('inf')
        meilleur_result = None
        
        candidats = []
        
        for i, vehicule in enumerate(vehicules_data):
            print(f"\n   Candidat {i+1}: {vehicule['nom']}")
            
            result = self._vehicule_peut_reussir_seul_avec_calcul(
                vehicule, 
                demande['quantite_poids'], 
                demande['quantite_volume'],
                demande['distance_km'], 
                duree_max_jours
            )
            
            if result['reussite']:
                candidats.append({
                    'vehicule': vehicule,
                    'result': result,
                    'cout': result['cout_estime']
                })
                
                if result['cout_estime'] < meilleur_cout:
                    meilleur_vehicule = vehicule
                    meilleur_cout = result['cout_estime']
                    meilleur_result = result
                
                print(f"      ✅ CANDIDAT VALIDE - Coût: {result['cout_estime']:.0f}DA")
            else:
                print(f"      ❌ NON VIABLE")
        
        if candidats:
            print(f"\n   📊 CLASSEMENT DES CANDIDATS:")
            candidats.sort(key=lambda x: x['cout'])
            
            for idx, candidat in enumerate(candidats):
                statut = "🏆 OPTIMAL" if idx == 0 else f"   #{idx+1}"
                print(f"      {statut} {candidat['vehicule']['nom']}: {candidat['cout']:.0f}DA")
                print(f"           Voyages: {candidat['result']['voyages_necessaires']}, Durée: {candidat['result']['jours_necessaires']:.1f}j")
            
            print(f"\n   🎯 VÉHICULE SÉLECTIONNÉ: {meilleur_vehicule['nom']}")
            print(f"      Coût optimal: {meilleur_cout:.0f}DA")
            print(f"      Voyages nécessaires: {meilleur_result['voyages_necessaires']}")
            print(f"      Durée estimée: {meilleur_result['jours_necessaires']:.1f} jours")
            
            return {
                'vehicule': meilleur_vehicule,
                'cout_total': meilleur_cout,
                'duree_reelle_jours': meilleur_result['jours_necessaires'],
                'type_solution': 'vehicule_unique',
                'vehicule_utilise': meilleur_vehicule,
                'nb_vehicules_necessaires': 1,
                'voyages_necessaires': meilleur_result['voyages_necessaires']
            }
        
        return None

    def _convertir_solution_vers_format_standard(self, solution, demande, date_debut, heure_debut, duree_max_jours):
        """Convertit une solution vers le format standard de retour avec extraction correcte du nom"""
        
        print(f"\n🔄 CONVERSION VERS FORMAT STANDARD")
        print(f"   Type de solution: {solution['type']}")
        
        nb_vehicules_total = solution['nb_vehicules_principal'] + solution.get('nb_vehicules_secondaire', 0)
        
        # EXTRACTION CORRECTE DU NOM DU VÉHICULE PRINCIPAL
        vehicule_principal = solution.get('vehicule_principal', {})
        nom_vehicule_principal = vehicule_principal.get('nom', 'Véhicule Principal')
        
        # EXTRACTION CORRECTE DU NOM DU VÉHICULE SECONDAIRE
        vehicule_secondaire = solution.get('vehicule_secondaire')
        nom_vehicule_secondaire = None
        if vehicule_secondaire:
            nom_vehicule_secondaire = vehicule_secondaire.get('nom', 'Véhicule Secondaire')
        
        print(f"   Véhicule principal: {nom_vehicule_principal}")
        if nom_vehicule_secondaire:
            print(f"   Véhicule secondaire: {nom_vehicule_secondaire}")
        
        result = {
            'type_solution': solution['type'],
            'vehicule_principal': nom_vehicule_principal,
            'nb_vehicules_principal': solution['nb_vehicules_principal'],
            'cout_total': solution['cout_total'],
            'demande_equivalente': demande,
            'date_debut_projet': date_debut,
            'duree_reelle': duree_max_jours,
            'nb_vehicules_necessaires': nb_vehicules_total,
            'vehicule_optimal': {
                'cout_total': solution['cout_total']
            },
            'respect_contrainte': True
        }
        
        # GESTION CORRECTE DES VÉHICULES SELON LE TYPE DE SOLUTION
        if solution.get('vehicule_secondaire'):
            # Solution hétérogène
            result['vehicule_secondaire'] = nom_vehicule_secondaire
            result['nb_vehicules_secondaire'] = solution['nb_vehicules_secondaire']
            
            # Créer nom combiné pour vehicule_utilise
            nom_combine = f"{nom_vehicule_principal} + {nom_vehicule_secondaire}"
            
            result['vehicule_utilise'] = {
                'nom': nom_combine,
                'type': 'FLOTTE_MULTIPLE',
                'capacite_poids_max': vehicule_principal.get('capacite_poids_max', 0),
                'capacite_volume_max': vehicule_principal.get('capacite_volume_max', 0)
            }
            
            print(f"   Nom combiné: {nom_combine}")
            
        else:
            # Solution homogène
            result['vehicule_secondaire'] = None
            result['nb_vehicules_secondaire'] = 0
            
            result['vehicule_utilise'] = {
                'nom': nom_vehicule_principal,
                'type': vehicule_principal.get('type', 'STANDARD'),
                'capacite_poids_max': vehicule_principal.get('capacite_poids_max', 0),
                'capacite_volume_max': vehicule_principal.get('capacite_volume_max', 0)
            }
            
            print(f"   Véhicule unique: {nom_vehicule_principal}")
        
        print(f"   ✅ Conversion terminée")
        print(f"      Coût final: {result['cout_total']:.0f} DA")
        print(f"      Véhicules: {nb_vehicules_total}")
        print(f"      Nom extrait: {result['vehicule_utilise']['nom']}")
        
        return result

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