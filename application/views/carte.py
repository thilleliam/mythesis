from folium import Map, Marker, Popup, Icon
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

# Import de votre modèle Chantier
from application.models.chantiers import Chantier
from application.config import Base, engine

class CarteChantiers(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Carte des Chantiers")
        self.setGeometry(100, 100, 1000, 800)
        
        # Layout principal
        layout = QVBoxLayout()
        
        # Création du widget pour afficher la carte web
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)
        
        # Widget central
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        # Création de la carte
        self.creer_carte()
        
    def creer_carte(self):
        """Crée une carte Folium avec les positions des chantiers depuis la base de données"""
        # Connexion à la base de données
        session = Session(engine)
        
        # Récupération de tous les chantiers
        chantiers = session.query(Chantier).all()
        session.close()
        
        # Déterminer le centre de la carte (moyenne des coordonnées)
        if chantiers:
            lat_moy = sum(c.latitude for c in chantiers if c.latitude is not None) / len([c for c in chantiers if c.latitude is not None]) if any(c.latitude is not None for c in chantiers) else 0
            lon_moy = sum(c.longitude for c in chantiers if c.longitude is not None) / len([c for c in chantiers if c.longitude is not None]) if any(c.longitude is not None for c in chantiers) else 0
        else:
            # Coordonnées par défaut (centre de la France)
            lat_moy, lon_moy = 46.603354, 1.888334
        
        # Création de la carte
        carte = Map(location=[lat_moy, lon_moy], zoom_start=6)
        
        # Ajout des marqueurs pour chaque chantier
        for chantier in chantiers:
            if chantier.latitude is not None and chantier.longitude is not None:
                # Gestion des valeurs None pour éviter les erreurs de formatage
                id_client = chantier.id_client or "Non spécifié"
                localisation = chantier.localisation or "Non spécifiée"
                nature_terrain = chantier.nature_terrain or "Non spécifiée"
                distance_goudron = f"{chantier.distanceAllerGoudron} km" if chantier.distanceAllerGoudron is not None else "Non spécifiée"
                distance_piste = f"{chantier.distanceAllerPiste} km" if chantier.distanceAllerPiste is not None else "Non spécifiée"
                temps_aller = f"{chantier.temps_aller:.2f} h" if chantier.temps_aller is not None else "Non spécifié"
                
                # Création d'un popup avec les informations du chantier
                popup_content = f"""
                <b>ID Client:</b> {id_client}<br>
                <b>Localisation:</b> {localisation}<br>
                <b>Nature du terrain:</b> {nature_terrain}<br>
                <b>Distance goudron:</b> {distance_goudron}<br>
                <b>Distance piste:</b> {distance_piste}<br>
                <b>Temps aller:</b> {temps_aller}
                """
                
                popup = Popup(popup_content, max_width=300)
                
                # Création du marqueur
                marker = Marker(
                    location=[chantier.latitude, chantier.longitude],
                    popup=popup,
                    tooltip=f"Chantier: {id_client}",
                    icon=Icon(color='blue', icon='info-sign')
                )
                marker.add_to(carte)
        
        # Sauvegarde temporaire de la carte HTML
        temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_map.html")
        carte.save(temp_file)
        
        # Affichage dans le navigateur
        self.browser.load(QUrl.fromLocalFile(temp_file))

def main():
    app = QApplication(sys.argv)
    fenetre = CarteChantiers()
    fenetre.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()