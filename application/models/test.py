#!/usr/bin/env python3
"""
Script de vérification de la table segments après migration Alembic
"""

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from application.config import engine

def verifier_table_segments():
    """
    Vérifie que la table segments a été correctement créée
    """
    print("🔍 VÉRIFICATION DE LA TABLE SEGMENTS")
    print("=" * 50)
    
    try:
        # Vérifier la connexion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Connexion à la base de données réussie")
        
        # Inspecter les tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'segments' in tables:
            print("✅ Table 'segments' trouvée dans la base de données")
            
            # Afficher la structure de la table
            print("\n📋 Structure de la table 'segments':")
            columns = inspector.get_columns('segments')
            
            print(f"{'Colonne':<25} {'Type':<20} {'Nullable':<10} {'Défaut'}")
            print("-" * 70)
            
            for col in columns:
                nullable = "OUI" if col['nullable'] else "NON"
                default = str(col['default']) if col['default'] else "-"
                print(f"{col['name']:<25} {str(col['type']):<20} {nullable:<10} {default}")
            
            # Vérifier les colonnes essentielles
            print("\n🔍 Vérification des colonnes essentielles:")
            colonnes_essentielles = [
                'id', 'point1_nom', 'point1_latitude', 'point1_longitude',
                'point2_nom', 'point2_latitude', 'point2_longitude', 
                'distance_km', 'couleur', 'date_creation'
            ]
            
            colonnes_presentes = [col['name'] for col in columns]
            
            for colonne in colonnes_essentielles:
                if colonne in colonnes_presentes:
                    print(f"   ✅ {colonne}")
                else:
                    print(f"   ❌ {colonne} - MANQUANTE")
            
            # Test d'insertion et de lecture
            print("\n🧪 Test d'insertion/lecture:")
            test_insertion_lecture()
            
            print("\n🎉 La table 'segments' est prête à être utilisée !")
            
        else:
            print("❌ Table 'segments' NON TROUVÉE")
            print("Tables disponibles:", tables)
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {str(e)}")

def test_insertion_lecture():
    """
    Test d'insertion et de lecture d'un segment
    """
    try:
        # Import du modèle (assurez-vous que le fichier existe)
        try:
            from application.models.segments import Segment
        except ImportError:
            print("⚠️  Modèle Segment non trouvé. Créez le fichier application/models/segments.py")
            return
        
        with Session(engine) as session:
            # Créer un segment de test
            segment_test = Segment(
                point1_nom="Test Point A",
                point1_latitude=48.8566,
                point1_longitude=2.3522,
                point1_type="test",
                point1_id_reference="TEST_A",
                
                point2_nom="Test Point B", 
                point2_latitude=48.8606,
                point2_longitude=2.3376,
                point2_type="test",
                point2_id_reference="TEST_B",
                
                distance_km=1.25,
                couleur="blue",
                epaisseur=3,
                afficher_distance=True,
                nom_segment="Segment de test",
                description="Test d'insertion après migration Alembic",
                cree_par="script_verification"
            )
            
            # Insérer
            session.add(segment_test)
            session.commit()
            session.refresh(segment_test)
            
            print(f"   ✅ Insertion réussie (ID: {segment_test.id})")
            
            # Lire
            segment_lu = session.query(Segment).filter(Segment.id == segment_test.id).first()
            if segment_lu:
                print(f"   ✅ Lecture réussie: {segment_lu.nom_segment}")
                print(f"      Distance: {segment_lu.distance_km} km")
                print(f"      Date création: {segment_lu.date_creation}")
            
            # Supprimer le test
            session.delete(segment_test)
            session.commit()
            print("   ✅ Suppression du segment de test réussie")
            
    except Exception as e:
        print(f"   ❌ Erreur lors du test: {str(e)}")

def afficher_statistiques_db():
    """
    Affiche des statistiques sur la base de données
    """
    print("\n📊 STATISTIQUES DE LA BASE DE DONNÉES")
    print("-" * 40)
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📈 Nombre total de tables: {len(tables)}")
        print("📋 Tables disponibles:")
        for table in sorted(tables):
            print(f"   • {table}")
        
        # Vérifier si la table segments contient des données
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as count FROM segments"))
            count = result.fetchone()[0]
            print(f"\n📊 Nombre de segments dans la table: {count}")
            
    except Exception as e:
        print(f"❌ Erreur lors du calcul des statistiques: {str(e)}")

if __name__ == "__main__":
    verifier_table_segments()
    afficher_statistiques_db()
    
    print("\n" + "=" * 50)
    print("🚀 PROCHAINES ÉTAPES:")
    print("1. Créez le fichier application/models/segments.py avec le modèle Segment")
    print("2. Modifiez votre classe CarteChantiers pour utiliser la sauvegarde")
    print("3. Testez la création de segments dans l'interface")
    print("=" * 50)