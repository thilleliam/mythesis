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
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QComboBox
from PyQt5.QtCore import QUrl, Qt
import time
import math

# Import de votre modèle Chantier
from application.models.chantiers import Chantier
from application.config import Base, engine


import pandas as pd
import os
import json
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from tkinter import messagebox, simpledialog
import tkinter as tk


class Segment:
    """Classe représentant un segment entre deux points"""
    def __init__(self, from_idx, to_idx, distance, road_type="Goudron"):
        self.from_idx = from_idx
        self.to_idx = to_idx
        self.distance = distance
        self.road_type = road_type

    def __str__(self):
        return f"Segment: {self.from_idx} → {self.to_idx}, {self.distance} km ({self.road_type})"


import os
import json
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from tkinter import messagebox, simpledialog
import tkinter as tk


class Segment:
    """Classe représentant un segment entre deux points"""
    def __init__(self, from_idx, to_idx, distance, road_type="Goudron"):
        self.from_idx = from_idx
        self.to_idx = to_idx
        self.distance = distance
        self.road_type = road_type

    def __str__(self):
        return f"Segment: {self.from_idx} → {self.to_idx}, {self.distance} km ({self.road_type})"


class ManageRoutesDialog(ttk.Toplevel):
    """Interface pour gérer les itinéraires et trajets"""

    def __init__(self, parent, callback_update_map=None):
        super().__init__(parent)
        self.parent = parent
        self.callback_update_map = callback_update_map

        # Configuration de la fenêtre
        self.title("Gestionnaire d'itinéraires")
        self.geometry("800x600")

        # Données
        self.points = []  # Liste des points (nom, lat, lon, description)
        self.segments = []  # Liste des segments (Segment objects)
        self.current_plan_name = "Nouveau Plan"
        self.plans_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plans")

        # Créer le répertoire des plans s'il n'existe pas
        if not os.path.exists(self.plans_directory):
            os.makedirs(self.plans_directory)

        # Interface
        self.create_widgets()
        self.load_saved_plans()
    def mettre_a_jour_carte(self):
        """Met à jour la carte avec les points et segments actuels"""
        # Exemple de logique pour mettre à jour la carte
        if self.callback_update_map:
            self.callback_update_map(self.points, self.segments)
            messagebox.showinfo("Succès", "La carte a été mise à jour avec succès.")
        else:
            messagebox.showerror("Erreur", "Aucune fonction de mise à jour de la carte n'est définie.")
    def create_widgets(self):
        """Création de l'interface utilisateur"""
        # Style
        style = ttk.Style()
        style.configure('TButton', font=('Helvetica', 10))
        style.configure('TLabel', font=('Helvetica', 11))
        style.configure('Heading.TLabel', font=('Helvetica', 14, 'bold'))

        # Notebook principal
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Onglet 1: Gestion des points
        self.tab_points = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_points, text="Points")

        # Onglet 2: Gestion des segments
        self.tab_segments = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_segments, text="Segments")

        # Onglet 3: Gestion des plans
        self.tab_plans = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_plans, text="Plans")

        # Configurer les onglets
        self.setup_points_tab()
        self.setup_segments_tab()
        self.setup_plans_tab()

        # Barre de boutons commune
        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(pady=10, padx=10, fill=tk.X)

        self.btn_apply = ttk.Button(self.btn_frame, text="Appliquer à la carte",
                                    bootstyle=SUCCESS, command=self.apply_to_map)
        self.btn_apply.pack(side=tk.RIGHT, padx=5)

        self.btn_close = ttk.Button(self.btn_frame, text="Fermer",
                                    bootstyle=SECONDARY, command=self.destroy)
        self.btn_close.pack(side=tk.RIGHT, padx=5)

    def setup_points_tab(self):
        """Configuration de l'onglet des points"""
        main_frame = ttk.Frame(self.tab_points)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="Gestion des points", style='Heading.TLabel').pack(pady=(0, 10))

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)

        self.btn_add_point = ttk.Button(action_frame, text="Ajouter un point",
                                        bootstyle=PRIMARY, command=self.add_point)
        self.btn_add_point.pack(side=tk.LEFT, padx=5)

        self.btn_remove_point = ttk.Button(action_frame, text="Supprimer le point sélectionné",
                                           bootstyle=DANGER, command=self.remove_point)
        self.btn_remove_point.pack(side=tk.LEFT, padx=5)

        self.points_frame = ScrolledFrame(main_frame, autohide=True)
        self.points_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.points_rows = []  # Pour stocker les références aux widgets

    def setup_segments_tab(self):
        """Configuration de l'onglet des segments"""
        main_frame = ttk.Frame(self.tab_segments)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="Gestion des segments", style='Heading.TLabel').pack(pady=(0, 10))

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=5)

        self.btn_add_segment = ttk.Button(action_frame, text="Ajouter un segment",
                                          bootstyle=PRIMARY, command=self.add_segment)
        self.btn_add_segment.pack(side=tk.LEFT, padx=5)

        self.btn_remove_segment = ttk.Button(action_frame, text="Supprimer le segment sélectionné",
                                             bootstyle=DANGER, command=self.remove_segment)
        self.btn_remove_segment.pack(side=tk.LEFT, padx=5)

        self.segments_frame = ScrolledFrame(main_frame, autohide=True)
        self.segments_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.segments_rows = []  # Pour stocker les références aux widgets

    def setup_plans_tab(self):
        """Configuration de l'onglet des plans"""
        main_frame = ttk.Frame(self.tab_plans)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text="Gestion des plans", style='Heading.TLabel').pack(pady=(0, 10))

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)

        self.btn_save_plan = ttk.Button(action_frame, text="Enregistrer le plan actuel",
                                        bootstyle=PRIMARY, command=self.save_current_plan)
        self.btn_save_plan.pack(side=tk.LEFT, padx=5)

        self.btn_load_plan = ttk.Button(action_frame, text="Charger le plan sélectionné",
                                        bootstyle=INFO, command=self.load_selected_plan)
        self.btn_load_plan.pack(side=tk.LEFT, padx=5)

        self.btn_delete_plan = ttk.Button(action_frame, text="Supprimer le plan sélectionné",
                                          bootstyle=DANGER, command=self.delete_selected_plan)
        self.btn_delete_plan.pack(side=tk.LEFT, padx=5)

        self.plans_listbox = ttk.Treeview(main_frame, columns=("name", "description"),
                                          show="headings", selectmode="browse")
        self.plans_listbox.heading("name", text="Nom du plan")
        self.plans_listbox.heading("description", text="Description")
        self.plans_listbox.pack(fill=tk.BOTH, expand=True)

    def add_point(self):
        """Ajoute un nouveau point"""
        name = simpledialog.askstring("Ajouter un point", "Nom du point :")
        if not name:
            return
        lat = simpledialog.askfloat("Ajouter un point", "Latitude :")
        lon = simpledialog.askfloat("Ajouter un point", "Longitude :")
        desc = simpledialog.askstring("Ajouter un point", "Description :")
        self.points.append((name, lat, lon, desc))
        self.update_points_list()

    def add_segment(self):
        """Ajoute un nouveau segment"""
        if len(self.points) < 2:
            messagebox.showinfo("Information", "Vous devez avoir au moins 2 points pour créer un segment")
            return
        from_idx = simpledialog.askinteger("Ajouter un segment", "Index du point de départ :")
        to_idx = simpledialog.askinteger("Ajouter un segment", "Index du point d'arrivée :")
        distance = simpledialog.askfloat("Ajouter un segment", "Distance (km) :")
        road_type = simpledialog.askstring("Ajouter un segment", "Type de route :", initialvalue="Goudron")
        segment = Segment(from_idx, to_idx, distance, road_type)
        self.segments.append(segment)
        self.update_segments_list()

    def update_points_list(self):
        """Met à jour l'affichage de la liste des points"""
        for widgets in self.points_rows:
            for widget in widgets:
                widget.destroy()
        self.points_rows = []
        for i, point in enumerate(self.points):
            row_frame = ttk.Frame(self.points_frame)
            row_frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(row_frame, text=f"{i}: {point[0]} ({point[1]}, {point[2]})").pack(side=tk.LEFT)

    def update_segments_list(self):
        """Met à jour l'affichage de la liste des segments"""
        for widgets in self.segments_rows:
            for widget in widgets:
                widget.destroy()
        self.segments_rows = []
        for i, segment in enumerate(self.segments):
            row_frame = ttk.Frame(self.segments_frame)
            row_frame.pack(fill=tk.X, padx=5, pady=2)
            ttk.Label(row_frame, text=f"{i}: {segment}").pack(side=tk.LEFT)

    def save_current_plan(self):
        """Enregistre le plan actuel"""
        name = simpledialog.askstring("Enregistrer le plan", "Nom du plan :")
        if not name:
            return
        plan_data = {
            "name": name,
            "points": self.points,
            "segments": [{"from_idx": s.from_idx, "to_idx": s.to_idx, "distance": s.distance, "road_type": s.road_type}
                         for s in self.segments]
        }
        file_path = os.path.join(self.plans_directory, f"{name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, ensure_ascii=False, indent=2)
        self.load_saved_plans()

    def load_saved_plans(self):
        """Charge la liste des plans sauvegardés"""
        for item in self.plans_listbox.get_children():
            self.plans_listbox.delete(item)
        for filename in os.listdir(self.plans_directory):
            if filename.endswith('.json'):
                with open(os.path.join(self.plans_directory, filename), 'r', encoding='utf-8') as f:
                    plan_data = json.load(f)
                    self.plans_listbox.insert("", "end", values=(plan_data["name"], plan_data.get("description", "")))

    def load_selected_plan(self):
        """Charge le plan sélectionné"""
        selected = self.plans_listbox.selection()
        if not selected:
            messagebox.showinfo("Information", "Veuillez sélectionner un plan à charger")
            return
        filename = self.plans_listbox.item(selected[0], "values")[0]
        file_path = os.path.join(self.plans_directory, f"{filename}.json")
        with open(file_path, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)
        self.points = plan_data["points"]
        self.segments = [Segment(**s) for s in plan_data["segments"]]
        self.update_points_list()
        self.update_segments_list()

    def delete_selected_plan(self):
        """Supprime le plan sélectionné"""
        selected = self.plans_listbox.selection()
        if not selected:
            messagebox.showinfo("Information", "Veuillez sélectionner un plan à supprimer")
            return
        filename = self.plans_listbox.item(selected[0], "values")[0]
        file_path = os.path.join(self.plans_directory, f"{filename}.json")
        os.remove(file_path)
        self.load_saved_plans()
    def remove_segment(self):
        """Supprime le segment sélectionné"""
        if not self.segments:
            messagebox.showinfo("Information", "Aucun segment à supprimer.")
            return

        # Demander à l'utilisateur quel segment supprimer
        segment_index = simpledialog.askinteger(
            "Supprimer un segment",
            f"Entrez l'index du segment à supprimer (0 à {len(self.segments) - 1}):"
        )

        if segment_index is None:
            return  # L'utilisateur a annulé

        if 0 <= segment_index < len(self.segments):
            del self.segments[segment_index]
            self.update_segments_list()
            messagebox.showinfo("Succès", "Le segment a été supprimé avec succès.")
        else:
            messagebox.showerror("Erreur", "Index invalide. Veuillez réessayer.")
    def remove_point(self):
        """Supprime le point sélectionné"""
        if not self.points:
            messagebox.showinfo("Information", "Aucun point à supprimer.")
            return

        # Demander à l'utilisateur quel point supprimer
        point_index = simpledialog.askinteger(
            "Supprimer un point",
            f"Entrez l'index du point à supprimer (0 à {len(self.points) - 1}):"
        )

        if point_index is None:
            return  # L'utilisateur a annulé

        if 0 <= point_index < len(self.points):
            del self.points[point_index]
            self.update_points_list()
            messagebox.showinfo("Succès", "Le point a été supprimé avec succès.")
        else:
            messagebox.showerror("Erreur", "Index invalide. Veuillez réessayer.")
    def apply_to_map(self):
        """Applique les modifications à la carte principale"""
        if self.callback_update_map:
            self.callback_update_map(self.points, self.segments)
        else:
            messagebox.showerror("Erreur", "Aucune fonction de mise à jour de la carte n'est définie.")
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Masquer la fenêtre principale
    dialog = ManageRoutesDialog(root)
    dialog.mainloop()

# Adaptation de ImportPlanDialog pour utiliser ttkbootstrap au lieu de PyQt5
class ImportPlanDialog(ttk.Toplevel):
    """Boîte de dialogue pour l'import de plans prédéfinis"""
    def __init__(self, parent=None, callback_import_plan=None):
        super().__init__(parent)
        self.title("Import de plans prédéfinis")
        self.geometry("500x400")
        
        self.callback_import_plan = callback_import_plan
        
        # Interface
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Liste des plans disponibles
        ttk.Label(main_frame, text="Sélectionnez un plan à importer :").pack(anchor=tk.W, pady=(0, 5))
        
        self.plans_listbox = ttk.Treeview(main_frame, columns=("name",), show="headings", selectmode="browse")
        self.plans_listbox.heading("name", text="Nom du plan")
        self.plans_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Ajouter les plans prédéfinis
        self.plans_listbox.insert("", "end", values=("Plan de la mission EGS190 (Sahara)",))
        # Ajouter d'autres plans ici si nécessaire
        
        # Options d'affichage
        options_frame = ttk.Labelframe(main_frame, text="Options d'affichage")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Variables pour les options
        self.markers_var = tk.BooleanVar(value=True)
        self.routes_var = tk.BooleanVar(value=True)
        self.distances_var = tk.BooleanVar(value=True)
        
        # Checkboxes pour les options
        ttk.Checkbutton(options_frame, text="Afficher les marqueurs des villes", 
                      variable=self.markers_var).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="Afficher les routes entre les points", 
                      variable=self.routes_var).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Checkbutton(options_frame, text="Afficher les distances sur les routes", 
                      variable=self.distances_var).pack(anchor=tk.W, padx=10, pady=2)
        
        # Couleur des routes
        color_frame = ttk.Labelframe(main_frame, text="Couleur des routes")
        color_frame.pack(fill=tk.X, pady=10)
        
        self.color_var = tk.StringVar(value="darkgreen")
        self.color_combo = ttk.Combobox(color_frame, textvariable=self.color_var)
        self.color_combo['values'] = ["Vert foncé", "Rouge", "Bleu"]
        self.color_combo['state'] = 'readonly'  # Empêche la saisie directe
        self.color_combo.pack(fill=tk.X, padx=10, pady=5)
        
        # Boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Importer", bootstyle=SUCCESS, 
                 command=self.import_selected_plan).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler", bootstyle=SECONDARY, 
                 command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def import_selected_plan(self):
        """Importe le plan sélectionné"""
        selected = self.plans_listbox.selection()
        if not selected:
            messagebox.showinfo("Information", "Veuillez sélectionner un plan à importer")
            return
            
        plan_name = self.plans_listbox.item(selected[0], "values")[0]
        
        # Conversion des couleurs
        color_map = {
            "Vert foncé": "darkgreen",
            "Rouge": "red",
            "Bleu": "blue"
        }
        
        color = color_map.get(self.color_combo.get(), "darkgreen")

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")  # Utilisation d'un thème moderne
    dialog = ManageRoutesDialog(root)
    dialog.mainloop()

class ImportPlanDialog(QDialog):
    """Boîte de dialogue pour l'import de plans prédéfinis"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import de plans prédéfinis")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Liste des plans disponibles
        layout.addWidget(QLabel("Sélectionnez un plan à importer :"))
        self.list_plans = QListWidget()
        self.list_plans.addItem("Plan de la mission EGS190 (Sahara)")
        # Ajoutez d'autres plans ici si nécessaire
        layout.addWidget(self.list_plans)
        
        # Options d'affichage
        layout.addWidget(QLabel("Options d'affichage :"))
        self.check_markers = QCheckBox("Afficher les marqueurs des villes")
        self.check_markers.setChecked(True)
        layout.addWidget(self.check_markers)
        
        self.check_routes = QCheckBox("Afficher les routes entre les points")
        self.check_routes.setChecked(True)
        layout.addWidget(self.check_routes)
        
        self.check_distances = QCheckBox("Afficher les distances sur les routes")
        self.check_distances.setChecked(True)
        layout.addWidget(self.check_distances)
        
        # Couleur des routes
        layout.addWidget(QLabel("Couleur des routes :"))
        self.combo_color = QComboBox()
        for color, name in [
            ("darkgreen", "Vert foncé"), 
            ("red", "Rouge"),
            ("blue", "Bleu"),
            ("orange", "Orange"),
            ("purple", "Violet"),
            ("black", "Noir")
        ]:
            self.combo_color.addItem(name, color)
        layout.addWidget(self.combo_color)
        
        # Boutons
        button_box = QHBoxLayout()
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        button_box.addWidget(self.btn_cancel)
        
        self.btn_import = QPushButton("Importer")
        self.btn_import.clicked.connect(self.accept)
        self.btn_import.setDefault(True)
        button_box.addWidget(self.btn_import)
        
        layout.addLayout(button_box)

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
        
        # Appel à la méthode pour créer le bouton du plan Sahara
        self.ajouter_bouton_plan_specifique()
        
        # Si nous avons un bouton pour le plan du Sahara à ajouter
        if hasattr(self, 'btn_sahara_to_add'):
            layout.addWidget(self.btn_sahara_to_add)
        
        # Widget central
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Stockage des chantiers pour une utilisation ultérieure
        self.chantiers = []
        self.chantiers_valides = []
        
        # Création de la carte
        self.creer_carte()
        self.ajouter_menu_plans_predefined()
    def ouvrir_dialog_routes(self):
        """Ouvre le gestionnaire d'itinéraires"""
        dialog = ManageRoutesDialog(parent=self, callback_update_map=self.mettre_a_jour_carte)
        dialog.mainloop()
    def mettre_a_jour_carte(self, points, segments):
        """Met à jour la carte avec les points et segments transmis"""
        # Recréer la carte pour éviter les doublons
        self.creer_carte()

        # Ajouter les points
        for point in points:
            name, lat, lon, desc = point
            marker = Marker(
                location=[lat, lon],
                popup=Popup(f"<b>{name}</b><br>{desc}" if desc else name, max_width=200),
                tooltip=name,
                icon=Icon(color='blue', icon='info-sign')
            )
            marker.add_to(self.carte)

        # Ajouter les segments
        for segment in segments:
            PolyLine(
                [[points[segment.from_idx][1], points[segment.from_idx][2]],
                [points[segment.to_idx][1], points[segment.to_idx][2]]],
                color='green',
                weight=3,
                opacity=0.7,
                tooltip=f"Segment: {segment.distance} km ({segment.road_type})"
            ).add_to(self.carte)

        # Sauvegarder et recharger la carte
        self.carte.save(self.temp_file)
        self.browser.load(QUrl.fromLocalFile(self.temp_file))
        QMessageBox.information(self, "Mise à jour", "La carte a été mise à jour avec succès.")
    def ouvrir_dialog_import_plan(self):
        dialog = ManageRoutesDialog(self)
        dialog.exec_()
    def mettre_a_jour_carte(self):
        """Met à jour la carte avec les points et segments actuels"""
        # Recréer la carte pour éviter les doublons
        self.creer_carte()

        # Ajouter les points actuels
        for chantier in self.chantiers_valides:
            id_client = chantier.id_client or "Non spécifié"
            localisation = chantier.localisation or "Non spécifiée"
            nature_terrain = chantier.nature_terrain or "Non spécifiée"
            distance_goudron = f"{chantier.distanceAllerGoudron} km" if chantier.distanceAllerGoudron is not None else "Non spécifiée"
            distance_piste = f"{chantier.distanceAllerPiste} km" if chantier.distanceAllerPiste is not None else "Non spécifiée"
            temps_aller = f"{chantier.temps_aller:.2f} h" if chantier.temps_aller is not None else "Non spécifié"

            popup_content = f"""
            <b>ID Client:</b> {id_client}<br>
            <b>Localisation:</b> {localisation}<br>
            <b>Nature du terrain:</b> {nature_terrain}<br>
            <b>Distance goudron:</b> {distance_goudron}<br>
            <b>Distance piste:</b> {distance_piste}<br>
            <b>Temps aller:</b> {temps_aller}
            """

            popup = Popup(popup_content, max_width=300)
            marker = Marker(
                location=[chantier.latitude, chantier.longitude],
                popup=popup,
                tooltip=f"Chantier: {id_client}",
                icon=Icon(color='blue', icon='info-sign')
            )
            marker.add_to(self.carte)

        # Ajouter les segments actuels (si vous avez des segments à afficher)
        for segment in self.segments:
            PolyLine(
                [[segment.from_idx, segment.to_idx]],
                color='green',
                weight=3,
                opacity=0.7,
                tooltip=f"Segment: {segment.distance} km"
            ).add_to(self.carte)

        # Sauvegarder et recharger la carte
        self.carte.save(self.temp_file)
        self.browser.load(QUrl.fromLocalFile(self.temp_file))
        QMessageBox.information(self, "Mise à jour", "La carte a été mise à jour avec succès.")       
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
    

    def ajouter_menu_plans_predefined(self):
        """Ajoute un menu pour gérer les plans d'itinéraires prédéfinis"""
        from PyQt5.QtWidgets import QMenuBar, QMenu, QAction
        
        # Création du menu s'il n'existe pas déjà
        if not hasattr(self, 'menubar'):
            self.menubar = QMenuBar(self)
            self.setMenuBar(self.menubar)
        
        # Menu Plans
        self.menu_plans = QMenu("Plans", self)
        self.menubar.addMenu(self.menu_plans)
        
        # Actions
        action_import_plan = QAction("Importer un plan prédéfini", self)
        action_import_plan.triggered.connect(self.ouvrir_dialog_import_plan)
        self.menu_plans.addAction(action_import_plan)
        
        action_clear_plans = QAction("Effacer tous les plans", self)
        action_clear_plans.triggered.connect(self.reset_carte)
        self.menu_plans.addAction(action_clear_plans)
    def importer_kml(self, fichier):
        """Importe un fichier KML contenant un itinéraire"""
        try:
            # Utiliser une bibliothèque pour parser le KML
            # Par exemple avec fastkml ou pykml
            # Voici une implémentation basique
            import xml.etree.ElementTree as ET
            
            # Espace de noms KML
            ns = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            # Analyser le fichier KML
            tree = ET.parse(fichier)
            root = tree.getroot()
            
            # Rechercher les éléments LineString ou Point
            coords_elements = root.findall('.//kml:LineString/kml:coordinates', ns)
            
            if not coords_elements:
                coords_elements = root.findall('.//kml:Point/kml:coordinates', ns)
            
            if not coords_elements:
                raise Exception("Aucun itinéraire trouvé dans ce fichier KML")
            
            for coords_elem in coords_elements:
                # Format KML: lon,lat,alt lon,lat,alt ...
                coords_text = coords_elem.text.strip()
                
                # Parser les coordonnées
                points = []
                for coord in coords_text.split():
                    if coord.strip():
                        parts = coord.split(',')
                        if len(parts) >= 2:
                            # KML: longitude,latitude[,altitude]
                            # Folium: [latitude, longitude]
                            lon, lat = float(parts[0]), float(parts[1])
                            points.append([lat, lon])
                
                if points:
                    # Ajouter l'itinéraire à la carte
                    PolyLine(
                        points,
                        color='green',
                        weight=4,
                        opacity=0.8,
                        tooltip="Itinéraire topographique importé"
                    ).add_to(self.carte)
            
            # Mettre à jour la carte
            self.carte.save(self.temp_file)
            self.browser.load(QUrl.fromLocalFile(self.temp_file))
            
            QMessageBox.information(self, "Import réussi", 
                                f"Le fichier KML a été importé avec succès.")
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'importation", 
                            f"Impossible d'importer le fichier KML: {str(e)}")

    def ouvrir_dialog_import_plan(self):
        """Ouvre la boîte de dialogue pour importer un plan prédéfini"""
        dialog = ImportPlanDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Récupération des options
            show_markers = dialog.check_markers.isChecked()
            show_routes = dialog.check_routes.isChecked()
            show_distances = dialog.check_distances.isChecked()
            color = dialog.combo_color.currentData()
            
            # Import du plan sélectionné
            selected_plan = dialog.list_plans.currentItem().text()
            if "EGS190" in selected_plan:
                self.ajouter_plan_route_specifique(
                    show_markers=show_markers,
                    show_routes=show_routes,
                    show_distances=show_distances,
                    route_color=color
                )
    def reset_carte(self):
        """Réinitialise la carte en supprimant tous les éléments ajoutés"""
        # Recréer une carte vide
        self.creer_carte()
        QMessageBox.information(self, "Carte réinitialisée", 
                            "La carte a été réinitialisée. Les plans ont été supprimés.")

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
        self.carte.save(self.temp_file)
        self.browser.load(QUrl.fromLocalFile(self.temp_file))
        
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
    def ajouter_bouton_plan_specifique(self):
        """Ajoute un bouton spécifique pour afficher le plan du Sahara"""
        from PyQt5.QtWidgets import QPushButton
        
        # Création du bouton
        self.btn_plan_sahara = QPushButton("Afficher le plan du Sahara (EGS190)")
        self.btn_plan_sahara.clicked.connect(lambda: self.ajouter_plan_route_specifique())
        
        # Le widget central et son layout seront créés plus tard dans creer_carte
        # On stocke le bouton pour l'ajouter plus tard
        self.btn_sahara_to_add = self.btn_plan_sahara
def main():
    app = QApplication(sys.argv)
    fenetre = CarteChantiers()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()