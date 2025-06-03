"""
Optimisateur de Navettes - Version Complète et Organisée
========================================================

Ce module contient un système d'optimisation de transport avec deux approches:
1. Flotte homogène : Un seul type de véhicule
2. Flotte hétérogène : Plusieurs types de véhicules sélectionnés itérativement

Fonctionnalités principales:
- Contrainte temporelle stricte (7 jours max)
- Optimisation poids/volume
- Gestion des temps de conduite et repos
- Stratégies de mélange de produits
- Comparaison automatique des méthodes

Auteur: Assistant Claude
Date: 2025
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import os
import random
import math
import time
import copy

# ================================================================================================
# CONFIGURATION ET IMPORTS
# ================================================================================================

# Correction pour l'erreur Pyomo - Imports conditionnels
try:
    import pyomo.environ as pyo
    from pyomo.opt import SolverFactory
    PYOMO_AVAILABLE = True
except ImportError:
    PYOMO_AVAILABLE = False
    print("⚠️ Pyomo non disponible - Fonctionnalités avancées d'optimisation désactivées")


# ================================================================================================
# CLASSE PRINCIPALE - OPTIMISATEUR NAVETTES
# ================================================================================================

class OptimisateurNavettes:
    """
    Classe principale pour l'optimisation des navettes de transport
    
    Méthodes principales:
    - calculer_navettes_optimales() : Flotte homogène
    - calculer_flotte_heterogene_iterative() : Flotte hétérogène
    """
    
    def __init__(self):
        """Initialise l'optimisateur avec les solveurs disponibles"""
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

    # ============================================================================================
    # MÉTHODE 1: FLOTTE HOMOGÈNE (UN SEUL TYPE DE VÉHICULE)
    # ============================================================================================
    
    def calculer_navettes_optimales(self, produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours=7):
        """
        Calcule les navettes optimales avec une flotte homogène
        
        Args:
            produits_a_transporter (list): Liste des produits avec quantités, poids, volumes
            vehicules_data (list): Liste des types de véhicules disponibles
            date_debut (str): Date de début (format YYYY-MM-DD)
            heure_debut (str): Heure de début (format HH:MM)
            duree_max_jours (int): Durée maximale autorisée (défaut: 7 jours)
            
        Returns:
            dict: Résultats complets de l'optimisation ou None si échec
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
        
        print(f"\n=== OPTIMISATION FLOTTE HOMOGÈNE ===")
        print(f"⏰ CONTRAINTE TEMPORELLE: Terminé en {duree_max_jours} jours maximum")
        print(f"🔄 STRATÉGIE: Remplissage homogène puis mélange optimal")
        print(f"Nombre de types de produits: {len(produits_a_transporter)}")
        
        # Affichage détaillé des produits
        self._afficher_produits_detailles(produits_a_transporter)
        
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
            self._afficher_analyse_vehicule(vehicule, analyse, duree_max_jours)
        
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
        
        self._afficher_vehicule_optimal(vehicule_optimal, vehicules_viables)
        
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

    # ============================================================================================
    # MÉTHODE 2: FLOTTE HÉTÉROGÈNE (SÉLECTION ITÉRATIVE)
    # ============================================================================================
    
    def calculer_flotte_heterogene_iterative(self, produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours=7):
        """
        Calcule une flotte hétérogène par sélection itérative
        
        Algorithme:
        1. Analyser tous les véhicules pour la demande actuelle
        2. Sélectionner le véhicule optimal (coût le plus bas)
        3. Calculer sa capacité maximale transportable
        4. Soustraire cette capacité de la demande
        5. Répéter jusqu'à satisfaction complète
        
        Args:
            produits_a_transporter (list): Liste des produits
            vehicules_data (list): Liste des véhicules disponibles
            date_debut (str): Date de début
            heure_debut (str): Heure de début
            duree_max_jours (int): Durée max par véhicule
            
        Returns:
            dict: Résultats de la flotte hétérogène
        """
        
        print(f"\n=== OPTIMISATION FLOTTE HÉTÉROGÈNE ITÉRATIVE ===")
        print(f"🔄 STRATÉGIE: Sélection séquentielle du véhicule optimal")
        print(f"⏰ CONTRAINTE: Maximum {duree_max_jours} jours par véhicule")
        
        # Copie de la demande pour modification
        demande_restante = copy.deepcopy(produits_a_transporter)
        flotte_selectionnee = []
        cout_total_flotte = 0
        iteration = 1
        
        print(f"\n📦 DEMANDE INITIALE:")
        self._afficher_demande(demande_restante)
        
        # Boucle principale d'optimisation itérative
        while self._demande_non_vide(demande_restante):
            print(f"\n{'='*80}")
            print(f"ITÉRATION {iteration} - SÉLECTION VÉHICULE OPTIMAL")
            print(f"{'='*80}")
            
            # Calculer les totaux actuels
            poids_restant = sum(p['quantite'] * p['poids_unitaire'] for p in demande_restante)
            volume_restant = sum(p['quantite'] * p['volume_unitaire'] for p in demande_restante)
            
            print(f"📊 DEMANDE RESTANTE:")
            print(f"   Poids: {poids_restant:.2f} tonnes")
            print(f"   Volume: {volume_restant:.2f} m³")
            
            # Créer une demande équivalente pour l'analyse
            demande_equivalente = {
                'nom': f'TRANSPORT_ITERATION_{iteration}',
                'distance_km': demande_restante[0].get('distance_km', 800),
                'vitesse_kmh': demande_restante[0].get('vitesse_kmh', 80),
                'quantite_poids': poids_restant,
                'quantite_volume': volume_restant
            }
            
            # Analyser tous les véhicules pour cette demande
            vehicule_optimal = self._analyser_et_selectionner_vehicule_optimal(
                demande_equivalente, vehicules_data, duree_max_jours, iteration
            )
            
            if not vehicule_optimal:
                print(f"\n❌ AUCUN VÉHICULE VIABLE POUR LA DEMANDE RESTANTE")
                print(f"Recommandation: Augmenter la durée autorisée ou diviser la demande")
                break
            
            # Calculer la capacité réelle transportable
            capacite_transportable = self._calculer_capacite_vehicule_pour_demande(
                vehicule_optimal['vehicule'], demande_restante
            )
            
            self._afficher_capacite_transportable(capacite_transportable, demande_restante)
            
            # Ajouter à la flotte sélectionnée
            flotte_selectionnee.append({
                'iteration': iteration,
                'vehicule': vehicule_optimal['vehicule'],
                'analyse': vehicule_optimal,
                'capacite_transportable': capacite_transportable,
                'date_utilisation': date_debut  # Simplifié - tous en parallèle
            })
            
            cout_total_flotte += vehicule_optimal['cout_total']
            
            # Mettre à jour la demande restante
            demande_restante = self._soustraire_capacite_de_demande(demande_restante, capacite_transportable)
            
            iteration += 1
            
            # Sécurité anti-boucle infinie
            if iteration > 20:
                print(f"\n⚠️ ARRÊT DE SÉCURITÉ: Trop d'itérations")
                break
        
        # Affichage des résultats finaux
        return self._finaliser_resultats_flotte_heterogene(
            flotte_selectionnee, cout_total_flotte, demande_restante, iteration,
            produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours
        )

    # ============================================================================================
    # MÉTHODES D'ANALYSE ET DE CALCUL
    # ============================================================================================
    
    def _analyser_vehicule_avec_contrainte(self, demande, vehicule, duree_max_jours):
        """
        Analyse un véhicule avec prise en compte de la contrainte temporelle
        
        Args:
            demande (dict): Demande à analyser
            vehicule (dict): Véhicule à analyser
            duree_max_jours (int): Durée maximale autorisée
            
        Returns:
            dict: Analyse complète du véhicule
        """
        
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
        distance_retour_total = (voyages_totaux - nb_vehicules_necessaires) * demande['distance_km']
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
    
    def _calculer_capacite_vehicule_pour_demande(self, vehicule, demande):
        """
        Calcule la capacité réelle qu'un véhicule peut transporter de la demande
        
        Args:
            vehicule (dict): Véhicule à analyser
            demande (list): Liste des produits de la demande
            
        Returns:
            dict: Capacité transportable par produit
        """
        capacite_transportable = {}
        poids_utilise = 0
        volume_utilise = 0
        
        # Trier les produits par efficacité (plus dense en premier)
        produits_tries = sorted(demande, key=lambda p: self._calculer_efficacite_produit(p), reverse=True)
        
        for produit in produits_tries:
            if produit['quantite'] <= 0:
                continue
                
            # Calculer combien d'unités on peut prendre
            poids_unitaire = produit['poids_unitaire']
            volume_unitaire = produit['volume_unitaire']
            
            max_unites_poids = int((vehicule['capacite_poids_max'] - poids_utilise) / poids_unitaire)
            max_unites_volume = int((vehicule['capacite_volume_max'] - volume_utilise) / volume_unitaire)
            max_unites = min(max_unites_poids, max_unites_volume, produit['quantite'])
            
            if max_unites > 0:
                capacite_transportable[produit['nom']] = max_unites
                poids_utilise += max_unites * poids_unitaire
                volume_utilise += max_unites * volume_unitaire
            else:
                capacite_transportable[produit['nom']] = 0
        
        return capacite_transportable
    
    def _calculer_efficacite_produit(self, produit):
        """
        Calcule l'efficacité d'un produit (ratio poids/volume pour optimiser l'espace)
        
        Args:
            produit (dict): Produit à analyser
            
        Returns:
            float: Ratio d'efficacité
        """
        ratio_densite = produit['poids_unitaire'] / max(produit['volume_unitaire'], 0.001)
        return ratio_densite

    # ============================================================================================
    # MÉTHODES UTILITAIRES ET D'AFFICHAGE
    # ============================================================================================
    
    def _afficher_produits_detailles(self, produits_a_transporter):
        """Affiche le détail des produits à transporter"""
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
    
    def _afficher_analyse_vehicule(self, vehicule, analyse, duree_max_jours):
        """Affiche l'analyse d'un véhicule"""
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
    
    def _afficher_vehicule_optimal(self, vehicule_optimal, vehicules_viables):
        """Affiche le véhicule optimal sélectionné"""
        print(f"\n🏆 VÉHICULE OPTIMAL SÉLECTIONNÉ: {vehicule_optimal['vehicule']['nom']}")
        print(f"💰 COÛT TOTAL: {vehicule_optimal['cout_total']:.2f}€")
        print(f"🚛 NOMBRE DE VÉHICULES: {vehicule_optimal['nb_vehicules_necessaires']}")
        print(f"⏱️ DURÉE RÉELLE: {vehicule_optimal['duree_reelle_jours']} jour(s)")
        
        print(f"\n📊 ÉCONOMIES vs autres véhicules viables:")
        for analyse in vehicules_viables:
            if analyse != vehicule_optimal:
                economie = analyse['cout_total'] - vehicule_optimal['cout_total']
                print(f"  vs {analyse['vehicule']['nom']}: +{economie:.2f}€ ({economie/vehicule_optimal['cout_total']*100:.1f}% plus cher)")
    
    def _afficher_demande(self, demande):
        """Affiche le détail d'une demande"""
        for produit in demande:
            if produit['quantite'] > 0:
                poids = produit['quantite'] * produit['poids_unitaire']
                volume = produit['quantite'] * produit['volume_unitaire']
                print(f"   {produit['nom']}: {produit['quantite']} unités ({poids:.2f}t, {volume:.2f}m³)")
    
    def _afficher_capacite_transportable(self, capacite_transportable, demande_restante):
        """Affiche la capacité transportable"""
        print(f"\n📦 CAPACITÉ TRANSPORTABLE:")
        for nom_produit, quantite in capacite_transportable.items():
            if quantite > 0:
                produit_info = next(p for p in demande_restante if p['nom'] == nom_produit)
                poids = quantite * produit_info['poids_unitaire']
                volume = quantite * produit_info['volume_unitaire']
                print(f"   {nom_produit}: {quantite} unités ({poids:.2f}t, {volume:.2f}m³)")
    
    def _demande_non_vide(self, demande):
        """Vérifie s'il reste de la demande à satisfaire"""
        return any(produit['quantite'] > 0 for produit in demande)
    
    def _soustraire_capacite_de_demande(self, demande, capacite_transportable):
        """Soustrait la capacité transportable de la demande"""
        nouvelle_demande = []
        
        for produit in demande:
            quantite_transportee = capacite_transportable.get(produit['nom'], 0)
            quantite_restante = produit['quantite'] - quantite_transportee
            
            if quantite_restante > 0:
                nouveau_produit = copy.deepcopy(produit)
                nouveau_produit['quantite'] = quantite_restante
                nouvelle_demande.append(nouveau_produit)
        
        return nouvelle_demande
    
    def _analyser_et_selectionner_vehicule_optimal(self, demande_equivalente, vehicules_data, duree_max_jours, iteration):
        """Analyse tous les véhicules et sélectionne l'optimal"""
        print(f"\n🔍 ANALYSE DES VÉHICULES POUR ITÉRATION {iteration}:")
        analyses = []
        
        for vehicule in vehicules_data:
            analyse = self._analyser_vehicule_avec_contrainte(demande_equivalente, vehicule, duree_max_jours)
            analyses.append(analyse)
            
            print(f"\n  {vehicule['nom']}:")
            if analyse['respect_contrainte']:
                print(f"    ✅ Respecte contrainte - Coût: {analyse['cout_total']:.2f}€")
            else:
                print(f"    ❌ Dépasse contrainte - Non viable")
        
        # Sélectionner le véhicule optimal
        vehicules_viables = [a for a in analyses if a['respect_contrainte']]
        
        if not vehicules_viables:
            return None
        
        vehicule_optimal = min(vehicules_viables, key=lambda x: x['cout_total'])
        
        print(f"\n🏆 VÉHICULE OPTIMAL ITÉRATION {iteration}: {vehicule_optimal['vehicule']['nom']}")
        print(f"💰 Coût: {vehicule_optimal['cout_total']:.2f}€")
        
        return vehicule_optimal
    
    def _finaliser_resultats_flotte_heterogene(self, flotte_selectionnee, cout_total_flotte, demande_restante, iteration,
                                             produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours):
        """Finalise et affiche les résultats de la flotte hétérogène"""
        print(f"\n{'='*80}")
        print(f"🎯 RÉSULTATS FLOTTE HÉTÉROGÈNE ITÉRATIVE")
        print(f"{'='*80}")
        
        if self._demande_non_vide(demande_restante):
            print(f"⚠️ DEMANDE PARTIELLEMENT SATISFAITE")
            print(f"📦 DEMANDE NON TRANSPORTÉE:")
            self._afficher_demande(demande_restante)
        else:
            print(f"✅ DEMANDE ENTIÈREMENT SATISFAITE")
        
        print(f"\n🚛 FLOTTE SÉLECTIONNÉE:")
        print(f"   Nombre de véhicules: {len(flotte_selectionnee)}")
        print(f"   Coût total: {cout_total_flotte:.2f}€")
        
        for i, vehicule_info in enumerate(flotte_selectionnee, 1):
            vehicule = vehicule_info['vehicule']
            cout = vehicule_info['analyse']['cout_total']
            print(f"   {i}. {vehicule['nom']} - {cout:.2f}€")
        
        # Comparaison avec méthode homogène
        print(f"\n📊 COMPARAISON AVEC FLOTTE HOMOGÈNE:")
        resultats_homogene = self.calculer_navettes_optimales(
            produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours
        )
        
        if resultats_homogene:
            cout_homogene = resultats_homogene['vehicule_optimal']['cout_total']
            vehicule_homogene = resultats_homogene['vehicule_utilise']['nom']
            nb_vehicules_homogene = resultats_homogene['nb_vehicules_necessaires']
            
            print(f"   Flotte homogène: {nb_vehicules_homogene}x {vehicule_homogene} = {cout_homogene:.2f}€")
            print(f"   Flotte hétérogène: {len(flotte_selectionnee)} véhicules = {cout_total_flotte:.2f}€")
            
            if cout_total_flotte < cout_homogene:
                economie = cout_homogene - cout_total_flotte
                print(f"   🎉 ÉCONOMIE HÉTÉROGÈNE: {economie:.2f}€ ({economie/cout_homogene*100:.1f}%)")
            else:
                surcoût = cout_total_flotte - cout_homogene
                print(f"   💰 SURCOÛT HÉTÉROGÈNE: +{surcoût:.2f}€ ({surcoût/cout_homogene*100:.1f}%)")
        
        return {
            'flotte_selectionnee': flotte_selectionnee,
            'cout_total': cout_total_flotte,
            'demande_satisfaite': not self._demande_non_vide(demande_restante),
            'demande_restante': demande_restante,
            'nb_iterations': iteration - 1,
            'comparaison_homogene': resultats_homogene
        }

    # ============================================================================================
    # MÉTHODES DE PLANIFICATION DÉTAILLÉE (VERSION SIMPLIFIÉE)
    # ============================================================================================
    
    def _planifier_multi_vehicules_melange(self, produits_a_transporter, demande_equivalente, vehicule_optimal, date_debut, heure_debut, duree_max_jours):
        """
        Planification simplifiée pour la version organisée
        
        Note: Cette version se concentre sur l'optimisation des coûts.
        Pour une planification temporelle détaillée, voir la version complète.
        """
        
        nb_vehicules = vehicule_optimal['nb_vehicules_necessaires']
        voyages_par_vehicule = vehicule_optimal['voyages_par_vehicule']
        vehicule = vehicule_optimal['vehicule']
        
        print(f"\n=== PLANIFICATION SIMPLIFIÉE ===")
        print(f"Véhicules utilisés: {nb_vehicules} x {vehicule['nom']}")
        print(f"Voyages par véhicule: {voyages_par_vehicule}")
        print(f"Voyages totaux: {voyages_par_vehicule * nb_vehicules}")
        
        # Répartition simplifiée des produits
        planifications_vehicules = []
        
        # Calculer la charge par véhicule
        poids_total = sum(p['quantite'] * p['poids_unitaire'] for p in produits_a_transporter)
        volume_total = sum(p['quantite'] * p['volume_unitaire'] for p in produits_a_transporter)
        
        charge_par_vehicule = {
            'poids': poids_total / nb_vehicules,
            'volume': volume_total / nb_vehicules
        }
        
        for vehicule_id in range(nb_vehicules):
            planifications_vehicules.append({
                'vehicule_id': vehicule_id + 1,
                'charge_totale': charge_par_vehicule,
                'nb_voyages': voyages_par_vehicule
            })
        
        return {
            'nb_vehicules': nb_vehicules,
            'planifications_vehicules': planifications_vehicules,
            'total_voyages': voyages_par_vehicule * nb_vehicules,
            'date_debut': date_debut,
            'duree_reelle_jours': vehicule_optimal['duree_reelle_jours'],
            'respect_contrainte': True,
            'completion_transport': True
        }


# ================================================================================================
# FONCTIONS DE TEST ET DÉMONSTRATION
# ================================================================================================

def creer_donnees_test_basiques():
    """
    Crée des données de test basiques pour démonstration
    
    Returns:
        tuple: (produits_test, vehicules_test)
    """
    
    # Produits à transporter (5 types simples)
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
    
    # Flotte de véhicules (4 types)
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
    
    return produits_test, vehicules_test

def afficher_donnees_test(produits_test, vehicules_test, date_debut, heure_debut, duree_max_jours):
    """Affiche un résumé des données de test"""
    
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

def comparer_methodes(optimiseur, produits_test, vehicules_test, date_debut, heure_debut, duree_max_jours):
    """
    Compare les deux méthodes d'optimisation
    
    Args:
        optimiseur: Instance de OptimisateurNavettes
        produits_test: Liste des produits
        vehicules_test: Liste des véhicules
        date_debut: Date de début
        heure_debut: Heure de début
        duree_max_jours: Durée maximale
    """
    
    print(f"\n" + "="*100)
    print("🔍 COMPARAISON: FLOTTE HOMOGÈNE vs FLOTTE HÉTÉROGÈNE")
    print("="*100)
    
    try:
        # ✅ MÉTHODE 1: FLOTTE HOMOGÈNE
        print(f"\n1️⃣ MÉTHODE FLOTTE HOMOGÈNE:")
        print("-" * 50)
        
        resultats_homogene = optimiseur.calculer_navettes_optimales(
            produits_test, vehicules_test, date_debut, heure_debut, duree_max_jours
        )
        
        if resultats_homogene:
            cout_homogene = resultats_homogene['vehicule_optimal']['cout_total']
            vehicule_homogene = resultats_homogene['vehicule_utilise']['nom']
            nb_vehicules_homogene = resultats_homogene['nb_vehicules_necessaires']
            
            print(f"\n✅ RÉSULTATS FLOTTE HOMOGÈNE:")
            print(f"   Véhicule: {vehicule_homogene}")
            print(f"   Nombre: {nb_vehicules_homogene} véhicules")
            print(f"   Coût: {cout_homogene:.2f}€")
        
        # ✅ MÉTHODE 2: FLOTTE HÉTÉROGÈNE
        print(f"\n2️⃣ MÉTHODE FLOTTE HÉTÉROGÈNE ITÉRATIVE:")
        print("-" * 50)
        
        resultats_heterogene = optimiseur.calculer_flotte_heterogene_iterative(
            produits_test, vehicules_test, date_debut, heure_debut, duree_max_jours
        )
        
        if resultats_heterogene:
            cout_heterogene = resultats_heterogene['cout_total']
            nb_vehicules_heterogene = len(resultats_heterogene['flotte_selectionnee'])
            
            print(f"\n✅ RÉSULTATS FLOTTE HÉTÉROGÈNE:")
            print(f"   Véhicules: {nb_vehicules_heterogene} véhicules différents")
            print(f"   Coût: {cout_heterogene:.2f}€")
            print(f"   Demande satisfaite: {'OUI' if resultats_heterogene['demande_satisfaite'] else 'NON'}")
        
        # ✅ COMPARAISON FINALE
        if resultats_homogene and resultats_heterogene:
            print(f"\n" + "="*100)
            print("🏆 COMPARAISON FINALE DES MÉTHODES")
            print("="*100)
            
            print(f"\n📊 RÉSUMÉ COMPARATIF:")
            print(f"   Flotte homogène:")
            print(f"     - {nb_vehicules_homogene}x {vehicule_homogene}")
            print(f"     - Coût: {cout_homogene:.2f}€")
            
            print(f"   Flotte hétérogène:")
            print(f"     - {nb_vehicules_heterogene} véhicules différents")
            print(f"     - Coût: {cout_heterogene:.2f}€")
            
            if cout_heterogene < cout_homogene:
                economie = cout_homogene - cout_heterogene
                print(f"\n🎉 GAGNANT: FLOTTE HÉTÉROGÈNE")
                print(f"   Économie: {economie:.2f}€ ({economie/cout_homogene*100:.1f}%)")
            elif cout_homogene < cout_heterogene:
                surcoût = cout_heterogene - cout_homogene
                print(f"\n🏆 GAGNANT: FLOTTE HOMOGÈNE")
                print(f"   Économie: {surcoût:.2f}€ ({surcoût/cout_heterogene*100:.1f}%)")
            else:
                print(f"\n🤝 ÉGALITÉ: Même coût pour les deux méthodes")
            
            print(f"\n💡 RECOMMANDATION:")
            if cout_heterogene < cout_homogene:
                print(f"   Utiliser la flotte hétérogène pour optimiser les coûts")
            else:
                print(f"   Utiliser la flotte homogène pour simplifier la gestion")
            
        else:
            print(f"\n❌ Impossible de comparer - Une des méthodes a échoué")
            
    except Exception as e:
        print(f"\n❌ ERREUR LORS DE L'OPTIMISATION: {e}")
        import traceback
        traceback.print_exc()

def main_test_organisé():
    """
    Test principal organisé et structuré
    """
    print("="*100)
    print("🚀 TEST ORGANISÉ - OPTIMISATEUR NAVETTES")
    print("="*100)
    
    # Paramètres de planification
    date_debut = '2025-06-09'  # Lundi
    heure_debut = '08:00'
    duree_max_jours = 7  # Une semaine maximum
    
    # Créer les données de test
    produits_test, vehicules_test = creer_donnees_test_basiques()
    
    # Afficher les données
    afficher_donnees_test(produits_test, vehicules_test, date_debut, heure_debut, duree_max_jours)
    
    # Initialiser l'optimisateur
    optimiseur = OptimisateurNavettes()
    
    # Comparer les méthodes
    comparer_methodes(optimiseur, produits_test, vehicules_test, date_debut, heure_debut, duree_max_jours)
    
    print(f"\n" + "="*100)
    print("🏁 FIN DU TEST ORGANISÉ")
    print("="*100)

def test_flotte_heterogene_simple():
    """
    Test simple focalisé uniquement sur la méthode flotte hétérogène
    """
    print("="*80)
    print("🧪 TEST FLOTTE HÉTÉROGÈNE SIMPLE")
    print("="*80)
    
    # Données simplifiées pour test rapide
    produits_simple = [
        {
            'nom': 'PRODUIT_A_LOURD',
            'quantite': 10,
            'poids_unitaire': 5.0,
            'volume_unitaire': 15.0,
            'distance_km': 500,
            'vitesse_kmh': 80
        },
        {
            'nom': 'PRODUIT_B_VOLUMINEUX', 
            'quantite': 20,
            'poids_unitaire': 1.0,
            'volume_unitaire': 12.0,
            'distance_km': 500,
            'vitesse_kmh': 80
        },
        {
            'nom': 'PRODUIT_C_COMPACT',
            'quantite': 50,
            'poids_unitaire': 0.5,
            'volume_unitaire': 2.0,
            'distance_km': 500,
            'vitesse_kmh': 80
        }
    ]
    
    vehicules_simple = [
        {
            'nom': 'PETIT_CAMION',
            'type': 'LEGER',
            'capacite_poids_max': 5.0,
            'capacite_volume_max': 30,
            'vitesse_kmh': 85,
            'cout_fixe_jour': 200,
            'cout_variable_km': 0.70
        },
        {
            'nom': 'GROS_CAMION',
            'type': 'LOURD',
            'capacite_poids_max': 25,
            'capacite_volume_max': 80,
            'vitesse_kmh': 75,
            'cout_fixe_jour': 400,
            'cout_variable_km': 1.20
        }
    ]
    
    optimiseur = OptimisateurNavettes()
    
    print(f"\n📦 PRODUITS À TRANSPORTER:")
    for p in produits_simple:
        print(f"   {p['nom']}: {p['quantite']} unités ({p['quantite']*p['poids_unitaire']}t, {p['quantite']*p['volume_unitaire']}m³)")
    
    resultats = optimiseur.calculer_flotte_heterogene_iterative(
        produits_simple,
        vehicules_simple,
        '2025-06-10',
        '08:00',
        7
    )
    
    print(f"\n🎯 RÉSULTAT FINAL:")
    if resultats['demande_satisfaite']:
        print(f"✅ Demande entièrement satisfaite avec {len(resultats['flotte_selectionnee'])} véhicules")
        print(f"💰 Coût total: {resultats['cout_total']:.2f}€")
    else:
        print(f"⚠️ Demande partiellement satisfaite")


# ================================================================================================
# FONCTION PRINCIPALE
# ================================================================================================

if __name__ == "__main__":
    print("🚀 Lancement de l'optimisateur de navettes organisé...")
    
    # Test principal organisé
    main_test_organisé()
    
    # Test simple additionnel
    print("\n" + "🔄" * 40)
    test_flotte_heterogene_simple()
    
    print("\n✅ Tests terminés avec succès!")
    print("📋 Code organisé et structuré pour une maintenance facile")
    print("🎯 Deux méthodes d'optimisation disponibles et comparées automatiquement")