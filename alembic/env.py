import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from application.config import Base  # Importez votre Base SQLAlchemy ici
from application.models.vehicule import Vehicule  # Importez vos modèles ici
from application.config import Base
from application.models.chantiers import Chantier
from application.models.equipements import Equipement
from application.models.commande import Commande
from application.models.conducteurs import Conducteur
from application.models.vehicule import Vehicule
from application.models.tournee import Tournee
from application.models.affectation import Affectation
# Charger la configuration Alembic
config = context.config  # <<== Assurez-vous que ceci est avant fileConfig
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Définir les métadonnées de la base de données
target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    print("Context:", context)  # Debugging
    print("Config:", config)  # Debugging

    # Définir l'URL de la base de données
    config.set_main_option('sqlalchemy.url', 'mysql+pymysql://root:thilleli1900@localhost/tms_db')

    # Créer le moteur SQLAlchemy
    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool
    )

    # Configurer le contexte de migration
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            dialect_opts={"paramstyle": "named"},
        )

        # Exécuter les migrations
        with context.begin_transaction():
            context.run_migrations()

# Exécuter les migrations
run_migrations_online()
