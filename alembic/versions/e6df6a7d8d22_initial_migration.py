from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text  # Ajoutez cette ligne

# revision identifiers, used by Alembic.
revision: str = 'e6df6a7d8d22'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def table_exists(table_name: str) -> bool:
    """Vérifie si une table existe déjà dans la base de données."""
    conn = op.get_bind()
    result = conn.execute(text(f"SHOW TABLES LIKE '{table_name}'"))  # Utilisez text() ici
    return bool(result.fetchone())

def upgrade() -> None:
    """Upgrade schema."""
    # Tables indépendantes
    if not table_exists('chantiers'):
        op.create_table(
            'chantiers',
            sa.Column('id_client', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('localisation', sa.String(255)),
            sa.Column('latitude', sa.Float),
            sa.Column('longitude', sa.Float),
            sa.Column('nature_terrain', sa.String(255)),
            sa.Column('distanceAllerGoudron', sa.Float),
            sa.Column('distanceAllerPiste', sa.Float),
        )

    if not table_exists('equipements'):
        op.create_table(
            'equipements',
            sa.Column('ID_equipement', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('quantite', sa.Integer),
            sa.Column('idCommande', sa.String(255)),
            sa.Column('nomEquipement', sa.String(255)),
            sa.Column('typeEquipement', sa.String(255)),
            sa.Column('etat', sa.String(255)),
        )

    # Tables dépendantes
    if not table_exists('commandes'):
        op.create_table(
            'commandes',
            sa.Column('id_commande', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('id_client', sa.Integer, sa.ForeignKey('chantiers.id_client')),
            sa.Column('nature_service', sa.String(255)),
            sa.Column('type_vehicule', sa.String(255)),
            sa.Column('ID_equipement', sa.Integer, sa.ForeignKey('equipements.ID_equipement')),
            sa.Column('quantite_requise', sa.Float),
            sa.Column('lieu_chargement', sa.String(255)),
            sa.Column('date_commande', sa.DateTime),
            sa.Column('date_livraison', sa.DateTime),
        )

    if not table_exists('conducteurs'):
        op.create_table(
            'conducteurs',
            sa.Column('id_conducteur', sa.String(255), primary_key=True),
            sa.Column('nom', sa.String(255)),
            sa.Column('prenom', sa.String(255)),
            sa.Column('numero_telephone', sa.String(255)),
            sa.Column('categorie', sa.String(255)),
        )

    if not table_exists('vehicules'):
        op.create_table(
            'vehicules',
            sa.Column('immatriculation', sa.String(255), primary_key=True),
            sa.Column('numero_chassis', sa.String(255)),
            sa.Column('numero_interne', sa.String(255)),
            sa.Column('marque_modele', sa.String(255)),
            sa.Column('type_vehicule', sa.String(255)),
            sa.Column('capacite_tonne', sa.Float),
            sa.Column('capacite_volume', sa.Float),
        )

    if not table_exists('tournees'):
        op.create_table(
            'tournees',
            sa.Column('id_tournee', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('id_conducteur', sa.String(255), sa.ForeignKey('conducteurs.id_conducteur')),
            sa.Column('immatriculation_vehicule', sa.String(255), sa.ForeignKey('vehicules.immatriculation')),
            sa.Column('id_commande', sa.Integer, sa.ForeignKey('commandes.id_commande')),
            sa.Column('objectif', sa.String(255)),
            sa.Column('lieu_depart', sa.String(255)),
            sa.Column('destination', sa.String(255)),
            sa.Column('itineraire', sa.String(255)),
            sa.Column('km_parcouru', sa.Float),
            sa.Column('date_heure_depart', sa.DateTime),
            sa.Column('date_heure_reception', sa.DateTime),
            sa.Column('date_heure_retour', sa.DateTime),
            sa.Column('date_heure_arrivee', sa.DateTime),
            sa.Column('duree', sa.Float),
        )

    if not table_exists('etape_rotation'):
        op.create_table(
            'etape_rotation',
            sa.Column('ID_Etape', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('ID_Tournee', sa.Integer, sa.ForeignKey('tournees.id_tournee')),
            sa.Column('lieu_chargement', sa.String(255)),
            sa.Column('lieu_dechargement', sa.String(255)),
            sa.Column('date_heure_depart', sa.DateTime),
            sa.Column('date_heure_arrivee', sa.DateTime),
            sa.Column('duree', sa.String(255)),
            sa.Column('type', sa.String(255)),
        )

    if not table_exists('affectations'):
        op.create_table(
            'affectations',
            sa.Column('id_affectation', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('id_conducteur', sa.String(255), sa.ForeignKey('conducteurs.id_conducteur')),
            sa.Column('id_tournee', sa.Integer, sa.ForeignKey('tournees.id_tournee')),
            sa.Column('date_affectation', sa.DateTime),
        )

def downgrade() -> None:
    """Downgrade schema."""
    # Supprimer les tables dans l'ordre inverse
    op.drop_table('affectations')
    op.drop_table('etape_rotation')
    op.drop_table('tournees')
    op.drop_table('vehicules')
    op.drop_table('conducteurs')
    op.drop_table('commandes')
    op.drop_table('equipements')
    op.drop_table('chantiers')