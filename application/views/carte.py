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
from PyQt5.QtGui import QIcon

# Import de votre modèle Chantier
from application.models.chantiers import Chantier
from application.config import Base, engine
from application.models.segment import Segment, GestionnaireSegments
class CarteChantiers(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carte Interactive des Chantiers")
        self.setGeometry(100, 100, 1200, 900)
        self.setWindowIcon(QIcon("C:\\Users\\BIG-computer\\Pictures\\Logo1.png"))
        
        
        # Fichier temporaire pour la carte
        self.temp_file = os.path.join(tempfile.gettempdir(), "carte_chantiers_temp.html")
        
        # Variables pour le dessin
        self.points_ajoutes = []
        self.segments_ajoutes = []
        self.en_mode_dessin = False
        self.points_selectionnes = []
        self.chantiers = []
        self.chantiers_valides = []
        self.segments_db = []  # Pour stocker les segments chargés de la DB
        
        # Charger les segments existants depuis la base de données
        self.charger_segments_depuis_db()
        # Groupes de calques pour les réseaux - Initialisation à None
        self.groupe_reseau_minimal = None
        self.groupe_reseau_complet = None
        self.groupe_toutes_connexions = None
        self.groupe_plan_sahara = None
        
        # Groupes de base
        self.groupe_chantiers = None
        self.groupe_points_utilisateur = None
        self.groupe_segments = None
        
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
        
        # Mettre à jour la carte (qui va ajouter correctement le groupe à la carte)
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
        
        # Créer le groupe pour le plan Sahara
        self.groupe_plan_sahara = FeatureGroup(name='Plan du Sahara (EGS190)')
        
        # Ajout des marqueurs si demandé
        if show_markers:
            for nom, lat, lon, desc in points:
                marker = Marker(
                    location=[lat, lon],
                    popup=Popup(f"<b>{nom}</b><br>{desc}" if desc else nom, max_width=200),
                    tooltip=nom,
                    icon=Icon(color='green', icon='info-sign')
                )
                marker.add_to(self.groupe_plan_sahara)
        
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
                ).add_to(self.groupe_plan_sahara)
        
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
        """
        Version mise à jour du menu avec les nouvelles fonctionnalités
        """
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("Fichier")
        
        action_export = QAction("Exporter la carte", self)
        action_export.triggered.connect(self.exporter_carte)
        file_menu.addAction(action_export)
        
        # 🔥 NOUVEAU: Export des segments
        action_export_segments = QAction("Exporter les segments (CSV)", self)
        action_export_segments.triggered.connect(self.exporter_segments_csv)
        file_menu.addAction(action_export_segments)
        
        file_menu.addSeparator()
        
        action_quit = QAction("Quitter", self)
        action_quit.triggered.connect(self.close)
        file_menu.addAction(action_quit)
        
        # Menu Segments (NOUVEAU)
        segments_menu = menubar.addMenu("Segments")
        
        action_stats = QAction("Statistiques des segments", self)
        action_stats.triggered.connect(self.afficher_statistiques_segments)
        segments_menu.addAction(action_stats)
        
        action_supprimer = QAction("Supprimer un segment", self)
        action_supprimer.triggered.connect(self.supprimer_segment_dialog)
        segments_menu.addAction(action_supprimer)
        
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
        
        # Mettre à jour la carte pour afficher le nouveau point
        self.mettre_a_jour_carte()
        QMessageBox.information(self, "Point ajouté", f"Le point {nom} a été ajouté à la carte.")
    
    def charger_segments_depuis_db(self):
        """
        Charge tous les segments existants depuis la base de données
        """
        try:
            segments_db = GestionnaireSegments.charger_tous_segments()
            self.segments_db = segments_db
            
            # Convertir les segments DB en format utilisable par l'interface
            for segment_db in segments_db:
                segment_interface = {
                    'point1': {
                        'id': segment_db.point1_id_reference,
                        'nom': segment_db.point1_nom,
                        'lat': segment_db.point1_latitude,
                        'lon': segment_db.point1_longitude,
                        'type': segment_db.point1_type
                    },
                    'point2': {
                        'id': segment_db.point2_id_reference,
                        'nom': segment_db.point2_nom,
                        'lat': segment_db.point2_latitude,
                        'lon': segment_db.point2_longitude,
                        'type': segment_db.point2_type
                    },
                    'distance': segment_db.distance_km,
                    'couleur': segment_db.couleur,
                    'epaisseur': segment_db.epaisseur,
                    'afficher_distance': segment_db.afficher_distance,
                    'db_id': segment_db.id,  # ID de la base de données
                    'nom_segment': segment_db.nom_segment,
                    'description': segment_db.description
                }
                self.segments_ajoutes.append(segment_interface)
                
            print(f"✅ {len(segments_db)} segments chargés depuis la base de données")
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des segments: {str(e)}")
    
    def creer_segment(self, dialog):
        """
        Version modifiée pour sauvegarder en base de données
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
            
            # Demander un nom pour le segment (optionnel)
            nom_segment, ok = QInputDialog.getText(
                self, "Nom du segment", 
                "Entrez un nom pour ce segment (optionnel):",
                text=f"{point1['nom']} - {point2['nom']}"
            )
            if not ok:
                nom_segment = f"{point1['nom']} - {point2['nom']}"
            
            # Demander une description (optionnel)
            description, ok = QInputDialog.getText(
                self, "Description", 
                "Entrez une description (optionnel):"
            )
            if not ok:
                description = ""
            
            # 🔥 NOUVEAUTÉ: Sauvegarder en base de données
            segment_db = GestionnaireSegments.sauvegarder_segment(
                point1=point1,
                point2=point2,
                distance=distance,
                couleur='blue',
                epaisseur=3,
                afficher_distance=afficher_distance,
                nom_segment=nom_segment,
                description=description,
                cree_par="utilisateur_carte"  # Vous pouvez personnaliser ceci
            )
            
            if segment_db:
                # Création du segment pour l'interface
                segment = {
                    'point1': point1,
                    'point2': point2,
                    'distance': distance,
                    'couleur': 'blue',
                    'epaisseur': 3,
                    'afficher_distance': afficher_distance,
                    'db_id': segment_db.id,  # 🔥 ID de la base de données
                    'nom_segment': nom_segment,
                    'description': description
                }
                self.segments_ajoutes.append(segment)
                
                dialog.accept()
                self.mettre_a_jour_carte()
                
                # Message de confirmation avec plus d'infos
                QMessageBox.information(
                    self, "Segment sauvegardé", 
                    f"✅ Segment créé et sauvegardé en base de données!\n\n"
                    f"📍 Points: {point1['nom']} → {point2['nom']}\n"
                    f"📏 Distance: {distance:.2f} km\n"
                    f"🏷️  Nom: {nom_segment}\n"
                    f"🆔 ID Base de données: {segment_db.id}"
                )
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de sauvegarder le segment en base de données.")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de créer le segment: {str(e)}")

    def supprimer_segment_dialog(self):
        """
        Nouvelle fonction pour supprimer un segment avec confirmation
        """
        if not self.segments_ajoutes:
            QMessageBox.information(self, "Aucun segment", "Aucun segment à supprimer.")
            return
        
        # Créer une boîte de dialogue pour sélectionner le segment à supprimer
        dialog = QDialog(self)
        dialog.setWindowTitle("Supprimer un segment")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Sélectionnez le segment à supprimer:"))
        
        liste_segments = QListWidget()
        for i, segment in enumerate(self.segments_ajoutes):
            nom_affichage = segment.get('nom_segment', f"{segment['point1']['nom']} - {segment['point2']['nom']}")
            distance = segment['distance']
            db_id = segment.get('db_id', 'N/A')
            
            item_text = f"[ID:{db_id}] {nom_affichage} ({distance:.2f} km)"
            liste_segments.addItem(item_text)
            
        layout.addWidget(liste_segments)
        
        # Boutons
        btn_box = QHBoxLayout()
        
        btn_supprimer = QPushButton("Supprimer")
        btn_supprimer.clicked.connect(lambda: self.confirmer_suppression_segment(dialog, liste_segments))
        btn_box.addWidget(btn_supprimer)
        
        btn_annuler = QPushButton("Annuler")
        btn_annuler.clicked.connect(dialog.reject)
        btn_box.addWidget(btn_annuler)
        
        layout.addLayout(btn_box)
        dialog.setLayout(layout)
        
        dialog.exec_()
    
    def confirmer_suppression_segment(self, dialog, liste_segments):
        """
        Confirme et exécute la suppression d'un segment
        """
        selection = liste_segments.currentRow()
        if selection == -1:
            QMessageBox.warning(self, "Sélection", "Veuillez sélectionner un segment à supprimer.")
            return
        
        segment = self.segments_ajoutes[selection]
        nom_segment = segment.get('nom_segment', f"{segment['point1']['nom']} - {segment['point2']['nom']}")
        
        # Confirmation
        confirm = QMessageBox.question(
            self, "Confirmation de suppression",
            f"Êtes-vous sûr de vouloir supprimer le segment :\n\n"
            f"🏷️  {nom_segment}\n"
            f"📏 Distance: {segment['distance']:.2f} km\n"
            f"🆔 ID: {segment.get('db_id', 'N/A')}\n\n"
            f"⚠️  Cette action est irréversible !",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Supprimer de la base de données
            db_id = segment.get('db_id')
            if db_id and GestionnaireSegments.supprimer_segment(db_id):
                # Supprimer de la liste locale
                self.segments_ajoutes.pop(selection)
                dialog.accept()
                self.mettre_a_jour_carte()
                QMessageBox.information(self, "Suppression", f"✅ Segment '{nom_segment}' supprimé avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer le segment de la base de données.")
    
    def afficher_statistiques_segments(self):
        """
        Affiche les statistiques des segments
        """
        stats = GestionnaireSegments.obtenir_statistiques_segments()
        
        if stats:
            message = "📊 STATISTIQUES DES SEGMENTS\n\n"
            message += f"📈 Nombre total de segments: {stats['total_segments']}\n"
            message += f"📏 Distance totale: {stats['distance_totale']} km\n"
            message += f"📊 Distance moyenne: {stats['distance_moyenne']} km\n"
            message += f"📉 Distance minimale: {stats['distance_min']} km\n"
            message += f"📈 Distance maximale: {stats['distance_max']} km\n"
            
            # Calcul du temps de parcours estimé (à 50 km/h moyenne)
            if stats['distance_totale'] > 0:
                temps_heures = stats['distance_totale'] / 50
                message += f"\n⏱️  Temps de parcours estimé (50 km/h): {temps_heures:.1f} heures"
        else:
            message = "❌ Impossible de récupérer les statistiques"
        
        QMessageBox.information(self, "Statistiques des segments", message)
    
    def exporter_segments_csv(self):
        """
        Exporte tous les segments dans un fichier CSV
        """
        import csv
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter les segments", "", 
            "Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        
        if file_path:
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            
            try:
                segments_db = GestionnaireSegments.charger_tous_segments()
                
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'ID', 'Nom_Segment', 'Point1_Nom', 'Point1_Lat', 'Point1_Lon', 'Point1_Type',
                        'Point2_Nom', 'Point2_Lat', 'Point2_Lon', 'Point2_Type',
                        'Distance_KM', 'Couleur', 'Date_Creation', 'Description'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for segment in segments_db:
                        writer.writerow({
                            'ID': segment.id,
                            'Nom_Segment': segment.nom_segment or '',
                            'Point1_Nom': segment.point1_nom,
                            'Point1_Lat': segment.point1_latitude,
                            'Point1_Lon': segment.point1_longitude,
                            'Point1_Type': segment.point1_type,
                            'Point2_Nom': segment.point2_nom,
                            'Point2_Lat': segment.point2_latitude,
                            'Point2_Lon': segment.point2_longitude,
                            'Point2_Type': segment.point2_type,
                            'Distance_KM': segment.distance_km,
                            'Couleur': segment.couleur,
                            'Date_Creation': segment.date_creation.strftime('%Y-%m-%d %H:%M:%S'),
                            'Description': segment.description or ''
                        })
                
                QMessageBox.information(self, "Export réussi", 
                                      f"✅ {len(segments_db)} segments exportés dans :\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur d'export", f"❌ Erreur lors de l'export: {str(e)}")
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
        
        if len(tous_points) < 2:
            QMessageBox.warning(self, "Erreur", "Il faut au moins 2 points pour dessiner un segment.")
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
        """
        Version modifiée pour proposer de supprimer aussi de la base de données
        """
        if not self.segments_ajoutes and not self.points_ajoutes:
            QMessageBox.information(self, "Aucun élément", "Aucun élément à effacer.")
            return
        
        # Options de suppression
        dialog = QDialog(self)
        dialog.setWindowTitle("Options de suppression")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Que souhaitez-vous effacer ?"))
        
        # Cases à cocher
        self.check_points_manuels = QCheckBox(f"Points ajoutés manuellement ({len(self.points_ajoutes)})")
        self.check_points_manuels.setChecked(True)
        layout.addWidget(self.check_points_manuels)
        
        self.check_segments_interface = QCheckBox(f"Segments de l'interface ({len(self.segments_ajoutes)})")
        self.check_segments_interface.setChecked(True)
        layout.addWidget(self.check_segments_interface)
        
        # Compter les segments avec ID de base de données
        segments_avec_db_id = len([s for s in self.segments_ajoutes if s.get('db_id')])
        self.check_segments_db = QCheckBox(f"Segments de la base de données ({segments_avec_db_id})")
        self.check_segments_db.setChecked(False)  # Par défaut, ne pas supprimer de la DB
        layout.addWidget(self.check_segments_db)
        
        # Message d'avertissement
        warning_label = QLabel("⚠️ La suppression des segments de la base de données est irréversible !")
        warning_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # Boutons
        btn_box = QHBoxLayout()
        
        btn_confirmer = QPushButton("Confirmer la suppression")
        btn_confirmer.clicked.connect(lambda: self.executer_suppression(dialog))
        btn_box.addWidget(btn_confirmer)
        
        btn_annuler = QPushButton("Annuler")
        btn_annuler.clicked.connect(dialog.reject)
        btn_box.addWidget(btn_annuler)
        
        layout.addLayout(btn_box)
        dialog.setLayout(layout)
        
        dialog.exec_()
    def executer_suppression(self, dialog):
        """
        Exécute la suppression selon les options choisies
        """
        elements_supprimes = []
        
        try:
            # Supprimer les points manuels
            if self.check_points_manuels.isChecked():
                nb_points = len(self.points_ajoutes)
                self.points_ajoutes = []
                elements_supprimes.append(f"{nb_points} points manuels")
            
            # Supprimer les segments de la base de données si demandé
            if self.check_segments_db.isChecked():
                segments_db_supprimes = 0
                for segment in self.segments_ajoutes:
                    db_id = segment.get('db_id')
                    if db_id and GestionnaireSegments.supprimer_segment(db_id):
                        segments_db_supprimes += 1
                
                if segments_db_supprimes > 0:
                    elements_supprimes.append(f"{segments_db_supprimes} segments de la base de données")
            
            # Supprimer les segments de l'interface
            if self.check_segments_interface.isChecked():
                nb_segments = len(self.segments_ajoutes)
                self.segments_ajoutes = []
                elements_supprimes.append(f"{nb_segments} segments de l'interface")
            
            # Réinitialiser les groupes de réseaux
            self.groupe_reseau_minimal = None
            self.groupe_reseau_complet = None
            self.groupe_toutes_connexions = None
            self.groupe_plan_sahara = None
            
            dialog.accept()
            self.mettre_a_jour_carte()
            
            if elements_supprimes:
                message = "✅ Éléments supprimés avec succès :\n" + "\n".join([f"• {elem}" for elem in elements_supprimes])
            else:
                message = "Aucun élément n'a été supprimé."
            
            QMessageBox.information(self, "Suppression terminée", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"❌ Erreur lors de la suppression: {str(e)}")

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
            
            # Recréation des groupes de calques de base
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
            
            # Ajouter les groupes de base à la nouvelle carte
            self.groupe_chantiers.add_to(self.carte)
            self.groupe_points_utilisateur.add_to(self.carte)
            self.groupe_segments.add_to(self.carte)
            
            # Ajouter les groupes de réseaux s'ils existent
            if self.groupe_reseau_minimal is not None:
                self.groupe_reseau_minimal.add_to(self.carte)
            if self.groupe_reseau_complet is not None:
                self.groupe_reseau_complet.add_to(self.carte)
            if self.groupe_toutes_connexions is not None:
                self.groupe_toutes_connexions.add_to(self.carte)
            if self.groupe_plan_sahara is not None:
                self.groupe_plan_sahara.add_to(self.carte)
            
            # Ajouter le contrôle des calques en dernier
            LayerControl().add_to(self.carte)
            
            # Sauvegarder et afficher la carte mise à jour
            self.carte.save(self.temp_file)
            self.browser.load(QUrl.fromLocalFile(self.temp_file))
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour de la carte : {str(e)}")
def initialiser_base_segments():
    """
    Fonction à exécuter une seule fois pour créer la table segments
    """
    try:
        from application.models.segment import creer_table_segments
        creer_table_segments()
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {str(e)}")
        return False

    
def main():
    """
    Fonction principale avec initialisation de la base de données
    """
    app = QApplication(sys.argv)
    
    # 1. Initialiser la table segments si elle n'existe pas
    print("=== Initialisation de la base de données ===")
    if not initialiser_base_segments():
        QMessageBox.critical(None, "Erreur", 
                           "❌ Impossible d'initialiser la base de données des segments.\n"
                           "L'application va continuer mais la sauvegarde ne fonctionnera pas.")
    
    # 2. Créer et afficher la fenêtre
    fenetre = CarteChantiers()
    fenetre.show()
    
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
