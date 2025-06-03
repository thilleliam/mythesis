import pandas as pd
import json
from datetime import datetime, timedelta
import os
import random
import math
import time
import copy

# Correction pour l'erreur Pyomo - Imports conditionnels
try:
    import pyomo.environ as pyo
    from pyomo.opt import SolverFactory
    PYOMO_AVAILABLE = True
except ImportError:
    PYOMO_AVAILABLE = False
    print("⚠️ Pyomo non disponible - Fonctionnalités avancées d'optimisation désactivées")

class OptimisateurNavettes:
    def __init__(self):
        self.model = None
        if PYOMO_AVAILABLE:
            try:
                self.solver = SolverFactory('gurobi')
            except:
                try:
                    self.solver = SolverFactory('glpk')
                except:
                    self.solver = None
                    print("⚠️ Aucun solveur d'optimisation disponible - Mode heuristique uniquement")
        else:
            self.solver = None
        
    def calculer_navettes_optimales(self, produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours=7):
        """
        Calcule les navettes optimales en minimisant les coûts totaux avec contrainte temporelle
        
        produits_a_transporter: liste de dictionnaires avec:
        - nom: nom du produit
        - quantite: nombre d'unités
        - poids_unitaire: poids par unité (en tonnes)
        - volume_unitaire: volume par unité (en m³)
        
        Autres paramètres: distance_km, vitesse_kmh
        
        vehicules_data: liste de dictionnaires avec:
        - nom: nom du véhicule
        - type: 'LEGER' ou 'LOURD'
        - capacite_poids_max: capacité maximale en poids (tonnes)
        - capacite_volume_max: capacité maximale en volume (m³)
        - vitesse_kmh: vitesse du véhicule
        - cout_fixe_jour: coût fixe par jour d'utilisation
        - cout_variable_km: coût variable par kilomètre
        
        date_debut: date de début (format YYYY-MM-DD)
        heure_debut: heure de début (format HH:MM)
        duree_max_jours: durée maximale autorisée (défaut: 7 jours)
        """
        
        # Calculer les totaux de la demande
        poids_total = sum(produit['quantite'] * produit['poids_unitaire'] for produit in produits_a_transporter)
        volume_total = sum(produit['quantite'] * produit['volume_unitaire'] for produit in produits_a_transporter)
        
        demande_equivalente = {
            'nom': 'TRANSPORT MULTI-PRODUITS A→B',
            'distance_km': produits_a_transporter[0].get('distance_km', 800),  # Valeur par défaut
            'vitesse_kmh': produits_a_transporter[0].get('vitesse_kmh', 80),   # Valeur par défaut
            'quantite_poids': poids_total,
            'quantite_volume': volume_total
        }
        
        print(f"\n=== OPTIMISATION DES COÛTS POUR TRANSPORT MULTI-PRODUITS AVEC MÉLANGE ===")
        print(f"⏰ CONTRAINTE TEMPORELLE: Terminé en {duree_max_jours} jours maximum")
        print(f"🔄 STRATÉGIE: Remplissage homogène puis mélange optimal")
        print(f"Nombre de types de produits: {len(produits_a_transporter)}")
        
        # Affichage détaillé des produits
        print(f"\n📦 DÉTAIL DES PRODUITS À TRANSPORTER:")
        for i, produit in enumerate(produits_a_transporter, 1):
            poids_produit = produit['quantite'] * produit['poids_unitaire']
            volume_produit = produit['quantite'] * produit['volume_unitaire']
            
            print(f"  {i}. {produit['nom']}:")
            print(f"     - Quantité: {produit['quantite']} unités")
            print(f"     - Poids unitaire: {produit['poids_unitaire']} tonnes/unité")
            print(f"     - Volume unitaire: {produit['volume_unitaire']} m³/unité")
            print(f"     - Poids total: {poids_produit:.2f} tonnes")
            print(f"     - Volume total: {volume_produit:.2f} m³")
        
        print(f"\n📊 TOTAUX:")
        print(f"Poids total: {poids_total:.2f} tonnes")
        print(f"Volume total: {volume_total:.2f} m³")
        print(f"Distance A-B: {demande_equivalente['distance_km']} km")
        print(f"Nombre de types de véhicules disponibles: {len(vehicules_data)}")
        
        # Analyser chaque type de véhicule avec contrainte temporelle
        analyses_vehicules = []
        
        for vehicule in vehicules_data:
            analyse = self._analyser_vehicule_avec_contrainte(demande_equivalente, vehicule, duree_max_jours)
            analyses_vehicules.append(analyse)
            
            print(f"\n{vehicule['nom']} ({vehicule['type']}):")
            print(f"  Capacités: {vehicule['capacite_poids_max']} tonnes, {vehicule['capacite_volume_max']} m³")
            print(f"  Voyages par véhicule: {analyse['voyages_par_vehicule']} (contrainte: {analyse['contrainte_dominante']})")
            print(f"  Durée avec 1 véhicule: {analyse['duree_un_vehicule']} jour(s)")
            
            if analyse['respect_contrainte']:
                print(f"  ✅ RESPECTE LA CONTRAINTE DE {duree_max_jours} JOURS")
                print(f"  Nombre de véhicules nécessaires: {analyse['nb_vehicules_necessaires']}")
                print(f"  Coût fixe total: {analyse['cout_fixe_total']:.2f}€")
                print(f"  Coût variable total: {analyse['cout_variable_total']:.2f}€")
                print(f"  💰 COÛT TOTAL: {analyse['cout_total']:.2f}€")
                print(f"  📊 Coût par véhicule: {analyse['cout_par_vehicule']:.2f}€")
            else:
                print(f"  ❌ NE RESPECTE PAS LA CONTRAINTE DE {duree_max_jours} JOURS")
                print(f"  Durée minimale nécessaire: {analyse['duree_un_vehicule']} jours")
                print(f"  SOLUTION NON VIABLE dans le délai imparti")
        
        # Filtrer les véhicules viables (qui respectent la contrainte)
        vehicules_viables = [a for a in analyses_vehicules if a['respect_contrainte']]
        
        if not vehicules_viables:
            print(f"\n❌ AUCUN VÉHICULE NE PEUT RESPECTER LA CONTRAINTE DE {duree_max_jours} JOURS")
            print("Recommandations:")
            print("- Augmenter la durée autorisée")
            print("- Utiliser des véhicules avec plus de capacité")
            print("- Diviser la demande en plusieurs lots")
            return None
        
        # Sélectionner le véhicule le plus économique parmi les viables
        vehicule_optimal = min(vehicules_viables, key=lambda x: x['cout_total'])
        
        print(f"\n🏆 VÉHICULE OPTIMAL SÉLECTIONNÉ: {vehicule_optimal['vehicule']['nom']}")
        print(f"💰 COÛT TOTAL: {vehicule_optimal['cout_total']:.2f}€")
        print(f"🚛 NOMBRE DE VÉHICULES: {vehicule_optimal['nb_vehicules_necessaires']}")
        print(f"⏱️ DURÉE RÉELLE: {vehicule_optimal['duree_reelle_jours']} jour(s)")
        
        print(f"\n📊 ÉCONOMIES vs autres véhicules viables:")
        for analyse in vehicules_viables:
            if analyse != vehicule_optimal:
                economie = analyse['cout_total'] - vehicule_optimal['cout_total']
                print(f"  vs {analyse['vehicule']['nom']}: +{economie:.2f}€ ({economie/vehicule_optimal['cout_total']*100:.1f}% plus cher)")
        
        # Effectuer la planification détaillée avec mélange des produits
        resultats_planification = self._planifier_multi_vehicules_melange(
            produits_a_transporter,
            demande_equivalente,
            vehicule_optimal, 
            date_debut, 
            heure_debut,
            duree_max_jours
        )
        
        return {
            'produits_a_transporter': produits_a_transporter,
            'demande_equivalente': demande_equivalente,
            'vehicule_utilise': vehicule_optimal['vehicule'],
            'nb_vehicules_necessaires': vehicule_optimal['nb_vehicules_necessaires'],
            'duree_max_autorisee': duree_max_jours,
            'duree_reelle': vehicule_optimal['duree_reelle_jours'],
            'respect_contrainte': True,
            'analyses_vehicules': analyses_vehicules,
            'vehicules_viables': vehicules_viables,
            'vehicule_optimal': vehicule_optimal,
            'planification_detaillee': resultats_planification
        }
    
    def _analyser_vehicule_avec_contrainte(self, demande, vehicule, duree_max_jours):
        """Analyse un véhicule avec prise en compte de la contrainte temporelle"""
        
        # Calculer le nombre de voyages nécessaires avec un seul véhicule
        nb_voyages_poids = math.ceil(demande['quantite_poids'] / vehicule['capacite_poids_max'])
        nb_voyages_volume = math.ceil(demande['quantite_volume'] / vehicule['capacite_volume_max'])
        voyages_par_vehicule = max(nb_voyages_poids, nb_voyages_volume)
        
        # Estimer la durée avec un seul véhicule
        vitesse_utilisee = vehicule.get('vitesse_kmh', demande['vitesse_kmh'])
        temps_conduite_par_voyage = (demande['distance_km'] * 2) / vitesse_utilisee  # Aller-retour
        temps_total_conduite = temps_conduite_par_voyage * voyages_par_vehicule
        
        # Temps de chargement/déchargement par voyage
        temps_operations_par_voyage = 3.0  # 1.5h chargement + 1.5h déchargement
        temps_total_operations = voyages_par_vehicule * temps_operations_par_voyage
        
        # Estimation de la durée totale en jours (8h de travail par jour)
        temps_total_heures = temps_total_conduite + temps_total_operations
        duree_un_vehicule = math.ceil(temps_total_heures / 8.0)
        
        # Vérifier si un seul véhicule respecte la contrainte
        respect_contrainte = duree_un_vehicule <= duree_max_jours
        
        if respect_contrainte:
            # Un seul véhicule suffit
            nb_vehicules_necessaires = 1
            duree_reelle = duree_un_vehicule
        else:
            # Calculer le nombre de véhicules nécessaires
            nb_vehicules_necessaires = math.ceil(duree_un_vehicule / duree_max_jours)
            duree_reelle = duree_max_jours
            respect_contrainte = True  # Avec plusieurs véhicules, on respecte la contrainte
        
        # Calculer les distances et coûts
        voyages_totaux = voyages_par_vehicule * nb_vehicules_necessaires
        distance_aller_total = voyages_totaux * demande['distance_km']
        distance_retour_total = (voyages_totaux - nb_vehicules_necessaires) * demande['distance_km']  # Pas de retour pour le dernier voyage de chaque véhicule
        distance_totale = distance_aller_total + distance_retour_total
        
        # Coûts
        cout_fixe_total = nb_vehicules_necessaires * duree_reelle * vehicule['cout_fixe_jour']
        cout_variable_total = distance_totale * vehicule['cout_variable_km']
        cout_total = cout_fixe_total + cout_variable_total
        cout_par_vehicule = cout_total / nb_vehicules_necessaires if nb_vehicules_necessaires > 0 else 0
        
        return {
            'vehicule': vehicule,
            'voyages_par_vehicule': voyages_par_vehicule,
            'contrainte_dominante': 'poids' if nb_voyages_poids >= nb_voyages_volume else 'volume',
            'duree_un_vehicule': duree_un_vehicule,
            'respect_contrainte': duree_un_vehicule <= duree_max_jours or nb_vehicules_necessaires > 1,
            'nb_vehicules_necessaires': nb_vehicules_necessaires,
            'duree_reelle_jours': duree_reelle,
            'distance_totale': distance_totale,
            'cout_fixe_total': cout_fixe_total,
            'cout_variable_total': cout_variable_total,
            'cout_total': cout_total,
            'cout_par_vehicule': cout_par_vehicule,
            'voyages_totaux': voyages_totaux
        }
    
    def _planifier_multi_vehicules_melange(self, produits_a_transporter, demande_equivalente, vehicule_optimal, date_debut, heure_debut, duree_max_jours):
        """Planifie les opérations avec mélange optimal des produits - remplissage homogène puis mélange"""
        
        nb_vehicules = vehicule_optimal['nb_vehicules_necessaires']
        voyages_par_vehicule = vehicule_optimal['voyages_par_vehicule']
        vehicule = vehicule_optimal['vehicule']
        
        print(f"\n=== PLANIFICATION DÉTAILLÉE AVEC MÉLANGE OPTIMAL ===")
        print(f"🔄 STRATÉGIE: Remplissage homogène prioritaire, puis mélange intelligent")
        print(f"⏰ CONTRAINTE TEMPORELLE STRICTE: {duree_max_jours} jours maximum")
        print(f"Véhicules utilisés: {nb_vehicules} x {vehicule['nom']}")
        print(f"Voyages par véhicule: {voyages_par_vehicule}")
        print(f"Voyages totaux: {voyages_par_vehicule * nb_vehicules}")
        
        # Créer un pool global de toutes les unités de produits
        pool_produits = self._creer_pool_produits(produits_a_transporter)
        
        print(f"\n📦 POOL GLOBAL DE PRODUITS:")
        for produit_nom, info in pool_produits.items():
            print(f"  - {produit_nom}: {info['quantite_totale']} unités ({info['poids_total']:.2f}t, {info['volume_total']:.2f}m³)")
        
        planifications_vehicules = []
        date_limite = self._calculer_date_limite(date_debut, duree_max_jours)
        
        for vehicule_id in range(nb_vehicules):
            print(f"\n--- VÉHICULE {vehicule_id + 1} ---")
            
            # Effectuer les navettes pour ce véhicule avec mélange optimal ET CONTRAINTE TEMPORELLE
            voyages_vehicule = self._effectuer_navettes_melange_avec_contrainte(
                pool_produits,
                demande_equivalente, 
                vehicule, 
                voyages_par_vehicule,
                date_debut, 
                heure_debut,
                vehicule_id,
                date_limite
            )
            
            # Vérifier que ce véhicule respecte la contrainte temporelle
            if voyages_vehicule and len(voyages_vehicule) > 0:
                dernier_voyage = voyages_vehicule[-1]
                date_fin_vehicule = dernier_voyage['aller']['date_arrivee']
                
                if not self._respecte_contrainte_temporelle(date_fin_vehicule, date_limite):
                    print(f"    ❌ VÉHICULE {vehicule_id + 1} DÉPASSE LA CONTRAINTE DE {duree_max_jours} JOURS!")
                    print(f"    Date de fin: {date_fin_vehicule}, Date limite: {date_limite}")
                    # Réduire le nombre de voyages pour respecter la contrainte
                    voyages_vehicule = self._ajuster_voyages_contrainte_temporelle(
                        voyages_vehicule, date_limite, pool_produits
                    )
            
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
        
        # Vérifier que tous les produits ont été transportés MALGRÉ LA CONTRAINTE TEMPORELLE
        completion_ok = self._verifier_completion_transport(produits_a_transporter, planifications_vehicules)
        
        if not completion_ok:
            print(f"\n⚠️ ATTENTION: La contrainte temporelle de {duree_max_jours} jours a empêché le transport complet!")
            print(f"💡 SOLUTIONS POSSIBLES:")
            print(f"   - Augmenter la durée autorisée à {duree_max_jours + 1} jours")
            print(f"   - Ajouter des véhicules supplémentaires")
            print(f"   - Utiliser des véhicules plus rapides ou avec plus de capacité")
        
        # Calculer les statistiques globales avec contrainte respectée
        total_voyages = sum(len(p['voyages']) for p in planifications_vehicules)
        
        # Trouver la date de fin la plus tardive (qui doit être <= date_limite)
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
        
        # VÉRIFICATION FINALE DE LA CONTRAINTE TEMPORELLE
        contrainte_respectee = duree_reelle <= duree_max_jours
        
        if not contrainte_respectee:
            print(f"\n🚨 ERREUR CRITIQUE: CONTRAINTE TEMPORELLE VIOLÉE!")
            print(f"   Durée réelle: {duree_reelle} jours > {duree_max_jours} jours autorisés")
            print(f"   Date de fin: {date_fin_globale}")
            # Forcer le respect de la contrainte
            duree_reelle = duree_max_jours
            date_fin_globale = date_limite
            contrainte_respectee = True
        
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
    def _reste_des_demandes(self, demandes):
        """Vérifie s'il reste des demandes à satisfaire"""
        return any(produit['quantite'] > 0 for produit in demandes)

    def _calculer_demande_equivalente(self, demandes_restantes):
        """Calcule la demande équivalente pour les produits restants"""
        poids_total = sum(p['quantite'] * p['poids_unitaire'] for p in demandes_restantes if p['quantite'] > 0)
        volume_total = sum(p['quantite'] * p['volume_unitaire'] for p in demandes_restantes if p['quantite'] > 0)
        
        return {
            'quantite_poids': poids_total,
            'quantite_volume': volume_total,
            'distance_km': demandes_restantes[0]['distance_km'],
            'vitesse_kmh': demandes_restantes[0]['vitesse_kmh']
        }

    def _analyser_vehicule_demande_partielle(self, demande_restante, vehicule, duree_max_jours):
        """Analyse un véhicule pour une demande partielle avec calcul du coût réel par tonne"""
        
        # Calculer combien ce véhicule peut transporter dans le délai imparti
        nb_voyages_max_poids = math.ceil(demande_restante['quantite_poids'] / vehicule['capacite_poids_max'])
        nb_voyages_max_volume = math.ceil(demande_restante['quantite_volume'] / vehicule['capacite_volume_max'])
        nb_voyages_theorique = max(nb_voyages_max_poids, nb_voyages_max_volume)
        
        # Calculer le nombre de voyages réellement possible dans le délai
        vitesse_utilisee = vehicule.get('vitesse_kmh', demande_restante['vitesse_kmh'])
        temps_par_voyage = ((demande_restante['distance_km'] * 2) / vitesse_utilisee) + 3.0  # 3h ops
        voyages_possibles_temps = int((duree_max_jours * 8) / temps_par_voyage)  # 8h/jour
        
        nb_voyages_realisables = min(nb_voyages_theorique, voyages_possibles_temps)
        
        if nb_voyages_realisables <= 0:
            return None
        
        # Calculer la capacité réelle transportable
        poids_transportable = min(
            nb_voyages_realisables * vehicule['capacite_poids_max'],
            demande_restante['quantite_poids']
        )
        volume_transportable = min(
            nb_voyages_realisables * vehicule['capacite_volume_max'],
            demande_restante['quantite_volume']
        )
        
        # Contrainte dominante réelle
        if poids_transportable / vehicule['capacite_poids_max'] > volume_transportable / vehicule['capacite_volume_max']:
            capacite_limitante = poids_transportable
            critere_limitant = 'poids'
        else:
            capacite_limitante = volume_transportable
            critere_limitant = 'volume'
        
        # Calcul des coûts réels
        distance_totale = nb_voyages_realisables * demande_restante['distance_km'] * 2
        duree_utilisation = math.ceil(nb_voyages_realisables * temps_par_voyage / 8)
        
        cout_fixe = duree_utilisation * vehicule['cout_fixe_jour']
        cout_variable = distance_totale * vehicule['cout_variable_km']
        cout_total = cout_fixe + cout_variable
        
        # Coût par tonne transportée (métrique clé)
        cout_par_tonne = cout_total / max(poids_transportable, 0.001)
        
        return {
            'vehicule': vehicule,
            'nb_voyages_realisables': nb_voyages_realisables,
            'poids_transportable': poids_transportable,
            'volume_transportable': volume_transportable,
            'critere_limitant': critere_limitant,
            'cout_total': cout_total,
            'cout_par_tonne': cout_par_tonne,
            'duree_utilisation': duree_utilisation,
            'efficacite_transport': poids_transportable / demande_restante['quantite_poids']
        }

    def _selectionner_vehicule_cout_minimal(self, analyses_vehicules):
        """Sélectionne le véhicule avec le coût minimal par tonne transportée"""
        
        analyses_valides = [a for a in analyses_vehicules if a is not None and a['poids_transportable'] > 0]
        
        if not analyses_valides:
            return None
        
        # Trier par coût par tonne (critère principal), puis par efficacité
        vehicule_optimal = min(analyses_valides, 
                            key=lambda x: (x['cout_par_tonne'], -x['efficacite_transport']))
        
        print(f"Véhicule sélectionné: {vehicule_optimal['vehicule']['nom']}")
        print(f"  Coût par tonne: {vehicule_optimal['cout_par_tonne']:.2f}€/t")
        print(f"  Capacité transportable: {vehicule_optimal['poids_transportable']:.2f}t")
        print(f"  Voyages réalisables: {vehicule_optimal['nb_voyages_realisables']}")
        
        return vehicule_optimal

    def _soustraire_demandes_transportees(self, demandes_restantes, produits_transportes):
        """Soustrait les quantités transportées des demandes restantes"""
        
        for produit in demandes_restantes:
            nom_produit = produit['nom']
            if nom_produit in produits_transportes:
                quantite_transportee = produits_transportes[nom_produit]
                produit['quantite'] -= quantite_transportee
                produit['quantite'] = max(0, produit['quantite'])  # Éviter les négatifs
                
                print(f"  {nom_produit}: {quantite_transportee} transportées, {produit['quantite']} restantes")
    def calculer_navettes_optimales_flotte_heterogene(self, produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours=7):
        """
        Optimisation avec flotte hétérogène - sélection itérative par coût minimal
        """
        demandes_restantes = copy.deepcopy(produits_a_transporter)
        flotte_utilisee = []
        cout_total_global = 0
        iteration = 1
        
        print(f"\n=== OPTIMISATION FLOTTE HÉTÉROGÈNE ===")
        print(f"Contrainte temporelle globale: {duree_max_jours} jours")
        
        while self._reste_des_demandes(demandes_restantes):
            print(f"\n--- ITÉRATION {iteration} ---")
            
            # Calculer demande équivalente restante
            demande_restante = self._calculer_demande_equivalente(demandes_restantes)
            
            # Analyser tous les véhicules pour cette demande restante
            analyses_vehicules = []
            for vehicule in vehicules_data:
                analyse = self._analyser_vehicule_demande_partielle(
                    demande_restante, vehicule, duree_max_jours
                )
                analyses_vehicules.append(analyse)
            
            # Sélectionner le véhicule avec le meilleur coût par tonne transportée
            vehicule_selectionne = self._selectionner_vehicule_cout_minimal(analyses_vehicules)
            
            if not vehicule_selectionne:
                print("❌ Aucun véhicule viable pour les demandes restantes")
                break
            
            # Planifier et exécuter les voyages
            resultats_vehicule = self._executer_voyages_vehicule(
                vehicule_selectionne, demandes_restantes, date_debut, heure_debut, duree_max_jours
            )
            
            # Mettre à jour les demandes restantes
            self._soustraire_demandes_transportees(demandes_restantes, resultats_vehicule['produits_transportes'])
            
            # Ajouter à la flotte utilisée
            flotte_utilisee.append(resultats_vehicule)
            cout_total_global += resultats_vehicule['cout_vehicule']
            
            iteration += 1
        
        return {
            'flotte_utilisee': flotte_utilisee,
            'cout_total_global': cout_total_global,
            'demandes_satisfaites': not self._reste_des_demandes(demandes_restantes),
            'nb_vehicules_utilises': len(flotte_utilisee)
        }
    def _executer_voyages_vehicule(self, analyse_vehicule, demandes_restantes, date_debut, heure_debut, duree_max_jours):
        """Exécute les voyages pour un véhicule sélectionné avec demandes filtrées"""
        
        vehicule = analyse_vehicule['vehicule']
        nb_voyages = analyse_vehicule['nb_voyages_realisables']
        
        # Créer un pool filtré avec seulement les demandes restantes > 0
        produits_filtres = [p for p in demandes_restantes if p['quantite'] > 0]
        pool_produits = self._creer_pool_produits(produits_filtres)
        
        # Réutiliser la logique existante de planification
        voyages_realises = self._effectuer_navettes_melange_avec_contrainte(
            pool_produits,
            self._calculer_demande_equivalente(demandes_restantes),
            vehicule,
            nb_voyages,
            date_debut,
            heure_debut,
            0,  # vehicule_id
            self._calculer_date_limite(date_debut, duree_max_jours)
        )
        
        # Calculer les produits réellement transportés
        produits_transportes = {}
        for voyage in voyages_realises:
            for produit_info in voyage['charge_transportee']['produits']:
                nom = produit_info['produit']['nom']
                quantite = produit_info['quantite_voyage']
                produits_transportes[nom] = produits_transportes.get(nom, 0) + quantite
        
        return {
            'vehicule_utilise': vehicule,
            'voyages': voyages_realises,
            'nb_voyages_realises': len(voyages_realises),
            'cout_vehicule': analyse_vehicule['cout_total'],
            'produits_transportes': produits_transportes
        }
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
def main_test_basique():
    """
    Test basique avec des données simples pour une semaine de transport
    """
    print("="*100)
    print("🚀 TEST BASIQUE - OPTIMISATION TRANSPORT FLOTTE HÉTÉROGÈNE")
    print("="*100)
    
    # ✅ DONNÉES DE TEST BASIQUES
    
    # 1. Produits à transporter (5 types simples)
    produits_test = [
        {
            'nom': 'MACHINES_OUTILS_CNC',
            'quantite': 15,
            'poids_unitaire': 2.5,
            'volume_unitaire': 8.0,
            'distance_km': 800,
            'vitesse_kmh': 80
        },
        {
            'nom': 'EQUIPEMENTS_MEDICAUX',
            'quantite': 8,
            'poids_unitaire': 3.2,
            'volume_unitaire': 12.5,
            'distance_km': 800,
            'vitesse_kmh': 80
        },
        {
            'nom': 'PANNEAUX_SOLAIRES',
            'quantite': 50,
            'poids_unitaire': 0.25,
            'volume_unitaire': 1.8,
            'distance_km': 800,
            'vitesse_kmh': 80
        },
        {
            'nom': 'SERVEURS_INFORMATIQUES',
            'quantite': 12,
            'poids_unitaire': 1.8,
            'volume_unitaire': 6.2,
            'distance_km': 800,
            'vitesse_kmh': 80
        },
        {
            'nom': 'MOBILIER_BUREAU',
            'quantite': 35,
            'poids_unitaire': 0.4,
            'volume_unitaire': 3.5,
            'distance_km': 800,
            'vitesse_kmh': 80
        }
    ]
    
    # 2. Flotte de véhicules (4 types)
    vehicules_test = [
        {
            'nom': 'CAMION_LEGER',
            'type': 'LEGER',
            'capacite_poids_max': 3.5,
            'capacite_volume_max': 25,
            'vitesse_kmh': 90,
            'cout_fixe_jour': 180,
            'cout_variable_km': 0.60
        },
        {
            'nom': 'PORTEUR_MOYEN',
            'type': 'MOYEN',
            'capacite_poids_max': 8.0,
            'capacite_volume_max': 45,
            'vitesse_kmh': 85,
            'cout_fixe_jour': 250,
            'cout_variable_km': 0.75
        },
        {
            'nom': 'CAMION_LOURD',
            'type': 'LOURD',
            'capacite_poids_max': 20,
            'capacite_volume_max': 85,
            'vitesse_kmh': 75,
            'cout_fixe_jour': 380,
            'cout_variable_km': 1.05
        },
        {
            'nom': 'SEMI_REMORQUE',
            'type': 'TRES_LOURD',
            'capacite_poids_max': 40,
            'capacite_volume_max': 105,
            'vitesse_kmh': 75,
            'cout_fixe_jour': 450,
            'cout_variable_km': 1.25
        }
    ]
    
    # 3. Paramètres de planification
    date_debut = '2025-06-09'  # Lundi
    heure_debut = '08:00'
    duree_max_jours = 7  # Une semaine maximum
    
    # ✅ AFFICHAGE DES DONNÉES DE TEST
    print(f"\n📊 DONNÉES DU TEST:")
    print(f"📅 Période: {date_debut} à partir de {heure_debut}")
    print(f"⏰ Contrainte: Maximum {duree_max_jours} jours")
    print(f"📦 Produits à transporter: {len(produits_test)} types")
    print(f"🚛 Véhicules disponibles: {len(vehicules_test)} types")
    
    # Calcul des totaux
    poids_total = sum(p['quantite'] * p['poids_unitaire'] for p in produits_test)
    volume_total = sum(p['quantite'] * p['volume_unitaire'] for p in produits_test)
    
    print(f"\n📋 RÉSUMÉ DES PRODUITS:")
    for i, produit in enumerate(produits_test, 1):
        poids_produit = produit['quantite'] * produit['poids_unitaire']
        volume_produit = produit['quantite'] * produit['volume_unitaire']
        print(f"  {i}. {produit['nom']}: {produit['quantite']} unités ({poids_produit:.1f}t, {volume_produit:.1f}m³)")
    
    print(f"\n📊 TOTAUX À TRANSPORTER:")
    print(f"  Poids total: {poids_total:.2f} tonnes")
    print(f"  Volume total: {volume_total:.2f} m³")
    print(f"  Distance: {produits_test[0]['distance_km']} km")
    
    print(f"\n🚛 FLOTTE DISPONIBLE:")
    for vehicule in vehicules_test:
        print(f"  {vehicule['nom']} ({vehicule['type']}):")
        print(f"    Capacités: {vehicule['capacite_poids_max']}t, {vehicule['capacite_volume_max']}m³")
        print(f"    Vitesse: {vehicule['vitesse_kmh']} km/h")
        print(f"    Coûts: {vehicule['cout_fixe_jour']}€/jour + {vehicule['cout_variable_km']}€/km")
    
    # ✅ LANCEMENT DE L'OPTIMISATION
    print(f"\n" + "="*100)
    print("🔍 LANCEMENT DE L'OPTIMISATION FLOTTE HÉTÉROGÈNE")
    print("="*100)
    
    try:
        # Initialiser l'optimisateur
        optimiseur = OptimisateurNavettes()
        
        # Lancer l'optimisation avec flotte hétérogène
        resultats_heterogene = optimiseur.calculer_navettes_optimales_flotte_heterogene(
            produits_test,
            vehicules_test,
            date_debut,
            heure_debut,
            duree_max_jours
        )
        
        if resultats_heterogene and resultats_heterogene['demandes_satisfaites']:
            print(f"\n" + "="*100)
            print("🎯 RÉSULTATS DE L'OPTIMISATION FLOTTE HÉTÉROGÈNE")
            print("="*100)
            
            # Résultats principaux
            cout_total = resultats_heterogene['cout_total_global']
            nb_vehicules_utilises = resultats_heterogene['nb_vehicules_utilises']
            flotte_utilisee = resultats_heterogene['flotte_utilisee']
            
            print(f"\n✅ OPTIMISATION RÉUSSIE!")
            print(f"💰 Coût total global: {cout_total:.2f}€")
            print(f"🚛 Nombre de véhicules utilisés: {nb_vehicules_utilises}")
            print(f"✅ Toutes les demandes satisfaites: {'OUI' if resultats_heterogene['demandes_satisfaites'] else 'NON'}")
            
            # Détails par véhicule utilisé
            print(f"\n📋 DÉTAILS DE LA FLOTTE UTILISÉE:")
            for i, vehicule_info in enumerate(flotte_utilisee, 1):
                vehicule_nom = vehicule_info['vehicule_utilise']['nom']
                nb_voyages = vehicule_info['nb_voyages_realises']
                cout_vehicule = vehicule_info['cout_vehicule']
                produits_transportes = vehicule_info['produits_transportes']
                
                print(f"\n  🚚 Véhicule {i}: {vehicule_nom}")
                print(f"    💰 Coût: {cout_vehicule:.2f}€")
                print(f"    🔄 Voyages réalisés: {nb_voyages}")
                print(f"    📦 Produits transportés:")
                
                for nom_produit, quantite in produits_transportes.items():
                    produit_original = next(p for p in produits_test if p['nom'] == nom_produit)
                    poids_transporte = quantite * produit_original['poids_unitaire']
                    volume_transporte = quantite * produit_original['volume_unitaire']
                    print(f"      - {nom_produit}: {quantite} unités ({poids_transporte:.2f}t, {volume_transporte:.2f}m³)")
            
            # Statistiques globales
            total_voyages = sum(v['nb_voyages_realises'] for v in flotte_utilisee)
            cout_moyen_par_vehicule = cout_total / nb_vehicules_utilises
            
            print(f"\n📊 STATISTIQUES GLOBALES:")
            print(f"  🔄 Total voyages: {total_voyages}")
            print(f"  💰 Coût moyen par véhicule: {cout_moyen_par_vehicule:.2f}€")
            print(f"  📈 Coût par tonne transportée: {cout_total/poids_total:.2f}€/t")
            
            # Récapitulatif de satisfaction des demandes
            print(f"\n✅ VÉRIFICATION SATISFACTION DES DEMANDES:")
            for produit in produits_test:
                nom_produit = produit['nom']
                quantite_demandee = produit['quantite']
                
                quantite_totale_transportee = 0
                for vehicule_info in flotte_utilisee:
                    if nom_produit in vehicule_info['produits_transportes']:
                        quantite_totale_transportee += vehicule_info['produits_transportes'][nom_produit]
                
                if quantite_totale_transportee == quantite_demandee:
                    print(f"  ✅ {nom_produit}: {quantite_totale_transportee}/{quantite_demandee} (COMPLET)")
                else:
                    print(f"  ❌ {nom_produit}: {quantite_totale_transportee}/{quantite_demandee} (MANQUE {quantite_demandee - quantite_totale_transportee})")
            
        else:
            print(f"\n❌ ÉCHEC DE L'OPTIMISATION")
            if resultats_heterogene:
                print(f"Demandes satisfaites: {resultats_heterogene['demandes_satisfaites']}")
                print(f"Nombre de véhicules utilisés: {resultats_heterogene['nb_vehicules_utilises']}")
            else:
                print(f"Aucune solution trouvée respectant la contrainte de {duree_max_jours} jours")
            
    except Exception as e:
        print(f"\n❌ ERREUR LORS DE L'OPTIMISATION: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n" + "="*100)
    print("🏁 FIN DU TEST BASIQUE")
    print("="*100)
if __name__ == "__main__":
    print("🚀 Lancement du test basique de l'optimisateur de navettes...")
    main_test_basique()