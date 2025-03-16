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

class CommandeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Commandes")
        self.root.geometry("900x500")
        
        # Import local pour éviter les imports circulaires
        from application.models.commande import Commande
        self.Commande = Commande
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

        # Formulaire
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill=X)

        # Première ligne
        ttk.Label(frame, text="ID Commande").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.id_commande_var, state=DISABLED).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="ID Client").grid(row=0, column=2, padx=5, pady=5)
        self.client_cb = ttk.Combobox(frame, textvariable=self.id_client_var)
        self.client_cb.grid(row=0, column=3, padx=5, pady=5)

        # Deuxième ligne
        ttk.Label(frame, text="Nature Service").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.nature_service_var).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Type Véhicule").grid(row=1, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.type_vehicule_var).grid(row=1, column=3, padx=5, pady=5)

        # Troisième ligne
        ttk.Label(frame, text="Quantité Requise").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.quantite_requise_var).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Lieu Chargement").grid(row=2, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.lieu_chargement_var).grid(row=2, column=3, padx=5, pady=5)

        # Quatrième ligne
        ttk.Label(frame, text="Date Commande").grid(row=3, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.date_commande_var).grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Date Livraison").grid(row=3, column=2, padx=5, pady=5)
        ttk.Entry(frame, textvariable=self.date_livraison_var).grid(row=3, column=3, padx=5, pady=5)

        # Cinquième ligne
        ttk.Label(frame, text="ID Tournée").grid(row=4, column=0, padx=5, pady=5)
        self.tournee_cb = ttk.Combobox(frame, textvariable=self.id_tournee_var)
        self.tournee_cb.grid(row=4, column=1, padx=5, pady=5)

        # Boutons
        btn_frame = ttk.Frame(self.root, padding=10)
        btn_frame.pack(fill=X)

        ttk.Button(btn_frame, text="Ajouter", command=self.ajouter, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.modifier, bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.supprimer, bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Vérifier Retard", command=self.verifier_retard, bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Associer Tournée", command=self.associer_tournee, bootstyle=INFO).pack(side=LEFT, padx=5)

        # Tableau
        self.tree = ttk.Treeview(self.root, columns=(
            "id_commande", "id_client", "id_tournee", "nature_service", 
            "type_vehicule", "quantite_requise", "lieu_chargement", 
            "date_commande", "date_livraison"), show="headings")
        self.tree.pack(fill=BOTH, expand=True)

        self.tree.heading("id_commande", text="ID")
        self.tree.heading("id_client", text="Client")
        self.tree.heading("id_tournee", text="Tournée")
        self.tree.heading("nature_service", text="Service")
        self.tree.heading("type_vehicule", text="Véhicule")
        self.tree.heading("quantite_requise", text="Quantité")
        self.tree.heading("lieu_chargement", text="Lieu")
        self.tree.heading("date_commande", text="Date Commande")
        self.tree.heading("date_livraison", text="Date Livraison")

        # Configurer les largeurs des colonnes
        self.tree.column("id_commande", width=50)
        self.tree.column("id_client", width=50)
        self.tree.column("id_tournee", width=50)
        self.tree.column("nature_service", width=100)
        self.tree.column("type_vehicule", width=100)
        self.tree.column("quantite_requise", width=80)
        self.tree.column("lieu_chargement", width=100)
        self.tree.column("date_commande", width=100)
        self.tree.column("date_livraison", width=100)

        self.tree.bind("<ButtonRelease-1>", self.selectionner)

        # Chargement initial des données
        self.charger_clients()
        self.charger_tournees()
        self.charger_donnees()

    def charger_clients(self):
        from application.models.chantiers import Chantier
        self.Chantier = Chantier
        clients = session.query(self.Chantier).all()
        self.client_cb["values"] = [str(client.id_client) for client in clients]

    def charger_tournees(self):
        from application.models.tournee import Tournee
        self.Tournee = Tournee
        tournees = session.query(self.Tournee).all()
        self.tournee_cb["values"] = [str(tournee.id_tournee) for tournee in tournees]

    def ajouter(self):
        try:
            quantite = float(self.quantite_requise_var.get())
            date_commande = datetime.strptime(self.date_commande_var.get(), "%Y-%m-%d %H:%M:%S")
            date_livraison = datetime.strptime(self.date_livraison_var.get(), "%Y-%m-%d %H:%M:%S")
            
            id_tournee = self.id_tournee_var.get()
            if not id_tournee:
                id_tournee = None
            else:
                id_tournee = int(id_tournee)
                
            commande = self.Commande(
                id_client=int(self.id_client_var.get()),
                id_tournee=id_tournee,
                nature_service=self.nature_service_var.get(),
                type_vehicule=self.type_vehicule_var.get(),
                quantite_requise=quantite,
                lieu_chargement=self.lieu_chargement_var.get(),
                date_commande=date_commande,
                date_livraison=date_livraison
            )
            session.add(commande)
            session.commit()
            self.charger_donnees()
            self.vider_formulaire()
            messagebox.showinfo("Succès", "Commande ajoutée avec succès")
        except ValueError as e:
            messagebox.showerror("Erreur", f"Erreur de format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout: {str(e)}")

    def modifier(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande à modifier")
            return
        
        try:
            id_commande = int(self.tree.item(item, "values")[0])
            commande = session.query(self.Commande).filter_by(id_commande=id_commande).first()
            
            if commande:
                quantite = float(self.quantite_requise_var.get())
                date_commande = datetime.strptime(self.date_commande_var.get(), "%Y-%m-%d %H:%M:%S")
                date_livraison = datetime.strptime(self.date_livraison_var.get(), "%Y-%m-%d %H:%M:%S")
                
                id_tournee = self.id_tournee_var.get()
                if not id_tournee:
                    id_tournee = None
                else:
                    id_tournee = int(id_tournee)
                
                commande.id_client = int(self.id_client_var.get())
                commande.id_tournee = id_tournee
                commande.nature_service = self.nature_service_var.get()
                commande.type_vehicule = self.type_vehicule_var.get()
                commande.quantite_requise = quantite
                commande.lieu_chargement = self.lieu_chargement_var.get()
                commande.date_commande = date_commande
                commande.date_livraison = date_livraison
                
                session.commit()
                self.charger_donnees()
                messagebox.showinfo("Succès", "Commande modifiée avec succès")
        except ValueError as e:
            messagebox.showerror("Erreur", f"Erreur de format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la modification: {str(e)}")

    def supprimer(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande à supprimer")
            return
        
        if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cette commande?"):
            id_commande = int(self.tree.item(item, "values")[0])
            session.query(self.Commande).filter_by(id_commande=id_commande).delete()
            session.commit()
            self.charger_donnees()
            self.vider_formulaire()
            messagebox.showinfo("Succès", "Commande supprimée avec succès")

    def selectionner(self, event):
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            self.id_commande_var.set(values[0])
            self.id_client_var.set(values[1])
            self.id_tournee_var.set(values[2] if values[2] != "None" else "")
            self.nature_service_var.set(values[3])
            self.type_vehicule_var.set(values[4])
            self.quantite_requise_var.set(values[5])
            self.lieu_chargement_var.set(values[6])
            self.date_commande_var.set(values[7])
            self.date_livraison_var.set(values[8])

    def charger_donnees(self):

        self.tree.delete(*self.tree.get_children())
        for commande in session.query(self.Commande).all():
            self.tree.insert("", END, values=(
                commande.id_commande, 
                commande.id_client, 
                commande.nature_service, 
                commande.type_vehicule, 
                commande.quantite_requise,
                commande.lieu_chargement, 
                commande.date_commande, 
                commande.date_livraison
            ))

    def vider_formulaire(self):
        self.id_commande_var.set("")
        self.id_client_var.set("")
        self.id_tournee_var.set("")
        self.nature_service_var.set("")
        self.type_vehicule_var.set("")
        self.quantite_requise_var.set("")
        self.lieu_chargement_var.set("")
        self.date_commande_var.set("")
        self.date_livraison_var.set("")

    def verifier_retard(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande pour vérifier son état")
            return
        
        id_commande = int(self.tree.item(item, "values")[0])
        commande = session.query(self.Commande).filter_by(id_commande=id_commande).first()
        
        if commande:
            date_actuelle = datetime.now()
            est_en_retard = commande.est_en_retard(date_actuelle)
            
            if est_en_retard:
                messagebox.showwarning("Retard", f"La commande n°{id_commande} est en retard!")
            else:
                messagebox.showinfo("À temps", f"La commande n°{id_commande} n'est pas en retard.")

    def associer_tournee(self):
    # La classe Tournee est déjà importée dans la méthode charger_tournees
    # Vous n'avez pas besoin de l'importer à nouveau
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande pour l'associer à une tournée")
            return  # Ajoutez un return ici pour éviter d'exécuter le reste de la fonction
            
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
                    messagebox.showinfo("Succès", f"Commande n°{id_commande} associée à la tournée n°{id_tournee}")
                else:
                    messagebox.showerror("Erreur", f"La tournée n°{id_tournee} n'existe pas")
    def calculer_delai_livraison(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande pour calculer son délai de livraison")
            return
        
        try:
            distance = simpledialog.askfloat("Délai de livraison", "Entrez la distance en km:")
            if distance is None:
                return
                
            id_commande = int(self.tree.item(item, "values")[0])
            commande = session.query(self.Commande).filter_by(id_commande=id_commande).first()
            
            if commande:
                poids = commande.quantite_requise
                delai = commande.calculer_delai_livraison(distance, poids)
                messagebox.showinfo("Délai de livraison", 
                                    f"Le délai estimé est de {delai:.2f} heures pour la commande n°{id_commande}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul: {str(e)}")

    def afficher_details_client(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une commande pour voir les détails du client")
            return
        
        id_client = int(self.tree.item(item, "values")[1])
        client = session.query(self.Chantier).filter_by(id_client=id_client).first()
        
        if client:
            details = f"ID: {client.id_client}\n"
            details += f"Nom: {client.nom_client}\n"
            details += f"Adresse: {client.adresse_client}\n"
            details += f"Téléphone: {client.telephone_client}\n"
            
            messagebox.showinfo(f"Détails du client", details)
        else:
            messagebox.showinfo("Information", "Client non trouvé")

    def recherche_avancee(self):
        """Permet une recherche avancée des commandes selon différents critères"""
        search_window = ttk.Toplevel(self.root)
        search_window.title("Recherche Avancée")
        search_window.geometry("400x300")
        
        # Variables de recherche
        client_var = StringVar()
        date_debut_var = StringVar()
        date_fin_var = StringVar()
        type_vehicule_var = StringVar()
        
        # Formulaire de recherche
        frame = ttk.Frame(search_window, padding=10)
        frame.pack(fill=X)
        
        ttk.Label(frame, text="ID Client").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=client_var).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Date Début (YYYY-MM-DD)").grid(row=1, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=date_debut_var).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Date Fin (YYYY-MM-DD)").grid(row=2, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=date_fin_var).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Type Véhicule").grid(row=3, column=0, padx=5, pady=5)
        ttk.Entry(frame, textvariable=type_vehicule_var).grid(row=3, column=1, padx=5, pady=5)
        
        # Bouton de recherche
        def executer_recherche():
            query = session.query(self.Commande)
            
            if client_var.get():
                query = query.filter(self.Commande.id_client == int(client_var.get()))
            
            if date_debut_var.get():
                date_debut = datetime.strptime(date_debut_var.get(), "%Y-%m-%d")
                query = query.filter(self.Commande.date_commande >= date_debut)
            
            if date_fin_var.get():
                date_fin = datetime.strptime(date_fin_var.get(), "%Y-%m-%d")
                query = query.filter(self.Commande.date_commande <= date_fin)
            
            if type_vehicule_var.get():
                query = query.filter(self.Commande.type_vehicule == type_vehicule_var.get())
            
            # Actualiser le tableau avec les résultats
            self.tree.delete(*self.tree.get_children())
            for commande in query.all():
                self.tree.insert("", END, values=(
                    commande.id_commande, 
                    commande.id_client, 
                    commande.id_tournee,
                    commande.nature_service, 
                    commande.type_vehicule, 
                    commande.quantite_requise,
                    commande.lieu_chargement, 
                    commande.date_commande, 
                    commande.date_livraison
                ))
            
            search_window.destroy()
            
        ttk.Button(frame, text="Rechercher", command=executer_recherche, bootstyle=PRIMARY).grid(row=4, column=0, columnspan=2, pady=10)

if __name__ == "__main__":
    # Créer une fenêtre avec le thème darkly directement lors de l'initialisation
    root = ttk.Window(themename="darkly")
    app = CommandeApp(root)
    root.mainloop()