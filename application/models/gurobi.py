import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import math
import numpy as np
from datetime import datetime, timedelta

def create_transport_optimization_model():
    """
    Modèle d'optimisation de transport multi-véhicules avec contraintes temporelles
    Basé sur la modélisation mathématique fournie
    """
    
    print("🚀 INITIALISATION DU MODÈLE D'OPTIMISATION TRANSPORT")
    print("=" * 80)
    
    # Création du modèle
    model = pyo.ConcreteModel()
    
    # =================================================================
    # DONNÉES D'ENTRÉE (basées sur votre exemple)
    # =================================================================
    
    # Types de véhicules disponibles
    vehicle_types = {
        'LEGER': {
            'vehicles': ['LEGER-001', 'LEGER-002'],
            'fixed_cost': 250,  # €/jour
            'variable_cost': 1.2,  # €/km
            'capacities': {
                'LEGER-001': {'weight': 12, 'volume': 30, 'speed': 90},
                'LEGER-002': {'weight': 15, 'volume': 35, 'speed': 85}
            }
        },
        'MOYEN': {
            'vehicles': ['MOYEN-001'],
            'fixed_cost': 350,  # €/jour
            'variable_cost': 1.5,  # €/km
            'capacities': {
                'MOYEN-001': {'weight': 25, 'volume': 60, 'speed': 80}
            }
        },
        'LOURD': {
            'vehicles': ['SEMI-REMORQUE-001', 'SEMI-REMORQUE-002'],
            'fixed_cost': 500,  # €/jour
            'variable_cost': 2.4,  # €/km
            'capacities': {
                'SEMI-REMORQUE-001': {'weight': 40, 'volume': 100, 'speed': 75},
                'SEMI-REMORQUE-002': {'weight': 35, 'volume': 90, 'speed': 70}
            }
        }
    }
    
    # Produits à transporter
    products = {
        'MACHINES': {
            'quantity': 8,
            'unit_weight': 2.5,  # tonnes/unité
            'unit_volume': 8.0   # m³/unité
        },
        'ELECTRONIQUES': {
            'quantity': 40,
            'unit_weight': 0.3,  # tonnes/unité
            'unit_volume': 1.2   # m³/unité
        },
        'MATIERES': {
            'quantity': 60,
            'unit_weight': 0.8,  # tonnes/unité
            'unit_volume': 2.5   # m³/unité
        }
    }
    
    # Paramètres temporels et logistiques
    params = {
        'distance': 800,  # km
        'loading_time': 1.5,  # heures
        'unloading_time': 1.5,  # heures
        'work_time_per_day': 8.0,  # heures
        'break_duration': 0.25,  # heures
        'night_stop_duration': 13.0,  # heures (19h→8h)
        'max_project_duration': 7,  # jours
        'max_continuous_driving': 2.0  # heures
    }
    
    print(f"📊 DONNÉES DU PROBLÈME:")
    print(f"   • Types de véhicules: {len(vehicle_types)}")
    print(f"   • Véhicules individuels: {sum(len(vt['vehicles']) for vt in vehicle_types.values())}")
    print(f"   • Produits à transporter: {len(products)}")
    print(f"   • Distance A→B: {params['distance']} km")
    print(f"   • Durée max projet: {params['max_project_duration']} jours")
    print()
    
    # =================================================================
    # ENSEMBLES (SETS)
    # =================================================================
    
    # Types de véhicules
    model.L = pyo.Set(initialize=list(vehicle_types.keys()))
    
    # Véhicules individuels par type
    model.K = pyo.Set(dimen=2, initialize=[
        (vtype, vid) for vtype, data in vehicle_types.items() 
        for vid in data['vehicles']
    ])
    
    # Produits
    model.P = pyo.Set(initialize=list(products.keys()))
    
    # Voyages (estimé max 10 voyages)
    max_trips = 3
    model.T = pyo.Set(initialize=range(1, max_trips + 1))
    
    print(f"🔧 ENSEMBLES CRÉÉS:")
    print(f"   • Types véhicules (L): {list(model.L)}")
    print(f"   • Véhicules individuels (K): {len(model.K)} véhicules")
    print(f"   • Produits (P): {list(model.P)}")
    print(f"   • Voyages max (T): {max_trips}")
    print()
    
    # =================================================================
    # PARAMÈTRES
    # =================================================================
    
    # Quantités de produits
    model.q = pyo.Param(model.P, initialize={
        p: data['quantity'] for p, data in products.items()
    })
    
    # Poids et volumes unitaires
    model.w = pyo.Param(model.P, initialize={
        p: data['unit_weight'] for p, data in products.items()
    })
    
    model.v = pyo.Param(model.P, initialize={
        p: data['unit_volume'] for p, data in products.items()
    })
    
    # Capacités des véhicules individuels
    model.Cw = pyo.Param(model.K, initialize={
        (vtype, vid): vehicle_types[vtype]['capacities'][vid]['weight']
        for vtype, vid in model.K
    })
    
    model.Cv = pyo.Param(model.K, initialize={
        (vtype, vid): vehicle_types[vtype]['capacities'][vid]['volume']
        for vtype, vid in model.K
    })
    
    model.S = pyo.Param(model.K, initialize={
        (vtype, vid): vehicle_types[vtype]['capacities'][vid]['speed']
        for vtype, vid in model.K
    })
    
    # Coûts par type
    model.F = pyo.Param(model.L, initialize={
        vtype: data['fixed_cost'] for vtype, data in vehicle_types.items()
    })
    
    model.G = pyo.Param(model.L, initialize={
        vtype: data['variable_cost'] for vtype, data in vehicle_types.items()
    })
    
    # Paramètres constants
    model.D = pyo.Param(initialize=params['distance'])
    model.T_load = pyo.Param(initialize=params['loading_time'])
    model.T_unload = pyo.Param(initialize=params['unloading_time'])
    model.T_work = pyo.Param(initialize=params['work_time_per_day'])
    model.T_break = pyo.Param(initialize=params['break_duration'])
    model.T_night = pyo.Param(initialize=params['night_stop_duration'])
    model.H_max = pyo.Param(initialize=params['max_project_duration'])
    
    print(f"📈 PARAMÈTRES INITIALISÉS:")
    print(f"   • Quantités totales: {sum(pyo.value(model.q[p]) for p in model.P)} unités")
    print(f"   • Poids total: {sum(pyo.value(model.q[p] * model.w[p]) for p in model.P):.1f} tonnes")
    print(f"   • Volume total: {sum(pyo.value(model.q[p] * model.v[p]) for p in model.P):.1f} m³")
    print()
    
    # =================================================================
    # VARIABLES DE DÉCISION
    # =================================================================
    
    # Sélection des véhicules individuels
    model.x = pyo.Var(model.K, domain=pyo.Binary)
    
    # Types de véhicules utilisés
    model.u = pyo.Var(model.L, domain=pyo.Binary)
    
    # Nombre d'unités de chaque véhicule
    model.n = pyo.Var(model.K, domain=pyo.NonNegativeIntegers)
    
    # Nombre de voyages par véhicule
    model.m = pyo.Var(model.K, domain=pyo.NonNegativeIntegers)
    
    # Quantité transportée
    model.y = pyo.Var(model.P, model.T, model.K, domain=pyo.NonNegativeIntegers)
    
    # Durée d'utilisation
    model.tau = pyo.Var(model.K, domain=pyo.NonNegativeReals)
    
    # Variables auxiliaires pour les temps
    model.T_driving = pyo.Var(model.K, model.T, domain=pyo.NonNegativeReals)
    model.T_breaks = pyo.Var(model.K, model.T, domain=pyo.NonNegativeReals)
    model.T_nights = pyo.Var(model.K, model.T, domain=pyo.NonNegativeReals)
    model.T_total_trip = pyo.Var(model.K, model.T, domain=pyo.NonNegativeReals)
    
    # Nombre de pauses et nuits
    model.N_breaks = pyo.Var(model.K, model.T, domain=pyo.NonNegativeIntegers)
    model.N_nights = pyo.Var(model.K, model.T, domain=pyo.Binary)
    
    print(f"🔧 VARIABLES CRÉÉES:")
    print(f"   • Variables binaires: {len(model.x) + len(model.u)} variables")
    print(f"   • Variables entières: {len(model.n) + len(model.m) + len(model.y)} variables")
    print(f"   • Variables continues: {len(model.tau) + len(model.T_driving)} variables")
    print()
    
    # =================================================================
    # FONCTION OBJECTIF
    # =================================================================
    
    def objective_rule(model):
        fixed_costs = sum(
            model.n[l, k] * model.tau[l, k] * model.F[l] 
            for l, k in model.K
        )
        
        variable_costs = sum(
            model.m[l, k] * model.n[l, k] * (2 * model.D) * model.G[l]
            for l, k in model.K
        )
        
        return fixed_costs + variable_costs
    
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
    
    print("🎯 FONCTION OBJECTIF: Minimisation des coûts totaux (fixes + variables)")
    print()
    
    # =================================================================
    # CONTRAINTES
    # =================================================================
    
    print("⚙️ CRÉATION DES CONTRAINTES...")
    
    # 1. Contraintes de cohérence type/véhicule (corrigées)
    def type_consistency_rule1(model, l):
        # Si un véhicule de type l est utilisé, alors u[l] = 1
        vehicles_of_type = [k for lt, k in model.K if lt == l]
        if not vehicles_of_type:
            return pyo.Constraint.Skip
        return model.u[l] >= sum(model.x[l, k] for k in vehicles_of_type) / len(vehicles_of_type)
    
    def type_consistency_rule2(model, l):
        # u[l] ne peut être 1 que si au moins un véhicule de type l est utilisé
        vehicles_of_type = [k for lt, k in model.K if lt == l]
        if not vehicles_of_type:
            return pyo.Constraint.Skip
        return model.u[l] <= sum(model.x[l, k] for k in vehicles_of_type)
    
    model.type_consistency1 = pyo.Constraint(model.L, rule=type_consistency_rule1)
    model.type_consistency2 = pyo.Constraint(model.L, rule=type_consistency_rule2)
    
    # 2. Contrainte de sélection d'au moins un véhicule
    def min_vehicle_rule(model):
        return sum(model.u[l] for l in model.L) >= 1
    
    model.min_vehicle = pyo.Constraint(rule=min_vehicle_rule)
    
    # 3. Contraintes de capacité par voyage (corrigées)
    def weight_capacity_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        return sum(model.y[p, t, l, k] * model.w[p] for p in model.P) <= model.Cw[l, k] * model.x[l, k]
    
    def volume_capacity_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        return sum(model.y[p, t, l, k] * model.v[p] for p in model.P) <= model.Cv[l, k] * model.x[l, k]
    
    model.weight_capacity = pyo.Constraint(model.K, model.T, rule=weight_capacity_rule)
    model.volume_capacity = pyo.Constraint(model.K, model.T, rule=volume_capacity_rule)
    
    # 4. Satisfaction de la demande
    def demand_satisfaction_rule(model, p):
        return sum(model.y[p, t, l, k] for t in model.T for l, k in model.K) == model.q[p]
    
    model.demand_satisfaction = pyo.Constraint(model.P, rule=demand_satisfaction_rule)
    
    # 5. Calcul du temps de conduite (simplifié)
    def driving_time_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        # Temps de conduite = 2*D/S si le voyage est utilisé
        total_load = sum(model.y[p, t, l, k] for p in model.P)
        # Approximation: si total_load > 0, alors temps = 2*D/S
        return model.T_driving[l, k, t] <= (2 * model.D / model.S[l, k])
    
    def driving_time_activation_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        # Si pas de charge, temps de conduite = 0
        total_load = sum(model.y[p, t, l, k] for p in model.P)
        M = 1000  # Grande constante
        return model.T_driving[l, k, t] <= M * (sum(model.y[p, t, l, k] for p in model.P) / max(1, sum(pyo.value(model.q[p]) for p in model.P)))
    
    model.driving_time = pyo.Constraint(model.K, model.T, rule=driving_time_rule)
    model.driving_activation = pyo.Constraint(model.K, model.T, rule=driving_time_activation_rule)
    
    # 6. Calcul simplifié des pauses (approximation)
    def breaks_calculation_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        # Approximation: 1 pause toutes les 2h, temps total / 2
        return model.N_breaks[l, k, t] * model.T_break == model.T_breaks[l, k, t]
    
    def breaks_number_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        # Approximation linéaire du nombre de pauses
        return model.N_breaks[l, k, t] <= model.T_driving[l, k, t] / 2
    
    model.breaks_calc = pyo.Constraint(model.K, model.T, rule=breaks_calculation_rule)
    model.breaks_number = pyo.Constraint(model.K, model.T, rule=breaks_number_rule)
    
    # 7. Calcul des arrêts nocturnes (simplifié)
    def night_stops_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        return model.T_nights[l, k, t] == model.N_nights[l, k, t] * model.T_night
    
    def night_detection_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        # Si temps total > seuil (disons 10h), nuit nécessaire
        total_time = model.T_driving[l, k, t] + model.T_breaks[l, k, t] + model.T_load + model.T_unload
        # Approximation linéaire: N_nights = 1 si total_time > 10
        return model.N_nights[l, k, t] * 10 >= total_time - 10
    
    def night_upper_bound_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        total_time = model.T_driving[l, k, t] + model.T_breaks[l, k, t] + model.T_load + model.T_unload
        return model.N_nights[l, k, t] <= total_time / 8  # Si > 8h de travail, nuit possible
    
    model.night_stops = pyo.Constraint(model.K, model.T, rule=night_stops_rule)
    model.night_detection = pyo.Constraint(model.K, model.T, rule=night_detection_rule)
    model.night_upper = pyo.Constraint(model.K, model.T, rule=night_upper_bound_rule)
    
    # 8. Temps total par voyage
    def total_trip_time_rule(model, l, k, t):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        return (model.T_total_trip[l, k, t] == 
                model.T_driving[l, k, t] + model.T_breaks[l, k, t] + 
                model.T_nights[l, k, t] + model.T_load + model.T_unload)
    
    model.total_trip_time = pyo.Constraint(model.K, model.T, rule=total_trip_time_rule)
    
    # 9. Calcul du nombre de voyages nécessaires (simplifié)
    def trip_count_rule(model, l, k):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        # Le nombre de voyages doit être au moins égal au nombre de voyages avec charge
        total_transported = sum(model.y[p, t, l, k] for p in model.P for t in model.T)
        # Approximation: au moins 1 voyage si véhicule sélectionné et charge > 0
        return model.m[l, k] >= model.x[l, k]
    
    def trip_count_upper_rule(model, l, k):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        # Limite supérieure basée sur la capacité
        return model.m[l, k] <= len(model.T) * model.x[l, k]
    
    model.trip_count = pyo.Constraint(model.K, rule=trip_count_rule)
    model.trip_upper = pyo.Constraint(model.K, rule=trip_count_upper_rule)
    
    # 10. Calcul de la durée totale par véhicule
    def vehicle_duration_rule(model, l, k):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        total_time = sum(model.T_total_trip[l, k, t] for t in model.T)
        return model.tau[l, k] >= total_time / model.T_work
    
    model.vehicle_duration = pyo.Constraint(model.K, rule=vehicle_duration_rule)
    
    # 11. Contrainte temporelle maximale
    def max_duration_rule(model, l, k):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        return model.tau[l, k] <= model.H_max * model.x[l, k]
    
    model.max_duration = pyo.Constraint(model.K, rule=max_duration_rule)
    
    # 12. Calcul du nombre d'unités nécessaires
    def vehicle_units_rule(model, l, k):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        return model.n[l, k] >= model.x[l, k]
    
    model.vehicle_units = pyo.Constraint(model.K, rule=vehicle_units_rule)
    
    print(f"✅ CONTRAINTES CRÉÉES:")
    print(f"   • Contraintes de cohérence: {len(model.type_consistency1) + len(model.type_consistency2)}")
    print(f"   • Contraintes de capacité: {len(model.weight_capacity) + len(model.volume_capacity)}")
    print(f"   • Contraintes de demande: {len(model.demand_satisfaction)}")
    print(f"   • Contraintes temporelles: {len(model.driving_time) + len(model.max_duration)}")
    print()
    
    return model

def solve_model(model):
    """
    Résolution du modèle avec Gurobi
    """
    
    print("🔍 RÉSOLUTION DU MODÈLE...")
    print("=" * 80)
    
    # Configuration du solveur Gurobi (licence gratuite)
    solver = pyo.SolverFactory('gurobi')
    
    # Options pour licence gratuite Gurobi
    solver.options['TimeLimit'] = 300  # 5 minutes max
    solver.options['MIPGap'] = 0.02    # 2% de gap acceptable
    solver.options['Threads'] = 2      # Max 2 threads pour licence gratuite
    solver.options['NodeMethod'] = 1   # Dual simplex
    solver.options['MIPFocus'] = 1     # Focus sur faisabilité
    
    print("⚙️ CONFIGURATION SOLVEUR:")
    print(f"   • Solveur: Gurobi (licence gratuite)")
    print(f"   • Limite temps: 300 secondes")
    print(f"   • Gap tolérance: 2%")
    print(f"   • Threads: 2")
    print()
    
    # Résolution
    print("🚀 LANCEMENT DE LA RÉSOLUTION...")
    start_time = datetime.now()
    
    try:
        results = solver.solve(model, tee=True)
        solve_time = datetime.now() - start_time
        
        print(f"⏱️ TEMPS DE RÉSOLUTION: {solve_time.total_seconds():.2f} secondes")
        print()
        
        # Vérification du statut
        if (results.solver.status == SolverStatus.ok and 
            results.solver.termination_condition == TerminationCondition.optimal):
            
            print("✅ SOLUTION OPTIMALE TROUVÉE!")
            return results, True
            
        elif results.solver.termination_condition == TerminationCondition.feasible:
            print("✅ SOLUTION RÉALISABLE TROUVÉE!")
            return results, True
            
        else:
            print("❌ AUCUNE SOLUTION TROUVÉE!")
            print(f"   Statut: {results.solver.status}")
            print(f"   Condition: {results.solver.termination_condition}")
            return results, False
            
    except Exception as e:
        print(f"❌ ERREUR LORS DE LA RÉSOLUTION: {e}")
        return None, False

def print_detailed_solution(model, results):
    """
    Affichage détaillé de la solution
    """
    
    print("📊 ANALYSE DÉTAILLÉE DE LA SOLUTION")
    print("=" * 80)
    
    # Coût total
    total_cost = pyo.value(model.obj)
    print(f"💰 COÛT TOTAL OPTIMAL: {total_cost:.2f}€")
    
    # Décomposition des coûts
    fixed_costs = sum(
        pyo.value(model.n[l, k] * model.tau[l, k] * model.F[l]) 
        for l, k in model.K if pyo.value(model.x[l, k]) > 0.5
    )
    
    variable_costs = sum(
        pyo.value(model.m[l, k] * model.n[l, k] * (2 * model.D) * model.G[l])
        for l, k in model.K if pyo.value(model.x[l, k]) > 0.5
    )
    
    print(f"   • Coûts fixes: {fixed_costs:.2f}€ ({100*fixed_costs/total_cost:.1f}%)")
    print(f"   • Coûts variables: {variable_costs:.2f}€ ({100*variable_costs/total_cost:.1f}%)")
    print()
    
    # Véhicules sélectionnés
    selected_vehicles = [(l, k) for l, k in model.K if pyo.value(model.x[l, k]) > 0.5]
    print(f"🚛 VÉHICULES SÉLECTIONNÉS: {len(selected_vehicles)}")
    
    for l, k in selected_vehicles:
        n_units = pyo.value(model.n[l, k])
        n_trips = pyo.value(model.m[l, k])
        duration = pyo.value(model.tau[l, k])
        
        print(f"   • {k} (Type: {l})")
        print(f"     - Unités utilisées: {n_units}")
        print(f"     - Voyages: {n_trips}")
        print(f"     - Durée: {duration:.1f} jours")
        print(f"     - Capacités: {pyo.value(model.Cw[l, k])}t, {pyo.value(model.Cv[l, k])}m³")
        print()
    
    # Types utilisés
    used_types = [l for l in model.L if pyo.value(model.u[l]) > 0.5]
    print(f"📋 TYPES DE VÉHICULES UTILISÉS: {used_types}")
    print()
    
    # Répartition des produits
    print("📦 RÉPARTITION DES PRODUITS PAR VOYAGE:")
    
    for l, k in selected_vehicles:
        print(f"\n--- VÉHICULE {k} (Type: {l}) ---")
        
        for t in model.T:
            trip_load = sum(pyo.value(model.y[p, t, l, k]) for p in model.P)
            if trip_load > 0:
                print(f"  Voyage {t}:")
                
                total_weight = 0
                total_volume = 0
                
                for p in model.P:
                    qty = pyo.value(model.y[p, t, l, k])
                    if qty > 0:
                        weight = qty * pyo.value(model.w[p])
                        volume = qty * pyo.value(model.v[p])
                        total_weight += weight
                        total_volume += volume
                        
                        print(f"    • {p}: {qty} unités ({weight:.1f}t, {volume:.1f}m³)")
                
                cap_w = pyo.value(model.Cw[l, k])
                cap_v = pyo.value(model.Cv[l, k])
                
                print(f"    Total: {total_weight:.1f}t/{cap_w}t ({100*total_weight/cap_w:.1f}%), " +
                      f"{total_volume:.1f}m³/{cap_v}m³ ({100*total_volume/cap_v:.1f}%)")
    
    print()
    
    # Vérification satisfaction demande
    print("🔍 VÉRIFICATION SATISFACTION DEMANDE:")
    all_satisfied = True
    
    for p in model.P:
        demanded = pyo.value(model.q[p])
        transported = sum(pyo.value(model.y[p, t, l, k]) 
                        for t in model.T for l, k in model.K)
        
        status = "✅" if abs(transported - demanded) < 0.001 else "❌"
        print(f"   {status} {p}: {transported}/{demanded} unités")
        
        if abs(transported - demanded) >= 0.001:
            all_satisfied = False
    
    if all_satisfied:
        print("🎉 TOUTES LES DEMANDES SONT SATISFAITES!")
    else:
        print("⚠️ CERTAINES DEMANDES NE SONT PAS SATISFAITES!")
    
    print()
    
    # Métriques de performance
    total_weight = sum(pyo.value(model.q[p] * model.w[p]) for p in model.P)
    total_volume = sum(pyo.value(model.q[p] * model.v[p]) for p in model.P)
    total_trips = sum(pyo.value(model.m[l, k]) for l, k in selected_vehicles)
    
    print("📈 MÉTRIQUES DE PERFORMANCE:")
    print(f"   • Coût par tonne: {total_cost/total_weight:.2f}€/t")
    print(f"   • Coût par m³: {total_cost/total_volume:.2f}€/m³")
    print(f"   • Voyages totaux: {total_trips}")
    print(f"   • Utilisation moyenne: {total_weight/total_trips:.1f}t/voyage")
    
    # Contrainte temporelle
    max_duration = max(pyo.value(model.tau[l, k]) for l, k in selected_vehicles)
    max_allowed = pyo.value(model.H_max)
    
    print(f"   • Durée max utilisée: {max_duration:.1f}/{max_allowed} jours")
    
    if max_duration <= max_allowed:
        print("   ✅ Contrainte temporelle respectée!")
    else:
        print("   ⚠️ Contrainte temporelle dépassée!")
    
    print()

def main():
    """
    Fonction principale d'exécution
    """
    
    print("🚀 OPTIMISATION DE TRANSPORT MULTI-VÉHICULES")
    print("=" * 80)
    print(f"🕐 Début d'exécution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. Création du modèle
        print("📋 ÉTAPE 1: CRÉATION DU MODÈLE")
        print("-" * 40)
        model = create_transport_optimization_model()
        
        # Statistiques du modèle
        print("📊 STATISTIQUES DU MODÈLE:")
        
        # Compter les variables de façon correcte pour Pyomo
        total_vars = 0
        binary_vars = 0
        integer_vars = 0
        continuous_vars = 0
        
        for v in model.component_objects(pyo.Var):
            if v.is_indexed():
                # Pour les variables indexées, compter chaque élément
                for index in v:
                    total_vars += 1
                    # Vérifier le domaine via les attributs de la variable
                    if hasattr(v[index], 'domain') and v[index].domain is pyo.Binary:
                        binary_vars += 1
                    elif hasattr(v[index], 'domain') and v[index].domain is pyo.NonNegativeIntegers:
                        integer_vars += 1
                    elif hasattr(v[index], 'domain') and v[index].domain is pyo.NonNegativeReals:
                        continuous_vars += 1
                    else:
                        # Déterminer le type par le nom de la variable
                        var_name = v.name
                        if var_name in ['x', 'u', 'N_nights']:
                            binary_vars += 1
                        elif var_name in ['n', 'm', 'y', 'N_breaks']:
                            integer_vars += 1
                        else:
                            continuous_vars += 1
            else:
                # Pour les variables scalaires
                total_vars += 1
                if hasattr(v, 'domain') and v.domain is pyo.Binary:
                    binary_vars += 1
                elif hasattr(v, 'domain') and v.domain is pyo.NonNegativeIntegers:
                    integer_vars += 1
                else:
                    continuous_vars += 1
        
        # Compter les contraintes
        num_constraints = sum(1 for c in model.component_objects(pyo.Constraint))
        
        print(f"   • Variables totales: {total_vars}")
        print(f"   • Variables binaires: {binary_vars}")
        print(f"   • Variables entières: {integer_vars}")
        print(f"   • Variables continues: {continuous_vars}")
        print(f"   • Contraintes: {num_constraints}")
        print()
        
        # 2. Résolution
        print("📋 ÉTAPE 2: RÉSOLUTION")
        print("-" * 40)
        results, success = solve_model(model)
        
        if not success:
            print("❌ Échec de la résolution!")
            return
        
        # 3. Analyse de la solution
        print("📋 ÉTAPE 3: ANALYSE DE LA SOLUTION")
        print("-" * 40)
        print_detailed_solution(model, results)
        
        # 4. Vérifications supplémentaires
        print("📋 ÉTAPE 4: VÉRIFICATIONS SUPPLÉMENTAIRES")
        print("-" * 40)
        
        # Vérification de la cohérence des coûts
        calculated_cost = 0
        for l, k in model.K:
            if pyo.value(model.x[l, k]) > 0.5:
                n_val = pyo.value(model.n[l, k])
                tau_val = pyo.value(model.tau[l, k])
                m_val = pyo.value(model.m[l, k])
                f_val = pyo.value(model.F[l])
                g_val = pyo.value(model.G[l])
                d_val = pyo.value(model.D)
                
                fixed = n_val * tau_val * f_val
                variable = m_val * n_val * (2 * d_val) * g_val
                calculated_cost += fixed + variable
                
                print(f"🧮 Coûts {k}:")
                print(f"   • Fixe: {n_val} × {tau_val:.1f} × {f_val} = {fixed:.2f}€")
                print(f"   • Variable: {m_val} × {n_val} × {2*d_val} × {g_val} = {variable:.2f}€")
        
        obj_value = pyo.value(model.obj)
        print(f"\n💰 Vérification coûts:")
        print(f"   • Coût calculé: {calculated_cost:.2f}€")
        print(f"   • Coût objectif: {obj_value:.2f}€")
        print(f"   • Différence: {abs(calculated_cost - obj_value):.2f}€")
        
        if abs(calculated_cost - obj_value) < 0.01:
            print("   ✅ Cohérence des coûts vérifiée!")
        else:
            print("   ⚠️ Incohérence dans les coûts!")
        
        print()
        
        # 5. Recommandations
        print("📋 ÉTAPE 5: RECOMMANDATIONS")
        print("-" * 40)
        
        selected_vehicles = [(l, k) for l, k in model.K if pyo.value(model.x[l, k]) > 0.5]
        
        if len(selected_vehicles) == 1:
            print("💡 STRATÉGIE OPTIMALE: Véhicule unique")
            print("   • Simplicité de gestion")
            print("   • Coûts fixes minimisés")
        else:
            print(f"💡 STRATÉGIE OPTIMALE: {len(selected_vehicles)} véhicules")
            print("   • Optimisation par capacités spécialisées")
            print("   • Parallélisation possible des opérations")
        
        # Analyse des goulots d'étranglement
        for l, k in selected_vehicles:
            cap_w = pyo.value(model.Cw[l, k])
            cap_v = pyo.value(model.Cv[l, k])
            
            # Calculer l'utilisation moyenne
            total_trips = pyo.value(model.m[l, k])
            if total_trips > 0:
                avg_weight = sum(
                    sum(pyo.value(model.y[p, t, l, k] * model.w[p]) for p in model.P)
                    for t in model.T
                ) / total_trips
                
                avg_volume = sum(
                    sum(pyo.value(model.y[p, t, l, k] * model.v[p]) for p in model.P)
                    for t in model.T
                ) / total_trips
                
                weight_usage = avg_weight / cap_w * 100
                volume_usage = avg_volume / cap_v * 100
                
                print(f"\n🔍 Analyse {k}:")
                print(f"   • Utilisation poids: {weight_usage:.1f}%")
                print(f"   • Utilisation volume: {volume_usage:.1f}%")
                
                if weight_usage > volume_usage + 10:
                    print("   ⚠️ Contrainte poids dominante")
                elif volume_usage > weight_usage + 10:
                    print("   ⚠️ Contrainte volume dominante")
                else:
                    print("   ✅ Utilisation équilibrée")
        
        # 6. Résumé final
        print("\n📋 RÉSUMÉ EXÉCUTIF")
        print("-" * 40)
        print(f"✅ Optimisation réussie!")
        print(f"💰 Coût total: {pyo.value(model.obj):.2f}€")
        print(f"🚛 Véhicules: {len(selected_vehicles)}")
        print(f"📦 Produits transportés: {sum(pyo.value(model.q[p]) for p in model.P)} unités")
        print(f"⚖️ Poids total: {sum(pyo.value(model.q[p] * model.w[p]) for p in model.P):.1f}t")
        print(f"📏 Volume total: {sum(pyo.value(model.q[p] * model.v[p]) for p in model.P):.1f}m³")
        
        max_duration = max(pyo.value(model.tau[l, k]) for l, k in selected_vehicles)
        print(f"⏱️ Durée projet: {max_duration:.1f} jours")
        
        # Solution summary dans un format structuré
        print("\n" + "="*80)
        print("📄 SOLUTION FINALE STRUCTURÉE")
        print("="*80)
        
        solution_data = {
            'optimal_cost': pyo.value(model.obj),
            'vehicles_used': len(selected_vehicles),
            'project_duration': max_duration,
            'total_trips': sum(pyo.value(model.m[l, k]) for l, k in selected_vehicles),
            'vehicles_details': []
        }
        
        for l, k in selected_vehicles:
            vehicle_info = {
                'id': k,
                'type': l,
                'units': pyo.value(model.n[l, k]),
                'trips': pyo.value(model.m[l, k]),
                'duration': pyo.value(model.tau[l, k]),
                'capacity_weight': pyo.value(model.Cw[l, k]),
                'capacity_volume': pyo.value(model.Cv[l, k]),
                'products_carried': {}
            }
            
            # Détail des produits transportés
            for p in model.P:
                total_qty = sum(pyo.value(model.y[p, t, l, k]) for t in model.T)
                if total_qty > 0:
                    vehicle_info['products_carried'][p] = {
                        'quantity': total_qty,
                        'weight': total_qty * pyo.value(model.w[p]),
                        'volume': total_qty * pyo.value(model.v[p])
                    }
            
            solution_data['vehicles_details'].append(vehicle_info)
        
        # Affichage structuré
        print(f"Coût optimal: {solution_data['optimal_cost']:.2f}€")
        print(f"Véhicules utilisés: {solution_data['vehicles_used']}")
        print(f"Durée projet: {solution_data['project_duration']:.1f} jours")
        print(f"Voyages totaux: {solution_data['total_trips']}")
        
        print(f"\n🕐 Fin d'exécution: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return model, results, solution_data
        
    except Exception as e:
        print(f"❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

# Point d'entrée principal
if __name__ == "__main__":
    # ... (vérifications et prints) ...
    result = main()
    if result is not None:
        model, results, solution = result
        print("\n🎉 EXÉCUTION TERMINÉE AVEC SUCCÈS!")
        # ... sauvegarde, etc ...
    else:
        print("\n❌ ÉCHEC DE L'EXÉCUTION!")
        exit(1)
    print("🔧 INSTALLATION REQUISE:")
    print("pip install pyomo")
    print("pip install gurobi")
    print("Licence Gurobi gratuite: https://www.gurobi.com/academia/academic-program-and-licenses/")
    print()
    
    # Vérification des dépendances
    try:
        import pyomo.environ as pyo
        print("✅ Pyomo installé")
    except ImportError:
        print("❌ Pyomo non installé: pip install pyomo")
        exit(1)
    
    try:
        solver = pyo.SolverFactory('gurobi')
        if solver.available():
            print("✅ Gurobi disponible")
        else:
            print("❌ Gurobi non disponible")
            print("   Alternatives: GLPK (pip install glpk), CBC, SCIP")
            
            # Tentative avec GLPK comme alternative
            solver_glpk = pyo.SolverFactory('glpk')
            if solver_glpk.available():
                print("✅ GLPK disponible comme alternative")
            else:
                print("❌ Aucun solveur disponible!")
                exit(1)
                
    except Exception as e:
        print(f"⚠️ Erreur vérification solveur: {e}")
    
    print("\n" + "="*80)
    
    # Exécution principale
    model, results, solution = main()
    
    if model is not None:
        print("\n🎉 EXÉCUTION TERMINÉE AVEC SUCCÈS!")
        
        # Sauvegarde optionnelle des résultats
        try:
            import json
            with open('transport_solution.json', 'w', encoding='utf-8') as f:
                json.dump(solution, f, indent=2, ensure_ascii=False)
            print("💾 Solution sauvegardée dans 'transport_solution.json'")
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde: {e}")
    else:
        print("\n❌ ÉCHEC DE L'EXÉCUTION!")
        exit(1)