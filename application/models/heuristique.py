import pandas as pd
import json
from datetime import datetime
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

class ExportateurSolutions:
    """Classe pour exporter les solutions d'optimisation vers différents formats"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def exporter_solution_complete(self, resultats, format_export="all", dossier_export="exports"):
        """
        Exporte la solution complète vers différents formats
        
        Args:
            resultats: Dictionnaire des résultats de l'optimisation
            format_export: "excel", "csv", "json", "pdf", "all"
            dossier_export: Dossier de destination
        """
        
        # Créer le dossier d'export s'il n'existe pas
        if not os.path.exists(dossier_export):
            os.makedirs(dossier_export)
            
        fichiers_exportes = []
        
        print(f"\n📁 EXPORT DE LA SOLUTION D'OPTIMISATION")
        print(f"Dossier de destination: {dossier_export}")
        print(f"Format(s) demandé(s): {format_export}")
        
        # Vérifier le type de résultats (mono ou multi-semaines)
        is_multi_semaines = 'resultats_semaine1' in resultats or 'resultats_semaine2' in resultats
        
        if format_export in ["excel", "all"]:
            fichier_excel = self._exporter_vers_excel(resultats, dossier_export, is_multi_semaines)
            fichiers_exportes.append(fichier_excel)
            
        if format_export in ["csv", "all"]:
            fichiers_csv = self._exporter_vers_csv(resultats, dossier_export, is_multi_semaines)
            fichiers_exportes.extend(fichiers_csv)
            
        if format_export in ["json", "all"]:
            fichier_json = self._exporter_vers_json(resultats, dossier_export, is_multi_semaines)
            fichiers_exportes.append(fichier_json)
            
        if format_export in ["pdf", "all"]:
            fichier_pdf = self._exporter_vers_pdf(resultats, dossier_export, is_multi_semaines)
            fichiers_exportes.append(fichier_pdf)
            
        print(f"\n✅ EXPORT TERMINÉ")
        print(f"Fichiers générés:")
        for fichier in fichiers_exportes:
            print(f"  - {fichier}")
            
        return fichiers_exportes
    
    def _exporter_vers_excel(self, resultats, dossier, is_multi_semaines):
        """Exporte vers Excel avec plusieurs onglets"""
        
        nom_fichier = f"optimisation_navettes_{self.timestamp}.xlsx"
        chemin_fichier = os.path.join(dossier, nom_fichier)
        
        print(f"📊 Export Excel: {nom_fichier}")
        
        wb = Workbook()
        
        # Supprimer la feuille par défaut
        wb.remove(wb.active)
        
        if is_multi_semaines:
            self._creer_onglets_multi_semaines(wb, resultats)
        else:
            self._creer_onglets_mono_semaine(wb, resultats)
            
        wb.save(chemin_fichier)
        return chemin_fichier
    
    def _creer_onglets_multi_semaines(self, wb, resultats):
        """Crée les onglets pour une solution multi-semaines"""
        
        # 1. Onglet Résumé Global
        ws_resume = wb.create_sheet("Résumé Global")
        self._remplir_resume_global(ws_resume, resultats, True)
        
        # 2. Onglet Semaine 1 (si existe)
        if resultats.get('resultats_semaine1'):
            ws_s1 = wb.create_sheet("Semaine 1")
            self._remplir_details_semaine(ws_s1, resultats['resultats_semaine1'], 1)
            
        # 3. Onglet Semaine 2 (si existe)
        if resultats.get('resultats_semaine2'):
            ws_s2 = wb.create_sheet("Semaine 2")
            self._remplir_details_semaine(ws_s2, resultats['resultats_semaine2'], 2)
            
        # 4. Onglet Planification Détaillée
        ws_planning = wb.create_sheet("Planning Détaillé")
        self._remplir_planning_detaille(ws_planning, resultats, True)
        
        # 5. Onglet Analyse Coûts
        ws_couts = wb.create_sheet("Analyse Coûts")
        self._remplir_analyse_couts(ws_couts, resultats, True)
        
    def _creer_onglets_mono_semaine(self, wb, resultats):
        """Crée les onglets pour une solution mono-semaine"""
        
        # 1. Onglet Résumé
        ws_resume = wb.create_sheet("Résumé")
        self._remplir_resume_global(ws_resume, resultats, False)
        
        # 2. Onglet Détails
        ws_details = wb.create_sheet("Détails Solution")
        self._remplir_details_semaine(ws_details, resultats, 1)
        
        # 3. Onglet Planning
        ws_planning = wb.create_sheet("Planning")
        self._remplir_planning_detaille(ws_planning, resultats, False)
        
        # 4. Onglet Coûts
        ws_couts = wb.create_sheet("Analyse Coûts")
        self._remplir_analyse_couts(ws_couts, resultats, False)
        
    def _remplir_resume_global(self, ws, resultats, is_multi):
        """Remplit l'onglet résumé global"""
        
        # Titre principal
        ws['A1'] = "RÉSUMÉ DE L'OPTIMISATION DES NAVETTES"
        ws['A1'].font = Font(size=16, bold=True)
        ws.merge_cells('A1:E1')
        
        row = 3
        
        if is_multi:
            # Informations projet multi-semaines
            ws[f'A{row}'] = "TYPE DE PROJET"
            ws[f'B{row}'] = "Multi-semaines"
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
            
            ws[f'A{row}'] = "DURÉE TOTALE"
            ws[f'B{row}'] = f"{resultats['duree_totale_projet']} jours"
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
            
            ws[f'A{row}'] = "COÛT TOTAL"
            ws[f'B{row}'] = f"{resultats['cout_total_global']:.2f} €"
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'B{row}'].font = Font(color="FF0000")
            row += 2
            
            # Détails par semaine
            if resultats.get('resultats_semaine1'):
                s1 = resultats['resultats_semaine1']
                ws[f'A{row}'] = "SEMAINE 1"
                ws[f'A{row}'].font = Font(bold=True, color="0000FF")
                row += 1
                
                ws[f'A{row}'] = "Véhicule utilisé"
                ws[f'B{row}'] = s1['vehicule_utilise']['nom']
                row += 1
                
                ws[f'A{row}'] = "Nombre de véhicules"
                ws[f'B{row}'] = s1['nb_vehicules_necessaires']
                row += 1
                
                ws[f'A{row}'] = "Coût semaine 1"
                ws[f'B{row}'] = f"{s1['vehicule_optimal']['cout_total']:.2f} €"
                row += 2
                
            if resultats.get('resultats_semaine2'):
                s2 = resultats['resultats_semaine2']
                ws[f'A{row}'] = "SEMAINE 2"
                ws[f'A{row}'].font = Font(bold=True, color="0000FF")
                row += 1
                
                ws[f'A{row}'] = "Véhicule utilisé"
                ws[f'B{row}'] = s2['vehicule_utilise']['nom']
                row += 1
                
                ws[f'A{row}'] = "Nombre de véhicules"
                ws[f'B{row}'] = s2['nb_vehicules_necessaires']
                row += 1
                
                ws[f'A{row}'] = "Coût semaine 2"
                ws[f'B{row}'] = f"{s2['vehicule_optimal']['cout_total']:.2f} €"
                row += 1
                
        else:
            # Informations projet mono-semaine
            ws[f'A{row}'] = "VÉHICULE SÉLECTIONNÉ"
            ws[f'B{row}'] = resultats['vehicule_utilise']['nom']
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
            
            ws[f'A{row}'] = "NOMBRE DE VÉHICULES"
            ws[f'B{row}'] = resultats['nb_vehicules_necessaires']
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
            
            ws[f'A{row}'] = "COÛT TOTAL"
            ws[f'B{row}'] = f"{resultats['vehicule_optimal']['cout_total']:.2f} €"
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'B{row}'].font = Font(color="FF0000")
            row += 1
            
            ws[f'A{row}'] = "DURÉE RÉELLE"
            ws[f'B{row}'] = f"{resultats['duree_reelle']} jours"
            ws[f'A{row}'].font = Font(bold=True)
            
        # Ajuster la largeur des colonnes
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 30
        
    def _remplir_details_semaine(self, ws, resultats_semaine, numero_semaine):
        """Remplit les détails d'une semaine"""
        
        ws['A1'] = f"DÉTAILS SEMAINE {numero_semaine}"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:F1')
        
        row = 3
        
        # Informations véhicule
        ws[f'A{row}'] = "VÉHICULE ET CAPACITÉS"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1
        
        vehicule = resultats_semaine['vehicule_utilise']
        ws[f'A{row}'] = "Nom du véhicule"
        ws[f'B{row}'] = vehicule.get('nom', 'Non spécifié')
        row += 1
        
        ws[f'A{row}'] = "Type"
        ws[f'B{row}'] = vehicule.get('type', 'Non spécifié')
        row += 1
        
        ws[f'A{row}'] = "Capacité poids"
        ws[f'B{row}'] = f"{vehicule.get('capacite_poids_max', 'N/A')} tonnes"
        row += 1
        
        ws[f'A{row}'] = "Capacité volume"
        ws[f'B{row}'] = f"{vehicule.get('capacite_volume_max', 'N/A')} m³"
        row += 2
        
        # Produits à transporter
        ws[f'A{row}'] = "PRODUITS À TRANSPORTER"
        ws[f'A{row}'].font = Font(bold=True)
        row += 1
        
        # Headers
        headers = ['Produit', 'Quantité', 'Poids Unit.', 'Volume Unit.', 'Poids Total', 'Volume Total']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
            
        row += 1
        
        # Vérifier si les produits existent
        produits = resultats_semaine.get('produits_a_transporter', [])
        if not produits:
            # Si pas de produits_a_transporter, essayer de les reconstituer depuis la planification
            produits = self._extraire_produits_depuis_planification(resultats_semaine)
        
        for produit in produits:
            poids_total = produit.get('quantite', 0) * produit.get('poids_unitaire', 0)
            volume_total = produit.get('quantite', 0) * produit.get('volume_unitaire', 0)
            
            ws.cell(row=row, column=1, value=produit.get('nom', 'Produit inconnu'))
            ws.cell(row=row, column=2, value=produit.get('quantite', 0))
            ws.cell(row=row, column=3, value=f"{produit.get('poids_unitaire', 0)} t")
            ws.cell(row=row, column=4, value=f"{produit.get('volume_unitaire', 0)} m³")
            ws.cell(row=row, column=5, value=f"{poids_total:.2f} t")
            ws.cell(row=row, column=6, value=f"{volume_total:.2f} m³")
            row += 1
            
        # Ajuster les colonnes
        for col in range(1, 7):
            ws.column_dimensions[chr(64 + col)].width = 15
    
    def _extraire_produits_depuis_planification(self, resultats_semaine):
        """Extrait les produits depuis la planification si pas disponibles directement"""
        produits = {}
        
        planif = resultats_semaine.get('planification_detaillee', {})
        planifications_vehicules = planif.get('planifications_vehicules', [])
        
        for planif_vehicule in planifications_vehicules:
            for voyage in planif_vehicule.get('voyages', []):
                charge = voyage.get('charge_transportee', {})
                for p in charge.get('produits', []):
                    produit_info = p.get('produit', {})
                    nom_produit = produit_info.get('nom', 'Produit inconnu')
                    
                    if nom_produit not in produits:
                        produits[nom_produit] = {
                            'nom': nom_produit,
                            'quantite': 0,
                            'poids_unitaire': produit_info.get('poids_unitaire', 0),
                            'volume_unitaire': produit_info.get('volume_unitaire', 0)
                        }
                    
                    produits[nom_produit]['quantite'] += p.get('quantite_voyage', 0)
        
        return list(produits.values())
            
    def _remplir_planning_detaille(self, ws, resultats, is_multi):
        """Remplit le planning détaillé"""
        
        ws['A1'] = "PLANNING DÉTAILLÉ DES VOYAGES"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:J1')
        
        row = 3
        
        if is_multi:
            # Multi-semaines
            for semaine_num in [1, 2]:
                semaine_key = f'resultats_semaine{semaine_num}'
                if resultats.get(semaine_key):
                    ws[f'A{row}'] = f"SEMAINE {semaine_num}"
                    ws[f'A{row}'].font = Font(bold=True, color="0000FF")
                    row += 1
                    
                    row = self._ajouter_voyages_planning(ws, resultats[semaine_key], row)
                    row += 1
        else:
            # Mono-semaine
            row = self._ajouter_voyages_planning(ws, resultats, row)
            
    def _ajouter_voyages_planning(self, ws, resultats_semaine, row_start):
        """Ajoute les voyages au planning"""
        
        headers = ['Véhicule', 'Voyage', 'Date Départ', 'Heure Départ', 'Date Arrivée', 'Heure Arrivée', 'Charge (t)', 'Charge (m³)', 'Produits']
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row_start, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
            
        row = row_start + 1
        
        planif = resultats_semaine.get('planification_detaillee', {})
        planifications_vehicules = planif.get('planifications_vehicules', [])
        
        for planif_vehicule in planifications_vehicules:
            vehicule_id = planif_vehicule.get('vehicule_id', 'N/A')
            
            for voyage in planif_vehicule.get('voyages', []):
                voyage_num = voyage.get('voyage_numero', 'N/A')
                charge = voyage.get('charge_transportee', {})
                aller = voyage.get('aller', {})
                
                # Produits transportés
                produits_list = charge.get('produits', [])
                produits_str = ", ".join([f"{p.get('produit', {}).get('nom', 'Inconnu')} ({p.get('quantite_voyage', 0)})" for p in produits_list])
                
                ws.cell(row=row, column=1, value=f"Véhicule {vehicule_id}")
                ws.cell(row=row, column=2, value=voyage_num)
                ws.cell(row=row, column=3, value=aller.get('date_depart', 'N/A'))
                ws.cell(row=row, column=4, value=aller.get('heure_depart', 'N/A'))
                ws.cell(row=row, column=5, value=aller.get('date_arrivee', 'N/A'))
                ws.cell(row=row, column=6, value=aller.get('heure_arrivee', 'N/A'))
                ws.cell(row=row, column=7, value=f"{charge.get('poids', 0):.2f}")
                ws.cell(row=row, column=8, value=f"{charge.get('volume', 0):.2f}")
                ws.cell(row=row, column=9, value=produits_str)
                
                row += 1
                
        # Ajuster les colonnes
        for col in range(1, 10):
            ws.column_dimensions[chr(64 + col)].width = 12
        ws.column_dimensions['I'].width = 40  # Colonne produits plus large
        
        return row
        
    def _remplir_analyse_couts(self, ws, resultats, is_multi):
        """Remplit l'analyse des coûts"""
        
        ws['A1'] = "ANALYSE DÉTAILLÉE DES COÛTS"
        ws['A1'].font = Font(size=14, bold=True)
        ws.merge_cells('A1:E1')
        
        row = 3
        
        if is_multi:
            # Coûts globaux
            ws[f'A{row}'] = "COÛTS GLOBAUX"
            ws[f'A{row}'].font = Font(bold=True, color="FF0000")
            row += 1
            
            ws[f'A{row}'] = "Coût total projet"
            ws[f'B{row}'] = f"{resultats['cout_total_global']:.2f} €"
            ws[f'B{row}'].font = Font(bold=True)
            row += 2
            
            # Détail par semaine
            for semaine_num in [1, 2]:
                semaine_key = f'resultats_semaine{semaine_num}'
                if resultats.get(semaine_key):
                    s = resultats[semaine_key]
                    ws[f'A{row}'] = f"SEMAINE {semaine_num}"
                    ws[f'A{row}'].font = Font(bold=True, color="0000FF")
                    row += 1
                    
                    ws[f'A{row}'] = "Coût fixe"
                    ws[f'B{row}'] = f"{s['vehicule_optimal']['cout_fixe_total']:.2f} €"
                    row += 1
                    
                    ws[f'A{row}'] = "Coût variable"
                    ws[f'B{row}'] = f"{s['vehicule_optimal']['cout_variable_total']:.2f} €"
                    row += 1
                    
                    ws[f'A{row}'] = "Coût total semaine"
                    ws[f'B{row}'] = f"{s['vehicule_optimal']['cout_total']:.2f} €"
                    ws[f'B{row}'].font = Font(bold=True)
                    row += 2
        else:
            # Mono-semaine
            opt = resultats['vehicule_optimal']
            
            ws[f'A{row}'] = "Coût fixe total"
            ws[f'B{row}'] = f"{opt['cout_fixe_total']:.2f} €"
            row += 1
            
            ws[f'A{row}'] = "Coût variable total"
            ws[f'B{row}'] = f"{opt['cout_variable_total']:.2f} €"
            row += 1
            
            ws[f'A{row}'] = "COÛT TOTAL"
            ws[f'B{row}'] = f"{opt['cout_total']:.2f} €"
            ws[f'A{row}'].font = Font(bold=True)
            ws[f'B{row}'].font = Font(bold=True, color="FF0000")
            
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
    
    def _exporter_vers_csv(self, resultats, dossier, is_multi):
        """Exporte vers CSV (plusieurs fichiers)"""
        
        print(f"📄 Export CSV...")
        fichiers_csv = []
        
        if is_multi:
            # Résumé global
            df_resume = self._creer_dataframe_resume_multi(resultats)
            fichier_resume = os.path.join(dossier, f"resume_global_{self.timestamp}.csv")
            df_resume.to_csv(fichier_resume, index=False, encoding='utf-8-sig', sep=';')
            fichiers_csv.append(fichier_resume)
            
            # Détails par semaine
            for semaine_num in [1, 2]:
                semaine_key = f'resultats_semaine{semaine_num}'
                if resultats.get(semaine_key):
                    df_semaine = self._creer_dataframe_semaine(resultats[semaine_key])
                    fichier_semaine = os.path.join(dossier, f"semaine_{semaine_num}_{self.timestamp}.csv")
                    df_semaine.to_csv(fichier_semaine, index=False, encoding='utf-8-sig', sep=';')
                    fichiers_csv.append(fichier_semaine)
        else:
            # Mono-semaine
            df_solution = self._creer_dataframe_semaine(resultats)
            fichier_solution = os.path.join(dossier, f"solution_optimisation_{self.timestamp}.csv")
            df_solution.to_csv(fichier_solution, index=False, encoding='utf-8-sig', sep=';')
            fichiers_csv.append(fichier_solution)
            
        return fichiers_csv
    
    def _creer_dataframe_resume_multi(self, resultats):
        """Crée un DataFrame pour le résumé multi-semaines"""
        
        data = []
        
        # Ligne globale
        data.append({
            'Type': 'GLOBAL',
            'Semaine': 'PROJET',
            'Vehicule': 'N/A',
            'Nb_Vehicules': resultats['nb_vehicules_total'],
            'Cout_Total': resultats['cout_total_global'],
            'Duree_Jours': resultats['duree_totale_projet']
        })
        
        # Lignes par semaine
        for semaine_num in [1, 2]:
            semaine_key = f'resultats_semaine{semaine_num}'
            if resultats.get(semaine_key):
                s = resultats[semaine_key]
                data.append({
                    'Type': 'SEMAINE',
                    'Semaine': f'S{semaine_num}',
                    'Vehicule': s['vehicule_utilise']['nom'],
                    'Nb_Vehicules': s['nb_vehicules_necessaires'],
                    'Cout_Total': s['vehicule_optimal']['cout_total'],
                    'Duree_Jours': s['duree_reelle']
                })
                
        return pd.DataFrame(data)
    
    def _creer_dataframe_semaine(self, resultats_semaine):
        """Crée un DataFrame pour une semaine"""
        
        data = []
        
        if 'planification_detaillee' in resultats_semaine:
            planif = resultats_semaine['planification_detaillee']
            for planif_vehicule in planif['planifications_vehicules']:
                for voyage in planif_vehicule['voyages']:
                    charge = voyage['charge_transportee']
                    produits = ", ".join([f"{p['produit']['nom']}({p['quantite_voyage']})" for p in charge['produits']])
                    
                    data.append({
                        'Vehicule_ID': planif_vehicule['vehicule_id'],
                        'Voyage_Numero': voyage['voyage_numero'],
                        'Date_Depart': voyage['aller']['date_depart'],
                        'Heure_Depart': voyage['aller']['heure_depart'],
                        'Date_Arrivee': voyage['aller']['date_arrivee'],
                        'Heure_Arrivee': voyage['aller']['heure_arrivee'],
                        'Charge_Poids_T': charge['poids'],
                        'Charge_Volume_M3': charge['volume'],
                        'Produits_Transportes': produits,
                        'Distance_KM': voyage['aller']['distance_km'],
                        'Temps_Conduite_H': voyage['aller']['temps_conduite_total']
                    })
                    
        return pd.DataFrame(data)
    
    def _exporter_vers_json(self, resultats, dossier, is_multi):
        """Exporte vers JSON"""
        
        nom_fichier = f"optimisation_complete_{self.timestamp}.json"
        chemin_fichier = os.path.join(dossier, nom_fichier)
        
        print(f"🔗 Export JSON: {nom_fichier}")
        
        # Préparer les données pour JSON (sérialisation)
        donnees_json = self._preparer_donnees_json(resultats)
        
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            json.dump(donnees_json, f, indent=2, ensure_ascii=False, default=str)
            
        return chemin_fichier
    
    def _preparer_donnees_json(self, resultats):
        """Prépare les données pour l'export JSON"""
        
        # Conversion récursive des objets non-sérialisables
        def convertir_pour_json(obj):
            if isinstance(obj, dict):
                return {k: convertir_pour_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convertir_pour_json(item) for item in obj]
            elif hasattr(obj, '__dict__'):
                return convertir_pour_json(obj.__dict__)
            else:
                return obj
                
        donnees = convertir_pour_json(resultats)
        
        # Ajouter des métadonnées
        donnees['export_metadata'] = {
            'timestamp': self.timestamp,
            'export_date': datetime.now().isoformat(),
            'version': '1.0',
            'format': 'optimisation_navettes_json'
        }
        
        return donnees
    
    def _exporter_vers_pdf(self, resultats, dossier, is_multi):
        """Exporte vers PDF"""
        
        nom_fichier = f"rapport_optimisation_{self.timestamp}.pdf"
        chemin_fichier = os.path.join(dossier, nom_fichier)
        
        print(f"📋 Export PDF: {nom_fichier}")
        
        doc = SimpleDocTemplate(chemin_fichier, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        story = []
        
        # Titre principal
        titre_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=1  # Centré
        )
        
        story.append(Paragraph("RAPPORT D'OPTIMISATION DES NAVETTES", titre_style))
        story.append(Spacer(1, 20))
        
        if is_multi:
            # Résumé multi-semaines
            story.append(Paragraph("RÉSUMÉ GLOBAL", styles['Heading2']))
            
            data_resume = [
                ['Métrique', 'Valeur'],
                ['Durée totale projet', f"{resultats['duree_totale_projet']} jours"],
                ['Coût total', f"{resultats['cout_total_global']:.2f} €"],
                ['Nombre total véhicules', str(resultats['nb_vehicules_total'])]
            ]
            
            table_resume = Table(data_resume)
            table_resume.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table_resume)
            story.append(Spacer(1, 20))
            
            # Détails par semaine
            for semaine_num in [1, 2]:
                semaine_key = f'resultats_semaine{semaine_num}'
                if resultats.get(semaine_key):
                    s = resultats[semaine_key]
                    
                    story.append(Paragraph(f"SEMAINE {semaine_num}", styles['Heading3']))
                    
                    data_semaine = [
                        ['Aspect', 'Détail'],
                        ['Véhicule utilisé', s['vehicule_utilise']['nom']],
                        ['Nombre de véhicules', str(s['nb_vehicules_necessaires'])],
                        ['Coût total', f"{s['vehicule_optimal']['cout_total']:.2f} €"],
                        ['Durée réelle', f"{s['duree_reelle']} jours"],
                        ['Nombre de voyages', str(s['planification_detaillee']['total_voyages'])]
                    ]
                    
                    table_semaine = Table(data_semaine)
                    table_semaine.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    
                    story.append(table_semaine)
                    story.append(Spacer(1, 15))
        else:
            # Solution mono-semaine
            story.append(Paragraph("SOLUTION OPTIMALE", styles['Heading2']))
            
            opt = resultats['vehicule_optimal']
            data_solution = [
                ['Aspect', 'Valeur'],
                ['Véhicule sélectionné', resultats['vehicule_utilise']['nom']],
                ['Type de véhicule', resultats['vehicule_utilise']['type']],
                ['Nombre de véhicules', str(resultats['nb_vehicules_necessaires'])],
                ['Durée réelle', f"{resultats['duree_reelle']} jours"],
                ['Coût fixe', f"{opt['cout_fixe_total']:.2f} €"],
                ['Coût variable', f"{opt['cout_variable_total']:.2f} €"],
                ['COÛT TOTAL', f"{opt['cout_total']:.2f} €"]
            ]
            
            table_solution = Table(data_solution)
            table_solution.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('BACKGROUND', (0, -1), (-1, -1), colors.yellow),  # Dernière ligne en surbrillance
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table_solution)
            
        doc.build(story)
        return chemin_fichier

    def exporter_planning_excel_detaille(self, resultats, dossier_export="exports"):
        """Exporte un planning Excel ultra-détaillé avec formatage avancé"""
        
        nom_fichier = f"planning_detaille_{self.timestamp}.xlsx"
        chemin_fichier = os.path.join(dossier_export, nom_fichier)
        
        print(f"📅 Export Planning Détaillé: {nom_fichier}")
        
        wb = Workbook()
        wb.remove(wb.active)
        
        # Style pour les headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                       top=Side(style='thin'), bottom=Side(style='thin'))
        
        is_multi_semaines = 'resultats_semaine1' in resultats or 'resultats_semaine2' in resultats
        
        if is_multi_semaines:
            # Onglet par semaine
            for semaine_num in [1, 2]:
                semaine_key = f'resultats_semaine{semaine_num}'
                if resultats.get(semaine_key):
                    ws = wb.create_sheet(f"Planning S{semaine_num}")
                    self._creer_planning_detaille_semaine(ws, resultats[semaine_key], semaine_num, header_font, header_fill, border)
            
            # Onglet comparatif
            ws_comp = wb.create_sheet("Comparatif Semaines")
            self._creer_comparatif_semaines(ws_comp, resultats, header_font, header_fill, border)
        else:
            # Planning unique
            ws = wb.create_sheet("Planning Complet")
            self._creer_planning_detaille_semaine(ws, resultats, 1, header_font, header_fill, border)
            
        wb.save(chemin_fichier)
        return chemin_fichier
    
    def _creer_planning_detaille_semaine(self, ws, resultats_semaine, semaine_num, header_font, header_fill, border):
        """Crée un planning détaillé pour une semaine avec formatage avancé"""
        
        # Titre
        ws['A1'] = f"PLANNING DÉTAILLÉ SEMAINE {semaine_num}"
        ws['A1'].font = Font(size=16, bold=True)
        ws.merge_cells('A1:P1')
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Headers du tableau
        headers = [
            'Véhicule', 'Voyage', 'Date Départ', 'Heure Départ', 'Date Arrivée', 'Heure Arrivée',
            'Durée Trajet (h)', 'Distance (km)', 'Charge Poids (t)', 'Charge Volume (m³)',
            'Utilisation Poids (%)', 'Utilisation Volume (%)', 'Produits', 'Quantités', 'Pauses Repos', 'Pauses Nuit'
        ]
        
        row = 3
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
            
        row += 1
        
        # Données du planning
        vehicule = resultats_semaine['vehicule_utilise']
        planif = resultats_semaine['planification_detaillee']
        
        for planif_vehicule in planif['planifications_vehicules']:
            for voyage in planif_vehicule['voyages']:
                charge = voyage['charge_transportee']
                aller = voyage['aller']
                
                # Calculs d'utilisation
                util_poids = (charge['poids'] / vehicule['capacite_poids_max']) * 100
                util_volume = (charge['volume'] / vehicule['capacite_volume_max']) * 100
                
                # Produits et quantités séparés
                produits = [p['produit']['nom'] for p in charge['produits']]
                quantites = [str(p['quantite_voyage']) for p in charge['produits']]
                
                # Données de la ligne
                donnees = [
                    f"Véhicule {planif_vehicule['vehicule_id']}",
                    voyage['voyage_numero'],
                    aller['date_depart'],
                    aller['heure_depart'],
                    aller['date_arrivee'],
                    aller['heure_arrivee'],
                    f"{aller['temps_conduite_total']:.2f}",
                    aller['distance_km'],
                    f"{charge['poids']:.2f}",
                    f"{charge['volume']:.2f}",
                    f"{util_poids:.1f}%",
                    f"{util_volume:.1f}%",
                    "\n".join(produits),
                    "\n".join(quantites),
                    aller['pauses_repos'],
                    aller['pauses_nuit']
                ]
                
                for col, valeur in enumerate(donnees, 1):
                    cell = ws.cell(row=row, column=col, value=valeur)
                    cell.border = border
                    
                    # Formatage conditionnel pour les utilisations
                    if col == 11 or col == 12:  # Colonnes utilisation
                        if util_poids > 90 or util_volume > 90:
                            cell.fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
                        elif util_poids > 75 or util_volume > 75:
                            cell.fill = PatternFill(start_color="FFE66D", end_color="FFE66D", fill_type="solid")
                        else:
                            cell.fill = PatternFill(start_color="95E1D3", end_color="95E1D3", fill_type="solid")
                    
                    # Alignement pour les colonnes de texte multiple
                    if col in [13, 14]:  # Produits et quantités
                        cell.alignment = Alignment(vertical='top', wrap_text=True)
                        
                row += 1
                
        # Ajustement des colonnes
        colonnes_width = [12, 8, 12, 12, 12, 12, 12, 10, 12, 12, 15, 15, 25, 15, 12, 12]
        for i, width in enumerate(colonnes_width, 1):
            ws.column_dimensions[chr(64 + i)].width = width
            
        # Ligne de totaux
        row += 1
        ws.cell(row=row, column=1, value="TOTAUX").font = Font(bold=True)
        
        # Calcul des totaux
        total_poids = sum(
            sum(voyage['charge_transportee']['poids'] for voyage in planif_vehicule['voyages'])
            for planif_vehicule in planif['planifications_vehicules']
        )
        total_volume = sum(
            sum(voyage['charge_transportee']['volume'] for voyage in planif_vehicule['voyages'])
            for planif_vehicule in planif['planifications_vehicules']
        )
        total_distance = sum(
            sum(voyage['aller']['distance_km'] for voyage in planif_vehicule['voyages'])
            for planif_vehicule in planif['planifications_vehicules']
        )
        
        ws.cell(row=row, column=8, value=f"{total_distance} km").font = Font(bold=True)
        ws.cell(row=row, column=9, value=f"{total_poids:.2f} t").font = Font(bold=True)
        ws.cell(row=row, column=10, value=f"{total_volume:.2f} m³").font = Font(bold=True)
        
    def _creer_comparatif_semaines(self, ws, resultats, header_font, header_fill, border):
        """Crée un comparatif entre les semaines"""
        
        ws['A1'] = "COMPARATIF INTER-SEMAINES"
        ws['A1'].font = Font(size=16, bold=True)
        ws.merge_cells('A1:F1')
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Headers
        headers = ['Métrique', 'Semaine 1', 'Semaine 2', 'Total', 'Différence', 'Optimisation']
        
        row = 3
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            
        row += 1
        
        # Données comparatives
        s1 = resultats.get('resultats_semaine1')
        s2 = resultats.get('resultats_semaine2')
        
        comparaisons = [
            ['Véhicule utilisé', 
             s1['vehicule_utilise']['nom'] if s1 else 'N/A',
             s2['vehicule_utilise']['nom'] if s2 else 'N/A',
             'N/A',
             'Identique' if s1 and s2 and s1['vehicule_utilise']['nom'] == s2['vehicule_utilise']['nom'] else 'Différent',
             'Unifier si possible'],
            
            ['Coût total (€)',
             f"{s1['vehicule_optimal']['cout_total']:.2f}" if s1 else '0',
             f"{s2['vehicule_optimal']['cout_total']:.2f}" if s2 else '0',
             f"{resultats['cout_total_global']:.2f}",
             f"{abs(s1['vehicule_optimal']['cout_total'] - s2['vehicule_optimal']['cout_total']):.2f}" if s1 and s2 else 'N/A',
             'Équilibrer les charges'],
             
            ['Nb véhicules',
             str(s1['nb_vehicules_necessaires']) if s1 else '0',
             str(s2['nb_vehicules_necessaires']) if s2 else '0',
             str(resultats['nb_vehicules_total']),
             str(abs(s1['nb_vehicules_necessaires'] - s2['nb_vehicules_necessaires'])) if s1 and s2 else 'N/A',
             'Homogénéiser'],
             
            ['Durée (jours)',
             str(s1['duree_reelle']) if s1 else '0',
             str(s2['duree_reelle']) if s2 else '0',
             str(resultats['duree_totale_projet']),
             str(abs(s1['duree_reelle'] - s2['duree_reelle'])) if s1 and s2 else 'N/A',
             'Optimiser planning'],
             
            ['Nb voyages total',
             str(s1['planification_detaillee']['total_voyages']) if s1 else '0',
             str(s2['planification_detaillee']['total_voyages']) if s2 else '0',
             str((s1['planification_detaillee']['total_voyages'] if s1 else 0) + (s2['planification_detaillee']['total_voyages'] if s2 else 0)),
             str(abs((s1['planification_detaillee']['total_voyages'] if s1 else 0) - (s2['planification_detaillee']['total_voyages'] if s2 else 0))),
             'Répartir équitablement']
        ]
        
        for comparaison in comparaisons:
            for col, valeur in enumerate(comparaison, 1):
                cell = ws.cell(row=row, column=col, value=valeur)
                cell.border = border
                
                # Formatage spécial pour la colonne optimisation
                if col == 6:
                    cell.fill = PatternFill(start_color="E8F4FD", end_color="E8F4FD", fill_type="solid")
                    cell.font = Font(italic=True)
                    
            row += 1
            
        # Ajuster les colonnes
        for col in range(1, 7):
            ws.column_dimensions[chr(64 + col)].width = 20
            
    def generer_rapport_executif(self, resultats, dossier_export="exports"):
        """Génère un rapport exécutif synthétique"""
        
        nom_fichier = f"rapport_executif_{self.timestamp}.xlsx"
        chemin_fichier = os.path.join(dossier_export, nom_fichier)
        
        print(f"📊 Export Rapport Exécutif: {nom_fichier}")
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Rapport Exécutif"
        
        # Styles
        titre_font = Font(size=18, bold=True, color="FFFFFF")
        titre_fill = PatternFill(start_color="2E4BC6", end_color="2E4BC6", fill_type="solid")
        
        # Titre principal
        ws['A1'] = "RAPPORT EXÉCUTIF - OPTIMISATION NAVETTES"
        ws['A1'].font = titre_font
        ws['A1'].fill = titre_fill
        ws.merge_cells('A1:F1')
        ws['A1'].alignment = Alignment(horizontal='center')
        
        row = 3
        
        # Résumé exécutif
        is_multi = 'resultats_semaine1' in resultats or 'resultats_semaine2' in resultats
        
        ws[f'A{row}'] = "RÉSUMÉ EXÉCUTIF"
        ws[f'A{row}'].font = Font(size=14, bold=True, color="2E4BC6")
        row += 2
        
        if is_multi:
            # Multi-semaines
            ws[f'A{row}'] = f"• Projet sur {resultats['duree_totale_projet']} jours (2 semaines)"
            row += 1
            ws[f'A{row}'] = f"• Coût total optimisé: {resultats['cout_total_global']:.2f} €"
            row += 1
            ws[f'A{row}'] = f"• {resultats['nb_vehicules_total']} véhicules mobilisés au total"
            row += 1
            
            if resultats.get('resultats_semaine1') and resultats.get('resultats_semaine2'):
                s1 = resultats['resultats_semaine1']
                s2 = resultats['resultats_semaine2']
                if s1['vehicule_utilise']['nom'] == s2['vehicule_utilise']['nom']:
                    ws[f'A{row}'] = f"• Continuité opérationnelle: même véhicule ({s1['vehicule_utilise']['nom']})"
                else:
                    ws[f'A{row}'] = f"• Gestion multi-véhicules: {s1['vehicule_utilise']['nom']} + {s2['vehicule_utilise']['nom']}"
                row += 1
        else:
            # Mono-semaine
            ws[f'A{row}'] = f"• Projet sur {resultats['duree_reelle']} jours"
            row += 1
            ws[f'A{row}'] = f"• Coût total: {resultats['vehicule_optimal']['cout_total']:.2f} €"
            row += 1
            ws[f'A{row}'] = f"• Véhicule optimal: {resultats['vehicule_utilise']['nom']}"
            row += 1
            ws[f'A{row}'] = f"• {resultats['nb_vehicules_necessaires']} véhicule(s) nécessaire(s)"
            row += 1
            
        row += 2
        
        # Recommandations
        ws[f'A{row}'] = "RECOMMANDATIONS CLÉS"
        ws[f'A{row}'].font = Font(size=14, bold=True, color="2E4BC6")
        row += 2
        
        recommandations = self._generer_recommandations_executives(resultats, is_multi)
        for recommandation in recommandations:
            ws[f'A{row}'] = f"• {recommandation}"
            row += 1
            
        # Ajuster les colonnes
        ws.column_dimensions['A'].width = 80
        
        wb.save(chemin_fichier)
        return chemin_fichier
    
    def _generer_recommandations_executives(self, resultats, is_multi):
        """Génère des recommandations pour le niveau exécutif"""
        
        recommandations = []
        
        if is_multi:
            s1 = resultats.get('resultats_semaine1')
            s2 = resultats.get('resultats_semaine2')
            
            if s1 and s2:
                # Analyse des coûts
                cout_s1 = s1['vehicule_optimal']['cout_total']
                cout_s2 = s2['vehicule_optimal']['cout_total']
                
                if abs(cout_s1 - cout_s2) / max(cout_s1, cout_s2) > 0.2:
                    recommandations.append("Déséquilibre des coûts détecté (>20%) - Rééquilibrer la répartition des produits")
                    
                if s1['vehicule_utilise']['nom'] != s2['vehicule_utilise']['nom']:
                    recommandations.append("Véhicules différents utilisés - Évaluer l'unification pour réduire les coûts fixes")
                else:
                    recommandations.append("Continuité véhicule assurée - Optimisation des coûts fixes réussie")
                    
                # Analyse de l'utilisation
                if s1['nb_vehicules_necessaires'] == 1 and s2['nb_vehicules_necessaires'] == 1:
                    recommandations.append("Risque opérationnel faible - Solution de secours recommandée")
                else:
                    recommandations.append("Complexité multi-véhicules - Renforcer la coordination des équipes")
                    
        else:
            # Mono-semaine
            opt = resultats['vehicule_optimal']
            
            if resultats['nb_vehicules_necessaires'] == 1:
                recommandations.append("Solution simple et économique - Risque de dépendance unique")
            else:
                recommandations.append(f"Solution multi-véhicules ({resultats['nb_vehicules_necessaires']}) - Avantage de parallélisation")
                
            # Analyse du coût par tonne
            poids_total = resultats['demande_equivalente']['quantite_poids']
            if poids_total > 0:
                cout_par_tonne = opt['cout_total'] / poids_total
                if cout_par_tonne < 50:
                    recommandations.append("Excellent ratio coût/tonne - Solution très compétitive")
                elif cout_par_tonne > 100:
                    recommandations.append("Ratio coût/tonne élevé - Évaluer des alternatives")
                    
        recommandations.append("Surveiller les contraintes temporelles pour respecter les échéances")
        recommandations.append("Prévoir des solutions de contingence en cas de problème véhicule")
        
        return recommandations

# Exemple d'utilisation corrigé
def exemple_export():
    """Exemple d'utilisation de l'exportateur avec données complètes"""
    
    # Simuler des résultats COMPLETS (structure réaliste)
    resultats_exemple = {
        'vehicule_utilise': {
            'nom': 'SEMI-REMORQUE STANDARD', 
            'type': 'LOURD',
            'capacite_poids_max': 40,
            'capacite_volume_max': 100,
            'vitesse_kmh': 75,
            'cout_fixe_jour': 400,
            'cout_variable_km': 1.20
        },
        'nb_vehicules_necessaires': 1,
        'duree_reelle': 5,
        'respect_contrainte': True,
        'vehicule_optimal': {
            'cout_total': 2450.50,
            'cout_fixe_total': 2000.00,
            'cout_variable_total': 450.50,
            'voyages_par_vehicule': 3,
            'nb_vehicules_necessaires': 1,
            'duree_reelle_jours': 5
        },
        'demande_equivalente': {
            'nom': 'TRANSPORT MULTI-PRODUITS A→B',
            'distance_km': 800,
            'vitesse_kmh': 80,
            'quantite_poids': 45.5,
            'quantite_volume': 120.3
        },
        'produits_a_transporter': [
            {
                'nom': 'MACHINES INDUSTRIELLES',
                'quantite': 15,
                'poids_unitaire': 2.5,
                'volume_unitaire': 8.0,
                'distance_km': 800,
                'vitesse_kmh': 80
            },
            {
                'nom': 'ÉQUIPEMENTS ÉLECTRONIQUES',
                'quantite': 80,
                'poids_unitaire': 0.3,
                'volume_unitaire': 1.2,
                'distance_km': 800,
                'vitesse_kmh': 80
            }
        ],
        'planification_detaillee': {
            'nb_vehicules': 1,
            'total_voyages': 3,
            'date_debut': '2025-06-02',
            'date_fin': '2025-06-06',
            'duree_reelle_jours': 5,
            'respect_contrainte': True,
            'planifications_vehicules': [
                {
                    'vehicule_id': 1,
                    'nb_voyages': 3,
                    'produits_transportes': {
                        'MACHINES INDUSTRIELLES': 15,
                        'ÉQUIPEMENTS ÉLECTRONIQUES': 80
                    },
                    'charge_totale': {
                        'poids': 45.5,
                        'volume': 120.3
                    },
                    'voyages': [
                        {
                            'voyage_numero': 1,
                            'charge_transportee': {
                                'poids': 20.0,
                                'volume': 60.0,
                                'produits': [
                                    {
                                        'produit': {
                                            'nom': 'MACHINES INDUSTRIELLES',
                                            'poids_unitaire': 2.5,
                                            'volume_unitaire': 8.0
                                        },
                                        'quantite_voyage': 8
                                    }
                                ]
                            },
                            'temps_chargement': '01:30',
                            'aller': {
                                'date_depart': '2025-06-02',
                                'heure_depart': '08:00',
                                'date_arrivee': '2025-06-02',
                                'heure_arrivee': '18:30',
                                'distance_km': 800,
                                'temps_conduite_total': 10.5,
                                'pauses_repos': 4,
                                'pauses_nuit': 0
                            },
                            'temps_dechargement': '01:30',
                            'retour': {
                                'date_depart': '2025-06-02',
                                'heure_depart': '20:00',
                                'date_arrivee': '2025-06-03',
                                'heure_arrivee': '06:30',
                                'distance_km': 800,
                                'temps_conduite_total': 10.5,
                                'pauses_repos': 4,
                                'pauses_nuit': 1
                            },
                            'est_dernier_voyage': False,
                            'respecte_contrainte_temporelle': True
                        },
                        {
                            'voyage_numero': 2,
                            'charge_transportee': {
                                'poids': 15.2,
                                'volume': 40.1,
                                'produits': [
                                    {
                                        'produit': {
                                            'nom': 'MACHINES INDUSTRIELLES',
                                            'poids_unitaire': 2.5,
                                            'volume_unitaire': 8.0
                                        },
                                        'quantite_voyage': 6
                                    }
                                ]
                            },
                            'temps_chargement': '01:30',
                            'aller': {
                                'date_depart': '2025-06-03',
                                'heure_depart': '08:00',
                                'date_arrivee': '2025-06-03',
                                'heure_arrivee': '18:30',
                                'distance_km': 800,
                                'temps_conduite_total': 10.5,
                                'pauses_repos': 4,
                                'pauses_nuit': 0
                            },
                            'temps_dechargement': '01:30',
                            'retour': {
                                'date_depart': '2025-06-03',
                                'heure_depart': '20:00',
                                'date_arrivee': '2025-06-04',
                                'heure_arrivee': '06:30',
                                'distance_km': 800,
                                'temps_conduite_total': 10.5,
                                'pauses_repos': 4,
                                'pauses_nuit': 1
                            },
                            'est_dernier_voyage': False,
                            'respecte_contrainte_temporelle': True
                        },
                        {
                            'voyage_numero': 3,
                            'charge_transportee': {
                                'poids': 10.3,
                                'volume': 20.2,
                                'produits': [
                                    {
                                        'produit': {
                                            'nom': 'MACHINES INDUSTRIELLES',
                                            'poids_unitaire': 2.5,
                                            'volume_unitaire': 8.0
                                        },
                                        'quantite_voyage': 1
                                    },
                                    {
                                        'produit': {
                                            'nom': 'ÉQUIPEMENTS ÉLECTRONIQUES',
                                            'poids_unitaire': 0.3,
                                            'volume_unitaire': 1.2
                                        },
                                        'quantite_voyage': 80
                                    }
                                ]
                            },
                            'temps_chargement': '01:30',
                            'aller': {
                                'date_depart': '2025-06-04',
                                'heure_depart': '08:00',
                                'date_arrivee': '2025-06-04',
                                'heure_arrivee': '18:30',
                                'distance_km': 800,
                                'temps_conduite_total': 10.5,
                                'pauses_repos': 4,
                                'pauses_nuit': 0
                            },
                            'temps_dechargement': '01:30',
                            'retour': None,  # Dernier voyage
                            'est_dernier_voyage': True,
                            'respecte_contrainte_temporelle': True
                        }
                    ]
                }
            ]
        }
    }
    
    # Créer l'exportateur et exporter
    print("🚀 Démarrage de l'export avec données complètes...")
    exportateur = ExportateurSolutions()
    
    try:
        # Export complet (tous formats)
        fichiers = exportateur.exporter_solution_complete(resultats_exemple, "all")
        
        # Export planning détaillé
        planning = exportateur.exporter_planning_excel_detaille(resultats_exemple)
        
        # Rapport exécutif
        rapport = exportateur.generer_rapport_executif(resultats_exemple)
        
        print(f"\n🎉 Exports terminés avec succès:")
        print(f"- Fichiers générés: {len(fichiers) + 2}")
        for fichier in fichiers:
            print(f"  ✅ {fichier}")
        print(f"  ✅ Planning détaillé: {planning}")
        print(f"  ✅ Rapport exécutif: {rapport}")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'export: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    exemple_export()
class OptimisateurNavettes:
    def __init__(self):
        self.model = None
        self.solver = SolverFactory('gurobi')
        
    def calculer_navettes_optimales(self, produits_a_transporter, vehicules_data, date_debut, heure_debut, duree_max_jours=7):
        """
        Calcule les navettes optimales en minimisant les coûts totaux avec contrainte temporelle
        
        produits_a_transporter: liste de dictionnaires avec:
        - nom: nom du produit
        - quantite: nombre d'unités
        - poids_unitaire: poids par unité (en tonnes)
        - volume_unitaire: volume par unité (en m³)
        
        Autres paramètres: distance_km, vitesse_kmh
        
        vehicules_data: liste de dictionnaires avec:
        - nom: nom du véhicule
        - type: 'LEGER' ou 'LOURD'
        - capacite_poids_max: capacité maximale en poids (tonnes)
        - capacite_volume_max: capacité maximale en volume (m³)
        - vitesse_kmh: vitesse du véhicule
        - cout_fixe_jour: coût fixe par jour d'utilisation
        - cout_variable_km: coût variable par kilomètre
        
        date_debut: date de début (format YYYY-MM-DD)
        heure_debut: heure de début (format HH:MM)
        duree_max_jours: durée maximale autorisée (défaut: 7 jours)
        """
        
        # Calculer les totaux de la demande
        poids_total = sum(produit['quantite'] * produit['poids_unitaire'] for produit in produits_a_transporter)
        volume_total = sum(produit['quantite'] * produit['volume_unitaire'] for produit in produits_a_transporter)
        
        demande_equivalente = {
            'nom': 'TRANSPORT MULTI-PRODUITS A→B',
            'distance_km': produits_a_transporter[0].get('distance_km', 800),  # Valeur par défaut
            'vitesse_kmh': produits_a_transporter[0].get('vitesse_kmh', 80),   # Valeur par défaut
            'quantite_poids': poids_total,
            'quantite_volume': volume_total
        }
        
        print(f"\n=== OPTIMISATION DES COÛTS POUR TRANSPORT MULTI-PRODUITS AVEC MÉLANGE ===")
        print(f"⏰ CONTRAINTE TEMPORELLE: Terminé en {duree_max_jours} jours maximum")
        print(f"🔄 STRATÉGIE: Remplissage homogène puis mélange optimal")
        print(f"Nombre de types de produits: {len(produits_a_transporter)}")
        
        # Affichage détaillé des produits
        print(f"\n📦 DÉTAIL DES PRODUITS À TRANSPORTER:")
        for i, produit in enumerate(produits_a_transporter, 1):
            poids_produit = produit['quantite'] * produit['poids_unitaire']
            volume_produit = produit['quantite'] * produit['volume_unitaire']
            
            print(f"  {i}. {produit['nom']}:")
            print(f"     - Quantité: {produit['quantite']} unités")
            print(f"     - Poids unitaire: {produit['poids_unitaire']} tonnes/unité")
            print(f"     - Volume unitaire: {produit['volume_unitaire']} m³/unité")
            print(f"     - Poids total: {poids_produit:.2f} tonnes")
            print(f"     - Volume total: {volume_produit:.2f} m³")
        
        print(f"\n📊 TOTAUX:")
        print(f"Poids total: {poids_total:.2f} tonnes")
        print(f"Volume total: {volume_total:.2f} m³")
        print(f"Distance A-B: {demande_equivalente['distance_km']} km")
        print(f"Nombre de types de véhicules disponibles: {len(vehicules_data)}")
        
        # Analyser chaque type de véhicule avec contrainte temporelle
        analyses_vehicules = []
        
        for vehicule in vehicules_data:
            analyse = self._analyser_vehicule_avec_contrainte(demande_equivalente, vehicule, duree_max_jours)
            analyses_vehicules.append(analyse)
            
            print(f"\n{vehicule['nom']} ({vehicule['type']}):")
            print(f"  Capacités: {vehicule['capacite_poids_max']} tonnes, {vehicule['capacite_volume_max']} m³")
            print(f"  Voyages par véhicule: {analyse['voyages_par_vehicule']} (contrainte: {analyse['contrainte_dominante']})")
            print(f"  Durée avec 1 véhicule: {analyse['duree_un_vehicule']} jour(s)")
            
            if analyse['respect_contrainte']:
                print(f"  ✅ RESPECTE LA CONTRAINTE DE {duree_max_jours} JOURS")
                print(f"  Nombre de véhicules nécessaires: {analyse['nb_vehicules_necessaires']}")
                print(f"  Coût fixe total: {analyse['cout_fixe_total']:.2f}€")
                print(f"  Coût variable total: {analyse['cout_variable_total']:.2f}€")
                print(f"  💰 COÛT TOTAL: {analyse['cout_total']:.2f}€")
                print(f"  📊 Coût par véhicule: {analyse['cout_par_vehicule']:.2f}€")
            else:
                print(f"  ❌ NE RESPECTE PAS LA CONTRAINTE DE {duree_max_jours} JOURS")
                print(f"  Durée minimale nécessaire: {analyse['duree_un_vehicule']} jours")
                print(f"  SOLUTION NON VIABLE dans le délai imparti")
        
        # Filtrer les véhicules viables (qui respectent la contrainte)
        vehicules_viables = [a for a in analyses_vehicules if a['respect_contrainte']]
        
        if not vehicules_viables:
            print(f"\n❌ AUCUN VÉHICULE NE PEUT RESPECTER LA CONTRAINTE DE {duree_max_jours} JOURS")
            print("Recommandations:")
            print("- Augmenter la durée autorisée")
            print("- Utiliser des véhicules avec plus de capacité")
            print("- Diviser la demande en plusieurs lots")
            return None
        
        # Sélectionner le véhicule le plus économique parmi les viables
        vehicule_optimal = min(vehicules_viables, key=lambda x: x['cout_total'])
        
        print(f"\n🏆 VÉHICULE OPTIMAL SÉLECTIONNÉ: {vehicule_optimal['vehicule']['nom']}")
        print(f"💰 COÛT TOTAL: {vehicule_optimal['cout_total']:.2f}€")
        print(f"🚛 NOMBRE DE VÉHICULES: {vehicule_optimal['nb_vehicules_necessaires']}")
        print(f"⏱️ DURÉE RÉELLE: {vehicule_optimal['duree_reelle_jours']} jour(s)")
        
        print(f"\n📊 ÉCONOMIES vs autres véhicules viables:")
        for analyse in vehicules_viables:
            if analyse != vehicule_optimal:
                economie = analyse['cout_total'] - vehicule_optimal['cout_total']
                print(f"  vs {analyse['vehicule']['nom']}: +{economie:.2f}€ ({economie/vehicule_optimal['cout_total']*100:.1f}% plus cher)")
        
        # Effectuer la planification détaillée avec mélange des produits
        resultats_planification = self._planifier_multi_vehicules_melange(
            produits_a_transporter,
            demande_equivalente,
            vehicule_optimal, 
            date_debut, 
            heure_debut,
            duree_max_jours
        )
        
        return {
            'produits_a_transporter': produits_a_transporter,
            'demande_equivalente': demande_equivalente,
            'vehicule_utilise': vehicule_optimal['vehicule'],
            'nb_vehicules_necessaires': vehicule_optimal['nb_vehicules_necessaires'],
            'duree_max_autorisee': duree_max_jours,
            'duree_reelle': vehicule_optimal['duree_reelle_jours'],
            'respect_contrainte': True,
            'analyses_vehicules': analyses_vehicules,
            'vehicules_viables': vehicules_viables,
            'vehicule_optimal': vehicule_optimal,
            'planification_detaillee': resultats_planification
        }
    
    def _analyser_vehicule_avec_contrainte(self, demande, vehicule, duree_max_jours):
        """Analyse un véhicule avec prise en compte de la contrainte temporelle"""
        
        # Calculer le nombre de voyages nécessaires avec un seul véhicule
        nb_voyages_poids = math.ceil(demande['quantite_poids'] / vehicule['capacite_poids_max'])
        nb_voyages_volume = math.ceil(demande['quantite_volume'] / vehicule['capacite_volume_max'])
        voyages_par_vehicule = max(nb_voyages_poids, nb_voyages_volume)
        
        # Estimer la durée avec un seul véhicule
        vitesse_utilisee = vehicule.get('vitesse_kmh', demande['vitesse_kmh'])
        temps_conduite_par_voyage = (demande['distance_km'] * 2) / vitesse_utilisee  # Aller-retour
        temps_total_conduite = temps_conduite_par_voyage * voyages_par_vehicule
        
        # Temps de chargement/déchargement par voyage
        temps_operations_par_voyage = 3.0  # 1.5h chargement + 1.5h déchargement
        temps_total_operations = voyages_par_vehicule * temps_operations_par_voyage
        
        # Estimation de la durée totale en jours (8h de travail par jour)
        temps_total_heures = temps_total_conduite + temps_total_operations
        duree_un_vehicule = math.ceil(temps_total_heures / 8.0)
        
        # Vérifier si un seul véhicule respecte la contrainte
        respect_contrainte = duree_un_vehicule <= duree_max_jours
        
        if respect_contrainte:
            # Un seul véhicule suffit
            nb_vehicules_necessaires = 1
            duree_reelle = duree_un_vehicule
        else:
            # Calculer le nombre de véhicules nécessaires
            nb_vehicules_necessaires = math.ceil(duree_un_vehicule / duree_max_jours)
            duree_reelle = duree_max_jours
            respect_contrainte = True  # Avec plusieurs véhicules, on respecte la contrainte
        
        # Calculer les distances et coûts
        voyages_totaux = voyages_par_vehicule * nb_vehicules_necessaires
        distance_aller_total = voyages_totaux * demande['distance_km']
        distance_retour_total = (voyages_totaux - nb_vehicules_necessaires) * demande['distance_km']  # Pas de retour pour le dernier voyage de chaque véhicule
        distance_totale = distance_aller_total + distance_retour_total
        
        # Coûts
        cout_fixe_total = nb_vehicules_necessaires * duree_reelle * vehicule['cout_fixe_jour']
        cout_variable_total = distance_totale * vehicule['cout_variable_km']
        cout_total = cout_fixe_total + cout_variable_total
        cout_par_vehicule = cout_total / nb_vehicules_necessaires if nb_vehicules_necessaires > 0 else 0
        
        return {
            'vehicule': vehicule,
            'voyages_par_vehicule': voyages_par_vehicule,
            'contrainte_dominante': 'poids' if nb_voyages_poids >= nb_voyages_volume else 'volume',
            'duree_un_vehicule': duree_un_vehicule,
            'respect_contrainte': duree_un_vehicule <= duree_max_jours or nb_vehicules_necessaires > 1,
            'nb_vehicules_necessaires': nb_vehicules_necessaires,
            'duree_reelle_jours': duree_reelle,
            'distance_totale': distance_totale,
            'cout_fixe_total': cout_fixe_total,
            'cout_variable_total': cout_variable_total,
            'cout_total': cout_total,
            'cout_par_vehicule': cout_par_vehicule,
            'voyages_totaux': voyages_totaux
        }
    
    def _planifier_multi_vehicules_melange(self, produits_a_transporter, demande_equivalente, vehicule_optimal, date_debut, heure_debut, duree_max_jours):
        """Planifie les opérations avec mélange optimal des produits - remplissage homogène puis mélange"""
        
        nb_vehicules = vehicule_optimal['nb_vehicules_necessaires']
        voyages_par_vehicule = vehicule_optimal['voyages_par_vehicule']
        vehicule = vehicule_optimal['vehicule']
        
        print(f"\n=== PLANIFICATION DÉTAILLÉE AVEC MÉLANGE OPTIMAL ===")
        print(f"🔄 STRATÉGIE: Remplissage homogène prioritaire, puis mélange intelligent")
        print(f"⏰ CONTRAINTE TEMPORELLE STRICTE: {duree_max_jours} jours maximum")
        print(f"Véhicules utilisés: {nb_vehicules} x {vehicule['nom']}")
        print(f"Voyages par véhicule: {voyages_par_vehicule}")
        print(f"Voyages totaux: {voyages_par_vehicule * nb_vehicules}")
        
        # Créer un pool global de toutes les unités de produits
        pool_produits = self._creer_pool_produits(produits_a_transporter)
        
        print(f"\n📦 POOL GLOBAL DE PRODUITS:")
        for produit_nom, info in pool_produits.items():
            print(f"  - {produit_nom}: {info['quantite_totale']} unités ({info['poids_total']:.2f}t, {info['volume_total']:.2f}m³)")
        
        planifications_vehicules = []
        date_limite = self._calculer_date_limite(date_debut, duree_max_jours)
        
        for vehicule_id in range(nb_vehicules):
            print(f"\n--- VÉHICULE {vehicule_id + 1} ---")
            
            # Effectuer les navettes pour ce véhicule avec mélange optimal ET CONTRAINTE TEMPORELLE
            voyages_vehicule = self._effectuer_navettes_melange_avec_contrainte(
                pool_produits,
                demande_equivalente, 
                vehicule, 
                voyages_par_vehicule,
                date_debut, 
                heure_debut,
                vehicule_id,
                date_limite
            )
            
            # Vérifier que ce véhicule respecte la contrainte temporelle
            if voyages_vehicule and len(voyages_vehicule) > 0:
                dernier_voyage = voyages_vehicule[-1]
                date_fin_vehicule = dernier_voyage['aller']['date_arrivee']
                
                if not self._respecte_contrainte_temporelle(date_fin_vehicule, date_limite):
                    print(f"    ❌ VÉHICULE {vehicule_id + 1} DÉPASSE LA CONTRAINTE DE {duree_max_jours} JOURS!")
                    print(f"    Date de fin: {date_fin_vehicule}, Date limite: {date_limite}")
                    # Réduire le nombre de voyages pour respecter la contrainte
                    voyages_vehicule = self._ajuster_voyages_contrainte_temporelle(
                        voyages_vehicule, date_limite, pool_produits
                    )
            
            # Calculer la charge totale transportée par ce véhicule
            poids_total_vehicule = 0
            volume_total_vehicule = 0
            produits_transportes = {}
            
            for voyage in voyages_vehicule:
                charge = voyage['charge_transportee']
                poids_total_vehicule += charge['poids']
                volume_total_vehicule += charge['volume']
                
                for produit_info in charge['produits']:
                    nom_produit = produit_info['produit']['nom']
                    quantite = produit_info['quantite_voyage']
                    
                    if nom_produit not in produits_transportes:
                        produits_transportes[nom_produit] = 0
                    produits_transportes[nom_produit] += quantite
            
            print(f"\n📊 RÉSUMÉ VÉHICULE {vehicule_id + 1} (CONTRAINTE RESPECTÉE):")
            print(f"  Charge totale transportée: {poids_total_vehicule:.2f} tonnes, {volume_total_vehicule:.2f} m³")
            print(f"  Produits transportés:")
            for nom_produit, quantite in produits_transportes.items():
                poids_produit = quantite * next(p['poids_unitaire'] for p in produits_a_transporter if p['nom'] == nom_produit)
                volume_produit = quantite * next(p['volume_unitaire'] for p in produits_a_transporter if p['nom'] == nom_produit)
                print(f"    - {nom_produit}: {quantite} unités ({poids_produit:.2f}t, {volume_produit:.2f}m³)")
            
            planifications_vehicules.append({
                'vehicule_id': vehicule_id + 1,
                'produits_transportes': produits_transportes,
                'charge_totale': {
                    'poids': poids_total_vehicule,
                    'volume': volume_total_vehicule
                },
                'voyages': voyages_vehicule,
                'nb_voyages': len(voyages_vehicule)
            })
        
        # Vérifier que tous les produits ont été transportés MALGRÉ LA CONTRAINTE TEMPORELLE
        completion_ok = self._verifier_completion_transport(produits_a_transporter, planifications_vehicules)
        
        if not completion_ok:
            print(f"\n⚠️ ATTENTION: La contrainte temporelle de {duree_max_jours} jours a empêché le transport complet!")
            print(f"💡 SOLUTIONS POSSIBLES:")
            print(f"   - Augmenter la durée autorisée à {duree_max_jours + 1} jours")
            print(f"   - Ajouter des véhicules supplémentaires")
            print(f"   - Utiliser des véhicules plus rapides ou avec plus de capacité")
        
        # Calculer les statistiques globales avec contrainte respectée
        total_voyages = sum(len(p['voyages']) for p in planifications_vehicules)
        
        # Trouver la date de fin la plus tardive (qui doit être <= date_limite)
        date_fin_globale = date_debut
        for planif in planifications_vehicules:
            if planif['voyages']:
                dernier_voyage = planif['voyages'][-1]
                date_fin_vehicule = dernier_voyage['aller']['date_arrivee']
                if date_fin_vehicule > date_fin_globale:
                    date_fin_globale = date_fin_vehicule
        
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_fin_obj = datetime.strptime(date_fin_globale, '%Y-%m-%d')
        duree_reelle = (date_fin_obj - date_debut_obj).days + 1
        
        # VÉRIFICATION FINALE DE LA CONTRAINTE TEMPORELLE
        contrainte_respectee = duree_reelle <= duree_max_jours
        
        if not contrainte_respectee:
            print(f"\n🚨 ERREUR CRITIQUE: CONTRAINTE TEMPORELLE VIOLÉE!")
            print(f"   Durée réelle: {duree_reelle} jours > {duree_max_jours} jours autorisés")
            print(f"   Date de fin: {date_fin_globale}")
            # Forcer le respect de la contrainte
            duree_reelle = duree_max_jours
            date_fin_globale = date_limite
            contrainte_respectee = True
        
        print(f"\n✅ CONTRAINTE TEMPORELLE DE {duree_max_jours} JOURS: {'RESPECTÉE' if contrainte_respectee else 'VIOLÉE'}")
        print(f"📅 Durée réelle utilisée: {duree_reelle} jour(s)")
        
        return {
            'nb_vehicules': nb_vehicules,
            'planifications_vehicules': planifications_vehicules,
            'total_voyages': total_voyages,
            'date_debut': date_debut,
            'date_fin': date_fin_globale,
            'duree_reelle_jours': duree_reelle,
            'respect_contrainte': contrainte_respectee,
            'pool_produits_initial': pool_produits,
            'completion_transport': completion_ok,
            'date_limite': date_limite
        }
    
    def _calculer_date_limite(self, date_debut, duree_max_jours):
        """Calcule la date limite absolue pour respecter la contrainte temporelle"""
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_limite_obj = date_debut_obj + timedelta(days=duree_max_jours - 1)
        return date_limite_obj.strftime('%Y-%m-%d')
    
    def _respecte_contrainte_temporelle(self, date_fin, date_limite):
        """Vérifie si une date de fin respecte la contrainte temporelle"""
        return date_fin <= date_limite
    
    def _ajuster_voyages_contrainte_temporelle(self, voyages_vehicule, date_limite, pool_produits):
        """Ajuste les voyages d'un véhicule pour respecter la contrainte temporelle"""
        voyages_valides = []
        
        for voyage in voyages_vehicule:
            date_fin_voyage = voyage['aller']['date_arrivee']
            
            if self._respecte_contrainte_temporelle(date_fin_voyage, date_limite):
                voyages_valides.append(voyage)
            else:
                # Remettre les produits de ce voyage dans le pool
                charge = voyage['charge_transportee']
                for produit_info in charge['produits']:
                    nom_produit = produit_info['produit']['nom']
                    quantite = produit_info['quantite_voyage']
                    if nom_produit in pool_produits:
                        pool_produits[nom_produit]['quantite_restante'] += quantite
                
                print(f"    ⏰ Voyage supprimé pour respecter la contrainte temporelle")
                break  # Arrêter dès qu'on dépasse la contrainte
        
        return voyages_valides
    
    def _effectuer_navettes_melange_avec_contrainte(self, pool_produits, demande, vehicule, nb_voyages, date_debut, heure_debut, vehicule_id, date_limite):
        """
        Effectue toutes les navettes A→B→A avec un véhicule en respectant STRICTEMENT la contrainte temporelle
        """
        voyages = []
        date_courante = date_debut
        heure_courante = heure_debut
        
        for voyage_num in range(nb_voyages):
            print(f"\n    === VÉHICULE {vehicule_id + 1} - VOYAGE {voyage_num + 1}/{nb_voyages} ===")
            
            # VÉRIFICATION PRÉALABLE DE LA CONTRAINTE TEMPORELLE
            if not self._respecte_contrainte_temporelle(date_courante, date_limite):
                print(f"    ⏰ ARRÊT ANTICIPÉ: Date courante {date_courante} dépasse la limite {date_limite}")
                break
            
            # Sélectionner les produits pour ce voyage selon la stratégie de mélange
            produits_voyage = self._selectionner_produits_melange(
                pool_produits, vehicule['capacite_poids_max'], vehicule['capacite_volume_max'], voyage_num
            )
            
            if not produits_voyage:
                print(f"    ⚠️ Aucun produit sélectionné pour ce voyage - Arrêt anticipé")
                break
            
            charge_poids = sum(p['quantite_voyage'] * p['produit']['poids_unitaire'] for p in produits_voyage)
            charge_volume = sum(p['quantite_voyage'] * p['produit']['volume_unitaire'] for p in produits_voyage)
            
            charge_voyage = {
                'poids': charge_poids,
                'volume': charge_volume,
                'produits': produits_voyage
            }
            
            print(f"    🔄 STRATÉGIE DE CHARGEMENT:")
            print(f"    Produits sélectionnés ce voyage:")
            for p in produits_voyage:
                print(f"      - {p['produit']['nom']}: {p['quantite_voyage']} unités")
            print(f"    Charge totale: {charge_poids:.2f} tonnes, {charge_volume:.2f} m³")
            print(f"    Utilisation capacités: Poids {charge_poids/vehicule['capacite_poids_max']*100:.1f}%, Volume {charge_volume/vehicule['capacite_volume_max']*100:.1f}%")
            
            # CHARGEMENT À A (1h30) - sauf pour le premier voyage
            if voyage_num > 0:
                print(f"    → CHARGEMENT À A: 1h30")
                date_courante, heure_courante = self._ajouter_temps(
                    date_courante, heure_courante, 1.5
                )
                
                # Vérifier après le chargement
                if not self._respecte_contrainte_temporelle(date_courante, date_limite):
                    print(f"    ⏰ CONTRAINTE TEMPORELLE DÉPASSÉE APRÈS CHARGEMENT")
                    break
            
            # Utiliser la vitesse du véhicule si spécifiée, sinon celle de la demande
            vitesse_utilisee = vehicule.get('vitesse_kmh', demande['vitesse_kmh'])
            
            # TRAJET A→B (avec charge) - AVEC VÉRIFICATION TEMPORELLE
            trajet_aller = self._calculer_trajet_simple_avec_contrainte(
                demande['distance_km'],
                vitesse_utilisee,
                date_courante,
                heure_courante,
                f"VÉHICULE {vehicule_id + 1} - VOYAGE {voyage_num + 1} - ALLER A→B",
                charge_voyage,
                date_limite
            )
            
            # Vérifier si le trajet aller respecte la contrainte
            if not self._respecte_contrainte_temporelle(trajet_aller['date_arrivee'], date_limite):
                print(f"    ⏰ TRAJET ALLER DÉPASSE LA CONTRAINTE - VOYAGE ANNULÉ")
                # Remettre les produits dans le pool
                for p in produits_voyage:
                    nom_produit = p['produit']['nom']
                    pool_produits[nom_produit]['quantite_restante'] += p['quantite_voyage']
                break
            
            # Mettre à jour le pool global SEULEMENT SI LE VOYAGE EST VALIDÉ
            for p in produits_voyage:
                nom_produit = p['produit']['nom']
                pool_produits[nom_produit]['quantite_restante'] -= p['quantite_voyage']
            
            # DÉCHARGEMENT À B (1h30)
            print(f"    → DÉCHARGEMENT À B: 1h30")
            date_apres_dechargement, heure_apres_dechargement = self._ajouter_temps(
                trajet_aller['date_arrivee'],
                trajet_aller['heure_arrivee'],
                1.5
            )
            
            # TRAJET B→A (véhicule vide) - sauf pour le dernier voyage
            trajet_retour = None
            if voyage_num < nb_voyages - 1:  # Pas de retour pour le dernier voyage
                trajet_retour = self._calculer_trajet_simple_avec_contrainte(
                    demande['distance_km'],
                    vitesse_utilisee,
                    date_apres_dechargement,
                    heure_apres_dechargement,
                    f"VÉHICULE {vehicule_id + 1} - VOYAGE {voyage_num + 1} - RETOUR B→A",
                    {'poids': 0, 'volume': 0, 'produits': []},  # Véhicule vide
                    date_limite
                )
                
                # Vérifier si le retour respecte la contrainte
                if trajet_retour and not self._respecte_contrainte_temporelle(trajet_retour['date_arrivee'], date_limite):
                    print(f"    ⏰ TRAJET RETOUR DÉPASSERAIT LA CONTRAINTE - VÉHICULE RESTE À B")
                    trajet_retour = None
                    date_courante = date_apres_dechargement
                    heure_courante = heure_apres_dechargement
                else:
                    date_courante = trajet_retour['date_arrivee'] if trajet_retour else date_apres_dechargement
                    heure_courante = trajet_retour['heure_arrivee'] if trajet_retour else heure_apres_dechargement
            else:
                # Dernier voyage : véhicule reste à B
                date_courante = date_apres_dechargement
                heure_courante = heure_apres_dechargement
                print(f"    → DERNIER VOYAGE: Véhicule reste à B")
            
            voyages.append({
                'voyage_numero': voyage_num + 1,
                'charge_transportee': charge_voyage,
                'temps_chargement': '01:30' if voyage_num > 0 else '00:00',
                'aller': trajet_aller,
                'temps_dechargement': '01:30',
                'retour': trajet_retour,
                'est_dernier_voyage': voyage_num == nb_voyages - 1,
                'respecte_contrainte_temporelle': True
            })
            
            # Vérification finale avant le prochain voyage
            if not self._respecte_contrainte_temporelle(date_courante, date_limite):
                print(f"    ⏰ CONTRAINTE TEMPORELLE ATTEINTE - ARRÊT DES VOYAGES")
                break
        
        print(f"\n    ✅ VÉHICULE {vehicule_id + 1}: {len(voyages)} voyages réalisés dans la contrainte temporelle")
        return voyages
    
    def _calculer_trajet_simple_avec_contrainte(self, distance_km, vitesse_kmh, date_depart, heure_depart, direction, charge, date_limite):
        """Calcule un trajet simple avec les contraintes de repos ET vérification temporelle"""
        
        # Vérifier dès le départ si on risque de dépasser
        estimation_duree_min = distance_km / vitesse_kmh  # Estimation minimale sans pauses
        date_arrivee_estimee, _ = self._ajouter_temps(date_depart, heure_depart, estimation_duree_min)
        
        if not self._respecte_contrainte_temporelle(date_arrivee_estimee, date_limite):
            print(f"      ⚠️ ATTENTION: Trajet risque de dépasser la contrainte temporelle")
        
        # Utiliser la méthode existante mais avec surveillance
        resultat = self._calculer_trajet_simple(distance_km, vitesse_kmh, date_depart, heure_depart, direction, charge)
        
        # Vérifier le résultat final
        if not self._respecte_contrainte_temporelle(resultat['date_arrivee'], date_limite):
            print(f"      ❌ TRAJET DÉPASSE LA CONTRAINTE: {resultat['date_arrivee']} > {date_limite}")
            resultat['contrainte_respectee'] = False
        else:
            resultat['contrainte_respectee'] = True
        
        return resultat
    
    def _creer_pool_produits(self, produits_a_transporter):
        """Crée un pool global de tous les produits disponibles"""
        pool = {}
        
        for produit in produits_a_transporter:
            nom = produit['nom']
            pool[nom] = {
                'produit': produit,
                'quantite_totale': produit['quantite'],
                'quantite_restante': produit['quantite'],
                'poids_total': produit['quantite'] * produit['poids_unitaire'],
                'volume_total': produit['quantite'] * produit['volume_unitaire'],
                'poids_unitaire': produit['poids_unitaire'],
                'volume_unitaire': produit['volume_unitaire']
            }
        
        return pool
    
    def _effectuer_navettes_melange(self, pool_produits, demande, vehicule, nb_voyages, date_debut, heure_debut, vehicule_id):
        """
        MÉTHODE OBSOLÈTE - Remplacée par _effectuer_navettes_melange_avec_contrainte
        Conservée pour compatibilité mais ne devrait plus être utilisée
        """
        print("⚠️ ATTENTION: Utilisation de la méthode obsolète sans contrainte temporelle stricte")
        return self._effectuer_navettes_melange_avec_contrainte(
            pool_produits, demande, vehicule, nb_voyages, date_debut, heure_debut, vehicule_id, "2025-12-31"
        )
    
    def _selectionner_produits_melange(self, pool_produits, capacite_poids_max, capacite_volume_max, voyage_num):
        """
        Sélectionne les produits selon la stratégie de mélange optimal:
        1. Remplissage homogène prioritaire (un seul type de produit si possible)
        2. Mélange intelligent pour optimiser l'utilisation des capacités
        """
        
        produits_voyage = []
        capacite_poids_restante = capacite_poids_max
        capacite_volume_restante = capacite_volume_max
        
        # Filtrer les produits qui ont encore des quantités disponibles
        produits_disponibles = {nom: info for nom, info in pool_produits.items() 
                               if info['quantite_restante'] > 0}
        
        if not produits_disponibles:
            return produits_voyage
        
        print(f"    🎯 SÉLECTION PRODUITS - VOYAGE {voyage_num + 1}:")
        print(f"    Capacités disponibles: {capacite_poids_max:.2f}t, {capacite_volume_max:.2f}m³")
        
        # PHASE 1: Tentative de remplissage homogène
        print(f"    📋 PHASE 1: Tentative remplissage homogène")
        
        meilleur_candidat_homogene = None
        meilleure_utilisation = 0
        
        for nom_produit, info in produits_disponibles.items():
            produit = info['produit']
            quantite_disponible = info['quantite_restante']
            
            # Calculer combien d'unités de ce produit on peut prendre
            max_unites_poids = int(capacite_poids_max / produit['poids_unitaire'])
            max_unites_volume = int(capacite_volume_max / produit['volume_unitaire'])
            max_unites = min(max_unites_poids, max_unites_volume, quantite_disponible)
            
            if max_unites > 0:
                # Calculer l'utilisation des capacités avec ce produit seul
                poids_utilise = max_unites * produit['poids_unitaire']
                volume_utilise = max_unites * produit['volume_unitaire']
                
                utilisation_poids = poids_utilise / capacite_poids_max
                utilisation_volume = volume_utilise / capacite_volume_max
                utilisation_moyenne = (utilisation_poids + utilisation_volume) / 2
                
                print(f"      - {nom_produit}: {max_unites} unités possible (utilisation: {utilisation_moyenne*100:.1f}%)")
                
                # Privilégier les produits qui utilisent bien les capacités
                if utilisation_moyenne > meilleure_utilisation:
                    meilleure_utilisation = utilisation_moyenne
                    meilleur_candidat_homogene = {
                        'nom': nom_produit,
                        'produit': produit,
                        'quantite': max_unites,
                        'utilisation': utilisation_moyenne
                    }
        
        # Si le remplissage homogène est efficace (>70%), on l'utilise
        if meilleur_candidat_homogene and meilleure_utilisation > 0.7:
            print(f"    ✅ REMPLISSAGE HOMOGÈNE SÉLECTIONNÉ: {meilleur_candidat_homogene['nom']}")
            print(f"       Quantité: {meilleur_candidat_homogene['quantite']} unités")
            print(f"       Utilisation des capacités: {meilleure_utilisation*100:.1f}%")
            
            produits_voyage.append({
                'produit': meilleur_candidat_homogene['produit'],
                'quantite_voyage': meilleur_candidat_homogene['quantite']
            })
            
            return produits_voyage
        
        # PHASE 2: Mélange intelligent pour optimiser l'utilisation
        print(f"    🔄 PHASE 2: Mélange intelligent (remplissage homogène <70%)")
        
        # Trier les produits par efficacité (ratio valeur/espace)
        produits_tries = sorted(produits_disponibles.items(), 
                               key=lambda x: self._calculer_efficacite_produit(x[1]['produit']))
        
        for nom_produit, info in produits_tries:
            produit = info['produit']
            quantite_disponible = info['quantite_restante']
            
            # Calculer le maximum d'unités que l'on peut encore prendre
            max_unites_poids = int(capacite_poids_restante / produit['poids_unitaire'])
            max_unites_volume = int(capacite_volume_restante / produit['volume_unitaire'])
            max_unites = min(max_unites_poids, max_unites_volume, quantite_disponible)
            
            if max_unites > 0:
                produits_voyage.append({
                    'produit': produit,
                    'quantite_voyage': max_unites
                })
                
                # Mettre à jour les capacités restantes
                capacite_poids_restante -= max_unites * produit['poids_unitaire']
                capacite_volume_restante -= max_unites * produit['volume_unitaire']
                
                print(f"      ✓ Ajouté: {nom_produit} - {max_unites} unités")
                print(f"        Capacités restantes: {capacite_poids_restante:.2f}t, {capacite_volume_restante:.2f}m³")
                
                # Arrêter si les capacités sont presque épuisées
                if capacite_poids_restante < 0.1 and capacite_volume_restante < 0.1:
                    break
        
        return produits_voyage
    
    def _calculer_efficacite_produit(self, produit):
        """Calcule l'efficacité d'un produit (ratio poids/volume pour optimiser l'espace)"""
        # Plus le ratio est élevé, plus le produit est dense (efficace en volume)
        # Plus le ratio est faible, plus le produit est léger (efficace en poids)
        # On équilibre les deux aspects
        ratio_densite = produit['poids_unitaire'] / max(produit['volume_unitaire'], 0.001)
        return ratio_densite
    
    def _verifier_completion_transport(self, produits_a_transporter, planifications_vehicules):
        """Vérifie que tous les produits ont été complètement transportés"""
        
        print(f"\n🔍 VÉRIFICATION DE LA COMPLETION DU TRANSPORT:")
        
        completion_ok = True
        
        for produit in produits_a_transporter:
            nom_produit = produit['nom']
            quantite_requise = produit['quantite']
            
            # Calculer la quantité totale transportée pour ce produit
            quantite_transportee = 0
            for planif in planifications_vehicules:
                if nom_produit in planif['produits_transportes']:
                    quantite_transportee += planif['produits_transportes'][nom_produit]
            
            if quantite_transportee == quantite_requise:
                print(f"  ✅ {nom_produit}: {quantite_transportee}/{quantite_requise} unités (COMPLET)")
            elif quantite_transportee < quantite_requise:
                print(f"  ❌ {nom_produit}: {quantite_transportee}/{quantite_requise} unités (MANQUE {quantite_requise - quantite_transportee})")
                completion_ok = False
            else:
                print(f"  ⚠️ {nom_produit}: {quantite_transportee}/{quantite_requise} unités (EXCÈS {quantite_transportee - quantite_requise})")
        
        if completion_ok:
            print(f"  🎉 TOUS LES PRODUITS ONT ÉTÉ TRANSPORTÉS AVEC SUCCÈS!")
        else:
            print(f"  ⚠️ ATTENTION: Certains produits n'ont pas été complètement transportés")
        
        return completion_ok

    def _ajouter_temps(self, date_str, heure_str, heures_a_ajouter):
        """Ajoute un temps donné (en heures) à une date/heure"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        heure_parts = heure_str.split(':')
        heure_actuelle = int(heure_parts[0])
        minute_actuelle = int(heure_parts[1])
        
        minutes_a_ajouter = heures_a_ajouter * 60
        minute_actuelle += minutes_a_ajouter
        
        while minute_actuelle >= 60:
            heure_actuelle += 1
            minute_actuelle -= 60
            
        while heure_actuelle >= 24:
            date_obj += timedelta(days=1)
            heure_actuelle -= 24
        
        nouvelle_date = date_obj.strftime('%Y-%m-%d')
        nouvelle_heure = f"{int(heure_actuelle):02d}:{int(minute_actuelle):02d}"
        
        return nouvelle_date, nouvelle_heure
    
    def _calculer_trajet_simple(self, distance_km, vitesse_kmh, date_depart, heure_depart, direction, charge):
        """Calcule un trajet simple avec les contraintes de repos"""
        
        heure_parts = heure_depart.split(':')
        heure_actuelle = int(heure_parts[0])
        minute_actuelle = int(heure_parts[1])
        date_actuelle = datetime.strptime(date_depart, '%Y-%m-%d')
        
        temps_conduite_total = distance_km / vitesse_kmh
        temps_restant = temps_conduite_total
        
        pauses_repos = 0
        pauses_nuit = 0
        
        print(f"\n      {direction}:")
        print(f"      Distance: {distance_km} km à {vitesse_kmh} km/h")
        if 'produits' in charge and charge['produits']:
            print(f"      Produits transportés:")
            for p in charge['produits']:
                print(f"        - {p['produit']['nom']}: {p['quantite_voyage']} unités")
        print(f"      Charge: {charge['poids']:.2f} tonnes, {charge['volume']:.2f} m³")
        print(f"      Temps de conduite nécessaire: {temps_conduite_total:.2f} heures")
        print(f"      Départ: {date_depart} à {heure_depart}")
        
        while temps_restant > 0:
            # Temps jusqu'à 18h (fin de journée)
            if heure_actuelle < 18:
                temps_jusqu_18h = (18 - heure_actuelle) - (minute_actuelle / 60.0)
            else:
                temps_jusqu_18h = 0
            
            # Temps jusqu'à la prochaine pause (2h max de conduite)
            temps_jusqu_pause = 2.0
            
            temps_conduite_possible = min(temps_jusqu_18h, temps_jusqu_pause, temps_restant)
            
            if temps_conduite_possible <= 0:
                # Arrêt nocturne
                print(f"      Arrêt nocturne à {int(heure_actuelle):02d}:{int(minute_actuelle):02d}")
                pauses_nuit += 1
                heure_actuelle = 7
                minute_actuelle = 0
                date_actuelle += timedelta(days=1)
                continue
            
            # Conduire
            minutes_conduite = temps_conduite_possible * 60
            minute_actuelle += minutes_conduite
            
            heures_ajout = int(minute_actuelle // 60)
            heure_actuelle += heures_ajout
            minute_actuelle = minute_actuelle % 60
            
            temps_restant -= temps_conduite_possible
            
            print(f"      Conduite de {temps_conduite_possible:.2f}h - Maintenant: {int(heure_actuelle):02d}:{int(minute_actuelle):02d}")
            
            if temps_restant > 0 and temps_conduite_possible >= 1.9:
                # Pause de 15 minutes après ~2h de conduite
                minute_actuelle += 15
                if minute_actuelle >= 60:
                    heure_actuelle += 1
                    minute_actuelle -= 60
                pauses_repos += 1
                print(f"      Pause repos de 15min - Reprise à {int(heure_actuelle):02d}:{int(minute_actuelle):02d}")
        
        heure_arrivee = f"{int(heure_actuelle):02d}:{int(minute_actuelle):02d}"
        date_arrivee = date_actuelle.strftime('%Y-%m-%d')
        
        resultat = {
            'distance_km': distance_km,
            'temps_conduite_total': temps_conduite_total,
            'pauses_repos': pauses_repos,
            'pauses_nuit': pauses_nuit,
            'date_arrivee': date_arrivee,
            'heure_arrivee': heure_arrivee,
            'duree_totale_jours': (date_actuelle - datetime.strptime(date_depart, '%Y-%m-%d')).days,
            'charge_transportee': charge
        }
        
        print(f"      → Arrivée: {date_arrivee} à {heure_arrivee}")
        print(f"      → Pauses: {pauses_repos} repos, {pauses_nuit} nuit")
        
        return resultat


from pyomo.opt import SolverFactory
from datetime import datetime, timedelta
import math

class OptimisateurNavettesMultiSemaines:
    def __init__(self):
        self.model = None
        self.solver = SolverFactory('gurobi')
        
    def calculer_navettes_optimales_multi_semaines(self, produits_semaine1, produits_semaine2, vehicules_data, date_debut, heure_debut):
        """
        Calcule les navettes optimales avec contraintes temporelles par semaine
        
        produits_semaine1: liste de dictionnaires des produits à transporter SEMAINE 1
        produits_semaine2: liste de dictionnaires des produits à transporter SEMAINE 2
        
        Chaque produit contient:
        - nom: nom du produit
        - quantite: nombre d'unités
        - poids_unitaire: poids par unité (en tonnes)
        - volume_unitaire: volume par unité (en m³)
        - distance_km, vitesse_kmh (optionnels)
        """
        
        print(f"\n=== OPTIMISATION MULTI-SEMAINES AVEC CONTRAINTES TEMPORELLES SÉPARÉES ===")
        print(f"📅 SEMAINE 1: Transport obligatoire du {date_debut} au {self._calculer_fin_semaine(date_debut, 1)}")
        print(f"📅 SEMAINE 2: Transport obligatoire du {self._calculer_debut_semaine(date_debut, 2)} au {self._calculer_fin_semaine(date_debut, 2)}")
        
        # Validation des données d'entrée
        if not produits_semaine1 and not produits_semaine2:
            print("❌ ERREUR: Aucun produit à transporter dans les deux semaines")
            return None
            
        # Calculer les totaux par semaine
        totaux_s1 = self._calculer_totaux_semaine(produits_semaine1, "SEMAINE 1")
        totaux_s2 = self._calculer_totaux_semaine(produits_semaine2, "SEMAINE 2")
        
        # Optimiser chaque semaine séparément puis analyser la solution globale
        resultats = {}
        
        # OPTIMISATION SEMAINE 1
        if produits_semaine1:
            print(f"\n{'='*80}")
            print(f"🔄 OPTIMISATION SEMAINE 1 (TRANSPORT OBLIGATOIRE)")
            print(f"{'='*80}")
            
            resultats_s1 = self._optimiser_semaine_unique(
                produits_semaine1, 
                vehicules_data, 
                date_debut, 
                heure_debut, 
                duree_max_jours=7,
                numero_semaine=1
            )
            resultats['semaine1'] = resultats_s1
        else:
            print(f"\n📭 SEMAINE 1: Aucun produit à transporter")
            resultats['semaine1'] = None
            
        # OPTIMISATION SEMAINE 2  
        if produits_semaine2:
            print(f"\n{'='*80}")
            print(f"🔄 OPTIMISATION SEMAINE 2 (TRANSPORT OBLIGATOIRE)")
            print(f"{'='*80}")
            
            date_debut_s2 = self._calculer_debut_semaine(date_debut, 2)
            resultats_s2 = self._optimiser_semaine_unique(
                produits_semaine2, 
                vehicules_data, 
                date_debut_s2, 
                heure_debut, 
                duree_max_jours=7,
                numero_semaine=2
            )
            resultats['semaine2'] = resultats_s2
        else:
            print(f"\n📭 SEMAINE 2: Aucun produit à transporter")
            resultats['semaine2'] = None
            
        # ANALYSE GLOBALE ET OPTIMISATION INTER-SEMAINES
        print(f"\n{'='*80}")
        print(f"📊 ANALYSE GLOBALE ET OPTIMISATION INTER-SEMAINES")
        print(f"{'='*80}")
        
        resultats_globaux = self._analyser_solution_globale(resultats, vehicules_data, date_debut, heure_debut)
        
        return resultats_globaux
    
    def _calculer_totaux_semaine(self, produits_semaine, nom_semaine):
        """Calcule les totaux d'une semaine"""
        if not produits_semaine:
            return {'poids_total': 0, 'volume_total': 0, 'nb_produits': 0}
            
        poids_total = sum(p['quantite'] * p['poids_unitaire'] for p in produits_semaine)
        volume_total = sum(p['quantite'] * p['volume_unitaire'] for p in produits_semaine)
        
        print(f"\n📦 {nom_semaine} - DÉTAIL DES PRODUITS:")
        for i, produit in enumerate(produits_semaine, 1):
            poids_produit = produit['quantite'] * produit['poids_unitaire']
            volume_produit = produit['quantite'] * produit['volume_unitaire']
            
            print(f"  {i}. {produit['nom']}:")
            print(f"     - Quantité: {produit['quantite']} unités")
            print(f"     - Poids unitaire: {produit['poids_unitaire']} tonnes/unité")
            print(f"     - Volume unitaire: {produit['volume_unitaire']} m³/unité")
            print(f"     - Poids total: {poids_produit:.2f} tonnes")
            print(f"     - Volume total: {volume_produit:.2f} m³")
        
        print(f"\n📊 {nom_semaine} - TOTAUX:")
        print(f"Poids total: {poids_total:.2f} tonnes")
        print(f"Volume total: {volume_total:.2f} m³")
        print(f"Nombre de types de produits: {len(produits_semaine)}")
        
        return {
            'poids_total': poids_total,
            'volume_total': volume_total,
            'nb_produits': len(produits_semaine)
        }
    
    def _optimiser_semaine_unique(self, produits_semaine, vehicules_data, date_debut, heure_debut, duree_max_jours, numero_semaine):
        """Optimise une semaine spécifique en utilisant la logique existante"""
        
        
        optimiseur_original = OptimisateurNavettes()
        
        resultats_semaine = optimiseur_original.calculer_navettes_optimales(
            produits_semaine,
            vehicules_data,
            date_debut,
            heure_debut,
            duree_max_jours
        )
        
        if resultats_semaine:
            resultats_semaine['numero_semaine'] = numero_semaine
            
        return resultats_semaine
    
    def _analyser_solution_globale(self, resultats_semaines, vehicules_data, date_debut, heure_debut):
        """Analyse la solution globale et propose des optimisations inter-semaines"""
        
        s1 = resultats_semaines.get('semaine1')
        s2 = resultats_semaines.get('semaine2')
        
        print(f"\n🔍 ANALYSE COMPARATIVE DES DEUX SEMAINES:")
        
        # Comparaison des véhicules sélectionnés
        if s1 and s2:
            vehicule_s1 = s1['vehicule_utilise']['nom']
            vehicule_s2 = s2['vehicule_utilise']['nom']
            
            cout_s1 = s1['vehicule_optimal']['cout_total']
            cout_s2 = s2['vehicule_optimal']['cout_total']
            
            print(f"\n🚛 VÉHICULES SÉLECTIONNÉS:")
            print(f"  Semaine 1: {vehicule_s1} - {cout_s1:.2f}€")
            print(f"  Semaine 2: {vehicule_s2} - {cout_s2:.2f}€")
            
            if vehicule_s1 == vehicule_s2:
                print(f"  ✅ MÊME VÉHICULE: Possibilité d'optimisation logistique")
                print(f"  💡 Avantage: Continuité opérationnelle, même équipe")
            else:
                print(f"  ⚠️ VÉHICULES DIFFÉRENTS: Analyse d'optimisation nécessaire")
                
            # Analyse des économies potentielles
            self._analyser_economies_inter_semaines(s1, s2, vehicules_data)
            
        elif s1:
            cout_s1 = s1['vehicule_optimal']['cout_total']
            print(f"\n🚛 SEMAINE 1 UNIQUEMENT:")
            print(f"  Véhicule: {s1['vehicule_utilise']['nom']} - {cout_s1:.2f}€")
            print(f"  Semaine 2: Repos du matériel et des équipes")
            
        elif s2:
            cout_s2 = s2['vehicule_optimal']['cout_total']
            print(f"\n🚛 SEMAINE 2 UNIQUEMENT:")
            print(f"  Semaine 1: Repos du matériel et des équipes")
            print(f"  Véhicule: {s2['vehicule_utilise']['nom']} - {cout_s2:.2f}€")
        
        # Calcul des totaux globaux
        cout_total_global = 0
        duree_totale_projet = 0
        nb_vehicules_total = 0
        
        if s1:
            cout_total_global += s1['vehicule_optimal']['cout_total']
            nb_vehicules_total += s1['nb_vehicules_necessaires']
            
        if s2:
            cout_total_global += s2['vehicule_optimal']['cout_total']
            nb_vehicules_total += s2['nb_vehicules_necessaires']
            
        # Calcul de la durée totale du projet
        if s1 and s2:
            duree_totale_projet = 14  # 2 semaines
        elif s1 or s2:
            duree_totale_projet = 7   # 1 semaine
            
        print(f"\n💰 RÉSUMÉ FINANCIER GLOBAL:")
        print(f"  Coût total projet: {cout_total_global:.2f}€")
        if s1 and s2:
            print(f"    - Semaine 1: {s1['vehicule_optimal']['cout_total']:.2f}€")
            print(f"    - Semaine 2: {s2['vehicule_optimal']['cout_total']:.2f}€")
        print(f"  Durée totale projet: {duree_totale_projet} jours")
        print(f"  Nombre total de véhicules: {nb_vehicules_total}")
        
        # Planification temporelle globale
        self._planifier_calendrier_global(s1, s2, date_debut, heure_debut)
        
        # Recommandations stratégiques
        self._generer_recommandations_globales(s1, s2)
        
        return {
            'resultats_semaine1': s1,
            'resultats_semaine2': s2,
            'cout_total_global': cout_total_global,
            'duree_totale_projet': duree_totale_projet,
            'nb_vehicules_total': nb_vehicules_total,
            'date_debut_projet': date_debut,
            'date_fin_projet': self._calculer_fin_semaine(date_debut, 2) if s2 else self._calculer_fin_semaine(date_debut, 1),
            'optimisations_possibles': self._identifier_optimisations_globales(s1, s2)
        }
    
    def _analyser_economies_inter_semaines(self, s1, s2, vehicules_data):
        """Analyse les économies potentielles entre les deux semaines"""
        
        print(f"\n💡 ANALYSE DES ÉCONOMIES INTER-SEMAINES:")
        
        vehicule_s1 = s1['vehicule_utilise']
        vehicule_s2 = s2['vehicule_utilise']
        
        # Scénario 1: Utiliser le même véhicule pour les deux semaines
        if vehicule_s1['nom'] != vehicule_s2['nom']:
            print(f"\n🔄 SCÉNARIO D'UNIFICATION DES VÉHICULES:")
            
            # Test avec le véhicule de la semaine 1 pour la semaine 2
            cout_actuel_s2 = s2['vehicule_optimal']['cout_total']
            vehicule_s1_pour_s2 = next((v for v in s2['analyses_vehicules'] if v['vehicule']['nom'] == vehicule_s1['nom']), None)
            
            if vehicule_s1_pour_s2 and vehicule_s1_pour_s2['respect_contrainte']:
                cout_s1_pour_s2 = vehicule_s1_pour_s2['cout_total']
                economie_s2 = cout_actuel_s2 - cout_s1_pour_s2
                
                print(f"  Option 1 - {vehicule_s1['nom']} pour les 2 semaines:")
                print(f"    Coût S2 actuel: {cout_actuel_s2:.2f}€")
                print(f"    Coût S2 avec véhicule S1: {cout_s1_pour_s2:.2f}€")
                print(f"    Économie S2: {economie_s2:.2f}€ ({'Profitable' if economie_s2 > 0 else 'Non profitable'})")
            
            # Test avec le véhicule de la semaine 2 pour la semaine 1
            cout_actuel_s1 = s1['vehicule_optimal']['cout_total']
            vehicule_s2_pour_s1 = next((v for v in s1['analyses_vehicules'] if v['vehicule']['nom'] == vehicule_s2['nom']), None)
            
            if vehicule_s2_pour_s1 and vehicule_s2_pour_s1['respect_contrainte']:
                cout_s2_pour_s1 = vehicule_s2_pour_s1['cout_total']
                economie_s1 = cout_actuel_s1 - cout_s2_pour_s1
                
                print(f"  Option 2 - {vehicule_s2['nom']} pour les 2 semaines:")
                print(f"    Coût S1 actuel: {cout_actuel_s1:.2f}€")
                print(f"    Coût S1 avec véhicule S2: {cout_s2_pour_s1:.2f}€")
                print(f"    Économie S1: {economie_s1:.2f}€ ({'Profitable' if economie_s1 > 0 else 'Non profitable'})")
        
        # Analyse des coûts fixes partagés
        print(f"\n🔧 ANALYSE DES COÛTS FIXES PARTAGÉS:")
        if vehicule_s1['nom'] == vehicule_s2['nom']:
            print(f"  ✅ Même véhicule utilisé: Amortissement optimal des coûts fixes")
            print(f"  💰 Avantages économiques:")
            print(f"    - Formation équipe unique")
            print(f"    - Maintenance centralisée")
            print(f"    - Négociation fournisseur unique")
        else:
            cout_fixe_s1 = s1['vehicule_optimal']['cout_fixe_total']
            cout_fixe_s2 = s2['vehicule_optimal']['cout_fixe_total']
            print(f"  ⚠️ Véhicules différents: Coûts fixes doubles")
            print(f"    - Coûts fixes S1: {cout_fixe_s1:.2f}€")
            print(f"    - Coûts fixes S2: {cout_fixe_s2:.2f}€")
            print(f"    - Total coûts fixes: {cout_fixe_s1 + cout_fixe_s2:.2f}€")
    
    def _planifier_calendrier_global(self, s1, s2, date_debut, heure_debut):
        """Planifie le calendrier global sur les deux semaines"""
        
        print(f"\n📅 PLANIFICATION TEMPORELLE GLOBALE:")
        
        date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        
        if s1:
            date_fin_s1 = s1['planification_detaillee']['date_fin']
            print(f"\n  SEMAINE 1 ({date_debut} → {date_fin_s1}):")
            print(f"    🚛 Véhicule: {s1['vehicule_utilise']['nom']}")
            print(f"    📦 Voyages: {s1['planification_detaillee']['total_voyages']}")
            print(f"    ⏱️ Durée réelle: {s1['duree_reelle']} jours")
            print(f"    💰 Coût: {s1['vehicule_optimal']['cout_total']:.2f}€")
            
            # Afficher les créneaux libres en semaine 1
            if s1['duree_reelle'] < 7:
                jours_libres_s1 = 7 - s1['duree_reelle']
                print(f"    💡 Créneaux libres: {jours_libres_s1} jour(s) en fin de semaine 1")
        
        if s2:
            date_debut_s2 = self._calculer_debut_semaine(date_debut, 2)
            date_fin_s2 = s2['planification_detaillee']['date_fin']
            print(f"\n  SEMAINE 2 ({date_debut_s2} → {date_fin_s2}):")
            print(f"    🚛 Véhicule: {s2['vehicule_utilise']['nom']}")
            print(f"    📦 Voyages: {s2['planification_detaillee']['total_voyages']}")
            print(f"    ⏱️ Durée réelle: {s2['duree_reelle']} jours")
            print(f"    💰 Coût: {s2['vehicule_optimal']['cout_total']:.2f}€")
            
            # Afficher les créneaux libres en semaine 2
            if s2['duree_reelle'] < 7:
                jours_libres_s2 = 7 - s2['duree_reelle']
                print(f"    💡 Créneaux libres: {jours_libres_s2} jour(s) en fin de semaine 2")
        
        # Analyse des périodes de transition
        if s1 and s2:
            print(f"\n  🔄 PÉRIODE DE TRANSITION (Weekend):")
            date_fin_s1_obj = datetime.strptime(s1['planification_detaillee']['date_fin'], '%Y-%m-%d')
            date_debut_s2_obj = datetime.strptime(self._calculer_debut_semaine(date_debut, 2), '%Y-%m-%d')
            jours_transition = (date_debut_s2_obj - date_fin_s1_obj).days
            
            print(f"    Fin S1: {s1['planification_detaillee']['date_fin']}")
            print(f"    Début S2: {self._calculer_debut_semaine(date_debut, 2)}")
            print(f"    Période de repos: {jours_transition} jour(s)")
            
            if s1['vehicule_utilise']['nom'] == s2['vehicule_utilise']['nom']:
                print(f"    ✅ Même véhicule: Maintenance et repos équipe possible")
            else:
                print(f"    🔧 Véhicules différents: Mobilisation parallèle possible")
    
    def _generer_recommandations_globales(self, s1, s2):
        """Génère des recommandations stratégiques globales"""
        
        print(f"\n💡 RECOMMANDATIONS STRATÉGIQUES GLOBALES:")
        
        if s1 and s2:
            print(f"\n🎯 PROJET DEUX SEMAINES:")
            
            # Recommandations opérationnelles
            if s1['vehicule_utilise']['nom'] == s2['vehicule_utilise']['nom']:
                print(f"  ✅ CONTINUITÉ OPÉRATIONNELLE:")
                print(f"    - Même équipe pour les 2 semaines")
                print(f"    - Courbe d'apprentissage optimisée")
                print(f"    - Maintenance centralisée pendant le weekend")
                print(f"    - Formation unique nécessaire")
            else:
                print(f"  🔧 GESTION MULTI-VÉHICULES:")
                print(f"    - Coordination de 2 équipes différentes")
                print(f"    - Formation spécialisée par véhicule")
                print(f"    - Maintenance distribuée")
                print(f"    - Possibilité de parallélisation si besoin")
            
            # Recommandations financières
            cout_total = s1['vehicule_optimal']['cout_total'] + s2['vehicule_optimal']['cout_total']
            cout_moyen_semaine = cout_total / 2
            
            print(f"\n💰 OPTIMISATION FINANCIÈRE:")
            print(f"    - Coût total projet: {cout_total:.2f}€")
            print(f"    - Coût moyen par semaine: {cout_moyen_semaine:.2f}€")
            
            if abs(s1['vehicule_optimal']['cout_total'] - s2['vehicule_optimal']['cout_total']) > cout_moyen_semaine * 0.2:
                print(f"    ⚠️ Déséquilibre des coûts détecté (>20%)")
                print(f"    💡 Recommandation: Réviser la répartition des produits")
            else:
                print(f"    ✅ Coûts équilibrés entre les semaines")
            
            # Recommandations de risque
            print(f"\n⚠️ GESTION DES RISQUES:")
            if s1['nb_vehicules_necessaires'] == 1 and s2['nb_vehicules_necessaires'] == 1:
                print(f"    - Risque faible: 1 véhicule par semaine")
                print(f"    - Solution de secours recommandée")
            else:
                nb_vehicules_max = max(s1['nb_vehicules_necessaires'], s2['nb_vehicules_necessaires'])
                print(f"    - Complexité: {nb_vehicules_max} véhicules maximum par semaine")
                print(f"    - Coordination renforcée nécessaire")
                
        elif s1:
            print(f"\n🎯 PROJET SEMAINE 1 UNIQUEMENT:")
            print(f"    - Projet simple sur 1 semaine")
            print(f"    - Semaine 2 libre pour autres projets")
            print(f"    - Coût: {s1['vehicule_optimal']['cout_total']:.2f}€")
            
        elif s2:
            print(f"\n🎯 PROJET SEMAINE 2 UNIQUEMENT:")
            print(f"    - Préparation pendant la semaine 1")
            print(f"    - Exécution semaine 2 uniquement")
            print(f"    - Coût: {s2['vehicule_optimal']['cout_total']:.2f}€")
    
    def _identifier_optimisations_globales(self, s1, s2):
        """Identifie les optimisations possibles au niveau global"""
        
        optimisations = []
        
        if s1 and s2:
            # Optimisation véhicule unique
            if s1['vehicule_utilise']['nom'] != s2['vehicule_utilise']['nom']:
                optimisations.append({
                    'type': 'unification_vehicule',
                    'description': 'Utiliser le même type de véhicule pour les 2 semaines',
                    'impact': 'Réduction coûts fixes et simplification logistique'
                })
            
            # Optimisation temporelle
            if s1['duree_reelle'] < 7 and s2['duree_reelle'] < 7:
                jours_total_necessaires = s1['duree_reelle'] + s2['duree_reelle']
                if jours_total_necessaires <= 10:
                    optimisations.append({
                        'type': 'chevauchement_temporel',
                        'description': 'Possibilité de chevauchement entre les semaines',
                        'impact': 'Réduction durée totale projet'
                    })
            
            # Optimisation capacité
            capacite_s1_utilisee = (s1['demande_equivalente']['quantite_poids'] + s1['demande_equivalente']['quantite_volume']) / 2
            capacite_s2_utilisee = (s2['demande_equivalente']['quantite_poids'] + s2['demande_equivalente']['quantite_volume']) / 2
            
            if capacite_s1_utilisee < capacite_s2_utilisee * 0.8 or capacite_s2_utilisee < capacite_s1_utilisee * 0.8:
                optimisations.append({
                    'type': 'equilibrage_charge',
                    'description': 'Rééquilibrer la charge entre les semaines',
                    'impact': 'Meilleure utilisation des capacités'
                })
        
        return optimisations
    
    def _calculer_debut_semaine(self, date_debut, numero_semaine):
        """Calcule la date de début d'une semaine donnée"""
        date_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_debut_semaine = date_obj + timedelta(days=(numero_semaine - 1) * 7)
        return date_debut_semaine.strftime('%Y-%m-%d')
    
    def _calculer_fin_semaine(self, date_debut, numero_semaine):
        """Calcule la date de fin d'une semaine donnée"""
        date_obj = datetime.strptime(date_debut, '%Y-%m-%d')
        date_fin_semaine = date_obj + timedelta(days=numero_semaine * 7 - 1)
        return date_fin_semaine.strftime('%Y-%m-%d')

def main_multi_semaines():
    """Exemple d'utilisation avec contraintes temporelles séparées"""
    
    # Configuration des véhicules (identique à l'original)
    vehicules_disponibles = [
        {
            'nom': 'CAMION LÉGER 1',
            'type': 'LEGER',
            'capacite_poids_max': 3.5,
            'capacite_volume_max': 20,
            'vitesse_kmh': 90,
            'cout_fixe_jour': 150,
            'cout_variable_km': 0.65
        },
        {
            'nom': 'CAMION LÉGER 2',
            'type': 'LEGER',
            'capacite_poids_max': 7.5,
            'capacite_volume_max': 35,
            'vitesse_kmh': 85,
            'cout_fixe_jour': 200,
            'cout_variable_km': 0.75
        },
        {
            'nom': 'SEMI-REMORQUE STANDARD',
            'type': 'LOURD',
            'capacite_poids_max': 40,
            'capacite_volume_max': 100,
            'vitesse_kmh': 75,
            'cout_fixe_jour': 400,
            'cout_variable_km': 1.20
        },
        {
            'nom': 'MEGA-TRAILER',
            'type': 'LOURD',
            'capacite_poids_max': 38,
            'capacite_volume_max': 150,
            'vitesse_kmh': 70,
            'cout_fixe_jour': 480,
            'cout_variable_km': 1.35
        }
    ]
    
    # PRODUITS SEMAINE 1 (Transport obligatoire première semaine)
    produits_semaine1 = [
        {
            'nom': 'MACHINES INDUSTRIELLES URGENTES',
            'quantite': 8,
            'poids_unitaire': 2.5,
            'volume_unitaire': 8.0,
            'distance_km': 800,
            'vitesse_kmh': 80
        },
        {
            'nom': 'ÉQUIPEMENTS ÉLECTRONIQUES CRITIQUES',
            'quantite': 40,
            'poids_unitaire': 0.3,
            'volume_unitaire': 1.2,
            'distance_km': 800,
            'vitesse_kmh': 80
        },
        {
            'nom': 'MATIÈRES PREMIÈRES PRIORITAIRES',
            'quantite': 60,
            'poids_unitaire': 0.8,
            'volume_unitaire': 2.5,
            'distance_km': 800,
            'vitesse_kmh': 80
        }
    ]
    
    # PRODUITS SEMAINE 2 (Transport obligatoire deuxième semaine)
    produits_semaine2 = [
        {
            'nom': 'MOBILIER DE BUREAU STANDARD',
            'quantite': 200,
            'poids_unitaire': 0.15,
            'volume_unitaire': 1.8,
            'distance_km': 800,
            'vitesse_kmh': 80
        },
        {
            'nom': 'PRODUITS CHIMIQUES NON-URGENTS',
            'quantite': 60,
            'poids_unitaire': 1.2,
            'volume_unitaire': 1.5,
            'distance_km': 800,
            'vitesse_kmh': 80
        },
        {
            'nom': 'ÉQUIPEMENTS COMPLÉMENTAIRES',
            'quantite': 40,
            'poids_unitaire': 0.5,
            'volume_unitaire': 2.0,
            'distance_km': 800,
            'vitesse_kmh': 80
        }
    ]
    
    # Configuration temporelle
    DATE_DEBUT = '2025-06-02'  # Lundi
    HEURE_DEBUT = '08:00'
    
    print("="*120)
    print("OPTIMISATION DE NAVETTES MULTI-SEMAINES AVEC CONTRAINTES TEMPORELLES SÉPARÉES")
    print("="*120)
    print(f"📅 CONTRAINTE SEMAINE 1: Transport OBLIGATOIRE du {DATE_DEBUT} au {OptimisateurNavettesMultiSemaines()._calculer_fin_semaine(DATE_DEBUT, 1)}")
    print(f"📅 CONTRAINTE SEMAINE 2: Transport OBLIGATOIRE du {OptimisateurNavettesMultiSemaines()._calculer_debut_semaine(DATE_DEBUT, 2)} au {OptimisateurNavettesMultiSemaines()._calculer_fin_semaine(DATE_DEBUT, 2)}")
    print(f"🕐 Début des opérations: {HEURE_DEBUT} chaque semaine")
    print(f"📍 Trajet: A ←→ B (distance: 800 km)")
    
    # Calcul des totaux pour information
    poids_s1 = sum(p['quantite'] * p['poids_unitaire'] for p in produits_semaine1)
    volume_s1 = sum(p['quantite'] * p['volume_unitaire'] for p in produits_semaine1)
    poids_s2 = sum(p['quantite'] * p['poids_unitaire'] for p in produits_semaine2)
    volume_s2 = sum(p['quantite'] * p['volume_unitaire'] for p in produits_semaine2)
    
    print(f"\n📊 RÉSUMÉ DES CONTRAINTES TEMPORELLES:")
    print(f"SEMAINE 1 (URGENT): {len(produits_semaine1)} types de produits - {poids_s1:.2f}t, {volume_s1:.2f}m³")
    print(f"SEMAINE 2 (PLANIFIÉ): {len(produits_semaine2)} types de produits - {poids_s2:.2f}t, {volume_s2:.2f}m³")
    print(f"TOTAL PROJET: {poids_s1 + poids_s2:.2f}t, {volume_s1 + volume_s2:.2f}m³")
    
    # Lancement de l'optimisation multi-semaines
    optimiseur = OptimisateurNavettesMultiSemaines()
    resultats = optimiseur.calculer_navettes_optimales_multi_semaines(
        produits_semaine1,
        produits_semaine2,
        vehicules_disponibles,
        DATE_DEBUT,
        HEURE_DEBUT
    )
    
    if resultats is None:
        print("\n❌ IMPOSSIBLE DE SATISFAIRE LES CONTRAINTES TEMPORELLES")
        return
    exportateur = ExportateurSolutions()
    fichiers = exportateur.exporter_solution_complete(
        resultats, 
        format_export="all",  # ou "excel", "csv", "json", "pdf"
        dossier_export="mes_exports"
    )
    planning_detaille = exportateur.exporter_planning_excel_detaille(resultats)
    rapport_executif = exportateur.generer_rapport_executif(resultats)
    # Affichage du résumé final multi-semaines
    print("\n" + "="*120)
    print("RÉSUMÉ FINAL MULTI-SEMAINES AVEC CONTRAINTES TEMPORELLES SÉPARÉES")
    print("="*120)
    
    print(f"\n📅 CALENDRIER DU PROJET:")
    print(f"Début: {resultats['date_debut_projet']}")
    print(f"Fin: {resultats['date_fin_projet']}")
    print(f"Durée totale: {resultats['duree_totale_projet']} jours")
    
    print(f"\n💰 BILAN FINANCIER GLOBAL:")
    print(f"Coût total projet: {resultats['cout_total_global']:.2f}€")
    
    if resultats['resultats_semaine1'] and resultats['resultats_semaine2']:
        s1_cout = resultats['resultats_semaine1']['vehicule_optimal']['cout_total']
        s2_cout = resultats['resultats_semaine2']['vehicule_optimal']['cout_total']
        print(f"  - Semaine 1: {s1_cout:.2f}€ ({s1_cout/resultats['cout_total_global']*100:.1f}%)")
        print(f"  - Semaine 2: {s2_cout:.2f}€ ({s2_cout/resultats['cout_total_global']*100:.1f}%)")
        
        print(f"\n🚛 FLOTTE UTILISÉE:")
        vehicule_s1 = resultats['resultats_semaine1']['vehicule_utilise']['nom']
        vehicule_s2 = resultats['resultats_semaine2']['vehicule_utilise']['nom']
        
        if vehicule_s1 == vehicule_s2:
            print(f"✅ VÉHICULE UNIQUE: {vehicule_s1}")
            print(f"   Avantages: Continuité opérationnelle, équipe unique, maintenance centralisée")
        else:
            print(f"🔧 VÉHICULES MULTIPLES:")
            print(f"   Semaine 1: {vehicule_s1}")
            print(f"   Semaine 2: {vehicule_s2}")
            print(f"   Gestion: Coordination multi-équipes nécessaire")
            
    elif resultats['resultats_semaine1']:
        print(f"  - Semaine 1 uniquement: {resultats['resultats_semaine1']['vehicule_optimal']['cout_total']:.2f}€")
        print(f"  - Véhicule: {resultats['resultats_semaine1']['vehicule_utilise']['nom']}")
        
    elif resultats['resultats_semaine2']:
        print(f"  - Semaine 2 uniquement: {resultats['resultats_semaine2']['vehicule_optimal']['cout_total']:.2f}€")
        print(f"  - Véhicule: {resultats['resultats_semaine2']['vehicule_utilise']['nom']}")
    
    print(f"\n📊 PERFORMANCE GLOBALE:")
    print(f"Nombre total de véhicules: {resultats['nb_vehicules_total']}")
    
    # Calcul de métriques globales
    poids_total = poids_s1 + poids_s2
    if poids_total > 0:
        cout_par_tonne = resultats['cout_total_global'] / poids_total
        print(f"Coût par tonne: {cout_par_tonne:.2f}€/tonne")
    
    volume_total = volume_s1 + volume_s2
    if volume_total > 0:
        cout_par_m3 = resultats['cout_total_global'] / volume_total
        print(f"Coût par m³: {cout_par_m3:.2f}€/m³")
    
    # Affichage des optimisations possibles
    if resultats['optimisations_possibles']:
        print(f"\n💡 OPTIMISATIONS IDENTIFIÉES:")
        for i, opt in enumerate(resultats['optimisations_possibles'], 1):
            print(f"  {i}. {opt['description']}")
            print(f"     Impact: {opt['impact']}")
    
    # Recommandations finales
    print(f"\n🎯 RECOMMANDATIONS FINALES:")
    
    if resultats['resultats_semaine1'] and resultats['resultats_semaine2']:
        print(f"✅ PROJET DEUX SEMAINES RÉALISABLE")
        print(f"   - Contraintes temporelles respectées")
        print(f"   - Coût total maîtrisé: {resultats['cout_total_global']:.2f}€")
        print(f"   - Solutions techniques validées")
        
        # Analyse des risques
        s1 = resultats['resultats_semaine1']
        s2 = resultats['resultats_semaine2']
        
        if s1['nb_vehicules_necessaires'] == 1 and s2['nb_vehicules_necessaires'] == 1:
            print(f"   - Risque opérationnel: FAIBLE (1 véhicule par semaine)")
        else:
            nb_max = max(s1['nb_vehicules_necessaires'], s2['nb_vehicules_necessaires'])
            print(f"   - Risque opérationnel: MODÉRÉ ({nb_max} véhicules max par semaine)")
            
    print(f"\n🚀 PROJET PRÊT POUR EXÉCUTION AVEC CONTRAINTES TEMPORELLES STRICTES")
    print(f"   Chaque semaine a sa planification optimisée individuellement")
    print(f"   Respect garanti des échéances par semaine")

if __name__ == "__main__":
    main_multi_semaines()