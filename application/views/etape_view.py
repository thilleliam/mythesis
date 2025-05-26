import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, StringVar, IntVar, BooleanVar
from tkinter import filedialog
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import engine
from datetime import datetime
import csv
import json

configure_mappers()
Session = sessionmaker(bind=engine)
session = Session()

from application.models.etape import EtapeRotation
from application.models.tournee import Tournee

class EtapeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🚐 Gestion des Étapes de Tournée - Version Améliorée")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Style moderne avec gestion d'erreur
        try:
            style = ttk.Style("cosmo")
        except:
            style = ttk.Style()  # Style par défaut si cosmo non disponible
        
        # Variables
        self.id_etape_var = StringVar()
        self.id_tournee_var = StringVar()
        self.nom_var = StringVar()
        self.description_var = StringVar()
        self.date_etape_var = StringVar()
        self.heure_var = StringVar(value="08:00")
        self.duree_var = IntVar(value=60)  # durée en minutes
        self.priorite_var = StringVar(value="Normale")
        self.statut_var = StringVar(value="Planifiée")
        self.filtre_var = StringVar()
        self.filtre_tournee_var = StringVar(value="Toutes")
        self.filtre_statut_var = StringVar(value="Tous")
        
        self.mode_edition = False
        
        try:
            self.setup_ui()
            self.charger_tournees()
            self.charger_donnees()
        except Exception as e:
            messagebox.showerror("Erreur d'initialisation", f"Erreur lors de l'initialisation: {str(e)}")
            print(f"Erreur détaillée: {e}")

    def setup_ui(self):
        # Menu principal
        self.create_menu()
        
        # Frame principal avec notebook
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Notebook pour organiser les onglets
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True)
        
        # Onglet principal - Gestion
        self.tab_gestion = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_gestion, text="📋 Gestion des Étapes")
        
        # Onglet statistiques
        self.tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stats, text="📊 Statistiques")
        
        self.setup_gestion_tab()
        self.setup_stats_tab()

    def create_menu(self):
        try:
            menubar = ttk.Menu(self.root)
            self.root.config(menu=menubar)
            
            # Menu Fichier
            file_menu = ttk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Fichier", menu=file_menu)
            file_menu.add_command(label="Exporter CSV", command=self.exporter_csv)
            file_menu.add_command(label="Importer CSV", command=self.importer_csv)
            file_menu.add_separator()
            file_menu.add_command(label="Quitter", command=self.root.quit)
            
            # Menu Outils
            tools_menu = ttk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Outils", menu=tools_menu)
            tools_menu.add_command(label="Actualiser", command=self.actualiser)
            tools_menu.add_command(label="Vider formulaire", command=self.vider_formulaire)
            
            # Menu Aide
            help_menu = ttk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Aide", menu=help_menu)
            help_menu.add_command(label="Guide d'utilisation", command=self.aide)
            help_menu.add_command(label="À propos", command=self.a_propos)
        except Exception as e:
            print(f"Erreur création menu: {e}")

    def setup_gestion_tab(self):
        # Frame pour les filtres
        filter_frame = ttk.LabelFrame(self.tab_gestion, text="🔍 Filtres et Recherche", padding=10)
        filter_frame.pack(fill=X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Recherche:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        ttk.Entry(filter_frame, textvariable=self.filtre_var, width=25).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Tournée:").grid(row=0, column=2, padx=5, pady=5, sticky=W)
        self.filtre_tournee_cb = ttk.Combobox(filter_frame, textvariable=self.filtre_tournee_var, width=15)
        self.filtre_tournee_cb.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Statut:").grid(row=0, column=4, padx=5, pady=5, sticky=W)
        self.filtre_statut_cb = ttk.Combobox(filter_frame, textvariable=self.filtre_statut_var, 
                                           values=["Tous", "Planifiée", "En cours", "Terminée", "Annulée"], width=12)
        self.filtre_statut_cb.grid(row=0, column=5, padx=5, pady=5)
        
        ttk.Button(filter_frame, text="🔍 Filtrer", command=self.appliquer_filtres, 
                  bootstyle=INFO, width=12).grid(row=0, column=6, padx=5, pady=5)
        ttk.Button(filter_frame, text="🗑️ Effacer", command=self.effacer_filtres, 
                  bootstyle=SECONDARY, width=12).grid(row=0, column=7, padx=5, pady=5)

        # Container principal
        main_container = ttk.PanedWindow(self.tab_gestion, orient=HORIZONTAL)
        main_container.pack(fill=BOTH, expand=True, padx=5, pady=5)

        # Frame gauche - Formulaire
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=1)
        
        self.setup_form(left_frame)

        # Frame droite - Tableau
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=2)
        
        self.setup_table(right_frame)

    def setup_form(self, parent):
        # Formulaire amélioré
        form_frame = ttk.LabelFrame(parent, text="📝 Informations de l'étape", padding=15)
        form_frame.pack(fill=BOTH, expand=True, padx=5)

        # ID Étape
        ttk.Label(form_frame, text="ID Étape:").grid(row=0, column=0, padx=5, pady=8, sticky=W)
        ttk.Entry(form_frame, textvariable=self.id_etape_var, state=DISABLED, width=15).grid(row=0, column=1, padx=5, pady=8, sticky=W+E)

        # Tournée
        ttk.Label(form_frame, text="Tournée:").grid(row=1, column=0, padx=5, pady=8, sticky=W)
        self.tournee_cb = ttk.Combobox(form_frame, textvariable=self.id_tournee_var, width=20)
        self.tournee_cb.grid(row=1, column=1, padx=5, pady=8, sticky=W+E)

        # Nom étape
        ttk.Label(form_frame, text="Nom étape:").grid(row=2, column=0, padx=5, pady=8, sticky=W)
        ttk.Entry(form_frame, textvariable=self.nom_var, width=25).grid(row=2, column=1, padx=5, pady=8, sticky=W+E)

        # Description
        ttk.Label(form_frame, text="Description:").grid(row=3, column=0, padx=5, pady=8, sticky=NW)
        desc_text = ttk.Text(form_frame, height=3, width=25)
        desc_text.grid(row=3, column=1, padx=5, pady=8, sticky=W+E)
        self.desc_text = desc_text

        # Date
        ttk.Label(form_frame, text="Date (YYYY-MM-DD):").grid(row=4, column=0, padx=5, pady=8, sticky=W)
        ttk.Entry(form_frame, textvariable=self.date_etape_var, width=12).grid(row=4, column=1, padx=5, pady=8, sticky=W)

        # Heure
        ttk.Label(form_frame, text="Heure:").grid(row=5, column=0, padx=5, pady=8, sticky=W)
        ttk.Entry(form_frame, textvariable=self.heure_var, width=10).grid(row=5, column=1, padx=5, pady=8, sticky=W)

        # Durée estimée
        ttk.Label(form_frame, text="Durée (min):").grid(row=6, column=0, padx=5, pady=8, sticky=W)
        ttk.Spinbox(form_frame, from_=15, to=480, textvariable=self.duree_var, width=10).grid(row=6, column=1, padx=5, pady=8, sticky=W)

        # Priorité
        ttk.Label(form_frame, text="Priorité:").grid(row=7, column=0, padx=5, pady=8, sticky=W)
        ttk.Combobox(form_frame, textvariable=self.priorite_var, 
                    values=["Faible", "Normale", "Élevée", "Urgente"], width=15).grid(row=7, column=1, padx=5, pady=8, sticky=W)

        # Statut
        ttk.Label(form_frame, text="Statut:").grid(row=8, column=0, padx=5, pady=8, sticky=W)
        ttk.Combobox(form_frame, textvariable=self.statut_var, 
                    values=["Planifiée", "En cours", "Terminée", "Annulée"], width=15).grid(row=8, column=1, padx=5, pady=8, sticky=W)

        # Boutons d'action
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=20, sticky=W+E)

        ttk.Button(btn_frame, text="➕ Ajouter", command=self.ajouter, 
                  bootstyle=SUCCESS, width=15).pack(pady=5, fill=X)
        ttk.Button(btn_frame, text="✏️ Modifier", command=self.modifier, 
                  bootstyle=WARNING, width=15).pack(pady=2, fill=X)
        ttk.Button(btn_frame, text="🗑️ Supprimer", command=self.supprimer, 
                  bootstyle=DANGER, width=15).pack(pady=2, fill=X)
        ttk.Button(btn_frame, text="🧹 Vider", command=self.vider_formulaire, 
                  bootstyle=SECONDARY, width=15).pack(pady=2, fill=X)

        # Configuration des colonnes pour le redimensionnement
        form_frame.columnconfigure(1, weight=1)

    def setup_table(self, parent):
        # Tableau amélioré
        table_frame = ttk.LabelFrame(parent, text="📊 Liste des Étapes", padding=10)
        table_frame.pack(fill=BOTH, expand=True, padx=5)

        # Frame pour les boutons au-dessus du tableau
        top_btn_frame = ttk.Frame(table_frame)
        top_btn_frame.pack(fill=X, pady=(0, 10))
        
        ttk.Button(top_btn_frame, text="🔄 Actualiser", command=self.charger_donnees, 
                  bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(top_btn_frame, text="📤 Exporter", command=self.exporter_csv, 
                  bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        
        # Compteur d'éléments
        self.count_label = ttk.Label(top_btn_frame, text="Total: 0 étapes")
        self.count_label.pack(side=RIGHT, padx=5)

        # Treeview avec scrollbars
        tree_container = ttk.Frame(table_frame)
        tree_container.pack(fill=BOTH, expand=True)

        self.tree = ttk.Treeview(tree_container, columns=("id_etape", "id_tournee", "nom", "description", 
                                                        "date_etape", "heure", "duree", "priorite", "statut"), 
                               show="headings", height=15)
        
        # Configuration des colonnes
        columns_config = {
            "id_etape": ("ID", 60),
            "id_tournee": ("Tournée", 80),
            "nom": ("Nom", 150),
            "description": ("Description", 200),
            "date_etape": ("Date", 100),
            "heure": ("Heure", 80),
            "duree": ("Durée", 80),
            "priorite": ("Priorité", 80),
            "statut": ("Statut", 100)
        }
        
        for col, (text, width) in columns_config.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.trier_colonne(c))
            self.tree.column(col, width=width, minwidth=50)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient=VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_container, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Placement
        self.tree.grid(row=0, column=0, sticky=NSEW)
        v_scrollbar.grid(row=0, column=1, sticky=NS)
        h_scrollbar.grid(row=1, column=0, sticky=EW)

        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        # Binding pour sélection
        self.tree.bind("<Double-1>", self.selectionner)
        self.tree.bind("<Button-3>", self.menu_contextuel)  # Clic droit

    def setup_stats_tab(self):
        stats_frame = ttk.LabelFrame(self.tab_stats, text="📈 Statistiques des Étapes", padding=20)
        stats_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Conteneur pour les métriques
        metrics_frame = ttk.Frame(stats_frame)
        metrics_frame.pack(fill=X, pady=10)
        
        # Métriques en cards
        self.create_metric_card(metrics_frame, "Total Étapes", "0", SUCCESS, 0, 0)
        self.create_metric_card(metrics_frame, "En Cours", "0", WARNING, 0, 1)
        self.create_metric_card(metrics_frame, "Terminées", "0", INFO, 0, 2)
        self.create_metric_card(metrics_frame, "Planifiées", "0", PRIMARY, 1, 0)
        self.create_metric_card(metrics_frame, "Annulées", "0", DANGER, 1, 1)
        self.create_metric_card(metrics_frame, "Durée Moy.", "0 min", SECONDARY, 1, 2)

    def create_metric_card(self, parent, title, value, style, row, col):
        card = ttk.Frame(parent, bootstyle=style)
        card.grid(row=row, column=col, padx=10, pady=10, sticky=NSEW)
        
        ttk.Label(card, text=title, font=("Arial", 10)).pack(pady=5)
        label = ttk.Label(card, text=value, font=("Arial", 14, "bold"))
        label.pack(pady=5)
        
        # Stocker la référence pour mise à jour
        setattr(self, f"metric_{title.lower().replace(' ', '_')}", label)
        
        parent.rowconfigure(row, weight=1)
        parent.columnconfigure(col, weight=1)

    def charger_tournees(self):
        try:
            tournees = session.query(Tournee).all()
            values = [f"{t.id_tournee} - {getattr(t, 'nom', f'Tournée {t.id_tournee}')}" for t in tournees]
            self.tournee_cb["values"] = values
            
            # Pour les filtres
            filter_values = ["Toutes"] + values
            self.filtre_tournee_cb["values"] = filter_values
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des tournées: {str(e)}")

    def charger_donnees(self):
        try:
            self.tree.delete(*self.tree.get_children())
            etapes = session.query(EtapeRotation).all()
            
            for etape in etapes:
                # Traitement des données pour l'affichage
                priorite = getattr(etape, 'priorite', 'Normale')
                statut = getattr(etape, 'statut', 'Planifiée')
                date_str = getattr(etape, 'date_etape', '')
                if isinstance(date_str, datetime):
                    date_str = date_str.strftime("%Y-%m-%d")
                
                values = (
                    etape.id_etape,
                    etape.id_tournee,
                    getattr(etape, 'nom', ''),
                    getattr(etape, 'description', ''),
                    date_str,
                    getattr(etape, 'heure', ''),
                    getattr(etape, 'duree', ''),
                    priorite,
                    statut
                )
                
                # Coloration selon le statut
                item = self.tree.insert("", "end", values=values)
                if statut == "Terminée":
                    self.tree.set(item, "statut", "✅ Terminée")
                elif statut == "En cours":
                    self.tree.set(item, "statut", "🔄 En cours")
                elif statut == "Annulée":
                    self.tree.set(item, "statut", "❌ Annulée")
                else:
                    self.tree.set(item, "statut", "📋 Planifiée")
            
            # Mise à jour du compteur
            count = len(etapes)
            self.count_label.config(text=f"Total: {count} étapes")
            
            # Mise à jour des statistiques
            self.mettre_a_jour_stats()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {str(e)}")

    def mettre_a_jour_stats(self):
        try:
            etapes = session.query(EtapeRotation).all()
            total = len(etapes)
            
            # Compteurs par statut
            statuts = {}
            durees = []
            
            for etape in etapes:
                statut = getattr(etape, 'statut', 'Planifiée')
                statuts[statut] = statuts.get(statut, 0) + 1
                
                duree = getattr(etape, 'duree', 0)
                if duree and duree > 0:
                    durees.append(duree)
            
            # Mise à jour des métriques
            self.metric_total_étapes.config(text=str(total))
            self.metric_en_cours.config(text=str(statuts.get('En cours', 0)))
            self.metric_terminées.config(text=str(statuts.get('Terminée', 0)))
            self.metric_planifiées.config(text=str(statuts.get('Planifiée', 0)))
            self.metric_annulées.config(text=str(statuts.get('Annulée', 0)))
            
            duree_moy = sum(durees) / len(durees) if durees else 0
            self.metric_durée_moy.config(text=f"{duree_moy:.0f} min")
            
        except Exception as e:
            print(f"Erreur stats: {e}")

    def ajouter(self):
        try:
            # Validation des champs
            if not self.nom_var.get().strip():
                messagebox.showwarning("Attention", "Le nom de l'étape est requis")
                return
            
            if not self.id_tournee_var.get():
                messagebox.showwarning("Attention", "Veuillez sélectionner une tournée")
                return
            
            # Extraction de l'ID tournée
            id_tournee = int(self.id_tournee_var.get().split(' - ')[0])
            
            # Construction de la date/heure
            date_etape = None
            if self.date_etape_var.get() and self.heure_var.get():
                date_str = self.date_etape_var.get()
                heure_str = self.heure_var.get()
                try:
                    date_etape = datetime.strptime(f"{date_str} {heure_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    messagebox.showwarning("Attention", "Format de date/heure invalide (YYYY-MM-DD HH:MM)")
                    return
            
            # Création de l'étape
            etape = EtapeRotation(
                id_tournee=id_tournee,
                nom=self.nom_var.get().strip(),
                description=self.desc_text.get("1.0", "end-1c").strip(),
                date_etape=date_etape,
                heure=self.heure_var.get(),
                duree=self.duree_var.get(),
                priorite=self.priorite_var.get(),
                statut=self.statut_var.get()
            )
            
            session.add(etape)
            session.commit()
            self.charger_donnees()
            self.vider_formulaire()
            messagebox.showinfo("✅ Succès", "Étape ajoutée avec succès!")
            
        except Exception as e:
            session.rollback()
            messagebox.showerror("❌ Erreur", f"Erreur lors de l'ajout: {str(e)}")

    def modifier(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une étape à modifier")
            return
        
        try:
            id_etape = int(self.tree.item(item, "values")[0])
            etape = session.query(EtapeRotation).filter_by(id_etape=id_etape).first()
            
            if etape:
                # Mise à jour des attributs
                id_tournee = int(self.id_tournee_var.get().split(' - ')[0])
                etape.id_tournee = id_tournee
                etape.nom = self.nom_var.get().strip()
                etape.description = self.desc_text.get("1.0", "end-1c").strip()
                
                # Gestion de la date
                if self.date_etape_var.get() and self.heure_var.get():
                    date_str = self.date_etape_var.get()
                    heure_str = self.heure_var.get()
                    try:
                        etape.date_etape = datetime.strptime(f"{date_str} {heure_str}", "%Y-%m-%d %H:%M")
                    except ValueError:
                        pass
                
                etape.heure = self.heure_var.get()
                etape.duree = self.duree_var.get()
                etape.priorite = self.priorite_var.get()
                etape.statut = self.statut_var.get()
                
                session.commit()
                self.charger_donnees()
                self.vider_formulaire()
                messagebox.showinfo("✅ Succès", "Étape modifiée avec succès!")
                
        except Exception as e:
            session.rollback()
            messagebox.showerror("❌ Erreur", f"Erreur lors de la modification: {str(e)}")

    def supprimer(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une étape à supprimer")
            return
        
        # Confirmation
        if not messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer cette étape ?"):
            return
            
        try:
            id_etape = int(self.tree.item(item, "values")[0])
            etape = session.query(EtapeRotation).filter_by(id_etape=id_etape).first()
            
            if etape:
                session.delete(etape)
                session.commit()
                self.charger_donnees()
                self.vider_formulaire()
                messagebox.showinfo("✅ Succès", "Étape supprimée avec succès!")
                
        except Exception as e:
            session.rollback()
            messagebox.showerror("❌ Erreur", f"Erreur lors de la suppression: {str(e)}")

    def selectionner(self, event=None):
        item = self.tree.selection()
        if item:
            values = self.tree.item(item, "values")
            self.id_etape_var.set(values[0])
            self.id_tournee_var.set(values[1])
            self.nom_var.set(values[2])
            
            # Description dans le widget Text
            self.desc_text.delete("1.0", "end")
            self.desc_text.insert("1.0", values[3])
            
            # Date et heure
            if values[4]:  # date_etape
                self.date_etape_var.set(values[4])
            else:
                self.date_etape_var.set("")
            
            self.heure_var.set(values[5] if values[5] else "08:00")
            
            try:
                self.duree_var.set(int(values[6]) if values[6] else 60)
            except:
                self.duree_var.set(60)
            
            self.priorite_var.set(values[7] if values[7] else "Normale")
            
            # Nettoyer le statut des icônes
            statut = values[8]
            if statut.startswith("✅"):
                statut = "Terminée"
            elif statut.startswith("🔄"):
                statut = "En cours"
            elif statut.startswith("❌"):
                statut = "Annulée"
            else:
                statut = "Planifiée"
            self.statut_var.set(statut)

    def vider_formulaire(self):
        self.id_etape_var.set("")
        self.id_tournee_var.set("")
        self.nom_var.set("")
        self.desc_text.delete("1.0", "end")
        self.date_etape_var.set("")
        self.heure_var.set("08:00")
        self.duree_var.set(60)
        self.priorite_var.set("Normale")
        self.statut_var.set("Planifiée")

    def appliquer_filtres(self):
        # Implémentation basique des filtres
        self.charger_donnees()  # Pour l'instant, recharge tout

    def effacer_filtres(self):
        self.filtre_var.set("")
        self.filtre_tournee_var.set("Toutes")
        self.filtre_statut_var.set("Tous")
        self.charger_donnees()

    def actualiser(self):
        self.charger_donnees()
        self.charger_tournees()

    def trier_colonne(self, col):
        # Tri simple par colonne
        pass

    def menu_contextuel(self, event):
        # Menu contextuel clic droit
        menu = ttk.Menu(self.root, tearoff=0)
        menu.add_command(label="✏️ Modifier", command=self.modifier)
        menu.add_command(label="🗑️ Supprimer", command=self.supprimer)
        menu.add_separator()
        menu.add_command(label="🔄 Actualiser", command=self.actualiser)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def exporter_csv(self):
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Exporter les étapes"
            )
            
            if filename:
                etapes = session.query(EtapeRotation).all()
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    # En-têtes
                    writer.writerow(['ID', 'Tournée', 'Nom', 'Description', 'Date', 'Heure', 'Durée', 'Priorité', 'Statut'])
                    
                    # Données
                    for etape in etapes:
                        date_str = ""
                        if hasattr(etape, 'date_etape') and etape.date_etape:
                            if isinstance(etape.date_etape, datetime):
                                date_str = etape.date_etape.strftime("%Y-%m-%d")
                            else:
                                date_str = str(etape.date_etape)
                        
                        writer.writerow([
                            etape.id_etape,
                            etape.id_tournee,
                            getattr(etape, 'nom', ''),
                            getattr(etape, 'description', ''),
                            date_str,
                            getattr(etape, 'heure', ''),
                            getattr(etape, 'duree', ''),
                            getattr(etape, 'priorite', 'Normale'),
                            getattr(etape, 'statut', 'Planifiée')
                        ])
                
                messagebox.showinfo("✅ Succès", f"Données exportées vers {filename}")
                
        except Exception as e:
            messagebox.showerror("❌ Erreur", f"Erreur lors de l'export: {str(e)}")

    def importer_csv(self):
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Importer des étapes"
            )
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    imported_count = 0
                    
                    for row in reader:
                        try:
                            # Validation et conversion des données
                            id_tournee = int(row.get('Tournée', 0))
                            nom = row.get('Nom', '').strip()
                            
                            if not nom:
                                continue
                            
                            # Conversion de la date
                            date_etape = None
                            if row.get('Date') and row.get('Heure'):
                                try:
                                    date_etape = datetime.strptime(f"{row['Date']} {row['Heure']}", "%Y-%m-%d %H:%M")
                                except:
                                    pass
                            
                            # Création de l'étape
                            etape = EtapeRotation(
                                id_tournee=id_tournee,
                                nom=nom,
                                description=row.get('Description', ''),
                                date_etape=date_etape,
                                heure=row.get('Heure', ''),
                                duree=int(row.get('Durée', 60)) if row.get('Durée', '').isdigit() else 60,
                                priorite=row.get('Priorité', 'Normale'),
                                statut=row.get('Statut', 'Planifiée')
                            )
                            
                            session.add(etape)
                            imported_count += 1
                            
                        except Exception as e:
                            print(f"Erreur ligne: {e}")
                            continue
                    
                    session.commit()
                    self.charger_donnees()
                    messagebox.showinfo("✅ Succès", f"{imported_count} étapes importées avec succès!")
                    
        except Exception as e:
            session.rollback()
            messagebox.showerror("❌ Erreur", f"Erreur lors de l'import: {str(e)}")

    def rechercher_etapes(self):
        """Fonction de recherche avancée"""
        terme = self.filtre_var.get().lower()
        if not terme:
            self.charger_donnees()
            return
        
        try:
            # Filtrer les éléments visibles dans le tableau
            all_items = self.tree.get_children()
            self.tree.delete(*all_items)
            
            etapes = session.query(EtapeRotation).all()
            count = 0
            
            for etape in etapes:
                # Recherche dans nom, description
                nom = getattr(etape, 'nom', '').lower()
                desc = getattr(etape, 'description', '').lower()
                
                if terme in nom or terme in desc:
                    # Afficher cette étape
                    date_str = ""
                    if hasattr(etape, 'date_etape') and etape.date_etape:
                        if isinstance(etape.date_etape, datetime):
                            date_str = etape.date_etape.strftime("%Y-%m-%d")
                    
                    statut = getattr(etape, 'statut', 'Planifiée')
                    priorite = getattr(etape, 'priorite', 'Normale')
                    
                    values = (
                        etape.id_etape,
                        etape.id_tournee,
                        getattr(etape, 'nom', ''),
                        getattr(etape, 'description', ''),
                        date_str,
                        getattr(etape, 'heure', ''),
                        getattr(etape, 'duree', ''),
                        priorite,
                        statut
                    )
                    
                    item = self.tree.insert("", "end", values=values)
                    
                    # Icônes selon statut
                    if statut == "Terminée":
                        self.tree.set(item, "statut", "✅ Terminée")
                    elif statut == "En cours":
                        self.tree.set(item, "statut", "🔄 En cours")
                    elif statut == "Annulée":
                        self.tree.set(item, "statut", "❌ Annulée")
                    else:
                        self.tree.set(item, "statut", "📋 Planifiée")
                    
                    count += 1
            
            self.count_label.config(text=f"Résultats: {count} étapes")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la recherche: {str(e)}")

    def generer_rapport(self):
        """Génère un rapport détaillé"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Sauvegarder le rapport"
            )
            
            if filename:
                etapes = session.query(EtapeRotation).all()
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("          RAPPORT DES ÉTAPES DE TOURNÉE\n")
                    f.write("=" * 60 + "\n")
                    f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    
                    # Statistiques générales
                    total = len(etapes)
                    statuts = {}
                    tournees = {}
                    
                    for etape in etapes:
                        statut = getattr(etape, 'statut', 'Planifiée')
                        statuts[statut] = statuts.get(statut, 0) + 1
                        
                        id_tournee = etape.id_tournee
                        tournees[id_tournee] = tournees.get(id_tournee, 0) + 1
                    
                    f.write("STATISTIQUES GÉNÉRALES:\n")
                    f.write("-" * 25 + "\n")
                    f.write(f"Total des étapes: {total}\n")
                    
                    for statut, count in statuts.items():
                        pourcentage = (count / total * 100) if total > 0 else 0
                        f.write(f"  {statut}: {count} ({pourcentage:.1f}%)\n")
                    
                    f.write(f"\nNombre de tournées: {len(tournees)}\n")
                    f.write(f"Moyenne étapes/tournée: {total/len(tournees):.1f}\n\n" if tournees else "\n")
                    
                    # Détail par tournée
                    f.write("DÉTAIL PAR TOURNÉE:\n")
                    f.write("-" * 20 + "\n")
                    
                    for id_tournee in sorted(tournees.keys()):
                        etapes_tournee = [e for e in etapes if e.id_tournee == id_tournee]
                        f.write(f"\nTournée {id_tournee} ({len(etapes_tournee)} étapes):\n")
                        
                        for etape in etapes_tournee:
                            nom = getattr(etape, 'nom', 'Sans nom')
                            statut = getattr(etape, 'statut', 'Planifiée')
                            date_str = ""
                            if hasattr(etape, 'date_etape') and etape.date_etape:
                                if isinstance(etape.date_etape, datetime):
                                    date_str = etape.date_etape.strftime("%Y-%m-%d")
                            
                            f.write(f"  • {nom} - {statut}")
                            if date_str:
                                f.write(f" - {date_str}")
                            f.write("\n")
                
                messagebox.showinfo("✅ Succès", f"Rapport généré: {filename}")
                
        except Exception as e:
            messagebox.showerror("❌ Erreur", f"Erreur génération rapport: {str(e)}")

    def dupliquer_etape(self):
        """Duplique l'étape sélectionnée"""
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Attention", "Sélectionnez une étape à dupliquer")
            return
        
        try:
            id_etape = int(self.tree.item(item, "values")[0])
            etape_orig = session.query(EtapeRotation).filter_by(id_etape=id_etape).first()
            
            if etape_orig:
                # Créer une copie
                nouvelle_etape = EtapeRotation(
                    id_tournee=etape_orig.id_tournee,
                    nom=f"{getattr(etape_orig, 'nom', '')} (Copie)",
                    description=getattr(etape_orig, 'description', ''),
                    date_etape=getattr(etape_orig, 'date_etape', None),
                    heure=getattr(etape_orig, 'heure', ''),
                    duree=getattr(etape_orig, 'duree', 60),
                    priorite=getattr(etape_orig, 'priorite', 'Normale'),
                    statut='Planifiée'  # Toujours planifiée pour une copie
                )
                
                session.add(nouvelle_etape)
                session.commit()
                self.charger_donnees()
                messagebox.showinfo("✅ Succès", "Étape dupliquée avec succès!")
                
        except Exception as e:
            session.rollback()
            messagebox.showerror("❌ Erreur", f"Erreur lors de la duplication: {str(e)}")

    def configurer_notifications(self):
        """Configuration des notifications (placeholder)"""
        messagebox.showinfo("Notifications", "Fonctionnalité à implémenter:\n- Rappels avant échéance\n- Notifications de changement de statut")

    def aide(self):
        """Affiche l'aide"""
        aide_text = """
AIDE - GESTION DES ÉTAPES DE TOURNÉE

🎯 FONCTIONNALITÉS PRINCIPALES:
• Ajouter, modifier, supprimer des étapes
• Organiser par tournées et statuts
• Filtrer et rechercher
• Exporter/Importer des données

📋 UTILISATION:
1. Sélectionnez une tournée dans la liste déroulante
2. Renseignez les informations de l'étape
3. Utilisez les boutons d'action à gauche
4. Double-cliquez sur une ligne pour éditer

🔍 FILTRES:
• Recherche textuelle dans nom/description
• Filtrage par tournée et statut
• Bouton "Effacer" pour réinitialiser

📊 STATISTIQUES:
• Onglet dédié avec métriques
• Répartition par statut
• Durées moyennes

💾 IMPORT/EXPORT:
• Format CSV supporté
• Menu Fichier > Exporter/Importer

🎨 INTERFACE:
• Thème moderne avec icônes
• Colonnes redimensionnables
• Menu contextuel (clic droit)

❓ SUPPORT:
Pour plus d'aide, consultez la documentation
ou contactez l'administrateur système.
        """
        
        # Fenêtre d'aide
        aide_window = ttk.Toplevel(self.root)
        aide_window.title("💡 Aide - Gestion des Étapes")
        aide_window.geometry("600x500")
        aide_window.resizable(True, True)
        
        # Texte d'aide avec scrollbar
        text_frame = ttk.Frame(aide_window)
        text_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        text_widget = ttk.Text(text_frame, wrap=WORD, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(text_frame, orient=VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        text_widget.insert("1.0", aide_text)
        text_widget.config(state=DISABLED)
        
        # Bouton fermer
        ttk.Button(aide_window, text="Fermer", command=aide_window.destroy, 
                  bootstyle=PRIMARY).pack(pady=10)

    def a_propos(self):
        """Informations sur l'application"""
        messagebox.showinfo("À propos", 
            "🚐 Gestion des Étapes de Tournée v2.0\n\n"
            "Application de gestion avancée des étapes\n"
            "avec interface moderne et fonctionnalités étendues.\n\n"
            "Développé avec ttkbootstrap\n"
            "© 2024 - Version améliorée")


def main():
    try:
        # Initialisation avec gestion d'erreurs
        root = ttk.Window(themename="cosmo")
        
        app = EtapeApp(root)
        
        # Raccourcis clavier simplifiés
        try:
            root.bind('<Control-n>', lambda e: app.vider_formulaire())
            root.bind('<Control-s>', lambda e: app.ajouter())
            root.bind('<F5>', lambda e: app.actualiser())
            root.bind('<F1>', lambda e: app.aide())
        except:
            pass  # Ignore si les raccourcis ne fonctionnent pas
        
        # Binding pour la recherche en temps réel
        try:
            app.filtre_var.trace('w', lambda *args: app.rechercher_etapes())
        except:
            pass
        
        root.mainloop()
        
    except ImportError as e:
        print(f"Erreur d'import: {e}")
        messagebox.showerror("Erreur", "Dépendances manquantes. Vérifiez l'installation de ttkbootstrap.")
    except Exception as e:
        print(f"Erreur de démarrage: {e}")
        messagebox.showerror("Erreur de démarrage", f"Impossible de démarrer l'application: {str(e)}")
    finally:
        try:
            session.close()
        except:
            pass

if __name__ == "__main__":
    main()