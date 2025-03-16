import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime
import tkinter as tk

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class TourneeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Tournées")
        self.root.geometry("1000x600")
        
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

        # Frame pour le formulaire principal
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=X)

        # Première ligne
        ttk.Label(main_frame, text="ID Tournée").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(main_frame, textvariable=self.id_tournee_var, state="readonly").grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Conducteur").grid(row=0, column=2, padx=5, pady=5)
        self.conducteur_cb = ttk.Combobox(main_frame, textvariable=self.id_conducteur_var, state="readonly")
        self.conducteur_cb.grid(row=0, column=3, padx=5, pady=5)
        self.conducteur_cb['values'] = [f"{c.id_conducteur} - {c.nom} {c.prenom}" for c in self.conducteurs]

        # Deuxième ligne
        ttk.Label(main_frame, text="Véhicule").grid(row=1, column=0, padx=5, pady=5)
        self.vehicule_cb = ttk.Combobox(main_frame, textvariable=self.immatriculation_var, state="readonly")
        self.vehicule_cb.grid(row=1, column=1, padx=5, pady=5)
        self.vehicule_cb['values'] = [f"{v.immatriculation} - {v.marque_modele}" for v in self.vehicules]

        ttk.Label(main_frame, text="Commande").grid(row=1, column=2, padx=5, pady=5)
        self.commande_cb = ttk.Combobox(main_frame, textvariable=self.id_commande_var, state="readonly")
        self.commande_cb.grid(row=1, column=3, padx=5, pady=5)
        self.commande_cb['values'] = [f"{c.id_commande} - {c.nature_service}" for c in self.commandes]


        # Troisième ligne
        ttk.Label(main_frame, text="Objectif").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(main_frame, textvariable=self.objectif_var).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Lieu de départ").grid(row=2, column=2, padx=5, pady=5)
        ttk.Entry(main_frame, textvariable=self.lieu_depart_var).grid(row=2, column=3, padx=5, pady=5)

        # Quatrième ligne
        ttk.Label(main_frame, text="Destination").grid(row=3, column=0, padx=5, pady=5)
        ttk.Entry(main_frame, textvariable=self.destination_var).grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(main_frame, text="Itinéraire").grid(row=3, column=2, padx=5, pady=5)
        ttk.Entry(main_frame, textvariable=self.itineraire_var).grid(row=3, column=3, padx=5, pady=5)

        # Cinquième ligne
        ttk.Label(main_frame, text="Kilomètres parcourus").grid(row=4, column=0, padx=5, pady=5)
        ttk.Entry(main_frame, textvariable=self.km_parcouru_var).grid(row=4, column=1, padx=5, pady=5)

        # Frame pour les dates et heures
        date_frame = ttk.LabelFrame(self.root, text="Dates et heures", padding=10)
        date_frame.pack(fill=X)

        # Fonction pour créer un groupe de widgets de date
        def create_date_widgets(parent, row, col, jour_var, mois_var, annee_var, label_text):
            ttk.Label(parent, text=label_text).grid(row=row, column=col, padx=5, pady=5)
            
            date_frame = ttk.Frame(parent)
            date_frame.grid(row=row, column=col+1, padx=5, pady=5)
            
            jour_spin = ttk.Spinbox(date_frame, from_=1, to=31, width=3, textvariable=jour_var)
            jour_spin.pack(side=LEFT, padx=1)
            
            ttk.Label(date_frame, text="/").pack(side=LEFT)
            
            mois_spin = ttk.Spinbox(date_frame, from_=1, to=12, width=3, textvariable=mois_var)
            mois_spin.pack(side=LEFT, padx=1)
            
            ttk.Label(date_frame, text="/").pack(side=LEFT)
            
            annee_spin = ttk.Spinbox(date_frame, from_=2020, to=2030, width=5, textvariable=annee_var)
            annee_spin.pack(side=LEFT, padx=1)
            
            return jour_spin, mois_spin, annee_spin

        # Dates et heures
        # Départ
        create_date_widgets(date_frame, 0, 0, self.jour_depart_var, self.mois_depart_var, self.annee_depart_var, "Date départ")
        ttk.Label(date_frame, text="Heure départ").grid(row=0, column=3, padx=5, pady=5)
        self.heure_depart = ttk.Spinbox(date_frame, from_=0, to=23, width=3)
        self.heure_depart.grid(row=0, column=4, padx=0, pady=5)
        ttk.Label(date_frame, text=":").grid(row=0, column=5, padx=0, pady=5)
        self.minute_depart = ttk.Spinbox(date_frame, from_=0, to=59, width=3)
        self.minute_depart.grid(row=0, column=6, padx=5, pady=5)

        # Réception
        create_date_widgets(date_frame, 1, 0, self.jour_reception_var, self.mois_reception_var, self.annee_reception_var, "Date réception")
        ttk.Label(date_frame, text="Heure réception").grid(row=1, column=3, padx=5, pady=5)
        self.heure_reception = ttk.Spinbox(date_frame, from_=0, to=23, width=3)
        self.heure_reception.grid(row=1, column=4, padx=0, pady=5)
        ttk.Label(date_frame, text=":").grid(row=1, column=5, padx=0, pady=5)
        self.minute_reception = ttk.Spinbox(date_frame, from_=0, to=59, width=3)
        self.minute_reception.grid(row=1, column=6, padx=5, pady=5)
        
        # Retour
        create_date_widgets(date_frame, 2, 0, self.jour_retour_var, self.mois_retour_var, self.annee_retour_var, "Date retour")
        ttk.Label(date_frame, text="Heure retour").grid(row=2, column=3, padx=5, pady=5)
        self.heure_retour = ttk.Spinbox(date_frame, from_=0, to=23, width=3)
        self.heure_retour.grid(row=2, column=4, padx=0, pady=5)
        ttk.Label(date_frame, text=":").grid(row=2, column=5, padx=0, pady=5)
        self.minute_retour = ttk.Spinbox(date_frame, from_=0, to=59, width=3)
        self.minute_retour.grid(row=2, column=6, padx=5, pady=5)
        
        # Arrivée
        create_date_widgets(date_frame, 3, 0, self.jour_arrivee_var, self.mois_arrivee_var, self.annee_arrivee_var, "Date arrivée")
        ttk.Label(date_frame, text="Heure arrivée").grid(row=3, column=3, padx=5, pady=5)
        self.heure_arrivee = ttk.Spinbox(date_frame, from_=0, to=23, width=3)
        self.heure_arrivee.grid(row=3, column=4, padx=0, pady=5)
        ttk.Label(date_frame, text=":").grid(row=3, column=5, padx=0, pady=5)
        self.minute_arrivee = ttk.Spinbox(date_frame, from_=0, to=59, width=3)
        self.minute_arrivee.grid(row=3, column=6, padx=5, pady=5)

        # Boutons
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=X)

        ttk.Button(btn_frame, text="Ajouter", command=self.ajouter, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.modifier, bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.supprimer, bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Voir Durée", command=self.afficher_duree, bootstyle=INFO).pack(side=LEFT, padx=5)

        # Tableau
        columns = ("id_tournee", "conducteur", "vehicule", "commande", "objectif", 
                  "depart", "destination", "km", "date_depart", "date_arrivee", "duree")
        
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")
        self.tree.pack(fill=BOTH, expand=True)

        self.tree.heading("id_tournee", text="ID")
        self.tree.heading("conducteur", text="Conducteur")
        self.tree.heading("vehicule", text="Véhicule")
        self.tree.heading("commande", text="Commande")
        self.tree.heading("objectif", text="Objectif")
        self.tree.heading("depart", text="Départ")
        self.tree.heading("destination", text="Destination")
        self.tree.heading("km", text="KM")
        self.tree.heading("date_depart", text="Départ le")
        self.tree.heading("date_arrivee", text="Arrivée le")
        self.tree.heading("duree", text="Durée")

        # Configurer les colonnes pour qu'elles soient toutes visibles
        for col in columns:
            self.tree.column(col, width=90)

        self.tree.bind("<ButtonRelease-1>", self.selectionner)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.charger_donnees()
        

    def charger_listes_dependantes(self):
        from application.models.conducteurs import Conducteur
        self.Conducteur = Conducteur
        self.conducteurs = session.query(self.Conducteur).all()
        from application.models.vehicule import Vehicule
        self.Vehicule = Vehicule
        self.vehicules = session.query(self.Vehicule).all()
        from application.models.commande import Commande
        self.Commande = Commande
        self.commandes = session.query(self.Commande).all()

    
    def get_datetime(self, jour_var, mois_var, annee_var, hour_widget, minute_widget):
            try:
                jour = int(jour_var.get())
                mois = int(mois_var.get())
                annee = int(annee_var.get())
                hour = int(hour_widget.get())
                minute = int(minute_widget.get())
                
                # Vérification des valeurs
                if jour < 1 or jour > 31 or mois < 1 or mois > 12 or annee < 2000 or annee > 2100:
                    return None
                    
                return datetime(annee, mois, jour, hour, minute)
            except:
                return None

    def set_datetime_widgets(self, dt, jour_var, mois_var, annee_var, hour_widget, minute_widget):
            if dt:
                jour_var.set(str(dt.day))
                mois_var.set(str(dt.month))
                annee_var.set(str(dt.year))
                hour_widget.set(dt.hour)
                minute_widget.set(dt.minute)
            else:
                today = datetime.now()
                jour_var.set(str(today.day))
                mois_var.set(str(today.month))
                annee_var.set(str(today.year))
                hour_widget.set(0)
                minute_widget.set(0)

    def ajouter(self):
            try:
                # Extraction des IDs des combobox
                id_conducteur = self.id_conducteur_var.get().split(" - ")[0] if self.id_conducteur_var.get() else None
                immatriculation = self.immatriculation_var.get().split(" - ")[0] if self.immatriculation_var.get() else None
                id_commande = self.id_commande_var.get().split(" - ")[0] if self.id_commande_var.get() else None
                
                # Conversion du kilométrage en float
                try:
                    km_parcouru = float(self.km_parcouru_var.get()) if self.km_parcouru_var.get() else 0
                except ValueError:
                    messagebox.showerror("Erreur", "Le kilométrage doit être un nombre")
                    return
                    
                # Récupération des dates et heures
                date_heure_depart = self.get_datetime(
                    self.jour_depart_var, self.mois_depart_var, self.annee_depart_var,
                    self.heure_depart, self.minute_depart
                )
                date_heure_reception = self.get_datetime(
                    self.jour_reception_var, self.mois_reception_var, self.annee_reception_var,
                    self.heure_reception, self.minute_reception
                )
                date_heure_retour = self.get_datetime(
                    self.jour_retour_var, self.mois_retour_var, self.annee_retour_var,
                    self.heure_retour, self.minute_retour
                )
                date_heure_arrivee = self.get_datetime(
                    self.jour_arrivee_var, self.mois_arrivee_var, self.annee_arrivee_var,
                    self.heure_arrivee, self.minute_arrivee
                )
                
                if not date_heure_depart or not date_heure_arrivee:
                    messagebox.showwarning("Attention", "Les dates de départ et d'arrivée sont obligatoires")
                    return
                
                tournee = self.Tournee(
                    id_conducteur=id_conducteur,
                    immatriculation_vehicule=immatriculation,
                    id_commande=int(id_commande) if id_commande else None,
                    objectif=self.objectif_var.get(),
                    lieu_depart=self.lieu_depart_var.get(),
                    destination=self.destination_var.get(),
                    itineraire=self.itineraire_var.get(),
                    km_parcouru=km_parcouru,
                    date_heure_depart=date_heure_depart,
                    date_heure_reception=date_heure_reception,
                    date_heure_retour=date_heure_retour,
                    date_heure_arrivee=date_heure_arrivee
                )
                session.add(tournee)
                session.commit()
                self.charger_donnees()
                self.vider_formulaire()
                messagebox.showinfo("Succès", "Tournée ajoutée avec succès")
            except Exception as e:
                session.rollback()
                messagebox.showerror("Erreur", f"Impossible d'ajouter la tournée: {str(e)}")

    def modifier(self):
            try:
                id_tournee = self.id_tournee_var.get()
                if not id_tournee:
                    messagebox.showwarning("Attention", "Veuillez sélectionner une tournée à modifier")
                    return
                    
                tournee = session.query(self.Tournee).get(id_tournee)
                if not tournee:
                    messagebox.showerror("Erreur", "Tournée non trouvée")
                    return
                    
                # Extraction des IDs des combobox
                id_conducteur = self.id_conducteur_var.get().split(" - ")[0] if self.id_conducteur_var.get() else None
                immatriculation = self.immatriculation_var.get().split(" - ")[0] if self.immatriculation_var.get() else None
                id_commande = self.id_commande_var.get().split(" - ")[0] if self.id_commande_var.get() else None
                
                # Conversion du kilométrage en float
                try:
                    km_parcouru = float(self.km_parcouru_var.get()) if self.km_parcouru_var.get() else 0
                except ValueError:
                    messagebox.showerror("Erreur", "Le kilométrage doit être un nombre")
                    return
                    
                # Récupération des dates et heures
                date_heure_depart = self.get_datetime(
                    self.jour_depart_var, self.mois_depart_var, self.annee_depart_var,
                    self.heure_depart, self.minute_depart
                )
                date_heure_reception = self.get_datetime(
                    self.jour_reception_var, self.mois_reception_var, self.annee_reception_var,
                    self.heure_reception, self.minute_reception
                )
                date_heure_retour = self.get_datetime(
                    self.jour_retour_var, self.mois_retour_var, self.annee_retour_var,
                    self.heure_retour, self.minute_retour
                )
                date_heure_arrivee = self.get_datetime(
                    self.jour_arrivee_var, self.mois_arrivee_var, self.annee_arrivee_var,
                    self.heure_arrivee, self.minute_arrivee
                )
                
                if not date_heure_depart or not date_heure_arrivee:
                    messagebox.showwarning("Attention", "Les dates de départ et d'arrivée sont obligatoires")
                    return
                    
                # Mise à jour des données
                tournee.id_conducteur = id_conducteur
                tournee.immatriculation_vehicule = immatriculation
                tournee.id_commande = int(id_commande) if id_commande else None
                tournee.objectif = self.objectif_var.get()
                tournee.lieu_depart = self.lieu_depart_var.get()
                tournee.destination = self.destination_var.get()
                tournee.itineraire = self.itineraire_var.get()
                tournee.km_parcouru = km_parcouru
                tournee.date_heure_depart = date_heure_depart
                tournee.date_heure_reception = date_heure_reception
                tournee.date_heure_retour = date_heure_retour
                tournee.date_heure_arrivee = date_heure_arrivee
                
                session.commit()
                self.charger_donnees()
                messagebox.showinfo("Succès", "Tournée modifiée avec succès")
            except Exception as e:
                session.rollback()
                messagebox.showerror("Erreur", f"Impossible de modifier la tournée: {str(e)}")

    def supprimer(self):
            try:
                id_tournee = self.id_tournee_var.get()
                if not id_tournee:
                    messagebox.showwarning("Attention", "Veuillez sélectionner une tournée à supprimer")
                    return
                    
                if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cette tournée ?"):
                    tournee = session.query(self.Tournee).get(id_tournee)
                    if tournee:
                        session.delete(tournee)
                        session.commit()
                        self.charger_donnees()
                        self.vider_formulaire()
                        messagebox.showinfo("Succès", "Tournée supprimée avec succès")
                    else:
                        messagebox.showerror("Erreur", "Tournée non trouvée")
            except Exception as e:
                session.rollback()
                messagebox.showerror("Erreur", f"Impossible de supprimer la tournée: {str(e)}")

    def afficher_duree(self):
            try:
                id_tournee = self.id_tournee_var.get()
                if not id_tournee:
                    messagebox.showwarning("Attention", "Veuillez sélectionner une tournée")
                    return
                    
                tournee = session.query(self.Tournee).get(id_tournee)
                if not tournee:
                    messagebox.showerror("Erreur", "Tournée non trouvée")
                    return
                    
                if tournee.date_heure_depart and tournee.date_heure_arrivee:
                    duree = tournee.date_heure_arrivee - tournee.date_heure_depart
                    heures = duree.total_seconds() // 3600
                    minutes = (duree.total_seconds() % 3600) // 60
                    messagebox.showinfo("Durée de la tournée", f"Durée totale: {int(heures)}h {int(minutes)}min")
                else:
                    messagebox.showinfo("Durée de la tournée", "Impossible de calculer la durée (dates manquantes)")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de calculer la durée: {str(e)}")

    def selectionner(self, event):
            try:
                selection = self.tree.selection()
                if not selection:
                    return
                    
                item = self.tree.item(selection[0])
                id_tournee = item['values'][0]
                
                tournee = session.query(self.Tournee).get(id_tournee)
                if tournee:
                    self.id_tournee_var.set(tournee.id_tournee)
                    
                    # Mettre à jour les combobox
                    if tournee.conducteur:
                        self.id_conducteur_var.set(f"{tournee.id_conducteur} - {tournee.conducteur.nom} {tournee.conducteur.prenom}")
                    else:
                        self.id_conducteur_var.set("")
                        
                    if tournee.vehicule:
                        self.immatriculation_var.set(f"{tournee.immatriculation_vehicule} - {tournee.vehicule.modele}")
                    else:
                        self.immatriculation_var.set("")
                        
                    if tournee.commande:
                        self.id_commande_var.set(f"{tournee.id_commande} - {tournee.commande.reference}")
                    else:
                        self.id_commande_var.set("")
                    
                    # Mettre à jour les autres champs
                    self.objectif_var.set(tournee.objectif or "")
                    self.lieu_depart_var.set(tournee.lieu_depart or "")
                    self.destination_var.set(tournee.destination or "")
                    self.itineraire_var.set(tournee.itineraire or "")
                    self.km_parcouru_var.set(str(tournee.km_parcouru) if tournee.km_parcouru else "")
                    
                    # Mettre à jour les dates
                    self.set_datetime_widgets(
                        tournee.date_heure_depart,
                        self.jour_depart_var, self.mois_depart_var, self.annee_depart_var,
                        self.heure_depart, self.minute_depart
                    )
                    self.set_datetime_widgets(
                        tournee.date_heure_reception,
                        self.jour_reception_var, self.mois_reception_var, self.annee_reception_var,
                        self.heure_reception, self.minute_reception
                    )
                    self.set_datetime_widgets(
                        tournee.date_heure_retour,
                        self.jour_retour_var, self.mois_retour_var, self.annee_retour_var,
                        self.heure_retour, self.minute_retour
                    )
                    self.set_datetime_widgets(
                        tournee.date_heure_arrivee,
                        self.jour_arrivee_var, self.mois_arrivee_var, self.annee_arrivee_var,
                        self.heure_arrivee, self.minute_arrivee
                    )
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sélectionner la tournée: {str(e)}")

    def vider_formulaire(self):
            self.id_tournee_var.set("")
            self.id_conducteur_var.set("")
            self.immatriculation_var.set("")
            self.id_commande_var.set("")
            self.objectif_var.set("")
            self.lieu_depart_var.set("")
            self.destination_var.set("")
            self.itineraire_var.set("")
            self.km_parcouru_var.set("")
            
            # Réinitialiser les dates
            today = datetime.now()
            for var in [self.jour_depart_var, self.jour_reception_var, self.jour_retour_var, self.jour_arrivee_var]:
                var.set(str(today.day))
            for var in [self.mois_depart_var, self.mois_reception_var, self.mois_retour_var, self.mois_arrivee_var]:
                var.set(str(today.month))
            for var in [self.annee_depart_var, self.annee_reception_var, self.annee_retour_var, self.annee_arrivee_var]:
                var.set(str(today.year))
            
            for widget in [self.heure_depart, self.minute_depart, self.heure_reception, self.minute_reception,
                           self.heure_retour, self.minute_retour, self.heure_arrivee, self.minute_arrivee]:
                widget.set(0)

    def charger_donnees(self):
        # Effacer les données existantes
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Charger les nouvelles données
        tournees = session.query(self.Tournee).all()
        for tournee in tournees:
            conducteur_info = f"{tournee.conducteur.nom} {tournee.conducteur.prenom}" if tournee.conducteur else ""
            vehicule_info = tournee.vehicule.marque_modele if tournee.vehicule else ""
            self.commande_cb['values'] = [f"{c.id_commande} - {c.nature_service}" for c in self.commandes]  # Exemple, adapte selon la bonne colonne
            commande_info = f"{tournee.commande.id_commande} - {tournee.commande.nature_service}" if tournee.commande else ""
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
            
            self.tree.insert("", "end", values=(
                tournee.id_tournee,
                conducteur_info,
                vehicule_info,
                commande_info,
                tournee.objectif,
                tournee.lieu_depart,
                tournee.destination,
                tournee.km_parcouru,
                date_depart,
                date_arrivee,
                duree
            ))


if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    app = TourneeApp(root)
    root.mainloop()