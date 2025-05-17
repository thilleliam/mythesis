import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime, timedelta
from sqlalchemy import outerjoin, exists

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class CommandeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Commandes")
        self.root.geometry("1200x700")
        
        # Appliquer le thème Darkly
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
        
        # Configuration du style
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
        
        # Onglet statistiques
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Statistiques")
        
        # Formulaire dans l'onglet principal
        form_frame = ttk.LabelFrame(main_frame, text="Informations de la commande", padding=15)
        form_frame.pack(fill=X, padx=10, pady=10)

        # Première ligne
        ttk.Label(form_frame, text="ID Commande").grid(row=0, column=0, padx=5, pady=8, sticky=W)
        ttk.Entry(form_frame, textvariable=self.id_commande_var, state=DISABLED, width=12).grid(row=0, column=1, padx=5, pady=8, sticky=W)

        ttk.Label(form_frame, text="ID Client").grid(row=0, column=2, padx=5, pady=8, sticky=W)
        self.client_cb = ttk.Combobox(form_frame, textvariable=self.id_client_var, width=15)
        self.client_cb.grid(row=0, column=3, padx=5, pady=8, sticky=W)

        ttk.Label(form_frame, text="Tournée").grid(row=0, column=4, padx=5, pady=8, sticky=W)
        self.tournee_cb = ttk.Combobox(form_frame, textvariable=self.id_tournee_var, width=15)
        self.tournee_cb.grid(row=0, column=5, padx=5, pady=8, sticky=W)

        # Deuxième ligne
        ttk.Label(form_frame, text="Nature Service").grid(row=1, column=0, padx=5, pady=8, sticky=W)
        ttk.Entry(form_frame, textvariable=self.nature_service_var).grid(row=1, column=1, padx=5, pady=8, sticky=W)

        ttk.Label(form_frame, text="Type Véhicule").grid(row=1, column=2, padx=5, pady=8, sticky=W)
        vehicle_types = ["Camion", "Semi-remorque", "Fourgon", "Benne", "Citerne"]
        self.type_vehicule_cb = ttk.Combobox(form_frame, textvariable=self.type_vehicule_var, values=vehicle_types)
        self.type_vehicule_cb.grid(row=1, column=3, padx=5, pady=8, sticky=W)

        ttk.Label(form_frame, text="Quantité Requise").grid(row=1, column=4, padx=5, pady=8, sticky=W)
        ttk.Entry(form_frame, textvariable=self.quantite_requise_var).grid(row=1, column=5, padx=5, pady=8, sticky=W)

        # Troisième ligne
        ttk.Label(form_frame, text="Lieu Chargement").grid(row=2, column=0, padx=5, pady=8, sticky=W)
        ttk.Entry(form_frame, textvariable=self.lieu_chargement_var).grid(row=2, column=1, columnspan=2, padx=5, pady=8, sticky=W+E)

        ttk.Label(form_frame, text="Date Commande").grid(row=2, column=3, padx=5, pady=8, sticky=W)
        date_cmd_entry = ttk.Entry(form_frame, textvariable=self.date_commande_var)
        date_cmd_entry.grid(row=2, column=4, padx=5, pady=8, sticky=W)
        ttk.Button(form_frame, text="Aujourd'hui", command=lambda: self.date_commande_var.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), 
                  bootstyle=INFO, width=12).grid(row=2, column=5, padx=5, pady=8, sticky=W)

        # Quatrième ligne
        ttk.Label(form_frame, text="Date Livraison").grid(row=3, column=0, padx=5, pady=8, sticky=W)
        date_liv_entry = ttk.Entry(form_frame, textvariable=self.date_livraison_var)
        date_liv_entry.grid(row=3, column=1, columnspan=2, padx=5, pady=8, sticky=W+E)
        ttk.Button(form_frame, text="+3 jours", command=lambda: self.date_livraison_var.set((datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")), 
                  bootstyle=INFO, width=12).grid(row=3, column=3, padx=5, pady=8, sticky=W)

        # Statut
        ttk.Label(form_frame, text="Statut").grid(row=3, column=4, padx=5, pady=8, sticky=W)
        status_types = ["En attente", "En cours", "Livrée", "Annulée"]
        self.statut_cb = ttk.Combobox(form_frame, textvariable=self.statut_var, values=status_types)
        self.statut_cb.grid(row=3, column=5, padx=5, pady=8, sticky=W)

        # Boutons d'actions
        btn_frame = ttk.Frame(main_frame, padding=10)
        btn_frame.pack(fill=X, pady=10)

        ttk.Button(btn_frame, text="Ajouter", command=self.ajouter, bootstyle=SUCCESS, width=15).pack(side=LEFT, padx=8)
        ttk.Button(btn_frame, text="Modifier", command=self.modifier, bootstyle=WARNING, width=15).pack(side=LEFT, padx=8)
        ttk.Button(btn_frame, text="Supprimer", command=self.supprimer, bootstyle=DANGER, width=15).pack(side=LEFT, padx=8)
        ttk.Button(btn_frame, text="Vider", command=self.vider_formulaire, bootstyle=SECONDARY, width=15).pack(side=LEFT, padx=8)
        
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
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=BOTH, expand=True, pady=10)
        
        # Barre de défilement pour le tableau
        scrollbar_y = ttk.Scrollbar(tree_frame)
        scrollbar_y.pack(side=RIGHT, fill=Y)
        
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=HORIZONTAL)
        scrollbar_x.pack(side=BOTTOM, fill=X)
        
        # Configuration du tableau
        self.tree = ttk.Treeview(tree_frame, columns=(
            "id_commande", "id_client", "tournee", "nature_service", 
            "type_vehicule", "quantite_requise", "lieu_chargement", 
            "date_commande", "date_livraison", "statut"), show="headings", 
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Configuration des barres de défilement
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Configuration des colonnes
        self.tree.heading("id_commande", text="ID")
        self.tree.heading("id_client", text="Client")
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
        
        # Contenu de l'onglet statistiques
        self.setup_stats_tab(stats_frame)
        
        # Barre d'état
        self.status_var = StringVar()
        self.status_var.set("Prêt")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side=BOTTOM, fill=X)

        # Chargement initial des données
        self.charger_clients()
        self.charger_tournees()
        self.charger_donnees()
    
    def setup_stats_tab(self, parent):
        """Configure l'onglet des statistiques"""
        # Frame pour les statistiques
        stats_frame = ttk.Frame(parent, padding=15)
        stats_frame.pack(fill=BOTH, expand=True)
        
        # Statistiques globales
        global_frame = ttk.LabelFrame(stats_frame, text="Statistiques globales", padding=15)
        global_frame.pack(fill=X, pady=15)
        
        # Variables pour les statistiques
        self.total_commandes_var = StringVar(value="0")
        self.commandes_retard_var = StringVar(value="0")
        self.commandes_sans_tournee_var = StringVar(value="0")
        
        # Affichage des statistiques
        ttk.Label(global_frame, text="Total des commandes:").grid(row=0, column=0, padx=8, pady=8, sticky=W)
        ttk.Label(global_frame, textvariable=self.total_commandes_var, width=12).grid(row=0, column=1, padx=8, pady=8, sticky=W)
        
        ttk.Label(global_frame, text="Commandes en retard:").grid(row=1, column=0, padx=8, pady=8, sticky=W)
        ttk.Label(global_frame, textvariable=self.commandes_retard_var, width=12).grid(row=1, column=1, padx=8, pady=8, sticky=W)
        
        ttk.Label(global_frame, text="Commandes sans tournée:").grid(row=2, column=0, padx=8, pady=8, sticky=W)
        ttk.Label(global_frame, textvariable=self.commandes_sans_tournee_var, width=12).grid(row=2, column=1, padx=8, pady=8, sticky=W)
        
        # Bouton pour rafraîchir les statistiques
        ttk.Button(global_frame, text="Rafraîchir", command=self.rafraichir_statistiques, 
                  bootstyle=PRIMARY, width=15).grid(row=3, column=0, columnspan=2, pady=15)
        
        # Graphique des commandes par type de véhicule
        chart_frame = ttk.LabelFrame(stats_frame, text="Répartition des commandes", padding=15)
        chart_frame.pack(fill=BOTH, expand=True, pady=15)
        
        # Ajout d'un espace pour un futur graphique
        canvas_frame = ttk.Frame(chart_frame, height=300)
        canvas_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(canvas_frame, text="Graphique de répartition des commandes").pack(pady=20)
        ttk.Button(canvas_frame, text="Générer graphique", 
                  bootstyle=INFO, width=20, command=self.generer_graphique).pack(pady=15)
    
    def generer_graphique(self):
        """Génère un graphique de répartition des commandes par type de véhicule"""
        try:
            # Cette fonction est préparée pour une future implémentation
            messagebox.showinfo("Information", "Fonctionnalité de graphique en cours de développement.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la génération du graphique: {str(e)}")
    
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
        
            sans_tournee = session.query(func.count(self.Commande.id_commande)).filter(
                ~exists().where(self.Tournee.id_commande == self.Commande.id_commande)
            ).scalar()
            
            self.commandes_sans_tournee_var.set(str(sans_tournee))
            
            messagebox.showinfo("Succès", "Statistiques mises à jour avec succès")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la mise à jour des statistiques: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_context_menu(self, event):
        """Affiche le menu contextuel sur clic droit"""
        if self.tree.selection():
            self.context_menu.post(event.x_root, event.y_root)

    def charger_clients(self):
        """Charge la liste des clients dans le combobox"""
        try:
            clients = session.query(self.Chantier).all()
            self.client_cb["values"] = [str(client.id_client) for client in clients]
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des clients: {str(e)}")

    def charger_tournees(self):
        """Charge la liste des tournées dans le combobox"""
        try:
            tournees = session.query(self.Tournee).all()
            self.tournee_cb["values"] = [""] + [str(tournee.id_tournee) for tournee in tournees]
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des tournées: {str(e)}")

    def ajouter(self):
        """Ajoute une nouvelle commande à la base de données"""
        try:
            # Validation des données
            if not self.id_client_var.get():
                messagebox.showwarning("Attention", "Veuillez sélectionner un client")
                return
                
            # Conversion des valeurs
            quantite = float(self.quantite_requise_var.get() or 0)
            
            # Dates par défaut si non fournies
            if not self.date_commande_var.get():
                date_commande = datetime.now()
                self.date_commande_var.set(date_commande.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                date_commande = datetime.strptime(self.date_commande_var.get(), "%Y-%m-%d %H:%M:%S")
                
            if not self.date_livraison_var.get():
                date_livraison = datetime.now() + timedelta(days=3)
                self.date_livraison_var.set(date_livraison.strftime("%Y-%m-%d %H:%M:%S"))
            else:
                date_livraison = datetime.strptime(self.date_livraison_var.get(), "%Y-%m-%d %H:%M:%S")
            
            # Création de la commande
            commande = self.Commande(
                id_client=self.id_client_var.get(),
                nature_service=self.nature_service_var.get(),
                type_vehicule=self.type_vehicule_var.get(),
                quantite_requise=quantite,
                lieu_chargement=self.lieu_chargement_var.get(),
                date_commande=date_commande,
                date_livraison=date_livraison
            )
            
            # Ajout de l'attribut statut (si on veut le gérer)
            if self.statut_var.get():
                if hasattr(commande, 'statut'):
                    commande.statut = self.statut_var.get()
            
            # Ajout à la base de données
            session.add(commande)
            session.commit()
            
            # Associer à une tournée si spécifiée
            if self.id_tournee_var.get():
                tournee_id = int(self.id_tournee_var.get())
                commande.associer_tournee(tournee_id)
                session.commit()
            
            # Mise à jour de l'interface
            self.charger_donnees()
            self.vider_formulaire()
            self.status_var.set(f"Commande ajoutée avec succès - {datetime.now().strftime('%H:%M:%S')}")
            messagebox.showinfo("Succès", "Commande ajoutée avec succès")
        except ValueError as e:
            messagebox.showerror("Erreur", f"Erreur de format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout: {str(e)}")
            import traceback
            traceback.print_exc()

    def modifier(self):
        """Modifie une commande existante"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande à modifier")
            return
        
        try:
            id_commande = int(self.tree.item(item, "values")[0])
            commande = session.query(self.Commande).filter_by(id_commande=id_commande).first()
            
            if commande:
                # Validation et conversion des valeurs
                quantite = float(self.quantite_requise_var.get() or 0)
                date_commande = datetime.strptime(self.date_commande_var.get(), "%Y-%m-%d %H:%M:%S")
                date_livraison = datetime.strptime(self.date_livraison_var.get(), "%Y-%m-%d %H:%M:%S")
                
                # Mise à jour de la commande
                commande.id_client = self.id_client_var.get()
                commande.nature_service = self.nature_service_var.get()
                commande.type_vehicule = self.type_vehicule_var.get()
                commande.quantite_requise = quantite
                commande.lieu_chargement = self.lieu_chargement_var.get()
                commande.date_commande = date_commande
                commande.date_livraison = date_livraison
                
                # Gestion du statut s'il est présent dans la classe
                if hasattr(commande, 'statut') and self.statut_var.get():
                    commande.statut = self.statut_var.get()
                
                # Traitement de la tournée
                if self.id_tournee_var.get():
                    # Associer à la nouvelle tournée
                    tournee_id = int(self.id_tournee_var.get())
                    commande.associer_tournee(tournee_id)
                else:
                    # Pour dissocier la tournée, on utilise la méthode associer_tournee avec None
                    commande.associer_tournee(None)
                
                # Mise à jour dans la base de données
                session.commit()
                
                # Mise à jour de l'interface
                self.charger_donnees()
                self.status_var.set(f"Commande n°{id_commande} modifiée - {datetime.now().strftime('%H:%M:%S')}")
                messagebox.showinfo("Succès", "Commande modifiée avec succès")
        except ValueError as e:
            messagebox.showerror("Erreur", f"Erreur de format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la modification: {str(e)}")
            import traceback
            traceback.print_exc()

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
                
                # Mise à jour de l'interface
                self.charger_donnees()
                self.vider_formulaire()
                self.status_var.set(f"Commande n°{id_commande} supprimée - {datetime.now().strftime('%H:%M:%S')}")
                messagebox.showinfo("Succès", "Commande supprimée avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")

    def selectionner(self, event=None):
        """Remplit le formulaire avec les données de la commande sélectionnée"""
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            self.id_commande_var.set(values[0])
            self.id_client_var.set(values[1])
            
            # Gestion du numéro de tournée
            tournee_id = values[2]
            if tournee_id and tournee_id != "None":
                self.id_tournee_var.set(tournee_id)
            else:
                self.id_tournee_var.set("")
                
            self.nature_service_var.set(values[3])
            self.type_vehicule_var.set(values[4])
            self.quantite_requise_var.set(values[5])
            self.lieu_chargement_var.set(values[6])
            self.date_commande_var.set(values[7])
            self.date_livraison_var.set(values[8])
            
            # Gestion du statut si présent
            if len(values) > 9:
                self.statut_var.set(values[9])
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
                
                # Récupérer le statut s'il existe
                statut = getattr(commande, 'statut', "En attente") if hasattr(commande, 'statut') else "En attente"
                
                self.tree.insert("", END, values=(
                    commande.id_commande, 
                    commande.id_client, 
                    id_tournee if id_tournee else "Non assignée",
                    commande.nature_service, 
                    commande.type_vehicule, 
                    commande.quantite_requise,
                    commande.lieu_chargement, 
                    commande.date_commande, 
                    commande.date_livraison,
                    statut
                ))
            
            # Mise à jour des statistiques si l'onglet existe
            if hasattr(self, 'total_commandes_var'):
                self.rafraichir_statistiques()
                
            self.status_var.set(f"Données chargées - {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données: {str(e)}")
            import traceback
            traceback.print_exc()

    def vider_formulaire(self):
        """Vide le formulaire pour une nouvelle saisie"""
        self.id_commande_var.set("")
        self.id_client_var.set("")
        self.id_tournee_var.set("")
        self.nature_service_var.set("")
        self.type_vehicule_var.set("")
        self.quantite_requise_var.set("")
        self.lieu_chargement_var.set("")
        self.date_commande_var.set("")
        self.date_livraison_var.set("")
        self.statut_var.set("")

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
        
        # Première ligne
        ttk.Label(criteria_frame, text="ID Client:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(criteria_frame, textvariable=client_search_var).grid(row=0, column=1, padx=5, pady=5, sticky=W+E)
        
        ttk.Label(criteria_frame, text="Type véhicule:").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        vehicle_types = ["", "Camion", "Semi-remorque", "Fourgon", "Benne", "Citerne"]
        ttk.Combobox(criteria_frame, textvariable=vehicle_search_var, values=vehicle_types).grid(row=0, column=3, padx=5, pady=5, sticky=W+E)
        
        # Deuxième ligne
        ttk.Label(criteria_frame, text="Date livraison de:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(criteria_frame, textvariable=date_from_var).grid(row=1, column=1, padx=5, pady=5, sticky=W+E)
        
        ttk.Label(criteria_frame, text="à:").grid(row=1, column=2, padx=5, pady=5, sticky=W)
        ttk.Entry(criteria_frame, textvariable=date_to_var).grid(row=1, column=3, padx=5, pady=5, sticky=W+E)
        
        # Boutons de recherche
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=10)
        
        def executer_recherche():
            """Exécute la recherche selon les critères spécifiés"""
            try:
                # Construire la requête de base
                query = session.query(self.Commande)
                
                # Appliquer les filtres
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
                
                # Exécuter la requête
                resultats = query.all()
                
                # Vider le tableau des résultats
                for item in result_tree.get_children():
                    result_tree.delete(item)
                    
                # Remplir avec les nouveaux résultats
                for commande in resultats:
                    # Récupérer l'ID de la tournée via la relation, s'il existe
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
                    
                # Mettre à jour le statut
                status_var.set(f"Recherche terminée - {len(resultats)} résultat(s)")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la recherche: {str(e)}")
                import traceback
                traceback.print_exc()
        def exporter_resultats():
            """Exporte les résultats de la recherche dans un fichier CSV"""
            # Vérifier s'il y a des résultats à exporter
            if not result_tree.get_children():
                messagebox.showinfo("Information", "Aucun résultat à exporter.")
                return
                
            try:
                import csv
                from tkinter import filedialog
                
                # Demander où enregistrer le fichier
                fichier = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Enregistrer les résultats"
                )
                
                if not fichier:
                    return  # Annulation par l'utilisateur
                
                # Écrire les données dans le fichier CSV
                with open(fichier, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';')
                    
                    # En-têtes
                    headers = ["ID", "Client", "Tournée", "Service", "Véhicule", 
                            "Quantité", "Lieu", "Date Commande", "Date Livraison"]
                    writer.writerow(headers)
                    
                    # Données
                    for item_id in result_tree.get_children():
                        values = result_tree.item(item_id, "values")
                        writer.writerow(values)
                
                # Confirmation
                messagebox.showinfo("Succès", f"Les résultats ont été exportés vers {fichier}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'exportation: {str(e)}")
        
        ttk.Button(btn_frame, text="Rechercher", command=executer_recherche, 
                bootstyle=PRIMARY, width=15).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter CSV", command=exporter_resultats, 
                bootstyle=SUCCESS, width=15).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Fermer", command=recherche_window.destroy, 
                bootstyle=SECONDARY, width=15).pack(side=RIGHT, padx=5)
        
        # Tableau des résultats
        result_frame = ttk.LabelFrame(main_frame, text="Résultats", padding=10)
        result_frame.pack(fill=BOTH, expand=True, pady=10)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(result_frame)
        y_scrollbar.pack(side=RIGHT, fill=Y)
        
        x_scrollbar = ttk.Scrollbar(result_frame, orient=HORIZONTAL)
        x_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Tableau
        result_tree = ttk.Treeview(result_frame, columns=(
            "id_commande", "id_client", "id_tournee", "nature_service", 
            "type_vehicule", "quantite_requise", "lieu_chargement", 
            "date_commande", "date_livraison"), show="headings",
            yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Configuration des barres de défilement
        y_scrollbar.config(command=result_tree.yview)
        x_scrollbar.config(command=result_tree.xview)
        
        # Configuration des colonnes
        result_tree.heading("id_commande", text="ID")
        result_tree.heading("id_client", text="Client")
        result_tree.heading("id_tournee", text="Tournée")
        result_tree.heading("nature_service", text="Service")
        result_tree.heading("type_vehicule", text="Véhicule")
        result_tree.heading("quantite_requise", text="Quantité")
        result_tree.heading("lieu_chargement", text="Lieu")
        result_tree.heading("date_commande", text="Date Commande")
        result_tree.heading("date_livraison", text="Date Livraison")
        
        # Configurer les largeurs des colonnes
        result_tree.column("id_commande", width=50)
        result_tree.column("id_client", width=50)
        result_tree.column("id_tournee", width=50)
        result_tree.column("nature_service", width=120)
        result_tree.column("type_vehicule", width=100)
        result_tree.column("quantite_requise", width=80)
        result_tree.column("lieu_chargement", width=120)
        result_tree.column("date_commande", width=150)
        result_tree.column("date_livraison", width=150)
        
        # Pack le tableau
        result_tree.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Barre d'état pour les résultats
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
                
                # Frame pour les détails
                details_frame = ttk.Frame(details_window, padding=15)
                details_frame.pack(fill=BOTH, expand=True)
                
                # Affichage des détails du client
                ttk.Label(details_frame, text=f"ID: {client.id_client}", font=("Segoe UI", 12, "bold")).pack(anchor=W, pady=5)
                ttk.Label(details_frame, text=f"Nom: {getattr(client, 'nom', 'Non spécifié')}").pack(anchor=W, pady=2)
                ttk.Label(details_frame, text=f"Adresse: {getattr(client, 'adresse', 'Non spécifiée')}").pack(anchor=W, pady=2)
                ttk.Label(details_frame, text=f"Contact: {getattr(client, 'contact', 'Non spécifié')}").pack(anchor=W, pady=2)
                ttk.Label(details_frame, text=f"Téléphone: {getattr(client, 'telephone', 'Non spécifié')}").pack(anchor=W, pady=2)
                
                # Statistiques du client
                stats_frame = ttk.LabelFrame(details_frame, text="Statistiques", padding=10)
                stats_frame.pack(fill=X, pady=10)
                
                # Nombre de commandes pour ce client
                nb_commandes = session.query(func.count(self.Commande.id_commande)).filter(
                    self.Commande.id_client == id_client).scalar()
                ttk.Label(stats_frame, text=f"Nombre de commandes: {nb_commandes}").pack(anchor=W, pady=2)
                
                # Bouton pour fermer
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
                # Ouvre une boîte de dialogue pour entrer les paramètres
                distance = simpledialog.askfloat("Distance", "Distance à parcourir (km):", minvalue=0.1)
                if distance is None:
                    return  # L'utilisateur a annulé
                    
                poids = simpledialog.askfloat("Poids", "Poids de la cargaison (kg):", minvalue=0.1)
                if poids is None:
                    return  # L'utilisateur a annulé
                
                # Calcule le délai
                delai = commande.calculer_delai_livraison(distance, poids)
                
                # Affiche le résultat
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
                # Vérifier si la commande est déjà livrée
                if hasattr(commande, 'statut') and commande.statut == 'livrée':
                    messagebox.showinfo("Information", f"La commande n°{id_commande} est déjà marquée comme livrée.")
                    return
                
                # Demander une confirmation
                confirmation = messagebox.askyesno("Confirmation", 
                                                f"Êtes-vous sûr de vouloir marquer la commande n°{id_commande} comme livrée ?")
                if not confirmation:
                    return
                
                # Ajouter un attribut statut si la classe ne l'a pas déjà
                if not hasattr(commande, 'statut'):
                    # On peut ajouter un attribut dynamiquement, mais cela ne sera pas sauvegardé dans la base
                    commande.statut = 'livrée'
                    messagebox.showinfo("Succès", f"La commande n°{id_commande} a été marquée comme livrée.")
                    messagebox.showwarning("Attention", "L'attribut 'statut' n'est pas persistant dans la base de données. "
                                        "Pensez à ajouter cette colonne à votre modèle pour un suivi permanent.")
                else:
                    # Si l'attribut existe dans le modèle de la base
                    commande.statut = 'livrée'
                    session.commit()
                    messagebox.showinfo("Succès", f"La commande n°{id_commande} a été marquée comme livrée.")
                
                # Mettre à jour l'interface
                self.charger_donnees()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du marquage: {str(e)}")
# Point d'entrée pour l'application
def main():
    root = ttk.Window(themename="cosmo")
    app = CommandeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
