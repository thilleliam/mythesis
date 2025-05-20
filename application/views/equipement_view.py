import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar, IntVar, DoubleVar, filedialog
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime
import csv
import pandas as pd
from tkinter import ttk as tk_ttk

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class EquipementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Équipements")
        self.root.geometry("950x650")  # Dimensions agrandies pour plus d'espace
        photo = ttk.PhotoImage(file="C:\\Users\\BIG-computer\\Pictures\\Logo1.png")
        root.iconphoto(False, photo)
        
        # Import local pour éviter les imports circulaires
        from application.models.equipements import Equipement
        self.Equipement = Equipement

        # Variables
        self.id_var = IntVar()
        self.quantite_var = IntVar()
        self.nom_var = StringVar()
        self.type_var = StringVar()
        self.etat_var = StringVar(value="bon")
        self.poids_var = DoubleVar()
        self.volume_var = DoubleVar()
        self.recherche_var = StringVar()
        
        # Création de l'interface avec un notebook pour séparer les fonctionnalités
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Onglet principal pour la gestion des équipements
        self.tab_main = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_main, text="Gestion des Équipements")
        
        # Onglet pour les statistiques et rapports
        self.tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stats, text="Statistiques & Rapports")
        
        # Construction de l'interface principale
        self.setup_main_tab()
        
        # Construction de l'interface des statistiques
        self.setup_stats_tab()

    def setup_main_tab(self):
        # Panneau de recherche
        search_frame = ttk.Frame(self.tab_main, padding=10)
        search_frame.pack(fill=X)
        
        ttk.Label(search_frame, text="Rechercher:", font=("TkDefaultFont", 10, "bold")).pack(side=LEFT, padx=5)
        ttk.Entry(search_frame, textvariable=self.recherche_var, width=40).pack(side=LEFT, padx=5)
        ttk.Button(
            search_frame, 
            text="Rechercher", 
            command=self.rechercher, 
            bootstyle="info"
        ).pack(side=LEFT, padx=5)
        ttk.Button(
            search_frame, 
            text="Réinitialiser", 
            command=self.charger_donnees, 
            bootstyle="secondary"
        ).pack(side=LEFT, padx=5)
        
        # Formulaire dans une frame avec style
        form_frame = ttk.LabelFrame(self.tab_main, text="Détails de l'équipement", padding=15)
        form_frame.pack(fill=X, pady=10, padx=10)
        
        # Grille pour le formulaire - première ligne
        ttk.Label(form_frame, text="ID:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        id_entry = ttk.Entry(form_frame, textvariable=self.id_var, state=DISABLED, width=10)
        id_entry.grid(row=0, column=1, padx=5, pady=5, sticky=W)
        
        ttk.Label(form_frame, text="Nom:").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        ttk.Entry(form_frame, textvariable=self.nom_var, width=25).grid(row=0, column=3, padx=5, pady=5, sticky=W)
        
        ttk.Label(form_frame, text="Type:").grid(row=0, column=4, padx=5, pady=5, sticky=W)
        ttk.Entry(form_frame, textvariable=self.type_var, width=25).grid(row=0, column=5, padx=5, pady=5, sticky=W)
        
        # Deuxième ligne
        ttk.Label(form_frame, text="Quantité:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        ttk.Spinbox(form_frame, textvariable=self.quantite_var, from_=0, to=1000, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=W)
        
        ttk.Label(form_frame, text="État:").grid(row=1, column=2, padx=5, pady=5, sticky=W)
        self.etat_cb = ttk.Combobox(
            form_frame, 
            textvariable=self.etat_var, 
            values=["bon", "endommagé", "en maintenance", "hors service"], 
            state="readonly", 
            width=15
        )
        self.etat_cb.grid(row=1, column=3, padx=5, pady=5, sticky=W)
        
        # Troisième ligne - nouvelles colonnes
        ttk.Label(form_frame, text="Poids (kg):").grid(row=2, column=0, padx=5, pady=5, sticky=W)
        ttk.Spinbox(
            form_frame, 
            textvariable=self.poids_var, 
            from_=0.0, 
            to=10000.0, 
            increment=0.1, 
            width=10
        ).grid(row=2, column=1, padx=5, pady=5, sticky=W)
        
        ttk.Label(form_frame, text="Volume (m³):").grid(row=2, column=2, padx=5, pady=5, sticky=W)
        ttk.Spinbox(
            form_frame, 
            textvariable=self.volume_var, 
            from_=0.0, 
            to=1000.0, 
            increment=0.01, 
            width=10
        ).grid(row=2, column=3, padx=5, pady=5, sticky=W)
        
        # Boutons d'action
        btn_frame = ttk.Frame(self.tab_main, padding=10)
        btn_frame.pack(fill=X)
        
        # CRUD buttons
        ttk.Button(
            btn_frame, 
            text="Ajouter", 
            command=self.ajouter, 
            bootstyle="success",
            width=12
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Modifier", 
            command=self.modifier, 
            bootstyle="warning",
            width=12
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Supprimer", 
            command=self.supprimer, 
            bootstyle="danger",
            width=12
        ).pack(side=LEFT, padx=5)
        
        # Fonctionnalités supplémentaires
        ttk.Button(
            btn_frame, 
            text="Voir Commandes", 
            command=self.afficher_commandes, 
            bootstyle="info",
            width=15
        ).pack(side=LEFT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Vider Formulaire", 
            command=self.vider_formulaire, 
            bootstyle="secondary",
            width=15
        ).pack(side=LEFT, padx=5)

        # Boutons d'import/export
        exp_frame = ttk.Frame(self.tab_main, padding=10)
        exp_frame.pack(fill=X)
        
        ttk.Button(
            exp_frame, 
            text="Exporter CSV", 
            command=self.exporter_csv, 
            bootstyle="outline-primary",
            width=15
        ).pack(side=RIGHT, padx=5)
        
        ttk.Button(
            exp_frame, 
            text="Importer CSV", 
            command=self.importer_csv, 
            bootstyle="outline-primary",
            width=15
        ).pack(side=RIGHT, padx=5)
        
        # Tableau avec scrollbar
        tree_frame = ttk.Frame(self.tab_main)
        tree_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Ajout de scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame)
        y_scrollbar.pack(side=RIGHT, fill=Y)
        
        x_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal')
        x_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Tableau amélioré
        self.tree = ttk.Treeview(
            tree_frame, 
            columns=("id", "nom", "quantite", "type", "etat", "poids", "volume"), 
            show="headings",
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        self.tree.pack(fill=BOTH, expand=True)
        
        # Configurer scrollbars
        y_scrollbar.config(command=self.tree.yview)
        x_scrollbar.config(command=self.tree.xview)
        
        # En-têtes du tableau
        self.tree.heading("id", text="ID")
        self.tree.heading("nom", text="Nom Équipement")
        self.tree.heading("quantite", text="Quantité")
        self.tree.heading("type", text="Type")
        self.tree.heading("etat", text="État")
        self.tree.heading("poids", text="Poids (kg)")
        self.tree.heading("volume", text="Volume (m³)")
        
        # Taille des colonnes
        self.tree.column("id", width=50, anchor=CENTER)
        self.tree.column("nom", width=180, anchor=W)
        self.tree.column("quantite", width=80, anchor=CENTER)
        self.tree.column("type", width=150, anchor=W)
        self.tree.column("etat", width=120, anchor=CENTER)
        self.tree.column("poids", width=100, anchor=CENTER)
        self.tree.column("volume", width=100, anchor=CENTER)
        
        # Ajouter un style de bandes alternées
        self.tree.tag_configure('oddrow', background='#2a2a2a')
        self.tree.tag_configure('evenrow', background='#323232')
        
        # Lier l'événement de sélection
        self.tree.bind("<ButtonRelease-1>", self.selectionner)
        
        # Barre de statut
        self.status_var = StringVar()
        self.status_var.set("Prêt")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor=W, padding=5)
        status_bar.pack(side=BOTTOM, fill=X)
        
        # Charger les données
        self.charger_donnees()

    def setup_stats_tab(self):
        """Configure l'onglet des statistiques"""
        stats_frame = ttk.Frame(self.tab_stats, padding=15)
        stats_frame.pack(fill=BOTH, expand=True)
        
        # Titre
        ttk.Label(
            stats_frame, 
            text="Statistiques des Équipements", 
            font=("TkDefaultFont", 14, "bold")
        ).pack(pady=10)
        
        # Cadres pour les statistiques
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(fill=X, pady=10)
        
        # Statistiques générales
        general_stats = ttk.LabelFrame(stats_container, text="Statistiques Générales", padding=10)
        general_stats.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        self.total_equipements_var = StringVar(value="0")
        self.total_quantite_var = StringVar(value="0")
        self.total_poids_var = StringVar(value="0.0 kg")
        self.total_volume_var = StringVar(value="0.0 m³")
        
        ttk.Label(general_stats, text="Nombre total d'équipements:").grid(row=0, column=0, sticky=W, pady=5)
        ttk.Label(general_stats, textvariable=self.total_equipements_var, font=("TkDefaultFont", 10, "bold")).grid(row=0, column=1, sticky=W, pady=5)
        
        ttk.Label(general_stats, text="Quantité totale en stock:").grid(row=1, column=0, sticky=W, pady=5)
        ttk.Label(general_stats, textvariable=self.total_quantite_var, font=("TkDefaultFont", 10, "bold")).grid(row=1, column=1, sticky=W, pady=5)
        
        ttk.Label(general_stats, text="Poids total des équipements:").grid(row=2, column=0, sticky=W, pady=5)
        ttk.Label(general_stats, textvariable=self.total_poids_var, font=("TkDefaultFont", 10, "bold")).grid(row=2, column=1, sticky=W, pady=5)
        
        ttk.Label(general_stats, text="Volume total des équipements:").grid(row=3, column=0, sticky=W, pady=5)
        ttk.Label(general_stats, textvariable=self.total_volume_var, font=("TkDefaultFont", 10, "bold")).grid(row=3, column=1, sticky=W, pady=5)
        
        # Statistiques par état
        etat_stats = ttk.LabelFrame(stats_container, text="Équipements par État", padding=10)
        etat_stats.pack(side=RIGHT, fill=BOTH, expand=True, padx=5)
        
        self.etat_tree = ttk.Treeview(
            etat_stats, 
            columns=("etat", "nombre", "pourcentage"), 
            show="headings",
            height=5
        )
        self.etat_tree.pack(fill=BOTH, expand=True, pady=5)
        
        self.etat_tree.heading("etat", text="État")
        self.etat_tree.heading("nombre", text="Nombre")
        self.etat_tree.heading("pourcentage", text="Pourcentage")
        
        self.etat_tree.column("etat", anchor=W, width=120)
        self.etat_tree.column("nombre", anchor=CENTER, width=80)
        self.etat_tree.column("pourcentage", anchor=CENTER, width=100)
        
        # Bouton de rafraîchissement des statistiques
        ttk.Button(
            stats_frame, 
            text="Rafraîchir les Statistiques", 
            command=self.calculer_statistiques,
            bootstyle="info"
        ).pack(pady=10)
        
        # Rapport des équipements qui nécessitent un entretien ou remplacement
        maintenance_frame = ttk.LabelFrame(stats_frame, text="Équipements Nécessitant Attention", padding=10)
        maintenance_frame.pack(fill=BOTH, expand=True, pady=10)
        
        self.maintenance_tree = ttk.Treeview(
            maintenance_frame, 
            columns=("id", "nom", "etat", "quantite"), 
            show="headings",
            height=6
        )
        self.maintenance_tree.pack(fill=BOTH, expand=True)
        
        self.maintenance_tree.heading("id", text="ID")
        self.maintenance_tree.heading("nom", text="Nom Équipement")
        self.maintenance_tree.heading("etat", text="État")
        self.maintenance_tree.heading("quantite", text="Quantité")
        
        self.maintenance_tree.column("id", width=50, anchor=CENTER)
        self.maintenance_tree.column("nom", width=250, anchor=W)
        self.maintenance_tree.column("etat", width=150, anchor=CENTER)
        self.maintenance_tree.column("quantite", width=100, anchor=CENTER)
        
        # Calculer les statistiques initiales
        self.calculer_statistiques()

    def ajouter(self):
        """Ajouter un nouvel équipement"""
        if not self.valider_formulaire():
            return
            
        try:
            equipement = self.Equipement(
                nomEquipement=self.nom_var.get(),
                quantite=self.quantite_var.get(),
                typeEquipement=self.type_var.get(),
                etat=self.etat_var.get(),
                poids=self.poids_var.get(),
                volume=self.volume_var.get()
            )
            session.add(equipement)
            session.commit()
            self.charger_donnees()
            self.vider_formulaire()
            self.calculer_statistiques()
            self.status_var.set(f"Équipement '{self.nom_var.get()}' ajouté avec succès")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout: {str(e)}")
            session.rollback()

    def modifier(self):
        """Modifier un équipement existant"""
        if not self.valider_formulaire():
            return
            
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un équipement à modifier")
            return
            
        id_equipement = self.tree.item(item, "values")[0]
        try:
            equipement = session.query(self.Equipement).filter_by(ID_equipement=id_equipement).first()
            if equipement:
                equipement.nomEquipement = self.nom_var.get()
                equipement.quantite = self.quantite_var.get()
                equipement.typeEquipement = self.type_var.get()
                equipement.etat = self.etat_var.get()
                equipement.poids = self.poids_var.get()
                equipement.volume = self.volume_var.get()
                session.commit()
                self.charger_donnees()
                self.calculer_statistiques()
                self.status_var.set(f"Équipement ID:{id_equipement} modifié avec succès")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la modification: {str(e)}")
            session.rollback()

    def supprimer(self):
        """Supprimer un équipement"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un équipement à supprimer")
            return
            
        id_equipement = self.tree.item(item, "values")[0]
        confirmation = messagebox.askyesno(
            "Confirmation", 
            f"Êtes-vous sûr de vouloir supprimer l'équipement ID:{id_equipement}?"
        )
        
        if confirmation:
            try:
                session.query(self.Equipement).filter_by(ID_equipement=id_equipement).delete()
                session.commit()
                self.charger_donnees()
                self.vider_formulaire()
                self.calculer_statistiques()
                self.status_var.set(f"Équipement ID:{id_equipement} supprimé avec succès")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {str(e)}")
                session.rollback()

    def selectionner(self, event):
        """Sélectionner un équipement dans le tableau"""
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            self.id_var.set(values[0])
            self.nom_var.set(values[1])
            self.quantite_var.set(values[2])
            self.type_var.set(values[3])
            self.etat_var.set(values[4])
            
            # Nouvelles colonnes
            self.poids_var.set(float(values[5]) if values[5] != "N/A" else 0.0)
            self.volume_var.set(float(values[6]) if values[6] != "N/A" else 0.0)

    def charger_donnees(self):
        """Charger les données depuis la base de données"""
        self.tree.delete(*self.tree.get_children())
        try:
            count = 0
            for equipement in session.query(self.Equipement).all():
                # Alternance des couleurs de ligne
                tag = 'evenrow' if count % 2 == 0 else 'oddrow'
                
                self.tree.insert(
                    "", 
                    END, 
                    values=(
                        equipement.ID_equipement, 
                        equipement.nomEquipement, 
                        equipement.quantite,
                        equipement.typeEquipement, 
                        equipement.etat,
                        f"{equipement.poids:.2f}" if equipement.poids is not None else "N/A",
                        f"{equipement.volume:.2f}" if equipement.volume is not None else "N/A"
                    ),
                    tags=(tag,)
                )
                count += 1
                
            self.status_var.set(f"{count} équipements chargés")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données: {str(e)}")

    def vider_formulaire(self):
        """Vider le formulaire"""
        self.id_var.set(0)
        self.nom_var.set("")
        self.quantite_var.set(0)
        self.type_var.set("")
        self.etat_var.set("bon")
        self.poids_var.set(0.0)
        self.volume_var.set(0.0)
        
        # Désélectionner dans le tableau
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def afficher_commandes(self):
        """Afficher les commandes liées à un équipement"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un équipement pour afficher ses commandes")
            return
            
        id_equipement = self.tree.item(item, "values")[0]
        self.afficher_details_commandes(id_equipement)
    
    def afficher_details_commandes(self, id_equipement):
        """Afficher les détails des commandes pour un équipement"""
        from application.models.commandeequipement import CommandeEquipement
        from application.database import SessionLocal
        session = SessionLocal()
        
        try:
            commandes = session.query(CommandeEquipement).filter(CommandeEquipement.ID_equipement == id_equipement).all()
            
            if not commandes:
                messagebox.showinfo("Commandes", "Aucune commande pour cet équipement.")
                return
                
            # Créer une nouvelle fenêtre pour afficher les détails
            details_window = ttk.Toplevel(self.root)
            details_window.title(f"Détails des Commandes - Équipement ID:{id_equipement}")
            details_window.geometry("700x500")
            
            # Informations de l'équipement
            info_frame = ttk.Frame(details_window, padding=10)
            info_frame.pack(fill=X)
            
            equipement = session.query(self.Equipement).filter_by(ID_equipement=id_equipement).first()
            info_text = f"Équipement: {equipement.nomEquipement} (ID: {equipement.ID_equipement}, Type: {equipement.typeEquipement})"
            ttk.Label(info_frame, text=info_text, font=("TkDefaultFont", 11, "bold")).pack(anchor=W)
            
            # Frame pour le tableau des commandes
            tree_frame = ttk.Frame(details_window, padding=10)
            tree_frame.pack(fill=BOTH, expand=True)
            
            # Scrollbars
            y_scrollbar = ttk.Scrollbar(tree_frame)
            y_scrollbar.pack(side=RIGHT, fill=Y)
            
            # Créer un Treeview pour afficher les commandes
            details_tree = ttk.Treeview(
                tree_frame, 
                columns=("id", "date", "quantite", "statut", "details"), 
                show="headings",
                yscrollcommand=y_scrollbar.set
            )
            details_tree.pack(fill=BOTH, expand=True)
            
            y_scrollbar.config(command=details_tree.yview)
            
            details_tree.heading("id", text="ID Commande")
            details_tree.heading("date", text="Date Commande")
            details_tree.heading("quantite", text="Quantité")
            details_tree.heading("statut", text="Statut")
            details_tree.heading("details", text="Détails")
            
            details_tree.column("id", width=80, anchor=CENTER)
            details_tree.column("date", width=120, anchor=CENTER)
            details_tree.column("quantite", width=80, anchor=CENTER)
            details_tree.column("statut", width=120, anchor=CENTER)
            details_tree.column("details", width=250, anchor=W)
            
            # Remplir le Treeview avec les données des commandes
            for i, commande in enumerate(commandes):
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
                details_tree.insert(
                    "", 
                    END, 
                    values=(
                        commande.id_commande,
                        commande.date_commande.strftime("%d/%m/%Y") if commande.date_commande else "N/A",
                        commande.quantite,
                        commande.statut,
                        commande.details if hasattr(commande, 'details') else "N/A"
                    ),
                    tags=(tag,)
                )
            
            details_tree.tag_configure('oddrow', background='#2a2a2a')
            details_tree.tag_configure('evenrow', background='#323232')
            
            # Boutons d'action
            button_frame = ttk.Frame(details_window, padding=10)
            button_frame.pack(fill=X, pady=5)
            
            ttk.Button(
                button_frame, 
                text="Exporter en CSV", 
                command=lambda: self.exporter_commandes_csv(commandes, id_equipement),
                bootstyle="outline-primary"
            ).pack(side=LEFT, padx=5)
            
            ttk.Button(
                button_frame, 
                text="Fermer", 
                command=details_window.destroy, 
                bootstyle="secondary"
            ).pack(side=RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage des commandes: {str(e)}")
            
    def rechercher(self):
        """Rechercher des équipements"""
        terme = self.recherche_var.get().strip().lower()
        if not terme:
            self.charger_donnees()
            return
            
        self.tree.delete(*self.tree.get_children())
        try:
            count = 0
            for equipement in session.query(self.Equipement).all():
                if (terme in str(equipement.ID_equipement).lower() or
                    terme in equipement.nomEquipement.lower() or
                    terme in equipement.typeEquipement.lower() or
                    terme in equipement.etat.lower()):
                    
                    tag = 'evenrow' if count % 2 == 0 else 'oddrow'
                    self.tree.insert(
                        "", 
                        END, 
                        values=(
                            equipement.ID_equipement, 
                            equipement.nomEquipement, 
                            equipement.quantite,
                            equipement.typeEquipement, 
                            equipement.etat,
                            f"{equipement.poids:.2f}" if equipement.poids is not None else "N/A",
                            f"{equipement.volume:.2f}" if equipement.volume is not None else "N/A"
                        ),
                        tags=(tag,)
                    )
                    count += 1
                    
            self.status_var.set(f"{count} équipements trouvés pour '{terme}'")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la recherche: {str(e)}")
    
    def calculer_statistiques(self):
        """Calculer et afficher les statistiques"""
        try:
            # Statistiques générales
            total_equipements = session.query(func.count(self.Equipement.ID_equipement)).scalar() or 0
            total_quantite = session.query(func.sum(self.Equipement.quantite)).scalar() or 0
            total_poids = session.query(func.sum(self.Equipement.poids)).scalar() or 0
            total_volume = session.query(func.sum(self.Equipement.volume)).scalar() or 0
            
            self.total_equipements_var.set(str(total_equipements))
            self.total_quantite_var.set(str(total_quantite))
            self.total_poids_var.set(f"{total_poids:.2f} kg")
            self.total_volume_var.set(f"{total_volume:.2f} m³")
            
            # Statistiques par état
            self.etat_tree.delete(*self.etat_tree.get_children())
            
            etats = ['bon', 'endommagé', 'en maintenance', 'hors service']
            for etat in etats:
                count = session.query(func.count(self.Equipement.ID_equipement)).filter(
                    self.Equipement.etat == etat
                ).scalar() or 0
                
                percentage = 0 if total_equipements == 0 else (count / total_equipements) * 100
                
                self.etat_tree.insert(
                    "", 
                    END, 
                    values=(etat, count, f"{percentage:.1f}%")
                )
            
            # Équipements nécessitant attention
            self.maintenance_tree.delete(*self.maintenance_tree.get_children())
            
            problematic = session.query(self.Equipement).filter(
                self.Equipement.etat.in_(['endommagé', 'en maintenance', 'hors service'])
            ).all()
            
            for equip in problematic:
                self.maintenance_tree.insert(
                    "", 
                    END, 
                    values=(
                        equip.ID_equipement,
                        equip.nomEquipement,
                        equip.etat,
                        equip.quantite
                    )
                )
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul des statistiques: {str(e)}")
            
    def exporter_csv(self):
        """Exporter les données vers un fichier CSV"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Exporter les équipements en CSV"
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # En-têtes
                writer.writerow(["ID", "Nom", "Quantité", "Type", "État", "Poids (kg)", "Volume (m³)"])
                
                # Données
                for item in self.tree.get_children():
                    values = self.tree.item(item, "values")
                    writer.writerow(values)
                    
            messagebox.showinfo("Exportation réussie", f"Les données ont été exportées vers {filepath}")
            self.status_var.set(f"Exportation réussie vers {filepath}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation: {str(e)}")
            
    def exporter_commandes_csv(self, commandes, id_equipement):
        """Exporter les commandes vers un fichier CSV"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title=f"Exporter les commandes de l'équipement {id_equipement}"
        )
        
        if not filepath:
            return
            
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # En-têtes
                writer.writerow(["ID Commande", "Date", "Quantité", "Statut", "Détails"])
                
                # Données
                for commande in commandes:
                    writer.writerow([
                        commande.id_commande,
                        commande.date_commande.strftime("%d/%m/%Y") if commande.date_commande else "N/A",
                        commande.quantite,
                        commande.statut,
                        commande.details if hasattr(commande, 'details') else "N/A"
                    ])
                    
            messagebox.showinfo("Exportation réussie", f"Les commandes ont été exportées vers {filepath}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation: {str(e)}")
            
    def importer_csv(self):
        """Importer des données depuis un fichier CSV"""
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="Importer des équipements depuis un CSV"
        )
        
        if not filepath:
            return
            
        try:
            success_count = 0
            error_count = 0
            
            df = pd.read_csv(filepath)
            for _, row in df.iterrows():
                try:
                    # Vérifier si l'ID existe déjà (mise à jour) ou s'il faut créer un nouvel enregistrement
                    if 'ID' in df.columns and not pd.isna(row['ID']):
                        equipement = session.query(self.Equipement).filter_by(ID_equipement=int(row['ID'])).first()
                        if equipement:
                            equipement.nomEquipement = row['Nom']
                            equipement.quantite = int(row['Quantité'])
                            equipement.typeEquipement = row['Type']
                            equipement.etat = row['État']
                            equipement.poids = float(row['Poids (kg)']) if 'Poids (kg)' in row and not pd.isna(row['Poids (kg)']) else 0.0
                            equipement.volume = float(row['Volume (m³)']) if 'Volume (m³)' in row and not pd.isna(row['Volume (m³)']) else 0.0
                        else:
                            equipement = self.Equipement(
                                nomEquipement=row['Nom'],
                                quantite=int(row['Quantité']),
                                typeEquipement=row['Type'],
                                etat=row['État'],
                                poids=float(row['Poids (kg)']) if 'Poids (kg)' in row and not pd.isna(row['Poids (kg)']) else 0.0,
                                volume=float(row['Volume (m³)']) if 'Volume (m³)' in row and not pd.isna(row['Volume (m³)']) else 0.0
                            )
                            session.add(equipement)
                    else:
                        equipement = self.Equipement(
                            nomEquipement=row['Nom'],
                            quantite=int(row['Quantité']),
                            typeEquipement=row['Type'],
                            etat=row['État'],
                            poids=float(row['Poids (kg)']) if 'Poids (kg)' in row and not pd.isna(row['Poids (kg)']) else 0.0,
                            volume=float(row['Volume (m³)']) if 'Volume (m³)' in row and not pd.isna(row['Volume (m³)']) else 0.0
                        )
                        session.add(equipement)
                        
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    continue
                    
            session.commit()
            self.charger_donnees()
            self.calculer_statistiques()
            messagebox.showinfo("Importation terminée", f"{success_count} équipements importés avec succès.\n{error_count} erreurs rencontrées.")
            self.status_var.set(f"Importation: {success_count} équipements ajoutés, {error_count} erreurs")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'importation: {str(e)}")
            session.rollback()
    
    def valider_formulaire(self):
        """Valider les données du formulaire"""
        if not self.nom_var.get().strip():
            messagebox.showwarning("Données invalides", "Le nom de l'équipement est obligatoire.")
            return False
            
        if not self.type_var.get().strip():
            messagebox.showwarning("Données invalides", "Le type d'équipement est obligatoire.")
            return False
            
        try:
            quantite = int(self.quantite_var.get())
            if quantite < 0:
                messagebox.showwarning("Données invalides", "La quantité doit être un nombre positif.")
                return False
        except ValueError:
            messagebox.showwarning("Données invalides", "La quantité doit être un nombre entier.")
            return False
            
        try:
            poids = float(self.poids_var.get())
            if poids < 0:
                messagebox.showwarning("Données invalides", "Le poids doit être un nombre positif.")
                return False
        except ValueError:
            messagebox.showwarning("Données invalides", "Le poids doit être un nombre décimal.")
            return False
            
        try:
            volume = float(self.volume_var.get())
            if volume < 0:
                messagebox.showwarning("Données invalides", "Le volume doit être un nombre positif.")
                return False
        except ValueError:
            messagebox.showwarning("Données invalides", "Le volume doit être un nombre décimal.")
            return False
            
        return True
if __name__ == "__main__":
    # Créer une fenêtre avec le thème darkly directement lors de l'initialisation
    root = ttk.Window(themename="cosmo")
    app = EquipementApp(root)
    root.mainloop()