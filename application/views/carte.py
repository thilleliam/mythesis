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
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, 
                            QMessageBox, QProgressDialog, QInputDialog, QCheckBox, QDialog,
                            QLabel, QListWidget, QComboBox, QFileDialog, QMenuBar, QMenu, QAction)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
import time
import math
import tempfile

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
        """Affiche le réseau routier minimal sur la carte"""
        QMessageBox.information(self, "Réseau minimal", "Cette fonctionnalité n'est pas encore implémentée.")
        
    def afficher_reseau_complet(self):
        """Affiche le réseau routier complet sur la carte"""
        QMessageBox.information(self, "Réseau complet", "Cette fonctionnalité n'est pas encore implémentée.")
        
    def afficher_toutes_connexions(self):
        """Affiche toutes les connexions possibles entre les points sur la carte"""
        QMessageBox.information(self, "Toutes les connexions", "Cette fonctionnalité n'est pas encore implémentée.")
        
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
    
    def dessiner_segment(self):
        """Permet à l'utilisateur de dessiner un segment entre deux points"""
        if not self.chantiers_valides and not self.points_ajoutes:
            QMessageBox.warning(self, "Erreur", "Aucun point disponible pour dessiner un segment.")
            return
        
        # Créer une liste de tous les points disponibles
        points_disponibles = []
        
        # Ajouter les chantiers
        for i, chantier in enumerate(self.chantiers_valides):
            points_disponibles.append({
                'id': f"chantier_{i}",
                'nom': chantier.id_client or f"Chantier {i}",
                'lat': chantier.latitude,
                'lon': chantier.longitude,
                'type': 'chantier'
            })
        
        # Ajouter les points manuels
        for i, point in enumerate(self.points_ajoutes):
            points_disponibles.append({
                'id': f"manuel_{i}",
                'nom': point['nom'],
                'lat': point['lat'],
                'lon': point['lon'],
                'type': 'manuel'
            })
        
        # Boîte de dialogue pour sélectionner les points
        dialog = QDialog(self)
        dialog.setWindowTitle("Sélection des points pour le segment")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Liste des points disponibles
        layout.addWidget(QLabel("Sélectionnez le premier point:"))
        self.combo_point1 = QComboBox()
        for point in points_disponibles:
            self.combo_point1.addItem(f"{point['nom']} ({point['lat']:.4f}, {point['lon']:.4f})", point)
        layout.addWidget(self.combo_point1)
        
        layout.addWidget(QLabel("Sélectionnez le deuxième point:"))
        self.combo_point2 = QComboBox()
        for point in points_disponibles:
            self.combo_point2.addItem(f"{point['nom']} ({point['lat']:.4f}, {point['lon']:.4f})", point)
        layout.addWidget(self.combo_point2)
        
        # Options du segment
        layout.addWidget(QLabel("Options du segment:"))
        
        self.check_distance = QCheckBox("Afficher la distance")
        self.check_distance.setChecked(True)
        layout.addWidget(self.check_distance)
        
        # Boutons
        btn_box = QVBoxLayout()
        btn_ok = QPushButton("Valider")
        btn_ok.clicked.connect(lambda: self.creer_segment(dialog))
        btn_box.addWidget(btn_ok)
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.clicked.connect(dialog.reject)
        btn_box.addWidget(btn_cancel)
        
        layout.addLayout(btn_box)
        dialog.setLayout(layout)
        
        dialog.exec_()
    
    def creer_segment(self, dialog):
        """Crée le segment entre les deux points sélectionnés"""
        point1 = self.combo_point1.currentData()
        point2 = self.combo_point2.currentData()
        
        if point1['id'] == point2['id']:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner deux points différents.")
            return
        
        # Calcul de la distance
        distance = self.calculer_distance(
            point1['lat'], point1['lon'],
            point2['lat'], point2['lon']
        )
        
        # Création du segment
        segment = {
            'point1': point1,
            'point2': point2,
            'distance': distance,
            'couleur': 'blue',
            'epaisseur': 3
        }
        self.segments_ajoutes.append(segment)
        
        # Dessiner le segment sur la carte
        PolyLine(
            locations=[
                [point1['lat'], point1['lon']],
                [point2['lat'], point2['lon']]
            ],
            color=segment['couleur'],
            weight=segment['epaisseur'],
            opacity=0.7,
            tooltip=f"Segment: {point1['nom']} → {point2['nom']} ({distance:.1f} km)"
        ).add_to(self.groupe_segments)
        
        dialog.accept()
        self.mettre_a_jour_carte()
        QMessageBox.information(self, "Segment ajouté", f"Segment créé entre {point1['nom']} et {point2['nom']}.")
    
    def calculer_distance(self, lat1, lon1, lat2, lon2):
        """Calcule la distance entre deux points en km (formule haversine)"""
        R = 6371  # Rayon de la Terre en km
        
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
        self.carte.save(self.temp_file)
        self.browser.load(QUrl.fromLocalFile(self.temp_file))

def main():
    app = QApplication(sys.argv)
    fenetre = CarteChantiers()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()