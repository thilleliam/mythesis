import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime
configure_mappers()

# Configuration de la session SQLAlchemy
Session = sessionmaker(bind=engine)
session = Session()

class VehiculeApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill=BOTH, expand=True)

        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule

        # Configuration du tableau
        self.tree = ttk.Treeview(
            self,
            columns=("Immatriculation", "Châssis", "Interne", "Marque", "Type", "Tonnes", "Volume", "Etat"),
            show="headings",
            style="Treeview"
        )

        # Ajout des colonnes et en-têtes
        colonnes = [
            ("Immatriculation", "Immatriculation"),
            ("Châssis", "Numéro Châssis"),
            ("Interne", "Numéro Interne"),
            ("Marque", "Marque & Modèle"),
            ("Type", "Type"),
            ("Tonnes", "Capacité (Tonnes)"),
            ("Volume", "Capacité (m³)"),
            ("Etat", "État")
        ]

        for col_id, col_name in colonnes:
            self.tree.heading(col_id, text=col_name)
            self.tree.column(col_id, width=120, anchor=CENTER)

        # Ajout du tableau avec scrollbar
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Boutons CRUD
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=X, padx=10, pady=5)

        ttk.Button(btn_frame, text="Ajouter", command=self.ajouter_vehicule, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.modifier_vehicule, bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.supprimer_vehicule, bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Total Parcourus", command=self.afficher_total_parcouru, bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Affectation", command=self.affectation_tournee, bootstyle=PRIMARY).pack(side=LEFT, padx=5)

        # Charger les données
        self.charger_donnees()

    def charger_donnees(self):
        """ Charge les véhicules depuis la base et les affiche """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        self.tree.delete(*self.tree.get_children())  # Vider le tableau avant rechargement
        vehicules = session.query(Vehicule).all()
        for v in vehicules:
            self.tree.insert("", END, values=(
                v.immatriculation, v.numero_chassis, v.numero_interne,
                v.marque_modele, v.type_vehicule, v.capacite_tonne, v.capacite_volume, v.etat
            ))

    def ajouter_vehicule(self):
        """ Ajoute un nouveau véhicule """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        immatriculation = simpledialog.askstring("Ajouter", "Immatriculation du véhicule :")
        if not immatriculation:
            return

        # Vérifier s'il existe déjà
        if session.query(Vehicule).filter_by(immatriculation=immatriculation).first():
            messagebox.showerror("Erreur", "Ce véhicule existe déjà.")
            return

        numero_chassis = simpledialog.askstring("Ajouter", "Numéro de châssis :")
        numero_interne = simpledialog.askstring("Ajouter", "Numéro interne :")
        marque_modele = simpledialog.askstring("Ajouter", "Marque et modèle :")
        type_vehicule = simpledialog.askstring("Ajouter", "Type de véhicule :")
        capacite_tonne = simpledialog.askfloat("Ajouter", "Capacité en tonnes :")
        capacite_volume = simpledialog.askfloat("Ajouter", "Capacité en m³ :")
        etat_mapping = {"p": "En panne", "s": "En service", "d": "Disponible"}
        etat_input = simpledialog.askstring("Ajouter", "État du véhicule (p=En panne, s=En service, d=Disponible) :")

        etat = etat_mapping.get(etat_input.lower(), etat_input)  # Convertir automatiquement si possible

        # Ajouter dans la base de données
        nouveau_vehicule = Vehicule(
            immatriculation=immatriculation,
            numero_chassis=numero_chassis,
            numero_interne=numero_interne,
            marque_modele=marque_modele,
            type_vehicule=type_vehicule,
            capacite_tonne=capacite_tonne,
            capacite_volume=capacite_volume,
            etat=etat
        )

        session.add(nouveau_vehicule)
        session.commit()

        # Mise à jour du tableau
        self.charger_donnees()
        messagebox.showinfo("Succès", "Véhicule ajouté avec succès !")

    def modifier_vehicule(self):
        """ Modifie un véhicule sélectionné """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un véhicule à modifier")
            return

        # Récupérer l'immatriculation
        item = self.tree.item(selected[0])
        immatriculation = item["values"][0]

        # Récupérer l'objet véhicule depuis la base
        vehicule = session.query(Vehicule).filter_by(immatriculation=immatriculation).first()

        if not vehicule:
            messagebox.showerror("Erreur", "Véhicule introuvable en base de données.")
            return

        # Modifier les valeurs avec des dialogues
        vehicule.numero_chassis = simpledialog.askstring("Modifier", "Numéro de châssis :", initialvalue=vehicule.numero_chassis)
        vehicule.numero_interne = simpledialog.askstring("Modifier", "Numéro interne :", initialvalue=vehicule.numero_interne)
        vehicule.marque_modele = simpledialog.askstring("Modifier", "Marque et modèle :", initialvalue=vehicule.marque_modele)
        vehicule.type_vehicule = simpledialog.askstring("Modifier", "Type de véhicule :", initialvalue=vehicule.type_vehicule)
        vehicule.capacite_tonne = simpledialog.askfloat("Modifier", "Capacité en tonnes :", initialvalue=vehicule.capacite_tonne)
        vehicule.capacite_volume = simpledialog.askfloat("Modifier", "Capacité en m³ :", initialvalue=vehicule.capacite_volume)
        etat_mapping = {"p": "En panne", "s": "En service", "d": "Disponible"}
        etat_input = simpledialog.askstring("Modifier", "État du véhicule (p=En panne, s=En service, d=Disponible) :", initialvalue=vehicule.etat)

        vehicule.etat = etat_mapping.get(etat_input.lower(), etat_input)  # Convertir automatiquement si possible

        session.commit()
        self.charger_donnees()
        messagebox.showinfo("Succès", "Véhicule modifié avec succès !")

    def supprimer_vehicule(self):
        """ Supprime un véhicule sélectionné """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un véhicule à supprimer")
            return

        item = self.tree.item(selected[0])
        immatriculation = item["values"][0]

        # Demander confirmation
        if not messagebox.askyesno("Confirmation", f"Voulez-vous supprimer le véhicule {immatriculation} ?"):
            return

        # Supprimer de la BDD
        session.query(Vehicule).filter_by(immatriculation=immatriculation).delete()
        session.commit()

        # Rafraîchir l'affichage
        self.charger_donnees()
        messagebox.showinfo("Succès", f"Véhicule {immatriculation} supprimé avec succès.")

    def afficher_total_parcouru(self):
        """ Affiche le total des kilomètres parcourus par le véhicule sélectionné """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un véhicule")
            return

        # Récupérer l'immatriculation
        item = self.tree.item(selected[0])
        immatriculation = item["values"][0]

        # Récupérer l'objet véhicule depuis la base
        vehicule = session.query(Vehicule).filter_by(immatriculation=immatriculation).first()

        if not vehicule:
            messagebox.showerror("Erreur", "Véhicule introuvable en base de données.")
            return

        # Calculer le total parcouru
        total_km = vehicule.calculer_total_parcouru(session)
        
        # Afficher le résultat
        messagebox.showinfo(
            "Total Parcouru", 
            f"Le véhicule {immatriculation} ({vehicule.marque_modele}) a parcouru un total de {total_km:.2f} km."
        )
        
    def affectation_tournee(self):
        """ Affecte le véhicule sélectionné à une tournée existante """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        from application.models.tournee import Tournee
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un véhicule")
            return

        # Récupérer l'immatriculation
        item = self.tree.item(selected[0])
        immatriculation = item["values"][0]

        # Récupérer l'objet véhicule depuis la base
        vehicule = session.query(Vehicule).filter_by(immatriculation=immatriculation).first()

        if not vehicule:
            messagebox.showerror("Erreur", "Véhicule introuvable en base de données.")
            return
            
        # Demander l'ID de la tournée
        id_tournee = simpledialog.askinteger("Affectation", "ID de la tournée :")
        if not id_tournee:
            return
            
        # Vérifier si la tournée existe
        tournee = session.query(Tournee).filter_by(id_tournee=id_tournee).first()
        if not tournee:
            messagebox.showerror("Erreur", f"Tournée avec ID {id_tournee} introuvable.")
            return
            
        # Affecter le véhicule à la tournée
        try:
            # Mise à jour de l'immatriculation du véhicule dans la tournée
            tournee.immatriculation_vehicule = immatriculation
            session.commit()
            messagebox.showinfo("Succès", f"Véhicule {immatriculation} affecté à la tournée {id_tournee}.")
        except Exception as e:
            session.rollback()
            messagebox.showerror("Erreur", f"Impossible d'affecter le véhicule à la tournée: {str(e)}")

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    root.title("Gestion des Véhicules")
    root.geometry("900x500")
    app = VehiculeApp(root)
    root.mainloop()