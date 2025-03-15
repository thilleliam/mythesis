# __init__.py
# Importez d'abord vos modèles
from application.database import Base
from application.models.chantiers import Chantier
from application.models.commandeequipement import CommandeEquipement
from application.models.equipements import Equipement
from application.models.commande import Commande
from application.models.conducteurs import Conducteur
from application.models.vehicule import Vehicule
from application.models.tournee import Tournee
from application.models.etape import EtapeRotation
from application.models.affectation import Affectation

# Configurez les mappeurs après avoir importé tous les modèles
from sqlalchemy.orm import configure_mappers
configure_mappers()