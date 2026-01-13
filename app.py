import streamlit as st
import json
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import math
from solver import DPSolver

st.set_page_config(page_title="OptiRelief: Disaster Logistics", layout="wide")

@st.cache_data
def load_data():
    with open('data/logistics_data.json', 'r') as f:
        return json.load(f)

try:
    data = load_data()
except FileNotFoundError:
    st.error("Data file not found!")
    st.stop()

st.title("SAH (Save All Humanity) - Optimasi Jalur Logistik")
st.markdown("Dynamic Programming: Perbandingan Jalur Darat vs Udara")

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Parameter Muatan")
    cargo_weight = st.number_input("Total Berat Bantuan (Kg)", min_value=100, value=5000, step=100)

    st.header("2. Kapasitas Moda")
    cap_air = st.number_input("Kapasitas Helikopter (Kg)", value=1000)
    cap_land = st.number_input("Kapasitas Truk (Kg)", value=3000)

    st.header("3. Simulasi Biaya")
    m_air = st.slider("Faktor Biaya Udara", 0.5, 2.0, 1.0)
    m_land = st.slider("Faktor Biaya Darat", 0.5, 2.0, 1.0)

# --- CALCULATION LOGIC ---
def calculate_edges(data, weight, c_air, c_land, m_a, m_l):
    adjusted = []
    for edge in data['edges']:
        mode = edge['mode']
        cost = edge['cost']
        duration = edge.get('duration_hours', 0)
        
        is_air = "Helikopter" in mode or "Plane" in mode
        capacity = c_air if is_air else c_land
        multiplier = m_a if is_air else m_l
        
        trips = math.ceil(weight / capacity)
        total_cost = cost * trips * multiplier
        
        # Duration simulation: assume parallel trips don't add time, but sequential convoy might? 
        # For simplicity, time is per trip duration (assuming fleet availability)
        # Or if limited fleet, time = duration * trips. Let's assume limited fleet for realism.
        total_time = duration * trips 
        
        new_edge = edge.copy()
        new_edge.update({'cost': total_cost, 'trips': trips, 'duration': total_time})
        adjusted.append(new_edge)
    return {"nodes": data['nodes'], "edges": adjusted}

processed_data = calculate_edges(data, cargo_weight, cap_air, cap_land, m_air, m_land)
solver = DPSolver(processed_data)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Analisis Perbandingan", "🗺️ Peta Distribusi", "📋 Detail Perhitungan"])

with tab1:
    st.subheader("Perbandingan Skenario")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("### 💰 Prioritas Termurah (Cost Efficient)")
        opt_cost = solver.get_optimal_path("Jakarta_Pool", metric='cost')
        if opt_cost:
            st.success(f"Biaya Minimum: Rp {opt_cost['min_val']:,.0f}")
            path_c = opt_cost['path']
            st.code(" ➔ ".join(path_c))
            
            # Calculate corresponding time for this path
            total_time_c = 0
            for i in range(len(path_c)-1):
                u, v = path_c[i], path_c[i+1]
                total_time_c += solver.graph[u][v]['duration']
            st.markdown(f"**Estimasi Waktu: {total_time_c:.1f} Jam**")
            
    with col_b:
        st.markdown("### ⏱️ Prioritas Tercepat (Time Efficient)")
        opt_time = solver.get_optimal_path("Jakarta_Pool", metric='time')
        if opt_time:
            st.warning(f"Waktu Tercepat: {opt_time['min_val']:.1f} Jam")
            path_t = opt_time['path']
            st.code(" ➔ ".join(path_t))
            
            # Calculate corresponding cost for this path
            total_cost_t = 0
            for i in range(len(path_t)-1):
                u, v = path_t[i], path_t[i+1]
                total_cost_t += solver.graph[u][v]['cost']
            st.markdown(f"**Estimasi Biaya: Rp {total_cost_t:,.0f}**")

    # Recommendation
    st.divider()
    st.markdown("#### 💡 Rekomendasi Sistem")
    
    cost_diff = total_cost_t - opt_cost['min_val']
    time_saved = total_time_c - opt_time['min_val']
    
    if path_c == path_t:
        st.info("Jalur optimal sama untuk Biaya maupun Waktu. Ini adalah pilihan mutlak terbaik.")
    else:
        if cost_diff > 0 and time_saved > 0:
            st.write(f"Jika memilih jalur tercepat, Anda menghemat **{time_saved:.1f} Jam**, namun biaya bertambah **Rp {cost_diff:,.0f}**.")
            st.write(f"Ratio: Anda membayar Rp {cost_diff/time_saved:,.0f} untuk setiap jam yang dihemat.")

with tab2:
    try:
        import pydot
        dot = nx.nx_pydot.to_pydot(solver.graph)
        st.graphviz_chart(dot.to_string())
    except:
        st.warning("Graphviz not found, using basic view")
        fig, ax = plt.subplots(figsize=(10, 6))
        pos = nx.shell_layout(solver.graph)
        nx.draw(solver.graph, pos, with_labels=True, node_color='lightblue')
        st.pyplot(fig)

with tab3:
    metric = st.radio("Tampilkan detail untuk:", ["Biaya (Rp)", "Waktu (Jam)"])
    metric_key = 'cost' if "Biaya" in metric else 'time'
    
    f_val, table = solver.backward_recursion(metric=metric_key)
    df = pd.DataFrame(table)
    st.dataframe(df, use_container_width=True)

st.caption("Ver 2.0 - Multi-Objective Optimization")
