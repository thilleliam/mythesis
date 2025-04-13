from folium import Map, Marker, Popup, Icon, PolyLine
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
                            QMessageBox, QProgressDialog, QInputDialog, QCheckBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
import time
import math

# Import de votre modèle Chantier
from application.models.chantiers import Chantier
from application.config import Base, engine

class CarteChantiers(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carte des Chantiers")
        self.setGeometry(100, 100, 1000, 800)
        
        # Layout principal
        layout = QVBoxLayout()
        
        # Création du widget pour afficher la carte web
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)
        
        # Boutons pour les différentes options de réseau routier
        self.btn_routes_min = QPushButton("Afficher réseau routier minimal")
        self.btn_routes_min.clicked.connect(self.afficher_reseau_minimal)
        layout.addWidget(self.btn_routes_min)
        
        self.btn_routes_complet = QPushButton("Afficher réseau routier complet")
        self.btn_routes_complet.clicked.connect(self.afficher_reseau_complet)
        layout.addWidget(self.btn_routes_complet)
        
        self.btn_routes_forcees = QPushButton("Afficher toutes les connexions (avec lignes directes)")
        self.btn_routes_forcees.clicked.connect(self.afficher_toutes_connexions)
        layout.addWidget(self.btn_routes_forcees)
        self.btn_import_topo = QPushButton("Importer un itinéraire topographique")
        self.btn_import_topo.clicked.connect(self.ajouter_itineraire_topographique)
        layout.addWidget(self.btn_import_topo)
        
        # Widget central
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Stockage des chantiers pour une utilisation ultérieure
        self.chantiers = []
        self.chantiers_valides = []
        
        # Création de la carte
        self.creer_carte()
        
    def creer_carte(self):
        """Crée une carte Folium avec les positions des chantiers depuis la base de données"""
        # Connexion à la base de données
        
        
        # Récupération de tous les chantiers
        with Session(engine) as session:
        # Récupération de tous les chantiers
            self.chantiers = session.query(Chantier).all()
    
        
        # Filtrer les chantiers qui ont des coordonnées valides
        self.chantiers_valides = [c for c in self.chantiers if c.latitude is not None and c.longitude is not None]
        
        # Déterminer le centre de la carte (moyenne des coordonnées)
        if self.chantiers_valides:
            lat_moy = sum(c.latitude for c in self.chantiers_valides) / len(self.chantiers_valides)
            lon_moy = sum(c.longitude for c in self.chantiers_valides) / len(self.chantiers_valides)
        else:
            # Coordonnées par défaut (centre de la France)
            lat_moy, lon_moy = 46.603354, 1.888334
        
        # Création de la carte
        self.carte = Map(location=[lat_moy, lon_moy], zoom_start=6)
        
        # Ajout des marqueurs pour chaque chantier
        for chantier in self.chantiers_valides:
            # Gestion des valeurs None pour éviter les erreurs de formatage
            id_client = chantier.id_client or "Non spécifié"
            localisation = chantier.localisation or "Non spécifiée"
            nature_terrain = chantier.nature_terrain or "Non spécifiée"
            distance_goudron = f"{chantier.distanceAllerGoudron} km" if chantier.distanceAllerGoudron is not None else "Non spécifiée"
            distance_piste = f"{chantier.distanceAllerPiste} km" if chantier.distanceAllerPiste is not None else "Non spécifiée"
            temps_aller = f"{chantier.temps_aller:.2f} h" if chantier.temps_aller is not None else "Non spécifié"
            
            # Création d'un popup avec les informations du chantier
            popup_content = f"""
            <b>ID Client:</b> {id_client}<br>
            <b>Localisation:</b> {localisation}<br>
            <b>Nature du terrain:</b> {nature_terrain}<br>
            <b>Distance goudron:</b> {distance_goudron}<br>
            <b>Distance piste:</b> {distance_piste}<br>
            <b>Temps aller:</b> {temps_aller}
            """
            
            popup = Popup(popup_content, max_width=300)
            
            # Création du marqueur
            marker = Marker(
                location=[chantier.latitude, chantier.longitude],
                popup=popup,
                tooltip=f"Chantier: {id_client}",
                icon=Icon(color='blue', icon='info-sign')
            )
            marker.add_to(self.carte)
        
        # Sauvegarde temporaire de la carte HTML
        self.temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_map.html")
        self.carte.save(self.temp_file)
        
        # Affichage dans le navigateur
        self.browser.load(QUrl.fromLocalFile(self.temp_file))
    
    def calcul_distance_aerienne(self, chantier1, chantier2):
        """Calcule la distance à vol d'oiseau entre deux chantiers"""
        # Formule de la distance haversine
        R = 6371  # Rayon de la Terre en km
        lat1, lon1 = math.radians(chantier1.latitude), math.radians(chantier1.longitude)
        lat2, lon2 = math.radians(chantier2.latitude), math.radians(chantier2.longitude)
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def obtenir_route_osrm(self, chantier1, chantier2, max_retries=3):
        """Obtient un itinéraire entre deux chantiers via OSRM avec plusieurs tentatives"""
        # Points de départ et d'arrivée
        start_long, start_lat = chantier1.longitude, chantier1.latitude
        end_long, end_lat = chantier2.longitude, chantier2.latitude
        
        # Requête au service OSRM
        url = f"http://router.project-osrm.org/route/v1/driving/{start_long},{start_lat};{end_long},{end_lat}?overview=full&geometries=geojson"
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data['code'] == 'Ok' and len(data['routes']) > 0:
                        # Extraction des coordonnées de l'itinéraire
                        geometry = data['routes'][0]['geometry']['coordinates']
                        
                        # Conversion du format [longitude, latitude] au format [latitude, longitude] pour Folium
                        route_points = [[point[1], point[0]] for point in geometry]
                        
                        # Calcul de la distance
                        distance_km = data['routes'][0]['distance'] / 1000  # Conversion en km
                        
                        return route_points, distance_km
                
                # Si on arrive ici, c'est que la requête a échoué ou n'a pas trouvé d'itinéraire
                if attempt < max_retries - 1:
                    time.sleep(2)  # Attendre avant de réessayer
            
            except Exception as e:
                print(f"Tentative {attempt+1}/{max_retries} échouée: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # Attendre avant de réessayer
        
        # Si toutes les tentatives ont échoué
        return None, None
    
    def algorithme_kruskal(self, graphe, nb_sommets):
        """Implémentation de l'algorithme de Kruskal pour créer un arbre couvrant minimal"""
        # Trier les arêtes par poids (distance)
        aretes = []
        for u in range(nb_sommets):
            for v, distance in graphe[u]:
                aretes.append((u, v, distance))
        
        aretes.sort(key=lambda x: x[2])  # Trier par poids
        
        # Structure pour l'union-find
        parent = list(range(nb_sommets))
        
        def trouver(i):
            if parent[i] != i:
                parent[i] = trouver(parent[i])
            return parent[i]
        
        def union(i, j):
            parent[trouver(i)] = trouver(j)
        
        # Résultat : arbre couvrant minimal
        mst = []
        
        for u, v, distance in aretes:
            if trouver(u) != trouver(v):  # Vérifie s'il n'y a pas de cycle
                union(u, v)
                mst.append((u, v, distance))
        
        return mst
    
    def afficher_reseau_minimal(self):
        """Affiche un réseau routier minimal qui connecte tous les chantiers"""
        if len(self.chantiers_valides) < 2:
            QMessageBox.warning(self, "Impossible d'afficher le réseau", 
                               "Il faut au moins 2 chantiers avec des coordonnées valides.")
            return
        
        # Créer une nouvelle carte pour éviter d'ajouter des routes en double
        self.creer_carte()
        
        nb_chantiers = len(self.chantiers_valides)
        
        # Création d'une boîte de dialogue de progression
        progress = QProgressDialog("Calcul du réseau routier minimal...", "Annuler", 0, nb_chantiers * (nb_chantiers - 1) // 2)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        # Calcul des distances entre tous les chantiers
        graphe = [[] for _ in range(nb_chantiers)]
        distances = {}
        
        count = 0
        for i, j in combinations(range(nb_chantiers), 2):
            chantier1 = self.chantiers_valides[i]
            chantier2 = self.chantiers_valides[j]
            
            # Mettre à jour la progression
            progress.setValue(count)
            if progress.wasCanceled():
                return
            count += 1
            
            # D'abord calculer la distance à vol d'oiseau pour estimer
            dist_aerienne = self.calcul_distance_aerienne(chantier1, chantier2)
            
            # Tenter d'obtenir l'itinéraire OSRM
            route_points, distance_km = self.obtenir_route_osrm(chantier1, chantier2)
            
            if route_points and distance_km:
                # Ajouter l'arête au graphe dans les deux sens
                graphe[i].append((j, distance_km))
                graphe[j].append((i, distance_km))
                
                # Stocker les points de la route pour plus tard
                distances[(i, j)] = (route_points, distance_km)
                distances[(j, i)] = (route_points, distance_km)
                
                # Pause pour éviter de surcharger le serveur OSRM
                time.sleep(0.5)
            else:
                # Si OSRM échoue, utiliser la distance à vol d'oiseau
                graphe[i].append((j, dist_aerienne))
                graphe[j].append((i, dist_aerienne))
                distances[(i, j)] = (None, dist_aerienne)
                distances[(j, i)] = (None, dist_aerienne)
        
        # Appliquer l'algorithme de Kruskal pour obtenir l'arbre couvrant minimal
        arbre_minimal = self.algorithme_kruskal(graphe, nb_chantiers)
        
        # Mettre à jour la progression
        progress.setLabelText("Affichage des routes...")
        progress.setValue(0)
        progress.setMaximum(len(arbre_minimal))
        
        # Tracer les routes de l'arbre minimal
        routes_ajoutees = 0
        routes_directes = 0
        
        for idx, (i, j, dist) in enumerate(arbre_minimal):
            progress.setValue(idx)
            if progress.wasCanceled():
                break
                
            chantier1 = self.chantiers_valides[i]
            chantier2 = self.chantiers_valides[j]
            
            route_points, distance_km = distances.get((i, j), (None, None))
            
            if route_points:
                # Si nous avons des points de route OSRM, les utiliser
                PolyLine(
                    route_points,
                    color='red',
                    weight=3,
                    opacity=0.7,
                    tooltip=f"Route: {chantier1.id_client} → {chantier2.id_client} ({distance_km:.1f} km)"
                ).add_to(self.carte)
                routes_ajoutees += 1
            else:
                # Sinon tracer une ligne droite
                PolyLine(
                    [[chantier1.latitude, chantier1.longitude], [chantier2.latitude, chantier2.longitude]],
                    color='orange',
                    weight=2,
                    opacity=0.6,
                    tooltip=f"Distance: {chantier1.id_client} → {chantier2.id_client} ({distance_km:.1f} km)",
                    dash_array='5, 5'
                ).add_to(self.carte)
                routes_ajoutees += 1
                routes_directes += 1
        
        # Fermer la boîte de dialogue de progression
        progress.close()
        
        # Mise à jour de la carte
        self.carte.save(self.temp_file)
        self.browser.load(QUrl.fromLocalFile(self.temp_file))
        
        if routes_ajoutees > 0:
            message = f"Un réseau routier minimal de {routes_ajoutees} routes a été affiché.\n"
            if routes_directes > 0:
                message += f"\n{routes_directes} connexions sont affichées en ligne droite car le service n'a pas pu calculer l'itinéraire réel."
                
            QMessageBox.information(self, "Réseau routier affiché", message)
        else:
            QMessageBox.warning(self, "Erreur", "Aucune route n'a pu être calculée.")
    
    def afficher_reseau_complet(self):
        """Affiche toutes les routes possibles entre les chantiers (limité aux chantiers proches)"""
        if len(self.chantiers_valides) < 2:
            QMessageBox.warning(self, "Impossible d'afficher le réseau", 
                               "Il faut au moins 2 chantiers avec des coordonnées valides.")
            return
        
        # Créer une nouvelle carte pour éviter d'ajouter des routes en double
        self.creer_carte()
        
        # Demander à l'utilisateur la distance maximale à prendre en compte
        max_distance, ok = QInputDialog.getDouble(
            self, "Distance maximale", 
            "Entrez la distance maximale entre les chantiers (km):\n(0 = aucune limite)", 
            200, 0, 1000, 1)
        
        if not ok:
            return
        
        # Si max_distance est 0, pas de limite
        if max_distance == 0:
            max_distance = float('inf')
            
        nb_chantiers = len(self.chantiers_valides)
        nb_paires = nb_chantiers * (nb_chantiers - 1) // 2
        
        # Création d'une boîte de dialogue de progression
        progress = QProgressDialog("Calcul du réseau routier complet...", "Annuler", 0, nb_paires)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        routes_ajoutees = 0
        routes_directes = 0
        count = 0
        
        for i, j in combinations(range(nb_chantiers), 2):
            # Mettre à jour la progression
            progress.setValue(count)
            if progress.wasCanceled():
                break
            count += 1
            
            chantier1 = self.chantiers_valides[i]
            chantier2 = self.chantiers_valides[j]
            
            # Calcul de la distance à vol d'oiseau
            dist_aerienne = self.calcul_distance_aerienne(chantier1, chantier2)
            
            # Ne traiter que les chantiers qui sont à une distance raisonnable
            if dist_aerienne <= max_distance:
                route_points, distance_km = self.obtenir_route_osrm(chantier1, chantier2)
                
                if route_points and distance_km:
                    # Tracer la route sur la carte
                    PolyLine(
                        route_points,
                        color='blue',
                        weight=2,
                        opacity=0.6,
                        tooltip=f"Route: {chantier1.id_client} → {chantier2.id_client} ({distance_km:.1f} km)"
                    ).add_to(self.carte)
                    routes_ajoutees += 1
                else:
                    # Tracer une ligne droite si le service n'a pas trouvé d'itinéraire
                    PolyLine(
                        [[chantier1.latitude, chantier1.longitude], [chantier2.latitude, chantier2.longitude]],
                        color='purple',
                        weight=1,
                        opacity=0.5,
                        tooltip=f"Distance: {chantier1.id_client} → {chantier2.id_client} ({dist_aerienne:.1f} km)",
                        dash_array='5, 5'
                    ).add_to(self.carte)
                    routes_ajoutees += 1
                    routes_directes += 1
                
                # Pause pour éviter de surcharger le serveur OSRM
                time.sleep(0.5)
        
        # Fermer la boîte de dialogue de progression
        progress.close()
        
        # Mise à jour de la carte
        self.carte.save(self.temp_file)
        self.browser.load(QUrl.fromLocalFile(self.temp_file))
        
        if routes_ajoutees > 0:
            message = f"{routes_ajoutees} routes ont été affichées sur la carte."
            if routes_directes > 0:
                message += f"\n\n{routes_directes} connexions sont affichées en ligne droite car le service n'a pas pu calculer l'itinéraire réel."
                
            QMessageBox.information(self, "Réseau routier affiché", message)
        else:
            QMessageBox.warning(self, "Erreur", "Aucune route n'a pu être calculée.")
    # Ajout d'une fonction pour importer des itinéraires personnalisés
    def ajouter_itineraire_topographique(self):
        """Permet d'importer un fichier d'itinéraire créé par l'équipe topographique"""
        from PyQt5.QtWidgets import QFileDialog
        
        # Ouvrir une boîte de dialogue pour sélectionner le fichier
        fichier, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un fichier d'itinéraire", "", 
            "Fichiers GPX (*.gpx);;Fichiers KML (*.kml);;Fichiers CSV (*.csv);;Tous les fichiers (*)"
        )
        
        if not fichier:
            return
        
        # Traitement selon le type de fichier
        extension = fichier.split('.')[-1].lower()
        
        if extension == 'gpx':
            self.importer_gpx(fichier)
        elif extension == 'kml':
            self.importer_kml(fichier)
        elif extension == 'csv':
            self.importer_csv(fichier)
        else:
            QMessageBox.warning(self, "Format non reconnu", 
                            f"Le format de fichier .{extension} n'est pas pris en charge.")
    def importer_gpx(self, fichier):
        """Importe un fichier GPX contenant un itinéraire"""
        try:
            import gpxpy
            
            with open(fichier, 'r') as gpx_file:
                gpx = gpxpy.parse(gpx_file)
                
                for track in gpx.tracks:
                    for segment in track.segments:
                        points = [[point.latitude, point.longitude] for point in segment.points]
                        
                        if points:
                            # Ajouter l'itinéraire à la carte
                            PolyLine(
                                points,
                                color='green',
                                weight=4,
                                opacity=0.8,
                                tooltip=f"Itinéraire topographique: {track.name or 'Sans nom'}"
                            ).add_to(self.carte)
            
            # Mettre à jour la carte
            self.carte.save(self.temp_file)
            self.browser.load(QUrl.fromLocalFile(self.temp_file))
            
            QMessageBox.information(self, "Import réussi", 
                                f"Le fichier GPX a été importé avec succès.")
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'importation", 
                            f"Impossible d'importer le fichier GPX: {str(e)}")
    
    def importer_csv(self, fichier):
        """Importe un fichier CSV contenant un itinéraire"""
        try:
            import pandas as pd
            
            # Ouvrir une boîte de dialogue pour choisir les colonnes
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
            
            class SelectionColonnesDialog(QDialog):
                def __init__(self, colonnes, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Sélection des colonnes")
                    layout = QVBoxLayout(self)
                    
                    layout.addWidget(QLabel("Sélectionnez la colonne latitude:"))
                    self.combo_lat = QComboBox()
                    self.combo_lat.addItems(colonnes)
                    layout.addWidget(self.combo_lat)
                    
                    layout.addWidget(QLabel("Sélectionnez la colonne longitude:"))
                    self.combo_lon = QComboBox()
                    self.combo_lon.addItems(colonnes)
                    layout.addWidget(self.combo_lon)
                    
                    self.btn_ok = QPushButton("OK")
                    self.btn_ok.clicked.connect(self.accept)
                    layout.addWidget(self.btn_ok)
            
            # Lire le CSV et obtenir les en-têtes
            df = pd.read_csv(fichier)
            colonnes = df.columns.tolist()
            
            # Afficher la boîte de dialogue
            dialog = SelectionColonnesDialog(colonnes, self)
            if dialog.exec_() != QDialog.Accepted:
                return
            
            col_lat = dialog.combo_lat.currentText()
            col_lon = dialog.combo_lon.currentText()
            
            # Extraire les points de l'itinéraire
            points = [[lat, lon] for lat, lon in zip(df[col_lat], df[col_lon])]
            
            if points:
                # Ajouter l'itinéraire à la carte
                PolyLine(
                    points,
                    color='green',
                    weight=4,
                    opacity=0.8,
                    tooltip=f"Itinéraire topographique importé"
                ).add_to(self.carte)
            
            # Mettre à jour la carte
            self.carte.save(self.temp_file)
            self.browser.load(QUrl.fromLocalFile(self.temp_file))
            
            QMessageBox.information(self, "Import réussi", 
                                f"Le fichier CSV a été importé avec succès.")
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'importation", 
                            f"Impossible d'importer le fichier CSV: {str(e)}")
    
    def afficher_toutes_connexions(self):
        """Affiche toutes les connexions entre chantiers avec des lignes droites pour garantir la connectivité"""
        if len(self.chantiers_valides) < 2:
            QMessageBox.warning(self, "Impossible d'afficher le réseau", 
                               "Il faut au moins 2 chantiers avec des coordonnées valides.")
            return
        
        # Créer une nouvelle carte pour éviter d'ajouter des routes en double
        self.creer_carte()
        
        # Demander si l'utilisateur veut aussi essayer de calculer les routes réelles
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Mode de calcul")
        msg_box.setText("Comment souhaitez-vous afficher les connexions ?")
        btn_all_direct = msg_box.addButton("Toutes en lignes directes", QMessageBox.ActionRole)
        btn_try_routes = msg_box.addButton("Essayer les itinéraires réels quand possible", QMessageBox.ActionRole)
        msg_box.addButton(QMessageBox.Cancel)
        msg_box.exec_()
        
        if msg_box.clickedButton() == QMessageBox.Cancel:
            return
        
        try_real_routes = (msg_box.clickedButton() == btn_try_routes)
        
        # Si beaucoup de chantiers, demander confirmation
        nb_chantiers = len(self.chantiers_valides)
        nb_connexions = nb_chantiers * (nb_chantiers - 1) // 2
        
        if nb_connexions > 50:
            confirm = QMessageBox.question(
                self, "Confirmation",
                f"Vous allez créer {nb_connexions} connexions, ce qui peut surcharger la carte. Continuer ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if confirm == QMessageBox.No:
                return
        
        # Création d'une boîte de dialogue de progression
        progress = QProgressDialog("Création des connexions...", "Annuler", 0, nb_connexions)
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        connections_added = 0
        count = 0
        
        for i, j in combinations(range(nb_chantiers), 2):
            # Mettre à jour la progression
            progress.setValue(count)
            if progress.wasCanceled():
                break
            count += 1
            
            chantier1 = self.chantiers_valides[i]
            chantier2 = self.chantiers_valides[j]
            
            # Calcul de la distance à vol d'oiseau
            dist_aerienne = self.calcul_distance_aerienne(chantier1, chantier2)
            
            if try_real_routes and dist_aerienne < 300:  # Limiter les tentatives aux distances raisonnables
                # Essayer d'obtenir l'itinéraire réel
                route_points, distance_km = self.obtenir_route_osrm(chantier1, chantier2)
                
                if route_points and distance_km:
                    # Tracer la route réelle
                    PolyLine(
                        route_points,
                        color='green',
                        weight=2,
                        opacity=0.6,
                        tooltip=f"Route: {chantier1.id_client} → {chantier2.id_client} ({distance_km:.1f} km)"
                    ).add_to(self.carte)
                    connections_added += 1
                    time.sleep(0.5)  # Pause pour éviter de surcharger le serveur
                    continue
            
            # Si on arrive ici, soit on ne veut pas essayer les routes réelles,
            # soit l'obtention de la route a échoué
            # Tracer une ligne droite
            PolyLine(
                [[chantier1.latitude, chantier1.longitude], [chantier2.latitude, chantier2.longitude]],
                color='gray',
                weight=1,
                opacity=0.4,
                tooltip=f"Distance: {chantier1.id_client} → {chantier2.id_client} ({dist_aerienne:.1f} km)",
                dash_array='3, 3'
            ).add_to(self.carte)
            connections_added += 1
        
        # Fermer la boîte de dialogue de progression
        progress.close()
        
        # Mise à jour de la carte
        self.carte.save(self.temp_file)
        self.browser.load(QUrl.fromLocalFile(self.temp_file))
        
        QMessageBox.information(self, "Connexions affichées", 
                              f"{connections_added} connexions ont été affichées sur la carte.")


def main():
    app = QApplication(sys.argv)
    fenetre = CarteChantiers()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()