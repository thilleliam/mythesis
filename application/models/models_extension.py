from application.models import TransfererEquipement, Equipement

def get_equipement(self, session):
    """Méthode pour TransfererEquipement"""
    return session.query(Equipement).filter(
        Equipement.nomEquipement == self.designation_equipement
    ).first()

def get_transferts(self, session):
    """Méthode pour Equipement"""
    return session.query(TransfererEquipement).filter(
        TransfererEquipement.designation_equipement == self.nomEquipement
    ).all()

# Ajout des méthodes aux classes
TransfererEquipement.get_equipement = get_equipement
Equipement.get_transferts = get_transferts