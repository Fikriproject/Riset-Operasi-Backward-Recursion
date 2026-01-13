import pandas as pd
import networkx as nx

class DPSolver:
    def __init__(self, data):
        self.nodes = data['nodes'] # Dictionary of stages
        self.edges = data['edges'] # List of dicts
        self.graph = self._build_graph()
        self.result_table = []
        
    def _build_graph(self):
        G = nx.DiGraph()
        for i in range(1, 5):
            stage_nodes = self.nodes.get(f"Stage_{i}", [])
            for node in stage_nodes:
                G.add_node(node, stage=i)
        
        for edge in self.edges:
            G.add_edge(edge['from'], edge['to'], 
                       cost=edge['cost'], 
                       duration=edge.get('duration_hours', 1), # Default 1 hour if missing
                       mode=edge['mode'], 
                       desc=edge['desc'])
        return G

    def backward_recursion(self, metric='cost'):
        """
        Executes Backward Recursion Dynamic Programming.
        f_n(s) = min { C_sn_xn + f_n+1(x_n) }
        metric: 'cost' or 'time'
        """
        f_star = {} 
        self.result_table = []
        
        # Start from the last stage (Stage 4)
        for node in self.nodes["Stage_4"]:
            f_star[node] = {"min_val": 0, "path": [node]}
            
        # Iterate backwards
        for stage_idx in range(3, 0, -1):
            current_stage_nodes = self.nodes[f"Stage_{stage_idx}"]
            next_stage_nodes = self.nodes[f"Stage_{stage_idx+1}"]
            
            stage_results = []
            
            for s in current_stage_nodes:
                possible_moves = []
                
                if self.graph.has_node(s):
                    for neighbor in self.graph.successors(s):
                        if neighbor in next_stage_nodes:
                            edge_data = self.graph[s][neighbor]
                            
                            # SELECT METRIC
                            if metric == 'time':
                                weight = edge_data['duration']
                            else:
                                weight = edge_data['cost']
                            
                            future_info = f_star.get(neighbor)
                            if future_info:
                                total_val = weight + future_info["min_val"]
                                possible_moves.append({
                                    "next_node": neighbor,
                                    "edge_val": weight,
                                    "future_val": future_info["min_val"],
                                    "total_val": total_val,
                                    "path_dest": future_info["path"]
                                })
                
                if possible_moves:
                    best_move = min(possible_moves, key=lambda x: x['total_val'])
                    f_star[s] = {
                        "min_val": best_move['total_val'],
                        "path": [s] + best_move['path_dest'],
                        "best_next": best_move['next_node']
                    }
                    
                    stage_results.append({
                        "Stage": stage_idx,
                        "State (Node)": s,
                        "Decision Variables": [m['next_node'] for m in possible_moves],
                        "Metric Values": [m['total_val'] for m in possible_moves],
                        "Optimal Decision (x*)": best_move['next_node'],
                        "Optimal Value (f*)": best_move['total_val']
                    })
                else:
                    f_star[s] = {"min_val": float('inf'), "path": [s]}
            
            self.result_table.extend(stage_results)
            
        return f_star, self.result_table

    def get_optimal_path(self, start_node, metric='cost'):
        f_star, _ = self.backward_recursion(metric=metric)
        if start_node in f_star:
            return f_star[start_node]
        return None
