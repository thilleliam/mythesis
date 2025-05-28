import sys
import os
from flask import Flask, request, jsonify
from datetime import datetime

def get_project_root():
    """
    Détermine le chemin racine du projet selon l'environnement
    """
    # 1. Vérifier si on est sur Render (chemin spécifique Render)
    render_path = '/opt/render/project/go/src/github.com/thilleliam/mythesis'
    if os.path.exists(render_path):
        return render_path
    
    # 2. Vérifier si on est dans le répertoire du projet (local)
    current_dir = os.getcwd()
    
    # Chercher le dossier 'application' dans le répertoire courant ou ses parents
    search_dir = current_dir
    for _ in range(5):  # Chercher jusqu'à 5 niveaux au-dessus
        if os.path.exists(os.path.join(search_dir, 'application')):
            return search_dir
        parent = os.path.dirname(search_dir)
        if parent == search_dir:  # On a atteint la racine
            break
        search_dir = parent
    
    # 3. Utiliser le répertoire courant par défaut
    return current_dir

# Configuration dynamique du chemin du projet
project_root = get_project_root()
sys.path.insert(0, project_root)

# Debug - affichage des informations
print("DEBUG - Project root:", project_root)
print("DEBUG - Current working directory:", os.getcwd())
print("DEBUG - Python path:", sys.path[:3])

# Vérification de l'existence des fichiers
application_path = os.path.join(project_root, 'application')
if os.path.exists(application_path):
    print("SUCCESS - Application directory found!")
    print("DEBUG - Application contents:", os.listdir(application_path))
else:
    print("ERROR - Application directory not found")
    print("DEBUG - Looking for 'application' folder in:", project_root)
    print("DEBUG - Available folders:", [d for d in os.listdir(project_root) if os.path.isdir(os.path.join(project_root, d))])

# Tentative d'import de la base de données
engine = None
Session = None

try:
    from application.database import engine
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    print("SUCCESS - Database import successful!")
except ImportError as e:
    print(f"ERROR - Database import failed: {e}")
    print("WARNING - Application will start without database connection")

# Tentative d'import des modèles
Commande = None
Equipement = None

try:
    from application.models.commande import Commande
    from application.models.equipements import Equipement
    print("SUCCESS - Models import successful!")
except ImportError as e:
    print(f"ERROR - Models import failed: {e}")
    print("WARNING - API endpoints will not work without models")

# Création de l'application Flask
app = Flask(__name__)

# HTML du formulaire
HTML_FORM = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TMS - Nouvelle Commande</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: #18bc9c;
            --primary-dark: #16a085;
            --secondary-color: #3498db;
            --success-color: #2ecc71;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --light-color: #ecf0f1;
            --dark-color: #2c3e50;
            --muted-color: #95a5a6;
            --white: #ffffff;
            --border-radius: 6px;
            --box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            --transition: all 0.3s ease;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        .version-banner {
            background: linear-gradient(90deg, #2ecc71, #27ae60);
            color: white;
            padding: 15px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { background: linear-gradient(90deg, #2ecc71, #27ae60); }
            50% { background: linear-gradient(90deg, #27ae60, #2ecc71); }
            100% { background: linear-gradient(90deg, #2ecc71, #27ae60); }
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            color: var(--dark-color);
            line-height: 1.6;
        }

        .navbar {
            background-color: var(--primary-color);
            padding: 1rem 0;
            box-shadow: var(--box-shadow);
            margin-bottom: 2rem;
        }

        .navbar .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .navbar h1 {
            color: var(--white);
            font-size: 1.5rem;
            font-weight: 600;
        }

        .main-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 0 20px;
        }

        .card {
            background-color: var(--white);
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            overflow: hidden;
            margin-bottom: 2rem;
        }

        .card-header {
            background-color: var(--light-color);
            padding: 1.5rem;
            border-bottom: 1px solid #dee2e6;
        }

        .card-header h2 {
            color: var(--dark-color);
            font-size: 1.5rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .card-body {
            padding: 2rem;
        }

        .alert {
            padding: 1rem;
            border-radius: var(--border-radius);
            margin-bottom: 1.5rem;
            border: 1px solid transparent;
            display: none;
        }

        .alert-success {
            background-color: #d1ecf1;
            border-color: #bee5eb;
            color: #0c5460;
        }

        .alert-danger {
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group.full-width {
            grid-column: 1 / -1;
        }

        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: var(--dark-color);
            font-size: 0.9rem;
        }

        .required::after {
            content: " *";
            color: var(--danger-color);
        }

        input, select, textarea {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #dee2e6;
            border-radius: var(--border-radius);
            font-size: 1rem;
            transition: var(--transition);
            background-color: var(--white);
        }

        input:focus, select:focus, textarea:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 0.2rem rgba(24, 188, 156, 0.25);
        }

        textarea {
            min-height: 100px;
            resize: vertical;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: var(--border-radius);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            text-decoration: none;
            min-width: 120px;
        }

        .btn-primary {
            background-color: var(--primary-color);
            color: var(--white);
        }

        .btn-primary:hover {
            background-color: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(24, 188, 156, 0.3);
        }

        .btn-secondary {
            background-color: var(--muted-color);
            color: var(--white);
        }

        .btn-secondary:hover {
            background-color: #7f8c8d;
        }

        .btn-group {
            display: flex;
            gap: 1rem;
            justify-content: flex-end;
            margin-top: 2rem;
            padding-top: 1.5rem;
            border-top: 1px solid #dee2e6;
        }

        .input-group {
            position: relative;
        }

        .input-group .fa {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--muted-color);
            z-index: 2;
        }

        .input-group input,
        .input-group select {
            padding-left: 2.5rem;
        }

        .form-text {
            font-size: 0.875rem;
            color: var(--muted-color);
            margin-top: 0.25rem;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 1rem;
        }

        .spinner {
            border: 2px solid #f3f3f3;
            border-top: 2px solid var(--primary-color);
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 0.5rem;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .progress-bar {
            background-color: #e9ecef;
            border-radius: var(--border-radius);
            overflow: hidden;
            height: 4px;
            margin-bottom: 1.5rem;
        }

        .progress-fill {
            height: 100%;
            background-color: var(--primary-color);
            width: 0%;
            transition: width 0.3s ease;
        }

        @media (max-width: 768px) {
            .form-row {
                grid-template-columns: 1fr;
                gap: 1rem;
            }

            .navbar .container {
                flex-direction: column;
                gap: 1rem;
            }

            .btn-group {
                flex-direction: column;
            }

            .card-body {
                padding: 1.5rem;
            }
        }

        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="version-banner">
        ✨ Version Adaptative - Fonctionne en Local et sur Render
    </div>

    <nav class="navbar">
        <div class="container">
            <h1><i class="fas fa-truck"></i> TMS - Transport Management</h1>
        </div>
    </nav>

    <div class="main-container fade-in">
        <div class="card">
            <div class="card-header">
                <h2><i class="fas fa-plus-circle"></i> Nouvelle Commande de Transport</h2>
            </div>
            <div class="card-body">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>

                <div id="successMessage" class="alert alert-success">
                    <i class="fas fa-check-circle"></i> <span id="successText"></span>
                </div>
                <div id="errorMessage" class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> <span id="errorText"></span>
                </div>

                <div class="loading" id="loadingIndicator">
                    <div class="spinner"></div> Création de la commande en cours...
                </div>

                <form id="commandeForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="id_client" class="required">ID Client</label>
                            <div class="input-group">
                                <i class="fas fa-user"></i>
                                <input type="number" id="id_client" name="id_client" required min="1">
                            </div>
                            <div class="form-text">Identifiant unique du client</div>
                        </div>

                        <div class="form-group">
                            <label for="nature_service" class="required">Nature de Service</label>
                            <div class="input-group">
                                <i class="fas fa-concierge-bell"></i>
                                <select id="nature_service" name="nature_service" required>
                                    <option value="">Sélectionner un service</option>
                                    <option value="Transport marchandises">Transport marchandises</option>
                                    <option value="Livraison express">Livraison express</option>
                                    <option value="Transport passagers">Transport passagers</option>
                                    <option value="Déménagement">Déménagement</option>
                                    <option value="Transport frigorifique">Transport frigorifique</option>
                                    <option value="Transport dangereux">Matières dangereuses</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="id_equipement" class="required">Équipement</label>
                            <div class="input-group">
                                <i class="fas fa-cogs"></i>
                                <select id="id_equipement" name="id_equipement" required>
                                    <option value="">Sélectionner un équipement</option>
                                    <!-- Les options seront chargées dynamiquement -->
                                </select>
                            </div>
                            <div class="form-text">Équipement requis pour le transport</div>
                        </div>

                        <div class="form-group">
                            <label for="quantite_requise">Quantité (tonnes)</label>
                            <div class="input-group">
                                <i class="fas fa-weight-hanging"></i>
                                <input type="number" id="quantite_requise" name="quantite_requise" step="0.1" min="0">
                            </div>
                            <div class="form-text">Poids total à transporter</div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="lieu_chargement" class="required">Lieu de Chargement</label>
                            <div class="input-group">
                                <i class="fas fa-map-marker-alt"></i>
                                <textarea id="lieu_chargement" name="lieu_chargement" required></textarea>
                            </div>
                            <div class="form-text">Adresse précise pour le point de collecte</div>
                        </div>

                        <div class="form-group">
                            <label for="type_vehicule" class="required">Véhicule Requis</label>
                            <div class="input-group">
                                <i class="fas fa-truck"></i>
                                <select id="type_vehicule" name="type_vehicule" required>
                                    <option value="">Sélectionner un véhicule</option>
                                    <option value="Camion léger">Camion léger (< 3.5T)</option>
                                    <option value="Camion">Camion (3.5T - 19T)</option>
                                    <option value="Poids lourd">Poids lourd (> 19T)</option>
                                    <option value="Camionnette">Camionnette</option>
                                    <option value="Remorque">Remorque</option>
                                    <option value="Semi-remorque">Semi-remorque</option>
                                    <option value="Frigorifique">Véhicule frigorifique</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="date_commande">Date de Commande</label>
                            <div class="input-group">
                                <i class="fas fa-calendar-plus"></i>
                                <input type="datetime-local" id="date_commande" name="date_commande">
                            </div>
                            <div class="form-text">Date et heure de création</div>
                        </div>

                        <div class="form-group">
                            <label for="date_livraison">Date de Livraison</label>
                            <div class="input-group">
                                <i class="fas fa-calendar-check"></i>
                                <input type="datetime-local" id="date_livraison" name="date_livraison">
                            </div>
                            <div class="form-text">Date et heure prévues</div>
                        </div>
                    </div>

                    <div class="btn-group">
                        <button type="button" class="btn btn-secondary" onclick="resetForm()">
                            <i class="fas fa-undo"></i> Réinitialiser
                        </button>
                        <button type="submit" class="btn btn-primary" id="submitBtn">
                            <i class="fas fa-save"></i> Créer la Commande
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        // Initialisation
        document.addEventListener('DOMContentLoaded', function() {
            // Définir la date/heure actuelle par défaut
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            document.getElementById('date_commande').value = now.toISOString().slice(0, 16);
            
            // Charger les équipements
            loadEquipements();
            
            // Calculer la barre de progression basée sur les champs remplis
            updateProgress();
            
            // Ajouter des écouteurs d'événements pour la progression
            const formElements = document.querySelectorAll('#commandeForm input, #commandeForm select, #commandeForm textarea');
            formElements.forEach(element => {
                element.addEventListener('input', updateProgress);
                element.addEventListener('change', updateProgress);
            });
        });

        async function loadEquipements() {
            try {
                const response = await fetch('/api/equipements');
                const equipements = await response.json();
                
                const select = document.getElementById('id_equipement');
                select.innerHTML = '<option value="">Sélectionner un équipement</option>';
                
                equipements.forEach(eq => {
                    const option = document.createElement('option');
                    option.value = eq.ID_equipement;
                    option.textContent = eq.nomEquipement;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Erreur lors du chargement des équipements:', error);
                showError('Impossible de charger la liste des équipements');
            }
        }

        function updateProgress() {
            const formElements = document.querySelectorAll('#commandeForm input, #commandeForm select, #commandeForm textarea');
            const totalFields = formElements.length;
            let filledFields = 0;

            formElements.forEach(element => {
                if (element.value.trim() !== '') {
                    filledFields++;
                }
            });

            const progress = (filledFields / totalFields) * 100;
            document.getElementById('progressFill').style.width = progress + '%';
        }

        function resetForm() {
            document.getElementById('commandeForm').reset();
            hideMessages();
            updateProgress();
            
            // Remettre la date actuelle
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
            document.getElementById('date_commande').value = now.toISOString().slice(0, 16);
        }

        function hideMessages() {
            document.getElementById('successMessage').style.display = 'none';
            document.getElementById('errorMessage').style.display = 'none';
        }

        function showSuccess(message) {
            hideMessages();
            document.getElementById('successText').textContent = message;
            document.getElementById('successMessage').style.display = 'block';
            document.getElementById('successMessage').scrollIntoView({ behavior: 'smooth' });
        }

        function showError(message) {
            hideMessages();
            document.getElementById('errorText').textContent = message;
            document.getElementById('errorMessage').style.display = 'block';
            document.getElementById('errorMessage').scrollIntoView({ behavior: 'smooth' });
        }

        function setLoading(loading) {
            const loadingIndicator = document.getElementById('loadingIndicator');
            const submitBtn = document.getElementById('submitBtn');
            
            if (loading) {
                loadingIndicator.style.display = 'block';
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Création...';
            } else {
                loadingIndicator.style.display = 'none';
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-save"></i> Créer la Commande';
            }
        }

        document.getElementById('commandeForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            setLoading(true);
            hideMessages();
            
            const formData = new FormData(this);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                if (value) {
                    if (key === 'date_commande' || key === 'date_livraison') {
                        // Convertir le format datetime-local vers le format attendu par l'API
                        data[key] = new Date(value).toISOString().slice(0, 19).replace('T', ' ');
                    } else if (key === 'quantite_requise' || key === 'id_client' || key === 'id_equipement') {
                        data[key] = parseFloat(value) || parseInt(value);
                    } else {
                        data[key] = value;
                    }
                }
            }

            try {
                const response = await fetch('/api/commandes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok) {
                    showSuccess(`Commande créée avec succès! ID: ${result.id_commande}`);
                    this.reset();
                    updateProgress();
                    
                    // Remettre la date actuelle après reset
                    const now = new Date();
                    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
                    document.getElementById('date_commande').value = now.toISOString().slice(0, 16);
                } else {
                    showError(`Erreur: ${result.error}`);
                }
            } catch (error) {
                showError(`Erreur de connexion: ${error.message}`);
            } finally {
                setLoading(false);
            }
        });

        // Validation en temps réel
        document.getElementById('id_client').addEventListener('input', function(e) {
            const value = parseInt(e.target.value);
            if (value && value < 1) {
                e.target.setCustomValidity('L\\'ID client doit être supérieur à 0');
            } else {
                e.target.setCustomValidity('');
            }
        });

        document.getElementById('quantite_requise').addEventListener('input', function(e) {
            const value = parseFloat(e.target.value);
            if (value && value < 0) {
                e.target.setCustomValidity('La quantité ne peut pas être négative');
            } else {
                e.target.setCustomValidity('');
            }
        });
    </script>
</body>
</html>
"""

# Route d'accueil avec diagnostic amélioré
@app.route('/')
def home():
    # Détection de l'environnement
    is_render = '/opt/render/' in project_root
    is_local = not is_render
    
    status_info = []
    
    # Informations sur l'environnement
    if is_render:
        status_info.append("🚀 Environnement : Render (Production)")
    else:
        status_info.append("💻 Environnement : Local (Développement)")
    
    status_info.append(f"📁 Projet : {project_root}")
    
    # Vérification de la base de données
    if engine is not None:
        status_info.append("✅ Base de données : Connectée")
    else:
        status_info.append("❌ Base de données : Non connectée")
    
    # Vérification des modèles
    if Commande is not None and Equipement is not None:
        status_info.append("✅ Modèles : Importés")
    else:
        status_info.append("❌ Modèles : Non importés")
    
    # Vérification du dossier application
    if os.path.exists(application_path):
        status_info.append("✅ Dossier application : Trouvé")
    else:
        status_info.append("❌ Dossier application : Non trouvé")
    
    status_html = "<br>".join(status_info)
    
    # Liens disponibles
    available_links = []
    available_links.append('<a href="/health">🔍 État détaillé</a>')
    available_links.append('<a href="/api/test">🧪 Test API</a>')
    
    if Session and Commande and Equipement:
        available_links.append('<a href="/commande/form">📝 Formulaire de commande</a>')
        available_links.append('<a href="/api/commandes">📋 API Commandes</a>')
        available_links.append('<a href="/api/equipements">🔧 API Équipements</a>')
    
    links_html = " ".join(available_links)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TMS - Diagnostic</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; max-width: 800px; margin: 0 auto; }}
            h1 {{ color: #18bc9c; text-align: center; }}
            .status {{ background: #e8f4f8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
            .environment {{ background: {'#d4edda' if is_render else '#fff3cd'}; padding: 15px; 
                          border-radius: 5px; margin: 20px 0; text-align: center; font-weight: bold; }}
            nav {{ text-align: center; margin-top: 30px; }}
            nav a {{ display: inline-block; margin: 10px; padding: 10px 20px; 
                     background: #18bc9c; color: white; text-decoration: none; border-radius: 5px; }}
            nav a:hover {{ background: #16a085; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 TMS - Transport Management System</h1>
            
            <div class="environment">
                {'🌐 Application déployée sur Render' if is_render else '💻 Application en développement local'}
            </div>
            
            <div class="status">
                <h3>État du système :</h3>
                {status_html}
            </div>
            
            <nav>
                {links_html}
            </nav>
            
            <div class="footer">
                Version adaptative - Compatible Local & Render<br>
                Dernière mise à jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """

# Route de diagnostic détaillé
@app.route('/health')
def health_check():
    health_data = {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": "render" if '/opt/render/' in project_root else "local",
        "project_root": project_root,
        "cwd": os.getcwd(),
        "database_connected": engine is not None,
        "models_imported": Commande is not None and Equipement is not None,
        "application_dir_exists": os.path.exists(application_path),
        "python_path": sys.path[:5]
    }
    
    # Test de connexion à la base de données
    if Session:
        try:
            session = Session()
            # Test simple de requête
            session.execute("SELECT 1")
            session.close()
            health_data["database_test"] = "OK"
        except Exception as e:
            health_data["database_test"] = f"ERROR: {str(e)}"
    else:
        health_data["database_test"] = "No session available"
    
    # Informations sur les fichiers
    if os.path.exists(application_path):
        health_data["application_contents"] = os.listdir(application_path)
        
        # Vérifier les fichiers critiques
        critical_files = {
            "database.py": os.path.exists(os.path.join(application_path, "database.py")),
            "models/commande.py": os.path.exists(os.path.join(application_path, "models", "commande.py")),
            "models/equipements.py": os.path.exists(os.path.join(application_path, "models", "equipements.py"))
        }
        health_data["critical_files"] = critical_files
    
    return jsonify(health_data)

# Route de test API simple
@app.route('/api/test')
def api_test():
    return jsonify({
        "message": "API is working!",
        "timestamp": datetime.now().isoformat(),
        "environment": "render" if '/opt/render/' in project_root else "local",
        "database_available": Session is not None,
        "models_available": Commande is not None and Equipement is not None,
        "project_root": project_root
    })

# Routes API conditionnelles (seulement si les modèles sont disponibles)
if Session and Commande and Equipement:
    
    @app.route('/api/equipements', methods=['GET'])
    def get_equipements():
        session = Session()
        try:
            equipements = session.query(Equipement).all()
            result = []
            for eq in equipements:
                result.append({
                    'ID_equipement': eq.ID_equipement,
                    'nomEquipement': eq.nomEquipement
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/api/commandes', methods=['POST'])
    def create_commande():
        data = request.json
        session = Session()
        try:
            commande = Commande(
                id_client=data.get('id_client'),
                id_equipement=data.get('id_equipement'),
                nature_service=data.get('nature_service'),
                type_vehicule=data.get('type_vehicule'),
                quantite_requise=data.get('quantite_requise'),
                lieu_chargement=data.get('lieu_chargement'),
                date_commande=datetime.strptime(data.get('date_commande'), '%Y-%m-%d %H:%M:%S') if data.get('date_commande') else None,
                date_livraison=datetime.strptime(data.get('date_livraison'), '%Y-%m-%d %H:%M:%S') if data.get('date_livraison') else None
            )
            session.add(commande)
            session.commit()
            return jsonify({'message': 'Commande créée', 'id_commande': commande.id_commande}), 201
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 400
        finally:
            session.close()

    @app.route('/api/commandes', methods=['GET'])
    def get_commandes():
        session = Session()
        try:
            commandes = session.query(Commande).join(Equipement, Commande.id_equipement == Equipement.ID_equipement).all()
            result = []
            for c in commandes:
                result.append({
                    'id_commande': c.id_commande,
                    'id_client': c.id_client,
                    'id_equipement': c.id_equipement,
                    'nomEquipement': c.equipement.nomEquipement,
                    'nature_service': c.nature_service,
                    'type_vehicule': c.type_vehicule,
                    'quantite_requise': c.quantite_requise,
                    'lieu_chargement': c.lieu_chargement,
                    'date_commande': c.date_commande.strftime('%Y-%m-%d %H:%M:%S') if c.date_commande else None,
                    'date_livraison': c.date_livraison.strftime('%Y-%m-%d %H:%M:%S') if c.date_livraison else None
                })
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @app.route('/commande/form')
    def commande_form():
        return HTML_FORM

else:
    # Routes de remplacement si les modèles ne sont pas disponibles
    @app.route('/api/equipements')
    @app.route('/api/commandes')
    @app.route('/commande/form')
    def unavailable_endpoint():
        return jsonify({
            "error": "Service unavailable",
            "message": "Database or models not properly loaded",
            "suggestion": "Check /health for more details",
            "environment": "render" if '/opt/render/' in project_root else "local"
        }), 503

# Gestionnaire d'erreur 404
@app.errorhandler(404)
def not_found_error(error):
    available_routes = ["/", "/health", "/api/test"]
    if Session and Commande and Equipement:
        available_routes.extend(["/api/commandes", "/api/equipements", "/commande/form"])
    
    return jsonify({
        "error": "Not Found",
        "message": "The requested URL was not found on the server",
        "environment": "render" if '/opt/render/' in project_root else "local",
        "available_routes": available_routes,
        "project_root": project_root
    }), 404

# Gestionnaire d'erreur 500
@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal Server Error",
        "message": "An internal error occurred",
        "suggestion": "Check the application logs for more details",
        "environment": "render" if '/opt/render/' in project_root else "local"
    }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting TMS Application - Version Adaptative")
    print("=" * 60)
    print(f"🌍 Environment: {'Render (Production)' if '/opt/render/' in project_root else 'Local (Development)'}")
    print(f"📁 Project root: {project_root}")
    print(f"📂 Application path: {application_path}")
    print(f"📂 Application exists: {'✅' if os.path.exists(application_path) else '❌'}")
    print(f"🗄️  Database: {'✅ Connected' if engine else '❌ Not connected'}")
    print(f"📊 Models: {'✅ Loaded' if Commande and Equipement else '❌ Not loaded'}")
    print(f"🔧 Session: {'✅ Available' if Session else '❌ Not available'}")
    print("=" * 60)
    
    port = int(os.environ.get('PORT', 5000))
    debug_mode = not ('/opt/render/' in project_root)  # Debug seulement en local
    
    print(f"🚀 Starting server on port {port}")
    print(f"🔧 Debug mode: {'ON' if debug_mode else 'OFF'}")
    print("=" * 60)
    
    app.run(debug=debug_mode, host='0.0.0.0', port=port)