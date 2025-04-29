import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar, IntVar, DISABLED, X, LEFT, BOTH
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func, or_
from datetime import date, datetime
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from tkinter import filedialog
import datetime

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class TransfererEquipementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Transferts d'Équipements")
        self.root.geometry("1200x700")
        
        # Import local pour éviter les imports circulaires
        from application.models.transferer_equipement import TransfererEquipement
        from application.models.chantiers import Chantier
        from application.models.equipements import Equipement
        self.TransfererEquipement = TransfererEquipement
        self.Chantier = Chantier
        self.Equipement = Equipement

        # Variables
        self.id_var = IntVar()
        self.volet_var = StringVar()
        self.nom_equipement_var = StringVar()  # Pour saisir le nom de l'équipement
        self.equipement_id_var = IntVar()  # Pour stocker l'ID de l'équipement correspondant
        self.modalite_transport_var = StringVar()
        self.total_equipements_var = IntVar(value=1)  # Valeur par défaut à 1
        self.id_client_var = StringVar()
        self.localisation_client_var = StringVar()  # Pour afficher la localisation
        self.recherche_var = StringVar()  # Variable pour la recherche
        
        # Variables pour les semaines
        self.semaines_vars = {
            'douze': IntVar(),
            'onze': IntVar(),
            'dix': IntVar(),
            'neuf': IntVar(),
            'huit': IntVar(),
            'sept': IntVar(),
            'six': IntVar(),
            'cinq': IntVar(),
            'quatre': IntVar(),
            'trois': IntVar(),
            'deux': IntVar(),
            'un': IntVar(),
            'zero': IntVar()
        }

        # Filtre client
        self.filtre_client_var = StringVar()
        
        # Cache pour les équipements
        self.equipements_cache = {}
        
        # Création de l'interface
        self.creer_interface()
        
        # Charger les données
        self.charger_clients()
        self.charger_equipements()
        self.charger_donnees()

    def creer_interface(self):
        """Crée l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Frame de recherche et filtre
        top_frame = ttk.Frame(main_frame, padding=10)
        top_frame.pack(fill=X)
        
        # Barre de recherche
        ttk.Label(top_frame, text="Rechercher:").pack(side=LEFT, padx=5)
        recherche_entry = ttk.Entry(top_frame, textvariable=self.recherche_var, width=30)
        recherche_entry.pack(side=LEFT, padx=5)
        recherche_entry.bind("<Return>", lambda e: self.rechercher())
        ttk.Button(top_frame, text="Rechercher", command=self.rechercher, bootstyle=INFO).pack(side=LEFT, padx=5)
        
        # Filtre client
        ttk.Label(top_frame, text="Filtrer par client:").pack(side=LEFT, padx=20)
        self.client_filter_cb = ttk.Combobox(top_frame, textvariable=self.filtre_client_var, state="readonly", width=30)
        self.client_filter_cb.pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="Appliquer filtre", command=self.appliquer_filtre, bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="Réinitialiser", command=self.reinitialiser_filtre, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        
        # Création du notebook pour l'interface à onglets
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Onglet de liste des transferts
        list_frame = ttk.Frame(notebook, padding=10)
        notebook.add(list_frame, text="Liste des transferts")
        
        # Onglet de formulaire
        form_frame = ttk.Frame(notebook, padding=10)
        notebook.add(form_frame, text="Formulaire de transfert")
        
        # Création du tableau dans l'onglet liste
        self.creer_tableau(list_frame)
        
        # Création du formulaire dans l'onglet formulaire
        self.creer_formulaire(form_frame)

    def creer_tableau(self, parent):
        """Crée le tableau des transferts d'équipements"""
        # Frame pour les boutons d'action
        btn_frame = ttk.Frame(parent, padding=5)
        btn_frame.pack(fill=X, pady=5)
        
        ttk.Button(btn_frame, text="Ajouter nouveau", command=lambda: self.basculer_vers_formulaire(nouveau=True), 
                  bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Modifier sélection", command=self.modifier_selection, 
                  bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer sélection", command=self.supprimer, 
                  bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Rafraîchir", command=self.charger_donnees, 
                  bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter PDF", command=self.generer_rapport, 
                  bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        
        # Configuration du tableau
        columns = ("id", "id_client", "localisation", "volet", "nom_equipement", "modalite_transport", 
                  "total_equipements", "12_semaines", "11_semaines", "10_semaines", "9_semaines", 
                  "8_semaines", "7_semaines", "6_semaines", "5_semaines", "4_semaines", 
                  "3_semaines", "2_semaines", "1_semaines", "0_semaines")
        
        self.tree = ttk.Treeview(parent, columns=columns, show="headings")
        self.tree.pack(fill=BOTH, expand=True)

        # Configuration des en-têtes
        self.tree.heading("id", text="ID", command=lambda: self.trier_tableau("id"))
        self.tree.heading("id_client", text="Client", command=lambda: self.trier_tableau("id_client"))
        self.tree.heading("localisation", text="Localisation", command=lambda: self.trier_tableau("localisation"))
        self.tree.heading("volet", text="Volet", command=lambda: self.trier_tableau("volet"))
        self.tree.heading("nom_equipement", text="Nom Équipement", command=lambda: self.trier_tableau("nom_equipement"))
        self.tree.heading("modalite_transport", text="Modalité Transport", command=lambda: self.trier_tableau("modalite_transport"))
        self.tree.heading("total_equipements", text="Total", command=lambda: self.trier_tableau("total_equipements"))
        
        # Configuration des en-têtes pour les semaines
        for i in range(12, -1, -1):
            col_name = f"{i}_semaines"
            self.tree.heading(col_name, text=f"{i} sem.", command=lambda i=i: self.trier_tableau(f"{i}_semaines"))
        
        # Configuration des largeurs de colonnes
        self.tree.column("id", width=50)
        self.tree.column("id_client", width=120)
        self.tree.column("localisation", width=120)
        self.tree.column("volet", width=80)
        self.tree.column("nom_equipement", width=200)
        self.tree.column("modalite_transport", width=120)
        self.tree.column("total_equipements", width=60)
        
        # Configuration des largeurs pour les semaines
        for col in columns[7:]:
            self.tree.column(col, width=60)

        # Binding pour la sélection d'élément avec double-clic
        self.tree.bind("<Double-1>", self.modifier_selection)
        
        # Ajout des barres de défilement
        y_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        y_scrollbar.pack(side="right", fill="y")
        
        x_scrollbar = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)
        x_scrollbar.pack(side="bottom", fill="x")
        
        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

    def creer_formulaire(self, parent):
        """Crée le formulaire de saisie"""
        # Frame pour les informations de base
        info_frame = ttk.LabelFrame(parent, text="Informations générales", padding=10)
        info_frame.pack(fill=X, pady=5)
        
        # Première ligne: ID et Client
        ttk.Label(info_frame, text="ID:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(info_frame, textvariable=self.id_var, state=DISABLED, width=5).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Client:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.client_cb = ttk.Combobox(info_frame, textvariable=self.id_client_var, state="readonly", width=20)
        self.client_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.client_cb.bind("<<ComboboxSelected>>", self.actualiser_localisation_client)
        
        ttk.Label(info_frame, text="Localisation:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        ttk.Entry(info_frame, textvariable=self.localisation_client_var, state=DISABLED, width=20).grid(row=0, column=5, padx=5, pady=5, sticky="w")
        
        # Deuxième ligne: Volet et Modalité
        ttk.Label(info_frame, text="Volet:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(info_frame, textvariable=self.volet_var, width=15).grid(row=1, column=1, padx=5, pady=5, sticky="w", columnspan=2)
        
        ttk.Label(info_frame, text="Modalité Transport:").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        transport_cb = ttk.Combobox(info_frame, textvariable=self.modalite_transport_var, values=["Camion", "Train", "Bateau", "Avion"], width=15)
        transport_cb.grid(row=1, column=4, padx=5, pady=5, sticky="w")
        
        # Troisième ligne: Nom équipement et Total
        ttk.Label(info_frame, text="Nom Équipement:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.equipement_cb = ttk.Combobox(info_frame, textvariable=self.nom_equipement_var, width=30)
        self.equipement_cb.grid(row=2, column=1, padx=5, pady=5, sticky="w", columnspan=3)
        self.equipement_cb.bind("<<ComboboxSelected>>", self.actualiser_id_equipement)
        
        ttk.Label(info_frame, text="Total Équipements:").grid(row=2, column=4, padx=5, pady=5, sticky="e")
        ttk.Spinbox(info_frame, textvariable=self.total_equipements_var, from_=1, to=1000, width=5).grid(row=2, column=5, padx=5, pady=5, sticky="w")
        
        # Frame pour les semaines
        semaines_frame = ttk.LabelFrame(parent, text="Planification des transferts (semaines avant la fin de l'ancien projet)", padding=10)
        semaines_frame.pack(fill=X, pady=10)
        
        # Première ligne de semaines (12 à 7)
        for i, semaine in enumerate(['douze', 'onze', 'dix', 'neuf', 'huit', 'sept']):
            ttk.Label(semaines_frame, text=f"{12-i} semaines:").grid(row=0, column=i*2, padx=5, pady=5, sticky="e")
            ttk.Spinbox(semaines_frame, textvariable=self.semaines_vars[semaine], from_=0, to=1000, width=5).grid(row=0, column=i*2+1, padx=5, pady=5, sticky="w")
        
        # Deuxième ligne de semaines (6 à 1)
        for i, semaine in enumerate(['six', 'cinq', 'quatre', 'trois', 'deux', 'un']):
            ttk.Label(semaines_frame, text=f"{6-i} semaines:").grid(row=1, column=i*2, padx=5, pady=5, sticky="e")
            ttk.Spinbox(semaines_frame, textvariable=self.semaines_vars[semaine], from_=0, to=1000, width=5).grid(row=1, column=i*2+1, padx=5, pady=5, sticky="w")
        
        # Dernière ligne (0 semaines)
        ttk.Label(semaines_frame, text="0 semaine:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Spinbox(semaines_frame, textvariable=self.semaines_vars['zero'], from_=0, to=1000, width=5).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Boutons d'action pour le formulaire
        btn_frame = ttk.Frame(parent, padding=10)
        btn_frame.pack(fill=X, pady=10)
        
        ttk.Button(btn_frame, text="Enregistrer", command=self.enregistrer, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Vider formulaire", command=self.vider_formulaire, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=lambda: self.root.children['!notebook'].select(0), bootstyle=DANGER).pack(side=LEFT, padx=5)

    def charger_equipements(self):
        """Charge la liste des équipements pour le combobox"""
        try:
            equipements = session.query(self.Equipement).order_by(self.Equipement.nomEquipement).all()
            self.equipement_cb['values'] = [e.nomEquipement for e in equipements]
            
            # Mettre en cache les équipements pour une recherche rapide
            self.equipements_cache = {e.nomEquipement: e.ID_equipement for e in equipements}
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les équipements: {str(e)}")
            print(f"Erreur lors du chargement des équipements: {str(e)}")

    def actualiser_id_equipement(self, event=None):
        """Met à jour l'ID d'équipement en fonction du nom sélectionné"""
        nom_equipement = self.nom_equipement_var.get()
        if nom_equipement in self.equipements_cache:
            self.equipement_id_var.set(self.equipements_cache[nom_equipement])
        else:
            self.equipement_id_var.set(0)

    def actualiser_localisation_client(self, event=None):
        """Met à jour la localisation du client sélectionné"""
        id_client = self.id_client_var.get()
        if id_client:
            client = session.query(self.Chantier).filter_by(id_client=id_client).first()
            if client:
                self.localisation_client_var.set(client.localisation or "Non spécifiée")
            else:
                self.localisation_client_var.set("Client inconnu")
        else:
            self.localisation_client_var.set("")

    def basculer_vers_formulaire(self, nouveau=False):
        """Bascule vers l'onglet du formulaire"""
        if nouveau:
            self.vider_formulaire()
        self.root.children['!notebook'].select(1)  # Sélectionner l'onglet du formulaire

    def charger_clients(self):
        """Charge la liste des clients pour les combobox"""
        try:
            clients = session.query(self.Chantier).order_by(self.Chantier.id_client).all()
            client_ids = [c.id_client for c in clients]
            
            # Mise à jour des combobox
            self.client_cb['values'] = client_ids
            self.client_filter_cb['values'] = ["Tous"] + client_ids
            self.filtre_client_var.set("Tous")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les clients: {str(e)}")
            print(f"Erreur lors du chargement des clients: {str(e)}")

    def enregistrer(self):
        """Enregistre un transfert (ajout ou modification)"""
        if not self.validation_formulaire():
            return

        try:
            # Vérifier si le nom d'équipement existe
            nom_equipement = self.nom_equipement_var.get()
            id_equipement = self.equipements_cache.get(nom_equipement)
            
            if not id_equipement:
                messagebox.showerror("Erreur", f"L'équipement '{nom_equipement}' n'existe pas dans la base de données")
                return
            
            # Préparation des données pour le modèle
            transfert_data = {
                "volet": self.volet_var.get() or None,
                "nom_equipement": nom_equipement,
                "id_equipement": id_equipement,
                "modalite_transport": self.modalite_transport_var.get() or None,
                "total_equipements": self.total_equipements_var.get(),
                "id_client": self.id_client_var.get(),
                "douze_semaines_avant": self.semaines_vars['douze'].get() or None,
                "onze_semaines_avant": self.semaines_vars['onze'].get() or None,
                "dix_semaines_avant": self.semaines_vars['dix'].get() or None,
                "neuf_semaines_avant": self.semaines_vars['neuf'].get() or None,
                "huit_semaines_avant": self.semaines_vars['huit'].get() or None,
                "sept_semaines_avant": self.semaines_vars['sept'].get() or None,
                "six_semaines_avant": self.semaines_vars['six'].get() or None,
                "cinq_semaines_avant": self.semaines_vars['cinq'].get() or None,
                "quatre_semaines_avant": self.semaines_vars['quatre'].get() or None,
                "trois_semaines_avant": self.semaines_vars['trois'].get() or None,
                "deux_semaines_avant": self.semaines_vars['deux'].get() or None,
                "un_semaines_avant": self.semaines_vars['un'].get() or None,
                "zero_semaines_avant": self.semaines_vars['zero'].get() or None
            }
            
            # Vérifier s'il s'agit d'un ajout ou d'une modification
            if self.id_var.get() == 0:  # Ajout
                # Créer un nouveau transfert en utilisant le constructeur avec les bons noms d'attributs
                transfert = self.TransfererEquipement(**transfert_data)
                session.add(transfert)
                message_succes = "Transfert d'équipement ajouté avec succès"
            else:  # Modification
                transfert = session.query(self.TransfererEquipement).filter_by(id=self.id_var.get()).first()
                if transfert:
                    # Mettre à jour les attributs individuellement
                    for key, value in transfert_data.items():
                        setattr(transfert, key, value)
                    message_succes = "Transfert d'équipement modifié avec succès"
                else:
                    messagebox.showerror("Erreur", f"Transfert avec ID {self.id_var.get()} non trouvé")
                    return
            
            session.commit()
            messagebox.showinfo("Succès", message_succes)
            self.charger_donnees()
            self.vider_formulaire()
            # Revenir à l'onglet liste
            self.root.children['!notebook'].select(0)
        except Exception as e:
            session.rollback()
            messagebox.showerror("Erreur", f"Impossible d'enregistrer le transfert: {str(e)}")
            print(f"Erreur lors de l'enregistrement: {str(e)}")

    def modifier_selection(self, event=None):
        """Prépare le formulaire pour modifier un élément sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un transfert à modifier.")
            return
            
        item_id = self.tree.item(selection[0], "values")[0]
        try:
            # Jointure avec la table des équipements pour obtenir le nom
            transfert = session.query(self.TransfererEquipement, self.Equipement.nomEquipement)\
                .join(self.Equipement, self.TransfererEquipement.id_equipement == self.Equipement.ID_equipement)\
                .filter(self.TransfererEquipement.id == item_id).first()
                
            if transfert:
                transfert_obj, nom_equipement = transfert
                
                # Remplir le formulaire avec les données
                self.id_var.set(transfert_obj.id)
                self.id_client_var.set(transfert_obj.id_client)
                self.volet_var.set(transfert_obj.volet or "")
                self.nom_equipement_var.set(nom_equipement)
                self.equipement_id_var.set(transfert_obj.id_equipement)
                self.modalite_transport_var.set(transfert_obj.modalite_transport or "")
                self.total_equipements_var.set(transfert_obj.total_equipements)
                
                # Mise à jour des variables pour les semaines
                self.semaines_vars['douze'].set(transfert_obj.douze_semaines_avant or 0)
                self.semaines_vars['onze'].set(transfert_obj.onze_semaines_avant or 0)
                self.semaines_vars['dix'].set(transfert_obj.dix_semaines_avant or 0)
                self.semaines_vars['neuf'].set(transfert_obj.neuf_semaines_avant or 0)
                self.semaines_vars['huit'].set(transfert_obj.huit_semaines_avant or 0)
                self.semaines_vars['sept'].set(transfert_obj.sept_semaines_avant or 0)
                self.semaines_vars['six'].set(transfert_obj.six_semaines_avant or 0)
                self.semaines_vars['cinq'].set(transfert_obj.cinq_semaines_avant or 0)
                self.semaines_vars['quatre'].set(transfert_obj.quatre_semaines_avant or 0)
                self.semaines_vars['trois'].set(transfert_obj.trois_semaines_avant or 0)
                self.semaines_vars['deux'].set(transfert_obj.deux_semaines_avant or 0)
                self.semaines_vars['un'].set(transfert_obj.un_semaines_avant or 0)
                self.semaines_vars['zero'].set(transfert_obj.zero_semaines_avant or 0)
                
                # Mise à jour de la localisation
                self.actualiser_localisation_client()
                
                # Basculer vers l'onglet formulaire
                self.basculer_vers_formulaire()
            else:
                messagebox.showerror("Erreur", f"Transfert avec ID {item_id} non trouvé")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données du transfert: {str(e)}")
            print(f"Erreur lors du chargement du transfert {item_id}: {str(e)}")

    def supprimer(self):
        """Supprime un transfert d'équipement"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un transfert à supprimer")
            return
            
        item_id = self.tree.item(selection[0], "values")[0]
        confirmation = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer ce transfert d'équipement?")
        
        if confirmation:
            try:
                session.query(self.TransfererEquipement).filter_by(id=item_id).delete()
                session.commit()
                messagebox.showinfo("Succès", "Transfert d'équipement supprimé avec succès")
                self.charger_donnees()
                self.vider_formulaire()
            except Exception as e:
                session.rollback()
                messagebox.showerror("Erreur", f"Impossible de supprimer le transfert: {str(e)}")

    def charger_donnees(self):
        """Charge les données dans le tableau"""
        # Effacer les données existantes
        self.tree.delete(*self.tree.get_children())
        
        try:
            # Préparer la requête avec jointures pour obtenir à la fois la localisation et le nom de l'équipement
            query = session.query(
                self.TransfererEquipement, 
                self.Chantier.localisation,
                self.Equipement.nomEquipement
            ).join(
                self.Chantier, 
                self.TransfererEquipement.id_client == self.Chantier.id_client, 
                isouter=True
            ).join(
                self.Equipement,
                self.TransfererEquipement.id_equipement == self.Equipement.ID_equipement,
                isouter=True
            )
            
            # Appliquer le filtre client si nécessaire
            if self.filtre_client_var.get() != "Tous":
                query = query.filter(self.TransfererEquipement.id_client == self.filtre_client_var.get())
            
            # Appliquer le filtre de recherche si présent
            if self.recherche_var.get():
                recherche = f"%{self.recherche_var.get()}%"
                query = query.filter(
                    or_(
                        self.TransfererEquipement.id_client.like(recherche),
                        self.TransfererEquipement.volet.like(recherche),
                        self.Equipement.nomEquipement.like(recherche),
                        self.TransfererEquipement.modalite_transport.like(recherche),
                        self.Chantier.localisation.like(recherche)
                    )
                )
            
            transferts = query.order_by(self.TransfererEquipement.id).all()
            
            # Remplir le tableau avec les données
            for transfert, localisation, nom_equipement in transferts:
                self.tree.insert("", "end", 
                values = (
                    transfert.id,
                    transfert.id_client,
                    localisation or "Non spécifiée",
                    transfert.volet or "",
                    nom_equipement or "Inconnu",
                    transfert.modalite_transport or "",
                    transfert.total_equipements,
                    transfert.douze_semaines_avant or 0,
                    transfert.onze_semaines_avant or 0,
                    transfert.dix_semaines_avant or 0,
                    transfert.neuf_semaines_avant or 0,
                    transfert.huit_semaines_avant or 0,
                    transfert.sept_semaines_avant or 0,
                    transfert.six_semaines_avant or 0,
                    transfert.cinq_semaines_avant or 0,
                    transfert.quatre_semaines_avant or 0,
                    transfert.trois_semaines_avant or 0,
                    transfert.deux_semaines_avant or 0,
                    transfert.un_semaines_avant or 0,
                    transfert.zero_semaines_avant or 0
                )
                )
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données: {str(e)}")
            print(f"Erreur lors du chargement des données: {str(e)}")

    def vider_formulaire(self):
        """Réinitialise le formulaire pour un nouvel ajout"""
        self.id_var.set(0)
        self.volet_var.set("")
        self.nom_equipement_var.set("")
        self.equipement_id_var.set(0)
        self.modalite_transport_var.set("")
        self.total_equipements_var.set(1)
        self.id_client_var.set("")
        self.localisation_client_var.set("")
        
        # Réinitialiser les semaines
        for semaine in self.semaines_vars:
            self.semaines_vars[semaine].set(0)

    def validation_formulaire(self):
        """Valide le formulaire avant enregistrement"""
        # Vérifier les champs obligatoires
        if not self.id_client_var.get():
            messagebox.showwarning("Validation", "Veuillez sélectionner un client")
            return False
            
        if not self.nom_equipement_var.get():
            messagebox.showwarning("Validation", "Veuillez sélectionner un équipement")
            return False
            
        if not self.total_equipements_var.get() or self.total_equipements_var.get() <= 0:
            messagebox.showwarning("Validation", "Le nombre total d'équipements doit être supérieur à 0")
            return False
            
        return True

    def rechercher(self):
        """Effectue une recherche dans les données"""
        self.charger_donnees()  # Recharge les données avec le filtre de recherche

    def appliquer_filtre(self):
        """Applique le filtre par client"""
        self.charger_donnees()  # Recharge les données avec le filtre client

    def reinitialiser_filtre(self):
        """Réinitialise les filtres"""
        self.recherche_var.set("")
        self.filtre_client_var.set("Tous")
        self.charger_donnees()  # Recharge toutes les données

    def trier_tableau(self, colonne):
        """Trie le tableau selon la colonne spécifiée"""
        # Obtenir les données actuelles du tableau
        data = [(self.tree.set(child, colonne), child) for child in self.tree.get_children('')]
        
        # Tenter de trier les données numériquement, sinon trier alphabétiquement
        try:
            # Pour les colonnes numériques
            data.sort(key=lambda x: float(x[0]) if x[0].strip() else 0)
        except ValueError:
            # Pour les colonnes textuelles
            data.sort(key=lambda x: x[0].lower())
        
        # Réorganiser les éléments dans le tableau selon le tri
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
        
        # Inverser l'ordre pour le prochain clic
        if hasattr(self, 'last_sort') and self.last_sort == colonne:
            data.reverse()
            for index, (val, child) in enumerate(data):
                self.tree.move(child, '', index)
            self.last_sort = None
        else:
            self.last_sort = colonne

    def generer_rapport(self):
        """Génère un rapport PDF des transferts d'équipements"""
        try:
            # Demander où enregistrer le fichier
            fichier = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Enregistrer le rapport"
            )
            
            if not fichier:  # Si l'utilisateur annule
                return
            
            # Création du document PDF
            doc = SimpleDocTemplate(
                fichier,
                pagesize=landscape(A4),
                title="Rapport des transferts d'équipements"
            )
            
            # Styles pour les textes
            styles = getSampleStyleSheet()
            titre_style = styles['Heading1']
            sous_titre_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Construction du contenu
            contenu = []
            
            # Titre du rapport
            titre = Paragraph("Rapport des transferts d'équipements", titre_style)
            contenu.append(titre)
            contenu.append(Spacer(1, 12))
            
            # Date de génération
            date_rapport = Paragraph(f"Généré le : {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M')}", normal_style)
            contenu.append(date_rapport)
            contenu.append(Spacer(1, 12))
            
            # Sous-titre avec filtres appliqués
            filtre_texte = "Tous les clients"
            if self.filtre_client_var.get() != "Tous":
                filtre_texte = f"Client: {self.filtre_client_var.get()}"
                
            if self.recherche_var.get():
                filtre_texte += f" | Recherche: {self.recherche_var.get()}"
                
            sous_titre = Paragraph(f"Filtres: {filtre_texte}", sous_titre_style)
            contenu.append(sous_titre)
            contenu.append(Spacer(1, 20))
            
            # Préparation des données pour le tableau
            donnees = []
            
            # En-têtes du tableau
            en_tetes = [
                "ID", "Client", "Localisation", "Volet", "Équipement", 
                "Transport", "Total", "12 sem", "11 sem", "10 sem", "9 sem", 
                "8 sem", "7 sem", "6 sem", "5 sem", "4 sem", "3 sem", 
                "2 sem", "1 sem", "0 sem"
            ]
            donnees.append(en_tetes)
            
            # Récupération des données du tableau affiché
            for item in self.tree.get_children():
                ligne = list(self.tree.item(item, "values"))
                donnees.append(ligne)
            
            # Création du tableau PDF
            if len(donnees) > 1:  # S'il y a des données à afficher
                tableau = Table(donnees)
                
                # Style du tableau
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                
                # Application du style alterné pour les lignes
                for i in range(1, len(donnees)):
                    if i % 2 == 0:
                        style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
                
                tableau.setStyle(style)
                contenu.append(tableau)
            else:
                # Message si aucune donnée
                contenu.append(Paragraph("Aucune donnée à afficher", normal_style))
            
            # Génération du PDF
            doc.build(contenu)
            
            # Message de confirmation
            messagebox.showinfo("Succès", f"Rapport PDF généré avec succès : {fichier}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de générer le rapport PDF: {str(e)}")
            print(f"Erreur lors de la génération du rapport: {str(e)}")

if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = TransfererEquipementApp(root)
    root.mainloop()