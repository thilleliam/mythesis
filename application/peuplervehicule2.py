from application.database import SessionLocal
from application.models.vehicule import Vehicule
from sqlalchemy import or_

def supprimer_tracteurs_et_citernes():
    """
    Supprime tous les tracteurs et camions citernes de la base de données
    """
    session = SessionLocal()
    
    try:
        print("🔍 Recherche des tracteurs et camions citernes...")
        
        # Rechercher tous les véhicules qui sont des tracteurs ou des citernes
        vehicules_a_supprimer = session.query(Vehicule).filter(
            or_(
                # Recherche par marque_modele contenant "tracteur"
                Vehicule.marque_modele.ilike('%tracteur%'),
                # Recherche par marque_modele contenant "citerne"
                Vehicule.marque_modele.ilike('%citerne%'),
                # Recherche par type_vehicule pour les tracteurs (optionnel)
                Vehicule.type_vehicule.ilike('%tracteur%')
            )
        ).all()
        
        if not vehicules_a_supprimer:
            print("ℹ️  Aucun tracteur ou camion citerne trouvé dans la base de données.")
            return
        
        # Afficher la liste des véhicules qui vont être supprimés
        print(f"\n📋 {len(vehicules_a_supprimer)} véhicule(s) trouvé(s) à supprimer:")
        print("-" * 80)
        
        tracteurs_count = 0
        citernes_count = 0
        
        for vehicule in vehicules_a_supprimer:
            print(f"   • {vehicule.immatriculation}: {vehicule.marque_modele} ({vehicule.etat})")
            
            if 'tracteur' in vehicule.marque_modele.lower():
                tracteurs_count += 1
            if 'citerne' in vehicule.marque_modele.lower():
                citernes_count += 1
        
        print(f"\n📊 Répartition:")
        print(f"   - Tracteurs: {tracteurs_count}")
        print(f"   - Camions citernes: {citernes_count}")
        print(f"   - Total: {len(vehicules_a_supprimer)}")
        
        # Demander confirmation (optionnel - vous pouvez commenter cette partie)
        confirmation = input(f"\n⚠️  Êtes-vous sûr de vouloir supprimer ces {len(vehicules_a_supprimer)} véhicules? (oui/non): ")
        if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
            print("❌ Suppression annulée par l'utilisateur.")
            return
        
        # Procéder à la suppression
        print(f"\n🗑️  Suppression en cours...")
        
        vehicules_supprimes = 0
        vehicules_erreur = 0
        
        for vehicule in vehicules_a_supprimer:
            try:
                session.delete(vehicule)
                session.commit()
                vehicules_supprimes += 1
                print(f"✓ Supprimé: {vehicule.immatriculation} - {vehicule.marque_modele}")
                
            except Exception as e:
                session.rollback()
                vehicules_erreur += 1
                print(f"✗ Erreur lors de la suppression de {vehicule.immatriculation}: {str(e)}")
        
        print(f"\n📊 Résumé de la suppression:")
        print(f"   - Véhicules supprimés: {vehicules_supprimes}")
        print(f"   - Erreurs: {vehicules_erreur}")
        print(f"   - Total traité: {len(vehicules_a_supprimer)}")
        
        if vehicules_supprimes > 0:
            print(f"✅ {vehicules_supprimes} véhicule(s) supprimé(s) avec succès!")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Erreur générale lors de la suppression: {str(e)}")
        raise
    finally:
        session.close()

def supprimer_par_requete_directe():
    """
    Alternative: suppression directe par requête SQL (plus rapide pour de gros volumes)
    """
    session = SessionLocal()
    
    try:
        print("🔍 Suppression directe des tracteurs et camions citernes...")
        
        # Compter d'abord les véhicules concernés
        count_tracteurs = session.query(Vehicule).filter(
            Vehicule.marque_modele.ilike('%tracteur%')
        ).count()
        
        count_citernes = session.query(Vehicule).filter(
            Vehicule.marque_modele.ilike('%citerne%')
        ).count()
        
        total_count = session.query(Vehicule).filter(
            or_(
                Vehicule.marque_modele.ilike('%tracteur%'),
                Vehicule.marque_modele.ilike('%citerne%')
            )
        ).count()
        
        print(f"📊 Véhicules à supprimer:")
        print(f"   - Tracteurs: {count_tracteurs}")
        print(f"   - Camions citernes: {count_citernes}")
        print(f"   - Total: {total_count}")
        
        if total_count == 0:
            print("ℹ️  Aucun véhicule à supprimer.")
            return
        
        # Suppression directe
        vehicules_supprimes = session.query(Vehicule).filter(
            or_(
                Vehicule.marque_modele.ilike('%tracteur%'),
                Vehicule.marque_modele.ilike('%citerne%')
            )
        ).delete(synchronize_session=False)
        
        session.commit()
        
        print(f"✅ {vehicules_supprimes} véhicule(s) supprimé(s) avec succès!")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Erreur lors de la suppression: {str(e)}")
        raise
    finally:
        session.close()

def verifier_suppression():
    """
    Vérifie que la suppression s'est bien déroulée
    """
    session = SessionLocal()
    try:
        # Vérifier qu'il ne reste plus de tracteurs ou citernes
        tracteurs_restants = session.query(Vehicule).filter(
            Vehicule.marque_modele.ilike('%tracteur%')
        ).count()
        
        citernes_restantes = session.query(Vehicule).filter(
            Vehicule.marque_modele.ilike('%citerne%')
        ).count()
        
        total_vehicules = session.query(Vehicule).count()
        
        print(f"\n📈 Vérification post-suppression:")
        print(f"   - Tracteurs restants: {tracteurs_restants}")
        print(f"   - Citernes restantes: {citernes_restantes}")
        print(f"   - Total véhicules dans la base: {total_vehicules}")
        
        if tracteurs_restants == 0 and citernes_restantes == 0:
            print("✅ Suppression réussie: aucun tracteur ou citerne restant!")
        else:
            print("⚠️  Il reste encore des tracteurs ou citernes dans la base.")
            
        # Afficher quelques exemples de véhicules restants
        if total_vehicules > 0:
            print(f"\n🚛 Exemples de véhicules restants:")
            exemples = session.query(Vehicule).limit(5).all()
            for vehicule in exemples:
                print(f"   - {vehicule.immatriculation}: {vehicule.marque_modele} ({vehicule.etat})")
        
    except Exception as e:
        print(f"✗ Erreur lors de la vérification: {str(e)}")
    finally:
        session.close()

def main():
    """
    Fonction principale
    """
    print("🚀 Début de la suppression des tracteurs et camions citernes...")
    print("=" * 70)
    
    try:
        # Choisir la méthode de suppression
        print("\n🔧 Méthodes de suppression disponibles:")
        print("1. Suppression détaillée (affiche chaque véhicule)")
        print("2. Suppression rapide (requête directe)")
        
        choix = input("\nChoisissez une méthode (1 ou 2): ").strip()
        
        if choix == "1":
            supprimer_tracteurs_et_citernes()
        elif choix == "2":
            supprimer_par_requete_directe()
        else:
            print("❌ Choix invalide. Utilisation de la méthode détaillée par défaut.")
            supprimer_tracteurs_et_citernes()
        
        # Vérification
        verifier_suppression()
        
        print("\n" + "=" * 70)
        print("✅ Processus de suppression terminé!")
        
    except Exception as e:
        print(f"\n❌ Erreur critique: {str(e)}")
        raise

if __name__ == "__main__":
    main()