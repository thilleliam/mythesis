#!/usr/bin/env python3
"""
Modèle Segment pour la sauvegarde des segments tracés sur la carte
Fichier: application/models/segments.py
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from application.config import Base, engine

class Segment(Base):
    """
    Modèle pour stocker les segments tracés sur la carte avec leurs distances
    """
    __tablename__ = 'segments'
    
    # Clé primaire
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Informations du premier point
    point1_nom = Column(String(255), nullable=False)
    point1_latitude = Column(Float, nullable=False)
    point1_longitude = Column(Float, nullable=False)
    point1_type = Column(String(50), nullable=False)  # 'chantier' ou 'manuel'
    point1_id_reference = Column(String(100))  # ID du chantier ou référence
    
    # Informations du deuxième point  
    point2_nom = Column(String(255), nullable=False)
    point2_latitude = Column(Float, nullable=False)
    point2_longitude = Column(Float, nullable=False)
    point2_type = Column(String(50), nullable=False)  # 'chantier' ou 'manuel'
    point2_id_reference = Column(String(100))  # ID du chantier ou référence
    
    # Propriétés du segment
    distance_km = Column(Float, nullable=False)
    couleur = Column(String(20), default='blue')
    epaisseur = Column(Integer, default=3)
    afficher_distance = Column(Boolean, default=True)
    
    # Métadonnées
    nom_segment = Column(String(255))  # Nom optionnel du segment
    description = Column(Text)  # Description optionnelle
    date_creation = Column(DateTime, default=datetime.utcnow)
    date_modification = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Utilisateur qui a créé le segment (optionnel)
    cree_par = Column(String(100))
    
    # Index pour améliorer les performances
    __table_args__ = (
        Index('idx_segments_point1_coords', 'point1_latitude', 'point1_longitude'),
        Index('idx_segments_point2_coords', 'point2_latitude', 'point2_longitude'),
        Index('idx_segments_date_creation', 'date_creation'),
        Index('idx_segments_distance', 'distance_km'),
    )
    
    def __repr__(self):
        return f"<Segment(id={self.id}, {self.point1_nom} -> {self.point2_nom}, {self.distance_km:.2f}km)>"
    
    def to_dict(self):
        """Convertit le segment en dictionnaire pour faciliter la manipulation"""
        return {
            'id': self.id,
            'point1': {
                'nom': self.point1_nom,
                'lat': self.point1_latitude,
                'lon': self.point1_longitude,
                'type': self.point1_type,
                'id_reference': self.point1_id_reference
            },
            'point2': {
                'nom': self.point2_nom,
                'lat': self.point2_latitude,
                'lon': self.point2_longitude,
                'type': self.point2_type,
                'id_reference': self.point2_id_reference
            },
            'distance': self.distance_km,
            'couleur': self.couleur,
            'epaisseur': self.epaisseur,
            'afficher_distance': self.afficher_distance,
            'nom_segment': self.nom_segment,
            'description': self.description,
            'date_creation': self.date_creation,
            'cree_par': self.cree_par
        }

class GestionnaireSegments:
    """
    Classe pour gérer les opérations CRUD sur les segments
    """
    
    @staticmethod
    def sauvegarder_segment(point1, point2, distance, couleur='blue', epaisseur=3, 
                          afficher_distance=True, nom_segment=None, description=None, 
                          cree_par=None):
        """
        Sauvegarde un segment dans la base de données
        
        Args:
            point1 (dict): Informations du premier point
            point2 (dict): Informations du deuxième point
            distance (float): Distance en km
            couleur (str): Couleur du segment
            epaisseur (int): Épaisseur du trait
            afficher_distance (bool): Afficher la distance
            nom_segment (str): Nom optionnel du segment
            description (str): Description optionnelle
            cree_par (str): Utilisateur créateur
            
        Returns:
            Segment: L'objet segment créé ou None en cas d'erreur
        """
        try:
            with Session(engine) as session:
                # Vérifier si le segment existe déjà (dans les deux sens)
                segment_existant = session.query(Segment).filter(
                    (
                        (Segment.point1_latitude == point1['lat']) & 
                        (Segment.point1_longitude == point1['lon']) &
                        (Segment.point2_latitude == point2['lat']) & 
                        (Segment.point2_longitude == point2['lon'])
                    ) |
                    (
                        (Segment.point1_latitude == point2['lat']) & 
                        (Segment.point1_longitude == point2['lon']) &
                        (Segment.point2_latitude == point1['lat']) & 
                        (Segment.point2_longitude == point1['lon'])
                    )
                ).first()
                
                if segment_existant:
                    print(f"⚠️  Segment entre {point1['nom']} et {point2['nom']} existe déjà (ID: {segment_existant.id})")
                    return segment_existant
                
                # Créer le nouveau segment
                nouveau_segment = Segment(
                    point1_nom=point1['nom'],
                    point1_latitude=point1['lat'],
                    point1_longitude=point1['lon'],
                    point1_type=point1['type'],
                    point1_id_reference=point1.get('id_reference', point1.get('id', '')),
                    
                    point2_nom=point2['nom'],
                    point2_latitude=point2['lat'],
                    point2_longitude=point2['lon'],
                    point2_type=point2['type'],
                    point2_id_reference=point2.get('id_reference', point2.get('id', '')),
                    
                    distance_km=distance,
                    couleur=couleur,
                    epaisseur=epaisseur,
                    afficher_distance=afficher_distance,
                    nom_segment=nom_segment,
                    description=description,
                    cree_par=cree_par
                )
                
                session.add(nouveau_segment)
                session.commit()
                session.refresh(nouveau_segment)
                
                print(f"✅ Segment sauvegardé: {point1['nom']} -> {point2['nom']} ({distance:.2f} km) [ID: {nouveau_segment.id}]")
                return nouveau_segment
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du segment: {str(e)}")
            return None
    
    @staticmethod
    def charger_tous_segments():
        """
        Charge tous les segments depuis la base de données
        
        Returns:
            list: Liste des segments
        """
        try:
            with Session(engine) as session:
                segments = session.query(Segment).order_by(Segment.date_creation.desc()).all()
                print(f"📊 {len(segments)} segments chargés depuis la base de données")
                return segments
                
        except Exception as e:
            print(f"❌ Erreur lors du chargement des segments: {str(e)}")
            return []
    
    @staticmethod
    def supprimer_segment(segment_id):
        """
        Supprime un segment de la base de données
        
        Args:
            segment_id (int): ID du segment à supprimer
            
        Returns:
            bool: True si supprimé avec succès
        """
        try:
            with Session(engine) as session:
                segment = session.query(Segment).filter(Segment.id == segment_id).first()
                if segment:
                    session.delete(segment)
                    session.commit()
                    print(f"✅ Segment ID {segment_id} supprimé")
                    return True
                else:
                    print(f"⚠️  Segment ID {segment_id} non trouvé")
                    return False
                    
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {str(e)}")
            return False
    
    @staticmethod
    def obtenir_statistiques_segments():
        """
        Obtient des statistiques sur les segments
        
        Returns:
            dict: Statistiques des segments
        """
        try:
            with Session(engine) as session:
                stats = session.query(
                    func.count(Segment.id).label('total_segments'),
                    func.sum(Segment.distance_km).label('distance_totale'),
                    func.avg(Segment.distance_km).label('distance_moyenne'),
                    func.min(Segment.distance_km).label('distance_min'),
                    func.max(Segment.distance_km).label('distance_max')
                ).first()
                
                return {
                    'total_segments': stats.total_segments or 0,
                    'distance_totale': round(stats.distance_totale or 0, 2),
                    'distance_moyenne': round(stats.distance_moyenne or 0, 2),
                    'distance_min': round(stats.distance_min or 0, 2),
                    'distance_max': round(stats.distance_max or 0, 2)
                }
                
        except Exception as e:
            print(f"❌ Erreur lors du calcul des statistiques: {str(e)}")
            return {}

    @staticmethod
    def obtenir_segment_par_id(segment_id):
        """
        Récupère un segment par son ID
        
        Args:
            segment_id (int): ID du segment
            
        Returns:
            Segment: Le segment trouvé ou None
        """
        try:
            with Session(engine) as session:
                segment = session.query(Segment).filter(Segment.id == segment_id).first()
                return segment
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du segment: {str(e)}")
            return None

    @staticmethod
    def mettre_a_jour_segment(segment_id, **kwargs):
        """
        Met à jour un segment existant
        
        Args:
            segment_id (int): ID du segment à mettre à jour
            **kwargs: Attributs à mettre à jour
            
        Returns:
            bool: True si mis à jour avec succès
        """
        try:
            with Session(engine) as session:
                segment = session.query(Segment).filter(Segment.id == segment_id).first()
                if segment:
                    for key, value in kwargs.items():
                        if hasattr(segment, key):
                            setattr(segment, key, value)
                    
                    segment.date_modification = datetime.utcnow()
                    session.commit()
                    print(f"✅ Segment ID {segment_id} mis à jour")
                    return True
                else:
                    print(f"⚠️  Segment ID {segment_id} non trouvé")
                    return False
                    
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {str(e)}")
            return False

def creer_table_segments():
    """
    Script pour créer la table segments dans votre base de données
    À exécuter une seule fois pour créer la table
    """
    try:
        # Créer la table segments
        Base.metadata.create_all(engine, tables=[Segment.__table__])
        print("✅ Table 'segments' créée avec succès!")
        
        # Vérifier la création
        from sqlalchemy import inspect
        inspector = inspect(engine)
        if 'segments' in inspector.get_table_names():
            print("✅ Confirmation: Table 'segments' existe dans la base de données")
            
            # Afficher les colonnes créées
            columns = inspector.get_columns('segments')
            print("\nColonnes créées:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
                
            return True
        else:
            print("❌ Erreur: Table 'segments' non trouvée")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {str(e)}")
        return False

# Test du modèle
if __name__ == "__main__":
    print("🧪 TEST DU MODÈLE SEGMENT")
    print("=" * 40)
    
    # 1. Créer la table
    print("1. Création de la table...")
    if creer_table_segments():
        print("✅ Table créée avec succès")
    else:
        print("❌ Échec de la création de la table")
        exit(1)
    
    # 2. Test d'insertion
    print("\n2. Test d'insertion...")
    point1 = {
        'nom': 'Test Point A',
        'lat': 48.8566,
        'lon': 2.3522,
        'type': 'test',
        'id_reference': 'TEST_A'
    }
    
    point2 = {
        'nom': 'Test Point B',
        'lat': 48.8606,
        'lon': 2.3376,
        'type': 'test',
        'id_reference': 'TEST_B'
    }
    
    segment = GestionnaireSegments.sauvegarder_segment(
        point1, point2, 1.25,
        nom_segment="Segment de test",
        description="Test du modèle",
        cree_par="test_script"
    )
    
    if segment:
        print(f"✅ Segment créé avec l'ID: {segment.id}")
        
        # 3. Test de lecture
        print("\n3. Test de lecture...")
        segments = GestionnaireSegments.charger_tous_segments()
        if segments:
            print(f"✅ {len(segments)} segments trouvés")
        
        # 4. Test des statistiques
        print("\n4. Test des statistiques...")
        stats = GestionnaireSegments.obtenir_statistiques_segments()
        print(f"Statistiques: {stats}")
        
        # 5. Test de suppression
        print("\n5. Test de suppression...")
        if GestionnaireSegments.supprimer_segment(segment.id):
            print("✅ Segment supprimé avec succès")
        
    print("\n🎉 Tests terminés !")