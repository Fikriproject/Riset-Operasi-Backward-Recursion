import pandas as pd
import solver

def verify():
    print("Loading data...")
    try:
        df = pd.read_csv('data_lokasi_bencana.csv')
        print(f"Data loaded: {len(df)} rows.")
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    stages_data = {}
    for _, row in df.iterrows():
        stage = int(row['stage_prioritas']) # Ensure int
        if stage not in stages_data:
            stages_data[stage] = []
        stages_data[stage].append(row.to_dict())
    
    print(f"Stages found: {list(stages_data.keys())}")
    
    cost_multipliers = {'land': 5000, 'air': 50000}
    
    print("Running solver...")
    try:
        # Pass k=1 just to see if it works
        results = solver.backward_recursion_k_best(stages_data, cost_multipliers, k=3)
        print(f"Solver returned {len(results)} solutions.")
        
        for i, res in enumerate(results):
            print(f"Option {i+1}: Cost {res['total_cost']}")
            names = [n['nama_lokasi'] for n in res['full_path']]
            print(f"  Path: {' -> '.join(names)}")
            
    except Exception as e:
        print(f"Error running solver: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
