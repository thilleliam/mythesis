from sqlalchemy import Label
import ttkbootstrap as ttk
import tkinter as tk
from ttkbootstrap.constants import *
from tkinter import PhotoImage
import os
import sys
from PIL import Image, ImageTk
import random
from tkinter import messagebox
from sqlalchemy.orm import sessionmaker, scoped_session, configure_mappers
from application.database import engine

# Configuration des mappers SQLAlchemy
configure_mappers()

# Créer une factory de sessions
Session = sessionmaker(bind=engine)
session_factory = scoped_session(Session)

# Ajoutez ces imports en haut de votre fichier
from datetime import datetime, date
from sqlalchemy import func
from application.models.commande import Commande
from application.models.tournee import Tournee
from application.models.vehicule import Vehicule
from application.models.conducteurs import Conducteur

class LoginScreen:
    def __init__(self, root, on_login_success):
        """
        Écran d'authentification pour FleetManager
        
        Args:
            root: Fenêtre principale Tkinter
            on_login_success: Fonction à appeler après authentification réussie
        """
        self.root = root
        self.on_login_success = on_login_success
        self.root.title("FleetManager - Authentification")
        photo = tk.PhotoImage(file="C:\\Users\\BIG-computer\\Pictures\\Logo1.png")
        root.iconphoto(False, photo)
        
        # Centrer la fenêtre avec taille fixe pour le login
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # Définir les couleurs et styles pour l'écran de connexion
        self.style = ttk.Style()
        self.primary_color = self.style.colors.primary
        self.secondary_color = self.style.colors.secondary
        self.success_color = self.style.colors.success
        self.danger_color = self.style.colors.danger
        
        # Couleurs de texte
        self.text_color = {
            "dark": "#212529",    # Texte principal
            "light": "#f8f9fa",   # Texte clair (sur fond sombre)
            "muted": "#6c757d",   # Texte atténué/secondaire
            "white": "#ffffff",   # Blanc pur
            "black": "#000000"    # Noir pur
        }
        
        # Styles pour les widgets du formulaire de connexion
        self.style.configure("Login.TLabel", font=("Roboto", 12), foreground=self.text_color["dark"])
        self.style.configure("Title.TLabel", font=("Roboto", 20, "bold"), foreground=self.primary_color)
        self.style.configure("LoginBtn.TButton", font=("Roboto", 12, "bold"))
        
        # Créer et afficher l'interface de connexion
        self.create_login_interface()
    
    def create_login_interface(self):
        """Crée l'interface de connexion avec animation"""
        # Container principal - fond blanc avec ombre
        # Canvas avec scrollbar pour le contenu scrollable
        canvas = tk.Canvas(self.root, highlightthickness=0)
        canvas.pack(fill=BOTH, expand=True, side=LEFT)

        scrollbar = ttk.Scrollbar(self.root, orient=VERTICAL, command=canvas.yview)
        scrollbar.pack(fill=Y, side=RIGHT)

        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interne (contenu réel)
        main_frame = ttk.Frame(canvas, padding=20)
        canvas.create_window((0, 0), window=main_frame, anchor="nw")

        # Ajustement du scroll quand la taille du contenu change
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        main_frame.bind("<Configure>", on_configure)

        
        # Logo et titre
        logo_frame = ttk.Frame(main_frame)
        logo_frame.pack(fill=X, pady=(20, 30))
        
        # Essayer de charger le logo ou créer un logo de remplacement
        try:
            logo_image = Image.open("C:\\Users\\BIG-computer\\Pictures\\Logo.png")
            logo_image = logo_image.resize((80, 80), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = ttk.Label(logo_frame, image=logo_photo)
            logo_label.image = logo_photo
            logo_label.pack(pady=(0, 10))
        except Exception:
            # Canvas pour créer un logo de remplacement
            logo_canvas = tk.Canvas(logo_frame, width=80, height=80, bg="white", highlightthickness=0)
            logo_canvas.pack(pady=(0, 10))
            logo_canvas.create_oval(10, 10, 70, 70, fill=self.primary_color, outline="")
            logo_canvas.create_text(40, 40, text="FL", font=("Segoe UI", 24, "bold"), fill="white")
        
        # Titre de l'application
        ttk.Label(
            logo_frame, 
            text="FleetManager",
            style="Title.TLabel"
        ).pack()
        
        # Sous-titre
        ttk.Label(
            logo_frame,
            text="Gestion de Flotte et Logistique",
            font=("Roboto", 12),
            foreground=self.text_color["muted"]
        ).pack(pady=(5, 0))
        
        # Formulaire de connexion
        self.login_form = ttk.Frame(main_frame, padding=10)
        self.login_form.pack(fill=BOTH, expand=True)
        
        # Champ nom d'utilisateur
        ttk.Label(
            self.login_form, 
            text="Nom d'utilisateur",
            style="Login.TLabel"
        ).pack(anchor=W, pady=(0, 5))
        
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(
            self.login_form,
            textvariable=self.username_var,
            font=("Roboto", 12),
            width=30
        )
        username_entry.pack(fill=X, pady=(0, 15))
        username_entry.focus()  # Placer le focus sur le champ username
        
        # Champ mot de passe
        ttk.Label(
            self.login_form, 
            text="Mot de passe",
            style="Login.TLabel"
        ).pack(anchor=W, pady=(0, 5))
        
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(
            self.login_form,
            textvariable=self.password_var,
            font=("Roboto", 12),
            width=30,
            show="•"  # Masquer le mot de passe
        )
        password_entry.pack(fill=X, pady=(0, 5))
        
        # Option "Se souvenir de moi"
        remember_frame = ttk.Frame(self.login_form)
        remember_frame.pack(fill=X, pady=10)
        
        self.remember_var = tk.BooleanVar()
        remember_check = ttk.Checkbutton(
            remember_frame,
            text="Se souvenir de moi",
            variable=self.remember_var
        )
        remember_check.pack(side=LEFT)
        
        # Lien "Mot de passe oublié"
        forgot_label = ttk.Label(
            remember_frame,
            text="Mot de passe oublié ?",
            font=("Roboto", 10),
            foreground=self.primary_color,
            cursor="hand2"
        )
        forgot_label.pack(side=RIGHT)
        forgot_label.bind("<Button-1>", self.on_forgot_password)
        
        # Bouton de connexion
        login_button = ttk.Button(
            self.login_form,
            text="Se connecter",
            style="LoginBtn.TButton",
            command=self.validate_login,
            bootstyle="primary",
            width=30
        )
        login_button.pack(pady=20)
        
        # Ajouter l'event Enter sur les champs pour valider
        password_entry.bind("<Return>", lambda event: self.validate_login())
        username_entry.bind("<Return>", lambda event: password_entry.focus())
        
        # Section du bas avec texte de copyright
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(side=BOTTOM, fill=X, pady=20)
        
        ttk.Label(
            footer_frame,
            text="© 2025 FleetManager Pro - Tous droits réservés",
            font=("Roboto", 9),
            foreground=self.text_color["muted"]
        ).pack()
        
        # Animation de démarrage
        self.animate_login_screen()
    def on_login_success(self):
        print("Connexion réussie")
        # Ici tu peux switcher vers l'interface principale

    def animate_login_screen(self):
        """Ajouter une simple animation au démarrage de l'écran de connexion"""
        # Pour une animation simple, on va faire apparaître les éléments progressivement
        children = self.root.winfo_children()[0].winfo_children()
        
        # Cacher tous les widgets initialement
        for child in children:
            child.pack_forget()
        
        # Les faire réapparaître avec un délai
        delay = 100  # millisecondes entre chaque widget
        
        def show_widget(index):
            if index < len(children):
                children[index].pack(fill=X if index > 0 else BOTH, expand=(index == 0), pady=(20 if index == 1 else 0, 30 if index == 1 else 0))
                self.root.after(delay, lambda: show_widget(index + 1))
        
        # Démarrer l'animation
        self.root.after(50, lambda: show_widget(0))
    
    def validate_login(self):
        """Valide les informations de connexion"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        try:
            self.error_label.destroy()
        except:
            pass

        if username and password:
            for widget in self.login_form.winfo_children():
                if isinstance(widget, ttk.Button):
                    widget.configure(text="Connexion en cours...", state="disabled")

            self.root.after(1000, self.on_login_success)
        else:
            self.error_label = ttk.Label(
                self.login_form,
                text="Veuillez saisir un nom d'utilisateur et un mot de passe",
                foreground=self.danger_color,
                font=("Roboto", 10)
            )
            self.error_label.pack(before=self.login_form.winfo_children()[-1], pady=(0, 10))
            self.shake_window()

    
    def shake_window(self):
        """Effet de secousse pour indiquer une erreur"""
        original_x = self.root.winfo_x()
        original_y = self.root.winfo_y()
        
        # Paramètres de l'animation
        shake_distance = 10
        shake_speed = 50
        shake_cycles = 3
        
        def shake_cycle(cycle, direction):
            if cycle <= 0:
                self.root.geometry(f"+{original_x}+{original_y}")
                return
                
            new_x = original_x + (shake_distance * direction)
            self.root.geometry(f"+{new_x}+{original_y}")
            
            self.root.after(shake_speed, lambda: shake_cycle(cycle - 0.5, -direction))
            
        shake_cycle(shake_cycles, 1)
    
    def on_forgot_password(self, event):
        """Gère le clic sur 'Mot de passe oublié'"""
        # Crée une fenêtre pop-up simple
        popup = ttk.Toplevel(self.root)
        popup.title("Récupération de mot de passe")
        popup.geometry("350x200")
        
        # Centrer la fenêtre
        popup.geometry(f"+{self.root.winfo_x() + 25}+{self.root.winfo_y() + 150}")
        
        # Contenu de la popup
        content_frame = ttk.Frame(popup, padding=20)
        content_frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(
            content_frame,
            text="Récupération de mot de passe",
            font=("Roboto", 14, "bold"),
            foreground=self.primary_color
        ).pack(pady=(0, 15))
        
        ttk.Label(
            content_frame,
            text="Entrez votre adresse email pour réinitialiser votre mot de passe:",
            wraplength=300,
            justify="left"
        ).pack(fill=X, pady=(0, 10))
        
        email_var = tk.StringVar()
        email_entry = ttk.Entry(content_frame, textvariable=email_var, width=30)
        email_entry.pack(fill=X, pady=5)
        email_entry.focus()
        
        # Frame pour les boutons
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=X, pady=15)
        
        # Bouton annuler
        ttk.Button(
            button_frame,
            text="Annuler",
            bootstyle="secondary-outline",
            command=popup.destroy,
            width=15
        ).pack(side=LEFT, padx=(0, 5))
        
        # Bouton envoyer
        ttk.Button(
            button_frame,
            text="Envoyer",
            bootstyle="primary",
            command=lambda: self.send_reset_email(email_var.get(), popup),
            width=15
        ).pack(side=RIGHT)
        
        # Rendre la fenêtre modale
        popup.transient(self.root)
        popup.grab_set()
        
    def send_reset_email(self, email, popup):
        """Simule l'envoi d'un e-mail de réinitialisation"""
        if not email.strip():
            # Afficher un message d'erreur
            try:
                self.reset_error_label.destroy()
            except:
                pass
                
            self.reset_error_label = ttk.Label(
                popup.winfo_children()[0],
                text="Veuillez saisir une adresse e-mail",
                foreground=self.danger_color,
                font=("Roboto", 10)
            )
            self.reset_error_label.pack(before=popup.winfo_children()[0].winfo_children()[-1])
            return
            
        # Afficher un message de confirmation
        for widget in popup.winfo_children()[0].winfo_children():
            widget.destroy()
            
        ttk.Label(
            popup.winfo_children()[0],
            text="Email envoyé !",
            font=("Roboto", 14, "bold"),
            foreground=self.success_color
        ).pack(pady=(20, 15))
        
        ttk.Label(
            popup.winfo_children()[0],
            text=f"Un lien de réinitialisation a été envoyé à {email}.\nVeuillez vérifier votre boîte de réception.",
            wraplength=300,
            justify="center"
        ).pack(fill=X, pady=10)
        
        ttk.Button(
            popup.winfo_children()[0],
            text="Fermer",
            bootstyle="primary",
            command=popup.destroy
        ).pack(pady=15)
        
        # Fermer automatiquement après 3 secondes
        popup.after(3000, popup.destroy)
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion de Flotte et Logistique")
        # Initialiser la session de base de données CORRECTEMENT
        self.session = None
        self._initialize_session()
        photo = tk.PhotoImage(file="C:\\Users\\BIG-computer\\Pictures\\Logo1.png")
        root.iconphoto(False, photo)
        # Initialiser l'écran de connexion d'abord
        self.show_login_screen()
    
    def _initialize_session(self):
        """Initialise la session de base de données"""
        try:
            self.session = session_factory()
            print("Session de base de données initialisée avec succès")
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la session: {e}")
            self.session = None
    
    def get_session(self):
        """Obtient une session de base de données"""
        if self.session is None:
            self._initialize_session()
        
        if self.session is None:
            messagebox.showerror("Erreur de base de données", 
                            "Impossible de se connecter à la base de données")
            return None
        
        return self.session
    
    def show_login_screen(self):
        """Affiche l'écran de connexion"""
        self.login_screen = LoginScreen(self.root, self.initialize_main_app)
    
    def initialize_main_app(self):
        """Initialise l'application principale après connexion réussie"""
        # Effacer tous les widgets existants
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Restaurer la géométrie complète pour l'application principale
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Initialiser l'application principale avec toutes ses fonctionnalités
        self.initialize_full_app()
    
    def initialize_full_app(self):
        """Initialise l'application complète - votre code existant"""
        # Configurez le style global
        self.style = ttk.Style()
        
        # Définir les couleurs de texte pour le thème cosmo
        self.text_color = {
            "dark": "#212529",    # Texte principal
            "light": "#f8f9fa",   # Texte clair (sur fond sombre)
            "muted": "#6c757d",   # Texte atténué/secondaire
            "white": "#ffffff",   # Blanc pur
            "black": "#000000"    # Noir pur
        }
        
        # Configuration globale des styles
        self.style.configure("TButton", font=("Roboto", 11))
        self.style.configure("TLabel", font=("Roboto", 11), foreground=self.text_color["dark"])
        self.style.configure("Title.TLabel", font=("Roboto", 28, "bold"), foreground=self.text_color["dark"])
        self.style.configure("Subtitle.TLabel", font=("Roboto", 14), foreground=self.text_color["muted"])
        self.style.configure("ModuleTitle.TLabel", font=("Roboto", 16, "bold"), foreground=self.text_color["dark"])
        self.style.configure("Card.TFrame", relief="raised", borderwidth=0)
        
        # Configurations spécifiques pour les labels sur fonds colorés
        self.style.configure("Light.TLabel", foreground=self.text_color["light"])
        self.style.configure("Dark.TLabel", foreground=self.text_color["dark"])
        self.style.configure("Muted.TLabel", foreground=self.text_color["muted"])
        
        # Création du conteneur principal avec structure de style sidebar
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=True)
        
        # Sidebar
        self.create_sidebar()
        
        # Zone de contenu principal
        self.content_area = ttk.Frame(self.main_container, padding=20)
        self.content_area.pack(side=LEFT, fill=BOTH, expand=True)
        
        # En-tête de l'application
        self.create_header()
        
        # MODIFICATION PRINCIPALE: Zone des modules avec scrollbars horizontal et vertical
        # Créer un frame conteneur pour les scrollbars
        scroll_container = ttk.Frame(self.content_area)
        scroll_container.pack(fill=BOTH, expand=True, pady=(10, 0))
        
        # Canvas principal avec scrollbars
        self.dashboard_canvas = tk.Canvas(
            scroll_container, 
            background="white", 
            highlightthickness=0,
            # Définir une taille minimale pour le canvas
            width=800,
            height=600
        )
        
        # Scrollbar verticale
        v_scrollbar = ttk.Scrollbar(scroll_container, orient=VERTICAL, command=self.dashboard_canvas.yview)
        v_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Scrollbar horizontale
        h_scrollbar = ttk.Scrollbar(scroll_container, orient=HORIZONTAL, command=self.dashboard_canvas.xview)
        h_scrollbar.pack(side=BOTTOM, fill=X)
        
        # Configurer le canvas avec les scrollbars
        self.dashboard_canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # Placer le canvas
        self.dashboard_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        # Frame qui contiendra les modules (scrollable)
        self.modules_frame = ttk.Frame(self.dashboard_canvas, padding=10)
        
        # Créer une fenêtre dans le canvas pour le frame des modules
        self.canvas_window = self.dashboard_canvas.create_window(
            (0, 0), 
            window=self.modules_frame, 
            anchor="nw"
        )

        # Fonctions pour gérer le scrolling
        def on_frame_configure(event):
            """Met à jour la région de scroll quand le contenu change"""
            self.dashboard_canvas.configure(scrollregion=self.dashboard_canvas.bbox("all"))
            
            # Ajuster la largeur du canvas window si nécessaire
            canvas_width = self.dashboard_canvas.winfo_width()
            frame_width = self.modules_frame.winfo_reqwidth()
            
            if frame_width < canvas_width:
                # Si le contenu est plus petit que le canvas, étendre pour remplir
                self.dashboard_canvas.itemconfig(self.canvas_window, width=canvas_width)

        def on_canvas_configure(event):
            """Ajuste la taille du frame quand le canvas change de taille"""
            canvas_width = event.width
            frame_width = self.modules_frame.winfo_reqwidth()
            
            if frame_width < canvas_width:
                # Étendre le frame pour remplir la largeur du canvas
                self.dashboard_canvas.itemconfig(self.canvas_window, width=canvas_width)

        # Lier les événements
        self.modules_frame.bind("<Configure>", on_frame_configure)
        self.dashboard_canvas.bind("<Configure>", on_canvas_configure)

        # Activer le scroll avec la molette de souris
        def on_mousewheel_vertical(event):
            """Scroll vertical avec la molette"""
            self.dashboard_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_mousewheel_horizontal(event):
            """Scroll horizontal avec Shift + molette"""
            self.dashboard_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_mousewheel(event):
            """Gestion du scroll avec la molette"""
            if event.state & 0x1:  # Shift est pressé
                on_mousewheel_horizontal(event)
            else:
                on_mousewheel_vertical(event)

        # Lier les événements de scroll à tous les widgets pertinents
        def bind_mousewheel_to_widget(widget):
            """Lie les événements de molette à un widget et ses enfants"""
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", lambda e: self.dashboard_canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>", lambda e: self.dashboard_canvas.yview_scroll(1, "units"))
            widget.bind("<Shift-Button-4>", lambda e: self.dashboard_canvas.xview_scroll(-1, "units"))
            widget.bind("<Shift-Button-5>", lambda e: self.dashboard_canvas.xview_scroll(1, "units"))
            
            # Appliquer récursivement aux widgets enfants
            for child in widget.winfo_children():
                bind_mousewheel_to_widget(child)

        # Appliquer le binding après un délai pour s'assurer que tous les widgets sont créés
        def apply_scroll_bindings():
            try:
                bind_mousewheel_to_widget(self.modules_frame)
                self.dashboard_canvas.bind("<MouseWheel>", on_mousewheel)
                self.dashboard_canvas.bind("<Button-4>", lambda e: self.dashboard_canvas.yview_scroll(-1, "units"))
                self.dashboard_canvas.bind("<Button-5>", lambda e: self.dashboard_canvas.yview_scroll(1, "units"))
                self.dashboard_canvas.bind("<Shift-Button-4>", lambda e: self.dashboard_canvas.xview_scroll(-1, "units"))
                self.dashboard_canvas.bind("<Shift-Button-5>", lambda e: self.dashboard_canvas.xview_scroll(1, "units"))
            except Exception as e:
                print(f"Erreur lors de l'application des bindings de scroll: {e}")

        # Gestion du focus pour le scroll au clavier
        self.dashboard_canvas.focus_set()
        
        # Bindings pour navigation clavier
        self.dashboard_canvas.bind("<Up>", lambda e: self.dashboard_canvas.yview_scroll(-1, "units"))
        self.dashboard_canvas.bind("<Down>", lambda e: self.dashboard_canvas.yview_scroll(1, "units"))
        self.dashboard_canvas.bind("<Left>", lambda e: self.dashboard_canvas.xview_scroll(-1, "units"))
        self.dashboard_canvas.bind("<Right>", lambda e: self.dashboard_canvas.xview_scroll(1, "units"))
        self.dashboard_canvas.bind("<Prior>", lambda e: self.dashboard_canvas.yview_scroll(-1, "pages"))  # Page Up
        self.dashboard_canvas.bind("<Next>", lambda e: self.dashboard_canvas.yview_scroll(1, "pages"))    # Page Down
        self.dashboard_canvas.bind("<Home>", lambda e: self.dashboard_canvas.yview_moveto(0))
        self.dashboard_canvas.bind("<End>", lambda e: self.dashboard_canvas.yview_moveto(1))

        self.style.configure("ModernCard.TFrame",
            background="white",
            relief="flat",
            borderwidth=1
        )
        self.style.map("ModernCard.TFrame", background=[("active", "white")])

        # Créer les modules sous forme de cartes modernes
        self.create_module_cards()
        
        # Appliquer les bindings de scroll après création des modules
        self.root.after(100, apply_scroll_bindings)
        
        # Barre d'état inférieure
        self.create_status_bar()
        
        # Animation de démarrage
        self.animate_startup()

    def create_module_cards(self):
        """Crée des cartes modernes pour les modules avec données réelles"""
        # Utiliser un notebook avec onglets pour organiser le contenu
        notebook = ttk.Notebook(self.modules_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tableau de bord principal
        dashboard_tab = ttk.Frame(notebook, padding=10)
        notebook.add(dashboard_tab, text="Tableau de bord")
        
        # Onglet de gestion
        management_tab = ttk.Frame(notebook, padding=10)
        notebook.add(management_tab, text="Gestion")
        
        # Onglet de rapports
        reports_tab = ttk.Frame(notebook, padding=10)
        notebook.add(reports_tab, text="Rapports")
        
        # Créer des modules dans l'onglet du tableau de bord
        # Première rangée: statistiques générales avec données réelles
        stats_frame = ttk.Frame(dashboard_tab)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Récupérer les données réelles
        data = self.get_dashboard_data()
        
        # KPI Cards avec données de la base
        kpi_data = [
            {
                "title": "Véhicules Disponibles",
                "value": f"{data['vehicules']['disponibles']}/{data['vehicules']['total']}",
                "change": f"{data['vehicules']['en_panne']} en panne" if data['vehicules']['en_panne'] > 0 else "Tous opérationnels",
                "icon": "🚛",
                "color": "success" if data['vehicules']['en_panne'] == 0 else "warning"
            },
            {
                "title": "Commandes Total",
                "value": str(data['commandes']['total']),
                "change": f"{data['commandes']['en_retard']} en retard" if data['commandes']['en_retard'] > 0 else f"{data['commandes']['en_cours']} en cours",
                "icon": "📦",
                "color": "danger" if data['commandes']['en_retard'] > 0 else "primary"
            },
            {
                "title": "Tournées du jour",
                "value": str(data['tournees']['aujourd_hui']),
                "change": f"{data['tournees']['en_cours']} en cours",
                "icon": "🗺️",
                "color": "warning"
            },
            {
                "title": "Conducteurs Actifs",
                "value": f"{data['conducteurs']['disponibles']}/{data['conducteurs']['total']}",
                "change": f"{data['conducteurs']['en_conge']} en congé",
                "icon": "👨‍💼",
                "color": "info"
            }
        ]
        
        for kpi in kpi_data:
            self.create_kpi_card(stats_frame, kpi)
        
        # Deuxième rangée: modules principaux sur 2 colonnes
        modules_container = ttk.Frame(dashboard_tab)
        modules_container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Colonne gauche
        left_col = ttk.Frame(modules_container)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Colonne droite
        right_col = ttk.Frame(modules_container)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Ajouter les modules avec données réelles
        self.create_vehicules_status_chart(left_col)
        self.create_tournees_progress_module(right_col)
        self.create_prochaines_livraisons_module(left_col)
        self.create_commandes_table_module(right_col, "Dernières commandes", "danger")
        
        # Forcer une mise à jour de la région de scroll après création du contenu
        self.modules_frame.update_idletasks()
        self.dashboard_canvas.configure(scrollregion=self.dashboard_canvas.bbox("all"))

    # Méthode utilitaire pour ajuster dynamiquement la taille du contenu
    def update_scroll_region(self):
        """Met à jour la région de scroll du dashboard"""
        try:
            self.modules_frame.update_idletasks()
            self.dashboard_canvas.configure(scrollregion=self.dashboard_canvas.bbox("all"))
        except Exception as e:
            print(f"Erreur lors de la mise à jour de la région de scroll: {e}")

    # Méthode pour réinitialiser la position de scroll
    def reset_scroll_position(self):
        """Remet le scroll en position initiale"""
        try:
            self.dashboard_canvas.yview_moveto(0)
            self.dashboard_canvas.xview_moveto(0)
        except Exception as e:
            print(f"Erreur lors de la réinitialisation du scroll: {e}")
    
    def create_sidebar(self):
        """Sidebar claire avec boutons unifiés"""
        self.sidebar = ttk.Frame(self.main_container, bootstyle="light", width=220)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        # Logo + titre
                # Définir le style pour le fond g# Style cohérent
        style = ttk.Style()
        style.configure("Sidebar.TFrame", background="#f8f9fa")
        style.configure("SidebarTitle.TLabel", font=("Segoe UI", 14, "bold"), foreground="#212529", background="#f8f9fa")

        # Frame du logo
        logo_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame", width=220)

        logo_frame.pack(fill=X, expand=True, padx=10, pady=20)


        # Logo (à gauche)
        # Logo (à gauche)
        try:
            logo_image = Image.open("C:\\Users\\BIG-computer\\Pictures\\Logo.png")
            logo_image = logo_image.resize((50, 50), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = ttk.Label(logo_frame, image=logo_photo, background="#f8f9fa")
            logo_label.image = logo_photo  # Conserver une référence à l'image
            logo_label.pack(side=LEFT, padx=5)
        except Exception:
            logo_canvas = tk.Canvas(logo_frame, width=50, height=50, bg="#f8f9fa", bd=0, highlightthickness=0)
            logo_canvas.create_oval(5, 5, 45, 45, fill="#007BFF", outline="")
            logo_canvas.create_text(25, 25, text="FL", font=("Segoe UI", 14, "bold"), fill="white")
            logo_canvas.pack(side=LEFT, padx=5)


        # Label "FleetManager" à gauche aussi
        title_container = ttk.Frame(logo_frame, style="Sidebar.TFrame")
        title_container.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))


        ttk.Label(
            title_container,
            text="Fleet Manager",
            style="SidebarTitle.TLabel",
            anchor="w"
        ).pack(fill=X)




        ttk.Separator(self.sidebar).pack(fill=X, padx=10, pady=(0, 15))

        # Boutons de menu
        menu_items = [
            ("Tableau de bord", self.show_dashboard),
            ("Véhicules", self.open_vehicule_view),
            ("Équipements", self.open_equipement_view),
            ("Chantiers", self.open_chantiers_view),
            ("Tournées", self.open_tournee_view),
            ("Conducteurs", self.open_conducteur_view),
            ("Commandes", self.open_commande_view),
            ("Affectations", self.open_affectation_view),
            ("Carte", self.open_carte_view),
            ("Notifications", self.open_notification_view),
            ("Gestion des DTM", self.open_transferer_equipement_view)
        ]

        for label, command in menu_items:
            self.create_sidebar_button(self.sidebar, label, command)

        self.create_user_section()

    def create_sidebar_button(self, parent, text, command):
        """Bouton clair à fond uni bleu"""
        button = ttk.Button(
            parent,
            text=text,
            style="Sidebar.TButton",
            command=command,
            cursor="hand2",
            padding=(10, 8)
        )
        button.pack(fill=X, padx=12, pady=4)
    

    def create_menu_item(self, parent, text, command, icon_name=None):
        """Crée un élément de menu dans la sidebar, adapté au thème flatly"""
        item_frame = ttk.Frame(parent, bootstyle="light")
        item_frame.pack(fill=X, pady=3, padx=5)
        item_frame.configure(cursor="hand2")

        def on_hover(e):
            item_frame.configure(style="secondary.TFrame")
        def on_leave(e):
            item_frame.configure(style="light.TFrame")

        item_frame.bind("<Enter>", on_hover)
        item_frame.bind("<Leave>", on_leave)
        item_frame.bind("<Button-1>", lambda e: command())

        icon_canvas = tk.Canvas(item_frame, width=24, height=24, bg=self.style.colors.light, highlightthickness=0)
        icon_canvas.pack(side=LEFT, padx=10, pady=6)

        icon_colors = {
            "house": self.style.colors.info,
            "truck": self.style.colors.success,
            "tools": self.style.colors.warning,
            "building": self.style.colors.info,
            "map": self.style.colors.primary,
            "people": self.style.colors.success,
            "clipboard": self.style.colors.info,
            "shuffle": self.style.colors.warning,
            "globe": self.style.colors.primary,
            "bell": self.style.colors.danger
        }

        color = icon_colors.get(icon_name, self.style.colors.secondary)
        if icon_name == "house":
            icon_canvas.create_polygon(4, 14, 12, 4, 20, 14, 20, 22, 4, 22, fill=color, outline="")
        elif icon_name == "truck":
            icon_canvas.create_rectangle(3, 10, 18, 16, fill=color, outline="")
            icon_canvas.create_rectangle(18, 12, 22, 16, fill=color, outline="")
            icon_canvas.create_oval(6, 16, 10, 20, fill="black")
            icon_canvas.create_oval(14, 16, 18, 20, fill="black")
        else:
            icon_canvas.create_rectangle(6, 6, 18, 18, fill=color, outline="")

        menu_label = ttk.Label(
            item_frame,
            text=text,
            bootstyle="dark",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2"
        )
        menu_label.pack(side=LEFT, fill=X, pady=6)
        menu_label.bind("<Button-1>", lambda e: command())
        icon_canvas.bind("<Button-1>", lambda e: command())

        return item_frame

    def create_user_section(self):
        """Crée la section utilisateur en bas de la sidebar"""
        # Créer un frame pour maintenir l'utilisateur en bas
        # qui prendra tout l'espace disponible restant
        spacer = ttk.Frame(self.sidebar)
        spacer.pack(fill=tk.Y, expand=True)

        # Séparateur
        ttk.Separator(self.sidebar).pack(fill=tk.X, padx=10, pady=(5, 10))

        # Frame utilisateur
        user_frame = ttk.Frame(self.sidebar, style="Sidebar.TFrame")
        user_frame.pack(fill=tk.X, padx=10, pady=10)

        # Avatar utilisateur
        avatar_canvas = tk.Canvas(
            user_frame,
            width=32,
            height=32,
            bg="#f8f9fa",  # Fond cohérent avec style Sidebar.TFrame
            highlightthickness=0
        )
        avatar_canvas.pack(side=tk.LEFT, padx=10, pady=5)
        avatar_canvas.create_oval(2, 2, 30, 30, fill="#007BFF", outline="")
        avatar_canvas.create_text(16, 16, text="AP", font=("Roboto", 10, "bold"), fill="white")

        # Info utilisateur
        user_info = ttk.Frame(user_frame, style="Sidebar.TFrame")
        user_info.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Label(
            user_info,
            text="Admin Projet",
            font=("Roboto", 10, "bold"),
            foreground="#212529"  # Texte foncé pour contraste
        ).pack(anchor=tk.W)

        ttk.Label(
            user_info,
            text="En ligne",
            font=("Roboto", 8),
            foreground="#28a745"  # Couleur verte pour "En ligne"
        ).pack(anchor=tk.W)
        
        # Bouton de déconnexion
        logout_btn = ttk.Button(
            user_frame,
            text="⏻",
            command=self.logout,
            style="Sidebar.TButton",
            cursor="hand2"
        )
        logout_btn.pack(side=tk.RIGHT, padx=5)
        
    def logout(self):
        """Déconnecte l'utilisateur et retourne à l'écran de connexion"""
        # Nettoyer la session
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                print(f"Erreur lors de la fermeture de la session: {e}")
            finally:
                self.session = None
        
        # Effacer tous les widgets existants
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Afficher l'écran de connexion
        self.show_login_screen()

    def create_header(self):
        """Crée l'en-tête de l'application"""
        header_frame = ttk.Frame(self.content_area)
        header_frame.pack(fill=X, pady=(0, 20))
        
        # Titre principal avec style plus moderne
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=LEFT)
        
        ttk.Label(
            title_frame, 
            text="Tableau de bord", 
            style="Title.TLabel",
            bootstyle="primary",
            foreground=self.style.colors.primary
        ).pack(anchor=W)
        
        ttk.Label(
            title_frame,
            text="Superviser et gérer efficacement votre flotte et vos ressources",
            style="Subtitle.TLabel"
        ).pack(anchor=W, pady=(5, 0))
        
        # Zone de recherche et notifications à droite
        actions_frame = ttk.Frame(header_frame)
        actions_frame.pack(side=RIGHT, fill=Y)
        
        # Barre de recherche
        search_frame = ttk.Frame(actions_frame)
        search_frame.pack(side=LEFT, padx=10)
        
        search_entry = ttk.Entry(search_frame, width=25, bootstyle="primary")
        search_entry.insert(0, "Rechercher...")
        search_entry.pack(side=LEFT)
        
        search_btn = ttk.Button(search_frame, text="🔍", bootstyle="primary-outline", width=3)
        search_btn.pack(side=LEFT, padx=(5, 0))
        
        # Bouton de notifications
        notif_btn = ttk.Button(actions_frame, text="🔔", bootstyle="primary-outline", width=3)
        notif_btn.pack(side=LEFT, padx=5)
        
        # Indicateur de notifications
        try:
            notif_canvas = tk.Canvas(actions_frame, width=16, height=16, 
                                   background=self.root.cget("background"), 
                                   highlightthickness=0)
            notif_canvas.place(in_=notif_btn, x=25, y=3)
            notif_canvas.create_oval(0, 0, 16, 16, fill=self.style.colors.danger, outline="")
            notif_canvas.create_text(8, 8, text="3", fill=self.text_color["white"], 
                                   font=("Roboto", 8, "bold"))
        except Exception:
            pass  # Ignorer si l'indicateur ne peut pas être créé

    def get_dashboard_data(self):
        """Récupère les données en temps réel depuis la base de données"""
        today = date.today()
        current_datetime = datetime.now()
        
        try:
            # Vérifier si la session est disponible
            session = self.get_session()
            if session is None:
                # Retourner des données par défaut si pas de session
                return self._get_default_data()
                
            # Commandes
            total_commandes = session.query(Commande).count()
            commandes_en_cours = session.query(Commande).filter(
                Commande.date_livraison > current_datetime
            ).count()
            
            # Calculer les commandes en retard de manière sécurisée
            commandes_en_retard = 0
            try:
                all_commandes = session.query(Commande).all()
                for cmd in all_commandes:
                    if hasattr(cmd, 'est_en_retard') and cmd.est_en_retard(current_datetime):
                        commandes_en_retard += 1
            except Exception:
                pass
                
            commandes_livrees = session.query(Commande).filter(
                Commande.date_livraison <= current_datetime
            ).count()

            # Véhicules
            total_vehicules = session.query(Vehicule).count()
            
            # Calculer les véhicules disponibles de manière sécurisée
            vehicules_disponibles = 0
            try:
                all_vehicules = session.query(Vehicule).all()
                for v in all_vehicules:
                    if hasattr(v, 'est_disponible') and v.est_disponible():
                        vehicules_disponibles += 1
            except Exception:
                pass
                
            vehicules_en_panne = session.query(Vehicule).filter(
                Vehicule.etat == "En panne"
            ).count()
            vehicules_en_service = session.query(Vehicule).filter(
                Vehicule.etat == "En service"
            ).count()

            # Conducteurs
            total_conducteurs = session.query(Conducteur).count()
            conducteurs_disponibles = session.query(Conducteur).filter(
                Conducteur.disponibilite == "disponible"
            ).count()
            conducteurs_en_conge = session.query(Conducteur).filter(
                Conducteur.disponibilite == "conge"
            ).count()

            # Tournées
            tournees_aujourd_hui = session.query(Tournee).filter(
                func.date(Tournee.date_heure_depart) == today
            ).count()
            tournees_en_cours = session.query(Tournee).filter(
                Tournee.date_heure_depart <= current_datetime,
                Tournee.date_heure_arrivee.is_(None)
            ).count()

            # KM totaux parcourus
            km_total = session.query(func.sum(Tournee.km_parcouru)).scalar() or 0
            km_aujourd_hui = session.query(func.sum(Tournee.km_parcouru)).filter(
                func.date(Tournee.date_heure_depart) == today
            ).scalar() or 0

            return {
                'commandes': {
                    'total': total_commandes,
                    'en_cours': commandes_en_cours,
                    'en_retard': commandes_en_retard,
                    'livrees': commandes_livrees
                },
                'vehicules': {
                    'total': total_vehicules,
                    'disponibles': vehicules_disponibles,
                    'en_panne': vehicules_en_panne,
                    'en_service': vehicules_en_service
                },
                'conducteurs': {
                    'total': total_conducteurs,
                    'disponibles': conducteurs_disponibles,
                    'en_conge': conducteurs_en_conge
                },
                'tournees': {
                    'aujourd_hui': tournees_aujourd_hui,
                    'en_cours': tournees_en_cours
                },
                'kilometrage': {
                    'total': km_total,
                    'aujourd_hui': km_aujourd_hui
                }
            }
        except Exception as e:
            print(f"Erreur lors de la récupération des données: {e}")
            return self._get_default_data()
    
    def _get_default_data(self):
        """Retourne des données par défaut en cas d'erreur"""
        return {
            'commandes': {'total': 0, 'en_cours': 0, 'en_retard': 0, 'livrees': 0},
            'vehicules': {'total': 0, 'disponibles': 0, 'en_panne': 0, 'en_service': 0},
            'conducteurs': {'total': 0, 'disponibles': 0, 'en_conge': 0},
            'tournees': {'aujourd_hui': 0, 'en_cours': 0},
            'kilometrage': {'total': 0, 'aujourd_hui': 0}
        }

    def create_kpi_card(self, parent, data):
        """Crée une carte KPI moderne et visible"""
        bg_color = "white"
        border_color = getattr(self.style.colors, data["color"], "#007BFF")
        
        card = tk.Frame(
            parent, 
            bg=bg_color,
            bd=0,
            highlightbackground=border_color,
            highlightthickness=2
        )
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, ipadx=10, ipady=10)

        # Titre
        ttk.Label(
            card,
            text=data["title"],
            font=("Roboto", 10),
            foreground="#000000",
            background=bg_color
        ).pack(anchor="w", pady=(0, 5))

        # Valeur + variation
        content = tk.Frame(card, bg=bg_color)
        content.pack(anchor="w")

        ttk.Label(
            content,
            text=data["value"],
            font=("Roboto", 22, "bold"),
            foreground="#000000",
            background=bg_color
        ).pack(side="left")

        change_color = getattr(self.style.colors, "success", "#28a745") if "+" in data["change"] or "opération" in data["change"] else getattr(self.style.colors, "danger", "#dc3545")

        ttk.Label(
            content,
            text=data["change"],
            font=("Roboto", 12),
            foreground=change_color,
            background=bg_color,
            padding=(10, 4)
        ).pack(side="left")

        # Icône
        icon_canvas = tk.Canvas(
            card, width=36, height=36, 
            bg=bg_color, highlightthickness=0
        )
        icon_canvas.pack(side="right", anchor="n", pady=5)
        icon_canvas.create_oval(2, 2, 34, 34, fill=border_color, outline="")
        icon_canvas.create_text(18, 18, text=data["icon"], fill="white", font=("Roboto", 14, "bold"))

    def create_vehicules_status_chart(self, parent):
        """Crée un graphique des statuts des véhicules"""
        module = ttk.LabelFrame(parent, text="État des Véhicules", padding=15, bootstyle="info")
        module.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Récupérer les données des véhicules
        vehicules_data = {}
        try:
            session = self.get_session()
            if session:
                vehicules = session.query(Vehicule).all()
                
                for vehicule in vehicules:
                    try:
                        if hasattr(vehicule, 'est_disponible') and vehicule.est_disponible():
                            status = "Disponible"
                        else:
                            status = getattr(vehicule, 'etat', 'Inconnu') or "Inconnu"
                        vehicules_data[status] = vehicules_data.get(status, 0) + 1
                    except Exception:
                        status = "Inconnu"
                        vehicules_data[status] = vehicules_data.get(status, 0) + 1
            else:
                vehicules_data = {"Aucune donnée": 1}
        except Exception as e:
            print(f"Erreur lors de la récupération des véhicules: {e}")
            vehicules_data = {"Aucune donnée": 1}
        
        # Canvas pour le graphique
        chart_canvas = tk.Canvas(module, width=400, height=200, bg="white")
        chart_canvas.pack(fill=tk.BOTH, expand=True)
        
        if not vehicules_data or "Aucune donnée" in vehicules_data:
            chart_canvas.create_text(200, 100, text="Aucune donnée disponible", font=("Roboto", 14))
            return
        
        # Couleurs pour chaque statut
        colors = {
            "Disponible": getattr(self.style.colors, "success", "#28a745"),
            "En service": getattr(self.style.colors, "warning", "#ffc107"),
            "En panne": getattr(self.style.colors, "danger", "#dc3545"),
            "Inconnu": getattr(self.style.colors, "secondary", "#6c757d")
        }
        
        # Dessiner le graphique en barres
        self._draw_bar_chart(chart_canvas, vehicules_data, colors)

    def _draw_bar_chart(self, canvas, data, colors):
        """Dessine un graphique en barres"""
        bar_width = 80
        margin = 50
        chart_width = 400 - 2*margin
        chart_height = 200 - 2*margin
        
        # Axes
        canvas.create_line(margin, margin, margin, chart_height+margin, width=2)
        canvas.create_line(margin, chart_height+margin, chart_width+margin, chart_height+margin, width=2)
        
        if not data:
            return
        
        # Barres
        max_value = max(data.values())
        statuts = list(data.keys())
        bar_spacing = chart_width / (len(statuts) + 1)
        
        for i, (statut, count) in enumerate(data.items()):
            bar_height = (count / max_value) * chart_height * 0.8 if max_value > 0 else 0
            x0 = margin + (i + 1) * bar_spacing - bar_width/2
            y0 = chart_height + margin - bar_height
            x1 = x0 + bar_width
            y1 = chart_height + margin
            
            color = colors.get(statut, getattr(self.style.colors, "secondary", "#6c757d"))
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            
            # Valeur au-dessus
            canvas.create_text(x0 + bar_width/2, y0 - 10, 
                              text=str(count), font=("Roboto", 10, "bold"))
            
            # Label en bas
            canvas.create_text(x0 + bar_width/2, y1 + 15, 
                              text=statut[:10], font=("Roboto", 8))

    def create_tournees_progress_module(self, parent):
        """Module des tournées en cours avec progression réelle"""
        module = ttk.LabelFrame(parent, text="Tournées en Cours", padding=15, bootstyle="warning")
        module.pack(fill=tk.BOTH, expand=True, pady=10)
        
        try:
            session = self.get_session()
            if session is None:
                ttk.Label(module, text="Connexion à la base de données requise", 
                         font=("Roboto", 12), foreground=self.text_color["muted"]).pack(pady=20)
                return
                
            # Récupérer les tournées en cours
            current_datetime = datetime.now()
            tournees_en_cours = session.query(Tournee).filter(
                Tournee.date_heure_depart <= current_datetime,
                Tournee.date_heure_arrivee.is_(None)
            ).limit(5).all()
        except Exception as e:
            print(f"Erreur lors de la récupération des tournées: {e}")
            tournees_en_cours = []
        
        if not tournees_en_cours:
            ttk.Label(module, text="Aucune tournée en cours", 
                     font=("Roboto", 12), foreground=self.text_color["muted"]).pack(pady=20)
            return
        
        for tournee in tournees_en_cours:
            item_frame = ttk.Frame(module)
            item_frame.pack(fill=tk.X, pady=5)
            
            # Informations de la tournée
            label_frame = ttk.Frame(item_frame)
            label_frame.pack(fill=tk.X)
            
            # Nom avec conducteur et destination
            try:
                conducteur_nom = tournee.conducteur.nom if tournee.conducteur else "Inconnu"
            except Exception:
                conducteur_nom = "Inconnu"
                
            destination = getattr(tournee, 'destination', 'Destination inconnue') or "Destination inconnue"
            tournee_info = f"{conducteur_nom} → {destination}"
            
            ttk.Label(label_frame, text=tournee_info, font=("Roboto", 10),
                     foreground=self.text_color["dark"]).pack(side=tk.LEFT)
            
            # Calcul du pourcentage de progression
            progress = self._calculate_tournee_progress(tournee, current_datetime)
            
            ttk.Label(label_frame, text=f"{progress:.0f}%", font=("Roboto", 10, "bold"),
                     foreground=getattr(self.style.colors, "warning", "#ffc107")).pack(side=tk.RIGHT)
            
            # Barre de progression
            progress_bar = ttk.Progressbar(item_frame, value=progress, bootstyle="warning")
            progress_bar.pack(fill=tk.X, pady=(5, 0))

    def _calculate_tournee_progress(self, tournee, current_datetime):
        """Calcule le pourcentage de progression d'une tournée"""
        try:
            if hasattr(tournee, 'date_heure_depart') and hasattr(tournee, 'date_heure_reception') and tournee.date_heure_depart and tournee.date_heure_reception:
                temps_ecoule = (current_datetime - tournee.date_heure_depart).total_seconds()
                temps_prevu = (tournee.date_heure_reception - tournee.date_heure_depart).total_seconds()
                progress = min(100, (temps_ecoule / temps_prevu) * 100) if temps_prevu > 0 else 0
            else:
                progress = 25  # Valeur par défaut
        except Exception:
            progress = 25  # Valeur par défaut en cas d'erreur
        return max(0, progress)

    def create_prochaines_livraisons_module(self, parent):
        """Module des prochaines livraisons"""
        module = ttk.LabelFrame(parent, text="Prochaines Livraisons", padding=15, bootstyle="info")
        module.pack(fill=tk.BOTH, expand=True, pady=10)
        
        try:
            session = self.get_session()
            if session is None:
                ttk.Label(module, text="Connexion à la base de données requise", 
                         font=("Roboto", 12), foreground=self.text_color["muted"]).pack(pady=20)
                return
                
            # Récupérer les prochaines commandes à livrer
            current_datetime = datetime.now()
            prochaines_commandes = session.query(Commande).filter(
                Commande.date_livraison > current_datetime
            ).order_by(Commande.date_livraison).limit(4).all()
        except Exception as e:
            print(f"Erreur lors de la récupération des livraisons: {e}")
            prochaines_commandes = []
        
        if not prochaines_commandes:
            ttk.Label(module, text="Aucune livraison programmée", 
                     font=("Roboto", 12), foreground=self.text_color["muted"]).pack(pady=20)
            return
        
        # En-tête
        header_frame = ttk.Frame(module)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="Client", font=("Roboto", 10, "bold"),
                 foreground=self.text_color["dark"]).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(header_frame, text="Date", font=("Roboto", 10, "bold"),
                 foreground=self.text_color["dark"]).pack(side=tk.LEFT, padx=50)
        ttk.Label(header_frame, text="Service", font=("Roboto", 10, "bold"),
                 foreground=self.text_color["dark"]).pack(side=tk.RIGHT)
        
        ttk.Separator(module).pack(fill=tk.X, pady=(0, 10))
        
        # Liste des livraisons
        for commande in prochaines_commandes:
            item_frame = ttk.Frame(module)
            item_frame.pack(fill=tk.X, pady=5)
            
            # Nom du client
            try:
                client_nom = commande.client.nom if commande.client else f"Client-{commande.id_client}"
            except Exception:
                client_nom = f"Client-{getattr(commande, 'id_client', 'Inconnu')}"
                
            ttk.Label(item_frame, text=client_nom, font=("Roboto", 10),
                     foreground=self.text_color["dark"]).pack(side=tk.LEFT)
            
            # Date de livraison
            try:
                date_livr = commande.date_livraison.strftime("%d/%m %H:%M") if commande.date_livraison else "N/A"
            except Exception:
                date_livr = "N/A"
                
            ttk.Label(item_frame, text=date_livr, font=("Roboto", 10),
                     foreground=self.text_color["muted"]).pack(side=tk.LEFT, padx=50)
            
            # Service
            service = getattr(commande, 'nature_service', 'Transport') or "Transport"
            ttk.Label(item_frame, text=service[:15], font=("Roboto", 10),
                     foreground=getattr(self.style.colors, "info", "#17a2b8")).pack(side=tk.RIGHT)

    def create_commandes_table_module(self, parent, title, color):
        """Tableau des commandes avec données réelles"""
        module = ttk.LabelFrame(parent, text=title, padding=15, bootstyle=color)
        module.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Frame conteneur
        table_frame = ttk.Frame(module)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview
        columns = ("id_commande", "client", "nature_service", "type_vehicule", 
                  "quantite", "lieu_chargement", "date_commande", "date_livraison", "statut")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
        
        # En-têtes
        headers = {
            "id_commande": "ID",
            "client": "Client", 
            "nature_service": "Service",
            "type_vehicule": "Véhicule",
            "quantite": "Qté",
            "lieu_chargement": "Lieu Chargement",
            "date_commande": "Date Cmd",
            "date_livraison": "Date Livr",
            "statut": "Statut"
        }
        
        for col, header in headers.items():
            tree.heading(col, text=header)
            tree.column(col, width=80, minwidth=60)
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar_h = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Remplir avec données réelles
        self._populate_commandes_table(tree)
        
        return tree

    def _populate_commandes_table(self, tree):
        """Remplit le tableau des commandes avec des données réelles"""
        try:
            session = self.get_session()
            if session is None:
                tree.insert("", "end", values=("Erreur", "Connexion DB", "requise", "", "", "", "", "", ""))
                return
                
            commandes = session.query(Commande).order_by(Commande.date_commande.desc()).limit(20).all()
            current_datetime = datetime.now()
            
            for i, commande in enumerate(commandes):
                # Déterminer le statut de manière sécurisée
                try:
                    if commande.date_livraison is None:
                        statut = "Programmée"
                    elif hasattr(commande, 'est_en_retard') and commande.est_en_retard(current_datetime):
                        statut = "En retard"
                    elif commande.date_livraison > current_datetime:
                        statut = "En cours"
                    else:
                        statut = "Livrée"
                except Exception:
                    statut = "Inconnu"
                
                # Formatage des données de manière sécurisée
                try:
                    date_cmd = commande.date_commande.strftime("%d/%m/%Y") if commande.date_commande else "N/A"
                except Exception:
                    date_cmd = "N/A"
                    
                try:
                    date_livr = commande.date_livraison.strftime("%d/%m/%Y") if commande.date_livraison else "N/A"
                except Exception:
                    date_livr = "N/A"
                    
                try:
                    nom_client = commande.client.nom if commande.client else f"Client-{commande.id_client}"
                except Exception:
                    nom_client = f"Client-{getattr(commande, 'id_client', 'Inconnu')}"
                    
                try:
                    quantite_str = f"{commande.quantite_requise:.1f}" if commande.quantite_requise else "N/A"
                except Exception:
                    quantite_str = "N/A"
                
                values = (
                    getattr(commande, 'id_commande', 'N/A'),
                    nom_client,
                    getattr(commande, 'nature_service', 'N/A') or "N/A",
                    getattr(commande, 'type_vehicule', 'N/A') or "N/A",
                    quantite_str,
                    getattr(commande, 'lieu_chargement', 'N/A') or "N/A",
                    date_cmd,
                    date_livr,
                    statut
                )
                
                tree.insert("", "end", values=values, tags=(f"row{i}", statut.lower().replace(" ", "_")))
                
                # Alternance des couleurs
                if i % 2 == 0:
                    tree.tag_configure(f"row{i}", background="#f8f9fa")
            
            # Configuration des couleurs par statut
            tree.tag_configure("en_retard", foreground="#dc3545", font=("", "", "bold"))
            tree.tag_configure("en_cours", foreground="#fd7e14")
            tree.tag_configure("livrée", foreground="#198754")
            tree.tag_configure("programmée", foreground="#0d6efd")
            
        except Exception as e:
            print(f"Erreur lors de la récupération des commandes: {e}")
            # Afficher un message d'erreur dans le tableau
            tree.insert("", "end", values=("Erreur", "Impossible de charger", "les données", "", "", "", "", "", ""))

    def create_status_bar(self):
        """Barre d'état avec informations temps réel"""
        status_bar = ttk.Frame(self.root, bootstyle="light")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Copyright
        ttk.Label(status_bar, text="© 2025 - FleetManager Pro v2.0",
                 font=("Roboto", 9), foreground=self.text_color["dark"]).pack(side=tk.LEFT, padx=10, pady=5)
        
        # Statut système (vérifier la connexion DB)
        try:
            session = self.get_session()
            if session:
                session.query(Commande).count()
                system_status = "Système: En ligne"
                status_color = getattr(self.style.colors, "success", "#28a745")
            else:
                system_status = "Système: Hors ligne"
                status_color = getattr(self.style.colors, "danger", "#dc3545")
        except Exception:
            system_status = "Système: Hors ligne"
            status_color = getattr(self.style.colors, "danger", "#dc3545")
        
        ttk.Label(status_bar, text=system_status, font=("Roboto", 9, "bold"),
                 foreground=status_color).pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Dernière mise à jour
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        ttk.Label(status_bar, text=f"Dernière mise à jour: {now}",
                 font=("Roboto", 9), foreground=self.text_color["dark"]).pack(side=tk.RIGHT, padx=10, pady=5)

    def animate_startup(self):
        """Applique une simple animation de démarrage"""
        try:
            # Masquer tous les widgets existants temporairement
            self.content_area.update_idletasks()
            
            # Révéler progressivement les éléments
            delay = 100  # millisecondes
            
            def reveal_widgets():
                self.sidebar.pack(side=LEFT, fill=Y)
                self.root.after(delay, lambda: self.content_area.pack(side=LEFT, fill=BOTH, expand=True))
            
            # Lancer l'animation
            self.root.after(delay, reveal_widgets)
        except Exception:
            pass  # Ignorer les erreurs d'animation

    def show_dashboard(self):
        """Affiche le tableau de bord principal"""
        # Implémentation future pour basculer entre les vues
        pass

    # Méthodes pour ouvrir les différentes vues avec gestion d'erreur améliorée
    def open_equipement_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Gestion des Équipements")
            new_window.geometry("1200x800")
            from application.views.equipement_view import EquipementApp
            app = EquipementApp(new_window)
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
        except ImportError as e:
            print(f"Module equipement_view non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Équipement: {str(e)}")
            self.root.deiconify()

    def open_vehicule_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Gestion des Véhicules")
            new_window.geometry("1200x800")
            
            from application.views.vehicule_view import VehiculeApp
            app = VehiculeApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except ImportError as e:
            print(f"Module vehicule_view non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Véhicule: {str(e)}")
            self.root.deiconify()

    def open_tournee_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Gestion des Tournées")
            new_window.geometry("1200x800")
            
            from application.views.tournee_view import TourneeApp
            app = TourneeApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except ImportError as e:
            print(f"Module tournee_view non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Tournée: {str(e)}")
            self.root.deiconify()

    def open_conducteur_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Gestion des Conducteurs")
            new_window.geometry("1200x800")
            
            from application.views.conducteur_view import ConducteurApp
            app = ConducteurApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except ImportError as e:
            print(f"Module conducteur_view non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Conducteur: {str(e)}")
            self.root.deiconify()

    def open_commande_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Gestion des Commandes")
            new_window.geometry("1200x800")
            
            from application.views.commande_view import CommandeApp
            app = CommandeApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except ImportError as e:
            print(f"Module commande_view non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Commande: {str(e)}")
            self.root.deiconify()

    def open_affectation_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Affectations")
            new_window.geometry("1200x800")
            
            from application.views.affectation_view import AffectationApp
            app = AffectationApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except ImportError as e:
            print(f"Module affectation_view non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Affectation: {str(e)}")
            self.root.deiconify()

    def open_chantiers_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Gestion des Chantiers")
            new_window.geometry("1000x700")
            
            from application.views.chantiers_view import ChantierApp
            app = ChantierApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except ImportError as e:
            print(f"Module chantiers_view non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Chantier: {str(e)}")
            self.root.deiconify() 

    def open_transferer_equipement_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Gestion des DTM")
            new_window.geometry("1000x700")
            
            from application.views.transferer_equipement_view import TransfererEquipementApp
            app = TransfererEquipementApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except ImportError as e:
            print(f"Module transferer_equipement_view non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue DTM: {str(e)}")
            self.root.deiconify()

    def open_carte_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Carte")
            new_window.geometry("1200x800")
            
            from application.views.carte import CarteChantiers
            app = CarteChantiers(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except ImportError as e:
            print(f"Module carte non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Carte: {str(e)}")
            self.root.deiconify()
    
    def open_notification_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Notifications")
            new_window.geometry("1200x800")
            
            from application.views.notification import NotificationApp
            app = NotificationApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except ImportError as e:
            print(f"Module notification non trouvé: {str(e)}")
            self.root.deiconify()
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Notification: {str(e)}")
            self.root.deiconify()
    
    def on_view_close(self, window):
        """Ferme la fenêtre et réaffiche la principale"""
        try:
            window.destroy()
            self.root.deiconify()
            
            # Afficher un message de statut temporaire
            self.show_status_notification("Retour au tableau de bord principal")
        except Exception as e:
            print(f"Erreur lors de la fermeture de la vue: {e}")
            self.root.deiconify()
    
    def show_status_notification(self, message, duration=3000):
        """Affiche une notification temporaire dans la barre d'état"""
        try:
            # Créer un cadre de notification flottant
            notification = ttk.Frame(self.root, padding=10, bootstyle="info")
            
            # Positionner en bas au centre
            notification.place(relx=0.5, rely=0.95, anchor=CENTER)
            
            # Message avec icône
            notif_frame = ttk.Frame(notification)
            notif_frame.pack()
            
            # Icône (simulée)
            icon_canvas = tk.Canvas(notif_frame, width=20, height=20, 
                                  background=getattr(self.style.colors, "info", "#17a2b8"),
                                  highlightthickness=0)
            icon_canvas.pack(side=LEFT, padx=(0, 10))
            icon_canvas.create_oval(2, 2, 18, 18, fill=self.text_color["light"], outline="")
            icon_canvas.create_text(10, 10, text="i", font=("Roboto", 10, "bold"), 
                                  fill=getattr(self.style.colors, "info", "#17a2b8"))
            
            # Texte de notification
            ttk.Label(
                notif_frame,
                text=message,
                font=("Roboto", 11),
                bootstyle="light"
            ).pack(side=LEFT)
            
            # Faire disparaître après un délai
            self.root.after(duration, notification.destroy)
        except Exception as e:
            print(f"Erreur lors de l'affichage de la notification: {e}")


# Point d'entrée de l'application
if __name__ == "__main__":
    try:
        # Configurer le chemin d'accès aux modules
        module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if module_path not in sys.path:
            sys.path.append(module_path)
        
        # Lancer l'application avec un thème moderne
        root = ttk.Window(themename="flatly")  # Options: cosmo, litera, minty, lumen, sandstone, yeti, pulse, morph, superhero, darkly
        app = MainApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Erreur lors du lancement de l'application: {e}")
        # Fallback avec tkinter standard
        import tkinter as tk
        root = tk.Tk()
        root.title("FleetManager - Mode de compatibilité")
        tk.Label(root, text=f"Erreur de démarrage: {e}\nVeuillez vérifier l'installation de ttkbootstrap").pack(pady=50)
        root.mainloop()
