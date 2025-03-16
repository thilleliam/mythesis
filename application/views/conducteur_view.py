import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class ConducteurApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Conducteurs")
        self.root.geometry("800x500")
        
        # Import local pour éviter les imports circulaires
        from application.models.conducteurs import Conducteur
        self.Conducteur = Conducteur

        # Variables
        self.id_var = StringVar()
        self.nom_var = StringVar()
        self.prenom_var = StringVar()
        self.tel_var = StringVar()
        self.categorie_var = StringVar()
        self.dispo_var = StringVar(value="disponible")
        self.commentaire_var = StringVar()

        # Formulaire
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=X)

        ttk.Label(frame, text="ID Conducteur").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.id_var).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Nom").grid(row=0, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.nom_var).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Prénom").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.prenom_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Téléphone").grid(row=1, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.tel_var).grid(row=1, column=3, padx=5, pady=5)

        ttk.Label(frame, text="Catégorie").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.categorie_var).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Disponibilité").grid(row=2, column=2, padx=5, pady=5)
        self.dispo_cb = ttk.Combobox(frame, textvariable=self.dispo_var, values=["disponible", "conge", "autres"], state="readonly")
        self.dispo_cb.grid(row=2, column=3, padx=5, pady=5)
        self.dispo_cb.bind("<<ComboboxSelected>>", self.toggle_commentaire)

        ttk.Label(frame, text="Commentaire").grid(row=3, column=0, padx=5, pady=5)
        self.commentaire_entry = ttk.Entry(frame, textvariable=self.commentaire_var, state=DISABLED)
        self.commentaire_entry.grid(row=3, column=1, padx=5, pady=5, columnspan=3, sticky="ew")

        # Boutons
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=X)

        ttk.Button(btn_frame, text="Ajouter", command=self.ajouter, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.modifier, bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.supprimer, bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Total Conduite", command=self.afficher_total_parcouru, bootstyle=INFO).pack(side=LEFT, padx=5)

        # Tableau
        self.tree = ttk.Treeview(self.root, columns=("id", "nom", "prenom", "tel", "categorie", "disponibilite", "commentaire"), show="headings")
        self.tree.pack(fill=BOTH, expand=True)

        self.tree.heading("id", text="ID")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("prenom", text="Prénom")
        self.tree.heading("tel", text="Téléphone")
        self.tree.heading("categorie", text="Catégorie")
        self.tree.heading("disponibilite", text="Disponibilité")
        self.tree.heading("commentaire", text="Commentaire")

        self.tree.bind("<ButtonRelease-1>", self.selectionner)

        self.charger_donnees()

    def toggle_commentaire(self, event):
        if self.dispo_var.get() == "autres":
            self.commentaire_entry.config(state=NORMAL)
        else:
            self.commentaire_entry.config(state=DISABLED)
            self.commentaire_var.set("")

    def ajouter(self):
        conducteur = self.Conducteur(
            id_conducteur=self.id_var.get(),
            nom=self.nom_var.get(),
            prenom=self.prenom_var.get(),
            numero_telephone=self.tel_var.get(),
            categorie=self.categorie_var.get(),
            disponibilite=self.dispo_var.get(),
            commentaire_disponibilite=self.commentaire_var.get() if self.dispo_var.get() == "autres" else None
        )
        session.add(conducteur)
        session.commit()
        self.charger_donnees()
        self.vider_formulaire()

    def modifier(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un conducteur à modifier")
            return
        id_conducteur = self.tree.item(item, "values")[0]
        conducteur = session.query(self.Conducteur).filter_by(id_conducteur=id_conducteur).first()
        if conducteur:
            conducteur.nom = self.nom_var.get()
            conducteur.prenom = self.prenom_var.get()
            conducteur.numero_telephone = self.tel_var.get()
            conducteur.categorie = self.categorie_var.get()
            conducteur.disponibilite = self.dispo_var.get()
            conducteur.commentaire_disponibilite = self.commentaire_var.get() if self.dispo_var.get() == "autres" else None
            session.commit()
            self.charger_donnees()

    def supprimer(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un conducteur à supprimer")
            return
        id_conducteur = self.tree.item(item, "values")[0]
        session.query(self.Conducteur).filter_by(id_conducteur=id_conducteur).delete()
        session.commit()
        self.charger_donnees()

    def selectionner(self, event):
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            self.id_var.set(values[0])
            self.nom_var.set(values[1])
            self.prenom_var.set(values[2])
            self.tel_var.set(values[3])
            self.categorie_var.set(values[4])
            self.dispo_var.set(values[5])
            self.commentaire_var.set(values[6] if values[6] else "")
            self.toggle_commentaire(None)

    def charger_donnees(self):
        self.tree.delete(*self.tree.get_children())
        for conducteur in session.query(self.Conducteur).all():
            self.tree.insert("", END, values=(
                conducteur.id_conducteur, conducteur.nom, conducteur.prenom,
                conducteur.numero_telephone, conducteur.categorie, conducteur.disponibilite,
                conducteur.commentaire_disponibilite or ""
            ))

    def vider_formulaire(self):
        self.id_var.set("")
        self.nom_var.set("")
        self.prenom_var.set("")
        self.tel_var.set("")
        self.categorie_var.set("")
        self.dispo_var.set("disponible")
        self.commentaire_var.set("")
        self.toggle_commentaire(None)
        
    def total_parcouru(self, id_conducteur):
        from application.models.tournee import Tournee
        from application.database import SessionLocal
        session = SessionLocal()
        """ Calcule le total des kilomètres parcourus par le conducteur """
        total = session.query(func.sum(Tournee.km_parcouru)).filter(Tournee.id_conducteur == id_conducteur).scalar()
        return total or 0  # Retourne 0 si aucune donnée n'existe
    
    def afficher_total_parcouru(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez un conducteur pour afficher son total de kilomètres")
            return
        id_conducteur = self.tree.item(item, "values")[0]
        total_km = self.total_parcouru(id_conducteur)
        nom_prenom = f"{self.nom_var.get()} {self.prenom_var.get()}"
        messagebox.showinfo("Total Kilomètres", f"Le conducteur {nom_prenom} a parcouru un total de {total_km} kilomètres.")

if __name__ == "__main__":
    # Créer une fenêtre avec le thème darkly directement lors de l'initialisation
    root = ttk.Window(themename="darkly")
    app = ConducteurApp(root)
    root.mainloop()