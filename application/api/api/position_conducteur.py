import sys
import os
from flask import Flask, request, jsonify

# Détection automatique du chemin vers la racine du projet
def get_project_root():
    """Trouve automatiquement la racine du projet"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Remonte dans l'arborescence jusqu'à trouver le dossier 'application'
    while current_dir != os.path.dirname(current_dir):  # Pas encore à la racine du système
        if 'application' in os.listdir(current_dir):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    
    # Si pas trouvé, utiliser le répertoire parent du script actuel
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration dynamique du chemin
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RENDER'):
    # En production (Railway/Render)
    project_root = '/opt/render/project/go/src/github.com/thilleliam/mythesis'
else:
    # En développement local
    project_root = get_project_root()

print(f"DEBUG - Chemin du projet détecté: {project_root}")
print(f"DEBUG - Chemin existe: {os.path.exists(project_root)}")

# Ajouter le chemin au PYTHONPATH
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Vérifier que le dossier application existe
app_path = os.path.join(project_root, 'application')
if os.path.exists(app_path):
    print("DEBUG - Contenu de application/:", os.listdir(app_path))
else:
    print(f"ERROR - Le dossier application n'existe pas dans: {project_root}")
    print(f"DEBUG - Contenu du projet: {os.listdir(project_root) if os.path.exists(project_root) else 'Chemin inexistant'}")

print("DEBUG - PYTHONPATH:", sys.path[:3])

# Import avec gestion d'erreur améliorée
try:
    from application.database import engine
    print("SUCCESS - Import de database réussi!")
except ImportError as e:
    print(f"ERROR - Import failed: {e}")
    print("INFO - Tentative d'import direct...")
    
    # Plan B - import direct avec chemin absolu
    try:
        import importlib.util
        database_path = os.path.join(project_root, "application", "database.py")
        
        if os.path.exists(database_path):
            spec = importlib.util.spec_from_file_location("database", database_path)
            database_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(database_module)
            engine = database_module.engine
            print("SUCCESS - Import direct réussi!")
        else:
            print(f"ERROR - Fichier database.py introuvable: {database_path}")
            raise ImportError("Impossible de charger le module database")
    except Exception as e2:
        print(f"ERROR - Import direct échoué: {e2}")
        raise ImportError(f"Échec complet de l'import: {e} | {e2}")
from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
from application.database import engine
from application.models.conducteurs import Conducteur
from application.models.commande import Commande
from application.models.tournee import Tournee
from datetime import datetime
from functools import wraps
import uuid
import os

# Configuration pour Railway

app = Flask(__name__)
# Port pour Railway
port = int(os.environ.get('PORT', 5000))

Session = sessionmaker(bind=engine)

# Table pour stocker les positions GPS des conducteurs

from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from application.database import Base

class PositionConducteur(Base):
    """Modèle pour stocker les positions GPS des conducteurs"""
    __tablename__ = 'positions_conducteurs'
    
    id = Column(String(255), primary_key=True)
    id_conducteur = Column(String(255), ForeignKey('conducteurs.id_conducteur'))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    vitesse = Column(Float, nullable=True)  # En km/h
    cap = Column(Float, nullable=True)      # Direction en degrés

# Stockage simple des sessions en mémoire (pour la démo)
# En production, utilisez Redis ou une base de données
active_sessions = {}

# Décorateur d'authentification pour les chauffeurs (version simplifiée)
def require_driver_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token manquant'}), 401
        
        try:
            # Retirer "Bearer " du token
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Vérifier si le token existe dans nos sessions actives
            if token not in active_sessions:
                return jsonify({'error': 'Session expirée'}), 401
            
            driver_id = active_sessions[token]['id_conducteur']
            
            # Vérifier que le conducteur existe toujours
            session = Session()
            conducteur = session.query(Conducteur).filter(
                Conducteur.id_conducteur == driver_id
            ).first()
            session.close()
            
            if not conducteur:
                return jsonify({'error': 'Conducteur non trouvé'}), 401
                
            # Ajouter l'ID conducteur à la requête
            request.driver_id = driver_id
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': 'Token invalide'}), 401
    
    return decorated

# =====================================
# ENDPOINTS POUR L'APP CHAUFFEUR
# =====================================

@app.route('/api/chauffeurs/login', methods=['POST'])
def chauffeur_login():
    """Authentification des chauffeurs"""
    data = request.json
    id_conducteur = data.get('id_conducteur')
    
    session = Session()
    try:
        conducteur = session.query(Conducteur).filter(
            Conducteur.id_conducteur == id_conducteur
        ).first()
        
        if not conducteur:
            return jsonify({'error': 'Conducteur non trouvé'}), 404
        
        # Générer un token unique pour cette session
        token = str(uuid.uuid4())
        
        # Stocker la session
        active_sessions[token] = {
            'id_conducteur': conducteur.id_conducteur,
            'nom': conducteur.nom,
            'prenom': conducteur.prenom,
            'login_time': datetime.now()
        }
        
        return jsonify({
            'token': token,
            'conducteur': {
                'id': conducteur.id_conducteur,
                'nom': conducteur.nom,
                'prenom': conducteur.prenom,
                'telephone': conducteur.numero_telephone,
                'disponibilite': conducteur.disponibilite
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/chauffeurs/logout', methods=['POST'])
@require_driver_auth
def chauffeur_logout():
    """Déconnexion du chauffeur"""
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
        
    # Supprimer la session
    if token in active_sessions:
        del active_sessions[token]
    
    return jsonify({'message': 'Déconnexion réussie'})
def update_position():
    """Mise à jour de la position GPS du conducteur"""
    data = request.json
    session = Session()
    
    try:
        # Créer un nouvel enregistrement de position
        position = PositionConducteur(
            id=f"{request.driver_id}_{datetime.now().timestamp()}",
            id_conducteur=request.driver_id,
            latitude=data.get('lat'),
            longitude=data.get('lng'),
            timestamp=datetime.fromisoformat(data.get('timestamp').replace('Z', '+00:00')),
            vitesse=data.get('vitesse'),
            cap=data.get('cap')
        )
        
        session.add(position)
        session.commit()
        
        return jsonify({'message': 'Position mise à jour'}), 200
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/chauffeurs/missions', methods=['GET'])
@require_driver_auth
def get_driver_missions():
    """Récupération des missions/tournées du conducteur"""
    session = Session()
    
    try:
        # Récupérer les tournées du conducteur
        tournees = session.query(Tournee).filter(
            Tournee.id_conducteur == request.driver_id
        ).order_by(Tournee.date_heure_depart.desc()).limit(5).all()
        
        missions = []
        for tournee in tournees:
            # Récupérer la commande associée
            commande = session.query(Commande).filter(
                Commande.id_commande == tournee.id_commande
            ).first()
            
            mission_data = {
                'id_tournee': tournee.id_tournee,
                'id_commande': tournee.id_commande,
                'objectif': tournee.objectif,
                'lieu_depart': tournee.lieu_depart,
                'destination': tournee.destination,
                'itineraire': tournee.itineraire,
                'date_heure_depart': tournee.date_heure_depart.isoformat() if tournee.date_heure_depart else None,
                'km_parcouru': tournee.km_parcouru,
                'statut': getattr(tournee, 'statut', 'planifiee'),  # Supposé que vous avez un champ statut
                'commande': {
                    'nature_service': commande.nature_service if commande else None,
                    'quantite_requise': commande.quantite_requise if commande else None,
                    'lieu_chargement': commande.lieu_chargement if commande else None
                } if commande else None
            }
            missions.append(mission_data)
        
        return jsonify(missions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/chauffeurs/missions/<int:id_tournee>/start', methods=['POST'])
@require_driver_auth
def start_mission(id_tournee):
    """Démarrer une mission"""
    session = Session()
    
    try:
        tournee = session.query(Tournee).filter(
            Tournee.id_tournee == id_tournee,
            Tournee.id_conducteur == request.driver_id
        ).first()
        
        if not tournee:
            return jsonify({'error': 'Mission non trouvée'}), 404
        
        # Mettre à jour le statut (supposé que vous avez ce champ)
        # tournee.statut = 'en_cours'
        # tournee.heure_debut_reel = datetime.now()
        
        session.commit()
        
        return jsonify({'message': 'Mission démarrée', 'id_tournee': id_tournee})
        
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/chauffeurs/status', methods=['PUT'])
@require_driver_auth
def update_driver_status():
    """Mise à jour du statut du conducteur"""
    data = request.json
    session = Session()
    
    try:
        conducteur = session.query(Conducteur).filter(
            Conducteur.id_conducteur == request.driver_id
        ).first()
        
        if not conducteur:
            return jsonify({'error': 'Conducteur non trouvé'}), 404
        
        # Mettre à jour la disponibilité
        new_status = data.get('disponibilite')
        if new_status in ['disponible', 'conge', 'autres']:
            conducteur.disponibilite = new_status
            conducteur.commentaire_disponibilite = data.get('commentaire', '')
            
            session.commit()
            
            return jsonify({
                'message': 'Statut mis à jour',
                'disponibilite': conducteur.disponibilite
            })
        else:
            return jsonify({'error': 'Statut invalide'}), 400
            
    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/chauffeurs/messages/new', methods=['GET'])
@require_driver_auth
def check_new_messages():
    """Vérifier les nouveaux messages pour le conducteur"""
    # Pour la démo, retourner des messages factices
    # En production, vous auriez une table de messages
    messages = []
    
    # Simuler des messages basés sur l'heure
    import random
    if random.random() > 0.8:  # 20% de chance d'avoir un nouveau message
        messages.append({
            'id': f"msg_{datetime.now().timestamp()}",
            'expediteur': 'Dispatcher Central',
            'message': 'Merci de confirmer votre ETA pour la prochaine livraison',
            'timestamp': datetime.now().isoformat(),
            'priorite': 'normale'
        })
    
    return jsonify(messages)

@app.route('/api/chauffeurs/profile', methods=['GET'])
@require_driver_auth
def get_driver_profile():
    """Profil du conducteur"""
    session = Session()
    
    try:
        conducteur = session.query(Conducteur).filter(
            Conducteur.id_conducteur == request.driver_id
        ).first()
        
        if not conducteur:
            return jsonify({'error': 'Conducteur non trouvé'}), 404
        
        # Calculer les statistiques
        total_km = conducteur.total_parcouru()
        
        profile = {
            'id_conducteur': conducteur.id_conducteur,
            'nom_complet': f"{conducteur.prenom} {conducteur.nom}",
            'telephone': conducteur.numero_telephone,
            'categorie': conducteur.categorie,
            'disponibilite': conducteur.disponibilite,
            'commentaire_disponibilite': conducteur.commentaire_disponibilite,
            'statistiques': {
                'total_km_parcouru': total_km,
                'missions_completees': session.query(Tournee).filter(
                    Tournee.id_conducteur == request.driver_id
                ).count()
            }
        }
        
        return jsonify(profile)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

@app.route('/api/chauffeurs/emergency', methods=['POST'])
@require_driver_auth
def emergency_alert():
    """Signal d'urgence du conducteur"""
    data = request.json
    session = Session()
    
    try:
        # Récupérer la dernière position
        last_position = session.query(PositionConducteur).filter(
            PositionConducteur.id_conducteur == request.driver_id
        ).order_by(PositionConducteur.timestamp.desc()).first()
        
        # En production, envoyer des notifications push, emails, SMS
        # Log de l'urgence
        urgence_data = {
            'conducteur_id': request.driver_id,
            'type_urgence': data.get('type', 'generale'),
            'message': data.get('message', ''),
            'position': {
                'lat': last_position.latitude if last_position else None,
                'lng': last_position.longitude if last_position else None
            },
            'timestamp': datetime.now().isoformat()
        }
        
        # Ici vous pourriez enregistrer dans une table d'urgences
        print(f"🚨 URGENCE CONDUCTEUR: {urgence_data}")
        
        return jsonify({
            'message': 'Signal d\'urgence envoyé',
            'numero_urgence': f"URG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()

# =====================================
# ROUTE POUR SERVIR L'APP CHAUFFEUR
# =====================================

@app.route('/chauffeur/app')
def chauffeur_app():
    """Route pour servir l'app chauffeur"""
    # Retourner le HTML complet de l'app chauffeur
    return """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#18bc9c">
    <title>TMS Chauffeur</title>
    <link rel="manifest" href="manifest.json">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding-bottom: 80px;
        }

        .header {
            background: #18bc9c;
            color: white;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .status-card {
            background: white;
            margin: 1rem;
            border-radius: 15px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            text-align: center;
        }

        .status-indicator {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            margin: 0 auto 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
        }

        .status-online { background: #2ecc71; }
        .status-offline { background: #e74c3c; }

        .mission-card {
            background: white;
            margin: 1rem;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }

        .mission-header {
            background: #3498db;
            color: white;
            padding: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .mission-body {
            padding: 1.5rem;
        }

        .mission-detail {
            display: flex;
            align-items: center;
            margin: 0.5rem 0;
            padding: 0.5rem;
            background: #f8f9fa;
            border-radius: 8px;
        }

        .mission-detail i {
            width: 30px;
            color: #666;
        }

        .btn {
            width: 100%;
            padding: 1rem;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            margin: 0.5rem 0;
            transition: all 0.3s ease;
        }

        .btn-primary {
            background: #18bc9c;
            color: white;
        }

        .btn-primary:hover {
            background: #16a085;
            transform: translateY(-2px);
        }

        .btn-success {
            background: #2ecc71;
            color: white;
        }

        .btn-warning {
            background: #f39c12;
            color: white;
        }

        .btn-danger {
            background: #e74c3c;
            color: white;
        }

        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            display: flex;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        }

        .nav-item {
            flex: 1;
            padding: 1rem;
            text-align: center;
            border: none;
            background: none;
            color: #666;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .nav-item.active {
            color: #18bc9c;
            background: #f8f9fa;
        }

        .nav-item i {
            display: block;
            font-size: 20px;
            margin-bottom: 0.25rem;
        }

        .hidden {
            display: none;
        }

        .alert {
            margin: 1rem;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
        }

        .alert-success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }

        .alert-warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }

        .gps-status {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin: 1rem 0;
        }

        .gps-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #2ecc71;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }

        .quick-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1rem;
        }

        .quick-action {
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .quick-action:hover {
            transform: translateY(-2px);
        }

        .quick-action i {
            font-size: 24px;
            color: #18bc9c;
            margin-bottom: 0.5rem;
        }

        .login-form {
            background: white;
            margin: 2rem 1rem;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }

        .form-group {
            margin-bottom: 1rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }

        .form-group input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
        }

        .form-group input:focus {
            outline: none;
            border-color: #18bc9c;
        }

        @media (max-width: 480px) {
            .mission-header {
                flex-direction: column;
                gap: 0.5rem;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1><i class="fas fa-truck"></i> TMS Chauffeur</h1>
        <p id="driverName">Connexion requise</p>
    </div>

    <!-- Formulaire de connexion -->
    <div id="loginSection" class="section">
        <div class="login-form">
            <h2 style="text-align: center; margin-bottom: 1.5rem;">
                <i class="fas fa-sign-in-alt"></i> Connexion Chauffeur
            </h2>
            <form id="loginForm">
                <div class="form-group">
                    <label for="id_conducteur">ID Conducteur</label>
                    <input type="text" id="id_conducteur" name="id_conducteur" placeholder="Votre ID conducteur" required>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-sign-in-alt"></i> Se connecter
                </button>
            </form>
            <div id="loginError" class="alert alert-warning" style="display: none; margin-top: 1rem;">
                <span id="loginErrorText"></span>
            </div>
        </div>
    </div>

    <!-- Section Tableau de bord -->
    <div id="dashboard" class="section hidden">
        <div class="status-card">
            <div class="status-indicator status-online">
                <i class="fas fa-check"></i>
            </div>
            <h3>Statut : En ligne</h3>
            <div class="gps-status">
                <div class="gps-dot"></div>
                <span>GPS Actif - Position mise à jour</span>
            </div>
            <p id="currentLocation"><strong>Dernière position :</strong> En cours...</p>
            <p><strong>Véhicule :</strong> <span id="vehicleInfo">À déterminer</span></p>
        </div>

        <div class="quick-actions">
            <button class="quick-action" onclick="startBreak()">
                <i class="fas fa-coffee"></i>
                <div>Pause</div>
            </button>
            <button class="quick-action" onclick="reportIssue()">
                <i class="fas fa-exclamation-triangle"></i>
                <div>Signaler</div>
            </button>
            <button class="quick-action" onclick="callDispatch()">
                <i class="fas fa-phone"></i>
                <div>Dispatcher</div>
            </button>
            <button class="quick-action" onclick="logout()">
                <i class="fas fa-sign-out-alt"></i>
                <div>Déconnexion</div>
            </button>
        </div>
    </div>

    <!-- Section Missions -->
    <div id="missions" class="section hidden">
        <div id="missionsContainer">
            <!-- Les missions seront chargées ici dynamiquement -->
        </div>
    </div>

    <!-- Section Messages -->
    <div id="messages" class="section hidden">
        <div id="messagesContainer">
            <!-- Les messages seront chargés ici -->
        </div>
    </div>

    <!-- Navigation bottom -->
    <div id="bottomNav" class="bottom-nav" style="display: none;">
        <button class="nav-item active" onclick="showSection('dashboard')">
            <i class="fas fa-tachometer-alt"></i>
            <span>Tableau</span>
        </button>
        <button class="nav-item" onclick="showSection('missions')">
            <i class="fas fa-tasks"></i>
            <span>Missions</span>
        </button>
        <button class="nav-item" onclick="showSection('messages')">
            <i class="fas fa-comments"></i>
            <span>Messages</span>
        </button>
        <button class="nav-item" onclick="logout()">
            <i class="fas fa-sign-out-alt"></i>
            <span>Sortie</span>
        </button>
    </div>

    <script>
        // Variables globales
        let authToken = null;
        let currentDriver = null;
        let watchId = null;
        let isOnline = true;

        // Initialisation de l'app
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 TMS Chauffeur App initialisée');
            
            // Vérifier si déjà connecté
            authToken = localStorage.getItem('driver_token');
            if (authToken) {
                loadDriverProfile();
            }
            
            requestNotificationPermission();
        });

        // Gestion de la connexion
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const idConducteur = document.getElementById('id_conducteur').value;
            
            try {
                const response = await fetch('/api/chauffeurs/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        id_conducteur: idConducteur
                    })
                });

                const result = await response.json();

                if (response.ok) {
                    authToken = result.token;
                    currentDriver = result.conducteur;
                    
                    localStorage.setItem('driver_token', authToken);
                    localStorage.setItem('driver_info', JSON.stringify(currentDriver));
                    
                    showDriverInterface();
                    loadMissions();
                    startGPSTracking();
                } else {
                    showLoginError(result.error || 'Erreur de connexion');
                }
            } catch (error) {
                showLoginError('Impossible de se connecter au serveur');
                console.error('Erreur login:', error);
            }
        });

        function showLoginError(message) {
            document.getElementById('loginErrorText').textContent = message;
            document.getElementById('loginError').style.display = 'block';
        }

        function showDriverInterface() {
            document.getElementById('loginSection').classList.add('hidden');
            document.getElementById('dashboard').classList.remove('hidden');
            document.getElementById('bottomNav').style.display = 'flex';
            
            document.getElementById('driverName').textContent = `${currentDriver.prenom} ${currentDriver.nom}`;
        }

        function logout() {
            if (confirm('Voulez-vous vraiment vous déconnecter ?')) {
                localStorage.removeItem('driver_token');
                localStorage.removeItem('driver_info');
                
                authToken = null;
                currentDriver = null;
                
                document.getElementById('loginSection').classList.remove('hidden');
                document.getElementById('dashboard').classList.add('hidden');
                document.getElementById('missions').classList.add('hidden');
                document.getElementById('messages').classList.add('hidden');
                document.getElementById('bottomNav').style.display = 'none';
                
                document.getElementById('driverName').textContent = 'Connexion requise';
                
                if (watchId) {
                    navigator.geolocation.clearWatch(watchId);
                }
            }
        }

        async function loadDriverProfile() {
            try {
                const response = await fetch('/api/chauffeurs/profile', {
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                });

                if (response.ok) {
                    const profile = await response.json();
                    currentDriver = profile;
                    showDriverInterface();
                    loadMissions();
                    startGPSTracking();
                } else {
                    logout();
                }
            } catch (error) {
                console.error('Erreur chargement profil:', error);
                logout();
            }
        }

        // Gestion des sections
        function showSection(sectionName) {
            document.querySelectorAll('.section').forEach(section => {
                section.classList.add('hidden');
            });
            
            document.getElementById(sectionName).classList.remove('hidden');
            
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.remove('active');
            });
            event.target.closest('.nav-item').classList.add('active');
        }

        // Gestion GPS
        function startGPSTracking() {
            if (navigator.geolocation) {
                watchId = navigator.geolocation.watchPosition(
                    updatePosition,
                    handleLocationError,
                    {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 30000
                    }
                );
                console.log('📍 Suivi GPS démarré');
            } else {
                alert('GPS non supporté par ce navigateur');
            }
        }

        function updatePosition(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            console.log(`📍 Position: ${lat}, ${lng}`);
            
            sendLocationToServer(lat, lng);
            updateLocationDisplay(lat, lng);
        }

        function handleLocationError(error) {
            console.error('Erreur GPS:', error);
            const statusElement = document.querySelector('.gps-status span');
            if (statusElement) {
                statusElement.textContent = 'GPS indisponible';
            }
        }

        // Communication avec le serveur
        async function sendLocationToServer(lat, lng) {
            if (!authToken) return;

            try {
                const response = await fetch('/api/chauffeurs/position', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${authToken}`
                    },
                    body: JSON.stringify({
                        lat: lat,
                        lng: lng,
                        timestamp: new Date().toISOString()
                    })
                });
                
                if (response.ok) {
                    console.log('✅ Position envoyée au serveur');
                }
            } catch (error) {
                console.error('❌ Erreur envoi position:', error);
            }
        }

        async function loadMissions() {
            if (!authToken) return;

            try {
                const response = await fetch('/api/chauffeurs/missions', {
                    headers: {
                        'Authorization': `Bearer ${authToken}`
                    }
                });
                
                if (response.ok) {
                    const missions = await response.json();
                    displayMissions(missions);
                }
            } catch (error) {
                console.error('Erreur chargement missions:', error);
            }
        }

        function displayMissions(missions) {
            const container = document.getElementById('missionsContainer');
            container.innerHTML = '';

            if (missions.length === 0) {
                container.innerHTML = '<div class="alert alert-warning">Aucune mission assignée</div>';
                return;
            }

            missions.forEach(mission => {
                const missionCard = `
                    <div class="mission-card">
                        <div class="mission-header">
                            <h3>Mission #${mission.id_commande}</h3>
                            <span class="badge">${mission.statut || 'Planifiée'}</span>
                        </div>
                        <div class="mission-body">
                            <div class="mission-detail">
                                <i class="fas fa-map-marker-alt"></i>
                                <span><strong>Départ :</strong> ${mission.lieu_depart || 'À définir'}</span>
                            </div>
                            <div class="mission-detail">
                                <i class="fas fa-flag-checkered"></i>
                                <span><strong>Destination :</strong> ${mission.destination || 'À définir'}</span>
                            </div>
                            <div class="mission-detail">
                                <i class="fas fa-clock"></i>
                                <span><strong>Départ prévu :</strong> ${new Date(mission.date_heure_depart).toLocaleString()}</span>
                            </div>
                            <div class="mission-detail">
                                <i class="fas fa-target"></i>
                                <span><strong>Objectif :</strong> ${mission.objectif || 'Transport'}</span>
                            </div>
                            
                            <button class="btn btn-success" onclick="startMission(${mission.id_tournee})">
                                <i class="fas fa-play"></i> Commencer la mission
                            </button>
                        </div>
                    </div>
                `;
                container.innerHTML += missionCard;
            });
        }

        // Gestion des notifications
        function requestNotificationPermission() {
            if ('Notification' in window) {
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        console.log('✅ Notifications autorisées');
                    }
                });
            }
        }

        function showNotification(title, body) {
            if ('Notification' in window && Notification.permission === 'granted') {
                const notification = new Notification(title, {
                    body: body,
                    icon: '/icon-192x192.png'
                });
                
                setTimeout(() => notification.close(), 5000);
            }
        }

        // Actions rapides
        async function startMission(idTournee) {
            if (confirm('Confirmer le début de la mission ?')) {
                try {
                    const response = await fetch(`/api/chauffeurs/missions/${idTournee}/start`, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${authToken}`
                        }
                    });

                    if (response.ok) {
                        showNotification('Mission démarrée', 'Bonne route ! Conduisez prudemment.');
                        loadMissions(); // Recharger les missions
                    }
                } catch (error) {
                    alert('Erreur lors du démarrage de la mission');
                }
            }
        }

        function startBreak() {
            if (confirm('Commencer une pause ?')) {
                showNotification('Pause démarrée', 'Prenez le temps de vous reposer.');
            }
        }

        function reportIssue() {
            const issue = prompt('Quel est le problème ?');
            if (issue) {
                showNotification('Signalement envoyé', 'Le dispatcher a été notifié.');
            }
        }

        function callDispatch() {
            if (confirm('Appeler le dispatcher ?')) {
                window.open('tel:+213555123456');
            }
        }

        function updateLocationDisplay(lat, lng) {
            const locationElement = document.getElementById('currentLocation');
            if (locationElement) {
                locationElement.innerHTML = `<strong>Position actuelle :</strong> ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            }
        }

        // Gestion des événements système
        window.addEventListener('online', () => {
            isOnline = true;
            showNotification('Connexion rétablie', 'Synchronisation en cours...');
        });

        window.addEventListener('offline', () => {
            isOnline = false;
            showNotification('Connexion perdue', 'Mode hors ligne activé');
        });
    </script>
</body>
</html>
    """

# =====================================
# ROUTE D'ACCUEIL MISE À JOUR
# =====================================

@app.route('/')
def home():
    return """
    <h1>🚀 TMS API</h1>
    <p><a href="/commande/form">📝 Nouveau formulaire de commande</a></p>
    <p><a href="/api/commandes">📋 Voir toutes les commandes (JSON)</a></p>
    <p><a href="/api/equipements">🔧 Voir tous les équipements (JSON)</a></p>
    <p><a href="/api/clients">👥 Voir tous les clients (JSON)</a></p>
    <p><a href="/chauffeur/app">📱 App Chauffeur</a></p>
    """

if __name__ == '__main__':
    # Créer les tables si elles n'existent pas
    with app.app_context():
        Base.metadata.create_all(bind=engine)
    
    # Mode production sur Railway
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        app.run(host='0.0.0.0', port=port)
    else:
        print("🚀 Serveur TMS démarré sur http://127.0.0.1:5000")
        print("📝 Formulaire: http://127.0.0.1:5000/commande/form")
        print("📱 App Chauffeur: http://127.0.0.1:5000/chauffeur/app")
        app.run(debug=True)