from application.database import SessionLocal
from application.models.vehicule import Vehicule
from sqlalchemy.exc import IntegrityError

def insert_vehicules():
    """
    Insère tous les véhicules dans la base de données
    """
    session = SessionLocal()
    
    # Données des véhicules extraites du fichier SQL
    vehicules_data = [
        ('0F085PHR', 'XPIVIKJT', '7G428JIQ', 'Porte-engin Astra', '4*4', 0, 0, 'Disponible'),
        ('0OINSCLC', 'B6TB8P6E', 'TOFCQ6HE', 'Semi-remorque simple RENAULT', '6*6', 10, 0, 'Disponible'),
        ('12TSC4J8', '63W82VYG', 'US73S0M9', 'Camions Frigo', '6*6', 7, 25, 'En panne'),
        ('1WI9OK55', 'T6RTWZF7', 'QFSALXZM', 'Camions Plateaux', '6*6', 12, 0, 'En panne'),
        ('23LH2RSV', 'FO8ZQINY', 'VOP01RRS', 'Tracteur Iveco  - Année 2008', '6*6', 35, 0, 'En panne'),
        ('2ZK3QXE8', 'TMYJHN8T', 'EYIIIC9B', 'Plateau Mercedes', ' 6×2', 35, 0, 'Disponible'),
        ('3', '', '', '', '', 22, 33, 'Disponible'),
        ('31981-04', 'F9JY7NXRBBT5DBZ1G', 'VEH-5969', 'Porte-engin Volvo FH16', '6*4', 22.9, 0, 'Disponible'),
        ('37153-43', 'U07JF527ZGHMBN0U6', 'VEH-5928', 'Plateau Peterbilt 389', '6*2', 14.5, 41, 'Disponible'),
        ('37409-24', 'CTMS5VW90XEU2LEMP', 'VEH-8682', 'MAN TGX Semi-remorque simple', '6*6', 25.3, 90.8, 'Disponible'),
        ('38JX3DZS', 'TWE302TT', '1SE0AD7K', 'Tracteur Astra  - Année 2012 & année 2016', '6*6', 0, 0, 'Disponible'),
        ('41417-41', 'VZ9JACT49XADPTUHL', 'VEH-9005', 'MAN TGX Semi-remorque simple', '6*2', 23.1, 84.5, 'Disponible'),
        ('41763-11', 'BZSDBLLAXRNE14ALM', 'VEH-3327', 'Renault T High Porte-engin', '6*6', 24.4, 0, 'Disponible'),
        ('439NCOHZ', 'WJ0FGB2O', 'SQPV3HK8', 'Semi-remorque Triple', '6*6', 7, 25, 'Disponible'),
        ('51LNQ5FA', 'ILIZ2B5T', 'XKCACKSP ', 'Camions Frigo ', '6*6', 7, 25, 'En panne'),
        ('54562-27', '1266XVCT2H3UWAWFV', 'VEH-1381', 'Scania R500 Semi-remorque simple', '4*4', 25.5, 95.8, 'Disponible'),
        ('56314-30', 'BZ634VLE0EZ37D35D', 'VEH-6883', 'Volvo FH16 Camions plateaux', '4*2', 10.7, 27.5, 'Disponible'),
        ('58059-03', 'TKVJ0WRWDH6L04542', 'VEH-1739', 'Mercedes Actros Semi-remorque simple', '6*4', 21.7, 83.9, 'Disponible'),
        ('5CJ0OQ03', 'K22ANIF7', 'J0AEC44Q', 'Camions plateaux', ' 6*6', 7, 25, 'Disponible'),
        ('5XI3U9M9', '4YHQGYTN', 'GUJKKU6H', 'Tracteur Iveco - Année 2008', '6*6', 35, 0, 'En panne'),
        ('63662-40', 'UMDM79HRD496964E7', 'VEH-6433', 'Freightliner Cascadia Plateau', '6*2', 14.9, 49.1, 'Disponible'),
        ('63966-36', 'SVLHKMU0HAVTX9JPR', 'VEH-3616', 'Camions plateaux Scania R500', '4*2', 9.5, 28.7, 'Disponible'),
        ('65826-41', '4PSUMRP0JE3CRVZZC', 'VEH-7068', 'Peterbilt 389 Porte-engin', '6*6', 24.7, 0, 'Disponible'),
        ('65898-08', '8DL2KHWZPW9JW49MY', 'VEH-3818', 'Peterbilt 389', 'Semi-remorque Triple', 33.2, 128, 'Disponible'),
        ('66H1ARFE', '6GCK91KQ', 'RRZQCWA6', '', 'Camions Frigo (6X6)', 7, 25, 'En panne'),
        ('6D2668YR', 'L1A9MGVW', 'UEETSQB0', 'Tracteur Astra - Année 2012 & année 2016', ' 6*6', 0, 0, 'Disponible'),
        ('73830-33', '36UJHVRAAABZR6C15', 'VEH-6154', 'DAF XF', 'Porte-engin', 25.8, 0, 'Disponible'),
        ('7G2OXRDV', 'C8FEU3X4', '1XHE2JBL', '', 'Camions Plateaux (6X6)', 12, None, 'En panne'),
        ('81014-23', 'MU16SG3PJM2ALL3H5', 'VEH-1451', 'Renault T High', 'Camions plateaux 6×6', 21.5, 57.8, 'Disponible'),
        ('855RB0AB', 'R53Q81ND', 'G5HHMPYM', 'Iveco', 'Tracteur (6X6) Iveco - Année 2008', 35, None, 'Disponible'),
        ('87600-11', 'S5PPRXXAX1D0JT3R0', 'VEH-7856', 'Freightliner Cascadia', 'Semi-remorque simple', 25.6, 93.1, 'Disponible'),
        ('8HOBTL12', '2KU9IAA5', '6KO4HML3', '', 'Camions plateaux 4×2', 7, 25, 'Disponible'),
        ('91169-47', 'D1ZDJ479VGGDSJGGC', 'VEH-6925', 'Mercedes Actros', 'Camions plateaux 4×2', 10, 28.1, 'Disponible'),
        ('92455-10', '2S2YAC9ZVS6X7TGFZ', 'VEH-7668', 'MAN TGX', 'Plateau 6×2', 14.5, 40.5, 'Disponible'),
        ('93395-46', 'E86UANR8WKPSDT37Y', 'VEH-9321', 'Iveco S-Way', 'Semi-remorque Triple', 36.9, 111.9, 'Disponible'),
        ('94UDSS4B', '5X22OQX4', '0XOFR6ME', 'FIAT', 'Camion Plateau 10 tonnes (4X2)', 10, None, 'Disponible'),
        ('97X1489B', 'ZQNV0SXK', 'T4MRFK54', 'Fiat', 'Tracteur (6X4) - Fiat Année 2008', 35, None, 'Disponible'),
        ('99258-36', 'YU4KEZBA0SVBP6FLG', 'VEH-9390', 'Scania R500', 'Semi-remorque simple', 26, 94.2, 'Disponible'),
        ('9MOMEPEU', 'RPPWYXGA', 'D97HYOU2', 'FIAT', 'Camion Plateau 10 tonnes (4X2)', 10, None, 'Disponible'),
        ('9P2H2OE8', '6FF1YDBD', 'RMEFW2U3', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('A5PCISRL', 'PBC2NPJF', 'NZ2Q2VVB', 'RENAULT', 'Camion Plateau 10 tonnes (4X2)', 10, None, 'Disponible'),
        ('APYZSRYT', 'U0215W20', 'Y6A1SCYW', '', 'Camion Citerne à Eau (4X2)', 8, 8000, 'Disponible'),
        ('AVFP96SO', '0PMOHPUF', '04LPKCIW', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('AZPI46N0', 'XB1JN2BO', '2T5NHTW4', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('BGF54CDD', '2EGCB0FL', '4ALTVU2X', '', 'Camions Plateaux (6X6)', 12, None, 'En panne'),
        ('C2NJA9GQ', 'U5TJO3UB', 'R746NKX9', 'Iveco', 'Tracteur (6X6) Iveco - Année 2008', 35, None, 'Disponible'),
        ('C682D9AN', '20AQLKC2', 'NK7QF05O', '', 'Camion Citerne Astra (Hydro cureur Neuf)', 12, 18000, 'En panne'),
        ('CG65X21K', '7MQETQGO', 'TXCT639M', 'RENAULT', 'Camion Plateau 10 tonnes (4X2)', None, None, 'En panne'),
        ('CZAOYTDV', 'E6D66Y8A', 'WFC0BDG1', '', 'Camions Plateaux (6X6)', 12, None, 'En panne'),
        ('D1IBPRTJ', 'PFPB5SNU', 'MUWQY7TU', 'Sonacom/Hyundai', 'Camion 2,5 tonnes à Benne (4X2)', 2.5, 3, 'En panne'),
        ('D4YQ2QZ6', 'NFAHVX34', 'S6244XKZ', 'Fiat', 'Tracteur (6X4) - Fiat Année 2008', 35, None, 'En panne'),
        ('DEF456', '987654321', 'V002', 'Peugeot Partner', 'Fourgon', 2.5, 8, None),
        ('DER5DPHF', '58NEWHXE', '3WDHVHF2', 'Mercedes', 'Tracteur (6X4) Mercedes - Année 2023', 35, None, 'Disponible'),
        ('DGUFI7S9', '551SCR08', '2JDPZ9ZE', 'Iveco', 'Tracteur (6X6) Iveco - Année 2008', 35, None, 'En panne'),
        ('DPVN5Y17', 'W5E8HXK3', '427WVXO4', 'Iveco', 'Tracteur (6X6) Iveco - Année 2008', 35, None, 'En panne'),
        ('E5N72NMH', 'QK7Z9PU1', '30P0PQND', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('EUG52GZR', '12CH4ZAA', '4IRDZZF4', 'Astra', 'Tracteur (6X6) (Astra) - Année 2012 & année 2016', None, None, 'Disponible'),
        ('FFKW5K6U', '8O433P53', 'CB5L9NPR', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('FGS6SVKO', 'UDEQ5GNY', '3BCKST4D', '', 'Camions Frigo (6X6)', 7, 25, 'En panne'),
        ('H6JHPTS1', 'GGJE8Q3Q', 'ZD18AYUB', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('H9ZCCGM9', 'FF97KSC0', 'B6LHVJ0D', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('HEUSNBKJ', '8SFFYWYQ', 'DC1HP8F0', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('HKTB1O0H', 'OGVIGB80', '6XXDIC2G', '', 'Camion Citerne (Hydro cureur)', 12, 12000, 'En panne'),
        ('I4I3DN7C', 'N76U8QXR', 'VJXZEWSY', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('IDKADADW', 'AVCF5XMS', 'ADSP5HRI', 'Astra', 'Tracteur (6X6) (Astra) - Année 2012 & année 2016', None, None, 'En panne'),
        ('IKH9TU86', 'W0CF9J7B', '8U7U3PW1', '', 'Camions Plateaux (4X2)', 7, None, 'Disponible'),
        ('JGK3D3U7', 'J6OA1MZV', '4MQ60XCW', '', 'Camions Ateliers (6X6)', None, None, 'Disponible'),
        ('JQOUKPLS', '34UARYRU', 'J6NGQ0OI', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('JYKN9NYV', 'T7SHC9U5', 'FQJVV8N1', 'Astra', 'Tracteur (6X6) (Astra) - Année 2012 & année 2016', None, None, 'En panne'),
        ('KLACA5SY', 'L1H7HYE7', 'KLWX8LOV', 'Fiat', 'Tracteur (6X4) - Fiat Année 2008', 35, None, 'En panne'),
        ('KWBCRLS2', 'GR5WI2TS', 'KYFLG2DE', '', 'Camions Plateaux (6X6)', 12, None, 'Disponible'),
        ('LQ6Y37LR', 'ERZ0ZI3V', 'D0RO7ILE', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('MQD1UM6D', 'VJFU9GHT', 'XY1PB5R6', '', 'Camions Plateaux (6X6)', 12, None, 'Disponible'),
        ('O4Q5OUH4', 'OUKI8U2G', 'C11597FL', 'Sonacom/Hyundai', 'Camion 2,5 tonnes à Benne (4X2)', 2.5, 3, 'En panne'),
        ('OJ0YP9I8', '34KBAR6Z', 'Q8VOLBA4', 'Sonacom/Hyundai', 'Camion 2,5 tonnes à Benne (4X2)', 2.5, 3, 'En panne'),
        ('P05ZGKZ8', '6K7J9U7C', 'MFAIJP6R', '', 'Camions Plateaux (6X6)', 12, None, 'Disponible'),
        ('Q7JSBKCO', '1HTI9PEH', 'MOUNYKAH', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('QF7W9YHB', '92LH5RV8', 'UAMWFTFL', '', 'Camions Plateaux (6X6)', 12, None, 'Disponible'),
        ('QKJ5732G', '2YXNQAKA', 'F1ZESI9X', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('SBGLZUU9', 'G6K62TVO', 'LBFSNWNE', '', 'Camions Plateaux (6X6)', 12, None, 'En panne'),
        ('SWKVXJBH', 'CCVAYV3G', '6EZ7DAYQ', '', 'Camions Frigo (6X6)', 7, 25, 'Disponible'),
        ('TPPJ49VI', 'DZJX5UJB', '15GKOK74', '', 'Camion Citerne (Hydro cureur)', 12, 12000, 'En panne'),
        ('U1E5XZJD', 'NM27N7J1', '9S7DEXF5', 'Iveco', 'Tracteur (6X6) Iveco - Année 2008', 35, None, 'Disponible'),
        ('U961GKEY', '5OA0GU2C', '54RI1K3B', 'Sonacom', 'Camion Plateau 10 tonnes (4X2)', None, None, 'En panne'),
        ('V40VPHGC', 'GFYPI227', 'DGAU3J9G', 'Astra', 'Tracteur (6X6) (Astra) - Année 2012 & année 2016', None, None, 'En panne'),
        ('VD175M0O', 'RUDMM77M', '29UYZUBC', 'Iveco', 'Tracteur (6X6) Iveco - Année 2008', 35, None, 'En panne'),
        ('VKRPZXJ8', 'OK6B4MJV', '3MZ59MT2', '', 'Camions Plateaux (6X6) à Grue', 20, None, 'Disponible'),
        ('VS8SVSY7', 'Q78UJCQA', 'MPGQLZU2', 'Iveco', 'Tracteur (6X6) Iveco - Année 2008', 35, None, 'Disponible'),
        ('WF27XZST', '1KWBTE62', 'H8DAK4IG', 'Camions Plateaux', ' 6*6', 12, 0, 'En panne'),
        ('WOV91XSO', '1559TQX2', 'NGO06247', 'Camions Plateaux', '4*2', 7, 0, 'Disponible'),
        ('WRHPLQJK', 'KLU56972', 'JIMSV104', 'Tracteur Astra- Année 2012 & année 2016', '6*6', 0, 0, 'Disponible'),
        ('XPQW66WI', 'B7XHMC3K', '6H1YL24B', 'Camions Plateaux ', '4*2', 7, 0, 'Disponible'),
        ('YC6AVR76', 'SGC946I0', 'CV5MW7YC', 'Camions Plateaux', '6*6', 12, 0, 'Disponible'),
        ('Z3YU5P7V', 'DH12K8XT', 'RUK2QC41', 'Tracteur Fiat- Fiat Année 2008', '6*4', 35, 0, 'En panne'),
        ('ZCJ6AIMM', 'GUKORILK', 'V5LK4FFP', '', 'Camions Plateaux (6X6) à Grue', 20, None, 'Disponible'),
    ]
    
    try:
        compteur_insere = 0
        compteur_ignore = 0
        
        for data in vehicules_data:
            # Créer un objet Vehicule
            vehicule = Vehicule(
                immatriculation=data[0],
                numero_chassis=data[1] if data[1] else None,
                numero_interne=data[2] if data[2] else None,
                marque_modele=data[3] if data[3] else None,
                type_vehicule=data[4] if data[4] else None,
                capacite_tonne=data[5] if data[5] is not None else None,
                capacite_volume=data[6] if data[6] is not None else None,
                etat=data[7] if data[7] else "Disponible"
            )
            
            try:
                # Vérifier si le véhicule existe déjà
                vehicule_existant = session.query(Vehicule).filter_by(
                    immatriculation=data[0]
                ).first()
                
                if vehicule_existant is None:
                    session.add(vehicule)
                    session.commit()
                    compteur_insere += 1
                    print(f"✓ Véhicule {data[0]} inséré avec succès")
                else:
                    compteur_ignore += 1
                    print(f"⚠ Véhicule {data[0]} existe déjà, ignoré")
                    
            except IntegrityError as e:
                session.rollback()
                compteur_ignore += 1
                print(f"✗ Erreur lors de l'insertion du véhicule {data[0]}: {str(e)}")
            except Exception as e:
                session.rollback()
                print(f"✗ Erreur inattendue pour le véhicule {data[0]}: {str(e)}")
        
        print(f"\n📊 Résumé de l'insertion:")
        print(f"   - Véhicules insérés: {compteur_insere}")
        print(f"   - Véhicules ignorés: {compteur_ignore}")
        print(f"   - Total traité: {len(vehicules_data)}")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Erreur générale lors de l'insertion: {str(e)}")
    finally:
        session.close()

def verifier_insertion():
    """
    Vérifie que l'insertion s'est bien déroulée
    """
    session = SessionLocal()
    try:
        # Compter le nombre total de véhicules
        total_vehicules = session.query(Vehicule).count()
        print(f"\n📈 Nombre total de véhicules dans la base: {total_vehicules}")
        
        # Compter par état
        disponibles = session.query(Vehicule).filter_by(etat="Disponible").count()
        en_panne = session.query(Vehicule).filter_by(etat="En panne").count()
        
        print(f"   - Disponibles: {disponibles}")
        print(f"   - En panne: {en_panne}")
        
        # Afficher quelques exemples
        print(f"\n🚛 Exemples de véhicules insérés:")
        exemples = session.query(Vehicule).limit(5).all()
        for vehicule in exemples:
            print(f"   - {vehicule.immatriculation}: {vehicule.marque_modele} ({vehicule.etat})")
            
    except Exception as e:
        print(f"✗ Erreur lors de la vérification: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Début de l'insertion des véhicules...")
    insert_vehicules()
    verifier_insertion()
    print("✅ Processus terminé!")