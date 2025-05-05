from folium import Map, Marker, Popup, Icon, PolyLine, FeatureGroup, LayerControl
import pandas as pd
import requests
import json
import numpy as np
from itertools import combinations
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                            QMessageBox, QProgressDialog, QInputDialog, QCheckBox, QDialog,
                            QLabel, QListWidget, QComboBox, QFileDialog, QMenuBar, QMenu, QAction)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
import time
import math
import tempfile
import networkx as nx # type: ignore

# Import de votre modèle Chantier
from application.models.chantiers import Chantier
from application.config import Base, engine

class CarteChantiers(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carte Interactive des Chantiers")
        self.setGeometry(100, 100, 1200, 900)
        
        # Fichier temporaire pour la carte
        self.temp_file = os.path.join(tempfile.gettempdir(), "carte_chantiers_temp.html")
        
        # Variables pour le dessin
        self.points_ajoutes = []
        self.segments_ajoutes = []
        self.en_mode_dessin = False
        self.points_selectionnes = []
        self.chantiers = []
        self.chantiers_valides = []
        
        # Groupes de calques pour les réseaux
        self.groupe_reseau_minimal = None
        self.groupe_reseau_complet = None
        self.groupe_toutes_connexions = None
        
        # Création de la carte
        self.creer_carte()
        
        # Layout principal
        layout = QVBoxLayout()
        
        # Création du widget pour afficher la carte web
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)
        
        # Boutons pour les différentes fonctionnalités
        self.btn_add_point = QPushButton("Ajouter un point manuellement")
        self.btn_add_point.clicked.connect(self.ajouter_point_manuel)
        layout.addWidget(self.btn_add_point)
        
        self.btn_draw_segment = QPushButton("Dessiner un segment")
        self.btn_draw_segment.clicked.connect(self.dessiner_segment)
        layout.addWidget(self.btn_draw_segment)
        
        self.btn_clear = QPushButton("Effacer tous les éléments")
        self.btn_clear.clicked.connect(self.effacer_carte)
        layout.addWidget(self.btn_clear)
        
        # Boutons pour les options de réseau routier
        self.btn_routes_min = QPushButton("Afficher réseau routier minimal")
        self.btn_routes_min.clicked.connect(self.afficher_reseau_minimal)
        layout.addWidget(self.btn_routes_min)
        
        self.btn_routes_complet = QPushButton("Afficher réseau routier complet")
        self.btn_routes_complet.clicked.connect(self.afficher_reseau_complet)
        layout.addWidget(self.btn_routes_complet)
        
        self.btn_routes_forcees = QPushButton("Afficher toutes les connexions")
        self.btn_routes_forcees.clicked.connect(self.afficher_toutes_connexions)
        layout.addWidget(self.btn_routes_forcees)
        
        # Bouton pour le plan Sahara
        self.btn_plan_sahara = QPushButton("Afficher le plan du Sahara (EGS190)")
        self.btn_plan_sahara.clicked.connect(lambda: self.ajouter_plan_route_specifique())
        layout.addWidget(self.btn_plan_sahara)
        
        # Widget central
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Ajouter le menu
        self.ajouter_menu()
        
        # Chargement initial de la carte
        self.mettre_a_jour_carte()
        
    def afficher_reseau_minimal(self):
        """
        Affiche le réseau routier minimal (arbre couvrant minimal) sur la carte.
        Les connexions sont affichées sous forme de segments entre les points.
        """
        # Vérifier qu'il y a suffisamment de points pour créer un réseau
        tous_points = self.obtenir_tous_points()
        if len(tous_points) < 2:
            QMessageBox.warning(self, "Réseau minimal", 
                            "Il faut au moins 2 points pour créer un réseau minimal.")
            return
            
        # Créer un graphe non dirigé
        G = nx.Graph()
        
        # Ajouter les noeuds (points) avec leurs coordonnées
        for idx, point in enumerate(tous_points):
            G.add_node(idx, pos=(point['lat'], point['lon']), nom=point['nom'])
        
        # Ajouter les arêtes (connexions entre points) avec leur poids (distance)
        for i, point1 in enumerate(tous_points):
            for j, point2 in enumerate(tous_points):
                if i < j:  # Pour éviter d'ajouter la même arête deux fois
                    distance = self.calculer_distance(
                        point1['lat'], point1['lon'], 
                        point2['lat'], point2['lon']
                    )
                    G.add_edge(i, j, weight=distance, 
                            points=((point1['lat'], point1['lon']), 
                                    (point2['lat'], point2['lon'])))
        
        # Calculer l'arbre couvrant minimal
        mst = nx.minimum_spanning_tree(G, weight='weight')
        
        # Supprimer l'ancien groupe s'il existe
        if hasattr(self, 'groupe_reseau_minimal'):
            if self.groupe_reseau_minimal in self.carte._children.values():
                self.carte._children = {k: v for k, v in self.carte._children.items() 
                                    if v != self.groupe_reseau_minimal}
        
        # Créer un nouveau groupe pour le réseau minimal
        self.groupe_reseau_minimal = FeatureGroup(name='Réseau routier minimal')
        
        # Dessiner les segments de l'arbre couvrant minimal
        total_distance = 0
        for u, v, data in mst.edges(data=True):
            point1 = tous_points[u]
            point2 = tous_points[v]
            distance = data['weight']
            total_distance += distance
            
            # Créer le segment entre les deux points
            line = PolyLine(
                locations=[
                    [point1['lat'], point1['lon']],
                    [point2['lat'], point2['lon']]
                ],
                color='green',
                weight=4,
                opacity=0.8,
                tooltip=f"{point1['nom']} ↔ {point2['nom']} ({distance:.1f} km)"
            )
            line.add_to(self.groupe_reseau_minimal)
        
        # Ajouter le groupe à la carte
        self.groupe_reseau_minimal.add_to(self.carte)
        
        # Mettre à jour la carte
        self.mettre_a_jour_carte()
        
        # Afficher un message d'information
        QMessageBox.information(self, "Réseau minimal", 
                            f"Réseau routier minimal affiché.\n"
                            f"Distance totale : {total_distance:.1f} km\n"
                            f"Nombre de segments : {mst.number_of_edges()}")
        
    def afficher_reseau_complet(self):
        """
        Affiche un réseau routier complet optimisé sur la carte.
        Ce réseau utilise l'algorithme du voyageur de commerce pour trouver un parcours efficace.
        """
        # Vérifier qu'il y a suffisamment de points pour créer un réseau
        tous_points = self.obtenir_tous_points()
        if len(tous_points) < 2:
            QMessageBox.warning(self, "Réseau complet", 
                            "Il faut au moins 2 points pour créer un réseau complet.")
            return
            
        # Créer une matrice de distance entre tous les points
        n = len(tous_points)
        distance_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance_matrix[i][j] = self.calculer_distance(
                        tous_points[i]['lat'], tous_points[i]['lon'],
                        tous_points[j]['lat'], tous_points[j]['lon']
                    )
        
        # Utiliser l'algorithme du plus proche voisin pour résoudre approximativement le TSP
        tour = self.nearest_neighbor_tsp(distance_matrix)
        
        # Créer un nouveau groupe pour le réseau complet
        self.groupe_reseau_complet = FeatureGroup(name='Réseau routier complet')
        
        # Dessiner le parcours
        total_distance = 0
        for i in range(len(tour)):
            idx1 = tour[i]
            idx2 = tour[(i + 1) % len(tour)]  # Retour au début après le dernier point
            
            point1 = tous_points[idx1]
            point2 = tous_points[idx2]
            
            distance = distance_matrix[idx1][idx2]
            total_distance += distance
            
            # Dessiner la ligne
            PolyLine(
                [[point1['lat'], point1['lon']], [point2['lat'], point2['lon']]],
                color='blue',
                weight=4,
                opacity=0.8,
                tooltip=f"{point1['nom']} → {point2['nom']} ({distance:.1f} km)"
            ).add_to(self.groupe_reseau_complet)
        
        # Mettre à jour la carte (qui va ajouter correctement le groupe à la carte)
        self.mettre_a_jour_carte()
        
        # Afficher un message d'information
        QMessageBox.information(self, "Réseau complet", 
                            f"Réseau routier complet affiché.\n"
                            f"Distance totale : {total_distance:.1f} km\n"
                            f"Nombre de points : {len(tour)}")

    def afficher_toutes_connexions(self):
        """
        Affiche toutes les connexions possibles entre les points sur la carte.
        Ce réseau complet montre toutes les liaisons directes entre chaque paire de points.
        """
        # Vérifier qu'il y a suffisamment de points pour créer un réseau
        tous_points = self.obtenir_tous_points()
        if len(tous_points) < 2:
            QMessageBox.warning(self, "Toutes les connexions", 
                            "Il faut au moins 2 points pour afficher les connexions.")
            return
            
        # Créer un nouveau groupe pour toutes les connexions
        self.groupe_toutes_connexions = FeatureGroup(name='Toutes les connexions')
        
        # Compteurs pour le message d'information
        total_distance = 0
        nb_connexions = 0
        
        # Dessiner une ligne entre chaque paire de points
        for i, point1 in enumerate(tous_points):
            for j, point2 in enumerate(tous_points):
                if i < j:  # Pour éviter de traiter la même paire deux fois
                    distance = self.calculer_distance(
                        point1['lat'], point1['lon'],
                        point2['lat'], point2['lon']
                    )
                    total_distance += distance
                    nb_connexions += 1
                    
                    # Dessiner la ligne
                    PolyLine(
                        [[point1['lat'], point1['lon']], [point2['lat'], point2['lon']]],
                        color='red',
                        weight=2,
                        opacity=0.5,
                        tooltip=f"{point1['nom']} ↔ {point2['nom']} ({distance:.1f} km)"
                    ).add_to(self.groupe_toutes_connexions)
        
        # Mettre à jour la carte (qui va ajouter correctement le groupe à la carte)
        self.mettre_a_jour_carte()
        
        # Afficher un message d'information
        QMessageBox.information(self, "Toutes les connexions", 
                            f"Toutes les connexions possibles affichées.\n"
                            f"Distance totale cumulée : {total_distance:.1f} km\n"
                            f"Nombre de connexions : {nb_connexions}")

    def mettre_a_jour_carte(self):
        """Sauvegarde et recharge la carte mise à jour"""
        try:
            # Méthode plus sûre pour recréer la carte au lieu de simplement ajouter/supprimer des calques
            # Sauvegarde de la position actuelle et du niveau de zoom
            center = self.carte.get_center()
            zoom = self.carte.options['zoom_start']
            
            # Recréation de la carte de base
            self.carte = Map(
                location=center,
                zoom_start=zoom,
                control_scale=True,
                tiles='OpenStreetMap'
            )
            
            # Ajouter à nouveau les groupes existants
            if hasattr(self, 'groupe_chantiers') and self.groupe_chantiers:
                self.groupe_chantiers.add_to(self.carte)
            if hasattr(self, 'groupe_points_utilisateur') and self.groupe_points_utilisateur:
                self.groupe_points_utilisateur.add_to(self.carte)
            if hasattr(self, 'groupe_segments') and self.groupe_segments:
                self.groupe_segments.add_to(self.carte)
                
            # Ajouter les groupes de réseaux s'ils existent
            if hasattr(self, 'groupe_reseau_minimal') and self.groupe_reseau_minimal:
                self.groupe_reseau_minimal.add_to(self.carte)
            if hasattr(self, 'groupe_reseau_complet') and self.groupe_reseau_complet:
                self.groupe_reseau_complet.add_to(self.carte)
            if hasattr(self, 'groupe_toutes_connexions') and self.groupe_toutes_connexions:
                self.groupe_toutes_connexions.add_to(self.carte)
            if hasattr(self, 'groupe_plan_sahara') and self.groupe_plan_sahara:
                self.groupe_plan_sahara.add_to(self.carte)
            
            # Ajouter le contrôle des calques en dernier
            LayerControl().add_to(self.carte)
            
            # Sauvegarder et afficher la carte mise à jour
            self.carte.save(self.temp_file)
            self.browser.load(QUrl.fromLocalFile(self.temp_file))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour de la carte : {str(e)}")
    def nearest_neighbor_tsp(self, distance_matrix):
        """
        Implémentation de l'algorithme du plus proche voisin pour le problème du voyageur de commerce.
        Retourne une liste d'indices représentant l'ordre des points à visiter.
        """
        n = len(distance_matrix)
        unvisited = set(range(n))
        tour = [0]  # Commencer par le premier point
        unvisited.remove(0)
        
        while unvisited:
            current = tour[-1]
            next_point = min(unvisited, key=lambda x: distance_matrix[current][x])
            tour.append(next_point)
            unvisited.remove(next_point)
            
        return tour
        
    def afficher_toutes_connexions(self):
        """
        Affiche toutes les connexions possibles entre les points sur la carte.
        Ce réseau complet montre toutes les liaisons directes entre chaque paire de points.
        """
        # Vérifier qu'il y a suffisamment de points pour créer un réseau
        tous_points = self.obtenir_tous_points()
        if len(tous_points) < 2:
            QMessageBox.warning(self, "Toutes les connexions", 
                               "Il faut au moins 2 points pour afficher les connexions.")
            return
            
        # Supprimer l'ancien groupe s'il existe
        if self.groupe_toutes_connexions:
            self.carte._children = {k: v for k, v in self.carte._children.items() 
                                  if v != self.groupe_toutes_connexions}
        
        # Créer un nouveau groupe pour toutes les connexions
        self.groupe_toutes_connexions = FeatureGroup(name='Toutes les connexions')
        
        # Compteurs pour le message d'information
        total_distance = 0
        nb_connexions = 0
        
        # Dessiner une ligne entre chaque paire de points
        for i, point1 in enumerate(tous_points):
            for j, point2 in enumerate(tous_points):
                if i < j:  # Pour éviter de traiter la même paire deux fois
                    distance = self.calculer_distance(
                        point1['lat'], point1['lon'],
                        point2['lat'], point2['lon']
                    )
                    total_distance += distance
                    nb_connexions += 1
                    
                    # Dessiner la ligne
                    PolyLine(
                        [[point1['lat'], point1['lon']], [point2['lat'], point2['lon']]],
                        color='red',
                        weight=2,
                        opacity=0.5,
                        tooltip=f"{point1['nom']} ↔ {point2['nom']} ({distance:.1f} km)"
                    ).add_to(self.groupe_toutes_connexions)
        
        # Ajouter le groupe à la carte
        self.groupe_toutes_connexions.add_to(self.carte)
        
        # Mettre à jour la carte
        self.mettre_a_jour_carte()
        
        # Afficher un message d'information
        QMessageBox.information(self, "Toutes les connexions", 
                               f"Toutes les connexions possibles affichées.\n"
                               f"Distance totale cumulée : {total_distance:.1f} km\n"
                               f"Nombre de connexions : {nb_connexions}")
    
    def obtenir_tous_points(self):
        """
        Retourne une liste unifiée de tous les points (chantiers et points ajoutés manuellement)
        avec leurs coordonnées et leur nom.
        """
        tous_points = []
        
        # Ajouter les chantiers
        for i, chantier in enumerate(self.chantiers_valides):
            tous_points.append({
                'id': f"chantier_{i}",
                'nom': chantier.id_client or f"Chantier {i+1}",
                'lat': chantier.latitude,
                'lon': chantier.longitude,
                'type': 'chantier'
            })
        
        # Ajouter les points manuels
        for i, point in enumerate(self.points_ajoutes):
            tous_points.append({
                'id': f"manuel_{i}",
                'nom': point['nom'],
                'lat': point['lat'],
                'lon': point['lon'],
                'type': 'manuel'
            })
            
        return tous_points
        
    def ajouter_plan_route_specifique(self, show_markers=True, show_routes=True, 
                                show_distances=True, route_color="darkgreen"):
        """Ajoute le plan de route du Sahara (EGS190) importé à la carte"""
        # Données géographiques précises basées sur l'image du plan
        # Format: (nom, latitude, longitude, description)
        points = [
            ("BENI ABBES", 30.1333, -1.0417, "Point de départ"),
            ("IGLI", 30.4667, -1.2667, ""),
            ("TAGHIT", 30.9167, -1.0833, ""),
            ("BECHAR", 31.6333, -2.2167, ""),
            ("LEBNOUD", 32.0000, -1.5833, ""),
            ("EL ABIODH SIDI CHEIKH", 32.9000, -0.5500, ""),
            ("BREZINA", 33.1000, 1.2500, ""),
            ("METLILI CHAANBA", 32.2667, 3.6500, ""),
            ("GHARDAIA", 32.4833, 3.6833, ""),
            ("ZELFANA", 32.4000, 3.8833, ""),
            ("OUARGLA", 31.9500, 5.3333, ""),
            ("HASSI MESSAOUD", 31.7000, 5.9667, "Point final du parcours")
        ]
        
        # Segments de route avec distances en km - extraits directement du plan
        segments = [
            ((0, 1), 20),   # BENI ABBES - IGLI
            ((1, 2), 80),   # IGLI - TAGHIT
            ((2, 3), 130),  # TAGHIT - BECHAR
            ((3, 4), 185),  # BECHAR - LEBNOUD
            ((4, 5), 140),  # LEBNOUD - EL ABIODH
            ((5, 6), 310),  # EL ABIODH - BREZINA
            ((6, 7), 175),  # BREZINA - METLILI
            ((7, 8), 80),   # METLILI - GHARDAIA
            ((8, 9), 70),   # GHARDAIA - ZELFANA
            ((9, 10), 190), # ZELFANA - OUARGLA
            ((10, 11), 80)  # OUARGLA - HASSI MESSAOUD
        ]
        
        # Ajout des marqueurs si demandé
        if show_markers:
            for nom, lat, lon, desc in points:
                marker = Marker(
                    location=[lat, lon],
                    popup=Popup(f"<b>{nom}</b><br>{desc}" if desc else nom, max_width=200),
                    tooltip=nom,
                    icon=Icon(color='green', icon='info-sign')
                )
                marker.add_to(self.carte)
        
        # Ajout des routes si demandé
        if show_routes:
            for (idx1, idx2), distance in segments:
                point1 = points[idx1]
                point2 = points[idx2]
                
                # Création du tooltip
                tooltip = f"{point1[0]} → {point2[0]}"
                if show_distances:
                    tooltip += f" ({distance} km)"
                
                # Tracer la ligne
                PolyLine(
                    [[point1[1], point1[2]], [point2[1], point2[2]]],
                    color=route_color,
                    weight=3,
                    opacity=0.7,
                    tooltip=tooltip
                ).add_to(self.carte)
        
        # Mise à jour de la carte
        self.mettre_a_jour_carte()
        
        # Afficher les informations sur le plan
        message = "Le plan de route du Sahara a été ajouté à la carte.\n\n"
        message += "Détails du plan:\n"
        message += "- Zone géographique: Sahara algérien\n"
        message += "- Distance totale: environ 970 km\n"
        message += "- 12 points principaux incluant Bechar, El Abiodh, Ghardaia et Ouargla\n"
        message += "- Distances: Route goudronnée vers camp EGS190 = 890 km\n"
        message += "- Distance piste non entretenue = 70 km\n"
        message += "- Distance de la piste au camp (itinéraire dégradé/rocailleux) = 10 km\n"
        message += "- Source: Plan d'itinéraire de la mission EGS190"
        
        QMessageBox.information(self, "Plan de route ajouté", message)
      
    def ajouter_menu(self):
        """Ajoute un menu à la fenêtre principale"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        
        action_export = QAction("Exporter la carte", self)
        action_export.triggered.connect(self.exporter_carte)
        file_menu.addAction(action_export)
        
        action_quit = QAction("Quitter", self)
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)
        
        # Menu Outils
        tools_menu = menubar.addMenu("Outils")
        
        action_measure = QAction("Mesurer une distance", self)
        action_measure.triggered.connect(self.mesurer_distance)
        tools_menu.addAction(action_measure)
        
        # Menu Réseaux
        network_menu = menubar.addMenu("Réseaux")
        
        action_minimal = QAction("Réseau minimal (MST)", self)
        action_minimal.triggered.connect(self.afficher_reseau_minimal)
        network_menu.addAction(action_minimal)
        
        action_complet = QAction("Réseau complet (TSP)", self)
        action_complet.triggered.connect(self.afficher_reseau_complet)
        network_menu.addAction(action_complet)
        
        action_all = QAction("Toutes les connexions", self)
        action_all.triggered.connect(self.afficher_toutes_connexions)
        network_menu.addAction(action_all)
    
    def creer_carte(self):
        """Crée une carte Folium avec les positions des chantiers depuis la base de données"""
        # Récupération des chantiers depuis la base de données
        with Session(engine) as session:
            self.chantiers = session.query(Chantier).all()
        
        # Filtrer les chantiers qui ont des coordonnées valides
        self.chantiers_valides = [c for c in self.chantiers if c.latitude is not None and c.longitude is not None]
        
        # Déterminer le centre de la carte
        if self.chantiers_valides:
            lat_moy = sum(c.latitude for c in self.chantiers_valides) / len(self.chantiers_valides)
            lon_moy = sum(c.longitude for c in self.chantiers_valides) / len(self.chantiers_valides)
        else:
            # Coordonnées par défaut (centre de la France)
            lat_moy, lon_moy = 46.603354, 1.888334
        
        # Création de la carte avec plusieurs calques
        self.carte = Map(
            location=[lat_moy, lon_moy], 
            zoom_start=6,
            control_scale=True,
            tiles='OpenStreetMap'
        )
        
        # Groupes de calques
        self.groupe_chantiers = FeatureGroup(name='Chantiers')
        self.groupe_points_utilisateur = FeatureGroup(name='Points ajoutés')
        self.groupe_segments = FeatureGroup(name='Segments')
        
        # Ajout des marqueurs pour chaque chantier
        for chantier in self.chantiers_valides:
            self.ajouter_marqueur_chantier(chantier)
        
        # Ajouter les groupes à la carte
        self.groupe_chantiers.add_to(self.carte)
        self.groupe_points_utilisateur.add_to(self.carte)
        self.groupe_segments.add_to(self.carte)
        
        # Ajout du contrôle des calques
        LayerControl().add_to(self.carte)
    
    def ajouter_marqueur_chantier(self, chantier):
        """Ajoute un marqueur pour un chantier sur la carte"""
        id_client = chantier.id_client or "Non spécifié"
        localisation = chantier.localisation or "Non spécifiée"
        nature_terrain = chantier.nature_terrain or "Non spécifiée"
        
        popup_content = f"""
        <b>ID Client:</b> {id_client}<br>
        <b>Localisation:</b> {localisation}<br>
        <b>Nature du terrain:</b> {nature_terrain}<br>
        <b>Coordonnées:</b> {chantier.latitude:.4f}, {chantier.longitude:.4f}
        """
        
        popup = Popup(popup_content, max_width=300)
        
        marker = Marker(
            location=[chantier.latitude, chantier.longitude],
            popup=popup,
            tooltip=f"Chantier: {id_client}",
            icon=Icon(color='blue', icon='info-sign')
        )
        marker.add_to(self.groupe_chantiers)
    
    def ajouter_point_manuel(self):
        """Permet à l'utilisateur d'ajouter un point manuellement"""
        lat, ok1 = QInputDialog.getDouble(
            self, "Coordonnées", "Entrez la latitude:", 
            value=46.0, min=-90, max=90, decimals=6
        )
        
        if not ok1:
            return
        
        lon, ok2 = QInputDialog.getDouble(
            self, "Coordonnées", "Entrez la longitude:", 
            value=2.0, min=-180, max=180, decimals=6
        )
        
        if not ok2:
            return
        
        nom, ok3 = QInputDialog.getText(
            self, "Nom du point", "Entrez un nom pour ce point:"
        )
        
        if not ok3:
            nom = f"Point {len(self.points_ajoutes) + 1}"
        
        # Ajouter le point à la liste
        point = {
            'nom': nom,
            'lat': lat,
            'lon': lon,
            'description': f"Point ajouté manuellement: {nom}"
        }
        self.points_ajoutes.append(point)
        
        # Ajouter le marqueur à la carte
        marker = Marker(
            location=[lat, lon],
            popup=Popup(f"<b>{nom}</b><br>Point ajouté manuellement", max_width=200),
            tooltip=nom,
            icon=Icon(color='red', icon='star')
        )
        marker.add_to(self.groupe_points_utilisateur)
        
        self.mettre_a_jour_carte()
        QMessageBox.information(self, "Point ajouté", f"Le point {nom} a été ajouté à la carte.")
    
    def creer_segment(self, dialog):
        """
        Crée le segment entre les deux points sélectionnés et l'ajoute à la carte.
        Calcule et affiche la distance entre les points.
        """
        try:
            point1 = self.combo_point1.currentData()
            point2 = self.combo_point2.currentData()
            
            # Vérifier que les deux points sont différents
            if point1['id'] == point2['id']:
                QMessageBox.warning(self, "Erreur", "Veuillez sélectionner deux points différents.")
                return
            
            # Calcul de la distance
            distance = self.calculer_distance(
                point1['lat'], point1['lon'],
                point2['lat'], point2['lon']
            )
            
            # Ajouter info de distance si cochée
            afficher_distance = self.check_distance.isChecked()
            
            # Création du segment
            segment = {
                'point1': point1,
                'point2': point2,
                'distance': distance,
                'couleur': 'blue',
                'epaisseur': 3,
                'afficher_distance': afficher_distance
            }
            self.segments_ajoutes.append(segment)
            
            # Préparer le texte du tooltip
            tooltip = f"Segment: {point1['nom']} → {point2['nom']}"
            if afficher_distance:
                tooltip += f" ({distance:.1f} km)"
            
            # Dessiner la ligne directement sans méthode séparée
            line = PolyLine(
                locations=[
                    [point1['lat'], point1['lon']],
                    [point2['lat'], point2['lon']]
                ],
                color='blue',
                weight=3,
                opacity=0.7,
                tooltip=tooltip
            )
            
            # Ajouter la ligne au groupe de segments
            line.add_to(self.groupe_segments)
            
            dialog.accept()
            self.mettre_a_jour_carte()
            QMessageBox.information(
                self, "Segment ajouté", 
                f"Segment créé entre {point1['nom']} et {point2['nom']}.\n"
                f"Distance: {distance:.2f} km"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de créer le segment: {str(e)}")

    def segment_existe_deja(self, point1, point2):
        """
        Vérifie si un segment entre les deux points existe déjà
        """
        for segment in self.segments_ajoutes:
            if ((segment['point1']['id'] == point1['id'] and segment['point2']['id'] == point2['id']) or
                (segment['point1']['id'] == point2['id'] and segment['point2']['id'] == point1['id'])):
                return True
        return False

    def dessiner_segment_sur_carte(self, segment):
        """
        Dessine un segment sur la carte selon les paramètres fournis
        """
        point1 = segment['point1']
        point2 = segment['point2']
        distance = segment['distance']
        
        # Préparer le texte du tooltip
        tooltip = f"Segment: {point1['nom']} → {point2['nom']}"
        if segment.get('afficher_distance', True):
            tooltip += f" ({distance:.1f} km)"
        
        # Dessiner la ligne
        poly_line = PolyLine(
            locations=[
                [point1['lat'], point1['lon']],
                [point2['lat'], point2['lon']]
            ],
            color=segment['couleur'],
            weight=segment['epaisseur'],
            opacity=0.7,
            tooltip=tooltip
        )
        
        poly_line.add_to(self.groupe_segments)
        return poly_line

    def dessiner_segment(self):
        """Permet à l'utilisateur de dessiner un segment entre deux points"""
        tous_points = self.obtenir_tous_points()
        
        if not tous_points:
            QMessageBox.warning(self, "Erreur", "Aucun point disponible pour dessiner un segment.")
            return
        
        # Créer une boîte de dialogue pour sélectionner les points
        dialog = QDialog(self)
        dialog.setWindowTitle("Sélection des points pour le segment")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Liste des points disponibles
        layout.addWidget(QLabel("Sélectionnez le premier point:"))
        self.combo_point1 = QComboBox()
        for point in tous_points:
            self.combo_point1.addItem(f"{point['nom']} ({point['lat']:.4f}, {point['lon']:.4f})", point)
        layout.addWidget(self.combo_point1)
        
        layout.addWidget(QLabel("Sélectionnez le deuxième point:"))
        self.combo_point2 = QComboBox()
        for point in tous_points:
            self.combo_point2.addItem(f"{point['nom']} ({point['lat']:.4f}, {point['lon']:.4f})", point)
        layout.addWidget(self.combo_point2)
        
        # Options du segment
        layout.addWidget(QLabel("Options du segment:"))
        
        self.check_distance = QCheckBox("Afficher la distance")
        self.check_distance.setChecked(True)
        layout.addWidget(self.check_distance)
        
        # Boutons
        btn_box = QHBoxLayout()
        btn_ok = QPushButton("Valider")
        btn_ok.clicked.connect(lambda: self.creer_segment(dialog))
        btn_box.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(dialog.reject)
        btn_box.addWidget(btn_cancel)
        
        layout.addLayout(btn_box)
        dialog.setLayout(layout)
        
        dialog.exec_()

    def trouver_point_plus_proche(self, point_source, liste_points):
        """
        Trouve l'index du point le plus proche de point_source
        dans la liste liste_points, en excluant le point source lui-même
        """
        if not liste_points or len(liste_points) < 2:
            return -1
        
        min_distance = float('inf')
        closest_idx = -1
        
        for idx, point in enumerate(liste_points):
            if point['id'] == point_source['id']:
                continue
            
            distance = self.calculer_distance(
                point_source['lat'], point_source['lon'],
                point['lat'], point['lon']
            )
            
            if distance < min_distance:
                min_distance = distance
                closest_idx = idx
        
        return closest_idx

    def calculer_distance(self, lat1, lon1, lat2, lon2):
        """
        Calcule la distance entre deux points en km (formule haversine)
        Précision améliorée par rapport à la version précédente
        """
        R = 6371.0  # Rayon de la Terre en km
        
        # Conversion des degrés en radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Différences de coordonnées
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Formule haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def mesurer_distance(self):
        """Permet à l'utilisateur de mesurer une distance entre deux points"""
        QMessageBox.information(
            self, "Mesure de distance",
            "Pour mesurer une distance :\n"
            "1. Ajoutez deux points sur la carte\n"
            "2. Créez un segment entre ces points\n"
            "3. La distance sera affichée dans l'infobulle du segment"
        )
    
    def exporter_carte(self):
        """Permet d'exporter la carte dans un fichier HTML"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter la carte", "", 
            "Fichiers HTML (*.html);;Tous les fichiers (*)"
        )
        
        if file_path:
            if not file_path.lower().endswith('.html'):
                file_path += '.html'
            
            self.carte.save(file_path)
            QMessageBox.information(self, "Export réussi", f"La carte a été exportée dans :\n{file_path}")
    
    def effacer_carte(self):
        """Efface tous les éléments ajoutés par l'utilisateur"""
        confirm = QMessageBox.question(
            self, "Confirmation",
            "Voulez-vous vraiment effacer tous les points et segments ajoutés ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.points_ajoutes = []
            self.segments_ajoutes = []
            
            # Recréer les groupes vides
            self.groupe_points_utilisateur = FeatureGroup(name='Points ajoutés')
            self.groupe_segments = FeatureGroup(name='Segments')
            
            # Re-ajouter les groupes à la carte
            self.groupe_points_utilisateur.add_to(self.carte)
            self.groupe_segments.add_to(self.carte)
            
            self.mettre_a_jour_carte()
            QMessageBox.information(self, "Carte effacée", "Tous les éléments ajoutés ont été supprimés.")
    def mettre_a_jour_carte(self):
        """Sauvegarde et recharge la carte mise à jour"""
        try:
            # Définir des valeurs par défaut pour le centre et le zoom
            center = [46.603354, 1.888334]  # Coordonnées par défaut (centre de la France)
            zoom = 6  # Niveau de zoom par défaut
            
            # Si la carte existe déjà, récupérer sa position et son zoom actuels
            if hasattr(self, 'carte') and self.carte:
                try:
                    center = self.carte.location
                    zoom = self.carte.options.get('zoom_start', zoom)
                except:
                    pass  # En cas d'erreur, utiliser les valeurs par défaut
            
            # Recréation complète de la carte
            self.carte = Map(
                location=center,
                zoom_start=zoom,
                control_scale=True,
                tiles='OpenStreetMap'
            )
            
            # Recréation des groupes de calques
            self.groupe_chantiers = FeatureGroup(name='Chantiers')
            self.groupe_points_utilisateur = FeatureGroup(name='Points ajoutés')
            self.groupe_segments = FeatureGroup(name='Segments')
            
            # Réajout des marqueurs de chantiers
            for chantier in self.chantiers_valides:
                self.ajouter_marqueur_chantier(chantier)
            
            # Réajout des points manuels
            for point in self.points_ajoutes:
                marker = Marker(
                    location=[point['lat'], point['lon']],
                    popup=Popup(f"<b>{point['nom']}</b><br>Point ajouté manuellement", max_width=200),
                    tooltip=point['nom'],
                    icon=Icon(color='red', icon='star')
                )
                marker.add_to(self.groupe_points_utilisateur)
            
            # Réajout des segments
            for segment in self.segments_ajoutes:
                self.dessiner_segment_sur_carte(segment)
            
            # Ajouter les groupes à la nouvelle carte
            self.groupe_chantiers.add_to(self.carte)
            self.groupe_points_utilisateur.add_to(self.carte)
            self.groupe_segments.add_to(self.carte)
            
            # Ajouter le contrôle des calques
            LayerControl().add_to(self.carte)
            
            # Sauvegarder et afficher la carte mise à jour
            self.carte.save(self.temp_file)
            self.browser.load(QUrl.fromLocalFile(self.temp_file))
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour de la carte : {str(e)}")

def main():
    app = QApplication(sys.argv)
    fenetre = CarteChantiers()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()