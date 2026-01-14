import pandas as pd
import numpy as np
import itertools
import math

class LogisticsSolver:
    def __init__(self, df, cost_multipliers=None):
        self.df = df
        self.cost_multipliers = cost_multipliers if cost_multipliers else {'land': 5000, 'air': 50000}
        # Identify Stages, excluding 0 (Jakarta/Start) from the recursive stages
        self.stages = sorted(df['stage_prioritas'].unique())
        if 0 in self.stages: self.stages.remove(0)
        self.steps_log = [] # <--- FITUR BARU: Menyimpan jejak perhitungan

    def calculate_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def get_transport_cost(self, node_a, node_b):
        dist = self.calculate_haversine(node_a['lat'], node_a['lon'], node_b['lat'], node_b['lon'])
        
        # Logika Biaya:
        # 1. Intra-Stage (Skeliling Satu Wilayah) -> Darat (Murah)
        # 2. Inter-Stage (Pindah Wilayah/Pulau) -> Udara (Mahal)
        
        is_same_stage = (node_a['stage_prioritas'] == node_b['stage_prioritas'])
        
        if is_same_stage:
            # Biaya Darat
            return dist * self.cost_multipliers.get('land', 5000)
        else:
            # Biaya Udara / Inter-Island
            variable_cost = dist * self.cost_multipliers.get('air', 50000)
            
            # Tambahan Biaya Basis (Fixed Cost) jika masuk Zona Merah (Stage 1)
            # Ini aturan khusus bisnis: landing fee / sewa heli khusus
            base_cost = 0
            if node_b['stage_prioritas'] == 1:
                base_cost = node_b.get('biaya_basis_idr', 0)
                
            return base_cost + variable_cost

    def solve_open_tsp_dynamic(self, stage_id, entry_node_id):
        stage_nodes = self.df[self.df['stage_prioritas'] == stage_id].copy()
        # Visit all OTHER nodes in this stage
        to_visit_ids = [nid for nid in stage_nodes['id'].tolist() if nid != entry_node_id]
        
        if not to_visit_ids:
            return 0, [entry_node_id], entry_node_id
            
        current_id = entry_node_id
        path = [entry_node_id]
        total_dist_cost = 0
        
        while to_visit_ids:
            curr_node = self.df[self.df['id'] == current_id].iloc[0]
            best_next_id = None
            min_step_cost = float('inf')
            
            # Simple Greedy Nearest Neighbor
            for cand_id in to_visit_ids:
                cand_node = self.df[self.df['id'] == cand_id].iloc[0]
                cost = self.get_transport_cost(curr_node, cand_node)
                if cost < min_step_cost:
                    min_step_cost = cost
                    best_next_id = cand_id
            
            total_dist_cost += min_step_cost
            path.append(best_next_id)
            to_visit_ids.remove(best_next_id)
            current_id = best_next_id
            
        return total_dist_cost, path, current_id

    def get_recommendations(self, top_k=1):
        self.steps_log = [] # Reset Log
        self.dp_table = {} # Store DP table for visualization
        dp = {}
        
        if not self.stages:
             return []

        # --- LANGKAH 1: STAGE TERAKHIR (Base Case) ---
        last_stage = self.stages[-1]
        dp[last_stage] = {}
        
        last_nodes = self.df[self.df['stage_prioritas'] == last_stage]['id'].tolist()
        for entry in last_nodes:
            cost, path, exit_node = self.solve_open_tsp_dynamic(last_stage, entry)
            dp[last_stage][entry] = {'total_cost': cost, 'full_path': path, 'next_entry': None}
            
            # LOG: Mencatat Base Case
            entry_name = self.df[self.df['id'] == entry].iloc[0]['nama_lokasi']
            self.steps_log.append({
                "stage": int(last_stage),
                "type": "Base Calculation",
                "node": entry_name,
                "detail": f"Menghitung biaya internal di Stage {last_stage}. Sisa biaya ke depan = 0.",
                "math": f"Biaya Lokal ({cost:,.0f}) + Future (0) = {cost:,.0f}"
            })

        # --- LANGKAH 2: BACKWARD RECURSION ---
        # Traverse from second to last stage down to the first stage
        for stage in reversed(self.stages[:-1]):
            dp[stage] = {}
            curr_nodes = self.df[self.df['stage_prioritas'] == stage]['id'].tolist()
            next_stage = stage + 1 # Assuming sequential stages
            # If actual stages are not strictly sequential (e.g. 1, 3, 4), this logic needs 'next_stage_in_list'
            # But sorted(unique) implies we treat them in order. 
            # If next_stage is NOT in dp (gap in stages), we should look at available next stages.
            # For this dataset, stages are 1, 2, 3, 4. So +1 works.
            
            for entry in curr_nodes:
                entry_name = self.df[self.df['id'] == entry].iloc[0]['nama_lokasi']
                
                # A. Hitung TSP Lokal
                local_cost, local_path, local_exit = self.solve_open_tsp_dynamic(stage, entry)
                local_exit_node = self.df[self.df['id'] == local_exit].iloc[0]
                
                # B. Cari Sambungan Termurah
                best_future_cost = float('inf')
                best_connection = None
                best_next_name = ""
                transit_cost_saved = 0
                future_cost_saved = 0
                
                if next_stage in dp:
                    for next_entry, future_data in dp[next_stage].items():
                        next_entry_node = self.df[self.df['id'] == next_entry].iloc[0]
                        
                        # Cost from Exit of this stage to Entry of Next Stage
                        transit_cost = self.get_transport_cost(local_exit_node, next_entry_node)
                        total = local_cost + transit_cost + future_data['total_cost']
                        
                        if total < best_future_cost:
                            best_future_cost = total
                            best_connection = {
                                'total_cost': total,
                                'full_path': local_path + future_data['full_path'],
                                'next_entry': next_entry
                            }
                            # Simpan data untuk Log
                            best_next_name = next_entry_node['nama_lokasi']
                            transit_cost_saved = transit_cost
                            future_cost_saved = future_data['total_cost']
                
                if best_connection:
                    dp[stage][entry] = best_connection
                    
                    # LOG: Mencatat Keputusan Rekursif
                    self.steps_log.append({
                        "stage": int(stage),
                        "type": "Recursive Decision",
                        "node": entry_name,
                        "detail": f"Dari {entry_name}, rute termurah adalah menuju **{best_next_name}** (Stage {next_stage}).",
                        "math": f"Lokal ({local_cost:,.0f}) + Transisi ({transit_cost_saved:,.0f}) + Future ({future_cost_saved:,.0f}) = **{best_future_cost:,.0f}**"
                    })

        # --- LANGKAH 3: FINAL START (Stage 0 -> First Stage) ---
        # Assuming ID 0 is Jakarta/Start
        start_node_match = self.df[self.df['id'] == 0] 
        if start_node_match.empty:
             # Fallback if 0 not found, maybe 'START'?
             start_node_match = self.df[self.df['id'] == 'START']
        
        if start_node_match.empty:
             # Fallback: Just take the first node in Stage 0
             start_node = self.df[self.df['stage_prioritas'] == 0].iloc[0]
        else:
             start_node = start_node_match.iloc[0]

        final_results = []
        first_stage = self.stages[0]
        
        for entry, data in dp[first_stage].items():
            entry_node = self.df[self.df['id'] == entry].iloc[0]
            initial_cost = self.get_transport_cost(start_node, entry_node)
            total_global = initial_cost + data['total_cost']
            
            final_results.append({
                'total_cost': total_global,
                'full_path': [start_node['id']] + data['full_path']
            })
            
            # LOG: Keputusan Akhir
            self.steps_log.append({
                "stage": 0,
                "type": "Final Decision",
                "node": f"{start_node['nama_lokasi']} (Start)",
                "detail": f"Memilih masuk ke **{entry_node['nama_lokasi']}** sebagai pintu gerbang Stage {first_stage}.",
                "math": f"Transport Awal ({initial_cost:,.0f}) + Sisa Rute ({data['total_cost']:,.0f}) = **{total_global:,.0f}**"
            })
            
        final_results.sort(key=lambda x: x['total_cost'])
        
        self.dp_table = dp # Save for access
        
        # Convert IDs to Node Dictionaries for app compatibility
        for res in final_results[:top_k]:
            path_ids = res['full_path']
            # Create a lookup map for speed, though N is small
            # res['full_path'] = [self.df[self.df['id'] == nid].iloc[0].to_dict() for nid in path_ids]
            # optimization:
            nodes_objs = []
            for nid in path_ids:
                row = self.df[self.df['id'] == nid]
                if not row.empty:
                    nodes_objs.append(row.iloc[0].to_dict())
            res['full_path'] = nodes_objs
            
        return final_results[:top_k]
