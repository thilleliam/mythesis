import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, StringVar
import pandas as pd
from application.models.transferer_equipement import TransfererEquipement, SemaineTransfert
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from sqlalchemy import func
from datetime import date, datetime

configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()

class TransfertEquipementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Planification des Transferts")
        self.root.geometry("1200x600")

        # Frame principale
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Frame pour les contrôles
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=X, pady=10)

        # Nombre de semaines
        ttk.Label(control_frame, text="Nombre de semaines :", font=("Arial", 12)).pack(side=LEFT, padx=5)
        self.entree_semaines = ttk.Entry(control_frame, width=5)
        self.entree_semaines.pack(side=LEFT, padx=5)
        self.entree_semaines.insert(0, "13")  # Valeur par défaut pour 13 semaines (0-12)

        # Boutons
        self.btn_generer = ttk.Button(control_frame, text="Générer", command=self.generer_tableau, bootstyle=SUCCESS)
        self.btn_generer.pack(side=LEFT, padx=10)

        self.btn_importer = ttk.Button(control_frame, text="Importer depuis Excel", command=self.importer_excel, bootstyle=INFO)
        self.btn_importer.pack(side=LEFT, padx=10)

        self.btn_exporter = ttk.Button(control_frame, text="Exporter vers Excel", command=self.exporter_excel, bootstyle=WARNING)
        self.btn_exporter.pack(side=LEFT, padx=10)

        self.btn_ajouter_ligne = ttk.Button(control_frame, text="Ajouter une ligne", command=self.ajouter_ligne, bootstyle=PRIMARY)
        self.btn_ajouter_ligne.pack(side=LEFT, padx=10)

        self.btn_supprimer_ligne = ttk.Button(control_frame, text="Supprimer la ligne", command=self.supprimer_ligne, bootstyle=DANGER)
        self.btn_supprimer_ligne.pack(side=LEFT, padx=10)

        self.btn_modifier_ligne = ttk.Button(control_frame, text="Modifier la ligne", command=self.modifier_ligne, bootstyle=SECONDARY)
        self.btn_modifier_ligne.pack(side=LEFT, padx=10)

        # Frame pour le tableau
        self.frame_tableau = ttk.Frame(main_frame)
        self.frame_tableau.pack(pady=10, fill=BOTH, expand=True)

        # Treeview (tableau)
        self.tree = None
        self.colonnes = []

        # Initialiser le tableau par défaut
        self.generer_tableau()

    def generer_tableau(self):
        """Génère dynamiquement les colonnes selon le nombre de semaines entrées."""
        try:
            nb_semaines = int(self.entree_semaines.get())
            if nb_semaines <= 0:
                messagebox.showerror("Erreur", "Le nombre de semaines doit être supérieur à 0.")
                return

            # Colonnes principales
            self.colonnes = [
                "Volet",
                "Désignation de l'équipement à transférer",
                "Modalité de transport (Tractable/Chargeable)",
                "Total des équipements à transférer"
            ]

            # Ajouter les colonnes pour chaque semaine
            for i in range(nb_semaines):
                semaine_num = nb_semaines - i - 1
                self.colonnes.append(f"{semaine_num:02d} semaines avant la fin de l'ancien projet")

            # Détruire l'ancien tableau s'il existe
            if self.tree:
                for widget in self.frame_tableau.winfo_children():
                    widget.destroy()

            # Scrollbars
            scroll_y = ttk.Scrollbar(self.frame_tableau, orient=VERTICAL)
            scroll_x = ttk.Scrollbar(self.frame_tableau, orient=HORIZONTAL)

            # Créer un nouveau tableau
            self.tree = ttk.Treeview(
                self.frame_tableau,
                columns=self.colonnes,
                show="headings",
                yscrollcommand=scroll_y.set,
                xscrollcommand=scroll_x.set
            )

            # Configurer les scrollbars
            scroll_y.config(command=self.tree.yview)
            scroll_y.pack(side=RIGHT, fill=Y)

            scroll_x.config(command=self.tree.xview)
            scroll_x.pack(side=BOTTOM, fill=X)

            # Configurer les colonnes
            for i, col in enumerate(self.colonnes):
                self.tree.heading(col, text=col)

                # Largeur adaptée selon le type de colonne
                if i < 3:  # Premières colonnes descriptives
                    self.tree.column(col, width=150, minwidth=100)
                elif i == 3:  # Colonne "Total"
                    self.tree.column(col, width=100, minwidth=80)
                else:  # Colonnes des semaines
                    self.tree.column(col, width=100, minwidth=80)
                    self.tree.heading(col, text=f"{col}\nQté à transférer")

            self.tree.pack(fill=BOTH, expand=True)

            # Charger les données depuis la base de données
            self.charger_donnees()

        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un nombre valide pour les semaines.")

    def charger_donnees(self):
        """Charge les données depuis la base de données et les affiche dans le tableau."""
        try:
            # Effacer le tableau actuel
            self.tree.delete(*self.tree.get_children())
            
            # Récupérer tous les équipements
            equipements = session.query(TransfererEquipement).all()
            
            for equipement in equipements:
                # Préparer les valeurs de base
                valeurs = [
                    equipement.volet or "",
                    equipement.designation_equipement or "",
                    equipement.modalite_transport or "",
                    equipement.total_equipements
                ]
                
                # Créer un dictionnaire des semaines pour cet équipement
                semaines_dict = {s.numero_semaine: s.quantite for s in equipement.semaines}
                
                # Pour chaque colonne de semaine dans le tableau
                for i in range(len(self.colonnes) - 4):  # -4 pour les 4 premières colonnes
                    # Obtenir le numéro de semaine à partir du nom de la colonne
                    col_name = self.colonnes[i+4]
                    try:
                        semaine_num = int(col_name.split()[0])
                        # Ajouter la quantité si disponible, sinon une chaîne vide
                        valeurs.append(semaines_dict.get(semaine_num, ""))
                    except (ValueError, IndexError):
                        valeurs.append("")  # En cas d'erreur, ajouter une chaîne vide
                
                # Insérer la ligne dans le tableau
                self.tree.insert("", "end", values=valeurs)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des données: {str(e)}")
            import traceback
            traceback.print_exc()

    def ajouter_ligne(self):
        """Ajoute une ligne vide au tableau puis ouvre une boîte de dialogue pour la remplir."""
        try:
            dialog = ttk.Toplevel(self.root)
            dialog.title("Ajouter un équipement à transférer")
            dialog.geometry("800x500")

            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

            # Canvas avec scrollbar
            canvas = tk.Canvas(main_frame)
            scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)

            # Champs pour les données principales
            ttk.Label(scrollable_frame, text="Volet").grid(row=0, column=0, sticky=W, padx=5, pady=5)
            volet_entry = ttk.Entry(scrollable_frame, width=50)
            volet_entry.grid(row=0, column=1, sticky=(W, E), padx=5, pady=5)

            ttk.Label(scrollable_frame, text="Désignation de l'équipement").grid(row=1, column=0, sticky=W, padx=5, pady=5)
            designation_entry = ttk.Entry(scrollable_frame, width=50)
            designation_entry.grid(row=1, column=1, sticky=(W, E), padx=5, pady=5)

            ttk.Label(scrollable_frame, text="Modalité de transport").grid(row=2, column=0, sticky=W, padx=5, pady=5)
            modalite_entry = ttk.Combobox(scrollable_frame, values=["Tractable", "Chargeable", "Tractage"])
            modalite_entry.grid(row=2, column=1, sticky=(W, E), padx=5, pady=5)

            ttk.Label(scrollable_frame, text="Total des équipements").grid(row=3, column=0, sticky=W, padx=5, pady=5)
            total_entry = ttk.Entry(scrollable_frame, width=50)
            total_entry.grid(row=3, column=1, sticky=(W, E), padx=5, pady=5)

            # Champs pour les semaines
            entries_semaine = []
            for i in range(4, len(self.colonnes)):
                ttk.Label(scrollable_frame, text=self.colonnes[i]).grid(row=i, column=0, sticky=W, padx=5, pady=5)
                entry = ttk.Entry(scrollable_frame, width=50)
                entry.grid(row=i, column=1, sticky=(W, E), padx=5, pady=5)
                entries_semaine.append((self.colonnes[i].split()[0], entry))

            def sauvegarder():
                try:
                    # Vérifier que les champs obligatoires sont remplis
                    if not designation_entry.get().strip():
                        messagebox.showerror("Erreur", "La désignation de l'équipement est obligatoire.")
                        return
                        
                    # Pour le total, utiliser 0 si vide
                    try:
                        total = int(total_entry.get() or 0)
                    except ValueError:
                        messagebox.showerror("Erreur", "Le total doit être un nombre entier.")
                        return
                    
                    # Créer un nouvel équipement
                    equipement = TransfererEquipement(
                        volet=volet_entry.get().strip(),
                        designation_equipement=designation_entry.get().strip(),
                        modalite_transport=modalite_entry.get().strip(),
                        total_equipements=total
                    )
                    session.add(equipement)
                    session.flush()

                    # Ajouter les semaines
                    for num_semaine, entry in entries_semaine:
                        quantite = entry.get().strip()
                        if quantite:
                            try:
                                quantite_int = int(quantite)
                                if quantite_int > 0:
                                    semaine = SemaineTransfert(
                                        id_equipement=equipement.id,
                                        numero_semaine=int(num_semaine),
                                        quantite=quantite_int
                                    )
                                    session.add(semaine)
                            except ValueError:
                                messagebox.showerror("Erreur", f"La quantité pour la semaine {num_semaine} doit être un nombre entier.")
                                session.rollback()
                                return

                    session.commit()
                    self.charger_donnees()
                    dialog.destroy()
                    messagebox.showinfo("Succès", "Équipement ajouté avec succès.")
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de l'ajout: {e}")
                    session.rollback()

            # Boutons
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill=X, pady=10)

            ttk.Button(btn_frame, text="Annuler", command=dialog.destroy, bootstyle=SECONDARY).pack(side=RIGHT, padx=5)
            ttk.Button(btn_frame, text="Sauvegarder", command=sauvegarder, bootstyle=SUCCESS).pack(side=RIGHT, padx=5)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture du formulaire: {e}")

    def supprimer_ligne(self):
        """Supprime la ligne sélectionnée du tableau."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner une ligne à supprimer.")
            return

        if messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cette ligne ?"):
            try:
                for item in selection:
                    values = self.tree.item(item, 'values')
                    volet = values[0]
                    designation = values[1]
                    
                    equipement = session.query(TransfererEquipement).filter_by(
                        volet=volet, 
                        designation_equipement=designation
                    ).first()
                    
                    if equipement:
                        session.query(SemaineTransfert).filter_by(id_equipement=equipement.id).delete()
                        session.delete(equipement)
                        session.commit()
                    
                    self.tree.delete(item)
                
                messagebox.showinfo("Succès", "Ligne(s) supprimée(s) avec succès.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression: {e}")
                session.rollback()

    def modifier_ligne(self):
        """Ouvre une fenêtre pour modifier la ligne sélectionnée."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner une ligne à modifier.")
            return

        item = selection[0]
        valeurs = self.tree.item(item, 'values')
        
        try:
            volet = valeurs[0]
            designation = valeurs[1]
            
            equipement = session.query(TransfererEquipement).filter_by(
                volet=volet, 
                designation_equipement=designation
            ).first()
            
            if not equipement:
                messagebox.showerror("Erreur", "Équipement non trouvé dans la base de données.")
                return
                
            dialog = ttk.Toplevel(self.root)
            dialog.title("Modifier la ligne")
            dialog.geometry("800x500")

            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

            canvas = tk.Canvas(main_frame)
            scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)

            ttk.Label(scrollable_frame, text="Volet").grid(row=0, column=0, sticky=W, padx=5, pady=5)
            volet_entry = ttk.Entry(scrollable_frame, width=50)
            volet_entry.grid(row=0, column=1, sticky=(W, E), padx=5, pady=5)
            volet_entry.insert(0, equipement.volet)

            ttk.Label(scrollable_frame, text="Désignation de l'équipement").grid(row=1, column=0, sticky=W, padx=5, pady=5)
            designation_entry = ttk.Entry(scrollable_frame, width=50)
            designation_entry.grid(row=1, column=1, sticky=(W, E), padx=5, pady=5)
            designation_entry.insert(0, equipement.designation_equipement)

            ttk.Label(scrollable_frame, text="Modalité de transport").grid(row=2, column=0, sticky=W, padx=5, pady=5)
            modalite_entry = ttk.Combobox(scrollable_frame, values=["Tractable", "Chargeable", "Tractage"])
            modalite_entry.grid(row=2, column=1, sticky=(W, E), padx=5, pady=5)
            modalite_entry.set(equipement.modalite_transport)

            ttk.Label(scrollable_frame, text="Total des équipements").grid(row=3, column=0, sticky=W, padx=5, pady=5)
            total_entry = ttk.Entry(scrollable_frame, width=50)
            total_entry.grid(row=3, column=1, sticky=(W, E), padx=5, pady=5)
            total_entry.insert(0, str(equipement.total_equipements))

            semaines_dict = {s.numero_semaine: s.quantite for s in equipement.semaines}
            
            entries_semaine = []
            for i in range(4, len(self.colonnes)):
                col = self.colonnes[i]
                num_semaine = int(col.split()[0])
                
                ttk.Label(scrollable_frame, text=col).grid(row=i, column=0, sticky=W, padx=5, pady=5)
                entry = ttk.Entry(scrollable_frame, width=50)
                entry.grid(row=i, column=1, sticky=(W, E), padx=5, pady=5)
                
                if num_semaine in semaines_dict:
                    entry.insert(0, str(semaines_dict[num_semaine]))
                
                entries_semaine.append((num_semaine, entry))

            def sauvegarder():
                try:
                    equipement.volet = volet_entry.get()
                    equipement.designation_equipement = designation_entry.get()
                    equipement.modalite_transport = modalite_entry.get()
                    equipement.total_equipements = int(total_entry.get() or 0)

                    session.query(SemaineTransfert).filter_by(id_equipement=equipement.id).delete()
                    
                    for num_semaine, entry in entries_semaine:
                        quantite = entry.get().strip()
                        if quantite:
                            semaine = SemaineTransfert(
                                id_equipement=equipement.id,
                                numero_semaine=num_semaine,
                                quantite=int(quantite)
                            )
                            session.add(semaine)

                    session.commit()
                    self.charger_donnees()
                    dialog.destroy()
                    messagebox.showinfo("Succès", "Équipement modifié avec succès.")
                except Exception as e:
                    messagebox.showerror("Erreur", f"Erreur lors de la modification: {e}")
                    session.rollback()

            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill=X, pady=10)

            ttk.Button(btn_frame, text="Annuler", command=dialog.destroy, bootstyle=SECONDARY).pack(side=RIGHT, padx=5)
            ttk.Button(btn_frame, text="Sauvegarder", command=sauvegarder, bootstyle=SUCCESS).pack(side=RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ouverture du formulaire: {e}")

    def importer_excel(self):
        """Importe les données depuis un fichier Excel."""
        fichier = filedialog.askopenfilename(filetypes=[("Fichiers Excel", "*.xlsx *.xls")])
        if not fichier: 
            return

        try:
            df = pd.read_excel(fichier, header=0)
            
            # Vérifier le format du fichier
            if len(df.columns) < 4:
                messagebox.showerror("Erreur", "Le fichier Excel doit contenir au moins 4 colonnes")
                return
                
            if not messagebox.askyesno("Confirmation", 
                                    "Cette action va remplacer toutes les données existantes. Continuer?"):
                return
            
            try:
                # Déterminer le nombre de semaines
                nb_semaines = len(df.columns) - 4
                if nb_semaines <= 0:
                    nb_semaines = 13
                    
                self.entree_semaines.delete(0, tk.END)
                self.entree_semaines.insert(0, str(nb_semaines))
                self.generer_tableau()
                
                # Vider les tables
                session.query(SemaineTransfert).delete()
                session.query(TransfererEquipement).delete()
                session.commit()
                
                importes = 0
                for idx, row in df.iterrows():
                    try:
                        # Ignorer les lignes vides ou les en-têtes
                        if pd.isna(row.iloc[0]) and pd.isna(row.iloc[1]):
                            continue
                            
                        if "volet" in str(row.iloc[0]).lower() or "désignation" in str(row.iloc[1]).lower():
                            continue
                        
                        # Récupérer les valeurs de base
                        volet = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                        designation = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
                        modalite = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
                        
                        # Gérer le total des équipements
                        try:
                            total_equipements = int(float(row.iloc[3])) if pd.notna(row.iloc[3]) else 0
                        except (ValueError, TypeError):
                            total_equipements = 0
                        
                        # Créer l'équipement
                        equipement = TransfererEquipement(
                            volet=volet.strip(),
                            designation_equipement=designation.strip(),
                            modalite_transport=modalite.strip(),
                            total_equipements=total_equipements
                        )
                        session.add(equipement)
                        session.flush()
                        
                        # Traiter les semaines
                        for i in range(4, min(len(df.columns), 4 + nb_semaines)):
                            # Extraire le numéro de semaine depuis l'en-tête
                            col_name = df.columns[i]
                            try:
                                # Gérer différents formats de noms de colonnes
                                if "semaine" in col_name.lower():
                                    parts = col_name.split()
                                    num_semaine = int(parts[0])
                                else:
                                    # Si le nom de colonne est juste un nombre
                                    num_semaine = int(col_name)
                            except (ValueError, IndexError):
                                # Si le format n'est pas reconnu, utiliser une position relative
                                num_semaine = nb_semaines - (i - 4) - 1
                            
                            val = row.iloc[i]
                            
                            if pd.notna(val) and str(val).strip():
                                try:
                                    quantite = int(float(val))
                                    if quantite > 0:
                                        semaine = SemaineTransfert(
                                            id_equipement=equipement.id,
                                            numero_semaine=num_semaine,
                                            quantite=quantite
                                        )
                                        session.add(semaine)
                                except (ValueError, TypeError):
                                    continue
                        
                        importes += 1
                        
                    except Exception as e:
                        print(f"Erreur ligne {idx}: {str(e)}")
                        continue
                        
                session.commit()
                self.charger_donnees()
                messagebox.showinfo("Succès", f"Données importées avec succès! {importes} équipements importés.")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Problème lors de l'importation: {str(e)}")
                session.rollback()
                import traceback
                traceback.print_exc()
        except Exception as e:
            messagebox.showerror("Erreur", f"Problème lors de la lecture du fichier Excel: {str(e)}")

    def exporter_excel(self):
        """Exporte les données du tableau vers un fichier Excel."""
        if not self.tree or len(self.tree.get_children()) == 0:
            messagebox.showinfo("Information", "Aucune donnée à exporter.")
            return

        fichier = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Fichiers Excel", "*.xlsx")]
        )

        if not fichier:
            return

        try:
            data = []
            for item_id in self.tree.get_children():
                values = self.tree.item(item_id)['values']
                data.append(values)

            df = pd.DataFrame(data, columns=self.colonnes)
            df.to_excel(fichier, index=False)

            messagebox.showinfo("Succès", "Données exportées avec succès !")
        except Exception as e:
            messagebox.showerror("Erreur", f"Problème lors de l'exportation : {e}")

if __name__ == "__main__":
    root = ttk.Window(themename="darkly")
    app = TransfertEquipementApp(root)
    root.mainloop()