import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar
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

        # Création d'un panneau principal avec des onglets
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Onglet pour la liste des véhicules
        self.tab_liste = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_liste, text="Liste des Véhicules")
        
        # Onglet pour les statistiques (à venir)
        self.tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stats, text="Statistiques")
        
        # Barre de recherche
        search_frame = ttk.Frame(self.tab_liste)
        search_frame.pack(fill=X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="Recherche:").pack(side=LEFT, padx=5)
        self.search_var = StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", self.filtrer_vehicules)
        
        # Options de filtre
        self.filter_var = StringVar(value="Tous")
        filter_options = ["Tous", "En service", "En panne", "Disponible"]
        ttk.Label(search_frame, text="Filtrer par état:").pack(side=LEFT, padx=10)
        filter_menu = ttk.Combobox(search_frame, values=filter_options, textvariable=self.filter_var, width=15, state="readonly")
        filter_menu.pack(side=LEFT, padx=5)
        filter_menu.bind("<<ComboboxSelected>>", self.filtrer_vehicules)
        
        ttk.Button(search_frame, text="Réinitialiser", command=self.charger_donnees, bootstyle=SECONDARY).pack(side=RIGHT, padx=5)

        # Configuration du tableau avec scrollbars
        table_frame = ttk.Frame(self.tab_liste)
        table_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_frame, orient=VERTICAL)
        y_scrollbar.pack(side=RIGHT, fill=Y)
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient=HORIZONTAL)
        x_scrollbar.pack(side=BOTTOM, fill=X)

        # Création du tableau avec lien aux scrollbars
        self.tree = ttk.Treeview(
            table_frame,
            columns=("Immatriculation", "Châssis", "Interne", "Marque", "Type", "Tonnes", "Volume", "Etat"),
            show="headings",
            style="Treeview",
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # Configuration des scrollbars
        y_scrollbar.config(command=self.tree.yview)
        x_scrollbar.config(command=self.tree.xview)

        # Ajout des colonnes et en-têtes
        colonnes = [
            ("Immatriculation", "Immatriculation", 120),
            ("Châssis", "Numéro Châssis", 150),
            ("Interne", "Numéro Interne", 100),
            ("Marque", "Marque & Modèle", 180),
            ("Type", "Type", 120),
            ("Tonnes", "Capacité (T)", 80),
            ("Volume", "Capacité (m³)", 90),
            ("Etat", "État", 100)
        ]

        for col_id, col_name, col_width in colonnes:
            self.tree.heading(col_id, text=col_name, command=lambda c=col_id: self.trier_par_colonne(c))
            self.tree.column(col_id, width=col_width, anchor=CENTER, minwidth=50)

        # Alternance de couleurs pour les lignes
        self.tree.tag_configure('oddrow', background='#2b3e50')
        self.tree.tag_configure('evenrow', background='#344b61')
        
        # États de véhicule colorés
        self.tree.tag_configure('panne', foreground='#f39c12')
        self.tree.tag_configure('service', foreground='#3498db')
        self.tree.tag_configure('disponible', foreground='#2ecc71')

        self.tree.pack(fill=BOTH, expand=True)

        # Création d'une barre d'état en bas
        self.status_var = StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=SUNKEN, anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)

        # Boutons CRUD
        btn_frame = ttk.Frame(self.tab_liste)
        btn_frame.pack(fill=X, padx=10, pady=5)

        ttk.Button(btn_frame, text="Ajouter", command=self.ajouter_vehicule, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Modifier", command=self.modifier_vehicule, bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer", command=self.supprimer_vehicule, bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Total Parcourus", command=self.afficher_total_parcouru, bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Affectation", command=self.affectation_tournee, bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter", command=self.exporter_donnees, bootstyle=SECONDARY).pack(side=RIGHT, padx=5)
        
        # Double-clic pour modifier
        self.tree.bind("<Double-1>", lambda event: self.modifier_vehicule())
        
        # Configuration de l'onglet statistiques
        self.configurer_tab_stats()
        
        # Charger les données
        self.charger_donnees()

    def configurer_tab_stats(self):
        """Configure l'onglet des statistiques"""
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        # Nettoyer l'onglet stats avant de le reconfigurer
        for widget in self.tab_stats.winfo_children():
            widget.destroy()
            
        stats_frame = ttk.Frame(self.tab_stats, padding=20)
        stats_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(stats_frame, text="Statistiques de la Flotte", font=("-size", 16, "-weight", "bold")).pack(pady=10)
        
        # Compter les véhicules par état
        en_panne = session.query(func.count(Vehicule.immatriculation)).filter(Vehicule.etat == "En panne").scalar() or 0
        en_service = session.query(func.count(Vehicule.immatriculation)).filter(Vehicule.etat == "En service").scalar() or 0
        disponible = session.query(func.count(Vehicule.immatriculation)).filter(Vehicule.etat == "Disponible").scalar() or 0
        total = en_panne + en_service + disponible
        
        # Éviter la division par zéro
        panne_pct = (en_panne/total*100) if total > 0 else 0
        service_pct = (en_service/total*100) if total > 0 else 0
        dispo_pct = (disponible/total*100) if total > 0 else 0
        
        # Afficher les statistiques
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(fill=BOTH, expand=True, pady=20)
        
        # Stats par état
        etat_frame = ttk.Labelframe(stats_container, text="État des véhicules", padding=10)
        etat_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        ttk.Label(etat_frame, text=f"Total de véhicules: {total}").pack(anchor=W, pady=5)
        ttk.Label(etat_frame, text=f"En service: {en_service} ({service_pct:.1f}%)", 
                 foreground="#3498db").pack(anchor=W, pady=5)
        ttk.Label(etat_frame, text=f"En panne: {en_panne} ({panne_pct:.1f}%)", 
                 foreground="#f39c12").pack(anchor=W, pady=5)
        ttk.Label(etat_frame, text=f"Disponibles: {disponible} ({dispo_pct:.1f}%)", 
                 foreground="#2ecc71").pack(anchor=W, pady=5)
        
        # Stats par type
        types_frame = ttk.Labelframe(stats_container, text="Types de véhicules", padding=10)
        types_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        # Obtenir les types uniques et leur compte
        types_count = {}
        for v_type, count in session.query(Vehicule.type_vehicule, func.count(Vehicule.type_vehicule)).group_by(Vehicule.type_vehicule).all():
            if v_type:  # Éviter les valeurs None
                types_count[v_type] = count
        
        for v_type, count in types_count.items():
            ttk.Label(types_frame, text=f"{v_type}: {count} véhicules").pack(anchor=W, pady=5)
            
        # Raffraîchir les stats
        ttk.Button(stats_frame, text="Rafraîchir les statistiques", command=self.configurer_tab_stats, bootstyle=INFO).pack(pady=10)

    def charger_donnees(self):
        """ Charge les véhicules depuis la base et les affiche """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        self.tree.delete(*self.tree.get_children())  # Vider le tableau avant rechargement
        vehicules = session.query(Vehicule).all()
        
        # Remplir le tableau avec alternance de couleurs
        for idx, v in enumerate(vehicules):
            row_tags = ['oddrow' if idx % 2 else 'evenrow']
            
            # Ajouter un tag pour l'état
            if v.etat == "En panne":
                row_tags.append('panne')
            elif v.etat == "En service":
                row_tags.append('service')
            elif v.etat == "Disponible":
                row_tags.append('disponible')
                
            self.tree.insert("", END, values=(
                v.immatriculation, v.numero_chassis, v.numero_interne,
                v.marque_modele, v.type_vehicule, v.capacite_tonne, v.capacite_volume, v.etat
            ), tags=row_tags)
            
        # Mettre à jour la barre d'état
        self.status_var.set(f"Total: {len(vehicules)} véhicules")

    def trier_par_colonne(self, col):
        """ Trie le tableau par la colonne cliquée """
        # Récupérer toutes les lignes
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        
        # Trier les données (par texte)
        data.sort()
        
        # Réorganiser les lignes dans le tableau
        for idx, item in enumerate(data):
            self.tree.move(item[1], '', idx)
            
            # Mise à jour des tags pour l'alternance de couleurs
            current_tags = list(self.tree.item(item[1], "tags"))
            if 'oddrow' in current_tags:
                current_tags.remove('oddrow')
            if 'evenrow' in current_tags:
                current_tags.remove('evenrow')
                
            if idx % 2 == 0:
                current_tags.append('evenrow')
            else:
                current_tags.append('oddrow')
                
            self.tree.item(item[1], tags=current_tags)

    def filtrer_vehicules(self, event=None):
        """ Filtre les véhicules selon la recherche et le filtre d'état """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        search_term = self.search_var.get().lower()
        filter_state = self.filter_var.get()
        
        self.tree.delete(*self.tree.get_children())
        
        # Construire la requête
        query = session.query(Vehicule)
        
        # Appliquer le filtre d'état si nécessaire
        if filter_state != "Tous":
            query = query.filter(Vehicule.etat == filter_state)
            
        vehicules = query.all()
        count = 0
        
        # Appliquer le filtre de recherche et afficher les résultats
        for idx, v in enumerate(vehicules):
            # Vérifie si le terme de recherche est dans l'un des champs
            if (search_term in v.immatriculation.lower() or
                (v.numero_chassis and search_term in v.numero_chassis.lower()) or
                (v.numero_interne and search_term in v.numero_interne.lower()) or
                (v.marque_modele and search_term in v.marque_modele.lower()) or
                (v.type_vehicule and search_term in v.type_vehicule.lower())):
                
                row_tags = ['oddrow' if count % 2 else 'evenrow']
                
                # Ajouter un tag pour l'état
                if v.etat == "En panne":
                    row_tags.append('panne')
                elif v.etat == "En service":
                    row_tags.append('service')
                elif v.etat == "Disponible":
                    row_tags.append('disponible')
                    
                self.tree.insert("", END, values=(
                    v.immatriculation, v.numero_chassis, v.numero_interne,
                    v.marque_modele, v.type_vehicule, v.capacite_tonne, v.capacite_volume, v.etat
                ), tags=row_tags)
                count += 1
                
        # Mettre à jour la barre d'état
        self.status_var.set(f"Résultats: {count} véhicules")

    def ajouter_vehicule(self):
        """ Ajoute un nouveau véhicule avec une interface améliorée """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        # Créer une fenêtre de dialogue personnalisée
        dialog = ttk.Toplevel(self, resizable=False)
        dialog.title("Ajouter un véhicule")
        dialog.grab_set()  # Rendre modal
        
        # Créer un formulaire
        form_frame = ttk.Frame(dialog, padding=20)
        form_frame.pack(fill=BOTH, expand=True)
        
        # Variables pour stocker les entrées
        immat_var = StringVar()
        chassis_var = StringVar()
        interne_var = StringVar()
        marque_var = StringVar()
        type_var = StringVar()
        tonnes_var = StringVar()
        volume_var = StringVar()
        etat_var = StringVar(value="Disponible")
        
        # Créer les champs de saisie
        fields = [
            ("Immatriculation*:", immat_var),
            ("Numéro de châssis:", chassis_var),
            ("Numéro interne:", interne_var),
            ("Marque et modèle*:", marque_var),
            ("Type de véhicule*:", type_var),
            ("Capacité (tonnes)*:", tonnes_var),
            ("Capacité (m³)*:", volume_var),
        ]
        
        for i, (label_text, var) in enumerate(fields):
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky=W, pady=5, padx=5)
            ttk.Entry(form_frame, textvariable=var, width=40).grid(row=i, column=1, sticky=W, pady=5, padx=5)
        
        # Menu déroulant pour l'état
        ttk.Label(form_frame, text="État*:").grid(row=len(fields), column=0, sticky=W, pady=5, padx=5)
        ttk.Combobox(form_frame, textvariable=etat_var, values=["En panne", "En service", "Disponible"], 
                     state="readonly", width=15).grid(row=len(fields), column=1, sticky=W, pady=5, padx=5)
        
        # Label pour les champs obligatoires
        ttk.Label(form_frame, text="* Champs obligatoires", foreground="gray").grid(row=len(fields)+1, column=0, 
                                                                                   columnspan=2, sticky=W, pady=10)
        
        # Boutons
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=len(fields)+2, column=0, columnspan=2, pady=10)
        
        def valider():
            # Vérifier les champs obligatoires
            if not immat_var.get() or not marque_var.get() or not type_var.get():
                messagebox.showerror("Erreur", "Veuillez remplir tous les champs obligatoires.")
                return
                
            try:
                # Convertir les valeurs numériques
                capacite_tonne = float(tonnes_var.get()) if tonnes_var.get() else 0
                capacite_volume = float(volume_var.get()) if volume_var.get() else 0
                
                # Vérifier s'il existe déjà
                if session.query(Vehicule).filter_by(immatriculation=immat_var.get()).first():
                    messagebox.showerror("Erreur", "Ce véhicule existe déjà.")
                    return
                
                # Ajouter dans la base de données
                nouveau_vehicule = Vehicule(
                    immatriculation=immat_var.get(),
                    numero_chassis=chassis_var.get(),
                    numero_interne=interne_var.get(),
                    marque_modele=marque_var.get(),
                    type_vehicule=type_var.get(),
                    capacite_tonne=capacite_tonne,
                    capacite_volume=capacite_volume,
                    etat=etat_var.get()
                )
                
                session.add(nouveau_vehicule)
                session.commit()
                
                # Fermer la fenêtre et mise à jour
                dialog.destroy()
                self.charger_donnees()
                messagebox.showinfo("Succès", "Véhicule ajouté avec succès !")
                
            except ValueError:
                messagebox.showerror("Erreur", "Les capacités doivent être des nombres.")
            except Exception as e:
                session.rollback()
                messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")
                
        ttk.Button(btn_frame, text="Valider", command=valider, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=dialog.destroy, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

    def modifier_vehicule(self):
        """ Modifie un véhicule sélectionné avec une interface améliorée """
        # Import local pour éviter les références circulaires
        from application.models.vehicule import Vehicule
        
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un véhicule à modifier")
            return

        # Récupérer l'immatriculation
        item = self.tree.item(selected[0])
        immatriculation = item["values"][0]

        try:
            # Récupérer le véhicule directement sans créer de nouvelle session
            vehicule = session.query(Vehicule).filter_by(immatriculation=immatriculation).first()

            if not vehicule:
                messagebox.showerror("Erreur", "Véhicule introuvable en base de données.")
                return
                
            # Créer une fenêtre de dialogue personnalisée
            dialog = ttk.Toplevel(self, resizable=False)
            dialog.title(f"Modifier le véhicule: {immatriculation}")
            dialog.grab_set()  # Rendre modal
            
            # Créer un formulaire
            form_frame = ttk.Frame(dialog, padding=20)
            form_frame.pack(fill=BOTH, expand=True)
            
            # Variables pour stocker les entrées
            chassis_var = StringVar(value=vehicule.numero_chassis or "")
            interne_var = StringVar(value=vehicule.numero_interne or "")
            marque_var = StringVar(value=vehicule.marque_modele or "")
            type_var = StringVar(value=vehicule.type_vehicule or "")
            tonnes_var = StringVar(value=str(vehicule.capacite_tonne) if vehicule.capacite_tonne is not None else "")
            volume_var = StringVar(value=str(vehicule.capacite_volume) if vehicule.capacite_volume is not None else "")
            etat_var = StringVar(value=vehicule.etat or "Disponible")
            
            # Créer les champs de saisie
            fields = [
                ("Immatriculation:", StringVar(value=immatriculation), True),  # Lecture seule
                ("Numéro de châssis:", chassis_var, False),
                ("Numéro interne:", interne_var, False),
                ("Marque et modèle*:", marque_var, False),
                ("Type de véhicule*:", type_var, False),
                ("Capacité (tonnes)*:", tonnes_var, False),
                ("Capacité (m³)*:", volume_var, False),
            ]
            
            for i, (label_text, var, readonly) in enumerate(fields):
                ttk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky=W, pady=5, padx=5)
                entry = ttk.Entry(form_frame, textvariable=var, width=40, state="readonly" if readonly else "normal")
                entry.grid(row=i, column=1, sticky=W, pady=5, padx=5)
            
            # Menu déroulant pour l'état
            ttk.Label(form_frame, text="État*:").grid(row=len(fields), column=0, sticky=W, pady=5, padx=5)
            ttk.Combobox(form_frame, textvariable=etat_var, values=["En panne", "En service", "Disponible"], 
                         state="readonly", width=15).grid(row=len(fields), column=1, sticky=W, pady=5, padx=5)
            
            # Label pour les champs obligatoires
            ttk.Label(form_frame, text="* Champs obligatoires", foreground="gray").grid(row=len(fields)+1, column=0, 
                                                                                       columnspan=2, sticky=W, pady=10)
            
            # Boutons
            btn_frame = ttk.Frame(form_frame)
            btn_frame.grid(row=len(fields)+2, column=0, columnspan=2, pady=10)
            
            def valider():
                # Vérifier les champs obligatoires
                if not marque_var.get() or not type_var.get():
                    messagebox.showerror("Erreur", "Veuillez remplir tous les champs obligatoires.")
                    return
                    
                try:
                    # Convertir les valeurs numériques
                    capacite_tonne = float(tonnes_var.get()) if tonnes_var.get() else 0
                    capacite_volume = float(volume_var.get()) if volume_var.get() else 0
                    
                    # Mettre à jour le véhicule (utiliser la session existante)
                    vehicule.numero_chassis = chassis_var.get()
                    vehicule.numero_interne = interne_var.get()
                    vehicule.marque_modele = marque_var.get()
                    vehicule.type_vehicule = type_var.get()
                    vehicule.capacite_tonne = capacite_tonne
                    vehicule.capacite_volume = capacite_volume
                    vehicule.etat = etat_var.get()
                    
                    # Commit les changements
                    session.commit()
                    
                    # Fermer la fenêtre et mettre à jour l'affichage
                    dialog.destroy()
                    self.charger_donnees()
                    messagebox.showinfo("Succès", "Véhicule modifié avec succès !")
                        
                except ValueError:
                    messagebox.showerror("Erreur", "Les capacités doivent être des nombres.")
                except Exception as e:
                    session.rollback()
                    messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")
                    print(f"Erreur détaillée lors de la modification: {e}")
            
            ttk.Button(btn_frame, text="Valider", command=valider, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
            ttk.Button(btn_frame, text="Annuler", command=dialog.destroy, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
            
            # Centrer la fenêtre
            dialog.update_idletasks()
            width = dialog.winfo_width()
            height = dialog.winfo_height()
            x = (dialog.winfo_screenwidth() // 2) - (width // 2)
            y = (dialog.winfo_screenheight() // 2) - (height // 2)
            dialog.geometry(f"{width}x{height}+{x}+{y}")
    
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de modifier le véhicule: {str(e)}")
            print(f"Erreur détaillée: {e}")
            
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
        try:
            vehicule = session.query(Vehicule).filter_by(immatriculation=immatriculation).first()
            if not vehicule:
                messagebox.showerror("Erreur", "Véhicule introuvable en base de données.")
                return
                
            session.delete(vehicule)  # Méthode plus propre que .delete()
            session.commit()
            
            # Rafraîchir l'affichage
            self.charger_donnees()
            messagebox.showinfo("Succès", f"Véhicule {immatriculation} supprimé avec succès.")
        except Exception as e:
            session.rollback()
            messagebox.showerror("Erreur", f"Impossible de supprimer le véhicule: {str(e)}")

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
        
        # Créer une fenêtre détaillée
        dialog = ttk.Toplevel(self)
        dialog.title(f"Kilométrage - {immatriculation}")
        dialog.geometry("400x300")
        dialog.grab_set()  # Rendre modal
        
        # Mise en page
        content = ttk.Frame(dialog, padding=20)
        content.pack(fill=BOTH, expand=True)
        
        ttk.Label(content, text=f"Véhicule: {immatriculation}", font=("-size", 12, "-weight", "bold")).pack(anchor=W, pady=5)
        ttk.Label(content, text=f"Marque/Modèle: {vehicule.marque_modele}", font=("-size", 11)).pack(anchor=W, pady=3)
        ttk.Label(content, text=f"Type: {vehicule.type_vehicule}", font=("-size", 11)).pack(anchor=W, pady=3)
        
        # Ligne de séparation
        ttk.Separator(content, orient=HORIZONTAL).pack(fill=X, pady=10)
        
        # Kilométrage
        ttk.Label(content, text=f"TOTAL PARCOURU:", font=("-size", 12, "-weight", "bold")).pack(anchor=W, pady=5)
        ttk.Label(content, text=f"{total_km:.2f} kilomètres", 
                  font=("-size", 16, "-weight", "bold"), foreground="#3498db").pack(anchor=CENTER, pady=10)
                  
        # Informations complémentaires (si disponibles)
        try:
            # On pourrait ajouter ici des informations sur les dernières tournées
            from application.models.tournee import Tournee
            dernieres_tournees = session.query(Tournee).filter_by(immatriculation_vehicule=immatriculation).order_by(Tournee.date_tournee.desc()).limit(3)
            
            if dernieres_tournees.count() > 0:
                ttk.Label(content, text="Dernières tournées:", font=("-size", 11, "-weight", "bold")).pack(anchor=W, pady=5)
                for tournee in dernieres_tournees:
                    ttk.Label(content, text=f"• {tournee.date_tournee.strftime('%d/%m/%Y')} - {tournee.distance_parcourue} km").pack(anchor=W, pady=2)
        except:
            pass  # Si la table tournée n'existe pas ou n'a pas ces champs
            
        # Bouton de fermeture
        ttk.Button(content, text="Fermer", command=dialog.destroy, bootstyle=SECONDARY).pack(pady=10)
        
        # Centrer la fenêtre
        dialog.update_idletasks()
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2),
            self.winfo_rooty() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        ))
        
    def affectation_tournee(self):
        """ Affecte le véhicule sélectionné à une tournée existante avec interface améliorée """
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
            
        # Créer une fenêtre de dialogue personnalisée
        dialog = ttk.Toplevel(self)
        dialog.title(f"Affectation de tournée - {immatriculation}")
        dialog.geometry("600x400")
        dialog.grab_set()  # Rendre modal
        
        # Charger les tournées sans affectation
        tournees_dispo = session.query(Tournee).filter(
            (Tournee.immatriculation_vehicule == None) | 
            (Tournee.immatriculation_vehicule == "")
        ).all()
        
        # Mise en page
        content = ttk.Frame(dialog, padding=10)
        content.pack(fill=BOTH, expand=True)
        
        # Informations sur le véhicule
        info_frame = ttk.Frame(content)
        info_frame.pack(fill=X, pady=10)
        
        ttk.Label(info_frame, text=f"Véhicule: {immatriculation}", font=("-weight", "bold")).pack(side=LEFT)
        ttk.Label(info_frame, text=f" - {vehicule.marque_modele} - {vehicule.type_vehicule}").pack(side=LEFT)
        ttk.Label(info_frame, text=f"État: {vehicule.etat}", foreground=
                  "#f39c12" if vehicule.etat == "En panne" else 
                  "#3498db" if vehicule.etat == "En service" else 
                  "#2ecc71").pack(side=RIGHT)
                  
        # Message d'avertissement si le véhicule est en panne
        if vehicule.etat == "En panne":
            warning_frame = ttk.Frame(content)
            warning_frame.pack(fill=X, pady=5)
            ttk.Label(warning_frame, text="⚠️ Ce véhicule est actuellement en panne.", 
                      foreground="#f39c12", font=("-weight", "bold")).pack()
                
        # Liste des tournées disponibles
        liste_frame = ttk.Labelframe(content, text="Tournées disponibles", padding=10)
        liste_frame.pack(fill=BOTH, expand=True, pady=10)
        
        # Scrollbar pour la liste
        scroll_frame = ttk.Frame(liste_frame)
        scroll_frame.pack(fill=BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Créer la listbox avec les tournées
        tournee_var = StringVar()
        tournee_listbox = ttk.Treeview(
            scroll_frame, 
            columns=("ID", "Date", "Client", "Distance", "Ville"),
            show="headings",
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )
        
        # Configuration des colonnes
        tournee_listbox.heading("ID", text="ID")
        tournee_listbox.heading("Date", text="Date")
        tournee_listbox.heading("Client", text="Client")
        tournee_listbox.heading("Distance", text="Distance")
        tournee_listbox.heading("Ville", text="Destination")
        
        tournee_listbox.column("ID", width=40)
        tournee_listbox.column("Date", width=100)
        tournee_listbox.column("Client", width=150)
        tournee_listbox.column("Distance", width=80)
        tournee_listbox.column("Ville", width=120)
        
        tournee_listbox.pack(fill=BOTH, expand=True)
        scrollbar.config(command=tournee_listbox.yview)
        
        # Remplir la liste des tournées
        if tournees_dispo:
            for t in tournees_dispo:
                date_str = t.date_tournee.strftime("%d/%m/%Y") if hasattr(t, 'date_tournee') and t.date_tournee else "N/A"
                client = t.client if hasattr(t, 'client') and t.client else "N/A"
                distance = f"{t.distance_parcourue} km" if hasattr(t, 'distance_parcourue') and t.distance_parcourue else "N/A"
                ville = t.destination if hasattr(t, 'destination') and t.destination else "N/A"
                
                tournee_listbox.insert("", END, values=(t.id_tournee, date_str, client, distance, ville))
        else:
            tournee_listbox.insert("", END, values=("", "Aucune tournée disponible", "", "", ""))
        
        # Boutons d'action
        btn_frame = ttk.Frame(content)
        btn_frame.pack(fill=X, pady=10)
        
        ttk.Label(btn_frame, text="ID Tournée:").pack(side=LEFT, padx=5)
        id_tournee_var = StringVar()
        id_entry = ttk.Entry(btn_frame, textvariable=id_tournee_var, width=10)
        id_entry.pack(side=LEFT, padx=5)
        
        def selectionner_tournee(event):
            selected = tournee_listbox.selection()
            if selected:
                item = tournee_listbox.item(selected[0])
                id_tournee = item["values"][0]
                id_tournee_var.set(str(id_tournee))
                
        tournee_listbox.bind("<<TreeviewSelect>>", selectionner_tournee)
        
        def affecter():
            id_tournee = id_tournee_var.get().strip()
            if not id_tournee:
                messagebox.showwarning("Avertissement", "Veuillez sélectionner ou saisir un ID de tournée.")
                return
                
            try:
                id_tournee = int(id_tournee)
                tournee = session.query(Tournee).filter_by(id_tournee=id_tournee).first()
                
                if not tournee:
                    messagebox.showerror("Erreur", f"Tournée avec ID {id_tournee} introuvable.")
                    return
                    
                # Affecter le véhicule à la tournée
                tournee.immatriculation_vehicule = immatriculation
                session.commit()
                
                messagebox.showinfo("Succès", f"Véhicule {immatriculation} affecté à la tournée {id_tournee}.")
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Erreur", "L'ID de tournée doit être un nombre entier.")
            except Exception as e:
                session.rollback()
                messagebox.showerror("Erreur", f"Impossible d'affecter le véhicule à la tournée: {str(e)}")
        
        ttk.Button(btn_frame, text="Affecter", command=affecter, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=dialog.destroy, bootstyle=SECONDARY).pack(side=RIGHT, padx=5)

    def exporter_donnees(self):
        """ Exporte les données du tableau vers un fichier CSV ou Excel """
        import csv
        from tkinter import filedialog
        import os
        
        # Demander où enregistrer le fichier
        filetypes = [("Fichier CSV", "*.csv"), ("Fichier Excel", "*.xlsx")]
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=filetypes,
            title="Exporter les données"
        )
        
        if not filepath:
            return
            
        # Récupérer les en-têtes
        headers = []
        for col in self.tree["columns"]:
            headers.append(self.tree.heading(col)["text"])
            
        # Récupérer les données
        data = []
        for item_id in self.tree.get_children():
            values = self.tree.item(item_id)["values"]
            data.append(values)
            
        try:
            # Si c'est un fichier Excel
            if filepath.endswith('.xlsx'):
                try:
                    import pandas as pd
                    df = pd.DataFrame(data, columns=headers)
                    df.to_excel(filepath, index=False)
                except ImportError:
                    messagebox.showerror("Erreur", "Le module pandas n'est pas installé. Utilisez pip install pandas openpyxl")
                    return
            # Sinon CSV
            else:
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(data)
                    
            messagebox.showinfo("Succès", f"Données exportées avec succès vers:\n{os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'exportation: {str(e)}")

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    root.title("Gestion des Véhicules")
    root.geometry("1100x650")  # Taille de fenêtre augmentée
    app = VehiculeApp(root)
    root.mainloop() 