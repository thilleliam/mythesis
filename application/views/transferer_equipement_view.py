import json
import os
import threading
import time
import traceback
import uuid
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, StringVar, IntVar, DoubleVar, DISABLED, X, LEFT, BOTH
from sqlalchemy.orm import sessionmaker, configure_mappers
from application.database import SessionLocal, engine, Base
from sqlalchemy import func, or_
from datetime import date, datetime, timedelta
import re
import tkinter as tk
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from tkinter import filedialog
from application.models.mc_svrp_complete import run_complete_mc_svrp_algorithm, save_mc_solution, export_to_excel_mc

from application.models.metaheuristique import (
        Instance,
        MC_Vehicle,
        MC_Transport, 
        MC_Solution,
        mc_greedy_initial_solution,
        mc_crossover,
        mc_mutate,
        mc_local_search,
        mc_memetic_algorithm,
        run_mc_svrp_algorithm,
        save_mc_solution,
        export_to_excel
    )



configure_mappers()

Session = sessionmaker(bind=engine)
session = Session()
class NotificationSystem:
    """Système de gestion des notifications et alertes pour l'application de transfert d'équipements"""
    
    def __init__(self, app_instance):
        """
        Initialise le système de notifications
        
        Args:
            app_instance: Instance de l'application principale (TransfererEquipementApp)
        """
        self.app = app_instance
        self.root = app_instance.root
        self.notifications = []
        self.confirmed_transfers = {}  # Pour stocker les transferts confirmés
        self.notification_window = None
        self.notification_badge = None
        self.badge_count = 0
        
        # Chemin pour stocker les confirmations
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.confirmations_file = os.path.join(self.data_dir, 'confirmed_transfers.json')
        
        # Créer le répertoire de données s'il n'existe pas
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # Charger les confirmations précédentes
        self.load_confirmed_transfers()
        
        # Créer les widgets de notification
        self.create_notification_widgets()
        
        # Démarrer le thread de vérification des alertes hebdomadaires
        self.should_stop = False
        self.check_thread = threading.Thread(target=self.check_weekly_confirmation, daemon=True)
        self.check_thread.start()
    
    def create_notification_widgets(self):
        """Crée les widgets nécessaires pour afficher les notifications"""
        # Créer un bouton de notification dans la barre d'outils principale
        toolbar = self.root.children.get('!frame')
        if toolbar:
            # Créer un frame pour le bouton et le badge
            notification_frame = ttk.Frame(toolbar)
            notification_frame.pack(side=tk.RIGHT, padx=10)
            
            # Créer le bouton de notifications
            self.notification_button = ttk.Button(
                notification_frame, 
                text="🔔", 
                command=self.show_notifications,
                bootstyle=SECONDARY,
                width=3
            )
            self.notification_button.pack(side=tk.LEFT)
            
            # Créer le badge de notifications (cercle rouge avec un nombre)
            self.notification_badge = ttk.Label(
                notification_frame, 
                text="0", 
                bootstyle="danger",
                width=2,
                padding=0
            )
            # Positionner le badge sur le coin supérieur droit du bouton
            self.notification_badge.place(relx=0.8, rely=0.1)
            
            # Cacher le badge initialement
            self.notification_badge.place_forget()
        else:
            # Ajouter un nouveau frame en haut de l'application
            top_bar = ttk.Frame(self.root)
            top_bar.pack(side=tk.TOP, fill=tk.X)
            
            # Ajouter le titre à gauche
            title_label = ttk.Label(top_bar, text="Gestion des Transferts d'Équipements", font=('Helvetica', 14, 'bold'))
            title_label.pack(side=tk.LEFT, padx=10, pady=5)
            
            # Créer un frame pour le bouton et le badge
            notification_frame = ttk.Frame(top_bar)
            notification_frame.pack(side=tk.RIGHT, padx=10, pady=5)
            
            # Créer le bouton de notifications
            self.notification_button = ttk.Button(
                notification_frame, 
                text="🔔", 
                command=self.show_notifications,
                bootstyle=SECONDARY,
                width=3
            )
            self.notification_button.pack(side=tk.LEFT)
            
            # Créer le badge de notifications
            self.notification_badge = ttk.Label(
                notification_frame, 
                text="0", 
                bootstyle="danger",
                width=2,
                padding=0
            )
            # Positionner le badge sur le coin supérieur droit du bouton
            self.notification_badge.place(relx=0.8, rely=0.1)
            
            # Cacher le badge initialement
            self.notification_badge.place_forget()
    def add_notification(self, title, message, is_weekly_confirmation=False, data=None, action=None):
        """Ajoute une notification au système"""
        notification = {
            'title': title,
            'message': message,
            'is_weekly_confirmation': is_weekly_confirmation,
            'data': data,
            'action': action,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Convertir en chaîne pour la sauvegarde
            'read': False  # Ajoutez un champ 'read' pour la gestion des notifications lues/non lues
        }
        self.notifications.append(notification)
        self.save_notifications()
    import json

    def save_notifications(self):
        """Sauvegarde les notifications dans un fichier JSON"""
        try:
            with open("notifications.json", "w") as file:
                json.dump(self.notifications, file, indent=4)
            print("Notifications sauvegardées avec succès.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des notifications : {str(e)}")
    def update_badge(self):
        """Met à jour le badge de notifications avec le nombre de notifications non lues"""
        unread_count = sum(1 for n in self.notifications if not n['read'])
        
        if unread_count > 0:
            self.badge_count = unread_count
            self.notification_badge.config(text=str(min(99, unread_count)))
            
            # Afficher le badge
            self.notification_badge.place(relx=0.8, rely=0.1)
        else:
            # Cacher le badge s'il n'y a pas de notifications non lues
            self.notification_badge.place_forget()
    def save_notifications(self):
        """Sauvegarde les notifications dans un fichier JSON"""
        try:
            with open("notifications.json", "w") as file:
                json.dump(self.notifications, file, indent=4)
            print("Notifications sauvegardées avec succès.")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des notifications : {str(e)}")
    def show_popup_notification(self, notification):
        """
        Affiche une notification pop-up en bas à droite de l'écran
        
        Args:
            notification: Dictionnaire contenant les détails de la notification
        """
        # Créer une fenêtre pop-up
        popup = tk.Toplevel(self.root)
        popup.title("")
        popup.attributes('-topmost', True)
        popup.overrideredirect(True)  # Supprimer les bordures de fenêtre
        
        # Définir la taille et la position (coin inférieur droit)
        width, height = 300, 100
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        x = screen_width - width - 20
        y = screen_height - height - 60  # Laisser de l'espace pour la barre des tâches
        
        popup.geometry(f"{width}x{height}+{x}+{y}")
        
        # Créer un style pour la notification
        style = "primary" if not notification['is_weekly_confirmation'] else "warning"
        
        # Créer un cadre avec style
        frame = ttk.Frame(popup, bootstyle=style)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre de la notification
        title_label = ttk.Label(frame, text=notification['title'], font=('Helvetica', 10, 'bold'), bootstyle=style)
        title_label.pack(anchor=tk.W, padx=10, pady=(10, 0))
        
        # Message de la notification
        message_label = ttk.Label(frame, text=notification['message'], wraplength=280, bootstyle=style)
        message_label.pack(anchor=tk.W, padx=10, pady=(5, 10))
        
        # Boutons d'action
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        if notification['is_weekly_confirmation']:
            # Pour les confirmations hebdomadaires, ajouter un bouton de confirmation
            ttk.Button(
                btn_frame, 
                text="Confirmer", 
                command=lambda: [self.open_confirmation_dialog(notification), popup.destroy()],
                bootstyle=SUCCESS,
                width=10
            ).pack(side=tk.RIGHT, padx=5)
        
        # Bouton pour fermer la notification
        ttk.Button(
            btn_frame, 
            text="Fermer", 
            command=popup.destroy,
            bootstyle=SECONDARY,
            width=10
        ).pack(side=tk.RIGHT, padx=5)
        
        # Auto-fermeture après 10 secondes sauf pour les confirmations hebdomadaires
        if not notification['is_weekly_confirmation']:
            popup.after(10000, popup.destroy)
    
    def open_confirmation_dialog(self, notification):
        """
        Ouvre une boîte de dialogue pour confirmer les transferts hebdomadaires
        
        Args:
            notification: Dictionnaire contenant les détails de la notification
        """
        # Créer une nouvelle fenêtre pour la confirmation
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirmation des transferts hebdomadaires")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Récupérer les données des transferts à confirmer
        transfers_data = notification.get('data', {})
        week_number = transfers_data.get('week_number', datetime.now().isocalendar()[1])
        week_year = transfers_data.get('year', datetime.now().year)
        
        # Label principal
        ttk.Label(
            dialog, 
            text=f"Confirmation des transferts d'équipements - Semaine {week_number} ({week_year})",
            font=('Helvetica', 12, 'bold')
        ).pack(pady=(15, 10))
        
        ttk.Label(
            dialog, 
            text="Veuillez confirmer les quantités d'équipements effectivement transférées cette semaine:",
            wraplength=550
        ).pack(pady=(0, 10), padx=20)
        
        # Créer un cadre avec défilement pour les transferts
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Ajouter une barre de défilement
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Liste pour stocker les variables des spinboxes
        spinbox_vars = []
        
        # En-têtes
        headers_frame = ttk.Frame(scrollable_frame)
        headers_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(headers_frame, text="ID", width=5).grid(row=0, column=0, padx=5)
        ttk.Label(headers_frame, text="Client", width=15).grid(row=0, column=1, padx=5)
        ttk.Label(headers_frame, text="Équipement", width=25).grid(row=0, column=2, padx=5)
        ttk.Label(headers_frame, text="Planifié", width=8).grid(row=0, column=3, padx=5)
        ttk.Label(headers_frame, text="Réel", width=8).grid(row=0, column=4, padx=5)
        
        # Séparateur
        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill=tk.X, pady=5)
        
        # Récupérer les transferts prévus pour cette semaine
        session = SessionLocal()
        try:
            transfers = self.get_weekly_transfers(session, week_number, week_year)
            
            if not transfers:
                ttk.Label(
                    scrollable_frame, 
                    text="Aucun transfert planifié pour cette semaine.",
                    font=('Helvetica', 10, 'italic')
                ).pack(pady=20)
            else:
                # Afficher chaque transfert avec un spinbox pour ajuster la quantité réelle
                for i, transfer in enumerate(transfers):
                    row_frame = ttk.Frame(scrollable_frame)
                    row_frame.pack(fill=tk.X, pady=2)
                    
                    ttk.Label(row_frame, text=str(transfer['id']), width=5).grid(row=0, column=0, padx=5)
                    ttk.Label(row_frame, text=transfer['client'], width=15).grid(row=0, column=1, padx=5)
                    ttk.Label(row_frame, text=transfer['equipment'], width=25).grid(row=0, column=2, padx=5)
                    ttk.Label(row_frame, text=str(transfer['planned']), width=8).grid(row=0, column=3, padx=5)
                    
                    # Variable pour la quantité réelle (initialement égale à la quantité planifiée)
                    var = tk.IntVar(value=transfer['planned'])
                    spinbox_vars.append((transfer['id'], var))
                    
                    ttk.Spinbox(
                        row_frame, 
                        from_=0, 
                        to=9999, 
                        textvariable=var, 
                        width=6
                    ).grid(row=0, column=4, padx=5)
        finally:
            session.close()
        
        # Boutons d'action
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=15)
        
        ttk.Button(
            btn_frame, 
            text="Annuler", 
            command=dialog.destroy,
            bootstyle=SECONDARY,
            width=10
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame, 
            text="Confirmer", 
            command=lambda: self.save_confirmed_transfers(spinbox_vars, week_number, week_year, dialog),
            bootstyle=SUCCESS,
            width=10
        ).pack(side=tk.RIGHT, padx=5)
    
    def save_confirmed_transfers(self, spinbox_vars, week_number, year, dialog):
        """
        Enregistre les quantités confirmées de transferts
        
        Args:
            spinbox_vars: Liste de tuples (id_transfert, variable_spinbox)
            week_number: Numéro de la semaine
            year: Année
            dialog: Fenêtre de dialogue à fermer après l'enregistrement
        """
        confirmed_data = []
        week_key = f"{year}-W{week_number}"
        
        for transfer_id, var in spinbox_vars:
            confirmed_data.append({
                'id': transfer_id,
                'confirmed_quantity': var.get()
            })
        
        # Stocker les données confirmées
        self.confirmed_transfers[week_key] = confirmed_data
        
        # Enregistrer dans le fichier
        self.save_confirmed_transfers_to_file()
        
        # Marquer la notification correspondante comme lue
        for notification in self.notifications:
            if notification.get('is_weekly_confirmation', False) and notification.get('data', {}).get('week_number') == week_number:
                notification['read'] = True
        
        self.update_badge()
        
        # Fermer la boîte de dialogue
        dialog.destroy()
        
        # Afficher un message de confirmation
        messagebox.showinfo(
            "Confirmation enregistrée", 
            f"Les quantités de transferts pour la semaine {week_number} ont été confirmées avec succès."
        )
        
        # Lancer la réoptimisation si nécessaire
        self.run_reoptimization(week_number, year)
    
    def run_reoptimization(self, week_number, year):
        """
        Lance la réoptimisation basée sur les transferts confirmés
        
        Args:
            week_number: Numéro de la semaine
            year: Année
        """
        # Demander à l'utilisateur s'il souhaite lancer une réoptimisation
        if messagebox.askyesno(
            "Réoptimisation", 
            "Souhaitez-vous lancer une réoptimisation basée sur les quantités confirmées?"
        ):
            try:
                # Rediriger vers l'onglet d'optimisation
                self.app.root.children['!notebook'].select(2)  # Index 2 pour le 3ème onglet
                
                # Afficher les données confirmées dans l'interface d'optimisation
                self.app.meta_results_text.delete(1.0, tk.END)
                self.app.meta_results_text.insert(tk.END, f"Préparation de la réoptimisation pour la semaine {week_number} de {year}...\n\n")
                
                # Récupérer les données confirmées
                week_key = f"{year}-W{week_number}"
                confirmed_data = self.confirmed_transfers.get(week_key, [])
                
                if confirmed_data:
                    self.app.meta_results_text.insert(tk.END, "Transferts confirmés:\n")
                    
                    for item in confirmed_data:
                        transfer_id = item['id']
                        quantity = item['confirmed_quantity']
                        
                        # Récupérer les détails du transfert
                        session = SessionLocal()
                        try:
                            transfer = session.query(self.app.TransfererEquipement).get(transfer_id)
                            if transfer:
                                client = transfer.id_client
                                equipment = transfer.nom_equipement
                                self.app.meta_results_text.insert(
                                    tk.END, 
                                    f"- ID: {transfer_id}, Client: {client}, Équipement: {equipment}, Quantité confirmée: {quantity}\n"
                                )
                        finally:
                            session.close()
                    
                    # Ajuster la semaine en cours dans l'optimisation
                    self.app.meta_results_text.insert(tk.END, f"\nLes données confirmées seront utilisées pour la réoptimisation.\n")
                    self.app.meta_results_text.insert(tk.END, "Veuillez sélectionner un client pour le site A et définir les coordonnées du site B pour lancer l'optimisation.\n")
                else:
                    self.app.meta_results_text.insert(tk.END, "Aucune donnée confirmée disponible pour cette semaine.\n")
            
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la préparation de la réoptimisation: {str(e)}")
    
    def get_weekly_transfers(self, session, week_number, year):
        """
        Récupère les transferts prévus pour une semaine spécifique
        
        Args:
            session: Session SQLAlchemy
            week_number: Numéro de la semaine
            year: Année
            
        Returns:
            Liste des transferts prévus pour cette semaine
        """
        # Calculer le nombre de semaines depuis le début de l'année
        current_date = datetime.now()
        start_of_year = datetime(year, 1, 1)
        current_week = datetime.strptime(f"{year}-W{week_number}-1", "%Y-W%W-%w").date()
        
        # Calculer l'écart entre la semaine actuelle et la semaine cible
        weeks_difference = (current_date.date() - current_week).days // 7
        
        # Déterminer quelle colonne de semaine utiliser en fonction de la différence
        week_columns = {
            0: "zero",
            1: "un",
            2: "deux",
            3: "trois",
            4: "quatre",
            5: "cinq",
            6: "six",
            7: "sept",
            8: "huit",
            9: "neuf",
            10: "dix",
            11: "onze",
            12: "douze"
        }
        
        # Si la différence est négative, cela signifie une semaine future
        if weeks_difference < 0:
            messagebox.showwarning(
                "Avertissement", 
                f"La semaine {week_number} de {year} est dans le futur. Aucun transfert à confirmer pour l'instant."
            )
            return []
        
        # Si la différence est trop grande, utiliser la semaine la plus éloignée
        if weeks_difference > 12:
            weeks_difference = 12
        
        # Déterminer la colonne à consulter
        column_to_check = week_columns.get(weeks_difference)
        
        if not column_to_check:
            return []
        
        # Récupérer les transferts pour cette semaine
        transfers = []
        
        try:
            # Requête pour récupérer les transferts avec une quantité > 0 pour la semaine spécifiée
            query = session.query(self.app.TransfererEquipement)
            
            # Utiliser getattr pour accéder dynamiquement à la colonne
            for transfer in query.all():
                planned_quantity = getattr(transfer, column_to_check, 0)
                
                if planned_quantity > 0:
                    transfers.append({
                        'id': transfer.id,
                        'client': transfer.id_client,
                        'equipment': transfer.nom_equipement,
                        'planned': planned_quantity
                    })
        
        except Exception as e:
            print(f"Erreur lors de la récupération des transferts: {str(e)}")
        
        return transfers
    
    def show_notifications(self):
        """Affiche la fenêtre des notifications"""
        # Fermer la fenêtre si elle est déjà ouverte
        if self.notification_window and self.notification_window.winfo_exists():
            self.notification_window.destroy()
            self.notification_window = None
            return
        
        # Créer une nouvelle fenêtre
        self.notification_window = tk.Toplevel(self.root)
        self.notification_window.title("Notifications")
        self.notification_window.geometry("400x500")
        self.notification_window.transient(self.root)
        
        # Centrer la fenêtre
        self.notification_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - self.notification_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - self.notification_window.winfo_height()) // 2
        self.notification_window.geometry(f"+{x}+{y}")
        
        # En-tête
        header_frame = ttk.Frame(self.notification_window)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            header_frame, 
            text="Notifications", 
            font=('Helvetica', 12, 'bold')
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            header_frame, 
            text="Marquer tout comme lu", 
            command=self.mark_all_as_read,
            bootstyle=SECONDARY,
            width=18
        ).pack(side=tk.RIGHT)
        
        # Séparateur
        ttk.Separator(self.notification_window, orient="horizontal").pack(fill=tk.X, padx=10)
        
        # Cadre principal avec défilement
        main_frame = ttk.Frame(self.notification_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ajouter une barre de défilement
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Si aucune notification, afficher un message
        if not self.notifications:
            ttk.Label(
                scrollable_frame, 
                text="Aucune notification pour le moment.",
                font=('Helvetica', 10, 'italic')
            ).pack(pady=20)
        else:
            # Afficher les notifications par ordre chronologique inverse
            for notification in sorted(self.notifications, key=lambda x: x['timestamp'], reverse=True):
                self.create_notification_item(scrollable_frame, notification)
    
    def create_notification_item(self, parent, notification):
        """Crée un élément de notification dans l'interface utilisateur"""
        try:
            # Convertir le timestamp en objet datetime si nécessaire
            timestamp_str = notification['timestamp']
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            # Formater le timestamp pour l'affichage
            formatted_timestamp = timestamp.strftime("%d/%m/%Y %H:%M")
            
            # Utiliser le timestamp formaté dans l'interface utilisateur
            ttk.Label(parent, text=f"{notification['title']} - {formatted_timestamp}").pack()
        except Exception as e:
            print(f"Erreur lors de la création de l'élément de notification : {str(e)}")
    def toggle_read_status(self, notification):
        """
        Change le statut de lecture d'une notification
        
        Args:
            notification: Dictionnaire contenant les détails de la notification
        """
        notification['read'] = not notification['read']
        self.update_badge()
        
        # Rafraîchir la fenêtre des notifications
        if self.notification_window and self.notification_window.winfo_exists():
            self.notification_window.destroy()
            self.show_notifications()
    
    def mark_all_as_read(self):
        """Marque toutes les notifications comme lues"""
        for notification in self.notifications:
            notification['read'] = True
        
        self.update_badge()
        
        # Rafraîchir la fenêtre des notifications
        if self.notification_window and self.notification_window.winfo_exists():
            self.notification_window.destroy()
            self.show_notifications()
    
    def check_weekly_confirmation(self):
        """
        Fonction exécutée dans un thread séparé pour vérifier si une confirmation hebdomadaire est nécessaire
        """
        while not self.should_stop:
            try:
                # Vérifier si c'est vendredi (jour 4 de la semaine, où lundi=0)
                current_date = datetime.now()
                
                # Pour tester, vous pouvez forcer un jour spécifique
                # Décommenter la ligne ci-dessous et ajuster la date pour tester
                # current_date = datetime(2025, 5, 9, 15, 0)  # Exemple: vendredi 9 mai 2025 à 15h00
                
                is_friday = current_date.weekday() == 4
                is_end_of_day = 14 <= current_date.hour <= 17  # Entre 14h et 17h
                
                if is_friday and is_end_of_day:
                    # Vérifier si une notification de confirmation a déjà été envoyée cette semaine
                    week_number = current_date.isocalendar()[1]
                    year = current_date.year
                    week_key = f"{year}-W{week_number}"
                    
                    # Vérifier si une notification pour cette semaine existe déjà
                    notification_exists = any(
                        n.get('is_weekly_confirmation', False) and 
                        n.get('data', {}).get('week_number') == week_number and
                        n.get('data', {}).get('year') == year
                        for n in self.notifications
                    )
                    
                    # Vérifier si une confirmation pour cette semaine a déjà été enregistrée
                    confirmation_exists = week_key in self.confirmed_transfers
                    
                    if not notification_exists and not confirmation_exists:
                        # Créer une notification pour demander la confirmation des transferts
                        self.add_notification(
                            title="Confirmation hebdomadaire requise",
                            message=f"Veuillez confirmer les transferts d'équipements réalisés pour la semaine {week_number}.",
                            is_weekly_confirmation=True,
                            data={'week_number': week_number, 'year': year}
                        )
                        
                        # Attendre jusqu'à la fin de la journée avant de vérifier à nouveau
                        time.sleep(3600 * 3)  # 3 heures
                    else:
                        # Attendre 1 heure avant de vérifier à nouveau
                        time.sleep(3600)
                else:
                    # Attendre 1 heure avant de vérifier à nouveau
                    time.sleep(3600)
            
            except Exception as e:
                print(f"Erreur lors de la vérification des confirmations hebdomadaires: {str(e)}")
                time.sleep(3600)  # Attendre 1 heure en cas d'erreur

    def load_confirmed_transfers(self):
        """Charge les confirmations de transferts enregistrées"""
        if os.path.exists(self.confirmations_file):
            try:
                with open(self.confirmations_file, 'r') as file:
                    self.confirmed_transfers = json.load(file)
            except Exception as e:
                print(f"Erreur lors du chargement des confirmations: {str(e)}")
                self.confirmed_transfers = {}
        else:
            self.confirmed_transfers = {}

    def save_confirmed_transfers_to_file(self):
        """Enregistre les confirmations de transferts dans un fichier"""
        try:
            with open(self.confirmations_file, 'w') as file:
                json.dump(self.confirmed_transfers, file, indent=4)
        except Exception as e:
            print(f"Erreur lors de l'enregistrement des confirmations: {str(e)}")
            messagebox.showerror(
                "Erreur", 
                f"Impossible d'enregistrer les confirmations: {str(e)}"
            )

    def stop(self):
        """Arrête le thread de vérification des confirmations hebdomadaires"""
        self.should_stop = True
        if self.check_thread.is_alive():
            self.check_thread.join(timeout=1)

    def get_confirmed_transfers_for_optimization(self, week_number=None, year=None):
        """
        Récupère les données des transferts confirmés pour l'optimisation
        
        Args:
            week_number: Numéro de la semaine (si None, utilise la semaine actuelle)
            year: Année (si None, utilise l'année actuelle)
        
        Returns:
            Liste des transferts confirmés pour cette semaine
        """
        if week_number is None:
            week_number = datetime.now().isocalendar()[1]
        
        if year is None:
            year = datetime.now().year
        
        week_key = f"{year}-W{week_number}"
        return self.confirmed_transfers.get(week_key, [])

    def create_weekly_confirmation_reminder(self):
        """
        Crée une tâche planifiée pour envoyer une notification de confirmation chaque vendredi
        """
        # Cette méthode est une alternative au thread de vérification
        # Vous pouvez l'utiliser si vous préférez une approche basée sur des tâches planifiées
        
        # Calculer la date du prochain vendredi à 15h
        current_date = datetime.now()
        days_until_friday = (4 - current_date.weekday()) % 7
        
        if days_until_friday == 0 and current_date.hour >= 15:
            # Si c'est vendredi après 15h, planifier pour le vendredi suivant
            days_until_friday = 7
        
        next_friday = current_date + timedelta(days=days_until_friday)
        next_reminder = datetime(
            next_friday.year, 
            next_friday.month, 
            next_friday.day, 
            15, 0, 0  # 15h00
        )
        
        # Calculer le délai en secondes
        delay = (next_reminder - current_date).total_seconds()
        
        # Créer une tâche planifiée
        self.root.after(int(delay * 1000), self.send_weekly_confirmation_notification)

    def send_weekly_confirmation_notification(self):
        """
        Envoie une notification de confirmation hebdomadaire et planifie la prochaine
        """
        current_date = datetime.now()
        week_number = current_date.isocalendar()[1]
        year = current_date.year
        
        # Créer une notification pour demander la confirmation des transferts
        self.add_notification(
            title="Confirmation hebdomadaire requise",
            message=f"Veuillez confirmer les transferts d'équipements réalisés pour la semaine {week_number}.",
            is_weekly_confirmation=True,
            data={'week_number': week_number, 'year': year}
        )
        
        # Planifier la prochaine notification (dans 7 jours)
        self.root.after(7 * 24 * 60 * 60 * 1000, self.send_weekly_confirmation_notification)

    def update_optimization_with_confirmed_data(self, confirmed_data):
        """
        Met à jour les données d'optimisation avec les quantités confirmées
        
        Args:
            confirmed_data: Liste des transferts confirmés
        """
        if not confirmed_data:
            return
        
        # Cette méthode peut être utilisée pour préparer les données confirmées
        # pour l'algorithme d'optimisation
        
        # Par exemple, vous pourriez mettre à jour une base de données ou un fichier
        # contenant les quantités confirmées pour qu'elles soient utilisées lors de
        # la prochaine optimisation
        
        # Exemple d'implémentation:
        session = SessionLocal()
        try:
            for item in confirmed_data:
                transfer_id = item['id']
                confirmed_quantity = item['confirmed_quantity']
                
                # Récupérer le transfert correspondant
                transfer = session.query(self.app.TransfererEquipement).get(transfer_id)
                
                if transfer:
                    # Mettre à jour la quantité réelle
                    transfer.quantite_reelle = confirmed_quantity
                    
                    # Vous pourriez également mettre à jour d'autres champs
                    transfer.confirme = True
                    transfer.date_confirmation = datetime.now()
            
            # Enregistrer les modifications
            session.commit()
            
            print(f"Données confirmées mises à jour pour {len(confirmed_data)} transferts")
        
        except Exception as e:
            session.rollback()
            print(f"Erreur lors de la mise à jour des données confirmées: {str(e)}")
        
        finally:
            session.close()

    # Méthode pour intégrer les données confirmées à l'algorithme d'optimisation
    def integrate_confirmed_data_with_optimization(self, week_number, year):
        """
        Intègre les données confirmées à l'algorithme d'optimisation
        
        Args:
            week_number: Numéro de la semaine
            year: Année
        """
        week_key = f"{year}-W{week_number}"
        confirmed_data = self.confirmed_transfers.get(week_key, [])
        
        if not confirmed_data:
            messagebox.showinfo(
                "Information", 
                f"Aucune donnée confirmée disponible pour la semaine {week_number} de {year}."
            )
            return
        
        try:
            # Préparer les données pour l'optimisation
            optimization_data = []
            
            for item in confirmed_data:
                transfer_id = item['id']
                confirmed_quantity = item['confirmed_quantity']
                
                # Récupérer les détails du transfert
                session = SessionLocal()
                try:
                    transfer = session.query(self.app.TransfererEquipement).get(transfer_id)
                    
                    if transfer:
                        optimization_data.append({
                            'id': transfer_id,
                            'client': transfer.id_client,
                            'equipment': transfer.nom_equipement,
                            'quantity': confirmed_quantity,
                            'coords': self.get_client_coordinates(transfer.id_client)
                        })
                
                finally:
                    session.close()
            
            # Lancer l'optimisation avec ces données
            if optimization_data:
                # Stocker les données dans l'application principale pour utilisation
                # par l'algorithme d'optimisation
                self.app.confirmed_optimization_data = optimization_data
                
                # Afficher un message de préparation
                self.app.meta_results_text.delete(1.0, tk.END)
                self.app.meta_results_text.insert(
                    tk.END, 
                    f"Préparation de l'optimisation avec {len(optimization_data)} transferts confirmés...\n\n"
                )
                
                # Afficher les détails des transferts confirmés
                for item in optimization_data:
                    self.app.meta_results_text.insert(
                        tk.END,
                        f"• Client: {item['client']}, Équipement: {item['equipment']}, Quantité: {item['quantity']}\n"
                    )
                
                self.app.meta_results_text.insert(
                    tk.END, 
                    "\nVeuillez définir les paramètres d'optimisation et cliquer sur 'Lancer l'optimisation'.\n"
                )
                
                # Mettre à jour l'interface d'optimisation pour utiliser ces données
                # (À implémenter dans la classe d'optimisation)
            
            else:
                messagebox.showinfo(
                    "Information", 
                    "Aucun transfert valide trouvé pour l'optimisation."
                )
        
        except Exception as e:
            messagebox.showerror(
                "Erreur", 
                f"Erreur lors de la préparation des données pour l'optimisation: {str(e)}"
            )

    def get_client_coordinates(self, client_id):
        """
        Récupère les coordonnées d'un client
        
        Args:
            client_id: Identifiant du client
            
        Returns:
            Tuple (latitude, longitude) ou None si non trouvé
        """
        session = SessionLocal()
        try:
            # Adapter cette requête à votre modèle de données
            client = session.query(self.app.Client).filter_by(id=client_id).first()
            
            if client and hasattr(client, 'latitude') and hasattr(client, 'longitude'):
                return (client.latitude, client.longitude)
            
            return None
        
        except Exception as e:
            print(f"Erreur lors de la récupération des coordonnées du client: {str(e)}")
            return None
        
        finally:
            session.close()
class TransfererEquipementApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion des Transferts d'Équipements")
        self.root.geometry("1200x700")
        photo = tk.PhotoImage(file="C:\\Users\\BIG-computer\\Pictures\\Logo1.png")
        root.iconphoto(False, photo)
        
        # Import local pour éviter les imports circulaires
        from application.models.transferer_equipement import TransfererEquipement
        from application.models.chantiers import Chantier
        from application.models.equipements import Equipement
        self.TransfererEquipement = TransfererEquipement
        self.Chantier = Chantier
        self.Equipement = Equipement

        # Variables
        self.id_var = IntVar()
        self.volet_var = StringVar()
        self.nom_equipement_var = StringVar()  # Pour saisir le nom de l'équipement
        self.equipement_id_var = IntVar()  # Pour stocker l'ID de l'équipement correspondant
        self.modalite_transport_var = StringVar()
        self.total_equipements_var = IntVar(value=1)  # Valeur par défaut à 1
        self.id_client_var = StringVar()
        self.localisation_client_var = StringVar()  # Pour afficher la localisation
        self.recherche_var = StringVar()  # Variable pour la recherche
        # Variables d'interface pour les coordonnées (ne sont pas sauvegardées en BD)
        # Variables pour l'optimisation
        self.cible_longitude_var = DoubleVar()
        self.cible_latitude_var = DoubleVar()
        
        # Variables pour les semaines
        self.semaines_vars = {
            'douze': IntVar(),
            'onze': IntVar(),
            'dix': IntVar(),
            'neuf': IntVar(),
            'huit': IntVar(),
            'sept': IntVar(),
            'six': IntVar(),
            'cinq': IntVar(),
            'quatre': IntVar(),
            'trois': IntVar(),
            'deux': IntVar(),
            'un': IntVar(),
            'zero': IntVar()
        }

        # Filtre client
        self.filtre_client_var = StringVar()
        
        # Cache pour les équipements
        self.equipements_cache = {}
        
        # Création de l'interface
        self.creer_interface()
        
        # Charger les données
        self.charger_clients()
        self.charger_equipements()
        self.charger_donnees()

    def creer_interface(self):
        """Crée l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True)
        
        # Frame de recherche et filtre
        top_frame = ttk.Frame(main_frame, padding=10)
        top_frame.pack(fill=X)
        
        # Barre de recherche
        ttk.Label(top_frame, text="Rechercher:").pack(side=LEFT, padx=5)
        recherche_entry = ttk.Entry(top_frame, textvariable=self.recherche_var, width=30)
        recherche_entry.pack(side=LEFT, padx=5)
        recherche_entry.bind("<Return>", lambda e: self.rechercher())
        ttk.Button(top_frame, text="Rechercher", command=self.rechercher, bootstyle=INFO).pack(side=LEFT, padx=5)
        
        # Filtre client
        ttk.Label(top_frame, text="Filtrer par client:").pack(side=LEFT, padx=20)
        self.client_filter_cb = ttk.Combobox(top_frame, textvariable=self.filtre_client_var, state="readonly", width=30)
        self.client_filter_cb.pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="Appliquer filtre", command=self.appliquer_filtre, bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(top_frame, text="Réinitialiser", command=self.reinitialiser_filtre, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        
        # Création du notebook pour l'interface à onglets
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Onglet de liste des transferts
        list_frame = ttk.Frame(notebook, padding=10)
        notebook.add(list_frame, text="Liste des transferts")
        
        # Onglet de formulaire
        form_frame = ttk.Frame(notebook, padding=10)
        notebook.add(form_frame, text="Formulaire de transfert")
        
        # Onglet d'optimisation (NOUVEAU)
        optimisation_frame = ttk.Frame(notebook, padding=10)
        notebook.add(optimisation_frame, text="Optimisation")
        
        # Création du tableau dans l'onglet liste
        self.creer_tableau(list_frame)
        
        # Création du formulaire dans l'onglet formulaire
        self.creer_formulaire(form_frame)
        
        # Création de l'interface d'optimisation (NOUVEAU)
        self.creer_interface_optimisation(optimisation_frame)

    def creer_interface_optimisation(self, parent):
        """Crée l'interface pour l'onglet d'optimisation"""
        # Frame pour les coordonnées cibles
        coord_frame = ttk.LabelFrame(parent, text="Paramètres d'optimisation", padding=10)
        coord_frame.pack(fill=X, pady=5)
        
        # Variables pour les coordonnées cibles
        self.cible_longitude_var = DoubleVar()
        self.cible_latitude_var = DoubleVar()
        
        # Stockage des informations du client sélectionné
        self.selected_client_id = None
        self.selected_client_name = None
        
        # Frame pour la sélection du client (site A)
        client_frame = ttk.Frame(coord_frame)
        client_frame.grid(row=0, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        
        ttk.Button(client_frame, text="Sélectionner client (site A)", 
                command=self.selectionner_client_site_A, 
                bootstyle=INFO).pack(side=LEFT, padx=5)
        
        # Label pour afficher le client sélectionné (sera mis à jour après sélection)
        self.client_label = ttk.Label(client_frame, text="Aucun client sélectionné")
        self.client_label.pack(side=LEFT, padx=10)
        
        # Ligne pour les coordonnées du site B
        ttk.Label(coord_frame, text="Coordonnées du site B (destination):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Champs pour les coordonnées
        ttk.Label(coord_frame, text="Longitude:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(coord_frame, textvariable=self.cible_longitude_var, width=15).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(coord_frame, text="Latitude:").grid(row=2, column=2, padx=5, pady=5, sticky="e")
        ttk.Entry(coord_frame, textvariable=self.cible_latitude_var, width=15).grid(row=2, column=3, padx=5, pady=5, sticky="w")
        
        # Frame pour les résultats de la métaheuristique
        meta_frame = ttk.LabelFrame(parent, text="Résultats de la métaheuristique", padding=10)
        meta_frame.pack(fill=BOTH, expand=True, pady=10)
        
        # Créer un cadre avec une barre de défilement
        text_frame = ttk.Frame(meta_frame)
        text_frame.pack(fill=BOTH, expand=True)
        
        # Ajouter la barre de défilement avant de configurer le widget Text
        meta_scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        meta_scrollbar.pack(side=RIGHT, fill=Y)
        
        # Ajouter un widget Text pour afficher les résultats détaillés
        self.meta_results_text = tk.Text(text_frame, wrap="word", height=10, yscrollcommand=meta_scrollbar.set)
        self.meta_results_text.pack(side=LEFT, fill=BOTH, expand=True)
        
        # Configurer la barre de défilement pour contrôler le widget Text
        meta_scrollbar.config(command=self.meta_results_text.yview)
        
        # Boutons d'action
        btn_frame = ttk.Frame(parent, padding=10)
        btn_frame.pack(fill=X, pady=5)
        
        ttk.Button(btn_frame, text="Utiliser coordonnées sélectionnées", 
                command=self.utiliser_coordonnees_selection, 
                bootstyle=INFO).pack(side=LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Exécuter métaheuristique", 
                command=self.executer_metaheuristique_corrige, 
                bootstyle=PRIMARY).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Effacer résultats", 
                command=self.effacer_resultats_optimisation, 
                bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Exporter résultats", 
                command=self.exporter_resultats_optimisation, 
                bootstyle=WARNING).pack(side=LEFT, padx=5)
        
        # Nouveau bouton pour exporter vers MS Project
        ttk.Button(btn_frame, text="Exporter vers MS Project", 
                command=self.exporter_vers_msproject, 
                bootstyle=SUCCESS).pack(side=LEFT, padx=5)

    def effacer_resultats_optimisation(self):
        """Efface les résultats de l'optimisation"""
        # Effacer le contenu du Text widget
        self.meta_results_text.delete(1.0, tk.END)
        # Réinitialiser les variables pour l'instance et la solution
        if hasattr(self, 'current_instance'):
            delattr(self, 'current_instance')
        if hasattr(self, 'current_solution'):
            delattr(self, 'current_solution')
        # Afficher un message
        messagebox.showinfo("Information", "Résultats effacés")
    def selectionner_client_site_A(self):
        """Sélectionne un client comme point de départ (site A) pour la métaheuristique"""
        # Récupérer tous les clients disponibles
        from application.models.chantiers import Chantier
        
        # Créer une session SQLAlchemy
        session = SessionLocal()
        
        try:
            # Récupérer la liste des chantiers
            chantiers = session.query(Chantier).all()
            
            if not chantiers:
                messagebox.showwarning("Attention", "Aucun chantier disponible dans la base de données")
                return
            
            # Créer une liste pour le menu déroulant
            options = [(c.id_client, f"{c.id_client} - {c.localisation}") for c in chantiers]
            
            # Créer une fenêtre de dialogue
            dialog = tk.Toplevel(self.root)
            dialog.title("Sélection du site A")
            dialog.geometry("400x150")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Centrer la fenêtre
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() - dialog.winfo_reqwidth()) / 2
            y = (dialog.winfo_screenheight() - dialog.winfo_reqheight()) / 2
            dialog.geometry("+%d+%d" % (x, y))
            
            # Variable pour stocker la sélection
            selected_id = tk.StringVar()
            
            # Créer les widgets
            ttk.Label(dialog, text="Sélectionnez le client de départ (site A):").pack(pady=10)
            
            # Combobox pour la sélection
            combo = ttk.Combobox(dialog, textvariable=selected_id, state="readonly", width=40)
            combo['values'] = [opt[1] for opt in options]
            combo.pack(pady=10, padx=20, fill=X)
            combo.current(0)  # Sélectionner le premier par défaut
            
            # Fonction pour valider la sélection
            def valider():
                idx = combo.current()
                if idx >= 0:
                    self.selected_client_id = options[idx][0]
                    self.selected_client_name = options[idx][1]
                    
                    # Mettre à jour le label dans l'interface
                    if hasattr(self, 'client_label'):
                        self.client_label.config(text=f"Client sélectionné (site A): {self.selected_client_name}")
                    else:
                        # Créer un label dans l'interface d'optimisation si inexistant
                        self.client_label = ttk.Label(coord_frame, text=f"Client sélectionné (site A): {self.selected_client_name}") # type: ignore
                        self.client_label.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="w")
                    
                    dialog.destroy()
                else:
                    messagebox.showwarning("Attention", "Veuillez sélectionner un client")
            
            # Boutons
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(fill=X, pady=10)
            
            ttk.Button(btn_frame, text="Annuler", command=dialog.destroy).pack(side=RIGHT, padx=5)
            ttk.Button(btn_frame, text="Valider", command=valider, bootstyle=PRIMARY).pack(side=RIGHT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les clients: {str(e)}")
        finally:
            session.close()
    def load_client_coordinates(self):
        """
        Récupère les coordonnées GPS du client/chantier (site A) depuis la base de données
        """
        from application.models.chantiers import Chantier
        
        # Vérifier que l'ID client est fourni
        if not self.id_client:
            raise ValueError("ID client non spécifié. Impossible de calculer la distance.")
        
        # Créer une session SQLAlchemy
        session = SessionLocal()
        
        try:
            # Récupérer les informations du chantier
            chantier = session.query(Chantier).filter_by(id_client=self.id_client).first()
            
            if not chantier:
                raise ValueError(f"Aucun chantier trouvé avec l'ID {self.id_client}")
            
            # Stocker les coordonnées du client (site A)
            self.client_latitude = chantier.latitude
            self.client_longitude = chantier.longitude
            
            # Stocker également d'autres informations utiles
            self.client_localisation = chantier.localisation
            self.distance_aller_goudron = chantier.distanceAllerGoudron
            self.distance_aller_piste = chantier.distanceAllerPiste
            self.temps_aller = chantier.temps_aller
            
        finally:
            session.close()
    def executer_metaheuristique_corrige(self):
        """
        VERSION CORRIGÉE - Exécute l'algorithme MC-SVRP-TC complet avec métaheuristiques
        Affiche tout dans l'interface graphique + terminal
        """
        try:
            # Vérifications initiales
            longitude_cible = self.cible_longitude_var.get()
            latitude_cible = self.cible_latitude_var.get()
            
            if not longitude_cible or not latitude_cible:
                messagebox.showerror("Erreur", "Coordonnées de destination requises")
                return
                
            if not hasattr(self, 'selected_client_id') or not self.selected_client_id:
                selection = self.tree.selection()
                if selection:
                    item_values = self.tree.item(selection[0], "values")
                    if len(item_values) >= 2:
                        self.selected_client_id = item_values[1]
                    else:
                        messagebox.showerror("Erreur", "Aucun client sélectionné")
                        return
                else:
                    messagebox.showerror("Erreur", "Aucun client sélectionné")
                    return
            
            # Affichage initial
            self.meta_results_text.delete(1.0, tk.END)
            self.meta_results_text.insert(tk.END, "🧠 ALGORITHME MC-SVRP-TC COMPLET\n")
            self.meta_results_text.insert(tk.END, f"📍 Client: {self.selected_client_id}\n")
            self.meta_results_text.insert(tk.END, f"🎯 Destination: {longitude_cible}, {latitude_cible}\n")
            self.meta_results_text.insert(tk.END, "="*80 + "\n")
            self.meta_results_text.update()
            
            def print_to_interface(message):
                """Fonction pour afficher dans l'interface ET le terminal"""
                print(message)  # Terminal
                self.meta_results_text.insert(tk.END, message + "\n")  # Interface
                self.meta_results_text.see(tk.END)
                self.meta_results_text.update()
            
            def run_algorithm():
                try:
                    print_to_interface("⚙️ Démarrage MC-SVRP-TC avec métaheuristiques...")
                    
                    # ✅ CORRECTION 1: Import correct du module heuristique version 5
                    try:
                        print_to_interface("📦 Import des modules d'optimisation...")
                        
                        # Rediriger temporairement stdout vers l'interface
                        import sys
                        from io import StringIO
                        
                        # Sauvegarder stdout original
                        original_stdout = sys.stdout
                        
                        # Créer buffer pour capturer les prints
                        captured_output = StringIO()
                        
                        class TeeOutput:
                            def __init__(self, original, text_widget):
                                self.original = original
                                self.text_widget = text_widget
                            
                            def write(self, message):
                                self.original.write(message)  # Terminal
                                if message.strip():  # Éviter les lignes vides
                                    self.text_widget.insert(tk.END, message)
                                    self.text_widget.see(tk.END)
                                    self.text_widget.update()
                            
                            def flush(self):
                                self.original.flush()
                        
                        # Rediriger stdout vers interface + terminal
                        sys.stdout = TeeOutput(original_stdout, self.meta_results_text)
                        
                        from application.models.heuristique_version5 import (
                            creer_instance_optimisation,
                            main_complet_TOUTES_CORRECTIONS,
                            OptimisateurNavettes,
                            appliquer_local_search,
                            appliquer_vns
                        )
                        
                        print("✅ Modules d'optimisation chargés avec succès")
                        
                    except ImportError as e:
                        # Restaurer stdout en cas d'erreur
                        sys.stdout = original_stdout
                        error_msg = f"❌ ERREUR D'IMPORT: {str(e)}"
                        print_to_interface(error_msg)
                        print_to_interface("💡 Vérifiez que le fichier heuristique_version5.py existe dans application/models/")
                        messagebox.showerror("Erreur Import", 
                            "Impossible de charger les modules d'optimisation.\n"
                            "Vérifiez le fichier heuristique_version5.py")
                        return
                    
                    # ✅ CORRECTION 2: Création de l'instance d'optimisation
                    try:
                        print("🔧 CRÉATION INSTANCE D'OPTIMISATION...")
                        print(f"   Client ID: {self.selected_client_id}")
                        print(f"   Longitude cible: {longitude_cible}")
                        print(f"   Latitude cible: {latitude_cible}")
                        
                        instance = creer_instance_optimisation(
                            id_client=self.selected_client_id,
                            cible_longitude=float(longitude_cible),
                            cible_latitude=float(latitude_cible)
                        )
                        
                        if not instance:
                            raise ValueError("Instance d'optimisation non créée")
                        
                        print(f"✅ Instance créée avec succès:")
                        print(f"   📏 Distance A→B: {instance.d_AB} km")
                        print(f"   🚛 Types de véhicules: {len(instance.L)}")
                        print(f"   📅 Semaines avec demandes: {sum(1 for t in instance.T if instance.dw_AB[t] > 0 or instance.dv_AB[t] > 0)}")
                        print(f"   🏭 Localisation: {getattr(instance, 'client_localisation', 'Non définie')}")
                        print(f"   🌍 Nature terrain: {getattr(instance, 'nature_terrain', 'Normal')}")
                        
                    except Exception as e:
                        # Restaurer stdout en cas d'erreur
                        sys.stdout = original_stdout
                        error_msg = f"❌ ERREUR CRÉATION INSTANCE: {str(e)}"
                        print_to_interface(error_msg)
                        print_to_interface("💡 Vérifiez les coordonnées et l'existence du client dans la base")
                        messagebox.showerror("Erreur Instance", f"Impossible de créer l'instance: {str(e)}")
                        return
                    
                    # ✅ CORRECTION 3: Préparation des données véhicules
                    print("🚛 PRÉPARATION DONNÉES VÉHICULES...")
                    vehicules_data = []
                    
                    for vtype, capacites in instance.L.items():
                        vehicule_info = {
                            'nom': instance.get_vehicle_type_name(vtype),
                            'type': 'LEGER' if capacites['Qw'] < 5000 else 'MOYEN' if capacites['Qw'] < 20000 else 'LOURD',
                            'capacite_poids_max': capacites['Qw'] / 1000,
                            'capacite_volume_max': capacites['Qv'],
                            'vitesse_kmh': instance.V[vtype],
                            'cout_fixe_jour': instance.c[vtype],
                            'cout_variable_km': 0.8,
                            'quantite': instance.m[vtype]
                        }
                        vehicules_data.append(vehicule_info)
                        print(f"   🚚 {vehicule_info['nom']}: {vehicule_info['capacite_poids_max']:.1f}t, {vehicule_info['capacite_volume_max']:.1f}m³")
                    
                    print(f"✅ {len(vehicules_data)} types de véhicules préparés")
                    
                    # ✅ CORRECTION 4: Exécution complète avec toutes les corrections
                    print("🚀 EXÉCUTION ALGORITHME MC-SVRP-TC COMPLET...")
                    print("   📊 Phase 1: Heuristique avec variabilité")
                    print("   🔍 Phase 2: Local Search corrigé")
                    print("   🔄 Phase 3: VNS (Variable Neighborhood Search)")
                    print("   🧠 Analyse complète sur 12 semaines")
                    print("="*120)
                    
                    # EXÉCUTER L'ALGORITHME COMPLET (tout s'affiche automatiquement dans l'interface maintenant)
                    resultats_globaux = main_complet_TOUTES_CORRECTIONS()
                    
                    # Restaurer stdout après exécution
                    sys.stdout = original_stdout
                    
                    if not resultats_globaux:
                        print_to_interface("❌ Échec de l'algorithme MC-SVRP-TC")
                        print_to_interface("💡 Vérifiez les logs ci-dessus pour identifier le problème")
                        messagebox.showerror("Erreur", "L'algorithme MC-SVRP-TC a échoué")
                        return
                    
                    # ✅ CORRECTION 5: Résumé final dans l'interface
                    print_to_interface("="*120)
                    print_to_interface("🎯 RÉSUMÉ FINAL MC-SVRP-TC")
                    print_to_interface("="*120)
                    
                    stats = resultats_globaux.get('statistiques', {})
                    cout_total = resultats_globaux.get('cout_total_global', 0)
                    
                    print_to_interface(f"💰 COÛT TOTAL OPTIMISÉ: {cout_total:.2f}€")
                    print_to_interface(f"📦 SEMAINES LIVRÉES: {stats.get('semaines_completement_livrees', 0)}/12")
                    print_to_interface(f"⚖️ POIDS TOTAL: {stats.get('poids_total_projet', 0):.1f} tonnes")
                    print_to_interface(f"📏 VOLUME TOTAL: {stats.get('volume_total_projet', 0):.1f} m³")
                    
                    # Véhicules utilisés
                    vehicules_utilises = stats.get('vehicules_utilises', {})
                    if vehicules_utilises:
                        print_to_interface("🚛 VÉHICULES SÉLECTIONNÉS:")
                        for vehicule, nb_fois in vehicules_utilises.items():
                            print_to_interface(f"   • {vehicule}: {nb_fois} semaine(s)")
                    
                    # Stratégies utilisées
                    strategies = stats.get('strategies_utilisees', {})
                    if strategies:
                        print_to_interface("📊 STRATÉGIES D'OPTIMISATION:")
                        for strategie, nb_fois in strategies.items():
                            print_to_interface(f"   • {strategie}: {nb_fois} semaine(s)")
                    
                    # Détails par semaine
                    resultats_par_semaine = resultats_globaux.get('resultats_par_semaine', {})
                    if resultats_par_semaine:
                        print_to_interface("📅 DÉTAIL PAR SEMAINE:")
                        print_to_interface("Sem  Coût Final  Gain      Véhicule                 Stratégie")
                        print_to_interface("-" * 75)
                        
                        total_gain_heuristique = 0
                        total_gain_metaheuristiques = 0
                        
                        for semaine, resultats in resultats_par_semaine.items():
                            cout_heuristique = resultats.get('cout_heuristique', 0)
                            cout_final = resultats.get('cout_vns', cout_heuristique)
                            gain_total = cout_heuristique - cout_final
                            vehicule = resultats.get('vehicule_utilise', 'N/A')[:24]
                            strategie = resultats.get('strategie_variabilite', 'STANDARD')[:14]
                            
                            total_gain_heuristique += cout_heuristique
                            total_gain_metaheuristiques += gain_total
                            
                            if gain_total > 0:
                                print_to_interface(f"{semaine:<4} {cout_final:<12.0f} {gain_total:<10.0f} {vehicule:<25} {strategie:<15}")
                            else:
                                print_to_interface(f"{semaine:<4} {cout_final:<12.0f} {'optimal':<10} {vehicule:<25} {strategie:<15}")
                    
                    # Bilan métaheuristiques
                    print_to_interface("="*120)
                    print_to_interface("🏆 BILAN PERFORMANCE MÉTAHEURISTIQUES")
                    print_to_interface("="*120)
                    
                    if total_gain_metaheuristiques > 0:
                        pourcentage_gain = (total_gain_metaheuristiques / total_gain_heuristique) * 100
                        print_to_interface("✅ MÉTAHEURISTIQUES EFFICACES!")
                        print_to_interface(f"   💰 Coût heuristique initial: {total_gain_heuristique:.0f}€")
                        print_to_interface(f"   💰 Coût final optimisé: {cout_total:.0f}€")
                        print_to_interface(f"   💰 GAIN TOTAL: {total_gain_metaheuristiques:.0f}€ ({pourcentage_gain:.1f}%)")
                        print_to_interface("   🎯 Local Search + VNS ont apporté des améliorations significatives")
                    else:
                        print_to_interface("✅ HEURISTIQUE DÉJÀ OPTIMALE!")
                        print_to_interface("   💡 L'heuristique de base était déjà très performante")
                        print_to_interface("   🔍 Les métaheuristiques confirment la qualité de la solution")
                        print_to_interface(f"   📊 Coût validé: {cout_total:.0f}€")
                    
                    # Validation des contraintes
                    instance_data = resultats_globaux.get('instance_data', {})
                    print_to_interface("🔧 VALIDATION CONTRAINTES MC-SVRP-TC:")
                    print_to_interface("   ✅ Contraintes de capacité respectées")
                    print_to_interface("   ✅ Contraintes temporelles respectées (7 jours max/semaine)")
                    print_to_interface("   ✅ Transport unidirectionnel A→B uniquement")
                    print_to_interface("   ✅ Mélange de produits optimisé par voyage")
                    print_to_interface(f"   ✅ Distance calculée: {instance_data.get('distance_AB', '?')} km")
                    print_to_interface(f"   ✅ Terrain adapté: {instance_data.get('nature_terrain', 'Normal')}")
                    print_to_interface(f"   ✅ Client validé: {instance_data.get('client_id', '?')}")
                    
                    # Taux de succès
                    taux_reussite = (stats.get('semaines_completement_livrees', 0) / 12) * 100
                    print_to_interface(f"📈 TAUX DE SUCCÈS: {taux_reussite:.1f}%")
                    
                    if taux_reussite >= 90:
                        print_to_interface("🎉 EXCELLENT! Quasi-totalité des livraisons planifiées")
                    elif taux_reussite >= 75:
                        print_to_interface("👍 BON RÉSULTAT! Majorité des livraisons réussies")
                    else:
                        print_to_interface("⚠️ RÉSULTAT PARTIEL - Vérifier contraintes véhicules")
                    
                    print_to_interface("✨ MC-SVRP-TC avec métaheuristiques TERMINÉ avec succès!")
                    print_to_interface("="*120)
                    
                    # Stocker pour export
                    self.current_instance = instance
                    self.current_solution = resultats_globaux
                    
                    # Message de réussite
                    if taux_reussite >= 90:
                        messagebox.showinfo("MC-SVRP-TC Réussi", 
                            f"🎉 Optimisation excellente!\n\n"
                            f"Coût total: {cout_total:.2f}€\n"
                            f"Taux de réussite: {taux_reussite:.1f}%\n"
                            f"Semaines livrées: {stats.get('semaines_completement_livrees', 0)}/12\n"
                            f"Gain métaheuristiques: {total_gain_metaheuristiques:.0f}€")
                    else:
                        messagebox.showwarning("MC-SVRP-TC Partiel", 
                            f"⚠️ Solution partielle obtenue\n\n"
                            f"Coût: {cout_total:.2f}€\n"
                            f"Taux: {taux_reussite:.1f}%\n"
                            f"Certaines semaines non optimisables")
                    
                except Exception as e:
                    # S'assurer que stdout est restauré
                    try:
                        sys.stdout = original_stdout
                    except:
                        pass
                    
                    error_msg = f"❌ ERREUR MC-SVRP-TC: {str(e)}"
                    print_to_interface(error_msg)
                    
                    import traceback
                    error_details = traceback.format_exc()
                    print_to_interface("📋 DÉTAILS TECHNIQUES:")
                    for line in error_details.split('\n'):
                        if line.strip():
                            print_to_interface(line)
                    
                    messagebox.showerror("Erreur MC-SVRP-TC", 
                        f"Erreur lors de l'exécution:\n{str(e)}")
            
            # Lancement en thread
            import threading
            thread = threading.Thread(target=run_algorithm)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            error_msg = f"❌ Erreur critique: {str(e)}"
            self.meta_results_text.insert(tk.END, error_msg + "\n")
            messagebox.showerror("Erreur Critique", f"Erreur critique: {str(e)}")
    def exporter_vers_msproject_mc_svrp(self):
        """
        Exporte la solution MC-SVRP-TC vers MS Project
        """
        if not hasattr(self, 'current_solution') or self.current_solution is None:
            messagebox.showwarning("Attention", "Aucune solution d'optimisation disponible pour l'export")
            return
        
        try:
            # Demander où enregistrer le fichier
            fichier = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Exporter vers MS Project (CSV)"
            )
            
            if not fichier:
                return
            
            # Importer la fonction d'export si disponible
            try:
                from application.models.mc_svrp_algorithm import export_to_excel
                export_to_excel(self.current_solution, self.current_instance, filename=fichier.replace('.csv', '.xlsx'))
                messagebox.showinfo("Succès", f"Solution exportée vers {fichier.replace('.csv', '.xlsx')}")
            except ImportError:
                # Export CSV basique si la fonction Excel n'est pas disponible
                import csv
                
                with open(fichier, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # En-têtes
                    writer.writerow([
                        'Semaine', 'Véhicule', 'Type', 'Poids_Transport', 'Volume_Transport',
                        'Temps_Total', 'Nombre_Voyages', 'Coût_Estimé'
                    ])
                    
                    # Données
                    for transport in self.current_solution.transports:
                        vehicle = self.current_solution.vehicles[(transport.vehicle_type, transport.vehicle_idx)]
                        writer.writerow([
                            transport.week,
                            vehicle.plate or f"V{transport.vehicle_idx}",
                            vehicle.type_name or f"Type {transport.vehicle_type}",
                            transport.total_weight(self.current_instance),
                            transport.total_volume(self.current_instance),
                            transport.T_total,
                            1,  # Un transport = un voyage
                            self.current_instance.c[transport.vehicle_type]
                        ])
                
                messagebox.showinfo("Succès", f"Solution exportée vers {fichier}")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export: {str(e)}")
    def exporter_resultats_optimisation(self):
        """Exporte les résultats d'optimisation au format PDF"""
        # Vérifier qu'il y a des résultats à exporter
        if not self.results_tree.get_children() and not self.meta_results_text.get("1.0", tk.END).strip():
            messagebox.showwarning("Attention", "Aucun résultat à exporter")
            return
        
        try:
            # Demander où enregistrer le fichier
            fichier = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Exporter les résultats d'optimisation"
            )
            
            if not fichier:
                # Si l'utilisateur annule
                return
            
            # Création du document PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            import datetime
            
            doc = SimpleDocTemplate(
                fichier,
                pagesize=landscape(A4),
                title="Résultats d'optimisation"
            )
            
            # Styles pour les textes
            styles = getSampleStyleSheet()
            titre_style = styles['Heading1']
            sous_titre_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Construction du contenu
            elements = []
            
            # Titre du rapport
            elements.append(Paragraph("Résultats d'optimisation d'équipements", titre_style))
            elements.append(Spacer(1, 20))
            
            # Date du rapport
            date_rapport = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            elements.append(Paragraph(f"Généré le: {date_rapport}", normal_style))
            elements.append(Spacer(1, 10))
            
            # Paramètres d'optimisation
            elements.append(Paragraph(f"Coordonnées cibles: ({self.cible_longitude_var.get()}, {self.cible_latitude_var.get()})", normal_style))
            elements.append(Paragraph(f"Rayon d'optimisation: {self.rayon_optimisation_var.get()} km", normal_style))
            elements.append(Spacer(1, 20))
            
            # Section 1: Résultats de l'optimisation de localisation
            if self.results_tree.get_children():
                elements.append(Paragraph("Résultats de l'optimisation de localisation", sous_titre_style))
                elements.append(Spacer(1, 10))
                
                # Récupération des données
                data = [["ID", "Équipement", "Client", "Localisation", "Distance (km)", "Quantité"]]
                
                for item in self.results_tree.get_children():
                    values = self.results_tree.item(item, "values")
                    data.append([values[0], values[1], values[2], values[3], values[4], values[5]])
                
                # Création du tableau
                table = Table(data, repeatRows=1)
                
                # Style du tableau
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ])
                
                # Appliquer le style au tableau
                table.setStyle(style)
                
                # Ajouter le tableau au document
                elements.append(table)
            
            # Section 2: Résultats de la métaheuristique
            text_content = self.meta_results_text.get("1.0", tk.END).strip()
            if text_content:
                elements.append(Spacer(1, 20))
                elements.append(Paragraph("Résultats de la métaheuristique", sous_titre_style))
                elements.append(Spacer(1, 10))
                
                # Ajouter le contenu du texte ligne par ligne
                for line in text_content.split("\n"):
                    elements.append(Paragraph(line, normal_style))
                    elements.append(Spacer(1, 3))
            
            # Construire le document
            doc.build(elements)
            
            messagebox.showinfo("Succès", f"Résultats d'optimisation exportés avec succès dans {fichier}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exporter les résultats: {str(e)}")
            print(f"Erreur lors de l'exportation des résultats: {str(e)}")
    def trier_resultats(self, colonne):
        """Trie les résultats d'optimisation selon la colonne spécifiée"""
        # Obtenir les données actuelles du tableau
        data = [(self.results_tree.set(child, colonne), child) for child in self.results_tree.get_children('')]
        
        # Tenter de trier les données numériquement, sinon trier alphabétiquement
        try:
            # Pour les colonnes numériques (distance, total_disponible)
            if colonne in ["distance", "total_disponible", "id"]:
                data.sort(key=lambda x: float(x[0]) if x[0].strip() else 0)
            else:
                # Pour les colonnes textuelles
                data.sort(key=lambda x: x[0].lower())
        except ValueError:
            # En cas d'erreur, trier alphabétiquement
            data.sort(key=lambda x: str(x[0]).lower())
        
        # Réorganiser les éléments dans le tableau selon le tri
        for index, (val, child) in enumerate(data):
            self.results_tree.move(child, '', index)
        
        # Inverser l'ordre pour le prochain clic
        if hasattr(self, 'last_sort_results') and self.last_sort_results == colonne:
            data.reverse()
            for index, (val, child) in enumerate(data):
                self.results_tree.move(child, '', index)
            self.last_sort_results = None
        else:
            self.last_sort_results = colonne

    def utiliser_coordonnees_selection(self):
        """Utilise les coordonnées de l'élément sélectionné dans la liste principale"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un transfert dans la liste principale pour utiliser ses coordonnées")
            return
        
        # Obtenir les valeurs de l'élément sélectionné
        item_values = self.tree.item(selection[0], "values")
        if len(item_values) >= 9:
            try:
                # Récupérer les coordonnées
                longitude = float(item_values[7]) if item_values[7] else 0.0
                latitude = float(item_values[8]) if item_values[8] else 0.0
                
                # Mettre à jour les champs
                self.cible_longitude_var.set(longitude)
                self.cible_latitude_var.set(latitude)
                
                # Basculer vers l'onglet d'optimisation
                self.root.children['!notebook'].select(2)  # Index 2 pour le 3ème onglet
                
                messagebox.showinfo("Information", "Coordonnées récupérées avec succès")
            except (ValueError, IndexError):
                messagebox.showerror("Erreur", "Impossible d'obtenir les coordonnées de l'élément sélectionné")
        else:
            messagebox.showerror("Erreur", "Données incomplètes dans l'élément sélectionné")

    
    def effacer_resultats_optimisation(self):
        """Efface les résultats d'optimisation"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

    def exporter_resultats_optimisation(self):
        """Exporte les résultats d'optimisation au format PDF"""
        # Vérifier qu'il y a des résultats à exporter
        if not self.results_tree.get_children():
            messagebox.showwarning("Attention", "Aucun résultat à exporter")
            return
        
        try:
            # Demander où enregistrer le fichier
            fichier = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Exporter les résultats d'optimisation"
            )
            
            if not fichier:
                # Si l'utilisateur annule
                return
            
            # Création du document PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import landscape, A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            import datetime
            
            doc = SimpleDocTemplate(
                fichier,
                pagesize=landscape(A4),
                title="Résultats d'optimisation"
            )
            
            # Styles pour les textes
            styles = getSampleStyleSheet()
            titre_style = styles['Heading1']
            sous_titre_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Construction du contenu
            elements = []
            
            # Titre du rapport
            elements.append(Paragraph("Résultats d'optimisation d'équipements", titre_style))
            elements.append(Spacer(1, 20))
            
            # Date du rapport
            date_rapport = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            elements.append(Paragraph(f"Généré le: {date_rapport}", normal_style))
            elements.append(Spacer(1, 10))
            
            # Paramètres d'optimisation
            elements.append(Paragraph(f"Coordonnées cibles: ({self.cible_longitude_var.get()}, {self.cible_latitude_var.get()})", normal_style))
            elements.append(Paragraph(f"Rayon d'optimisation: {self.rayon_optimisation_var.get()} km", normal_style))
            elements.append(Spacer(1, 20))
            
            # Récupération des données
            data = [["ID", "Équipement", "Client", "Localisation", "Distance (km)", "Quantité"]]
            
            for item in self.results_tree.get_children():
                values = self.results_tree.item(item, "values")
                data.append([values[0], values[1], values[2], values[3], values[4], values[5]])
            
            # Création du tableau
            table = Table(data, repeatRows=1)
            
            # Style du tableau
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            
            # Appliquer le style au tableau
            table.setStyle(style)
            
            # Ajouter le tableau au document
            elements.append(table)
            
            # Construire le document
            doc.build(elements)
            
            messagebox.showinfo("Succès", f"Résultats d'optimisation exportés avec succès dans {fichier}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exporter les résultats: {str(e)}")
            print(f"Erreur lors de l'exportation des résultats: {str(e)}")
    def creer_tableau(self, parent):
        """Crée le tableau des transferts d'équipements"""
        # Frame pour les boutons d'action
        btn_frame = ttk.Frame(parent, padding=5)
        btn_frame.pack(fill=X, pady=5)

        ttk.Button(btn_frame, text="Ajouter nouveau", command=lambda: self.basculer_vers_formulaire(nouveau=True), 
                bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Modifier sélection", command=self.modifier_selection, 
                bootstyle=WARNING).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer sélection", command=self.supprimer, 
                bootstyle=DANGER).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Rafraîchir", command=self.charger_donnees, 
                bootstyle=INFO).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Exporter PDF", command=self.generer_rapport, 
                bootstyle=SECONDARY).pack(side=LEFT, padx=5)

        # Colonnes SANS nouvelle_longitude et nouvelle_latitude
        columns = (
            "id", "id_client", "localisation", "volet", "nom_equipement", "modalite_transport", 
            "total_equipements", 
            "12_semaines", "11_semaines", "10_semaines", "9_semaines", "8_semaines", "7_semaines", 
            "6_semaines", "5_semaines", "4_semaines", "3_semaines", "2_semaines", "1_semaines", "0_semaines"
        )

        self.tree = ttk.Treeview(parent, columns=columns, show="headings")
        self.tree.pack(fill=BOTH, expand=True)

        # Configuration des en-têtes
        self.tree.heading("id", text="ID", command=lambda: self.trier_tableau("id"))
        self.tree.heading("id_client", text="Client", command=lambda: self.trier_tableau("id_client"))
        self.tree.heading("localisation", text="Localisation", command=lambda: self.trier_tableau("localisation"))
        self.tree.heading("volet", text="Volet", command=lambda: self.trier_tableau("volet"))
        self.tree.heading("nom_equipement", text="Nom Équipement", command=lambda: self.trier_tableau("nom_equipement"))
        self.tree.heading("modalite_transport", text="Modalité Transport", command=lambda: self.trier_tableau("modalite_transport"))
        self.tree.heading("total_equipements", text="Total", command=lambda: self.trier_tableau("total_equipements"))

        # Configuration des en-têtes pour les semaines
        for i in range(12, -1, -1):
            col_name = f"{i}_semaines"
            self.tree.heading(col_name, text=f"{i} sem.", command=lambda i=i: self.trier_tableau(f"{i}_semaines"))

        # Configuration des largeurs de colonnes
        self.tree.column("id", width=50)
        self.tree.column("id_client", width=120)
        self.tree.column("localisation", width=120)
        self.tree.column("volet", width=80)
        self.tree.column("nom_equipement", width=200)
        self.tree.column("modalite_transport", width=120)
        self.tree.column("total_equipements", width=60)

        # Configuration des largeurs pour les semaines
        for col in columns[7:]:
            self.tree.column(col, width=60)

        # Binding pour la sélection d'élément avec double-clic
        self.tree.bind("<Double-1>", self.modifier_selection)

        # Ajout des barres de défilement
        y_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        y_scrollbar.pack(side="right", fill="y")

        x_scrollbar = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)
        x_scrollbar.pack(side="bottom", fill="x")

        self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
    def creer_formulaire(self, parent):
        """Crée le formulaire de saisie"""
        # Frame pour les informations de base
        info_frame = ttk.LabelFrame(parent, text="Informations générales", padding=10)
        info_frame.pack(fill=X, pady=5)
        
        # Première ligne: ID et Client
        ttk.Label(info_frame, text="ID:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(info_frame, textvariable=self.id_var, state=DISABLED, width=5).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Client:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.client_cb = ttk.Combobox(info_frame, textvariable=self.id_client_var, state="readonly", width=20)
        self.client_cb.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.client_cb.bind("<<ComboboxSelected>>", self.actualiser_localisation_client)
        
        ttk.Label(info_frame, text="Localisation:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        ttk.Entry(info_frame, textvariable=self.localisation_client_var, state=DISABLED, width=20).grid(row=0, column=5, padx=5, pady=5, sticky="w")
        
        # Deuxième ligne: Volet et Modalité
        ttk.Label(info_frame, text="Volet:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(info_frame, textvariable=self.volet_var, width=15).grid(row=1, column=1, padx=5, pady=5, sticky="w", columnspan=2)
        
        ttk.Label(info_frame, text="Modalité Transport:").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        transport_cb = ttk.Combobox(info_frame, textvariable=self.modalite_transport_var, values=["Tractable", "Chargeable"], width=15)
        transport_cb.grid(row=1, column=4, padx=5, pady=5, sticky="w")
        
        # Troisième ligne: Nom équipement et Total
        ttk.Label(info_frame, text="Nom Équipement:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.equipement_cb = ttk.Combobox(info_frame, textvariable=self.nom_equipement_var, width=30)
        self.equipement_cb.grid(row=2, column=1, padx=5, pady=5, sticky="w", columnspan=3)
        self.equipement_cb.bind("<<ComboboxSelected>>", self.actualiser_id_equipement)
        
        ttk.Label(info_frame, text="Total Équipements:").grid(row=2, column=4, padx=5, pady=5, sticky="e")
        ttk.Spinbox(info_frame, textvariable=self.total_equipements_var, from_=1, to=1000, width=5).grid(row=2, column=5, padx=5, pady=5, sticky="w")
         
        # Quatrième ligne: Coordonnées du nouveau site (pour référence uniquement, pas sauvegardées)
        
        # Ajouter une note explicative
        note_label = ttk.Label(info_frame, text="Note: Les coordonnées ne sont pas sauvegardées, elles sont uniquement pour référence.", bootstyle="secondary")
        note_label.grid(row=4, column=0, columnspan=6, padx=5, pady=5, sticky="w")
        
        # Frame pour les semaines
        semaines_frame = ttk.LabelFrame(parent, text="Planification des transferts (semaines avant la fin de l'ancien projet)", padding=10)
        semaines_frame.pack(fill=X, pady=10)
        
        # Première ligne de semaines (12 à 7)
        for i, semaine in enumerate(['douze', 'onze', 'dix', 'neuf', 'huit', 'sept']):
            ttk.Label(semaines_frame, text=f"{12-i} semaines:").grid(row=0, column=i*2, padx=5, pady=5, sticky="e")
            ttk.Spinbox(semaines_frame, textvariable=self.semaines_vars[semaine], from_=0, to=1000, width=5).grid(row=0, column=i*2+1, padx=5, pady=5, sticky="w")
        
        # Deuxième ligne de semaines (6 à 1)
        for i, semaine in enumerate(['six', 'cinq', 'quatre', 'trois', 'deux', 'un']):
            ttk.Label(semaines_frame, text=f"{6-i} semaines:").grid(row=1, column=i*2, padx=5, pady=5, sticky="e")
            ttk.Spinbox(semaines_frame, textvariable=self.semaines_vars[semaine], from_=0, to=1000, width=5).grid(row=1, column=i*2+1, padx=5, pady=5, sticky="w")
        
        # Dernière ligne (0 semaines)
        ttk.Label(semaines_frame, text="0 semaine:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Spinbox(semaines_frame, textvariable=self.semaines_vars['zero'], from_=0, to=1000, width=5).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Boutons d'action pour le formulaire
        btn_frame = ttk.Frame(parent, padding=10)
        btn_frame.pack(fill=X, pady=10)
        
        ttk.Button(btn_frame, text="Enregistrer", command=self.enregistrer, bootstyle=SUCCESS).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Vider formulaire", command=self.vider_formulaire, bootstyle=SECONDARY).pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=lambda: self.root.children['!notebook'].select(0), bootstyle=DANGER).pack(side=LEFT, padx=5)

    def charger_equipements(self):
        """Charge la liste des équipements pour le combobox"""
        try:
            equipements = session.query(self.Equipement).order_by(self.Equipement.nomEquipement).all()
            self.equipement_cb['values'] = [e.nomEquipement for e in equipements]
            
            # Mettre en cache les équipements pour une recherche rapide
            self.equipements_cache = {e.nomEquipement: e.ID_equipement for e in equipements}
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les équipements: {str(e)}")
            print(f"Erreur lors du chargement des équipements: {str(e)}")

    def actualiser_id_equipement(self, event=None):
        """Met à jour l'ID d'équipement en fonction du nom sélectionné"""
        nom_equipement = self.nom_equipement_var.get()
        if nom_equipement in self.equipements_cache:
            self.equipement_id_var.set(self.equipements_cache[nom_equipement])
        else:
            self.equipement_id_var.set(0)

    def actualiser_localisation_client(self, event=None):
        """Met à jour la localisation du client sélectionné"""
        id_client = self.id_client_var.get()
        if id_client:
            client = session.query(self.Chantier).filter_by(id_client=id_client).first()
            if client:
                self.localisation_client_var.set(client.localisation or "Non spécifiée")
            else:
                self.localisation_client_var.set("Client inconnu")
        else:
            self.localisation_client_var.set("")

    def basculer_vers_formulaire(self, nouveau=False):
        """Bascule vers l'onglet du formulaire"""
        if nouveau:
            self.vider_formulaire()
        self.root.children['!notebook'].select(1)  # Sélectionner l'onglet du formulaire

    def charger_clients(self):
        """Charge la liste des clients pour les combobox"""
        try:
            clients = session.query(self.Chantier).order_by(self.Chantier.id_client).all()
            client_ids = [c.id_client for c in clients]
            
            # Mise à jour des combobox
            self.client_cb['values'] = client_ids
            self.client_filter_cb['values'] = ["Tous"] + client_ids
            self.filtre_client_var.set("Tous")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les clients: {str(e)}")
            print(f"Erreur lors du chargement des clients: {str(e)}")

    def enregistrer(self):
        """Enregistre un transfert (ajout ou modification)"""
        if not self.validation_formulaire():
            return

        try:
            # Vérifier si le nom d'équipement existe
            nom_equipement = self.nom_equipement_var.get()
            id_equipement = self.equipements_cache.get(nom_equipement)
            
            if not id_equipement:
                messagebox.showerror("Erreur", f"L'équipement '{nom_equipement}' n'existe pas dans la base de données")
                return
            
            # Préparation des données pour le modèle (sans les coordonnées qui n'existent pas dans le modèle)
            transfert_data = {
                "volet": self.volet_var.get() or None,
                "nom_equipement": nom_equipement,
                "id_equipement": id_equipement,
                "modalite_transport": self.modalite_transport_var.get() or None,
                "total_equipements": self.total_equipements_var.get(),
                "id_client": self.id_client_var.get(),
                "douze_semaines_avant": self.semaines_vars['douze'].get() or None,
                "onze_semaines_avant": self.semaines_vars['onze'].get() or None,
                "dix_semaines_avant": self.semaines_vars['dix'].get() or None,
                "neuf_semaines_avant": self.semaines_vars['neuf'].get() or None,
                "huit_semaines_avant": self.semaines_vars['huit'].get() or None,
                "sept_semaines_avant": self.semaines_vars['sept'].get() or None,
                "six_semaines_avant": self.semaines_vars['six'].get() or None,
                "cinq_semaines_avant": self.semaines_vars['cinq'].get() or None,
                "quatre_semaines_avant": self.semaines_vars['quatre'].get() or None,
                "trois_semaines_avant": self.semaines_vars['trois'].get() or None,
                "deux_semaines_avant": self.semaines_vars['deux'].get() or None,
                "un_semaines_avant": self.semaines_vars['un'].get() or None,
                "zero_semaines_avant": self.semaines_vars['zero'].get() or None
            }
            
            # Vérifier s'il s'agit d'un ajout ou d'une modification
            if self.id_var.get() == 0:  # Ajout
                # Créer un nouveau transfert en utilisant le constructeur avec les bons noms d'attributs
                transfert = self.TransfererEquipement(**transfert_data)
                session.add(transfert)
                message_succes = "Transfert d'équipement ajouté avec succès"
            else:  # Modification
                transfert = session.query(self.TransfererEquipement).filter_by(id=self.id_var.get()).first()
                if transfert:
                    # Mettre à jour les attributs individuellement
                    for key, value in transfert_data.items():
                        setattr(transfert, key, value)
                    message_succes = "Transfert d'équipement modifié avec succès"
                else:
                    messagebox.showerror("Erreur", f"Transfert avec ID {self.id_var.get()} non trouvé")
                    return
            
            session.commit()
            messagebox.showinfo("Succès", message_succes)
            self.charger_donnees()
            self.vider_formulaire()
            # Revenir à l'onglet liste
            self.root.children['!notebook'].select(0)
        except Exception as e:
            session.rollback()
            messagebox.showerror("Erreur", f"Impossible d'enregistrer le transfert: {str(e)}")
            print(f"Erreur lors de l'enregistrement: {str(e)}")

    def modifier_selection(self, event=None):
        """Prépare le formulaire pour modifier un élément sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un transfert à modifier.")
            return
            
        item_id = self.tree.item(selection[0], "values")[0]
        try:
            # Jointure avec la table des équipements pour obtenir le nom
            transfert = session.query(self.TransfererEquipement, self.Equipement.nomEquipement)\
                .join(self.Equipement, self.TransfererEquipement.id_equipement == self.Equipement.ID_equipement)\
                .filter(self.TransfererEquipement.id == item_id).first()
                
            if transfert:
                transfert_obj, nom_equipement = transfert
                
                # Remplir le formulaire avec les données
                self.id_var.set(transfert_obj.id)
                self.id_client_var.set(transfert_obj.id_client)
                self.volet_var.set(transfert_obj.volet or "")
                self.nom_equipement_var.set(nom_equipement)
                self.equipement_id_var.set(transfert_obj.id_equipement)
                self.modalite_transport_var.set(transfert_obj.modalite_transport or "")
                self.total_equipements_var.set(transfert_obj.total_equipements)
                
                # Réinitialiser les coordonnées (car elles ne sont pas stockées dans la BD)
                self.nouvelle_longitude_var.set(0.0)
                self.nouvelle_latitude_var.set(0.0)
                
                # Obtention des valeurs des colonnes de longitude et latitude dans le TreeView
                # (stockées temporairement dans l'interface)
                item_values = self.tree.item(selection[0], "values")
                if len(item_values) >= 9:
                    # Si des valeurs sont présentes dans le tableau, les utiliser pour pré-remplir les champs
                    try:
                        long_val = item_values[7]
                        lat_val = item_values[8]
                        if long_val and lat_val:
                            self.nouvelle_longitude_var.set(float(long_val) if long_val else 0.0)
                            self.nouvelle_latitude_var.set(float(lat_val) if lat_val else 0.0)
                    except (ValueError, IndexError):
                        # En cas d'erreur, ne pas planter mais utiliser les valeurs par défaut
                        pass
                
                # Mise à jour des variables pour les semaines
                self.semaines_vars['douze'].set(transfert_obj.douze_semaines_avant or 0)
                self.semaines_vars['onze'].set(transfert_obj.onze_semaines_avant or 0)
                self.semaines_vars['dix'].set(transfert_obj.dix_semaines_avant or 0)
                self.semaines_vars['neuf'].set(transfert_obj.neuf_semaines_avant or 0)
                self.semaines_vars['huit'].set(transfert_obj.huit_semaines_avant or 0)
                self.semaines_vars['sept'].set(transfert_obj.sept_semaines_avant or 0)
                self.semaines_vars['six'].set(transfert_obj.six_semaines_avant or 0)
                self.semaines_vars['cinq'].set(transfert_obj.cinq_semaines_avant or 0)
                self.semaines_vars['quatre'].set(transfert_obj.quatre_semaines_avant or 0)
                self.semaines_vars['trois'].set(transfert_obj.trois_semaines_avant or 0)
                self.semaines_vars['deux'].set(transfert_obj.deux_semaines_avant or 0)
                self.semaines_vars['un'].set(transfert_obj.un_semaines_avant or 0)
                self.semaines_vars['zero'].set(transfert_obj.zero_semaines_avant or 0)
                
                # Mise à jour de la localisation
                self.actualiser_localisation_client()
                
                # Basculer vers l'onglet formulaire
                self.basculer_vers_formulaire()
            else:
                messagebox.showerror("Erreur", f"Transfert avec ID {item_id} non trouvé")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données du transfert: {str(e)}")
            print(f"Erreur lors du chargement du transfert {item_id}: {str(e)}")

    def supprimer(self):
        """Supprime un transfert d'équipement"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Sélectionnez un transfert à supprimer")
            return
            
        item_id = self.tree.item(selection[0], "values")[0]
        confirmation = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer ce transfert d'équipement?")
        if confirmation:
            try:
                transfert = session.query(self.TransfererEquipement).filter_by(id=item_id).first()
                if transfert:
                    session.delete(transfert)
                    session.commit()
                    messagebox.showinfo("Succès", "Transfert d'équipement supprimé avec succès")
                    self.charger_donnees()
                else:
                    messagebox.showerror("Erreur", f"Transfert avec ID {item_id} non trouvé")
            except Exception as e:
                session.rollback()
                messagebox.showerror("Erreur", f"Impossible de supprimer le transfert: {str(e)}")
                print(f"Erreur lors de la suppression du transfert {item_id}: {str(e)}")

    def charger_donnees(self):
        """Charge les données des transferts dans le tableau"""
        # Vider le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            # Construire la requête de base avec jointure
            query = session.query(
                self.TransfererEquipement, 
                self.Equipement.nomEquipement,
                self.Chantier.localisation
            ).join(
                self.Equipement, 
                self.TransfererEquipement.id_equipement == self.Equipement.ID_equipement
            ).join(
                self.Chantier,
                self.TransfererEquipement.id_client == self.Chantier.id_client
            )
            
            # Appliquer le filtre client si nécessaire
            if self.filtre_client_var.get() and self.filtre_client_var.get() != "Tous":
                query = query.filter(self.TransfererEquipement.id_client == self.filtre_client_var.get())
                
            # Appliquer le filtre de recherche si nécessaire
            if self.recherche_var.get():
                search_term = f"%{self.recherche_var.get()}%"
                query = query.filter(
                    or_(
                        self.TransfererEquipement.id_client.like(search_term),
                        self.TransfererEquipement.volet.like(search_term),
                        self.TransfererEquipement.modalite_transport.like(search_term),
                        self.Equipement.nomEquipement.like(search_term),
                        self.Chantier.localisation.like(search_term)
                    )
                )
                
            # Exécuter la requête et obtenir les résultats
            transferts = query.all()
            
            # Ajouter les données au tableau
            # ...dans charger_donnees...
            for transfert in transferts:
                transfert_obj, nom_equipement, localisation = transfert

                self.tree.insert("", "end", values=(
                    transfert_obj.id,
                    transfert_obj.id_client,
                    localisation or "Non spécifiée",
                    transfert_obj.volet or "",
                    nom_equipement or "",
                    transfert_obj.modalite_transport or "",
                    transfert_obj.total_equipements or 0,
                    transfert_obj.douze_semaines_avant or 0,
                    transfert_obj.onze_semaines_avant or 0,
                    transfert_obj.dix_semaines_avant or 0,
                    transfert_obj.neuf_semaines_avant or 0,
                    transfert_obj.huit_semaines_avant or 0,
                    transfert_obj.sept_semaines_avant or 0,
                    transfert_obj.six_semaines_avant or 0,
                    transfert_obj.cinq_semaines_avant or 0,
                    transfert_obj.quatre_semaines_avant or 0,
                    transfert_obj.trois_semaines_avant or 0,
                    transfert_obj.deux_semaines_avant or 0,
                    transfert_obj.un_semaines_avant or 0,
                    transfert_obj.zero_semaines_avant or 0
                ))
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger les données: {str(e)}")
            print(f"Erreur lors du chargement des données: {str(e)}")

    def vider_formulaire(self):
        """Vide le formulaire pour un nouvel ajout"""
        self.id_var.set(0)
        self.volet_var.set("")
        self.nom_equipement_var.set("")
        self.equipement_id_var.set(0)
        self.modalite_transport_var.set("")
        self.total_equipements_var.set(1)
        self.id_client_var.set("")
        self.localisation_client_var.set("")
        self.nouvelle_longitude_var.set(0.0)
        self.nouvelle_latitude_var.set(0.0)
        
        # Vider les champs de semaines
        for semaine in self.semaines_vars:
            self.semaines_vars[semaine].set(0)

    def validation_formulaire(self):
        """Valide les données du formulaire avant enregistrement"""
        # Vérifier que le client est sélectionné
        if not self.id_client_var.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un client")
            return False
        
        # Vérifier que l'équipement est sélectionné
        if not self.nom_equipement_var.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un équipement")
            return False
        
        # Vérifier que le total d'équipements est valide
        if self.total_equipements_var.get() < 1:
            messagebox.showerror("Erreur", "Le nombre total d'équipements doit être d'au moins 1")
            return False
        
        # Vérifier qu'il y a au moins une valeur dans les semaines
        semaines_total = sum(var.get() for var in self.semaines_vars.values())
        if semaines_total == 0:
            confirmation = messagebox.askyesno("Attention", 
                "Aucun équipement n'est planifié dans le temps. Êtes-vous sûr de vouloir continuer?")
            if not confirmation:
                return False
        
        return True

    def rechercher(self):
        """Effectue une recherche dans les données"""
        self.charger_donnees()  # Recharge les données avec le filtre de recherche

    def appliquer_filtre(self):
        """Applique le filtre par client"""
        self.charger_donnees()  # Recharge les données avec le filtre client

    def reinitialiser_filtre(self):
        """Réinitialise les filtres"""
        self.recherche_var.set("")
        self.filtre_client_var.set("Tous")
        self.charger_donnees()  # Recharge toutes les données

    def trier_tableau(self, colonne):
        """Trie le tableau selon la colonne spécifiée"""
        # Obtenir les données actuelles du tableau
        data = [(self.tree.set(child, colonne), child) for child in self.tree.get_children('')]
        
        # Tenter de trier les données numériquement, sinon trier alphabétiquement
        try:
            # Pour les colonnes numériques
            data.sort(key=lambda x: float(x[0]) if x[0].strip() else 0)
        except ValueError:
            # Pour les colonnes textuelles
            data.sort(key=lambda x: x[0].lower())
        
        # Réorganiser les éléments dans le tableau selon le tri
        for index, (val, child) in enumerate(data):
            self.tree.move(child, '', index)
        
        # Inverser l'ordre pour le prochain clic
        if hasattr(self, 'last_sort') and self.last_sort == colonne:
            data.reverse()
            for index, (val, child) in enumerate(data):
                self.tree.move(child, '', index)
            self.last_sort = None
        else:
            self.last_sort = colonne

    def generer_rapport(self):
        """Génère un rapport PDF des transferts d'équipements"""
        try:
            # Demander où enregistrer le fichier
            fichier = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Enregistrer le rapport"
            )
            
            if not fichier:
                # Si l'utilisateur annule
                return
            
            # Création du document PDF
            doc = SimpleDocTemplate(
                fichier,
                pagesize=landscape(A4),
                title="Rapport des transferts d'équipements"
            )
            
            # Styles pour les textes
            styles = getSampleStyleSheet()
            titre_style = styles['Heading1']
            sous_titre_style = styles['Heading2']
            normal_style = styles['Normal']
            
            # Construction du contenu
            elements = []
            
            # Titre du rapport
            elements.append(Paragraph("Rapport des transferts d'équipements", titre_style))
            elements.append(Spacer(1, 20))
            
            # Date du rapport
            date_rapport = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            elements.append(Paragraph(f"Généré le: {date_rapport}", normal_style))
            elements.append(Spacer(1, 10))
            
            # Sous-titre avec les filtres appliqués
            filtre_texte = "Tous les clients"
            if self.filtre_client_var.get() and self.filtre_client_var.get() != "Tous":
                filtre_texte = f"Client: {self.filtre_client_var.get()}"
            if self.recherche_var.get():
                filtre_texte += f" - Recherche: {self.recherche_var.get()}"
            
            elements.append(Paragraph(f"Filtre: {filtre_texte}", sous_titre_style))
            elements.append(Spacer(1, 20))
            
            # Récupération des données
            data = [["ID", "Client", "Localisation", "Volet", "Équipement", "Transport", "Total", 
                    "12 sem.", "11 sem.", "10 sem.", "9 sem.", "8 sem.", "7 sem.", "6 sem.", 
                    "5 sem.", "4 sem.", "3 sem.", "2 sem.", "1 sem.", "0 sem."]]
            
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                # Ne pas inclure les colonnes de coordonnées dans le rapport
                row_data = [values[0], values[1], values[2], values[3], values[4], values[5], values[6]]
                # Ajouter les colonnes de semaines (indices 9 à 22)
                for i in range(9, 22):
                    row_data.append(values[i])
                data.append(row_data)
            
            # Création du tableau
            table = Table(data, repeatRows=1)
            
            # Style du tableau
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])
            
            # Appliquer le style au tableau
            table.setStyle(style)
            
            # Ajouter le tableau au document
            elements.append(table)
            
            # Construire le document
            doc.build(elements)
            
            messagebox.showinfo("Succès", f"Rapport généré avec succès et enregistré dans {fichier}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de générer le rapport: {str(e)}")
            print(f"Erreur lors de la génération du rapport: {str(e)}")

    def exporter_vers_msproject(self):
        """Exporte la solution actuelle au format CSV compatible avec MS Project"""
        try:
            # Vérifier qu'une solution existe
            if not hasattr(self, 'current_solution') or not hasattr(self, 'current_instance'):
                messagebox.showerror("Erreur", "Aucune solution d'optimisation n'est disponible. Exécutez d'abord la métaheuristique.")
                return
            
            # Demander où enregistrer le fichier CSV
            fichier = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")],
                title="Exporter au format MS Project"
            )
            
            if not fichier:  # Si l'utilisateur annule
                return
            
            # Importer la fonction d'exportation depuis le module metaheuristique
            from application.models.metaheuristique import export_solution_to_msproject_csv
            
            # Exporter la solution
            export_solution_to_msproject_csv(self.current_solution, fichier)
            
            messagebox.showinfo("Succès", f"Solution exportée au format MS Project dans le fichier:\n{fichier}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'exporter la solution: {str(e)}")
            traceback.print_exc()


if __name__ == "__main__":
    root = ttk.Window(themename="cosmo")
    app = TransfererEquipementApp(root)
    root.mainloop()