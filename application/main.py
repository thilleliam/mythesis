from sqlalchemy import Label
import ttkbootstrap as ttk
import tkinter as tk
from ttkbootstrap.constants import *
from tkinter import PhotoImage
import os
import sys
from PIL import Image, ImageTk
import random


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
        
        # Initialiser l'écran de connexion d'abord
        self.show_login_screen()
    
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
        
        # Zone des modules (dashboard)
        # Canvas scrollable dans content_area
        canvas = tk.Canvas(self.content_area, background="white", highlightthickness=0)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.content_area, orient=VERTICAL, command=canvas.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame qui contiendra les modules (scrollable)
        self.modules_frame = ttk.Frame(canvas, padding=10)
        canvas.create_window((0, 0), window=self.modules_frame, anchor="nw")

        # Mise à jour du scroll en fonction du contenu
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.modules_frame.bind("<Configure>", on_frame_configure)

        # Activer le scroll avec la molette
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        self.style.configure("ModernCard.TFrame",
            background="white",
            relief="flat",
            borderwidth=1
        )
        self.style.map("ModernCard.TFrame", background=[("active", "white")])

        # Créer les modules sous forme de cartes modernes
        self.create_module_cards()
        
        # Barre d'état inférieure
        self.create_status_bar()
        
        # Animation de démarrage
        self.animate_startup()
    
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
        notif_canvas = ttk.Canvas(actions_frame, width=16, height=16, background=self.root.cget("background"))
        notif_canvas.place(in_=notif_btn, x=25, y=3)
        notif_canvas.create_oval(0, 0, 16, 16, fill=self.style.colors.danger, outline="")
        notif_canvas.create_text(8, 8, text="3", fill=self.text_color["white"], font=("Roboto", 8, "bold"))
    
    def create_module_cards(self):
        """Crée des cartes modernes pour les modules"""
        # Utiliser un notebook avec onglets pour organiser le contenu
        notebook = ttk.Notebook(self.modules_frame)
        notebook.pack(fill=BOTH, expand=True)
        
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
        # Première rangée: statistiques générales
        stats_frame = ttk.Frame(dashboard_tab)
        stats_frame.pack(fill=X, pady=10)
        
        # KPI Cards
        kpi_data = [
            {"title": "Véhicules actifs", "value": "42", "change": "+5%", "icon": "truck", "color": "primary"},
            {"title": "DTM en cours", "value": "12", "change": "+2", "icon": "building", "color": "success"},
            {"title": "Tournées du jour", "value": "8", "change": "-1", "icon": "map", "color": "warning"},
            {"title": "Commandes à livrer", "value": "23", "change": "+15%", "icon": "clipboard", "color": "danger"}
        ]
        
        for kpi in kpi_data:
            self.create_kpi_card(stats_frame, kpi)
        
        # Deuxième rangée: modules principaux sur 2 colonnes
        modules_container = ttk.Frame(dashboard_tab)
        modules_container.pack(fill=BOTH, expand=True, pady=10)
        
        # Colonne gauche
        left_col = ttk.Frame(modules_container)
        left_col.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 5))
        
        # Colonne droite
        right_col = ttk.Frame(modules_container)
        right_col.pack(side=LEFT, fill=BOTH, expand=True, padx=(5, 0))
        
        # Ajouter les modules graphiques
        self.create_chart_module(left_col, "Disponibilité des véhicules", "primary")
        self.create_progress_module(right_col, "Statut des DTM", "success")
        self.create_list_module(left_col, "Prochaines tournées", "warning")
        self.create_table_module(right_col, "Dernières commandes", "danger")
    
    def create_kpi_card(self, parent, data):
        """Crée une carte KPI moderne et visible"""
        bg_color = "white"
        border_color = self.style.colors.get(data["color"])
        
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
            foreground=bg_color,
            background=bg_color
        ).pack(side="left")

        change_color = self.style.colors.success if "+" in data["change"] else self.style.colors.danger

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
        icon_canvas.create_text(18, 18, text=data["icon"][0].upper(), fill="white", font=("Roboto", 14, "bold"))

        
    def create_chart_module(self, parent, title, color):
        """Crée un module avec graphique"""
        module = ttk.LabelFrame(parent, text=title, padding=15, bootstyle=color)
        module.pack(fill=BOTH, expand=True, pady=10)
        
        # Canvas pour simuler un graphique
        chart_canvas = ttk.Canvas(module, width=400, height=200)
        chart_canvas.pack(fill=BOTH, expand=True)
        
        # Simuler un graphique en barres
        chart_colors = [self.style.colors.primary, self.style.colors.info, 
                     self.style.colors.warning, self.style.colors.success, 
                     self.style.colors.danger]
        
        bar_width = 50
        margin = 40
        chart_width = chart_canvas.winfo_reqwidth() - 2*margin
        chart_height = chart_canvas.winfo_reqheight() - 2*margin
        
        # Dessiner les axes
        chart_canvas.create_line(margin, margin, margin, chart_height+margin)
        chart_canvas.create_line(margin, chart_height+margin, chart_width+margin, chart_height+margin)
        
        # Dessiner les barres
        data = [75, 45, 80, 60, 90]
        max_value = max(data)
        bar_spacing = chart_width / (len(data) + 1)
        
        for i, value in enumerate(data):
            bar_height = (value / max_value) * chart_height
            x0 = margin + (i + 1) * bar_spacing - bar_width/2
            y0 = chart_height + margin - bar_height
            x1 = x0 + bar_width
            y1 = chart_height + margin
            
            chart_canvas.create_rectangle(x0, y0, x1, y1, 
                                      fill=chart_colors[i % len(chart_colors)], 
                                      outline="")
            
            # Ajouter la valeur au-dessus de la barre
            chart_canvas.create_text(x0 + bar_width/2, y0 - 10, 
                                  text=str(value) + "%", 
                                  font=("Roboto", 8),
                                  fill=self.text_color["dark"])
            
            # Ajouter l'étiquette
            labels = ["Lun", "Mar", "Mer", "Jeu", "Ven"]
            chart_canvas.create_text(x0 + bar_width/2, y1 + 15, 
                                  text=labels[i], 
                                  font=("Roboto", 8),
                                  fill=self.text_color["dark"])
    
    def create_progress_module(self, parent, title, color):
        """Crée un module avec barres de progression"""
        module = ttk.LabelFrame(parent, text=title, padding=15, bootstyle=color)
        module.pack(fill=BOTH, expand=True, pady=10)
        
        # Données de progression
        progress_data = [
            {"name": "Chantier EGS 100", "progress": 75, "color": "success"},
            {"name": "Chantier EGS 120", "progress": 45, "color": "primary"},
            {"name": "Chantier MMM", "progress": 90, "color": "warning"},
            {"name": "Chantier 100", "progress": 30, "color": "danger"},
            {"name": "Chantier 200", "progress": 60, "color": "info"}
        ]
        
        for item in progress_data:
            item_frame = ttk.Frame(module)
            item_frame.pack(fill=X, pady=5)
            
            # Nom et pourcentage
            label_frame = ttk.Frame(item_frame)
            label_frame.pack(fill=X)
            
            # Utiliser une couleur foncée pour les textes sur fond clair
            ttk.Label(
                label_frame,
                text=item["name"],
                font=("Roboto", 10),
                foreground=self.text_color["dark"]
            ).pack(side=LEFT)
            
            ttk.Label(
                label_frame,
                text=f"{item['progress']}%",
                font=("Roboto", 10, "bold"),
                foreground=self.style.colors.get(item["color"])
            ).pack(side=RIGHT)
            
            # Barre de progression
            progress = ttk.Progressbar(
                item_frame,
                value=item["progress"],
                bootstyle=item["color"]
            )
            progress.pack(fill=X, pady=(5, 0))

    def create_list_module(self, parent, title, color):
        """Crée un module avec liste d'éléments"""
        module = ttk.LabelFrame(parent, text=title, padding=15, bootstyle=color)
        module.pack(fill=BOTH, expand=True, pady=10)
        
        # En-tête de liste
        header_frame = ttk.Frame(module)
        header_frame.pack(fill=X, pady=(0, 10))
        
        # Utiliser des couleurs foncées pour les en-têtes sur fond clair
        ttk.Label(
            header_frame,
            text="Tournée",
            font=("Roboto", 10, "bold"),
            foreground=self.text_color["dark"]
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk.Label(
            header_frame,
            text="Date",
            font=("Roboto", 10, "bold"),
            foreground=self.text_color["dark"]
        ).pack(side=LEFT, padx=50)
        
        ttk.Label(
            header_frame,
            text="Statut",
            font=("Roboto", 10, "bold"),
            foreground=self.text_color["dark"]
        ).pack(side=RIGHT)
        
        # Séparateur
        ttk.Separator(module).pack(fill=X, pady=(0, 10))
        
        # Éléments de liste
        list_data = [
            {"name": "Tournée X", "date": "18/05/2025", "status": "À venir", "status_color": "info"},
            {"name": "Tournée Y", "date": "19/05/2025", "status": "Planifiée", "status_color": "primary"},
            {"name": "Tournée Z", "date": "20/05/2025", "status": "Planifiée", "status_color": "primary"},
            {"name": "Tournée A", "date": "21/05/2025", "status": "Attente", "status_color": "warning"}
        ]
        
        for item in list_data:
            item_frame = ttk.Frame(module)
            item_frame.pack(fill=X, pady=5)
            
            # Texte principal en couleur foncée
            ttk.Label(
                item_frame,
                text=item["name"],
                font=("Roboto", 10),
                foreground=self.text_color["dark"]
            ).pack(side=LEFT)
            
            # Date en couleur légèrement atténuée mais encore visible
            ttk.Label(
                item_frame,
                text=item["date"],
                font=("Roboto", 10),
                foreground=self.text_color["muted"]
            ).pack(side=LEFT, padx=50)
            
            # Badge de statut avec contraste amélioré
            status_frame = ttk.Frame(item_frame, bootstyle=f"{item['status_color']}-light")
            status_frame.pack(side=RIGHT, padx=2, pady=2)
            
            # S'assurer que le texte du statut est bien visible sur son fond
            status_label = ttk.Label(
                status_frame,
                text=item["status"],
                font=("Roboto", 9, "bold"),  # Ajout du bold pour améliorer la lisibilité
                padding=(5, 2),
                foreground=self.style.colors.get(item['status_color'])
            )
            status_label.pack()

    def create_table_module(self, parent, title, color):
        """Crée un module avec tableau"""
        module = ttk.LabelFrame(parent, text=title, padding=15, bootstyle=color)
        module.pack(fill=BOTH, expand=True, pady=10)
        
        # Créer un tableau avec Treeview
        columns = ("id", "client", "date", "montant", "statut")
        tree = ttk.Treeview(module, columns=columns, show="headings", height=5)
        
        # Définir les en-têtes
        tree.heading("id", text="ID")
        tree.heading("client", text="Client")
        tree.heading("date", text="Date")
        tree.heading("montant", text="Montant")
        tree.heading("statut", text="Statut")
        
        # Définir les largeurs de colonnes
        tree.column("id", width=50)
        tree.column("client", width=120)
        tree.column("date", width=80)
        tree.column("montant", width=80)
        tree.column("statut", width=80)
        
        # Insérer des données de test
        data = [
            ("CMD-001", "A", "17/05/2025", "1250 €", "Livrée"),
            ("CMD-002", " B", "16/05/2025", "890 €", "En cours"),
            ("CMD-003", " C", "15/05/2025", "2340 €", "En cours"),
            ("CMD-004", "D", "14/05/2025", "760 €", "Livrée"),
            ("CMD-005", "E", "13/05/2025", "1120 €", "Livrée")
        ]
        
        for i, item in enumerate(data):
            tree.insert("", END, values=item, tags=(f"row{i}",))
            if i % 2 == 0:
                tree.tag_configure(f"row{i}", background="#f5f5f5")
        
        tree.pack(fill=BOTH, expand=True)

    def create_status_bar(self):
        """Crée une barre d'état moderne"""
        status_bar = ttk.Frame(self.root, bootstyle="light")
        status_bar.pack(side=BOTTOM, fill=X)
        
        # Informations système - amélioration du contraste
        ttk.Label(
            status_bar,
            text="© 2025 - FleetManager Pro v2.0",
            font=("Roboto", 9),
            foreground=self.text_color["dark"]  # Utiliser une couleur foncée sur fond clair
        ).pack(side=LEFT, padx=10, pady=5)
        
        # Statut du système - s'assurer que le vert est visible
        ttk.Label(
            status_bar,
            text="Système: En ligne",
            font=("Roboto", 9, "bold"),  # Ajout du bold pour la visibilité
            foreground=self.style.colors.success
        ).pack(side=RIGHT, padx=10, pady=5)
        
        # Heure de dernière mise à jour
        ttk.Label(
            status_bar,
            text="Dernière mise à jour: 17/05/2025 14:30",
            font=("Roboto", 9),
            foreground=self.text_color["dark"]  # Utiliser une couleur foncée sur fond clair
        ).pack(side=RIGHT, padx=10, pady=5)

    def animate_startup(self):
        """Applique une simple animation de démarrage"""
        # Masquer tous les widgets existants temporairement
        self.content_area.update_idletasks()
        
        # Révéler progressivement les éléments
        delay = 100  # millisecondes
        
        def reveal_widgets():
            self.sidebar.pack(side=LEFT, fill=Y)
            self.root.after(delay, lambda: self.content_area.pack(side=LEFT, fill=BOTH, expand=True))
        
        # Lancer l'animation
        self.root.after(delay, reveal_widgets)

    def show_dashboard(self):
        """Affiche le tableau de bord principal"""
        # Implémentation future pour basculer entre les vues
        pass

    # Méthodes pour ouvrir les différentes vues
    def open_equipement_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Gestion des Équipements")
            new_window.geometry("1200x800")
            from application.views.equipement_view import EquipementApp
            app = EquipementApp(new_window)
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Équipement: {str(e)}")
            self.root.deiconify()

    def open_vehicule_view(self):
        try:
            self.root.withdraw()  # Cacher la fenêtre principale
            new_window = ttk.Toplevel(title="Gestion des Véhicules")
            new_window.geometry("1200x800")
            
            # Import local pour éviter les imports circulaires
            from application.views.vehicule_view import VehiculeApp
            app = VehiculeApp(new_window)
            
            # Quand la fenêtre est fermée, réafficher la principale
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Chantier: {str(e)}")
            self.root.deiconify()

    def open_tournee_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Gestion des Tournées")
            new_window.geometry("1200x800")
            
            from application.views.tournee_view import TourneeApp
            app = TourneeApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
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
            
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Chantier: {str(e)}")
            self.root.deiconify()

    def open_carte_view(self):
        try:
            self.root.withdraw()
            new_window = ttk.Toplevel(title="Carte")
            new_window.geometry("1200x800")
            
            from application.views.carte import CarteApp
            app = CarteApp(new_window)
            
            new_window.protocol("WM_DELETE_WINDOW", lambda: self.on_view_close(new_window))
            
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
            
        except Exception as e:
            print(f"Erreur lors de l'ouverture de la vue Notification: {str(e)}")
            self.root.deiconify()
    
    def on_view_close(self, window):
        # Ferme la fenêtre et réaffiche la principale
        window.destroy()
        self.root.deiconify()
        
        # Afficher un message de statut temporaire
        self.show_status_notification("Retour au tableau de bord principal")
    
    def show_status_notification(self, message, duration=3000):
        """Affiche une notification temporaire dans la barre d'état"""
        # Créer un cadre de notification flottant
        notification = ttk.Frame(self.root, padding=10, bootstyle="info")
        
        # Positionner en bas au centre
        notification.place(relx=0.5, rely=0.95, anchor=CENTER)
        
        # Message avec icône
        notif_frame = ttk.Frame(notification)
        notif_frame.pack()
        
        # Icône (simulée)
        icon_canvas = ttk.Canvas(notif_frame, width=20, height=20, background=self.style.colors.info)
        icon_canvas.pack(side=LEFT, padx=(0, 10))
        icon_canvas.create_oval(2, 2, 18, 18, fill=self.style.colors.light, outline="")
        icon_canvas.create_text(10, 10, text="i", font=("Roboto", 10, "bold"), fill=self.style.colors.info)
        
        # Texte de notification
        ttk.Label(
            notif_frame,
            text=message,
            font=("Roboto", 11),
            bootstyle="light"
        ).pack(side=LEFT)
        
        # Faire disparaître après un délai
        self.root.after(duration, notification.destroy)


# Point d'entrée de l'application
if __name__ == "__main__":
    # Configurer le chemin d'accès aux modules
    module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if module_path not in sys.path:
        sys.path.append(module_path)
    
    # Lancer l'application avec un thème moderne
    root = ttk.Window(themename="flatly")  # Options: cosmo, litera, minty, lumen, sandstone, yeti, pulse, morph, superhero, darkly
    app = MainApp(root)
    root.mainloop()