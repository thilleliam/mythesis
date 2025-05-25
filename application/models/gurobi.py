import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import math
import numpy as np
from datetime import datetime, timedelta

def create_multi_week_transport_model():
    """
    Modèle d'optimisation de transport multi-semaines avec chargement intelligent
    Version simplifiée pour licence gratuite Pyomo/Gurobi
    """
    
    print("🚀 MODÈLE MULTI-SEMAINES AVEC CHARGEMENT INTELLIGENT")
    print("=" * 70)
    
    # Création du modèle
    model = pyo.ConcreteModel()
    
    # =================================================================
    # DONNÉES SIMPLIFIÉES POUR LICENCE GRATUITE
    # =================================================================
    
    # Types de véhicules (réduits pour licence gratuite)
    vehicle_types = {
        'LEGER': {
            'vehicles': ['L1'],  # Un seul véhicule par type
            'fixed_cost': 200,   # €/jour
            'variable_cost': 1.0,  # €/km
            'capacities': {
                'L1': {'weight': 10, 'volume': 25, 'speed': 80}
            }
        },
        'MOYEN': {
            'vehicles': ['M1'],
            'fixed_cost': 300,
            'variable_cost': 1.5,
            'capacities': {
                'M1': {'weight': 20, 'volume': 50, 'speed': 75}
            }
        }
    }
    
    # Produits à transporter (simplifié)
    products = {
        'MACHINES': {
            'quantities_per_week': [3, 2],  # Semaine 1, Semaine 2
            'unit_weight': 2.0,   # tonnes/unité
            'unit_volume': 6.0,   # m³/unité
            'efficiency': 2.0/6.0  # wp/vp
        },
        'ELECTRONIQUES': {
            'quantities_per_week': [8, 6],
            'unit_weight': 0.5,
            'unit_volume': 2.0,
            'efficiency': 0.5/2.0
        }
    }
    
    # Paramètres temporels et logistiques
    params = {
        'distance': 400,  # km (réduit)
        'loading_time': 1.0,    # heures
        'unloading_time': 1.0,  # heures
        'work_time_per_day': 8.0,
        'break_duration': 0.25,
        'max_continuous_driving': 2.0,
        'weeks': 2,
        'max_days_per_week': 5  # 5 jours par semaine
    }
    
    print(f"📊 DONNÉES SIMPLIFIÉES:")
    print(f"   • Types de véhicules: {len(vehicle_types)}")
    print(f"   • Produits: {len(products)}")
    print(f"   • Semaines: {params['weeks']}")
    print(f"   • Distance: {params['distance']} km")
    print()
    
    # =================================================================
    # ENSEMBLES (SETS)
    # =================================================================
    
    # Semaines
    model.S = pyo.Set(initialize=range(1, params['weeks'] + 1))
    
    # Types de véhicules
    model.L = pyo.Set(initialize=list(vehicle_types.keys()))
    
    # Véhicules individuels par type
    model.K = pyo.Set(dimen=2, initialize=[
        (vtype, vid) for vtype, data in vehicle_types.items() 
        for vid in data['vehicles']
    ])
    
    # Produits
    model.P = pyo.Set(initialize=list(products.keys()))
    
    # Voyages maximum par semaine (réduit)
    max_trips_per_week = 2
    model.T = pyo.Set(initialize=range(1, max_trips_per_week + 1))
    
    print(f"🔧 ENSEMBLES CRÉÉS:")
    print(f"   • Semaines (S): {list(model.S)}")
    print(f"   • Types véhicules (L): {list(model.L)}")
    print(f"   • Véhicules (K): {len(model.K)} véhicules")
    print(f"   • Produits (P): {list(model.P)}")
    print(f"   • Voyages/semaine (T): {max_trips_per_week}")
    print()
    
    # =================================================================
    # PARAMÈTRES
    # =================================================================
    
    # Quantités par produit et semaine
    model.q = pyo.Param(model.P, model.S, initialize={
        (p, s): data['quantities_per_week'][s-1] 
        for p, data in products.items() 
        for s in model.S
    })
    
    # Poids et volumes unitaires
    model.w = pyo.Param(model.P, initialize={
        p: data['unit_weight'] for p, data in products.items()
    })
    
    model.v = pyo.Param(model.P, initialize={
        p: data['unit_volume'] for p, data in products.items()
    })
    
    # Efficacité des produits (pour chargement intelligent)
    model.eta = pyo.Param(model.P, initialize={
        p: data['efficiency'] for p, data in products.items()
    })
    
    # Capacités des véhicules
    model.Cw = pyo.Param(model.K, initialize={
        (vtype, vid): vehicle_types[vtype]['capacities'][vid]['weight']
        for vtype, vid in model.K
    })
    
    model.Cv = pyo.Param(model.K, initialize={
        (vtype, vid): vehicle_types[vtype]['capacities'][vid]['volume']
        for vtype, vid in model.K
    })
    
    model.S_speed = pyo.Param(model.K, initialize={
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
    model.H_week = pyo.Param(initialize=params['max_days_per_week'])
    
    print(f"📈 PARAMÈTRES INITIALISÉS:")
    total_demand = sum(pyo.value(model.q[p, s]) for p in model.P for s in model.S)
    print(f"   • Demande totale (2 semaines): {total_demand} unités")
    print()
    
    # =================================================================
    # VARIABLES DE DÉCISION MULTI-SEMAINES
    # =================================================================
    
    # Sélection des véhicules par semaine
    model.x = pyo.Var(model.K, model.S, domain=pyo.Binary)
    
    # Types de véhicules utilisés par semaine
    model.u = pyo.Var(model.L, model.S, domain=pyo.Binary)
    
    # Nombre de voyages par véhicule et semaine
    model.m = pyo.Var(model.K, model.S, domain=pyo.NonNegativeIntegers)
    
    # Transport de produits (avec semaine)
    model.y = pyo.Var(model.P, model.T, model.K, model.S, domain=pyo.NonNegativeIntegers)
    
    # Durée d'utilisation par véhicule et semaine
    model.tau = pyo.Var(model.K, model.S, domain=pyo.NonNegativeReals)
    
    # Variables pour chargement intelligent
    # Stratégie de chargement (0=mélange, 1=homogène)
    model.strategy = pyo.Var(model.K, model.T, model.S, domain=pyo.Binary)
    
    # Produit dominant pour chargement homogène
    model.dominant_product = pyo.Var(model.P, model.K, model.T, model.S, domain=pyo.Binary)
    
    # Utilisation des capacités
    model.weight_util = pyo.Var(model.K, model.T, model.S, bounds=(0, 1))
    model.volume_util = pyo.Var(model.K, model.T, model.S, bounds=(0, 1))
    
    print(f"🔧 VARIABLES MULTI-SEMAINES CRÉÉES:")
    print(f"   • Variables binaires: {len(model.x) + len(model.u)} par semaine")
    print(f"   • Variables transport: {len(model.y)} (P×T×K×S)")
    print(f"   • Variables chargement intelligent: {len(model.strategy) + len(model.dominant_product)}")
    print()
    
    # =================================================================
    # FONCTION OBJECTIF MULTI-SEMAINES
    # =================================================================
    
    def objective_rule(model):
        total_cost = 0
        
        # Coûts par semaine
        for s in model.S:
            for l, k in model.K:
                # Coûts fixes
                fixed_cost = model.tau[l, k, s] * model.F[l] * model.x[l, k, s]
                
                # Coûts variables (approximation simple)
                variable_cost = model.m[l, k, s] * (2 * model.D) * model.G[l]
                
                total_cost += fixed_cost + variable_cost
        
        return total_cost
    
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
    
    print("🎯 FONCTION OBJECTIF: Minimisation coûts totaux multi-semaines")
    print()
    
    # =================================================================
    # CONTRAINTES MULTI-SEMAINES
    # =================================================================
    
    print("⚙️ CRÉATION DES CONTRAINTES MULTI-SEMAINES...")
    
    # 1. Contraintes de cohérence type/véhicule par semaine
    def type_consistency_rule1(model, l, s):
        vehicles_of_type = [k for lt, k in model.K if lt == l]
        if not vehicles_of_type:
            return pyo.Constraint.Skip
        return model.u[l, s] >= sum(model.x[l, k, s] for k in vehicles_of_type) / len(vehicles_of_type)
    
    def type_consistency_rule2(model, l, s):
        vehicles_of_type = [k for lt, k in model.K if lt == l]
        if not vehicles_of_type:
            return pyo.Constraint.Skip
        return model.u[l, s] <= sum(model.x[l, k, s] for k in vehicles_of_type)
    
    model.type_consistency1 = pyo.Constraint(model.L, model.S, rule=type_consistency_rule1)
    model.type_consistency2 = pyo.Constraint(model.L, model.S, rule=type_consistency_rule2)
    
    # 2. Satisfaction de la demande par semaine
    def demand_satisfaction_rule(model, p, s):
        return sum(model.y[p, t, l, k, s] for t in model.T for l, k in model.K) == model.q[p, s]
    
    model.demand_satisfaction = pyo.Constraint(model.P, model.S, rule=demand_satisfaction_rule)
    
    # 3. Contraintes de capacité avec chargement intelligent
    def weight_capacity_rule(model, l, k, t, s):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        total_weight = sum(model.y[p, t, l, k, s] * model.w[p] for p in model.P)
        return total_weight <= model.Cw[l, k] * model.x[l, k, s]
    
    def volume_capacity_rule(model, l, k, t, s):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        total_volume = sum(model.y[p, t, l, k, s] * model.v[p] for p in model.P)
        return total_volume <= model.Cv[l, k] * model.x[l, k, s]
    
    model.weight_capacity = pyo.Constraint(model.K, model.T, model.S, rule=weight_capacity_rule)
    model.volume_capacity = pyo.Constraint(model.K, model.T, model.S, rule=volume_capacity_rule)
    
    # 4. Contraintes de chargement intelligent
    def smart_loading_weight_util(model, l, k, t, s):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        total_weight = sum(model.y[p, t, l, k, s] * model.w[p] for p in model.P)
        return model.weight_util[l, k, t, s] * model.Cw[l, k] == total_weight
    
    def smart_loading_volume_util(model, l, k, t, s):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        total_volume = sum(model.y[p, t, l, k, s] * model.v[p] for p in model.P)
        return model.volume_util[l, k, t, s] * model.Cv[l, k] == total_volume
    
    model.weight_utilization = pyo.Constraint(model.K, model.T, model.S, rule=smart_loading_weight_util)
    model.volume_utilization = pyo.Constraint(model.K, model.T, model.S, rule=smart_loading_volume_util)
    
    # 5. Stratégie de chargement homogène vs mélange
    def homogeneous_loading_rule(model, p, l, k, t, s):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        # Si produit dominant, alors strategy = 1
        M = 1000  # Grande constante
        return model.y[p, t, l, k, s] <= M * model.dominant_product[p, l, k, t, s]
    
    def single_dominant_product_rule(model, l, k, t, s):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        return sum(model.dominant_product[p, l, k, t, s] for p in model.P) <= 1
    
    model.homogeneous_loading = pyo.Constraint(model.P, model.K, model.T, model.S, rule=homogeneous_loading_rule)
    model.single_dominant = pyo.Constraint(model.K, model.T, model.S, rule=single_dominant_product_rule)
    
    # 6. Calcul du nombre de voyages (simplifié)
    def trip_count_rule(model, l, k, s):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        total_transported = sum(model.y[p, t, l, k, s] for p in model.P for t in model.T)
        return model.m[l, k, s] >= model.x[l, k, s]  # Au moins 1 voyage si véhicule utilisé
    
    model.trip_count = pyo.Constraint(model.K, model.S, rule=trip_count_rule)
    
    # 7. Durée par véhicule et semaine (simplifié)
    def duration_calculation_rule(model, l, k, s):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        # Approximation: durée = (voyages * temps_voyage) / temps_travail_jour
        trip_time = (2 * model.D / model.S_speed[l, k]) + model.T_load + model.T_unload
        total_time = model.m[l, k, s] * trip_time
        return model.tau[l, k, s] * model.T_work >= total_time * model.x[l, k, s]
    
    model.duration_calc = pyo.Constraint(model.K, model.S, rule=duration_calculation_rule)
    
    # 8. Contrainte temporelle par semaine
    def weekly_time_limit_rule(model, l, k, s):
        if (l, k) not in model.K:
            return pyo.Constraint.Skip
        return model.tau[l, k, s] <= model.H_week * model.x[l, k, s]
    
    model.weekly_time_limit = pyo.Constraint(model.K, model.S, rule=weekly_time_limit_rule)
    
    # 9. Contrainte de sélection minimale
    def min_selection_rule(model, s):
        return sum(model.u[l, s] for l in model.L) >= 1
    
    model.min_selection = pyo.Constraint(model.S, rule=min_selection_rule)
    
    print(f"✅ CONTRAINTES MULTI-SEMAINES CRÉÉES:")
    print(f"   • Contraintes de cohérence: {len(model.type_consistency1) + len(model.type_consistency2)}")
    print(f"   • Satisfaction demande par semaine: {len(model.demand_satisfaction)}")
    print(f"   • Contraintes capacité: {len(model.weight_capacity) + len(model.volume_capacity)}")
    print(f"   • Chargement intelligent: {len(model.homogeneous_loading) + len(model.single_dominant)}")
    print(f"   • Contraintes temporelles: {len(model.weekly_time_limit)}")
    print()
    
    return model

def solve_multi_week_model(model):
    """
    Résolution du modèle avec solveur adapté à la licence gratuite
    """
    
    print("🔍 RÉSOLUTION DU MODÈLE MULTI-SEMAINES...")
    print("=" * 50)
    
    # Tentative avec différents solveurs
    solvers_to_try = ['gurobi', 'glpk', 'cbc']
    
    for solver_name in solvers_to_try:
        try:
            solver = pyo.SolverFactory(solver_name)
            if solver.available():
                print(f"✅ Utilisation du solveur: {solver_name.upper()}")
                
                # Configuration adaptée
                if solver_name == 'gurobi':
                    solver.options['TimeLimit'] = 120  # 2 minutes
                    solver.options['MIPGap'] = 0.05    # 5% gap
                    solver.options['Threads'] = 2
                
                # Résolution
                start_time = datetime.now()
                results = solver.solve(model, tee=True)
                solve_time = datetime.now() - start_time
                
                print(f"⏱️ TEMPS DE RÉSOLUTION: {solve_time.total_seconds():.2f} secondes")
                
                # Vérification du statut
                if (results.solver.status == SolverStatus.ok and 
                    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
                    
                    status = "OPTIMALE" if results.solver.termination_condition == TerminationCondition.optimal else "RÉALISABLE"
                    print(f"✅ SOLUTION {status} TROUVÉE!")
                    return results, True
                    
        except Exception as e:
            print(f"❌ Erreur avec {solver_name}: {e}")
            continue
    
    print("❌ AUCUN SOLVEUR DISPONIBLE!")
    return None, False

def print_multi_week_solution(model, results):
    """
    Affichage détaillé de la solution multi-semaines
    """
    
    print("\n📊 SOLUTION MULTI-SEMAINES DÉTAILLÉE")
    print("=" * 60)
    
    # Coût total
    total_cost = pyo.value(model.obj)
    print(f"💰 COÛT TOTAL OPTIMAL: {total_cost:.2f}€")
    
    # Analyse par semaine
    for s in model.S:
        print(f"\n📅 SEMAINE {s}:")
        print("-" * 30)
        
        # Véhicules sélectionnés
        selected_vehicles = [(l, k) for l, k in model.K if pyo.value(model.x[l, k, s]) > 0.5]
        print(f"🚛 Véhicules utilisés: {len(selected_vehicles)}")
        
        weekly_cost = 0
        for l, k in selected_vehicles:
            tau_val = pyo.value(model.tau[l, k, s])
            m_val = pyo.value(model.m[l, k, s])
            
            fixed_cost = tau_val * pyo.value(model.F[l])
            variable_cost = m_val * (2 * pyo.value(model.D)) * pyo.value(model.G[l])
            vehicle_cost = fixed_cost + variable_cost
            weekly_cost += vehicle_cost
            
            print(f"   • {k} (Type: {l})")
            print(f"     - Voyages: {m_val}")
            print(f"     - Durée: {tau_val:.1f} jours")
            print(f"     - Coût: {vehicle_cost:.2f}€")
        
        print(f"💰 Coût semaine {s}: {weekly_cost:.2f}€")
        
        # Demandes satisfaites
        print(f"📦 Transport par produit:")
        for p in model.P:
            demanded = pyo.value(model.q[p, s])
            transported = sum(pyo.value(model.y[p, t, l, k, s]) 
                            for t in model.T for l, k in model.K)
            print(f"   • {p}: {transported}/{demanded} unités")
    
    # Statistiques globales
    print(f"\n📈 STATISTIQUES GLOBALES:")
    total_demand = sum(pyo.value(model.q[p, s]) for p in model.P for s in model.S)
    total_transported = sum(pyo.value(model.y[p, t, l, k, s]) 
                          for p in model.P for t in model.T 
                          for l, k in model.K for s in model.S)
    
    print(f"   • Demande totale: {total_demand} unités")
    print(f"   • Quantité transportée: {total_transported} unités")
    print(f"   • Satisfaction: {100*total_transported/total_demand:.1f}%")
    
    # Utilisation des véhicules
    total_vehicle_weeks = sum(pyo.value(model.x[l, k, s]) for l, k in model.K for s in model.S)
    print(f"   • Semaines-véhicules utilisées: {total_vehicle_weeks}")
    print(f"   • Coût moyen par semaine-véhicule: {total_cost/max(total_vehicle_weeks, 1):.2f}€")

def main():
    """
    Fonction principale d'exécution
    """
    
    print("🚀 OPTIMISATION MULTI-SEMAINES AVEC CHARGEMENT INTELLIGENT")
    print("=" * 70)
    print(f"🕐 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. Création du modèle
        print("📋 ÉTAPE 1: CRÉATION DU MODÈLE MULTI-SEMAINES")
        print("-" * 50)
        model = create_multi_week_transport_model()
        
        # 2. Résolution
        print("📋 ÉTAPE 2: RÉSOLUTION")
        print("-" * 50)
        results, success = solve_multi_week_model(model)
        
        if not success:
            print("❌ Échec de la résolution!")
            return
        
        # 3. Analyse des résultats
        print("📋 ÉTAPE 3: ANALYSE DES RÉSULTATS")
        print("-" * 50)
        print_multi_week_solution(model, results)
        
        print(f"\n🕐 Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎉 OPTIMISATION TERMINÉE AVEC SUCCÈS!")
        
        return model, results
        
    except Exception as e:
        print(f"❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# Point d'entrée principal
if __name__ == "__main__":
    print("🔧 VÉRIFICATION DES DÉPENDANCES:")
    
    # Vérification Pyomo
    try:
        import pyomo.environ as pyo
        print("✅ Pyomo installé")
    except ImportError:
        print("❌ Pyomo non installé: pip install pyomo")
        exit(1)
    
    # Vérification des solveurs
    solvers_available = []
    for solver_name in ['gurobi', 'glpk', 'cbc']:
        try:
            solver = pyo.SolverFactory(solver_name)
            if solver.available():
                solvers_available.append(solver_name)
                print(f"✅ {solver_name.upper()} disponible")
        except:
            print(f"❌ {solver_name.upper()} non disponible")
    
    if not solvers_available:
        print("❌ Aucun solveur disponible!")
        print("💡 Installez au moins un solveur: pip install glpk")
        exit(1)
    
    print(f"✅ Solveurs disponibles: {', '.join(solvers_available)}")
    print("\n" + "="*70)
    
    # Exécution principale
    model, results = main()
    
    if model is not None:
        print("\n🎉 EXÉCUTION TERMINÉE AVEC SUCCÈS!")
        
        # Sauvegarde optionnelle
        try:
            import json
            solution_summary = {
                'total_cost': pyo.value(model.obj),
                'weeks': len(model.S),
                'vehicles_used': sum(pyo.value(model.x[l, k, s]) for l, k in model.K for s in model.S),
                'solver_status': 'optimal'
            }
            
            with open('multi_week_solution.json', 'w', encoding='utf-8') as f:
                json.dump(solution_summary, f, indent=2, ensure_ascii=False)
            print("💾 Résumé sauvegardé dans 'multi_week_solution.json'")
            
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde: {e}")
    else:
        print("\n❌ ÉCHEC DE L'EXÉCUTION!")