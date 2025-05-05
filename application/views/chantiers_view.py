import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar, DoubleVar
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class ChantierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Chantiers")
        self.root.geometry("900x600")
        
        # Import local pour éviter les imports circulaires
        from application.models.chantiers import Chantier
        self.Chantier = Chantier

        # Variables
        self.id_client_var = StringVar()
        self.localisation_var = StringVar()
        self.latitude_var = DoubleVar()
        self.longitude_var = DoubleVar()
        self.nature_terrain_var = StringVar()
        self.distance_aller_goudron_var = DoubleVar()
        self.distance_aller_piste_var = DoubleVar()
        self.temps_aller_var = DoubleVar()

        # Formulaire
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=X)

        ttk.Label(frame, text="ID Client").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.id_client_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Localisation").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.localisation_var).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Latitude").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.latitude_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Longitude").grid(row=1, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.longitude_var).grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Nature Terrain").grid(row=2, column=0, padx=5, pady=5)
        # Remplacer l'Entry par une Combobox pour Nature Terrain
        self.nature_terrain_combo = ttk.Combobox(frame, textvariable=self.nature_terrain_var, 
                                              values=["Accès facile", "Accès difficile"],
                                              state="readonly")
        self.nature_terrain_combo.grid(row=2, column=1, padx=5, pady=5)
        self.nature_terrain_combo.current(0)  # Définir la valeur par défaut

        ttk.Label(frame, text="Distance Aller Goudron (km)").grid(row=2, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.distance_aller_goudron_var).grid(row=2, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Distance Aller Piste (km)").grid(row=3, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.distance_aller_piste_var).grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Temps Aller (h)").grid(row=3, column=2, padx=5, pady=5)
        temps_aller_entry = ttk.Entry(frame, textvariable=self.temps_aller_var, state=DISABLED)
        temps_aller_entry.grid(row=3, column=3, padx=5, pady=5)

        # Boutons
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=X)

        ttk.Button(btn_frame, text="Ajouter", command=self.ajouter, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.modifier, bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.supprimer, bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Calculer Temps", command=self.calculer_temps_aller, bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Voir Commandes", command=self.voir_commandes, bootstyle=INFO).pack(side=LEFT, padx=5)

        # Tableau
        self.tree = ttk.Treeview(self.root, columns=("id_client", "localisation", "latitude", "longitude", 
                                                    "nature_terrain", "distance_goudron", "distance_piste", "temps_aller"), 
                                                    show="headings")
        self.tree.pack(fill=BOTH, expand=True)

        self.tree.heading("id_client", text="ID Client")
        self.tree.heading("localisation", text="Localisation")
        self.tree.heading("latitude", text="Latitude")
        self.tree.heading("longitude", text="Longitude")
        self.tree.heading("nature_terrain", text="Nature Terrain")
        self.tree.heading("distance_goudron", text="Distance Goudron (km)")
        self.tree.heading("distance_piste", text="Distance Piste (km)")
        self.tree.heading("temps_aller", text="Temps Aller (h)")

        # Ajuster la largeur des colonnes
        self.tree.column("id_client", width=70)
        self.tree.column("localisation", width=150)
        self.tree.column("latitude", width=100)
        self.tree.column("longitude", width=100)
        self.tree.column("nature_terrain", width=120)
        self.tree.column("distance_goudron", width=120)
        self.tree.column("distance_piste", width=120)
        self.tree.column("temps_aller", width=100)

        self.tree.bind("<ButtonRelease-1>", self.selectionner)

        self.charger_donnees()

    def calculer_temps_aller(self):
        try:
            # Calcul basé sur la formule de la classe Chantier
            distance_goudron = self.distance_aller_goudron_var.get()
            distance_piste = self.distance_aller_piste_var.get()
            temps = (distance_goudron + distance_piste) / 400
            self.temps_aller_var.set(round(temps, 2))
            return temps
        except:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides pour les distances.")
            return None

    def ajouter(self):
        try:
            temps_aller = self.calculer_temps_aller()
            if temps_aller is None:
                return

            id_client = int(self.id_client_var.get())

            chantier = self.Chantier(
                id_client=id_client,
                localisation=self.localisation_var.get(),
                latitude=self.latitude_var.get(),
                longitude=self.longitude_var.get(),
                nature_terrain=self.nature_terrain_var.get(),
                distanceAllerGoudron=self.distance_aller_goudron_var.get(),
                distanceAllerPiste=self.distance_aller_piste_var.get(),
                temps_aller = self.calculer_temps_aller()
            )
            session.add(chantier)
            session.commit()
            self.charger_donnees()
            self.vider_formulaire()
            messagebox.showinfo("Succès", "Chantier ajouté avec succès!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout du chantier: {str(e)}")


    def modifier(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un chantier à modifier")
            return
        try:
            id_client = self.tree.item(item, "values")[0]
            temps_aller = self.calculer_temps_aller()
            if temps_aller is None:
                return
                
            chantier = session.query(self.Chantier).filter_by(id_client=id_client).first()
            if chantier:
                chantier.localisation = self.localisation_var.get()
                chantier.latitude = self.latitude_var.get()
                chantier.longitude = self.longitude_var.get()
                chantier.nature_terrain = self.nature_terrain_var.get()
                chantier.distanceAllerGoudron = self.distance_aller_goudron_var.get()
                chantier.distanceAllerPiste = self.distance_aller_piste_var.get()
                chantier.temps_aller = self.calculer_temps_aller()
                session.commit()
                self.charger_donnees()
                messagebox.showinfo("Succès", "Chantier modifié avec succès!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la modification du chantier: {str(e)}")


    def supprimer(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un chantier à supprimer")
            return
        
        # Demande de confirmation
        if not messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer ce chantier? Cette action supprimera également toutes les commandes associées."):
            return
            
        try:
            id_client = self.tree.item(item, "values")[0]
            session.query(self.Chantier).filter_by(id_client=id_client).delete()
            session.commit()
            self.charger_donnees()
            self.vider_formulaire()
            messagebox.showinfo("Succès", "Chantier supprimé avec succès!")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression du chantier: {str(e)}")

    def selectionner(self, event):
        item = self.tree.selection()
        if item:
            try:
                values = self.tree.item(item, "values")
                self.id_client_var.set(values[0])
                self.localisation_var.set(values[1])
                
                # Convertir les valeurs numériques en vérifiant si elles sont None ou vides
                self.latitude_var.set(float(values[2]) if values[2] and values[2] != 'None' else 0.0)
                self.longitude_var.set(float(values[3]) if values[3] and values[3] != 'None' else 0.0)
                
                # Pour la combobox, s'assurer que la valeur est l'une des deux options permises
                terrain = values[4] if values[4] and values[4] != 'None' else "Accès facile"
                if terrain not in ["Accès facile", "Accès difficile"]:
                    terrain = "Accès facile"  # Valeur par défaut si la valeur existante n'est pas valide
                self.nature_terrain_var.set(terrain)
                
                self.distance_aller_goudron_var.set(float(values[5]) if values[5] and values[5] != 'None' else 0.0)
                self.distance_aller_piste_var.set(float(values[6]) if values[6] and values[6] != 'None' else 0.0)
                self.temps_aller_var.set(float(values[7]) if values[7] and values[7] != 'None' else 0.0)
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la sélection: {str(e)}")

    def charger_donnees(self):
        # Effacer le tableau actuel
        self.tree.delete(*self.tree.get_children())
        for chantier in session.query(self.Chantier).all():
            # Vérifier et normaliser la valeur de nature_terrain
            nature_terrain = chantier.nature_terrain or ""
            if nature_terrain not in ["Accès facile", "Accès difficile"]:
                nature_terrain = "Accès facile"  # Valeur par défaut
                
            self.tree.insert("", "end", values=(
                chantier.id_client,
                chantier.localisation or "",
                chantier.latitude or "",
                chantier.longitude or "",
                nature_terrain,
                chantier.distanceAllerGoudron or "",
                chantier.distanceAllerPiste or "",
                chantier.temps_aller or ""
                ))
                
        print(f"Nombre de lignes affichées dans le tableau: {len(self.tree.get_children())}")
        
    def vider_formulaire(self):
        self.id_client_var.set("")
        self.localisation_var.set("")
        self.latitude_var.set(0.0)
        self.longitude_var.set(0.0)
        self.nature_terrain_var.set("Accès facile")  # Définir la valeur par défaut
        self.distance_aller_goudron_var.set(0.0)
        self.distance_aller_piste_var.set(0.0)
        self.temps_aller_var.set(0.0)
    
    def voir_commandes(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un chantier pour voir ses commandes")
            return
            
        id_client = self.tree.item(item, "values")[0]
        
        # Création d'une nouvelle fenêtre pour afficher les commandes
        commandes_window = ttk.Toplevel(self.root)
        commandes_window.title(f"Commandes pour le chantier {id_client}")
        commandes_window.geometry("800x400")
        
        # Import des modèles nécessaires
        from application.models.commande import Commande
        
        # Tableau des commandes
        commandes_tree = ttk.Treeview(commandes_window, columns=(
            "id_commande", "nature_service", "type_vehicule", "quantite", 
            "lieu_chargement", "date_commande", "date_livraison"
        ), show="headings")
        
        commandes_tree.heading("id_commande", text="ID Commande")
        commandes_tree.heading("nature_service", text="Nature Service")
        commandes_tree.heading("type_vehicule", text="Type Véhicule")
        commandes_tree.heading("quantite", text="Quantité")
        commandes_tree.heading("lieu_chargement", text="Lieu Chargement")
        commandes_tree.heading("date_commande", text="Date Commande")
        commandes_tree.heading("date_livraison", text="Date Livraison")
        
        commandes_tree.pack(fill=BOTH, expand=True)
        
        # Chargement des commandes pour ce client
        try:
            commandes = session.query(Commande).filter_by(id_client=id_client).all()
            for commande in commandes:
                date_commande = commande.date_commande.strftime('%d/%m/%Y') if commande.date_commande else ""
                date_livraison = commande.date_livraison.strftime('%d/%m/%Y') if commande.date_livraison else ""
                
                commandes_tree.insert("", END, values=(
                    commande.id_commande,
                    commande.nature_service,
                    commande.type_vehicule,
                    commande.quantite_requise,
                    commande.lieu_chargement,
                    date_commande,
                    date_livraison
                ))
            
            # Afficher un message si aucune commande n'est trouvée
            if not commandes:
                ttk.Label(commandes_window, text="Aucune commande pour ce chantier", 
                          font=("Helvetica", 12), padding=20).pack()
        
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des commandes: {str(e)}")
        
        # Ajout d'un bouton pour fermer la fenêtre
        ttk.Button(commandes_window, text="Fermer", 
                  command=commandes_window.destroy, 
                  bootstyle=SECONDARY).pack(pady=10)


if __name__ == "__main__":
    # Créer une fenêtre avec le thème darkly directement lors de l'initialisation
    root = ttk.Window(themename="cosmo")
    app = ChantierApp(root)
    root.mainloop()