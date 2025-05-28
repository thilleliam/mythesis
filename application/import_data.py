import sys
import os
from application.database import engine
import sqlalchemy as sa

def import_all_data():
    """Import complet avec toutes vos données"""
    
    try:
        print("🚀 Import complet de toutes vos données...")
        
        with engine.connect() as conn:
            
            # D'abord, vérifions la connexion
            print("🔍 Test connexion...")
            result = conn.execute(sa.text("SELECT 1"))
            print("✅ Connexion OK")
            
            # Supprimons les tables existantes s'il y en a
            print("🧹 Nettoyage des tables existantes...")
            conn.execute(sa.text("SET FOREIGN_KEY_CHECKS = 0"))
            
            tables_to_drop = [
                'commandes_equipements', 'etapes_rotation', 'affectations', 
                'tournees', 'commandes', 'transferer_equipement', 
                'equipements', 'vehicules', 'conducteurs', 'chantiers', 'alembic_version'
            ]
            
            for table in tables_to_drop:
                try:
                    conn.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))
                    print(f"🗑️ Table {table} supprimée")
                except:
                    pass
            
            conn.execute(sa.text("SET FOREIGN_KEY_CHECKS = 1"))
            
            # 1. Créer table chantiers
            print("📋 Création table chantiers...")
            conn.execute(sa.text("""
                CREATE TABLE `chantiers` (
                  `id_client` varchar(255) NOT NULL,
                  `localisation` varchar(255) DEFAULT NULL,
                  `latitude` float DEFAULT NULL,
                  `longitude` float DEFAULT NULL,
                  `nature_terrain` varchar(255) DEFAULT NULL,
                  `distanceAllerGoudron` float DEFAULT NULL,
                  `distanceAllerPiste` float DEFAULT NULL,
                  `temps_aller` float DEFAULT NULL,
                  PRIMARY KEY (`id_client`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            
            # 2. Insérer données chantiers
            print("📝 Insertion données chantiers...")
            conn.execute(sa.text("""
                INSERT INTO `chantiers` VALUES 
                ('37', 'Nouveau camp - Zone Sbaa (G: 170 km - P: ...)', 32.5, 3, 'Accès difficile', 232, 80, 0.78),
                ('38', 'Tinirkouk - W. Adrar', 28.9, -1.2, '', 961, 75, 2.59),
                ('39', 'El Oued', 33.35, 6.85, 'Accès facile', 290, 0, 0.725),
                ('40', 'BEZIM DAHRAOUI', 32.85, 5.65, '', 15, 0, 0.0375),
                ('41', 'El Menia', 30.57, 2.88, NULL, 475, 65, 1),
                ('42', 'Hassi El Fehal - El Menia', 30.47, 3.23, NULL, 343, 3, 1),
                ('43', 'HASSI AGRAB', 29.15, -1.45, NULL, 94, 2, 0.5),
                ('EGS 100', 'BIR LAHRACHE (G: 860 Km - P: 04 Km)', 34.2, 2.5, 'Accès difficile', 1155, 7, 2.905),
                ('EGS 120', 'TFT - OHANET', 32.9, 5.7, NULL, 603, 1, 2),
                ('EGS 60', 'Hassi R\\'Mel - Laghouat', 33.1, 3.2, '', 393, 72, 1.1625)
            """))
            
            # 3. Créer table conducteurs
            print("👥 Création table conducteurs...")
            conn.execute(sa.text("""
                CREATE TABLE `conducteurs` (
                  `id_conducteur` varchar(255) NOT NULL,
                  `nom` varchar(255) NOT NULL,
                  `prenom` varchar(255) NOT NULL,
                  `numero_telephone` varchar(255) NOT NULL,
                  `categorie` varchar(255) NOT NULL,
                  `disponibilite` enum('disponible','conge','autres') NOT NULL,
                  `commentaire_disponibilite` varchar(255) DEFAULT NULL,
                  PRIMARY KEY (`id_conducteur`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            
            # 4. Insérer données conducteurs
            print("📝 Insertion données conducteurs...")
            conn.execute(sa.text("""
                INSERT INTO `conducteurs` VALUES 
                ('33345', 'Fechath', 'ameur', '0673454647', 'chauffeur', 'autres', 'maladie'),
                ('COND-4f14efeb', 'qassi', 'thilleli', '0673243441', 'conducteur', 'conge', NULL),
                ('COND001', 'Dupont', 'Qassi', '0123456789', 'A', 'disponible', NULL),
                ('COND002', 'Martin', 'Pierre', '0123456790', 'B', 'disponible', NULL)
            """))
            
            # 5. Créer table equipements
            print("⚙️ Création table equipements...")
            conn.execute(sa.text("""
                CREATE TABLE `equipements` (
                  `ID_equipement` int(11) NOT NULL AUTO_INCREMENT,
                  `quantite` int(11) DEFAULT NULL,
                  `nomEquipement` varchar(255) DEFAULT NULL,
                  `typeEquipement` varchar(255) DEFAULT NULL,
                  `etat` varchar(255) DEFAULT NULL,
                  `poids` float DEFAULT NULL COMMENT 'Poids de l\\'équipement en kilogrammes',
                  `volume` float DEFAULT NULL COMMENT 'Volume de l\\'équipement en mètres cubes',
                  PRIMARY KEY (`ID_equipement`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            
            # 6. Insérer données equipements
            print("📝 Insertion données equipements...")
            conn.execute(sa.text("""
                INSERT INTO `equipements` (`ID_equipement`, `quantite`, `nomEquipement`, `typeEquipement`, `etat`, `poids`, `volume`) VALUES 
                (5, 20, 'climatiseurs', 'hhhhhhhh', 'bon', 2, 3),
                (6, 1, 'Baraque (Unité)', 'Chargeable', 'Neuf', 3000, 15),
                (7, 1, 'Baraque (Unité)', 'Tractable', 'Neuf', 3500, 18),
                (8, 1, 'Conteneur', 'Chargeable', 'Bon état', 2500, 12),
                (20, 1, 'Bentonite', 'Chargeable', 'Neuf', 1200, 6),
                (22, 1, 'Batterie (Unité)', 'Chargeable', 'Neuf', 40, 0.5)
            """))
            
            # 7. Créer table vehicules
            print("🚗 Création table vehicules...")
            conn.execute(sa.text("""
                CREATE TABLE `vehicules` (
                  `immatriculation` varchar(255) NOT NULL,
                  `numero_chassis` varchar(255) DEFAULT NULL,
                  `numero_interne` varchar(255) DEFAULT NULL,
                  `marque_modele` varchar(255) DEFAULT NULL,
                  `type_vehicule` varchar(255) DEFAULT NULL,
                  `capacite_tonne` float DEFAULT NULL,
                  `capacite_volume` float DEFAULT NULL,
                  `etat` enum('Disponible','En panne','En service') DEFAULT NULL,
                  PRIMARY KEY (`immatriculation`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            
            # 8. Insérer quelques vehicules
            print("📝 Insertion données vehicules...")
            conn.execute(sa.text("""
                INSERT INTO `vehicules` VALUES 
                ('2ZK3QXE8', 'TMYJHN8T', 'EYIIIC9B', 'Plateau Mercedes', '6×2', 35, 0, 'Disponible'),
                ('31981-04', 'F9JY7NXRBBT5DBZ1G', 'VEH-5969', 'Porte-engin Volvo FH16', '6*4', 22.9, 0, 'Disponible'),
                ('1WI9OK55', 'T6RTWZF7', 'QFSALXZM', 'Camions Plateaux', '6*6', 12, 0, 'En panne')
            """))
            
            # 9. Créer table commandes
            print("📦 Création table commandes...")
            conn.execute(sa.text("""
                CREATE TABLE `commandes` (
                  `id_commande` int(11) NOT NULL AUTO_INCREMENT,
                  `id_client` varchar(255) DEFAULT NULL,
                  `nature_service` varchar(255) DEFAULT NULL,
                  `type_vehicule` varchar(255) DEFAULT NULL,
                  `quantite_requise` float DEFAULT NULL,
                  `lieu_chargement` varchar(255) DEFAULT NULL,
                  `date_commande` datetime DEFAULT NULL,
                  `date_livraison` datetime DEFAULT NULL,
                  `id_equipement` int(11) DEFAULT NULL,
                  `statut` varchar(255) DEFAULT NULL,
                  PRIMARY KEY (`id_commande`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            
            # 10. Insérer données commandes
            print("📝 Insertion données commandes...")
            conn.execute(sa.text("""
                INSERT INTO `commandes` (`id_commande`, `id_client`, `nature_service`, `type_vehicule`, `quantite_requise`, `lieu_chargement`, `date_commande`, `date_livraison`, `id_equipement`, `statut`) VALUES 
                (2, 'EGS 100', 'hhh', 'Semi-remorque', 33, 'hhhh', '2025-04-15 07:46:00', '2025-04-18 07:45:54', NULL, NULL),
                (5, '40', 'chargement', 'Semi-remorque', 15, 'ain benyan', '2025-04-24 14:47:11', '2025-04-27 14:47:08', NULL, NULL),
                (10, '37', 'Transport marchandises', 'Poids lourd', 30, 'OUERGLA', '2025-05-31 06:49:00', '2025-05-30 06:50:00', 20, NULL)
            """))
            
            # 11. Créer autres tables
            print("📋 Création tables restantes...")
            
            # Table tournees
            conn.execute(sa.text("""
                CREATE TABLE `tournees` (
                  `id_tournee` int(11) NOT NULL AUTO_INCREMENT,
                  `id_conducteur` varchar(255) DEFAULT NULL,
                  `immatriculation_vehicule` varchar(255) DEFAULT NULL,
                  `id_commande` int(11) DEFAULT NULL,
                  `objectif` varchar(255) DEFAULT NULL,
                  `lieu_depart` varchar(255) DEFAULT NULL,
                  `destination` varchar(255) DEFAULT NULL,
                  `itineraire` varchar(255) DEFAULT NULL,
                  `km_parcouru` float DEFAULT NULL,
                  `date_heure_depart` datetime DEFAULT NULL,
                  `date_heure_reception` datetime DEFAULT NULL,
                  `date_heure_retour` datetime DEFAULT NULL,
                  `date_heure_arrivee` datetime DEFAULT NULL,
                  `duree` varchar(255) DEFAULT NULL,
                  PRIMARY KEY (`id_tournee`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            
            # Table affectations
            conn.execute(sa.text("""
                CREATE TABLE `affectations` (
                  `id_affectation` int(11) NOT NULL AUTO_INCREMENT,
                  `id_conducteur` varchar(255) DEFAULT NULL,
                  `immatriculation_vehicule` varchar(255) DEFAULT NULL,
                  `id_tournee` int(11) DEFAULT NULL,
                  `date_affectation` datetime DEFAULT NULL,
                  PRIMARY KEY (`id_affectation`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            
            conn.commit()
            
            # Vérification finale
            print("🔍 Vérification finale...")
            result = conn.execute(sa.text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"✅ Tables créées: {[table[0] for table in tables]}")
            
            print("🎉 Import complet réussi!")
            print(f"📊 Nombre de tables: {len(tables)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Import complet de toutes vos données...")
    success = import_all_data()
    
    if success:
        print("\n✅ Succès! Vérifiez maintenant dans Railway Data!")
        print("🔄 Actualisez la page Railway (F5)")
        print("📋 Vous devriez voir vos tables maintenant!")
    else:
        print("\n💡 Il y a eu un problème, vérifiez les erreurs ci-dessus")