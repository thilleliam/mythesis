import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime, timedelta
from sqlalchemy import outerjoin, exists
import tkinter as tk

# Imports pour matplotlib
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.style as style
    from collections import Counter
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib non disponible. Installez-le avec: pip install matplotlib")

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class CommandeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Commandes")
        self.root.geometry("1600x900")  # Plus large pour les graphiques
        photo = ttk.PhotoImage(file="C:\\Users\\BIG-computer\\Pictures\\Logo1.png")
        root.iconphoto(False, photo)
        
        # Appliquer le thème
        style = ttk.Style("cosmo")
        
        # Import local pour éviter les imports circulaires
        from application.models.commande import Commande
        from application.models.chantiers import Chantier
        from application.models.tournee import Tournee
        
        self.Commande = Commande
        self.Chantier = Chantier
        self.Tournee = Tournee
        
        # Variables
        self.id_commande_var = StringVar()
        self.id_client_var = StringVar()
        self.id_tournee_var = StringVar()
        self.nature_service_var = StringVar()
        self.type_vehicule_var = StringVar()
        self.quantite_requise_var = StringVar()
        self.lieu_chargement_var = StringVar()
        self.date_commande_var = StringVar()
        self.date_livraison_var = StringVar()
        self.statut_var = StringVar()
        
        # Configuration du style matplotlib
        if MATPLOTLIB_AVAILABLE:
            plt.style.use('seaborn-v0_8-whitegrid')  # Style moderne
        
        # Configuration du style tkinter
        style.configure('Treeview', rowheight=30)
        style.configure('TButton', font=("Segoe UI", 10))
        style.configure('TLabel', font=("Segoe UI", 10))
        style.configure('TEntry', font=("Segoe UI", 10))
        
        # Frame principal avec des onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # Onglet principal de gestion
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Gestion des commandes")
        
        # Onglet tableau de bord
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Tableau de bord")
        
        # Setup des onglets
        self.setup_main_tab(main_frame)
        self.setup_dashboard_tab(dashboard_frame)
        
        # Barre d'état
        self.status_var = StringVar()
        self.status_var.set("Prêt")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side=BOTTOM, fill=X)

        # Chargement initial des données
        self.charger_donnees()
        self.update_dashboard()
    
    def setup_main_tab(self, parent):
        """Configure l'onglet principal de gestion"""
        # Boutons d'actions
        btn_frame = ttk.Frame(parent, padding=10)
        btn_frame.pack(fill=X, pady=10)

        ttk.Button(btn_frame, text="Supprimer", command=self.supprimer, bootstyle=DANGER, width=15).pack(side=LEFT, padx=8)
        ttk.Button(btn_frame, text="Actualiser", command=self.charger_donnees, bootstyle=SECONDARY, width=15).pack(side=LEFT, padx=8)
        
        # Frame d'outils à droite
        tools_frame = ttk.Frame(btn_frame)
        tools_frame.pack(side=RIGHT)
        
        ttk.Button(tools_frame, text="Vérifier Retard", command=self.verifier_retard, 
                  bootstyle=INFO, width=18).pack(side=LEFT, padx=8)
        ttk.Button(tools_frame, text="Associer Tournée", command=self.associer_tournee, 
                  bootstyle=INFO, width=18).pack(side=LEFT, padx=8)
        ttk.Button(tools_frame, text="Recherche", command=self.recherche_avancee, 
                  bootstyle=PRIMARY, width=18).pack(side=LEFT, padx=8)

        # Tableau des commandes
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=BOTH, expand=True, pady=10)
        
        # Barre de défilement pour le tableau
        scrollbar_y = ttk.Scrollbar(tree_frame)
        scrollbar_y.pack(side=RIGHT, fill=Y)
        
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=HORIZONTAL)
        scrollbar_x.pack(side=BOTTOM, fill=X)
        
        # Configuration du tableau
        self.tree = ttk.Treeview(tree_frame, columns=(
            "id_commande", "id_client", "nom_equipement", "tournee", "nature_service", 
            "type_vehicule", "quantite_requise", "lieu_chargement", 
            "date_commande", "date_livraison", "statut"), show="headings", 
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Configuration des barres de défilement
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Configuration des colonnes
        self.tree.heading("id_commande", text="ID")
        self.tree.heading("id_client", text="Client")
        self.tree.heading("nom_equipement", text="Nom Equipement")
        self.tree.heading("tournee", text="Tournée")
        self.tree.heading("nature_service", text="Service")
        self.tree.heading("type_vehicule", text="Véhicule")
        self.tree.heading("quantite_requise", text="Quantité")
        self.tree.heading("lieu_chargement", text="Lieu")
        self.tree.heading("date_commande", text="Date Commande")
        self.tree.heading("date_livraison", text="Date Livraison")
        self.tree.heading("statut", text="Statut")

        # Configurer les largeurs des colonnes
        self.tree.column("id_commande", width=50)
        self.tree.column("id_client", width=50)
        self.tree.column("nom_equipement", width=120)
        self.tree.column("tournee", width=60)
        self.tree.column("nature_service", width=120)
        self.tree.column("type_vehicule", width=100)
        self.tree.column("quantite_requise", width=80)
        self.tree.column("lieu_chargement", width=120)
        self.tree.column("date_commande", width=150)
        self.tree.column("date_livraison", width=150)
        self.tree.column("statut", width=80)
        
        # Pack le tableau
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Bind le double-click pour sélectionner
        self.tree.bind("<Double-1>", self.selectionner)
        self.tree.bind("<ButtonRelease-1>", self.selectionner)
        
        # Menu contextuel (clic droit)
        self.context_menu = ttk.Menu(self.root)
        self.context_menu.add_command(label="Détails du client", command=self.afficher_details_client)
        self.context_menu.add_command(label="Calculer délai de livraison", command=self.calculer_delai_livraison)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Marquer comme livrée", command=self.marquer_livree)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
    
    def setup_dashboard_tab(self, parent):
        # Frame principal pour le dashboard avec scrollbars
        outer_frame = ttk.Frame(parent)
        outer_frame.pack(fill=BOTH, expand=True)

        # Création du canvas
        dashboard_canvas = tk.Canvas(outer_frame)
        dashboard_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(outer_frame, orient=VERTICAL, command=dashboard_canvas.yview)
        scrollbar_y.pack(side=RIGHT, fill=Y)
        scrollbar_x = ttk.Scrollbar(outer_frame, orient=HORIZONTAL, command=dashboard_canvas.xview)
        scrollbar_x.pack(side=BOTTOM, fill=X)

        dashboard_canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Frame interne qui contiendra tout le dashboard
        dashboard_main = ttk.Frame(dashboard_canvas)
        dashboard_canvas.create_window((0, 0), window=dashboard_main, anchor="nw")

        def on_configure(event):
            dashboard_canvas.configure(scrollregion=dashboard_canvas.bbox("all"))

        dashboard_main.bind("<Configure>", on_configure)

        # Frame pour les statistiques en haut
        stats_frame = ttk.LabelFrame(dashboard_main, text="Statistiques globales", padding=10)
        stats_frame.pack(fill=X, pady=(0, 10))
        
        # Variables pour les statistiques
        self.total_commandes_var = StringVar(value="0")
        self.commandes_retard_var = StringVar(value="0")
        self.commandes_sans_tournee_var = StringVar(value="0")
        self.commandes_livrees_var = StringVar(value="0")
        
        # Création des cartes de statistiques
        stats_inner_frame = ttk.Frame(stats_frame)
        stats_inner_frame.pack(fill=X)
        
        # Configuration en grille pour les stats
        for i in range(4):
            stats_inner_frame.columnconfigure(i, weight=1)
        
        # Cartes de statistiques avec style amélioré
        self.create_stat_card(stats_inner_frame, "Total Commandes", self.total_commandes_var, "blue", 0)
        self.create_stat_card(stats_inner_frame, "En Retard", self.commandes_retard_var, "red", 1)
        self.create_stat_card(stats_inner_frame, "Sans Tournée", self.commandes_sans_tournee_var, "orange", 2)
        self.create_stat_card(stats_inner_frame, "Livrées", self.commandes_livrees_var, "green", 3)
        
        # Bouton actualiser
        ttk.Button(stats_frame, text="🔄 Actualiser Dashboard", command=self.update_dashboard, 
                  bootstyle=PRIMARY, width=25).pack(pady=10)
        
        # Frame pour les graphiques matplotlib
        if MATPLOTLIB_AVAILABLE:
            self.setup_matplotlib_charts(dashboard_main)
        else:
            # Fallback si matplotlib n'est pas disponible
            error_frame = ttk.LabelFrame(dashboard_main, text="Graphiques non disponibles", padding=20)
            error_frame.pack(fill=BOTH, expand=True)
            ttk.Label(error_frame, text="Matplotlib n'est pas installé.\nInstallez-le avec: pip install matplotlib", 
                     font=("Segoe UI", 12), foreground="red").pack(pady=50)
        
        # Ajout d'un tableau Treeview avec scrollbars pour les commandes (aperçu)
        table_frame = ttk.LabelFrame(dashboard_main, text="Aperçu des commandes", padding=10)
        table_frame.pack(fill=BOTH, expand=True, pady=10)
        
        # Scrollbars pour le tableau (déjà présentes)
        self.dashboard_scrollbar_y = ttk.Scrollbar(table_frame)
        self.dashboard_scrollbar_y.pack(side=RIGHT, fill=Y)
        self.dashboard_scrollbar_x = ttk.Scrollbar(table_frame, orient=HORIZONTAL)
        self.dashboard_scrollbar_x.pack(side=BOTTOM, fill=X)
        
        # Treeview
        self.dashboard_tree = ttk.Treeview(
            table_frame,
            columns=("id_commande", "id_client", "statut", "date_commande", "date_livraison"),
            show="headings",
            yscrollcommand=self.dashboard_scrollbar_y.set,
            xscrollcommand=self.dashboard_scrollbar_x.set
        )
        self.dashboard_tree.heading("id_commande", text="ID")
        self.dashboard_tree.heading("id_client", text="Client")
        self.dashboard_tree.heading("statut", text="Statut")
        self.dashboard_tree.heading("date_commande", text="Date Commande")
        self.dashboard_tree.heading("date_livraison", text="Date Livraison")
        for col in ("id_commande", "id_client", "statut", "date_commande", "date_livraison"):
            self.dashboard_tree.column(col, width=120)
        self.dashboard_tree.pack(side=LEFT, fill=BOTH, expand=True)
        self.dashboard_scrollbar_y.config(command=self.dashboard_tree.yview)
        self.dashboard_scrollbar_x.config(command=self.dashboard_tree.xview)
    
    def create_stat_card(self, parent, title, var, color, column):
        """Crée une carte de statistique stylée"""
        card = ttk.Frame(parent, relief=RAISED, borderwidth=2)
        card.grid(row=0, column=column, padx=5, pady=5, sticky="ew")
        
        # Titre
        ttk.Label(card, text=title, font=("Segoe UI", 10, "bold")).pack(pady=(10, 5))
        
        # Valeur avec couleur
        value_label = ttk.Label(card, textvariable=var, font=("Segoe UI", 20, "bold"))
        value_label.pack(pady=(0, 10))
        
        # Appliquer la couleur (limité avec ttkbootstrap, mais on essaie)
        try:
            if color == "blue":
                value_label.configure(foreground="#007bff")
            elif color == "red":
                value_label.configure(foreground="#dc3545")
            elif color == "orange":
                value_label.configure(foreground="#fd7e14")
            elif color == "green":
                value_label.configure(foreground="#28a745")
        except:
            pass  # Si la couleur ne fonctionne pas, on continue
    
    def setup_matplotlib_charts(self, parent):
        """Configure les graphiques matplotlib"""
        # Frame pour contenir tous les graphiques
        charts_main_frame = ttk.Frame(parent)
        charts_main_frame.pack(fill=BOTH, expand=True)
        
        # Configuration en grille
        charts_main_frame.columnconfigure(0, weight=1)
        charts_main_frame.columnconfigure(1, weight=1)
        charts_main_frame.rowconfigure(0, weight=1)
        charts_main_frame.rowconfigure(1, weight=1)
        
        # Frame pour graphique véhicules (camembert)
        self.vehicle_frame = ttk.LabelFrame(charts_main_frame, text="📊 Répartition par Type de Véhicule", padding=5)
        self.vehicle_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # Frame pour graphique statuts (barres)
        self.status_frame = ttk.LabelFrame(charts_main_frame, text="📈 Répartition par Statut", padding=5)
        self.status_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Frame pour graphique clients (barres horizontales)
        self.client_frame = ttk.LabelFrame(charts_main_frame, text="👥 Top 10 Clients", padding=5)
        self.client_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # Initialiser les figures matplotlib
        self.vehicle_fig = Figure(figsize=(6, 4), dpi=80, facecolor='white')
        self.status_fig = Figure(figsize=(6, 4), dpi=80, facecolor='white')
        self.client_fig = Figure(figsize=(12, 4), dpi=80, facecolor='white')
        
        # Créer les canvas
        self.vehicle_canvas = FigureCanvasTkAgg(self.vehicle_fig, self.vehicle_frame)
        self.vehicle_canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        
        self.status_canvas = FigureCanvasTkAgg(self.status_fig, self.status_frame)
        self.status_canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        
        self.client_canvas = FigureCanvasTkAgg(self.client_fig, self.client_frame)
        self.client_canvas.get_tk_widget().pack(fill=BOTH, expand=True)
    
    def create_vehicle_pie_chart(self, data):
        """Crée un graphique en camembert pour les types de véhicules"""
        if not MATPLOTLIB_AVAILABLE or not data:
            return
        
        self.vehicle_fig.clear()
        ax = self.vehicle_fig.add_subplot(111)
        
        # Couleurs modernes
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        # Données
        labels = list(data.keys())
        sizes = list(data.values())
        
        # Créer le camembert
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', 
                                         startangle=90, colors=colors[:len(labels)],
                                         textprops={'fontsize': 9})
        
        # Améliorer l'apparence
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Répartition par Type de Véhicule', fontsize=12, fontweight='bold', pad=20)
        
        # Rafraîchir le canvas
        self.vehicle_canvas.draw()
    
    def create_status_bar_chart(self, data):
        """Crée un graphique en barres pour les statuts"""
        if not MATPLOTLIB_AVAILABLE or not data:
            return
        
        self.status_fig.clear()
        ax = self.status_fig.add_subplot(111)
        
        # Couleurs selon le statut
        color_map = {
            'En attente': '#FFA500',
            'En cours': '#4169E1', 
            'Livré': '#32CD32',
            'Annulé': '#DC143C'
        }
        
        # Données
        statuts = list(data.keys())
        counts = list(data.values())
        colors = [color_map.get(statut, '#708090') for statut in statuts]
        
        # Créer le graphique en barres
        bars = ax.bar(statuts, counts, color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)
        
        # Ajouter les valeurs sur les barres
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{count}', ha='center', va='bottom', fontweight='bold')
        
        # Améliorer l'apparence
        ax.set_title('Répartition par Statut', fontsize=12, fontweight='bold', pad=20)
        ax.set_ylabel('Nombre de commandes', fontsize=10)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', alpha=0.3)
        
        # Ajuster la mise en page
        self.status_fig.tight_layout()
        
        # Rafraîchir le canvas
        self.status_canvas.draw()
    
    def create_client_bar_chart(self, data, max_items=10):
        """Crée un graphique en barres horizontales pour les clients"""
        if not MATPLOTLIB_AVAILABLE or not data:
            return
        
        self.client_fig.clear()
        ax = self.client_fig.add_subplot(111)
        
        # Prendre les top clients
        sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:max_items]
        
        if not sorted_data:
            return
        
        # Données
        clients = [item[0] for item in sorted_data]
        counts = [item[1] for item in sorted_data]
        
        # Créer un dégradé de couleurs
        colors = plt.cm.Set3(np.linspace(0, 1, len(clients)))
        
        # Créer le graphique en barres horizontales
        bars = ax.barh(clients, counts, color=colors, alpha=0.8, edgecolor='white', linewidth=1)
        
        # Ajouter les valeurs à côté des barres
        for bar, count in zip(bars, counts):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                   f'{count}', ha='left', va='center', fontweight='bold')
        
        # Améliorer l'apparence
        ax.set_title(f'Top {len(clients)} Clients par Nombre de Commandes', 
                    fontsize=12, fontweight='bold', pad=20)
        ax.set_xlabel('Nombre de commandes', fontsize=10)
        ax.grid(axis='x', alpha=0.3)
        
        # Inverser l'ordre pour avoir le plus grand en haut
        ax.invert_yaxis()
        
        # Ajuster la mise en page
        self.client_fig.tight_layout()
        
        # Rafraîchir le canvas
        self.client_canvas.draw()
    
    def update_dashboard(self):
        """Met à jour le tableau de bord avec les dernières données"""
        try:
            # Mise à jour des statistiques
            self.rafraichir_statistiques()
            
            # Mise à jour du tableau dashboard_tree
            if hasattr(self, 'dashboard_tree'):
                self.dashboard_tree.delete(*self.dashboard_tree.get_children())
                commandes = session.query(self.Commande).all()
                for commande in commandes:
                    statut = commande.statut if getattr(commande, 'statut', None) else "En attente"
                    self.dashboard_tree.insert("", END, values=(
                        commande.id_commande,
                        commande.id_client,
                        statut,
                        commande.date_commande,
                        commande.date_livraison
                    ))
            
            if not MATPLOTLIB_AVAILABLE:
                return
            
            # Récupérer les données pour les graphiques
            commandes = session.query(self.Commande).all()
            
            if not commandes:
                # Afficher des graphiques vides
                self.create_empty_charts()
                return
            
            # Préparer les données
            types_vehicules = [cmd.type_vehicule for cmd in commandes if cmd.type_vehicule]
            vehicle_data = Counter(types_vehicules)
            
            statuts = [cmd.statut if getattr(cmd, 'statut', None) else 'En attente' for cmd in commandes]
            status_data = Counter(statuts)
            
            clients = [cmd.id_client for cmd in commandes if cmd.id_client]
            client_data = Counter(clients)
            
            # Créer les graphiques
            self.create_vehicle_pie_chart(vehicle_data)
            self.create_status_bar_chart(status_data)
            self.create_client_bar_chart(client_data)
            
            self.status_var.set(f"Dashboard mis à jour - {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour du dashboard: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def create_empty_charts(self):
        """Crée des graphiques vides quand il n'y a pas de données"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Graphique véhicules vide
        self.vehicle_fig.clear()
        ax1 = self.vehicle_fig.add_subplot(111)
        ax1.text(0.5, 0.5, 'Aucune donnée\ndisponible', 
                ha='center', va='center', transform=ax1.transAxes,
                fontsize=14, color='gray')
        ax1.set_title('Répartition par Type de Véhicule', fontsize=12, fontweight='bold')
        self.vehicle_canvas.draw()
        
        # Graphique statuts vide
        self.status_fig.clear()
        ax2 = self.status_fig.add_subplot(111)
        ax2.text(0.5, 0.5, 'Aucune donnée\ndisponible', 
                ha='center', va='center', transform=ax2.transAxes,
                fontsize=14, color='gray')
        ax2.set_title('Répartition par Statut', fontsize=12, fontweight='bold')
        self.status_canvas.draw()
        
        # Graphique clients vide
        self.client_fig.clear()
        ax3 = self.client_fig.add_subplot(111)
        ax3.text(0.5, 0.5, 'Aucune donnée disponible', 
                ha='center', va='center', transform=ax3.transAxes,
                fontsize=14, color='gray')
        ax3.set_title('Top 10 Clients', fontsize=12, fontweight='bold')
        self.client_canvas.draw()
    
    def rafraichir_statistiques(self):
        """Met à jour les statistiques des commandes"""
        try:
            # Nombre total de commandes
            total = session.query(func.count(self.Commande.id_commande)).scalar()
            self.total_commandes_var.set(str(total))
            
            # Commandes en retard
            date_actuelle = datetime.now()
            retard = session.query(func.count(self.Commande.id_commande)).filter(
                self.Commande.date_livraison < date_actuelle).scalar()
            self.commandes_retard_var.set(str(retard))
        
            # Commandes sans tournée
            sans_tournee = session.query(func.count(self.Commande.id_commande)).filter(
                ~exists().where(self.Tournee.id_commande == self.Commande.id_commande)
            ).scalar()
            self.commandes_sans_tournee_var.set(str(sans_tournee))
            
            # Commandes livrées
            livrees = session.query(func.count(self.Commande.id_commande)).filter(
                self.Commande.statut == 'Livré').scalar() if hasattr(self.Commande, 'statut') else 0
            self.commandes_livrees_var.set(str(livrees))
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour des statistiques: {str(e)}")
            import traceback
            traceback.print_exc()

    # [Le reste des méthodes reste identique - supprimer, selectionner, charger_donnees, etc.]
    def show_context_menu(self, event):
        """Affiche le menu contextuel sur clic droit"""
        if self.tree.selection():
            self.context_menu.post(event.x_root, event.y_root)

    def supprimer(self):
        """Supprime une commande existante"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande à supprimer")
            return
        
        if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cette commande?"):
            try:
                id_commande = int(self.tree.item(item, "values")[0])
                commande = session.query(self.Commande).filter_by(id_commande=id_commande).first()
                if commande:
                    session.delete(commande)
                    session.commit()
                
                # Mise à jour de l'interface et du dashboard
                self.charger_donnees()
                self.update_dashboard()
                self.status_var.set(f"Commande n°{id_commande} supprimée - {datetime.now().strftime('%H:%M:%S')}")
                messagebox.showinfo("Succès", "Commande supprimée avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")

    def selectionner(self, event=None):
        """Remplit les variables avec les données de la commande sélectionnée"""
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            self.id_commande_var.set(values[0])
            self.id_client_var.set(values[1])
            
            # Gestion du numéro de tournée
            tournee_id = values[3]
            if tournee_id and tournee_id != "Non assignée":
                self.id_tournee_var.set(tournee_id)
            else:
                self.id_tournee_var.set("")
                
            self.nature_service_var.set(values[4])
            self.type_vehicule_var.set(values[5])
            self.quantite_requise_var.set(values[6])
            self.lieu_chargement_var.set(values[7])
            self.date_commande_var.set(values[8])
            self.date_livraison_var.set(values[9])
            
            # Gestion du statut si présent
            if len(values) > 10:
                self.statut_var.set(values[10])
            else:
                self.statut_var.set("")

    def charger_donnees(self):
        """Charge les commandes depuis la base de données et les affiche dans le tableau"""
        self.tree.delete(*self.tree.get_children())
        try:
            commandes = session.query(self.Commande).all()
            for commande in commandes:
                # Récupérer l'ID de la tournée associée à travers la relation, s'il y en a une
                id_tournee = None
                if hasattr(commande, 'tournee') and commande.tournee:
                    id_tournee = commande.tournee.id_tournee
                
                # Récupérer le statut s'il existe, sinon afficher 'En attente'
                statut = commande.statut if getattr(commande, 'statut', None) else "En attente"
                
                # Récupérer le nom d'équipement
                nom_equipement = commande.equipement.nomEquipement if commande.equipement else "-"
                
                self.tree.insert("", END, values=(
                    commande.id_commande, 
                    commande.id_client, 
                    nom_equipement,
                    id_tournee if id_tournee else "Non assignée",
                    commande.nature_service, 
                    commande.type_vehicule, 
                    commande.quantite_requise,
                    commande.lieu_chargement, 
                    commande.date_commande, 
                    commande.date_livraison,
                    statut
                ))
            
            self.status_var.set(f"Données chargées - {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données: {str(e)}")
            import traceback
            traceback.print_exc()

    def verifier_retard(self):
        """Vérifie si une commande est en retard"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande pour vérifier son état")
            return
        
        try:
            id_commande = int(self.tree.item(item, "values")[0])
            commande = session.query(self.Commande).filter_by(id_commande=id_commande).first()
            
            if commande:
                date_actuelle = datetime.now()
                est_en_retard = commande.est_en_retard(date_actuelle)
                
                if est_en_retard:
                    messagebox.showwarning("Retard", f"La commande n°{id_commande} est en retard!")
                else:
                    messagebox.showinfo("À temps", f"La commande n°{id_commande} n'est pas en retard.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la vérification: {str(e)}")

    def associer_tournee(self):
        """Associe une tournée à une commande"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande pour l'associer à une tournée")
            return
            
        try:
            id_commande = int(self.tree.item(item, "values")[0])
            commande = session.query(self.Commande).filter_by(id_commande=id_commande).first()
            
            if commande:
                id_tournee = simpledialog.askinteger("Associer Tournée", "Entrez l'ID de la tournée à associer:")
                if id_tournee is not None:
                    # Vérifier si la tournée existe
                    tournee = session.query(self.Tournee).filter_by(id_tournee=id_tournee).first()
                    if tournee:
                        commande.associer_tournee(id_tournee)
                        session.commit()
                        self.charger_donnees()
                        self.update_dashboard()
                        self.status_var.set(f"Commande n°{id_commande} associée à tournée n°{id_tournee}")
                        messagebox.showinfo("Succès", f"Commande n°{id_commande} associée à la tournée n°{id_tournee}")
                    else:
                        messagebox.showerror("Erreur", f"La tournée n°{id_tournee} n'existe pas.")
            else:
                messagebox.showerror("Erreur", "Commande introuvable.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'association: {str(e)}")
            import traceback
            traceback.print_exc()

    def recherche_avancee(self):
        """Ouvre une fenêtre de recherche avancée"""
        recherche_window = ttk.Toplevel(self.root)
        recherche_window.title("Recherche avancée")
        recherche_window.geometry("600x400")
        
        # Frame principal
        main_frame = ttk.Frame(recherche_window, padding=15)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Critères de recherche
        criteria_frame = ttk.LabelFrame(main_frame, text="Critères de recherche", padding=10)
        criteria_frame.pack(fill=X, pady=10)
        
        # Variables de recherche
        client_search_var = StringVar()
        vehicle_search_var = StringVar()
        date_from_var = StringVar()
        date_to_var = StringVar()
        
        # Configuration des critères
        ttk.Label(criteria_frame, text="ID Client:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(criteria_frame, textvariable=client_search_var).grid(row=0, column=1, padx=5, pady=5, sticky=W+E)
        
        ttk.Label(criteria_frame, text="Type véhicule:").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        vehicle_types = ["", "Camion", "Semi-remorque", "Fourgon", "Benne", "Citerne"]
        ttk.Combobox(criteria_frame, textvariable=vehicle_search_var, values=vehicle_types).grid(row=0, column=3, padx=5, pady=5, sticky=W+E)
        
        ttk.Label(criteria_frame, text="Date livraison de:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(criteria_frame, textvariable=date_from_var).grid(row=1, column=1, padx=5, pady=5, sticky=W+E)
        
        ttk.Label(criteria_frame, text="à:").grid(row=1, column=2, padx=5, pady=5, sticky=W)
        ttk.Entry(criteria_frame, textvariable=date_to_var).grid(row=1, column=3, padx=5, pady=5, sticky=W+E)
        
        # Fonctions de recherche
        def executer_recherche():
            try:
                query = session.query(self.Commande)
                
                if client_search_var.get():
                    query = query.filter(self.Commande.id_client == client_search_var.get())
                    
                if vehicle_search_var.get():
                    query = query.filter(self.Commande.type_vehicule == vehicle_search_var.get())
                    
                if date_from_var.get():
                    try:
                        date_from = datetime.strptime(date_from_var.get(), "%Y-%m-%d")
                        query = query.filter(self.Commande.date_livraison >= date_from)
                    except ValueError:
                        messagebox.showwarning("Format de date incorrect", "Utilisez le format YYYY-MM-DD")
                        return
                
                if date_to_var.get():
                    try:
                        date_to = datetime.strptime(date_to_var.get(), "%Y-%m-%d")
                        query = query.filter(self.Commande.date_livraison <= date_to)
                    except ValueError:
                        messagebox.showwarning("Format de date incorrect", "Utilisez le format YYYY-MM-DD")
                        return
                
                resultats = query.all()
                
                for item in result_tree.get_children():
                    result_tree.delete(item)
                    
                for commande in resultats:
                    id_tournee = None
                    if commande.tournee:
                        id_tournee = commande.tournee.id_tournee
                    
                    result_tree.insert("", END, values=(
                        commande.id_commande, 
                        commande.id_client, 
                        id_tournee if id_tournee else "None",
                        commande.nature_service, 
                        commande.type_vehicule, 
                        commande.quantite_requise,
                        commande.lieu_chargement, 
                        commande.date_commande, 
                        commande.date_livraison
                    ))
                    
                status_var.set(f"Recherche terminée - {len(resultats)} résultat(s)")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la recherche: {str(e)}")
        
        def exporter_resultats():
            if not result_tree.get_children():
                messagebox.showinfo("Information", "Aucun résultat à exporter.")
                return
                
            try:
                import csv
                from tkinter import filedialog
                
                fichier = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Enregistrer les résultats"
                )
                
                if not fichier:
                    return
                
                with open(fichier, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    
                    headers = ["ID", "Client", "Tournée", "Service", "Véhicule", 
                            "Quantité", "Lieu", "Date Commande", "Date Livraison"]
                    writer.writerow(headers)
                    
                    for item_id in result_tree.get_children():
                        values = result_tree.item(item_id, "values")
                        writer.writerow(values)
                
                messagebox.showinfo("Succès", f"Les résultats ont été exportés vers {fichier}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'exportation: {str(e)}")
        
        # Boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=10)
        
        ttk.Button(btn_frame, text="Rechercher", command=executer_recherche, 
                bootstyle=PRIMARY, width=15).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter CSV", command=exporter_resultats, 
                bootstyle=SUCCESS, width=15).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Fermer", command=recherche_window.destroy, 
                bootstyle=SECONDARY, width=15).pack(side=RIGHT, padx=5)
        
        # Tableau des résultats
        result_frame = ttk.LabelFrame(main_frame, text="Résultats", padding=10)
        result_frame.pack(fill=BOTH, expand=True, pady=10)
        
        y_scrollbar = ttk.Scrollbar(result_frame)
        y_scrollbar.pack(side=RIGHT, fill=Y)
        
        x_scrollbar = ttk.Scrollbar(result_frame, orient=HORIZONTAL)
        x_scrollbar.pack(side=BOTTOM, fill=X)
        
        result_tree = ttk.Treeview(result_frame, columns=(
            "id_commande", "id_client", "id_tournee", "nature_service", 
            "type_vehicule", "quantite_requise", "lieu_chargement", 
            "date_commande", "date_livraison"), show="headings",
            yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        y_scrollbar.config(command=result_tree.yview)
        x_scrollbar.config(command=result_tree.xview)
        
        # Configuration des colonnes du tableau de résultats
        for col in result_tree["columns"]:
            result_tree.heading(col, text=col.replace("_", " ").title())
            result_tree.column(col, width=100)
        
        result_tree.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Barre d'état
        status_var = StringVar()
        status_var.set("Prêt pour la recherche")
        status_bar = ttk.Label(recherche_window, textvariable=status_var, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)

    def afficher_details_client(self):
        """Affiche les détails du client associé à la commande sélectionnée"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande pour voir les détails du client")
            return
        
        try:
            id_client = self.tree.item(item, "values")[1]
            client = session.query(self.Chantier).filter_by(id_client=id_client).first()
            
            if client:
                details_window = ttk.Toplevel(self.root)
                details_window.title(f"Détails du Client {id_client}")
                details_window.geometry("500x300")
                
                details_frame = ttk.Frame(details_window, padding=15)
                details_frame.pack(fill=BOTH, expand=True)
                
                ttk.Label(details_frame, text=f"ID: {client.id_client}", font=("Segoe UI", 12, "bold")).pack(anchor=W, pady=5)
                ttk.Label(details_frame, text=f"Localisation: {getattr(client, 'localisation', 'Non spécifiée')}").pack(anchor=W, pady=2)
                ttk.Label(details_frame, text=f"Nature terrain: {getattr(client, 'nature_terrain', 'Non spécifiée')}").pack(anchor=W, pady=2)
                ttk.Label(details_frame, text=f"Distance goudron: {getattr(client, 'distanceAllerGoudron', 'Non spécifiée')} km").pack(anchor=W, pady=2)
                ttk.Label(details_frame, text=f"Distance piste: {getattr(client, 'distanceAllerPiste', 'Non spécifiée')} km").pack(anchor=W, pady=2)
                ttk.Label(details_frame, text=f"Temps aller: {getattr(client, 'temps_aller', 'Non calculé')} h").pack(anchor=W, pady=2)
                
                stats_frame = ttk.LabelFrame(details_frame, text="Statistiques", padding=10)
                stats_frame.pack(fill=X, pady=10)
                
                nb_commandes = session.query(func.count(self.Commande.id_commande)).filter(
                    self.Commande.id_client == id_client).scalar()
                ttk.Label(stats_frame, text=f"Nombre de commandes: {nb_commandes}").pack(anchor=W, pady=2)
                
                ttk.Button(details_window, text="Fermer", command=details_window.destroy, 
                        bootstyle=SECONDARY, width=15).pack(pady=10)
            else:
                messagebox.showinfo("Information", f"Aucune information disponible pour le client {id_client}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage des détails: {str(e)}")

    def calculer_delai_livraison(self):
        """Calcule et affiche le délai de livraison estimé pour une commande"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande pour calculer le délai")
            return
        
        try:
            id_commande = int(self.tree.item(item, "values")[0])
            commande = session.query(self.Commande).filter_by(id_commande=id_commande).first()
            
            if commande:
                distance = simpledialog.askfloat("Distance", "Distance à parcourir (km):", minvalue=0.1)
                if distance is None:
                    return
                    
                poids = simpledialog.askfloat("Poids", "Poids de la cargaison (kg):", minvalue=0.1)
                if poids is None:
                    return
                
                delai = commande.calculer_delai_livraison(distance, poids)
                
                heures = int(delai)
                minutes = int((delai - heures) * 60)
                
                messagebox.showinfo("Délai de livraison", 
                                    f"Pour la commande n°{id_commande} :\n\n"
                                    f"Distance : {distance} km\n"
                                    f"Poids : {poids} kg\n\n"
                                    f"Délai estimé : {heures}h {minutes}min")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul: {str(e)}")

    def marquer_livree(self):
        """Marque une commande comme livrée"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande à marquer comme livrée")
            return
        
        try:
            id_commande = int(self.tree.item(item, "values")[0])
            commande = session.query(self.Commande).filter_by(id_commande=id_commande).first()
            
            if commande:
                if hasattr(commande, 'statut') and commande.statut == 'Livré':
                    messagebox.showinfo("Information", f"La commande n°{id_commande} est déjà marquée comme livrée.")
                    return
                
                confirmation = messagebox.askyesno("Confirmation", 
                                                f"Êtes-vous sûr de vouloir marquer la commande n°{id_commande} comme livrée ?")
                if not confirmation:
                    return
                
                commande.statut = 'Livré'
                session.commit()
                messagebox.showinfo("Succès", f"La commande n°{id_commande} a été marquée comme livrée.")
                
                self.charger_donnees()
                self.update_dashboard()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du marquage: {str(e)}")

# Point d'entrée pour l'application
def main():
    root = ttk.Window(themename="cosmo")
    app = CommandeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()