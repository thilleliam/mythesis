import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import tkinter as tk
from datetime import datetime  # Importation correcte une seule fois
import os
import sys

# Assurez-vous que le module parent est dans le chemin d'importation
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importez votre classe NotificationSystem
# Remplacez 'application' par le nom réel de votre package
from application.views.transferer_equipement_view import NotificationSystem
# Si votre NotificationSystem est dans un autre module, ajustez l'importation

class NotificationSystemTester:
    """Classe pour tester le système de notifications"""
    
    def __init__(self):
        # Créer la fenêtre principale
        self.root = ttk.Window(themename="cosmo")
        self.root.title("Test du Système de Notifications")
        self.root.geometry("800x600")
        
        # Variables factices pour simuler l'application principale
        self.TransfererEquipement = None  # Sera remplacé par un Mock
        self.Client = None  # Sera remplacé par un Mock
        
        # Créer un cadre principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Titre
        ttk.Label(
            main_frame, 
            text="Test du Système de Notifications", 
            font=('Helvetica', 16, 'bold')
        ).pack(pady=(0, 20))
        
        # Cadre pour les contrôles de test
        test_frame = ttk.LabelFrame(main_frame, text="Actions de test")
        test_frame.pack(fill=tk.X, pady=10)
        
        # Boutons de test
        ttk.Button(
            test_frame, 
            text="Créer une notification simple", 
            command=self.create_simple_notification,
            bootstyle=PRIMARY,
            width=25
        ).grid(row=0, column=0, padx=10, pady=10)
        
        ttk.Button(
            test_frame, 
            text="Simuler alerte de confirmation", 
            command=self.simulate_weekly_confirmation,
            bootstyle=WARNING,
            width=25
        ).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Button(
            test_frame, 
            text="Simuler des données de transferts", 
            command=self.create_mock_transfers,
            bootstyle=INFO,
            width=25
        ).grid(row=1, column=0, padx=10, pady=10)
        
        ttk.Button(
            test_frame, 
            text="Afficher les notifications", 
            command=self.show_notifications,
            bootstyle=SECONDARY,
            width=25
        ).grid(row=1, column=1, padx=10, pady=10)
        
        # Cadre pour les logs
        log_frame = ttk.LabelFrame(main_frame, text="Journal des actions")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Champ de texte pour les logs
        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ajouter une barre de défilement
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Cadre pour les contrôles de mock
        mock_frame = ttk.LabelFrame(main_frame, text="Configuration des simulations")
        mock_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(mock_frame, text="Date simulée:").grid(row=0, column=0, padx=10, pady=10)
        
        self.mock_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(mock_frame, textvariable=self.mock_date_var, width=15).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(mock_frame, text="Heure simulée:").grid(row=0, column=2, padx=10, pady=10)
        
        self.mock_time_var = tk.StringVar(value=datetime.now().strftime("%H:%M"))
        ttk.Entry(mock_frame, textvariable=self.mock_time_var, width=10).grid(row=0, column=3, padx=10, pady=10)
        
        ttk.Button(
            mock_frame, 
            text="Définir la date/heure", 
            command=self.set_mock_datetime,
            bootstyle=SUCCESS,
            width=20
        ).grid(row=0, column=4, padx=10, pady=10)
        
        # Initialiser le système de notifications avec cette instance comme "application principale"
        self.notification_system = None
        
        # Journal
        self.log("Application de test démarrée")
        self.log("Veuillez initialiser le système de notifications en cliquant sur 'Simuler des données de transferts'")
    
    def log(self, message):
        """Ajoute un message au journal avec l'horodatage"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{current_time}] {message}\n")
        self.log_text.see(tk.END)  # Faire défiler jusqu'à la fin
    
    def create_simple_notification(self):
        """Crée une notification simple pour tester le système"""
        if not self.notification_system:
            self.log("ERREUR: Système de notifications non initialisé!")
            return
        
        self.notification_system.add_notification(
            title="Notification de test",
            message="Ceci est une notification de test créée le " + datetime.now().strftime("%d/%m/%Y à %H:%M:%S"),
            action=None,
            data=None,
            is_weekly_confirmation=False
            # Retirer timestamp si non supporté par add_notification
        )
        
        self.log("Notification simple créée")
    
    def simulate_weekly_confirmation(self):
        """Simule une alerte de confirmation hebdomadaire"""
        if not self.notification_system:
            self.log("ERREUR: Système de notifications non initialisé!")
            return
        
        # Récupérer la date simulée
        mock_date = self.get_mock_datetime()
        
        week_number = mock_date.isocalendar()[1]
        year = mock_date.year
        
        # Ne pas réimporter datetime ici
        
        self.notification_system.add_notification(
            title="Confirmation hebdomadaire requise",
            message=f"Veuillez confirmer les transferts d'équipements réalisés pour la semaine {week_number}.",
            is_weekly_confirmation=True,
            data={'week_number': week_number, 'year': year}
            # Retirer timestamp si non supporté par add_notification
        )
        
        self.log(f"Alerte de confirmation hebdomadaire créée pour la semaine {week_number} de {year}")
    
    def show_notifications(self):
        """Affiche la fenêtre des notifications"""
        if not self.notification_system:
            self.log("ERREUR: Système de notifications non initialisé!")
            return
        
        self.notification_system.show_notifications()
        self.log("Fenêtre des notifications affichée")
    
    def create_mock_transfers(self):
        """Crée des transferts fictifs pour tester le système"""
        # Définir des classes Mock pour simuler les modèles de données
        class MockTransfererEquipement:
            def __init__(self, id, id_client, nom_equipement, zero=0, un=0, deux=0, trois=0):
                self.id = id
                self.id_client = id_client
                self.nom_equipement = nom_equipement
                self.zero = zero
                self.un = un
                self.deux = deux
                self.trois = trois
                self.quantite_reelle = 0
                self.confirme = False
                self.date_confirmation = None
        
        class MockClient:
            def __init__(self, id, nom, latitude, longitude):
                self.id = id
                self.nom = nom
                self.latitude = latitude
                self.longitude = longitude
        
        # Créer un SessionLocal Mock
        class MockSessionLocal:
            def __init__(self):
                self.closed = False
                
                # Données fictives
                self.clients = [
                    MockClient(1, "Client A", 48.856614, 2.3522219),
                    MockClient(2, "Client B", 45.764043, 4.835659),
                    MockClient(3, "Client C", 43.296482, 5.369780)
                ]
                
                self.transfers = [
                    MockTransfererEquipement(1, "Client A", "Équipement X", zero=5),
                    MockTransfererEquipement(2, "Client B", "Équipement Y", zero=8),
                    MockTransfererEquipement(3, "Client C", "Équipement Z", zero=12),
                    MockTransfererEquipement(4, "Client A", "Équipement W", zero=3)
                ]
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.close()
            
            def query(self, model):
                if model == self.app.TransfererEquipement:
                    return MockQueryTransfererEquipement(self)
                elif model == self.app.Client:
                    return MockQueryClient(self)
                return None
            
            def close(self):
                self.closed = True
            
            def commit(self):
                pass
            
            def rollback(self):
                pass
        
        class MockQueryTransfererEquipement:
            def __init__(self, session):
                self.session = session
            
            def all(self):
                return self.session.transfers
            
            def get(self, id):
                for transfer in self.session.transfers:
                    if transfer.id == id:
                        return transfer
                return None
            
            def filter_by(self, **kwargs):
                results = []
                for transfer in self.session.transfers:
                    match = True
                    for key, value in kwargs.items():
                        if getattr(transfer, key, None) != value:
                            match = False
                            break
                    if match:
                        results.append(transfer)
                return MockResult(results)
        
        class MockQueryClient:
            def __init__(self, session):
                self.session = session
            
            def filter_by(self, **kwargs):
                results = []
                for client in self.session.clients:
                    match = True
                    for key, value in kwargs.items():
                        if getattr(client, key, None) != value:
                            match = False
                            break
                    if match:
                        results.append(client)
                return MockResult(results)
        
        class MockResult:
            def __init__(self, results):
                self.results = results
            
            def first(self):
                return self.results[0] if self.results else None
            
            def all(self):
                return self.results
        
        # Assigner les mocks à l'instance de test
        self.TransfererEquipement = MockTransfererEquipement
        self.Client = MockClient
        
        # Remplacer la fonction SessionLocal
        import types
        self.SessionLocal = types.SimpleNamespace()
        self.SessionLocal.__call__ = lambda: MockSessionLocal()
        
        # Nettoyer toute instance précédente du système de notifications
        if self.notification_system:
            self.notification_system.stop()
        
        # Créer une nouvelle instance du système de notifications
        self.notification_system = NotificationSystem(self)
        
        # Remplacer la méthode de vérification pour utiliser notre date simulée
        original_check_weekly = self.notification_system.check_weekly_confirmation
        
        def mock_check_weekly_confirmation(self):
            """Version modifiée qui utilise la date simulée"""
            while not self.should_stop:
                try:
                    # Utiliser la date simulée par le testeur
                    current_date = self.app.get_mock_datetime()
                    
                    is_friday = current_date.weekday() == 4
                    is_end_of_day = 14 <= current_date.hour <= 17
                    
                    if is_friday and is_end_of_day:
                        # Le reste du code est identique à l'original
                        week_number = current_date.isocalendar()[1]
                        year = current_date.year
                        week_key = f"{year}-W{week_number}"
                        
                        notification_exists = any(
                            n.get('is_weekly_confirmation', False) and 
                            n.get('data', {}).get('week_number') == week_number and
                            n.get('data', {}).get('year') == year
                            for n in self.notifications
                        )
                        
                        confirmation_exists = week_key in self.confirmed_transfers
                        
                        if not notification_exists and not confirmation_exists:
                            self.add_notification(
                                title="Confirmation hebdomadaire requise",
                                message=f"Veuillez confirmer les transferts d'équipements réalisés pour la semaine {week_number}.",
                                is_weekly_confirmation=True,
                                data={'week_number': week_number, 'year': year}
                            )
                            
                            self.app.log(f"Notification de confirmation automatique créée pour la semaine {week_number}")
                            
                            break  # Pour les tests, on sort de la boucle après avoir créé la notification
                    
                    break  # Pour les tests, on sort toujours de la boucle
                
                except Exception as e:
                    self.app.log(f"Erreur dans check_weekly_confirmation: {str(e)}")
                    break
        
        # Remplacer la méthode originale par notre version de test
        self.notification_system.check_weekly_confirmation = types.MethodType(mock_check_weekly_confirmation, self.notification_system)
        
        self.log("Système de notifications initialisé avec des données fictives")
        self.log("4 transferts d'équipements ont été créés pour 3 clients différents")
    
    def get_mock_datetime(self):
        """Retourne un objet datetime basé sur les valeurs actuelles des champs date/heure"""
        try:
            date_str = self.mock_date_var.get()
            time_str = self.mock_time_var.get()
            
            datetime_str = f"{date_str} {time_str}"
            return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            self.log("ERREUR: Format de date/heure invalide. Utilisation de la date/heure actuelle.")
            return datetime.now()
    
    def set_mock_datetime(self):
        """Configure la date/heure simulée et vérifie si une notification hebdomadaire doit être créée"""
        mock_date = self.get_mock_datetime()
        
        weekday_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        weekday = weekday_names[mock_date.weekday()]
        
        self.log(f"Date/heure simulée définie: {mock_date.strftime('%d/%m/%Y à %H:%M')} ({weekday})")
        
        if self.notification_system:
            # Vérifier si c'est un vendredi après-midi
            if mock_date.weekday() == 4 and 14 <= mock_date.hour <= 17:
                self.log("C'est vendredi après-midi! Vérification des notifications hebdomadaires...")
                
                # Forcer l'exécution de la vérification hebdomadaire
                check_thread = self.notification_system.check_thread
                if check_thread and check_thread.is_alive():
                    self.notification_system.should_stop = True
                    check_thread.join(timeout=1)
                
                # Créer un nouveau thread
                import threading
                self.notification_system.should_stop = False
                self.notification_system.check_thread = threading.Thread(
                    target=self.notification_system.check_weekly_confirmation, 
                    daemon=True
                )
                self.notification_system.check_thread.start()
            else:
                self.log("Ce n'est pas un vendredi après-midi. Aucune notification hebdomadaire ne sera créée automatiquement.")

if __name__ == "__main__":
    app = NotificationSystemTester()
    app.root.mainloop()