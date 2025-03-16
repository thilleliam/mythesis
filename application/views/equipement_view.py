import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar, IntVar
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class EquipementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Équipements")
        self.root.geometry("800x500")
        
        # Import local pour éviter les imports circulaires
        from application.models.equipements import Equipement
        self.Equipement = Equipement

        # Variables
        self.id_var = IntVar()
        self.quantite_var = IntVar()
        self.nom_var = StringVar()
        self.type_var = StringVar()
        self.etat_var = StringVar(value="bon")

        # Formulaire
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=X)

        ttk.Label(frame, text="ID Équipement").grid(row=0, column=0, padx=5, pady=5)
        id_entry = ttk.Entry(frame, textvariable=self.id_var, state=DISABLED)
        id_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Nom Équipement").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.nom_var).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Quantité").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.quantite_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Type Équipement").grid(row=1, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.type_var).grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame, text="État").grid(row=2, column=0, padx=5, pady=5)
        self.etat_cb = ttk.Combobox(frame, textvariable=self.etat_var, values=["bon", "endommagé", "en maintenance", "hors service"], state="readonly")
        self.etat_cb.grid(row=2, column=1, padx=5, pady=5)

        # Boutons
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=X)

        ttk.Button(btn_frame, text="Ajouter", command=self.ajouter, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.modifier, bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.supprimer, bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Afficher Commandes", command=self.afficher_commandes, bootstyle=INFO).pack(side=LEFT, padx=5)

        # Tableau
        self.tree = ttk.Treeview(self.root, columns=("id", "nom", "quantite", "type", "etat"), show="headings")
        self.tree.pack(fill=BOTH, expand=True)

        self.tree.heading("id", text="ID")
        self.tree.heading("nom", text="Nom Équipement")
        self.tree.heading("quantite", text="Quantité")
        self.tree.heading("type", text="Type")
        self.tree.heading("etat", text="État")

        self.tree.column("id", width=50)
        self.tree.column("nom", width=200)
        self.tree.column("quantite", width=100)
        self.tree.column("type", width=200)
        self.tree.column("etat", width=150)

        self.tree.bind("<ButtonRelease-1>", self.selectionner)

        self.charger_donnees()

    def ajouter(self):
        equipement = self.Equipement(
            nomEquipement=self.nom_var.get(),
            quantite=self.quantite_var.get(),
            typeEquipement=self.type_var.get(),
            etat=self.etat_var.get()
        )
        session.add(equipement)
        session.commit()
        self.charger_donnees()
        self.vider_formulaire()

    def modifier(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un équipement à modifier")
            return
        id_equipement = self.tree.item(item, "values")[0]
        equipement = session.query(self.Equipement).filter_by(ID_equipement=id_equipement).first()
        if equipement:
            equipement.nomEquipement = self.nom_var.get()
            equipement.quantite = self.quantite_var.get()
            equipement.typeEquipement = self.type_var.get()
            equipement.etat = self.etat_var.get()
            session.commit()
            self.charger_donnees()

    def supprimer(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un équipement à supprimer")
            return
        id_equipement = self.tree.item(item, "values")[0]
        confirmation = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cet équipement?")
        if confirmation:
            session.query(self.Equipement).filter_by(ID_equipement=id_equipement).delete()
            session.commit()
            self.charger_donnees()

    def selectionner(self, event):
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            self.id_var.set(values[0])
            self.nom_var.set(values[1])
            self.quantite_var.set(values[2])
            self.type_var.set(values[3])
            self.etat_var.set(values[4])

    def charger_donnees(self):
        self.tree.delete(*self.tree.get_children())
        for equipement in session.query(self.Equipement).all():
            self.tree.insert("", END, values=(
                equipement.ID_equipement, equipement.nomEquipement, equipement.quantite,
                equipement.typeEquipement, equipement.etat
            ))

    def vider_formulaire(self):
        self.id_var.set(0)
        self.nom_var.set("")
        self.quantite_var.set(0)
        self.type_var.set("")
        self.etat_var.set("bon")
        
    def afficher_commandes(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un équipement pour afficher ses commandes")
            return
        id_equipement = self.tree.item(item, "values")[0]
        self.afficher_details_commandes(id_equipement)
        
    def afficher_details_commandes(self, id_equipement):
        from application.models.commandeequipement import CommandeEquipement
        from application.database import SessionLocal
        session = SessionLocal()
        
        commandes = session.query(CommandeEquipement).filter(CommandeEquipement.ID_equipement == id_equipement).all()
        
        if not commandes:
            messagebox.showinfo("Commandes", "Aucune commande pour cet équipement.")
            return
            
        # Créer une nouvelle fenêtre pour afficher les détails
        details_window = ttk.Toplevel(self.root)
        details_window.title("Détails des Commandes")
        details_window.geometry("600x400")
        
        # Créer un Treeview pour afficher les commandes
        details_tree = ttk.Treeview(details_window, columns=("id", "date", "quantite", "statut"), show="headings")
        details_tree.pack(fill=BOTH, expand=True)
        
        details_tree.heading("id", text="ID Commande")
        details_tree.heading("date", text="Date Commande")
        details_tree.heading("quantite", text="Quantité")
        details_tree.heading("statut", text="Statut")
        
        # Remplir le Treeview avec les données des commandes
        for commande in commandes:
            details_tree.insert("", END, values=(
                commande.id_commande,
                commande.date_commande.strftime("%d/%m/%Y") if commande.date_commande else "N/A",
                commande.quantite,
                commande.statut
            ))
        
        ttk.Button(details_window, text="Fermer", command=details_window.destroy).pack(pady=10)


if __name__ == "__main__":
    # Créer une fenêtre avec le thème darkly directement lors de l'initialisation
    root = ttk.Window(themename="darkly")
    app = EquipementApp(root)
    root.mainloop()