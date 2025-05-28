from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
from application.database import engine
from application.models.commande import Commande
from application.models.equipements import Equipement  # Import du modèle Equipement
from datetime import datetime
import os

app = Flask(__name__)
Session = sessionmaker(bind=engine)

# HTML intégré directement dans le code Python
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

        .navbar .nav-links {
            display: flex;
            gap: 1rem;
        }

        .navbar .nav-link {
            color: var(--white);
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: var(--border-radius);
            transition: var(--transition);
        }

        .navbar .nav-link:hover {
            background-color: var(--primary-dark);
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

    <nav class="navbar">
        <div class="container">
            <h1><i class="fas fa-truck"></i> TMS - Transport Management</h1>
            <div class="nav-links">
                <a href="#" class="nav-link"><i class="fas fa-sign-in-alt"></i> Login</a>
                <a href="/api/commandes" class="nav-link"><i class="fas fa-list"></i> Commandes</a>
            </div>
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

# Routes API
@app.route('/api/equipements', methods=['GET'])
def get_equipements():
    """Endpoint pour récupérer la liste des équipements"""
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
            id_equipement=data.get('id_equipement'),  # Utilisation de id_equipement au lieu de produits
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
        # Jointure avec la table equipements pour récupérer le nom
        commandes = session.query(Commande).join(Equipement, Commande.id_equipement == Equipement.ID_equipement).all()
        result = []
        for c in commandes:
            result.append({
                'id_commande': c.id_commande,
                'id_client': c.id_client,
                'id_equipement': c.id_equipement,
                'nomEquipement': c.equipement.nomEquipement,  # Nom de l'équipement via la relation
                'nature_service': c.nature_service,
                'type_vehicule': c.type_vehicule,
                'quantite_requise': c.quantite_requise,
                'lieu_chargement': c.lieu_chargement,
                'date_commande': c.date_commande.strftime('%Y-%m-%d %H:%M:%S') if c.date_commande else None,
                'date_livraison': c.date_livraison.strftime('%Y-%m-%d %H:%M:%S') if c.date_livraison else None
            })
    except Exception as e:
        # Si la jointure échoue, récupérer les commandes sans les noms d'équipements
        commandes = session.query(Commande).all()
        result = []
        for c in commandes:
            result.append({
                'id_commande': c.id_commande,
                'id_client': c.id_client,
                'id_equipement': c.id_equipement,
                'nomEquipement': None,
                'nature_service': c.nature_service,
                'type_vehicule': c.type_vehicule,
                'quantite_requise': c.quantite_requise,
                'lieu_chargement': c.lieu_chargement,
                'date_commande': c.date_commande.strftime('%Y-%m-%d %H:%M:%S') if c.date_commande else None,
                'date_livraison': c.date_livraison.strftime('%Y-%m-%d %H:%M:%S') if c.date_livraison else None
            })
    finally:
        session.close()
    
    return jsonify(result)

# Route pour le formulaire - HTML intégré
@app.route('/commande/form')
def commande_form():
    return HTML_FORM

# Route d'accueil
@app.route('/')
def home():
    return """
    <h1>🚀 TMS API</h1>
    <p><a href="/commande/form">📝 Nouveau formulaire de commande</a></p>
    <p><a href="/api/commandes">📋 Voir toutes les commandes (JSON)</a></p>
    <p><a href="/api/equipements">🔧 Voir tous les équipements (JSON)</a></p>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)