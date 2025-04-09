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
        self.root.geometry("1200x700")  # Augmenté la hauteur pour plus d'espace
        
        # Import local pour éviter les imports circulaires
        from application.models.transferer_equipement import TransfererEquipement
        from application.models.chantiers import Chantier
        self.TransfererEquipement = TransfererEquipement
        self.Chantier = Chantier

        # Variables
        self.id_var = IntVar()
        self.volet_var = StringVar()
        self.designation_equipement_var = StringVar()
        self.modalite_transport_var = StringVar()
        self.total_equipements_var = IntVar(value=1)  # Valeur par défaut à 1
        self.id_client_var = StringVar()
        self.localisation_client_var = StringVar()  # Nouvelle variable pour afficher la localisation
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
        
        # Création de l'interface
        self.creer_interface()
        
        # Charger les données
        self.charger_clients()
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
        
        # Configuration du tableau
        columns = ("id", "id_client", "localisation", "volet", "designation_equipement", "modalite_transport", 
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
        self.tree.heading("designation_equipement", text="Désignation Équipement", command=lambda: self.trier_tableau("designation_equipement"))
        self.tree.heading("modalite_transport", text="Modalité Transport", command=lambda: self.trier_tableau("modalite_transport"))
        self.tree.heading("total_equipements", text="Total", command=lambda: self.trier_tableau("total_equipements"))
        
        # Configuration des en-têtes pour les semaines
        # Configuration des en-têtes pour les semaines
        # Configuration des en-têtes pour les semaines
        for i in range(12, -1, -1):
            col_name = f"{i}_semaines"  # Toujours au pluriel pour toutes les semaines
            self.tree.heading(col_name, text=f"{i} sem.", command=lambda i=i: self.trier_tableau(f"{i}_semaines"))
        # Configuration des largeurs de colonnes
        self.tree.column("id", width=50)
        self.tree.column("id_client", width=120)
        self.tree.column("localisation", width=120)
        self.tree.column("volet", width=80)
        self.tree.column("designation_equipement", width=200)
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
        
        # Troisième ligne: Désignation et Total
        ttk.Label(info_frame, text="Désignation Équipement:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(info_frame, textvariable=self.designation_equipement_var, width=30).grid(row=2, column=1, padx=5, pady=5, sticky="w", columnspan=3)
        
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
            # Vérifier s'il s'agit d'un ajout ou d'une modification
            if self.id_var.get() == 0:  # Ajout
                transfert = self.TransfererEquipement(
                    volet=self.volet_var.get() or None,
                    designation_equipement=self.designation_equipement_var.get(),
                    modalite_transport=self.modalite_transport_var.get() or None,
                    total_equipements=self.total_equipements_var.get(),
                    id_client=self.id_client_var.get(),
                    douze_semaines_avant=self.semaines_vars['douze'].get() or None,
                    onze_semaines_avant=self.semaines_vars['onze'].get() or None,
                    dix_semaines_avant=self.semaines_vars['dix'].get() or None,
                    neuf_semaines_avant=self.semaines_vars['neuf'].get() or None,
                    huit_semaines_avant=self.semaines_vars['huit'].get() or None,
                    sept_semaines_avant=self.semaines_vars['sept'].get() or None,
                    six_semaines_avant=self.semaines_vars['six'].get() or None,
                    cinq_semaines_avant=self.semaines_vars['cinq'].get() or None,
                    quatre_semaines_avant=self.semaines_vars['quatre'].get() or None,
                    trois_semaines_avant=self.semaines_vars['trois'].get() or None,
                    deux_semaines_avant=self.semaines_vars['deux'].get() or None,
                    un_semaines_avant=self.semaines_vars['un'].get() or None,
                    zero_semaines_avant=self.semaines_vars['zero'].get() or None
                )
                session.add(transfert)
                message_succes = "Transfert d'équipement ajouté avec succès"
            else:  # Modification
                transfert = session.query(self.TransfererEquipement).filter_by(id=self.id_var.get()).first()
                if transfert:
                    transfert.volet = self.volet_var.get() or None
                    transfert.designation_equipement = self.designation_equipement_var.get()
                    transfert.modalite_transport = self.modalite_transport_var.get() or None
                    transfert.total_equipements = self.total_equipements_var.get()
                    transfert.id_client = self.id_client_var.get()
                    transfert.douze_semaines_avant = self.semaines_vars['douze'].get() or None
                    transfert.onze_semaines_avant = self.semaines_vars['onze'].get() or None
                    transfert.dix_semaines_avant = self.semaines_vars['dix'].get() or None
                    transfert.neuf_semaines_avant = self.semaines_vars['neuf'].get() or None
                    transfert.huit_semaines_avant = self.semaines_vars['huit'].get() or None
                    transfert.sept_semaines_avant = self.semaines_vars['sept'].get() or None
                    transfert.six_semaines_avant = self.semaines_vars['six'].get() or None
                    transfert.cinq_semaines_avant = self.semaines_vars['cinq'].get() or None
                    transfert.quatre_semaines_avant = self.semaines_vars['quatre'].get() or None
                    transfert.trois_semaines_avant = self.semaines_vars['trois'].get() or None
                    transfert.deux_semaines_avant = self.semaines_vars['deux'].get() or None
                    transfert.un_semaines_avant = self.semaines_vars['un'].get() or None
                    transfert.zero_semaines_avant = self.semaines_vars['zero'].get() or None
                message_succes = "Transfert d'équipement modifié avec succès"
            
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
            transfert = session.query(self.TransfererEquipement).filter_by(id=item_id).first()
            if transfert:
                # Remplir le formulaire avec les données
                self.id_var.set(transfert.id)
                self.id_client_var.set(transfert.id_client)
                self.volet_var.set(transfert.volet or "")
                self.designation_equipement_var.set(transfert.designation_equipement)
                self.modalite_transport_var.set(transfert.modalite_transport or "")
                self.total_equipements_var.set(transfert.total_equipements)
                
                # Mise à jour des variables pour les semaines
                self.semaines_vars['douze'].set(transfert.douze_semaines_avant or 0)
                self.semaines_vars['onze'].set(transfert.onze_semaines_avant or 0)
                self.semaines_vars['dix'].set(transfert.dix_semaines_avant or 0)
                self.semaines_vars['neuf'].set(transfert.neuf_semaines_avant or 0)
                self.semaines_vars['huit'].set(transfert.huit_semaines_avant or 0)
                self.semaines_vars['sept'].set(transfert.sept_semaines_avant or 0)
                self.semaines_vars['six'].set(transfert.six_semaines_avant or 0)
                self.semaines_vars['cinq'].set(transfert.cinq_semaines_avant or 0)
                self.semaines_vars['quatre'].set(transfert.quatre_semaines_avant or 0)
                self.semaines_vars['trois'].set(transfert.trois_semaines_avant or 0)
                self.semaines_vars['deux'].set(transfert.deux_semaines_avant or 0)
                self.semaines_vars['un'].set(transfert.un_semaines_avant or 0)
                self.semaines_vars['zero'].set(transfert.zero_semaines_avant or 0)
                
                # Mise à jour de la localisation
                self.actualiser_localisation_client()
                
                # Basculer vers l'onglet formulaire
                self.basculer_vers_formulaire()
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
            # Préparer la requête avec jointure pour obtenir les informations du chantier
            query = session.query(
                self.TransfererEquipement, 
                self.Chantier.localisation
            ).join(
                self.Chantier, 
                self.TransfererEquipement.id_client == self.Chantier.id_client, 
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
                        self.TransfererEquipement.designation_equipement.like(recherche),
                        self.TransfererEquipement.modalite_transport.like(recherche),
                        self.Chantier.localisation.like(recherche)
                    )
                )
            
            # Exécuter la requête
            resultats = query.all()
            
            # Remplir le tableau
            for transfert, localisation in resultats:
                self.tree.insert("", "end", values=(
                    transfert.id, 
                    transfert.id_client,
                    localisation or "Non spécifiée",
                    transfert.volet or "-",
                    transfert.designation_equipement,
                    transfert.modalite_transport or "-",
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
                ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données: {str(e)}")
            print(f"Erreur lors du chargement des données: {str(e)}")

    def vider_formulaire(self):
        """Réinitialise les champs du formulaire"""
        self.id_var.set(0)
        self.id_client_var.set("")
        self.localisation_client_var.set("")
        self.volet_var.set("")
        self.designation_equipement_var.set("")
        self.modalite_transport_var.set("")
        self.total_equipements_var.set(1)  # Valeur par défaut à 1
        
        # Réinitialisation des semaines
        for semaine in self.semaines_vars:
            self.semaines_vars[semaine].set(0)

    def validation_formulaire(self):
        """Valide les champs du formulaire avant ajout/modification"""
        # Vérifier que les champs obligatoires sont remplis
        if not self.designation_equipement_var.get():
            messagebox.showerror("Erreur", "La désignation de l'équipement est obligatoire")
            return False
            
        if not self.id_client_var.get():
            messagebox.showerror("Erreur", "Le client est obligatoire")
            return False
            
        # Vérifier que les valeurs numériques sont valides
        try:
            if self.total_equipements_var.get() <= 0:
                messagebox.showerror("Erreur", "Le total des équipements doit être supérieur à 0")
                return False
        except:
            messagebox.showerror("Erreur", "Le total des équipements doit être un nombre valide")
            return False
            
        # Vérifier que les valeurs des semaines sont valides
        for semaine, var in self.semaines_vars.items():
            try:
                if var.get() < 0:
                    messagebox.showerror("Erreur", f"La valeur pour {semaine} semaines doit être positive ou nulle")
                    return False
            except:
                messagebox.showerror("Erreur", f"La valeur pour {semaine} semaines doit être un nombre valide")
                return False
            
        return True

    def appliquer_filtre(self):
        """Applique le filtre client sélectionné"""
        self.charger_donnees()

    def reinitialiser_filtre(self):
        """Réinitialise le filtre client"""
        self.filtre_client_var.set("Tous")
        self.recherche_var.set("")
        self.charger_donnees()
        
    def rechercher(self):
        """Effectue une recherche dans les données"""
        self.charger_donnees()
        
    def trier_tableau(self, colonne):
        """Trie le tableau selon la colonne spécifiée"""
        # Récupérer toutes les lignes avec leurs valeurs
        data = [(self.tree.set(child, colonne), child) for child in self.tree.get_children('')]
        
        # Déterminer l'ordre de tri (croissant par défaut)
        # Si la colonne est numérique, convertir en entier pour le tri
        if colonne in ["id", "total_equipements"] or "_semaines" in colonne:
            # Pour les colonnes numériques
            try:
                # Vérifier si nous trions déjà par cette colonne
                last_sort = getattr(self, "_last_sort", None)
                if last_sort == (colonne, "asc"):
                    # Inverser l'ordre
                    data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=True)
                    self._last_sort = (colonne, "desc")
                else:
                    # Tri croissant
                    data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0)
                    self._last_sort = (colonne, "asc")
            except ValueError:
                # En cas d'erreur, tri en tant que chaîne
                data.sort(reverse=(getattr(self, "_last_sort", None) == (colonne, "asc")))
                self._last_sort = (colonne, "desc" if getattr(self, "_last_sort", None) == (colonne, "asc") else "asc")
        else:
            # Pour les colonnes de texte
            last_sort = getattr(self, "_last_sort", None)
            if last_sort == (colonne, "asc"):
                data.sort(reverse=True)
                self._last_sort = (colonne, "desc")
            else:
                data.sort()
                self._last_sort = (colonne, "asc")
                
        # Réorganiser les éléments dans l'ordre trié
        for index, (val, item) in enumerate(data):
            self.tree.move(item, '', index)
    
    def exporter_donnees(self):
        """Exporte les données actuelles vers un fichier CSV"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            title="Exporter les données"
        )
        
        if not filename:
            return
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Écrire les en-têtes
                headers = []
                for col in self.tree["columns"]:
                    headers.append(self.tree.heading(col)["text"])
                writer.writerow(headers)
                
                # Écrire les données
                for item_id in self.tree.get_children():
                    values = self.tree.item(item_id, "values")
                    writer.writerow(values)
                    
            messagebox.showinfo("Succès", f"Données exportées avec succès vers {filename}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation: {str(e)}")
    
    def importer_donnees(self):
        """Importe des données depuis un fichier CSV"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.askopenfilename(
            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
            title="Importer des données"
        )
        
        if not filename:
            return
            
        try:
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                
                # Sauter l'en-tête
                next(reader)
                
                # Pour chaque ligne, ajouter un nouvel enregistrement
                for row in reader:
                    if len(row) < 7:  # Vérifier qu'il y a au moins les colonnes essentielles
                        continue
                        
                    # Créer un nouveau transfert
                    transfert = self.TransfererEquipement(
                        id_client=row[1],
                        volet=row[3] if row[3] != "-" else None,
                        designation_equipement=row[4],
                        modalite_transport=row[5] if row[5] != "-" else None,
                        total_equipements=int(row[6]) if row[6].isdigit() else 0
                    )
                    
                    # Ajouter les semaines si disponibles
                    if len(row) > 7:
                        transfert.douze_semaines_avant = int(row[7]) if row[7].isdigit() else None
                    if len(row) > 8:
                        transfert.onze_semaines_avant = int(row[8]) if row[8].isdigit() else None
                    if len(row) > 9:
                        transfert.dix_semaines_avant = int(row[9]) if row[9].isdigit() else None
                    if len(row) > 10:
                        transfert.neuf_semaines_avant = int(row[10]) if row[10].isdigit() else None
                    if len(row) > 11:
                        transfert.huit_semaines_avant = int(row[11]) if row[11].isdigit() else None
                    if len(row) > 12:
                        transfert.sept_semaines_avant = int(row[12]) if row[12].isdigit() else None
                    if len(row) > 13:
                        transfert.six_semaines_avant = int(row[13]) if row[13].isdigit() else None
                    if len(row) > 14:
                        transfert.cinq_semaines_avant = int(row[14]) if row[14].isdigit() else None
                    if len(row) > 15:
                        transfert.quatre_semaines_avant = int(row[15]) if row[15].isdigit() else None
                    if len(row) > 16:
                        transfert.trois_semaines_avant = int(row[16]) if row[16].isdigit() else None
                    if len(row) > 17:
                        transfert.deux_semaines_avant = int(row[17]) if row[17].isdigit() else None
                    if len(row) > 18:
                        transfert.un_semaines_avant = int(row[18]) if row[18].isdigit() else None
                    if len(row) > 19:
                        transfert.zero_semaines_avant = int(row[19]) if row[19].isdigit() else None
                    
                    # Ajouter à la session
                    session.add(transfert)
                
                # Committer toutes les modifications
                session.commit()
                messagebox.showinfo("Succès", "Données importées avec succès")
                self.charger_donnees()
        except Exception as e:
            session.rollback()
            messagebox.showerror("Erreur", f"Erreur lors de l'importation: {str(e)}")
            
    def generer_rapport(self):
        """Génère un rapport PDF des transferts d'équipements"""
        try:
            
            
            # Demander où enregistrer le fichier
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")],
                title="Enregistrer le rapport"
            )
            
            if not filename:
                return
                
            # Créer le document
            doc = SimpleDocTemplate(filename, pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            elements = []
            
            # Titre
            title_style = styles["Heading1"]
            title_style.alignment = 1  # Centre
            elements.append(Paragraph("Rapport des Transferts d'Équipements", title_style))
            elements.append(Spacer(1, 20))
            
            # Sous-titre avec date
            date_str = datetime.datetime.now().strftime("%d/%m/%Y à %H:%M")
            subtitle_style = styles["Heading3"]
            subtitle_style.alignment = 1  # Centre
            elements.append(Paragraph(f"Généré le {date_str}", subtitle_style))
            elements.append(Spacer(1, 20))
            
            # Filtres appliqués
            if self.filtre_client_var.get() != "Tous":
                elements.append(Paragraph(f"Filtre par client: {self.filtre_client_var.get()}", styles["Normal"]))
                elements.append(Spacer(1, 10))
            
            if self.recherche_var.get():
                elements.append(Paragraph(f"Recherche: {self.recherche_var.get()}", styles["Normal"]))
                elements.append(Spacer(1, 10))
            
            # Préparation des données
            data = []
            
            # En-têtes du tableau
            headers = ["ID", "Client", "Volet", "Désignation", "Transport", "Total"]
            for i in range(12, -1, -1):
                headers.append(f"{i} sem.")
            data.append(headers)
            
            # Contenu du tableau
            for item in self.tree.get_children():
                values = list(self.tree.item(item, "values"))
                # Supprimer la colonne "localisation" pour le PDF
                values.pop(2)
                data.append(values)
            
            # Création du tableau
            table = Table(data)
            
            # Style du tableau
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (5, 1), (-1, -1), 'CENTER'),  # Centrer les colonnes numériques
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ])
            
            # Alternance de couleurs pour les lignes
            for i in range(1, len(data)):
                if i % 2 == 0:
                    table_style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
            
            table.setStyle(table_style)
            elements.append(table)
            
            # Générer le PDF
            doc.build(elements)
            
            messagebox.showinfo("Succès", f"Rapport généré avec succès: {filename}")
            
            # Ouvrir le fichier PDF
            import os, subprocess
            if os.name == 'nt':  # Windows
                os.startfile(filename)
            elif os.name == 'posix':  # macOS et Linux
                subprocess.run(['xdg-open', filename])
        except ImportError:
            messagebox.showerror("Erreur", "Le module ReportLab est nécessaire pour cette fonction. Installez-le avec 'pip install reportlab'.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la génération du rapport: {str(e)}")


def main():
    """Point d'entrée principal"""
    try:
        # Créer une fenêtre avec le thème darkly
        root = ttk.Window(themename="darkly")
        
        # Ajouter le menu principal
        menu_bar = ttk.Menu(root)
        root.config(menu=menu_bar)
        
        # Menu Fichier
        file_menu = ttk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Fichier", menu=file_menu)
        
        # Création de l'application et ajout des options de menu
        app = TransfererEquipementApp(root)
        
        file_menu.add_command(label="Exporter les données", command=app.exporter_donnees)
        file_menu.add_command(label="Importer des données", command=app.importer_donnees)
        file_menu.add_separator()
        file_menu.add_command(label="Générer un rapport", command=app.generer_rapport)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=root.quit)
        
        # Définir la taille minimale de la fenêtre
        root.update()
        root.minsize(root.winfo_width(), root.winfo_height())
        
        # Démarrer l'application
        root.mainloop()
    finally:
        # Fermer la session SQLAlchemy à la fin
        if session:
            session.close()


if __name__ == "__main__":
    main()