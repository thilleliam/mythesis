import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar, filedialog, BooleanVar
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime, timedelta
import tkinter as tk
import calendar
import pandas as pd
import os
from ttkbootstrap.scrolled import ScrolledFrame
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class DateEntry(ttk.Frame):
    """Widget personnalisé pour la sélection de date"""
    def __init__(self, parent, textvariable_jour, textvariable_mois, textvariable_annee, **kwargs):
        super().__init__(parent, **kwargs)
        photo = tk.PhotoImage(file="C:\\Users\\BIG-computer\\Pictures\\Logo1.png")
        root.iconphoto(False, photo)
        self.jour_var = textvariable_jour
        self.mois_var = textvariable_mois
        self.annee_var = textvariable_annee
        
        # Création des widgets
        self.jour_spin = ttk.Spinbox(self, from_=1, to=31, width=3, textvariable=self.jour_var)
        self.jour_spin.pack(side=tk.LEFT, padx=1)
        
        ttk.Label(self, text="/").pack(side=tk.LEFT)
        
        self.mois_spin = ttk.Spinbox(self, from_=1, to=12, width=3, textvariable=self.mois_var)
        self.mois_spin.pack(side=tk.LEFT, padx=1)
        
        ttk.Label(self, text="/").pack(side=tk.LEFT)
        
        self.annee_spin = ttk.Spinbox(self, from_=2020, to=2030, width=5, textvariable=self.annee_var)
        self.annee_spin.pack(side=tk.LEFT, padx=1)
        
        # Bouton pour afficher un calendrier
        self.calendar_btn = ttk.Button(self, text="📅", width=3, command=self.show_calendar)
        self.calendar_btn.pack(side=tk.LEFT, padx=3)
        
        # Ajouter des validations pour les changements de mois
        self.mois_spin.bind("<FocusOut>", self.validate_day)
        self.annee_spin.bind("<FocusOut>", self.validate_day)
    
    def show_calendar(self):
        """Affiche une fenêtre de calendrier pour sélectionner une date"""
        top = ttk.Toplevel(self)
        top.title("Sélectionner une date")
        top.geometry("300x250")
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()
        
        # Année et mois actuels
        try:
            current_year = int(self.annee_var.get())
            current_month = int(self.mois_var.get())
        except ValueError:
            today = datetime.now()
            current_year = today.year
            current_month = today.month
        
        year_month_frame = ttk.Frame(top)
        year_month_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Boutons pour naviguer entre les mois
        prev_month = ttk.Button(year_month_frame, text="<", width=3, 
                               command=lambda: self.change_month(month_label, -1, cal_frame))
        prev_month.pack(side=tk.LEFT, padx=5)
        
        month_label = ttk.Label(year_month_frame, text=f"{calendar.month_name[current_month]} {current_year}")
        month_label.pack(side=tk.LEFT, expand=True)
        
        next_month = ttk.Button(year_month_frame, text=">", width=3,
                               command=lambda: self.change_month(month_label, 1, cal_frame))
        next_month.pack(side=tk.RIGHT, padx=5)
        
        # Frame pour le calendrier
        cal_frame = ttk.Frame(top)
        cal_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Afficher le calendrier
        self.display_calendar(cal_frame, current_year, current_month, top)
        
    def change_month(self, label, increment, cal_frame):
        """Change le mois affiché dans le calendrier"""
        # Récupérer l'année et le mois actuels
        month_year = label.cget("text").split()
        month_name = month_year[0]
        year = int(month_year[1])
        
        # Trouver le numéro du mois
        month_num = list(calendar.month_name).index(month_name)
        
        # Calculer le nouveau mois
        month_num += increment
        
        if month_num > 12:
            month_num = 1
            year += 1
        elif month_num < 1:
            month_num = 12
            year -= 1
        
        # Mettre à jour le titre
        label.config(text=f"{calendar.month_name[month_num]} {year}")
        
        # Effacer et recréer le calendrier
        for widget in cal_frame.winfo_children():
            widget.destroy()
        
        self.display_calendar(cal_frame, year, month_num, cal_frame.master)
    
    def display_calendar(self, parent, year, month, top):
        """Affiche un calendrier pour le mois et l'année donnés"""
        # Jours de la semaine
        days = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
        
        # Créer les en-têtes
        for i, day in enumerate(days):
            ttk.Label(parent, text=day, width=4).grid(row=0, column=i)
        
        # Obtenir le premier jour du mois et le nombre de jours
        cal = calendar.monthcalendar(year, month)
        
        # Remplir le calendrier
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                if day != 0:
                    btn = ttk.Button(parent, text=str(day), width=4, 
                                    command=lambda d=day: self.set_date(d, month, year, top))
                    btn.grid(row=week_idx+1, column=day_idx, padx=1, pady=1)
    
    def set_date(self, day, month, year, top):
        """Définit la date sélectionnée"""
        self.jour_var.set(str(day))
        self.mois_var.set(str(month))
        self.annee_var.set(str(year))
        top.destroy()
    
    def validate_day(self, event=None):
        """Valide que le jour est valide pour le mois et l'année choisis"""
        try:
            jour = int(self.jour_var.get())
            mois = int(self.mois_var.get())
            annee = int(self.annee_var.get())
            
            # Obtenir le dernier jour du mois
            _, last_day = calendar.monthrange(annee, mois)
            
            # Ajuster si nécessaire
            if jour > last_day:
                self.jour_var.set(str(last_day))
        except ValueError:
            pass  # Ignorer si les valeurs ne sont pas des nombres

class TimeEntry(ttk.Frame):
    """Widget personnalisé pour la sélection d'heure"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.hour_var = tk.StringVar(value="0")
        self.minute_var = tk.StringVar(value="0")
        
        # Création des widgets
        self.hour_spin = ttk.Spinbox(self, from_=0, to=23, width=3, textvariable=self.hour_var)
        self.hour_spin.pack(side=tk.LEFT, padx=1)
        
        ttk.Label(self, text=":").pack(side=tk.LEFT)
        
        self.minute_spin = ttk.Spinbox(self, from_=0, to=59, width=3, textvariable=self.minute_var)
        self.minute_spin.pack(side=tk.LEFT, padx=1)
    
    def get(self):
        """Renvoie l'heure et les minutes sous forme de tuple"""
        try:
            return int(self.hour_var.get()), int(self.minute_var.get())
        except ValueError:
            return 0, 0
    
    def set(self, hour, minute):
        """Définit l'heure et les minutes"""
        self.hour_var.set(str(hour))
        self.minute_var.set(str(minute))

class DateTimeEntry(ttk.Frame):
    """Widget combiné pour date et heure"""
    def __init__(self, parent, jour_var, mois_var, annee_var, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Création des widgets
        self.date_entry = DateEntry(self, jour_var, mois_var, annee_var)
        self.date_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.time_entry = TimeEntry(self)
        self.time_entry.pack(side=tk.LEFT)
    
    def get_datetime(self):
        """Renvoie la date et l'heure sous forme d'objet datetime"""
        try:
            jour = int(self.date_entry.jour_var.get())
            mois = int(self.date_entry.mois_var.get())
            annee = int(self.date_entry.annee_var.get())
            
            hour, minute = self.time_entry.get()
            
            return datetime(annee, mois, jour, hour, minute)
        except (ValueError, OverflowError):
            return None
    
    def set_datetime(self, dt):
        """Définit la date et l'heure à partir d'un objet datetime"""
        if dt:
            self.date_entry.jour_var.set(str(dt.day))
            self.date_entry.mois_var.set(str(dt.month))
            self.date_entry.annee_var.set(str(dt.year))
            self.time_entry.set(dt.hour, dt.minute)
        else:
            today = datetime.now()
            self.date_entry.jour_var.set(str(today.day))
            self.date_entry.mois_var.set(str(today.month))
            self.date_entry.annee_var.set(str(today.year))
            self.time_entry.set(0, 0)

class SearchFrame(ttk.Frame):
    """Frame pour la recherche et le filtrage"""
    def __init__(self, parent, search_function, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.search_function = search_function
        
        # Variables
        self.search_var = StringVar()
        self.filter_conducteur_var = StringVar()
        self.filter_vehicule_var = StringVar()
        self.filter_date_active = BooleanVar(value=False)
        self.date_debut_var = StringVar(value=datetime.now().strftime("%d/%m/%Y"))
        self.date_fin_var = StringVar(value=(datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"))
        
        # Layout
        search_label = ttk.Label(self, text="Rechercher:")
        search_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        search_entry = ttk.Entry(self, textvariable=self.search_var, width=30)
        search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        search_entry.bind("<KeyRelease>", lambda e: self.search_function())
        
        # Frame pour les filtres
        filter_frame = ttk.LabelFrame(self, text="Filtres", padding=5)
        filter_frame.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=tk.EW)
        
        # Filtre par conducteur
        ttk.Label(filter_frame, text="Conducteur:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.conducteur_cb = ttk.Combobox(filter_frame, textvariable=self.filter_conducteur_var, width=20)
        self.conducteur_cb.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        self.conducteur_cb.bind("<<ComboboxSelected>>", lambda e: self.search_function())
        
        # Filtre par véhicule
        ttk.Label(filter_frame, text="Véhicule:").grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        self.vehicule_cb = ttk.Combobox(filter_frame, textvariable=self.filter_vehicule_var, width=20)
        self.vehicule_cb.grid(row=0, column=3, padx=5, pady=2, sticky=tk.W)
        self.vehicule_cb.bind("<<ComboboxSelected>>", lambda e: self.search_function())
        
        # Filtre par période
        date_check = ttk.Checkbutton(filter_frame, text="Filtrer par période", variable=self.filter_date_active,
                                    command=self.toggle_date_filter)
        date_check.grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        
        date_frame = ttk.Frame(filter_frame)
        date_frame.grid(row=1, column=1, columnspan=3, padx=5, pady=2, sticky=tk.W)
        
        ttk.Label(date_frame, text="Du:").pack(side=tk.LEFT, padx=5)
        self.date_debut_entry = ttk.Entry(date_frame, textvariable=self.date_debut_var, width=10)
        self.date_debut_entry.pack(side=tk.LEFT, padx=2)
        self.date_debut_entry.configure(state="disabled")
        
        ttk.Label(date_frame, text="Au:").pack(side=tk.LEFT, padx=5)
        self.date_fin_entry = ttk.Entry(date_frame, textvariable=self.date_fin_var, width=10)
        self.date_fin_entry.pack(side=tk.LEFT, padx=2)
        self.date_fin_entry.configure(state="disabled")
        
        # Bouton de réinitialisation des filtres
        reset_btn = ttk.Button(self, text="Réinitialiser les filtres", command=self.reset_filters)
        reset_btn.grid(row=2, column=3, padx=5, pady=5, sticky=tk.E)
    
    def toggle_date_filter(self):
        """Active ou désactive le filtre par date"""
        state = "normal" if self.filter_date_active.get() else "disabled"
        self.date_debut_entry.configure(state=state)
        self.date_fin_entry.configure(state=state)
        self.search_function()
    
    def reset_filters(self):
        """Réinitialise tous les filtres"""
        self.search_var.set("")
        self.filter_conducteur_var.set("")
        self.filter_vehicule_var.set("")
        self.filter_date_active.set(False)
        self.toggle_date_filter()
        self.search_function()
    
    def update_filter_lists(self, conducteurs, vehicules):
        """Met à jour les listes de filtres"""
        self.conducteur_cb['values'] = [""] + [f"{c.id_conducteur} - {c.nom} {c.prenom}" for c in conducteurs]
        self.vehicule_cb['values'] = [""] + [f"{v.immatriculation} - {v.marque_modele}" for v in vehicules]

class TourneeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Tournées")
        self.root.geometry("1200x700")
        
        # Style
        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("TEntry", font=("Segoe UI", 10))
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        
        # Import local pour éviter les imports circulaires
        from application.models.tournee import Tournee
        
        self.Tournee = Tournee
        
        # Variables
        self.id_tournee_var = StringVar()
        self.id_conducteur_var = StringVar()
        self.immatriculation_var = StringVar()
        self.id_commande_var = StringVar()
        self.objectif_var = StringVar()
        self.lieu_depart_var = StringVar()
        self.destination_var = StringVar()
        self.itineraire_var = StringVar()
        self.km_parcouru_var = StringVar()
        
        # Variables pour les dates
        self.jour_depart_var = StringVar()
        self.mois_depart_var = StringVar()
        self.annee_depart_var = StringVar()
        
        self.jour_reception_var = StringVar()
        self.mois_reception_var = StringVar()
        self.annee_reception_var = StringVar()
        
        self.jour_retour_var = StringVar()
        self.mois_retour_var = StringVar()
        self.annee_retour_var = StringVar()
        
        self.jour_arrivee_var = StringVar()
        self.mois_arrivee_var = StringVar()
        self.annee_arrivee_var = StringVar()
        
        # Initialiser les dates à aujourd'hui
        today = datetime.now()
        for var in [self.jour_depart_var, self.jour_reception_var, self.jour_retour_var, self.jour_arrivee_var]:
            var.set(str(today.day))
        for var in [self.mois_depart_var, self.mois_reception_var, self.mois_retour_var, self.mois_arrivee_var]:
            var.set(str(today.month))
        for var in [self.annee_depart_var, self.annee_reception_var, self.annee_retour_var, self.annee_arrivee_var]:
            var.set(str(today.year))
        
        # Données pour les combobox
        self.conducteurs = []
        self.vehicules = []
        self.commandes = []
        self.charger_listes_dependantes()
        
        # Création de l'interface
        self.create_notebook()
        # Charger les données
        self.charger_donnees()
    
    def create_notebook(self):
        """Crée l'interface à onglets"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Onglet Liste des tournées
        self.list_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.list_tab, text="Liste des tournées")
        
        # Onglet Formulaire
        self.form_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.form_tab, text="Ajouter/Modifier une tournée")
        
        # Onglet Statistiques
        self.stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_tab, text="Statistiques")
        
        # Construire chaque onglet
        self.build_list_tab()
        self.build_form_tab()
        self.build_stats_tab()
        
        # Événement de changement d'onglet
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_tab_changed(self, event):
        """Gestion du changement d'onglet"""
        tab_id = self.notebook.index(self.notebook.select())
        
        # Si l'onglet des statistiques est sélectionné
        if tab_id == 2:  # Stats tab
            self.update_stats()
    def nouvelle_tournee(self):
        """Prépare le formulaire pour une nouvelle tournée"""
        self.vider_formulaire()
        self.notebook.select(1)  # Switch to the form tab
    
    def build_list_tab(self):
        """Construit l'onglet de liste des tournées"""
        # Frame de recherche
        self.search_frame = SearchFrame(self.list_tab, self.filtrer_donnees)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)
        self.search_frame.update_filter_lists(self.conducteurs, self.vehicules)
        
        # Barre d'outils
        toolbar = ttk.Frame(self.list_tab)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Boutons
        new_btn = ttk.Button(toolbar, text="Nouvelle tournée", 
                           command=self.nouvelle_tournee, bootstyle=SUCCESS)
        new_btn.pack(side=tk.LEFT, padx=2)
        
        edit_btn = ttk.Button(toolbar, text="Modifier", 
                            command=self.editer_tournee_selectionnee, bootstyle=WARNING)
        edit_btn.pack(side=tk.LEFT, padx=2)
        
        delete_btn = ttk.Button(toolbar, text="Supprimer", 
                                     command=self.supprimer, bootstyle=DANGER)
        delete_btn.pack(side=tk.LEFT, padx=2)
        
        view_duration_btn = ttk.Button(toolbar, text="Voir détails", 
                                     command=self.afficher_details, bootstyle=INFO)
        view_duration_btn.pack(side=tk.LEFT, padx=2)
        
        export_btn = ttk.Button(toolbar, text="Exporter", 
                              command=self.exporter_donnees, bootstyle=SECONDARY)
        export_btn.pack(side=tk.RIGHT, padx=2)
        
        refresh_btn = ttk.Button(toolbar, text="Actualiser", 
                               command=self.charger_donnees, bootstyle=DEFAULT)
        refresh_btn.pack(side=tk.RIGHT, padx=2)
        
        # Tableau avec scrollbars
        table_frame = ttk.Frame(self.list_tab)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Créer les scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")
        
        # Colonnes
        columns = ("id_tournee", "conducteur", "vehicule", "commande", "objectif", 
                  "depart", "destination", "km", "date_depart", "date_arrivee", "duree", "statut")
        
        # Créer le Treeview avec référence aux scrollbars
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", 
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                bootstyle="primary")
        
        # Configurer les scrollbars pour commander le Treeview
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Placement en utilisant grid pour un meilleur contrôle
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        # Configurer grid pour s'adapter correctement
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Définir les entêtes
        self.tree.heading("id_tournee", text="ID", command=lambda: self.treeview_sort_column("id_tournee", False))
        self.tree.heading("conducteur", text="Conducteur", command=lambda: self.treeview_sort_column("conducteur", False))
        self.tree.heading("vehicule", text="Véhicule", command=lambda: self.treeview_sort_column("vehicule", False))
        self.tree.heading("commande", text="Commande", command=lambda: self.treeview_sort_column("commande", False))
        self.tree.heading("objectif", text="Objectif", command=lambda: self.treeview_sort_column("objectif", False))
        self.tree.heading("depart", text="Départ", command=lambda: self.treeview_sort_column("depart", False))
        self.tree.heading("destination", text="Destination", command=lambda: self.treeview_sort_column("destination", False))
        self.tree.heading("km", text="KM", command=lambda: self.treeview_sort_column("km", False))
        self.tree.heading("date_depart", text="Départ le", command=lambda: self.treeview_sort_column("date_depart", False))
        self.tree.heading("date_arrivee", text="Arrivée le", command=lambda: self.treeview_sort_column("date_arrivee", False))
        self.tree.heading("duree", text="Durée", command=lambda: self.treeview_sort_column("duree", False))
        self.tree.heading("statut", text="Statut", command=lambda: self.treeview_sort_column("statut", False))
        
        # Configurer les colonnes
        self.tree.column("id_tournee", width=50, minwidth=50)
        self.tree.column("conducteur", width=120, minwidth=100)
        self.tree.column("vehicule", width=120, minwidth=100)
        self.tree.column("commande", width=120, minwidth=100)
        self.tree.column("objectif", width=150, minwidth=100)
        self.tree.column("depart", width=100, minwidth=100)
        self.tree.column("destination", width=100, minwidth=100)
        self.tree.column("km", width=60, minwidth=50)
        self.tree.column("date_depart", width=120, minwidth=100)
        self.tree.column("date_arrivee", width=120, minwidth=100)
        self.tree.column("duree", width=80, minwidth=80)
        self.tree.column("statut", width=80, minwidth=80)
        
        # Liaison à la sélection
        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        
        # Barre de statut
        self.status_var = StringVar()
        status_bar = ttk.Label(self.list_tab, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5)
    
    def build_form_tab(self):
        """Construit l'onglet de formulaire"""
        # Création d'un ScrolledFrame pour le formulaire
        form_scroll = ScrolledFrame(self.form_tab, autohide=True)
        form_scroll.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame principal
        main_form = ttk.Frame(form_scroll)
        main_form.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ID Tournée (hidden)
        self.id_tournee_entry = ttk.Entry(main_form, textvariable=self.id_tournee_var, state="readonly")
        
        # Informations générales
        info_frame = ttk.LabelFrame(main_form, text="Informations générales", padding=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)
        
        # Première ligne
        ttk.Label(info_grid, text="Conducteur", width=15).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.conducteur_cb = ttk.Combobox(info_grid, textvariable=self.id_conducteur_var, state="readonly", width=40)
        self.conducteur_cb.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.conducteur_cb['values'] = [f"{c.id_conducteur} - {c.nom} {c.prenom}" for c in self.conducteurs]
        
        ttk.Label(info_grid, text="Véhicule", width=15).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.vehicule_cb = ttk.Combobox(info_grid, textvariable=self.immatriculation_var, state="readonly", width=40)
        self.vehicule_cb.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.vehicule_cb['values'] = [f"{v.immatriculation} - {v.marque_modele}" for v in self.vehicules]
        ttk.Label(info_grid, text="Commande", width=15).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.commande_cb = ttk.Combobox(info_grid, textvariable=self.id_commande_var, state="readonly", width=40)
        self.commande_cb.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.commande_cb['values'] = [f"{c.id_commande} - {c.nature_service}" for c in self.commandes]
        
        ttk.Label(info_grid, text="Objectif", width=15).grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        objectif_entry = ttk.Entry(info_grid, textvariable=self.objectif_var, width=40)
        objectif_entry.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Troisième ligne
        ttk.Label(info_grid, text="Lieu de départ", width=15).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        depart_entry = ttk.Entry(info_grid, textvariable=self.lieu_depart_var, width=40)
        depart_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_grid, text="Destination", width=15).grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        destination_entry = ttk.Entry(info_grid, textvariable=self.destination_var, width=40)
        destination_entry.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Quatrième ligne
        ttk.Label(info_grid, text="Itinéraire", width=15).grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        itineraire_entry = ttk.Entry(info_grid, textvariable=self.itineraire_var, width=40)
        itineraire_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(info_grid, text="KM parcourus", width=15).grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)
        km_entry = ttk.Entry(info_grid, textvariable=self.km_parcouru_var, width=40)
        km_entry.grid(row=3, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Dates et heures
        dates_frame = ttk.LabelFrame(main_form, text="Dates et heures", padding=10)
        dates_frame.pack(fill=tk.X, pady=5)
        
        dates_grid = ttk.Frame(dates_frame)
        dates_grid.pack(fill=tk.X)
        
        # Première ligne - Départ
        ttk.Label(dates_grid, text="Date de départ", width=15).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        depart_date_frame = ttk.Frame(dates_grid)
        depart_date_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.depart_date_widget = DateTimeEntry(depart_date_frame, 
                                               self.jour_depart_var, 
                                               self.mois_depart_var, 
                                               self.annee_depart_var)
        self.depart_date_widget.pack(fill=tk.X)
        
        # Initialisation des attributs pour les heures et minutes
        self.heure_depart = self.depart_date_widget.time_entry.hour_var
        self.minute_depart = self.depart_date_widget.time_entry.minute_var
        
        # Deuxième ligne - Arrivée
        ttk.Label(dates_grid, text="Date d'arrivée", width=15).grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        arrivee_date_frame = ttk.Frame(dates_grid)
        arrivee_date_frame.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        self.arrivee_date_widget = DateTimeEntry(arrivee_date_frame, 
                                                self.jour_arrivee_var, 
                                                self.mois_arrivee_var, 
                                                self.annee_arrivee_var)
        self.arrivee_date_widget.pack(fill=tk.X)
        
        # Initialisation des attributs pour les heures et minutes
        self.heure_arrivee = self.arrivee_date_widget.time_entry.hour_var
        self.minute_arrivee = self.arrivee_date_widget.time_entry.minute_var
        
        # Troisième ligne - Réception
        ttk.Label(dates_grid, text="Date de réception", width=15).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        reception_date_frame = ttk.Frame(dates_grid)
        reception_date_frame.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        self.reception_date_widget = DateTimeEntry(reception_date_frame, 
                                                  self.jour_reception_var, 
                                                  self.mois_reception_var, 
                                                  self.annee_reception_var)
        self.reception_date_widget.pack(fill=tk.X)
        
        # Initialisation des attributs pour les heures et minutes
        self.heure_reception = self.reception_date_widget.time_entry.hour_var
        self.minute_reception = self.reception_date_widget.time_entry.minute_var
        
        # Quatrième ligne - Retour
        ttk.Label(dates_grid, text="Date de retour", width=15).grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        retour_date_frame = ttk.Frame(dates_grid)
        retour_date_frame.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        self.retour_date_widget = DateTimeEntry(retour_date_frame, 
                                               self.jour_retour_var, 
                                               self.mois_retour_var, 
                                               self.annee_retour_var)
        self.retour_date_widget.pack(fill=tk.X)
        
        # Initialisation des attributs pour les heures et minutes
        self.heure_retour = self.retour_date_widget.time_entry.hour_var
        self.minute_retour = self.retour_date_widget.time_entry.minute_var
        
        # Boutons d'action
        buttons_frame = ttk.Frame(main_form)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        save_btn = ttk.Button(buttons_frame, text="Enregistrer", command=self.enregistrer, bootstyle=SUCCESS)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(buttons_frame, text="Effacer", command=self.vider_formulaire, bootstyle=WARNING)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(buttons_frame, text="Annuler", command=lambda: self.notebook.select(0), bootstyle=DANGER)
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def build_stats_tab(self):
        """Construit l'onglet des statistiques avec une barre de défilement"""
        # Frame principal
        stats_main = ttk.Frame(self.stats_tab)
        stats_main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Ajouter un ScrolledFrame pour permettre le défilement
        self.stats_scroll = ScrolledFrame(stats_main, autohide=True)
        self.stats_scroll.pack(fill=tk.BOTH, expand=True)

        # Conteneur pour les graphiques (à l'intérieur du ScrolledFrame)
        self.stats_frame = ttk.Frame(self.stats_scroll)
        self.stats_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Panneau de filtrage pour les statistiques
        filter_frame = ttk.LabelFrame(self.stats_frame, text="Filtres", padding=10)
        filter_frame.pack(fill=tk.X, pady=5)

        # Filtres de date
        date_filter_frame = ttk.Frame(filter_frame)
        date_filter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(date_filter_frame, text="Du:").pack(side=tk.LEFT, padx=5)

        self.stats_date_debut_var = StringVar()
        self.stats_date_debut_jour_var = StringVar(value=str(date.today().day))
        self.stats_date_debut_mois_var = StringVar(value=str(date.today().month))
        self.stats_date_debut_annee_var = StringVar(value=str(date.today().year - 1))

        self.stats_date_debut_widget = DateEntry(date_filter_frame, 
                                                self.stats_date_debut_jour_var, 
                                                self.stats_date_debut_mois_var, 
                                                self.stats_date_debut_annee_var)
        self.stats_date_debut_widget.pack(side=tk.LEFT, padx=5)

        ttk.Label(date_filter_frame, text="Au:").pack(side=tk.LEFT, padx=5)

        self.stats_date_fin_var = StringVar()
        self.stats_date_fin_jour_var = StringVar(value=str(date.today().day))
        self.stats_date_fin_mois_var = StringVar(value=str(date.today().month))
        self.stats_date_fin_annee_var = StringVar(value=str(date.today().year))

        self.stats_date_fin_widget = DateEntry(date_filter_frame, 
                                            self.stats_date_fin_jour_var, 
                                            self.stats_date_fin_mois_var, 
                                            self.stats_date_fin_annee_var)
        self.stats_date_fin_widget.pack(side=tk.LEFT, padx=5)

        # Bouton pour appliquer les filtres
        apply_filter_btn = ttk.Button(date_filter_frame, text="Appliquer", command=self.update_stats, bootstyle=INFO)
        apply_filter_btn.pack(side=tk.LEFT, padx=15)

        # Divisé en deux colonnes
        col1_frame = ttk.Frame(self.stats_frame)
        col1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        col2_frame = ttk.Frame(self.stats_frame)
        col2_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Graphiques pour la première colonne
        self.km_par_conducteur_frame = ttk.LabelFrame(col1_frame, text="Kilomètres par conducteur", padding=10)
        self.km_par_conducteur_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tournees_par_mois_frame = ttk.LabelFrame(col1_frame, text="Nombre de tournées par mois", padding=10)
        self.tournees_par_mois_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Graphiques pour la deuxième colonne
        self.km_par_vehicule_frame = ttk.LabelFrame(col2_frame, text="Kilomètres par véhicule", padding=10)
        self.km_par_vehicule_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.duree_moyenne_frame = ttk.LabelFrame(col2_frame, text="Durée moyenne des tournées", padding=10)
        self.duree_moyenne_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Statistiques générales
        stats_summary_frame = ttk.LabelFrame(self.stats_frame, text="Résumé", padding=10)
        stats_summary_frame.pack(fill=tk.X, pady=5)

        self.stats_summary_text = ttk.Label(stats_summary_frame, text="", font=("Segoe UI", 10))
        self.stats_summary_text.pack(fill=tk.X, padx=10, pady=5)

        # Bouton pour exporter les statistiques
        export_stats_btn = ttk.Button(self.stats_frame, text="Exporter les statistiques", command=self.exporter_statistiques, bootstyle=SUCCESS)
        export_stats_btn.pack(anchor=tk.E, padx=10, pady=10)

    def editer_tournee_selectionnee(self):
        """Édite la tournée sélectionnée dans le tableau"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une tournée à modifier")
            return
            
        # Récupère l'ID de la tournée sélectionnée
        item = self.tree.item(selection[0])
        id_tournee = item['values'][0]
        
        # Charger les données de la tournée
        tournee = session.query(self.Tournee).get(id_tournee)
        if not tournee:
            messagebox.showerror("Erreur", "Tournée non trouvée")
            return
            
        # Remplir le formulaire avec les données de la tournée
        self.id_tournee_var.set(str(tournee.id_tournee))
        
        # Remplir les combobox
        if tournee.conducteur:
            self.id_conducteur_var.set(f"{tournee.id_conducteur} - {tournee.conducteur.nom} {tournee.conducteur.prenom}")
        
        if tournee.vehicule:
            self.immatriculation_var.set(f"{tournee.immatriculation_vehicule} - {tournee.vehicule.marque_modele}")
        
        if tournee.commande:
            self.id_commande_var.set(f"{tournee.id_commande} - {tournee.commande.nature_service}")
        
        # Remplir les champs texte
        self.objectif_var.set(tournee.objectif or "")
        self.lieu_depart_var.set(tournee.lieu_depart or "")
        self.destination_var.set(tournee.destination or "")
        self.itineraire_var.set(tournee.itineraire or "")
        self.km_parcouru_var.set(str(tournee.km_parcouru) if tournee.km_parcouru else "")
        
        # Remplir les dates
        self.set_datetime_widgets(tournee.date_heure_depart, 
                                 self.jour_depart_var, self.mois_depart_var, self.annee_depart_var,
                                 self.heure_depart, self.minute_depart)
        
        self.set_datetime_widgets(tournee.date_heure_arrivee, 
                                 self.jour_arrivee_var, self.mois_arrivee_var, self.annee_arrivee_var,
                                 self.heure_arrivee, self.minute_arrivee)
        
        self.set_datetime_widgets(tournee.date_heure_reception, 
                                 self.jour_reception_var, self.mois_reception_var, self.annee_reception_var,
                                 self.heure_reception, self.minute_reception)
        
        self.set_datetime_widgets(tournee.date_heure_retour, 
                                 self.jour_retour_var, self.mois_retour_var, self.annee_retour_var,
                                 self.heure_retour, self.minute_retour)
        
        # Passer à l'onglet du formulaire
        self.notebook.select(1)

    def afficher_details(self):
        """Affiche les détails de la tournée sélectionnée"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner une tournée")
            return
            
        # Récupère l'ID de la tournée sélectionnée
        item = self.tree.item(selection[0])
        id_tournee = item['values'][0]
        
        # Charger les données de la tournée
        tournee = session.query(self.Tournee).get(id_tournee)
        if not tournee:
            messagebox.showerror("Erreur", "Tournée non trouvée")
            return
            
        # Créer une fenêtre de détails
        details_window = ttk.Toplevel(self.root)
        details_window.title(f"Détails de la tournée #{tournee.id_tournee}")
        details_window.geometry("600x500")
        details_window.resizable(True, True)
        
        # Frame principal
        main_frame = ttk.Frame(details_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Informations générales
        ttk.Label(main_frame, text=f"Tournée #{tournee.id_tournee}", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        # Conducteur
        conductor_frame = ttk.LabelFrame(main_frame, text="Conducteur", padding=10)
        conductor_frame.pack(fill=tk.X, pady=5)
        
        conductor_info = "Non assigné"
        if tournee.conducteur:
            conductor_info = f"{tournee.conducteur.nom} {tournee.conducteur.prenom}"
            if hasattr(tournee.conducteur, 'telephone'):
                conductor_info += f" - Tél: {tournee.conducteur.telephone}"
        
        ttk.Label(conductor_frame, text=conductor_info).pack(anchor=tk.W)
        
        # Véhicule
        vehicle_frame = ttk.LabelFrame(main_frame, text="Véhicule", padding=10)
        vehicle_frame.pack(fill=tk.X, pady=5)
        
        vehicle_info = "Non assigné"
        if tournee.vehicule:
            vehicle_info = f"{tournee.vehicule.marque_modele} - {tournee.immatriculation_vehicule}"
            if hasattr(tournee.vehicule, 'type_vehicule'):
                vehicle_info += f" - Type: {tournee.vehicule.type_vehicule}"
        
        ttk.Label(vehicle_frame, text=vehicle_info).pack(anchor=tk.W)
        
        # Mission
        mission_frame = ttk.LabelFrame(main_frame, text="Mission", padding=10)
        mission_frame.pack(fill=tk.X, pady=5)
        
        mission_grid = ttk.Frame(mission_frame)
        mission_grid.pack(fill=tk.X)
        
        ttk.Label(mission_grid, text="Objectif:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(mission_grid, text=tournee.objectif or "Non spécifié").grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(mission_grid, text="Départ:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(mission_grid, text=tournee.lieu_depart or "Non spécifié").grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(mission_grid, text="Destination:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(mission_grid, text=tournee.destination or "Non spécifié").grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(mission_grid, text="Itinéraire:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(mission_grid, text=tournee.itineraire or "Non spécifié").grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(mission_grid, text="Distance:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(mission_grid, text=f"{tournee.km_parcouru} km" if tournee.km_parcouru else "Non spécifié").grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Dates
        dates_frame = ttk.LabelFrame(main_frame, text="Dates et heures", padding=10)
        dates_frame.pack(fill=tk.X, pady=5)
        
        dates_grid = ttk.Frame(dates_frame)
        dates_grid.pack(fill=tk.X)
        
        ttk.Label(dates_grid, text="Départ:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(dates_grid, text=tournee.date_heure_depart.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_depart else "Non spécifié").grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(dates_grid, text="Arrivée:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(dates_grid, text=tournee.date_heure_arrivee.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_arrivee else "Non spécifié").grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(dates_grid, text="Réception:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(dates_grid, text=tournee.date_heure_reception.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_reception else "Non spécifié").grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(dates_grid, text="Retour:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(dates_grid, text=tournee.date_heure_retour.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_retour else "Non spécifié").grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Durée
        if tournee.date_heure_depart and tournee.date_heure_arrivee:
            duree = tournee.date_heure_arrivee - tournee.date_heure_depart
            heures = duree.total_seconds() // 3600
            minutes = (duree.total_seconds() % 3600) // 60
            
            ttk.Label(dates_grid, text="Durée totale:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)
            ttk.Label(dates_grid, text=f"{int(heures)}h {int(minutes)}min").grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Boutons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        close_btn = ttk.Button(buttons_frame, text="Fermer", command=details_window.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        edit_btn = ttk.Button(buttons_frame, text="Modifier", command=lambda: [details_window.destroy(), self.editer_tournee_selectionnee()])
        edit_btn.pack(side=tk.RIGHT, padx=5)

    def get_datetime(self, jour_var, mois_var, annee_var, heure_var, minute_var):
        """Convertit les variables de date et heure en objet datetime"""
        try:
            jour = int(jour_var.get())
            mois = int(mois_var.get())
            annee = int(annee_var.get())
            heure = int(heure_var.get())
            minute = int(minute_var.get())
            
            return datetime(annee, mois, jour, heure, minute)
        except (ValueError, TypeError):
            return None

    def set_datetime_widgets(self, dt, jour_var, mois_var, annee_var, heure_var, minute_var):
        """Définit les widgets de date et heure à partir d'un objet datetime"""
        if dt:
            jour_var.set(str(dt.day))
            mois_var.set(str(dt.month))
            annee_var.set(str(dt.year))
            heure_var.set(str(dt.hour))
            minute_var.set(str(dt.minute))
        else:
            today = datetime.now()
            jour_var.set(str(today.day))
            mois_var.set(str(today.month))
            annee_var.set(str(today.year))
            heure_var.set("0")
            minute_var.set("0")

    def charger_listes_dependantes(self):
        """Charge les listes de conducteurs, véhicules et commandes"""
        try:
            # Import local pour éviter les imports circulaires
            from application.models.conducteurs import Conducteur
            from application.models.vehicule import Vehicule
            from application.models.commande import Commande
            
            self.conducteurs = session.query(Conducteur).all()
            self.vehicules = session.query(Vehicule).all()
            self.commandes = session.query(Commande).all()
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données: {str(e)}")

    def on_tree_select(self, event):
        """Gestion de l'événement de sélection dans le tableau"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            id_tournee = item['values'][0]
            self.id_tournee_var.set(str(id_tournee))
            self.status_var.set(f"Tournée #{id_tournee} sélectionnée")
        else:
            self.id_tournee_var.set("")
            self.status_var.set("")

    def on_tree_double_click(self, event):
        """Gestion du double-clic sur une ligne du tableau"""
        selection = self.tree.selection()
        if selection:
            self.editer_tournee_selectionnee()

    def treeview_sort_column(self, col, reverse):
        """Trie les données du tableau par colonne"""
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # Convertir les données en nombres si possible
        try:
            data = [(float(item[0]) if item[0].replace('.', '', 1).isdigit() else item[0], item[1]) for item in data]
        except ValueError:
            pass
        
        data.sort(reverse=reverse)
        
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
        
        # Changer le sens du tri pour le prochain clic
        self.tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))

    def filtrer_donnees(self):
        """Filtre les données du tableau selon les critères de recherche"""
        search_term = self.search_frame.search_var.get().lower()
        conducteur_filter = self.search_frame.filter_conducteur_var.get()
        vehicule_filter = self.search_frame.filter_vehicule_var.get()
        date_filter_active = self.search_frame.filter_date_active.get()
            
        # Effacer les données existantes
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Charger les nouvelles données filtrées
        tournees = session.query(self.Tournee).all()
        for tournee in tournees:
            # Appliquer les filtres
            if conducteur_filter and not tournee.id_conducteur == conducteur_filter.split(" - ")[0]:
                continue
            if vehicule_filter and not tournee.immatriculation_vehicule == vehicule_filter.split(" - ")[0]:
                continue
            
            # Filtre par date
            if date_filter_active:
                try:
                    date_debut = datetime.strptime(self.search_frame.date_debut_var.get(), "%d/%m/%Y")
                    date_fin = datetime.strptime(self.search_frame.date_fin_var.get(), "%d/%m/%Y")
                    
                    if tournee.date_heure_depart and not (date_debut <= tournee.date_heure_depart.date() <= date_fin):
                        continue
                except ValueError:
                    pass
            
            # Filtre par terme de recherche
            if search_term:
                search_fields = [
                    str(tournee.id_tournee),
                    tournee.conducteur.nom if tournee.conducteur else "",
                    tournee.conducteur.prenom if tournee.conducteur else "",
                    tournee.vehicule.marque_modele if tournee.vehicule else "",
                    tournee.commande.nature_service if tournee.commande else "",
                    tournee.objectif,
                    tournee.lieu_depart,
                    tournee.destination,
                    str(tournee.km_parcouru),
                    tournee.date_heure_depart.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_depart else "",
                    tournee.date_heure_arrivee.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_arrivee else "",
                ]
                if not any(search_term in str(field).lower() for field in search_fields):
                    continue
            
            # Calcul de la durée
            duree = ""
            if tournee.date_heure_depart and tournee.date_heure_arrivee:
                delta = tournee.date_heure_arrivee - tournee.date_heure_depart
                heures = delta.total_seconds() // 3600
                minutes = (delta.total_seconds() % 3600) // 60
                duree = f"{int(heures)}h {int(minutes)}min"
            
            # Formatage des dates
            date_depart = tournee.date_heure_depart.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_depart else ""
            date_arrivee = tournee.date_heure_arrivee.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_arrivee else ""
            
            # Insertion dans le tableau
            self.tree.insert("", "end", values=(
                tournee.id_tournee,
                f"{tournee.conducteur.nom} {tournee.conducteur.prenom}" if tournee.conducteur else "",
                f"{tournee.vehicule.marque_modele}" if tournee.vehicule else "",
                f"{tournee.commande.nature_service}" if tournee.commande else "",
                tournee.objectif,
                tournee.lieu_depart,
                tournee.destination,
                tournee.km_parcouru,
                date_depart,
                date_arrivee,
                duree
            ))

    def exporter_donnees(self):
        """Exporte les données du tableau vers un fichier CSV"""
        try:
            # Demander à l'utilisateur où enregistrer le fichier
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Fichiers CSV", "*.csv")],
                title="Enregistrer les données"
            )
            if not file_path:  # Si l'utilisateur annule
                return
            
            # Récupérer les données du tableau
            data = []
            for item in self.tree.get_children():
                values = self.tree.item(item, 'values')
                data.append(values)
            
            # Créer un DataFrame pandas avec les données
            columns = [self.tree.heading(col)['text'] for col in self.tree['columns']]
            df = pd.DataFrame(data, columns=columns)
            
            # Exporter le DataFrame en CSV
            df.to_csv(file_path, index=False, encoding='utf-8')
            messagebox.showinfo("Succès", f"Les données ont été exportées avec succès vers {file_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exporter les données : {str(e)}")

    def update_stats(self):
        """Met à jour les statistiques affichées"""
        try:
            # Récupérer les dates de filtrage
            date_debut = datetime(
                int(self.stats_date_debut_annee_var.get()),
                int(self.stats_date_debut_mois_var.get()),
                int(self.stats_date_debut_jour_var.get())
            )
            date_fin = datetime(
                int(self.stats_date_fin_annee_var.get()),
                int(self.stats_date_fin_mois_var.get()),
                int(self.stats_date_fin_jour_var.get())
            )
            
            # Filtrer les tournées
            tournees = session.query(self.Tournee).filter(
                self.Tournee.date_heure_depart >= date_debut,
                self.Tournee.date_heure_depart <= date_fin
            ).all()
            
            # Calcul des statistiques
            km_par_conducteur = {}
            km_par_vehicule = {}
            tournees_par_mois = {}
            durees = []
            
            for tournee in tournees:
                # Kilomètres par conducteur
                if tournee.conducteur:
                    conducteur = f"{tournee.conducteur.nom} {tournee.conducteur.prenom}"
                    km_par_conducteur[conducteur] = km_par_conducteur.get(conducteur, 0) + (tournee.km_parcouru or 0)
                
                # Kilomètres par véhicule
                if tournee.vehicule:
                    vehicule = f"{tournee.vehicule.marque_modele} ({tournee.immatriculation_vehicule})"
                    km_par_vehicule[vehicule] = km_par_vehicule.get(vehicule, 0) + (tournee.km_parcouru or 0)
                
                # Tournées par mois
                if tournee.date_heure_depart:
                    mois = tournee.date_heure_depart.strftime("%Y-%m")
                    tournees_par_mois[mois] = tournees_par_mois.get(mois, 0) + 1
                
                # Durée des tournées
                if tournee.date_heure_depart and tournee.date_heure_arrivee:
                    duree = (tournee.date_heure_arrivee - tournee.date_heure_depart).total_seconds() / 3600
                    durees.append(duree)
            
            # Mise à jour des graphiques
            self.update_km_par_conducteur_chart(km_par_conducteur)
            self.update_km_par_vehicule_chart(km_par_vehicule)
            self.update_tournees_par_mois_chart(tournees_par_mois)
            self.update_duree_moyenne_chart(durees)
            
            # Mise à jour du résumé
            total_tournees = len(tournees)
            total_km = sum(tournee.km_parcouru or 0 for tournee in tournees)
            duree_moyenne = sum(durees) / len(durees) if durees else 0
            self.stats_summary_text.config(text=f"Total tournées: {total_tournees} | Total km: {total_km} | Durée moyenne: {duree_moyenne:.2f} heures")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de mettre à jour les statistiques: {str(e)}")

    def update_km_par_conducteur_chart(self, data):
        """Met à jour le graphique des kilomètres par conducteur"""
        for widget in self.km_par_conducteur_frame.winfo_children():
            widget.destroy()
        
        if not data:
            ttk.Label(self.km_par_conducteur_frame, text="Aucune donnée disponible").pack()
            return
        
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(data.keys(), data.values())
        ax.set_xlabel("Conducteur")
        ax.set_ylabel("Kilomètres")
        ax.set_title("Kilomètres par conducteur")
        ax.tick_params(axis='x', rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, master=self.km_par_conducteur_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_km_par_vehicule_chart(self, data):
        """Met à jour le graphique des kilomètres par véhicule"""
        for widget in self.km_par_vehicule_frame.winfo_children():
            widget.destroy()
        
        if not data:
            ttk.Label(self.km_par_vehicule_frame, text="Aucune donnée disponible").pack()
            return
        
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(data.keys(), data.values())
        ax.set_xlabel("Véhicule")
        ax.set_ylabel("Kilomètres")
        ax.set_title("Kilomètres par véhicule")
        ax.tick_params(axis='x', rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, master=self.km_par_vehicule_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def supprimer(self):
        """Supprime la tournée sélectionnée"""
        try:
            # Récupérer l'élément sélectionné dans le tableau
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("Attention", "Veuillez sélectionner une tournée à supprimer")
                return
            
            # Demander une confirmation avant de supprimer
            if not messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cette tournée ?"):
                return
            
            # Récupérer l'ID de la tournée sélectionnée
            item = self.tree.item(selection[0])
            id_tournee = item['values'][0]
            
            # Supprimer la tournée de la base de données
            tournee = session.query(self.Tournee).get(id_tournee)
            if tournee:
                session.delete(tournee)
                session.commit()
                messagebox.showinfo("Succès", "Tournée supprimée avec succès")
                self.charger_donnees()  # Recharger les données après suppression
            else:
                messagebox.showerror("Erreur", "Tournée non trouvée")
        except Exception as e:
            session.rollback()  # Annuler la transaction en cas d'erreur
            messagebox.showerror("Erreur", f"Impossible de supprimer la tournée : {str(e)}")

    def update_tournees_par_mois_chart(self, data):
        """Met à jour le graphique des tournées par mois"""
        for widget in self.tournees_par_mois_frame.winfo_children():
            widget.destroy()
        
        if not data:
            ttk.Label(self.tournees_par_mois_frame, text="Aucune donnée disponible").pack()
            return
        
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(data.keys(), data.values(), marker='o')
        ax.set_xlabel("Mois")
        ax.set_ylabel("Nombre de tournées")
        ax.set_title("Tournées par mois")
        ax.tick_params(axis='x', rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, master=self.tournees_par_mois_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update_duree_moyenne_chart(self, data):
        """Met à jour le graphique de la durée moyenne des tournées"""
        for widget in self.duree_moyenne_frame.winfo_children():
            widget.destroy()
        
        if not data:
            ttk.Label(self.duree_moyenne_frame, text="Aucune donnée disponible").pack()
            return
        
        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.hist(data, bins=10, edgecolor='black')
        ax.set_xlabel("Durée (heures)")
        ax.set_ylabel("Nombre de tournées")
        ax.set_title("Durée moyenne des tournées")
        
        canvas = FigureCanvasTkAgg(fig, master=self.duree_moyenne_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def charger_donnees(self):
        """Charge les données des tournées dans le tableau"""
        try:
            # Effacer les données existantes dans le tableau
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Récupérer toutes les tournées depuis la base de données
            tournees = session.query(self.Tournee).all()
            
            # Ajouter chaque tournée dans le tableau
            for tournee in tournees:
                # Calculer la durée de la tournée
                duree = ""
                if tournee.date_heure_depart and tournee.date_heure_arrivee:
                    delta = tournee.date_heure_arrivee - tournee.date_heure_depart
                    heures = delta.total_seconds() // 3600
                    minutes = (delta.total_seconds() % 3600) // 60
                    duree = f"{int(heures)}h {int(minutes)}min"
                
                # Formater les dates
                date_depart = tournee.date_heure_depart.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_depart else ""
                date_arrivee = tournee.date_heure_arrivee.strftime("%d/%m/%Y %H:%M") if tournee.date_heure_arrivee else ""
                
                # Ajouter la tournée dans le tableau
                self.tree.insert("", "end", values=(
                    tournee.id_tournee,
                    f"{tournee.conducteur.nom} {tournee.conducteur.prenom}" if tournee.conducteur else "",
                    f"{tournee.vehicule.marque_modele}" if tournee.vehicule else "",
                    f"{tournee.commande.nature_service}" if tournee.commande else "",
                    tournee.objectif,
                    tournee.lieu_depart,
                    tournee.destination,
                    tournee.km_parcouru,
                    date_depart,
                    date_arrivee,
                    duree
                ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données : {str(e)}")

    def exporter_statistiques(self):
        """Exporte les statistiques vers un fichier CSV"""
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        
        try:
            # Récupérer les données des graphiques
            data = {
                "Kilomètres par conducteur": self.km_par_conducteur_frame.winfo_children()[0].get_data(),
                "Kilomètres par véhicule": self.km_par_vehicule_frame.winfo_children()[0].get_data(),
                "Tournées par mois": self.tournees_par_mois_frame.winfo_children()[0].get_data(),
                "Durée moyenne des tournées": self.duree_moyenne_frame.winfo_children()[0].get_data(),
            }
            
            # Créer un DataFrame et exporter
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8')
            messagebox.showinfo("Succès", "Statistiques exportées avec succès")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exporter les statistiques: {str(e)}")

    def enregistrer(self):
        """Enregistre les données du formulaire dans la base de données"""
        try:
            # Récupérer les valeurs du formulaire
            id_tournee = self.id_tournee_var.get()
            id_conducteur = self.id_conducteur_var.get().split(" - ")[0] if self.id_conducteur_var.get() else None
            immatriculation = self.immatriculation_var.get().split(" - ")[0] if self.immatriculation_var.get() else None
            id_commande = self.id_commande_var.get().split(" - ")[0] if self.id_commande_var.get() else None
            objectif = self.objectif_var.get()
            lieu_depart = self.lieu_depart_var.get()
            destination = self.destination_var.get()
            itineraire = self.itineraire_var.get()
            km_parcouru = float(self.km_parcouru_var.get()) if self.km_parcouru_var.get() else None

            # Récupérer les dates et heures
            date_heure_depart = self.get_datetime(
                self.jour_depart_var, self.mois_depart_var, self.annee_depart_var,
                self.heure_depart, self.minute_depart
            )
            date_heure_arrivee = self.get_datetime(
                self.jour_arrivee_var, self.mois_arrivee_var, self.annee_arrivee_var,
                self.heure_arrivee, self.minute_arrivee
            )
            date_heure_reception = self.get_datetime(
                self.jour_reception_var, self.mois_reception_var, self.annee_reception_var,
                self.heure_reception, self.minute_reception
            )
            date_heure_retour = self.get_datetime(
                self.jour_retour_var, self.mois_retour_var, self.annee_retour_var,
                self.heure_retour, self.minute_retour
            )

            # Vérifier si c'est une nouvelle tournée ou une mise à jour
            if id_tournee:
                # Mettre à jour une tournée existante
                tournee = session.query(self.Tournee).get(id_tournee)
                if not tournee:
                    messagebox.showerror("Erreur", "Tournée non trouvée")
                    return
            else:
                # Créer une nouvelle tournée
                tournee = self.Tournee()

            # Mettre à jour les attributs de la tournée
            tournee.id_conducteur = id_conducteur
            tournee.immatriculation_vehicule = immatriculation
            tournee.id_commande = id_commande
            tournee.objectif = objectif
            tournee.lieu_depart = lieu_depart
            tournee.destination = destination
            tournee.itineraire = itineraire
            tournee.km_parcouru = km_parcouru
            tournee.date_heure_depart = date_heure_depart
            tournee.date_heure_arrivee = date_heure_arrivee
            tournee.date_heure_reception = date_heure_reception
            tournee.date_heure_retour = date_heure_retour

            # Ajouter ou mettre à jour la tournée dans la session
            if not id_tournee:
                session.add(tournee)
            
            # Commit des changements
            session.commit()

            # Afficher un message de succès
            messagebox.showinfo("Succès", "Tournée enregistrée avec succès")

            # Recharger les données dans le tableau
            self.charger_donnees()

            # Revenir à l'onglet de liste
            self.notebook.select(0)

        except Exception as e:
            session.rollback()  # Annuler la transaction en cas d'erreur
            messagebox.showerror("Erreur", f"Impossible d'enregistrer la tournée : {str(e)}")

    def get_datetime(self, jour_var, mois_var, annee_var, heure_var, minute_var):
        """Convertit les variables de date et heure en objet datetime"""
        try:
            jour = int(jour_var.get())
            mois = int(mois_var.get())
            annee = int(annee_var.get())
            heure = int(heure_var.get())
            minute = int(minute_var.get())
            
            return datetime(annee, mois, jour, heure, minute)
        except (ValueError, TypeError):
            return None

    def vider_formulaire(self):
        """Réinitialise les champs du formulaire"""
        self.id_tournee_var.set("")
        self.id_conducteur_var.set("")
        self.immatriculation_var.set("")
        self.id_commande_var.set("")
        self.objectif_var.set("")
        self.lieu_depart_var.set("")
        self.destination_var.set("")
        self.itineraire_var.set("")
        self.km_parcouru_var.set("")
        
        today = datetime.now()
        for var in [self.jour_depart_var, self.jour_reception_var, self.jour_retour_var, self.jour_arrivee_var]:
            var.set(str(today.day))
        for var in [self.mois_depart_var, self.mois_reception_var, self.mois_retour_var, self.mois_arrivee_var]:
            var.set(str(today.month))
        for var in [self.annee_depart_var, self.annee_reception_var, self.annee_retour_var, self.annee_arrivee_var]:
            var.set(str(today.year))
        
        for var in [self.heure_depart, self.heure_arrivee, self.heure_reception, self.heure_retour]:
            var.set("0")
        for var in [self.minute_depart, self.minute_arrivee, self.minute_reception, self.minute_retour]:
            var.set("0")

if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = TourneeApp(root)
    root.mainloop()