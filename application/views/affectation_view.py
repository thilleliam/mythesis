import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from ttkbootstrap.tableview import Tableview
from ttkbootstrap.dialogs import Messagebox
import datetime
from datetime import datetime
from sqlalchemy import func

from application.database import SessionLocal
from application.models.affectation import Affectation
from application.models.conducteurs import Conducteur
from application.models.vehicule import Vehicule
from application.models.tournee import Tournee


class AffectationView(ttkb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.session = SessionLocal()
        
        # Configuration initiale
        self.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Titre principal
        title_frame = ttkb.Frame(self)
        title_frame.pack(fill=X, pady=10)
        style = ttk.Style()
        style.configure("Treeview", rowheight=25)  # Ajustez la hauteur des lignes ici
        title_label = ttkb.Label(
            title_frame, 
            text="GESTION DES AFFECTATIONS",
            font=("TkDefaultFont", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side=TOP, fill=X)
        
        # Conteneur principal
        main_container = ttkb.Frame(self)
        main_container.pack(fill=BOTH, expand=YES)
        
        # Panneau gauche: Formulaire
        self.form_frame = ttkb.LabelFrame(main_container, text="Formulaire d'affectation", bootstyle="primary")
        self.form_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=(0, 5), pady=5)
        
        # Panneau droit: Liste des affectations
        self.list_frame = ttkb.LabelFrame(main_container, text="Liste des affectations", bootstyle="primary")
        self.list_frame.pack(side=RIGHT, fill=BOTH, expand=YES, padx=(5, 0), pady=5)
        
        # Configuration du formulaire
        self._setup_form()
        
        # Configuration de la liste
        self._setup_list()
        
        # Barre d'état
        self.status_var = tk.StringVar(value="Prêt")
        self.status_bar = ttkb.Label(self, textvariable=self.status_var, bootstyle="primary")
        self.status_bar.pack(side=BOTTOM, fill=X, pady=(5, 0))
        
        # Charger les données initiales
        self.refresh_data()
    
    def _setup_form(self):
        """Configure le formulaire d'affectation"""
        # Container pour les champs du formulaire
        form_container = ttkb.Frame(self.form_frame)
        form_container.pack(padx=10, pady=10, fill=BOTH, expand=YES)
        
        # Variables pour les champs
        self.id_affectation_var = tk.StringVar()
        self.conducteur_var = tk.StringVar()
        self.vehicule_var = tk.StringVar()
        self.tournee_var = tk.StringVar()
        self.date_affectation_var = tk.StringVar()
        
        # Récupération des données pour les combobox
        self.conducteurs = self._get_conducteurs()
        self.vehicules = self._get_vehicules()
        self.tournees = self._get_tournees()
        
        # ID Affectation (caché pour les nouvelles affectations)
        id_frame = ttkb.Frame(form_container)
        id_frame.pack(fill=X, pady=5)
        
        id_label = ttkb.Label(id_frame, text="ID:", width=15, anchor=W)
        id_label.pack(side=LEFT)
        
        id_entry = ttkb.Entry(id_frame, textvariable=self.id_affectation_var, state="readonly")
        id_entry.pack(side=LEFT, fill=X, expand=YES)
        
        # Conducteur (Combobox)
        conducteur_frame = ttkb.Frame(form_container)
        conducteur_frame.pack(fill=X, pady=5)
        
        conducteur_label = ttkb.Label(conducteur_frame, text="Conducteur:", width=15, anchor=W)
        conducteur_label.pack(side=LEFT)
        
        self.conducteur_cb = ttkb.Combobox(conducteur_frame, textvariable=self.conducteur_var)
        self.conducteur_cb['values'] = [f"{c.id_conducteur} - {c.nom} {c.prenom}" for c in self.conducteurs]
        self.conducteur_cb.pack(side=LEFT, fill=X, expand=YES)
        
        # Véhicule (Combobox)
        vehicule_frame = ttkb.Frame(form_container)
        vehicule_frame.pack(fill=X, pady=5)
        
        vehicule_label = ttkb.Label(vehicule_frame, text="Véhicule:", width=15, anchor=W)
        vehicule_label.pack(side=LEFT)
        
        self.vehicule_cb = ttkb.Combobox(vehicule_frame, textvariable=self.vehicule_var)
        self.vehicule_cb['values'] = [f"{v.immatriculation} - {v.marque_modele}" for v in self.vehicules]
        self.vehicule_cb.pack(side=LEFT, fill=X, expand=YES)
        
        # Tournée (Combobox)
        tournee_frame = ttkb.Frame(form_container)
        tournee_frame.pack(fill=X, pady=5)
        
        tournee_label = ttkb.Label(tournee_frame, text="Tournée:", width=15, anchor=W)
        tournee_label.pack(side=LEFT)
        
        self.tournee_cb = ttkb.Combobox(tournee_frame, textvariable=self.tournee_var)
        self.tournee_cb['values'] = [f"{t.id_tournee} - {t.objectif}" for t in self.tournees]
        self.tournee_cb.pack(side=LEFT, fill=X, expand=YES)
        
        # Date d'affectation (DateEntry)
        date_frame = ttkb.Frame(form_container)
        date_frame.pack(fill=X, pady=5)
        
        date_label = ttkb.Label(date_frame, text="Date d'affectation:", width=15, anchor=W)
        date_label.pack(side=LEFT)
        
        self.date_entry = ttkb.DateEntry(date_frame, dateformat="%Y-%m-%d", firstweekday=0)
        self.date_entry.pack(side=LEFT, fill=X, expand=YES)
        
        # Boutons d'action
        button_frame = ttkb.Frame(form_container)
        button_frame.pack(fill=X, pady=10)
        
        self.save_btn = ttkb.Button(
            button_frame, 
            text="Enregistrer", 
            command=self.save_affectation, 
            bootstyle="success",
            width=12
        )
        self.save_btn.pack(side=LEFT, padx=5)
        
        self.new_btn = ttkb.Button(
            button_frame, 
            text="Nouveau", 
            command=self.new_affectation, 
            bootstyle="primary",
            width=12
        )
        self.new_btn.pack(side=LEFT, padx=5)
        
        self.delete_btn = ttkb.Button(
            button_frame, 
            text="Supprimer", 
            command=self.delete_affectation, 
            bootstyle="danger",
            width=12
        )
        self.delete_btn.pack(side=LEFT, padx=5)
        
        # Désactiver le bouton supprimer au début
        self.delete_btn.config(state=DISABLED)
    
    def _setup_list(self):
        """Configure la liste des affectations"""
        # Définir les colonnes
        columns = [
            {"text": "ID", "stretch": False, "width": 50},
            {"text": "Conducteur", "stretch": True, "width": 120},
            {"text": "Véhicule", "stretch": True, "width": 120},
            {"text": "Tournée", "stretch": True, "width": 120},
            {"text": "Date d'affectation", "stretch": True, "width": 120}
        ]
        
        # Créer la table
        self.table = Tableview(
            master=self.list_frame,
            coldata=columns,
            paginated=True,
            searchable=True,
            bootstyle="primary",
            pagesize=10,
            height=15  # Vous pouvez ajuster la hauteur ici si nécessaire
        )
        self.table.pack(fill=tk.BOTH, expand=tk.YES, padx=5, pady=5)
        
        # Associer la sélection à l'événement
        self.table.bind_all("<<TreeviewSelect>>", self._on_table_select)
    
    def _get_conducteurs(self):
        """Récupère la liste des conducteurs disponibles"""
        try:
            return self.session.query(Conducteur).all()
        except Exception as e:
            self.status_var.set(f"Erreur lors de la récupération des conducteurs: {str(e)}")
            return []
    
    def _get_vehicules(self):
        """Récupère la liste des véhicules"""
        try:
            return self.session.query(Vehicule).all()
        except Exception as e:
            self.status_var.set(f"Erreur lors de la récupération des véhicules: {str(e)}")
            return []
    
    def _get_tournees(self):
        """Récupère la liste des tournées disponibles"""
        try:
            return self.session.query(Tournee).all()
        except Exception as e:
            self.status_var.set(f"Erreur lors de la récupération des tournées: {str(e)}")
            return []
    
    def _on_table_select(self, event):
        """Gère la sélection d'une ligne dans la table"""
        selection = self.table.get_selection()
        if selection:
            # Activer le bouton supprimer
            self.delete_btn.config(state=NORMAL)
            
            # Récupérer l'ID de l'affectation sélectionnée
            affectation_id = selection[0][0]
            
            # Charger les détails de l'affectation
            self.load_affectation(affectation_id)
        else:
            # Désactiver le bouton supprimer si aucune sélection
            self.delete_btn.config(state=DISABLED)
    
    def load_affectation(self, affectation_id):
        """Charge les détails d'une affectation dans le formulaire"""
        try:
            # Récupérer l'affectation depuis la base de données
            affectation = self.session.query(Affectation).filter_by(id_affectation=affectation_id).first()
            
            if affectation:
                # Mise à jour des variables du formulaire
                self.id_affectation_var.set(str(affectation.id_affectation))
                
                # Rechercher le conducteur correspondant dans la liste
                for i, c in enumerate(self.conducteurs):
                    if c.id_conducteur == affectation.id_conducteur:
                        self.conducteur_var.set(f"{c.id_conducteur} - {c.nom} {c.prenom}")
                        self.conducteur_cb.current(i)
                        break
                
                # Rechercher le véhicule correspondant dans la liste
                for i, v in enumerate(self.vehicules):
                    if v.immatriculation == affectation.immatriculation_vehicule:
                        self.vehicule_var.set(f"{v.immatriculation} - {v.marque_modele}")
                        self.vehicule_cb.current(i)
                        break
                
                # Rechercher la tournée correspondante dans la liste
                for i, t in enumerate(self.tournees):
                    if t.id_tournee == affectation.id_tournee:
                        self.tournee_var.set(f"{t.id_tournee} - {t.objectif}")
                        self.tournee_cb.current(i)
                        break
                
                # Définir la date d'affectation
                if affectation.date_affectation:
                    self.date_entry.entry.delete(0, tk.END)
                    self.date_entry.entry.insert(0, affectation.date_affectation.strftime("%Y-%m-%d"))
                
                self.status_var.set(f"Affectation #{affectation.id_affectation} chargée")
            else:
                self.status_var.set(f"Affectation #{affectation_id} non trouvée")
        except Exception as e:
            self.status_var.set(f"Erreur lors du chargement de l'affectation: {str(e)}")
    
    def new_affectation(self):
        """Réinitialise le formulaire pour une nouvelle affectation"""
        # Effacer les variables
        self.id_affectation_var.set("")
        self.conducteur_var.set("")
        self.vehicule_var.set("")
        self.tournee_var.set("")
        
        # Réinitialiser la date à aujourd'hui
        self.date_entry.entry.delete(0, tk.END)
        self.date_entry.entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Désactiver le bouton supprimer
        self.delete_btn.config(state=DISABLED)
        
        self.status_var.set("Nouvelle affectation")
    
    def save_affectation(self):
        """Enregistre une nouvelle affectation ou met à jour une existante"""
        try:
            # Récupérer les valeurs du formulaire
            id_affectation = self.id_affectation_var.get()
            
            # Vérifier si tous les champs sont remplis
            if not self.conducteur_var.get() or not self.vehicule_var.get() or not self.tournee_var.get():
                Messagebox.show_error(
                    "Tous les champs sont obligatoires.",
                    "Erreur de validation"
                )
                return
            
            # Extraire les identifiants des sélections
            conducteur_id = self.conducteur_var.get().split(" - ")[0]
            vehicule_immatriculation = self.vehicule_var.get().split(" - ")[0]
            tournee_id = int(self.tournee_var.get().split(" - ")[0])
            
            # Récupérer la date d'affectation
            date_str = self.date_entry.entry.get()
            date_affectation = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Vérifier la disponibilité du véhicule
            vehicule = self.session.query(Vehicule).filter_by(immatriculation=vehicule_immatriculation).first()
            
            if not vehicule.est_disponible() and not id_affectation:
                confirmer = Messagebox.show_question(
                    "Le véhicule sélectionné n'est pas disponible. Voulez-vous quand même l'affecter?",
                    "Véhicule non disponible"
                )
                if not confirmer:
                    return
            
            # Vérifier la disponibilité du conducteur
            conducteur = self.session.query(Conducteur).filter_by(id_conducteur=conducteur_id).first()
            if conducteur.disponibilite != "disponible":
                confirmer = Messagebox.show_question(
                    f"Le conducteur est marqué comme '{conducteur.disponibilite}'. Voulez-vous quand même l'affecter?",
                    "Conducteur non disponible"
                )
                if not confirmer:
                    return
            
            if id_affectation:  # Mise à jour
                # Récupérer l'affectation existante
                affectation = self.session.query(Affectation).filter_by(id_affectation=int(id_affectation)).first()
                
                if affectation:
                    # Mettre à jour les champs
                    affectation.id_conducteur = conducteur_id
                    affectation.immatriculation_vehicule = vehicule_immatriculation
                    affectation.id_tournee = tournee_id
                    affectation.date_affectation = date_affectation
                    
                    self.session.commit()
                    self.status_var.set(f"Affectation #{id_affectation} mise à jour avec succès")
                else:
                    self.status_var.set(f"Affectation #{id_affectation} non trouvée")
            else:  # Nouvelle affectation
                nouvelle_affectation = Affectation(
                    id_conducteur=conducteur_id,
                    immatriculation_vehicule=vehicule_immatriculation,
                    id_tournee=tournee_id,
                    date_affectation=date_affectation
                )
                
                self.session.add(nouvelle_affectation)
                self.session.commit()
                
                self.status_var.set(f"Nouvelle affectation créée avec succès (ID: {nouvelle_affectation.id_affectation})")
            
            # Rafraîchir la liste des affectations
            self.refresh_data()
            
            # Réinitialiser le formulaire pour une nouvelle affectation
            self.new_affectation()
            
        except Exception as e:
            self.session.rollback()
            Messagebox.show_error(
                f"Erreur lors de l'enregistrement de l'affectation: {str(e)}",
                "Erreur"
            )
            self.status_var.set(f"Erreur: {str(e)}")
    
    def delete_affectation(self):
        """Supprime l'affectation sélectionnée"""
        id_affectation = self.id_affectation_var.get()
        
        if not id_affectation:
            self.status_var.set("Aucune affectation sélectionnée")
            return
        
        # Demander confirmation
        confirmer = Messagebox.show_question(
            f"Êtes-vous sûr de vouloir supprimer l'affectation #{id_affectation}?",
            "Confirmation de suppression"
        )
        
        if confirmer:
            try:
                # Récupérer l'affectation
                affectation = self.session.query(Affectation).filter_by(id_affectation=int(id_affectation)).first()
                
                if affectation:
                    # Supprimer l'affectation
                    self.session.delete(affectation)
                    self.session.commit()
                    
                    self.status_var.set(f"Affectation #{id_affectation} supprimée avec succès")
                    
                    # Rafraîchir la liste et réinitialiser le formulaire
                    self.refresh_data()
                    self.new_affectation()
                else:
                    self.status_var.set(f"Affectation #{id_affectation} non trouvée")
            except Exception as e:
                self.session.rollback()
                Messagebox.show_error(
                    f"Erreur lors de la suppression de l'affectation: {str(e)}",
                    "Erreur"
                )
                self.status_var.set(f"Erreur: {str(e)}")
    
    def refresh_data(self):
        """Rafraîchit la liste des affectations"""
        try:
            # Effacer les données existantes
            self.table.delete_rows()
            
            # Récupérer toutes les affectations
            affectations = self.session.query(Affectation).all()
            
            # Préparer les données pour la table
            rows = []
            for a in affectations:
                # Récupérer les informations du conducteur
                conducteur = self.session.query(Conducteur).filter_by(id_conducteur=a.id_conducteur).first()
                conducteur_info = f"{conducteur.nom} {conducteur.prenom}" if conducteur else "Inconnu"
                
                # Récupérer les informations du véhicule
                vehicule = self.session.query(Vehicule).filter_by(immatriculation=a.immatriculation_vehicule).first()
                vehicule_info = vehicule.marque_modele if vehicule else "Inconnu"
                
                # Récupérer les informations de la tournée
                tournee = self.session.query(Tournee).filter_by(id_tournee=a.id_tournee).first()
                tournee_info = tournee.objectif if tournee else "Inconnue"
                
                # Formater la date
                date_info = a.date_affectation.strftime("%Y-%m-%d") if a.date_affectation else "N/A"
                
                # Ajouter la ligne
                rows.append((a.id_affectation, conducteur_info, vehicule_info, tournee_info, date_info))
            
            # Insérer les données dans la table
            self.table.insert_rows(rows)
            
            # Rafraîchir aussi les listes déroulantes
            self.conducteurs = self._get_conducteurs()
            self.vehicules = self._get_vehicules()
            self.tournees = self._get_tournees()
            
            self.conducteur_cb['values'] = [f"{c.id_conducteur} - {c.nom} {c.prenom}" for c in self.conducteurs]
            self.vehicule_cb['values'] = [f"{v.immatriculation} - {v.marque_modele}" for v in self.vehicules]
            self.tournee_cb['values'] = [f"{t.id_tournee} - {t.objectif}" for t in self.tournees]
            
            self.status_var.set(f"{len(affectations)} affectation(s) chargée(s)")
            
        except Exception as e:
            self.status_var.set(f"Erreur lors du rafraîchissement des données: {str(e)}")
    
    def __del__(self):
        """Ferme la session à la destruction de l'objet"""
        if hasattr(self, 'session'):
            self.session.close()


# Pour tester l'interface indépendamment
if __name__ == "__main__":
    root = ttkb.Window(themename="superhero")
    root.title("Gestion des Affectations")
    root.geometry("1200x700")
    
    app = AffectationView(root)
    
    root.mainloop()