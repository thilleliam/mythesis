from sqlalchemy.orm import sessionmaker
from application.models import TransfererEquipement, Equipement  # Assure-toi que la classe Equipement existe
from application.database import engine
import pandas as pd

# Chargement des données depuis l'Excel
file_path = '/mnt/data/canevas modifee.xlsx'
df = pd.read_excel(file_path, sheet_name='Feuil1')

# Connexion à la base de données
Session = sessionmaker(bind=engine)
session = Session()

# Données à insérer dans la table TransfererEquipement
transfer_data = []

# Parcours des lignes du DataFrame
for index, row in df.iterrows():
    if pd.isna(row['ID Client']) or pd.isna(row['Désignation de l\'équipement à transférer']):
        continue  # On ignore les lignes où les données essentielles sont manquantes

    # Recherche de l'ID de l'équipement à partir du nom dans la table Equipement
    equipement = session.query(Equipement).filter_by(nom_equipement=row['Désignation de l\'équipement à transférer']).first()
    
    # Si l'équipement existe, on prépare les données à insérer
    if equipement:
        transfer_data.append(TransfererEquipement(
            id_client=row['ID Client'],
            volet=row['Volet'] if pd.notna(row['Volet']) else None,
            nom_equipement=row['Désignation de l\'équipement à transférer'],
            id_equipement=equipement.ID_equipement,
            modalite_transport=row['Modalité de transport (Tractable/chargeable)'] if pd.notna(row['Modalité de transport (Tractable/chargeable)']) else None,
            total_equipements=row['Total des équipements à transférer'] if pd.notna(row['Total des équipements à transférer']) else 0,
            douze_semaines_avant=row['12 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['12 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            onze_semaines_avant=row['11 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['11 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            dix_semaines_avant=row['10 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['10 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            neuf_semaines_avant=row['09 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['09 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            huit_semaines_avant=row['08 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['08 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            sept_semaines_avant=row['07 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['07 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            six_semaines_avant=row['06 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['06 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            cinq_semaines_avant=row['05 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['05 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            quatre_semaines_avant=row['04 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['04 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            trois_semaines_avant=row['03 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['03 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            deux_semaines_avant=row['02 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['02 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            un_semaines_avant=row['01 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['01 semaines avant la fin de l\'ancien projet Qté à transférer']) else None,
            zero_semaines_avant=row['0 semaines avant la fin de l\'ancien projet Qté à transférer'] if pd.notna(row['0 semaines avant la fin de l\'ancien projet Qté à transférer']) else None
        ))

# Commit des données dans la base de données
try:
    session.bulk_save_objects(transfer_data)
    session.commit()
    print(f"Mise à jour terminée : {len(transfer_data)} équipements transférés ajoutés.")
except Exception as e:
    session.rollback()
    print(f"Erreur lors de l'ajout des équipements transférés : {e}")
finally:
    session.close()
