import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import solver

# Page Config
st.set_page_config(page_title="OptiRelief Logistics", layout="wide")

# --- Sidebar: Sensitivity Analysis ---
st.sidebar.header("🔧 Sensitivity Analysis (Parameter Biaya)")
cost_land = st.sidebar.slider("Biaya Transport Darat (per Km)", 1000, 10000, 5000, 500)
cost_air = st.sidebar.slider("Biaya Transport Udara (per Km)", 10000, 100000, 50000, 5000)

cost_multipliers = {'land': cost_land, 'air': cost_air}

# --- Data Loading ---
@st.cache_data
def load_data():
    # Load from the local CSV we created
    df = pd.read_csv('data_lokasi_bencana.csv')
    return df

df = load_data()

# --- Main Logic ---
st.title("🚁 OptiRelief: Disaster Logistics Chain Optimization")
st.markdown("Optimization of multi-stage disaster relief distribution using **Dynamic Open-TSP** and **Backward Recursion**.")

# 1. Group Data by Stage
# 2. Run Optimization (Class-Based with Trace)
# 2. Run Optimization (Class-Based with Trace)
# Pass dynamic multipliers from sidebar
solver_instance = solver.LogisticsSolver(df, cost_multipliers=cost_multipliers)
top_k_solutions = solver_instance.get_recommendations(top_k=3)

# --- Visualization Function ---
def draw_sequential_chain(df, selected_path_list, total_cost):
    """
    Memvisualisasikan Rantai Distribusi Logistik dengan Tata Letak Berlapis yang Jelas.
    """
    
    # 1. Setup Graph & Data
    G = nx.DiGraph()
    pos = {} # Kamus untuk menyimpan posisi node
    colors = []
    labels = {}
    
    # Mapping Warna per Stage (Warna lebih cerah agar kontras)
    stage_colors = {
        0: '#A9A9A9', # Abu-abu Tua (Start)
        1: '#FF6B6B', # Merah Cerah (Stage 1)
        2: '#FFD93D', # Kuning Emas (Stage 2)
        3: '#6BCB77', # Hijau (Stage 3)
        4: '#4D96FF'  # Biru (Stage 4 - Finish)
    }

    # 2. Logika Tata Letak Berlapis (Layered Layout)
    # Kita perlu tahu ada berapa node di setiap layer (stage) untuk mengatur jarak Y
    # Adapting column name 'stage' to 'stage_prioritas' and 'nama' to 'nama_lokasi'
    nodes_per_stage = df.groupby('stage_prioritas')['id'].count().to_dict()
    current_count_per_stage = {stage: 0 for stage in nodes_per_stage}
    
    # Jarak Horizontal antar Stage (Sumbu X)
    X_SPACING = 3.0
    # Jarak Vertikal antar Node dalam satu Stage (Sumbu Y)
    Y_SPACING = 1.5

    for _, row in df.iterrows():
        node_id = row['id']
        stage = row['stage_prioritas']
        
        G.add_node(node_id)
        # Label disingkat jika terlalu panjang (Opsional, agar rapi)
        label_text = row['nama_lokasi']
        if len(label_text) > 15:
             label_text = label_text[:12] + "..."
        labels[node_id] = label_text
        
        # --- INI KUNCI TATA LETAKNYA ---
        # Posisi X: Berdasarkan Stage (Semakin besar stage, semakin ke kanan)
        x_pos = stage * X_SPACING
        
        # Posisi Y: Disejajarkan secara vertikal.
        # Kita hitung offset agar node berada di tengah secara vertikal.
        count = current_count_per_stage[stage]
        total_in_stage = nodes_per_stage[stage]
        # Rumus ini membuat node tersebar rapi ke atas dan bawah dari garis tengah (Y=0)
        y_pos = (count - (total_in_stage - 1) / 2.0) * Y_SPACING
        
        pos[node_id] = (x_pos, y_pos)
        current_count_per_stage[stage] += 1
        
        colors.append(stage_colors.get(stage, '#000000'))

    # 3. Identifikasi Edge (Garis Jalur)
    edge_colors = []
    styles = []
    edges_to_draw = []
    
    for i in range(len(selected_path_list) - 1):
        u = selected_path_list[i]
        v = selected_path_list[i+1]
        
        G.add_edge(u, v)
        edges_to_draw.append((u, v))
        
        # Logika Gaya Garis (Udara vs Darat)
        stage_u = df[df['id']==u]['stage_prioritas'].values[0]
        stage_v = df[df['id']==v]['stage_prioritas'].values[0]
        
        # Transisi dari Stage 0 -> 1 dianggap Udara/Jarak Jauh
        # Also generally inter-stage transitions
        if stage_u != stage_v:
            styles.append('dashed')
            if stage_u == 0 and stage_v == 1:
                 edge_colors.append('black')
            else:
                 edge_colors.append('#E74C3C') # Red
        else:
            styles.append('solid')
            edge_colors.append('#FF4500') # Oranye-Merah agar mencolok

    # 4. Menggambar Canvas (Plotting)
    fig, ax = plt.subplots(figsize=(14, 8)) # Perbesar ukuran canvas
    
    # Gambar Background (Pita Warna per Stage)
    # Menggunakan koordinat X yang sudah kita tentukan
    layer_names = ["Start", "Stage 1\n(Prioritas Tinggi)", "Stage 2\n(Sedang)", "Stage 3\n(Ringan)", "Stage 4\n(Finish)"]
    for stage_idx in range(5):
        if stage_idx not in nodes_per_stage: continue 
        
        start_x = (stage_idx * X_SPACING) - (X_SPACING/2)
        end_x = (stage_idx * X_SPACING) + (X_SPACING/2)
        color = stage_colors.get(stage_idx, '#ffffff')
        # Gambar pita vertikal transparan
        ax.axvspan(start_x, end_x, color=color, alpha=0.15, zorder=0)
        # Tambahkan label stage di bagian atas
        # Calculate max Y for this specific stage to place label
        max_nodes_any = max(nodes_per_stage.values())
        header_y_pos = (max_nodes_any * Y_SPACING / 2) + 0.5
        
        ax.text(stage_idx * X_SPACING, header_y_pos, 
                layer_names[stage_idx] if stage_idx < len(layer_names) else f"Stage {stage_idx}", 
                horizontalalignment='center', fontweight='bold', fontsize=10, color=color)

    # Gambar Nodes
    nodes = nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=1000, 
                           edgecolors='black', linewidths=1.5, ax=ax)
    nodes.set_zorder(2)
    
    # Gambar Labels (Nama Kota)
    # Posisikan label sedikit di bawah node agar tidak tertutup
    label_pos = {k: (v[0], v[1]-0.3) for k, v in pos.items()}
    # draw_networkx_labels returns a dict of text objects
    text_items = nx.draw_networkx_labels(G, label_pos, labels=labels, font_size=9, font_weight='bold', ax=ax)
    for t in text_items.values():
        t.set_zorder(3)
    
    # Gambar Edges (Jalur Berantai) satu per satu
    for i, edge in enumerate(edges_to_draw):
        edges = nx.draw_networkx_edges(
            G, pos,
            edgelist=[edge],
            width=3,
            edge_color=edge_colors[i],
            style=styles[i],
            arrowstyle='-|>', arrowsize=25, # Panah yang jelas
            connectionstyle="arc3,rad=0.1", # Lengkungan halus
            ax=ax
        )
        for e in edges:
            e.set_zorder(1)

    # Dekorasi Akhir
    ax.set_title(f"Visualisasi Rantai Distribusi Optimal (Total Cost: Rp {total_cost:,.0f})", 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_axis_off() # Hilangkan sumbu
    # Set batas agar semua elemen terlihat (memberi 'padding')
    ax.set_xlim(-X_SPACING, 4 * X_SPACING + X_SPACING)
    
    # Dynamic Y limits
    max_y = max(nodes_per_stage.values()) * Y_SPACING / 2
    ax.set_ylim(-max_y - 1, max_y + 2) # Tambah ruang di atas untuk label stage

    return fig

# --- Display Results ---

if not top_k_solutions:
    st.error("No valid path found provided the constraints.")
else:
    tabs = st.tabs([f"Option {i+1} (Cost: {sol['total_cost']:,.0f})" for i, sol in enumerate(top_k_solutions)])
    
    for i, tab in enumerate(tabs):
        with tab:
            sol = top_k_solutions[i]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Visualisasi Jalur")
                path_ids = [node['id'] for node in sol['full_path']]
                fig = draw_sequential_chain(df, path_ids, sol['total_cost'])
                st.pyplot(fig)
                
                st.markdown("""
                ### ℹ️ Penjelasan Visual
                
                **Simbol & Alur Distribusi:**
                - **Garis Putus-Putus Hitam/Red ( --- )**: 
                    - Transportasi Jarak Jauh / Antar-Pulau (Helikopter/Pesawat).
                    - Menghubungkan *Exit Node* tahap sebelumnya ke *Entry Node* tahap berikutnya.
                
                - **Garis Tegas Oranye ( ─── )**:
                    - Transportasi Lokal / Darat (Truk/Mobil Box).
                    - Bergerak menyusuri semua titik di dalam satu tahap (zona merah).
                
                - **Latat Belakang Warna**:
                    - Menunjukkan pengelompokan prioritas waktu. Logistik HARUS menyelesaikan area kiri (Prioritas Tinggi) sebelum bergerak ke kanan.
                """)
                
            with col2:
                st.subheader("Detail Perjalanan")
                st.success(f"**Total Biaya Estimasi**: IDR {sol['total_cost']:,.2f}")
                
                st.write("**Rincian Perjalanan & Biaya:**")
                
                # Header Table
                st.markdown("""
                | Dari | Ke | Jarak (KM) | Transport | Biaya (IDR) |
                |---|---|---|---|---|
                """)
                
                full_path = sol['full_path']
                for j in range(len(full_path)-1):
                    node_a = full_path[j]
                    node_b = full_path[j+1]
                    
                    # Calculate Dist
                    dist = solver_instance.calculate_haversine(node_a['lat'], node_a['lon'], node_b['lat'], node_b['lon'])
                    
                    # Determine Mode
                    stage_a = node_a['stage_prioritas']
                    stage_b = node_b['stage_prioritas']
                    
                    mode = 'land'
                    transport_name = "Truk/Darat"
                    if stage_a != stage_b:
                        mode = 'air'
                        transport_name = "**Helikopter**" # Bold high cost
                    
                    # Calculate Cost
                    # Use solver_instance method if possible, or recalculate manually
                    # Since solver_instance.get_transport_cost takes nodes, we do:
                    # But get_transport_cost includes logic. Let's use it.
                    calced_cost = solver_instance.get_transport_cost(node_a, node_b)
                    
                    st.markdown(f"| {node_a['nama_lokasi']} | {node_b['nama_lokasi']} | {dist:.2f} km | {transport_name} | {calced_cost:,.0f} |")
                

                
                with st.expander("Debug Info (Transition Steps)"):
                    for info in sol.get('debug_info', []):
                        st.write(f"- {info}")

# --- Comparison / Naive Section (Placeholder) ---
# ==========================================
# BAGIAN VISUALISASI TRACE (Update di app.py)
# Taruh kode ini di bagian paling bawah file
# ==========================================

st.divider()
st.header("🧬 Audit Algoritma: Bagaimana Rute Ini Ditemukan?")
st.write("Algoritma menggunakan metode **Backward Recursion** (Menghitung Mundur) untuk menghindari jebakan biaya di awal.")

# Buat Tab untuk melihat Trace
tab_ringkas, tab_detail, tab_struktur = st.tabs(["📄 Ringkasan Keputusan", "📖 Bedah Logika (Story Mode)", "📊 Struktur DP Table"])

# --- TAB 1: RINGKASAN (Tabel Pemenang) ---
with tab_ringkas:
    st.info("📋 Tabel ini hanya menampilkan **RUTE PEMENANG (The Golden Path)** yang dipilih algoritma dari ribuan kemungkinan.")

    # 1. Pastikan kita punya data rute terbaik
    # (Mengambil data dari hasil rekomendasi solver yang sudah dijalankan di atas)
    if 'top_k_solutions' in locals() and top_k_solutions:
        best_route = top_k_solutions[0] # Ambil rute terbaik (Top 1)
        full_path_ids = best_route['full_path'] # List Node Objects
        total_cost_final = best_route['total_cost']
        
        # 2. Siapkan List untuk Tabel
        table_data = []
        
        # Helper: Cari detail node berdasarkan ID or Object
        # In our case, full_path is a list of node dicts already
        
        # Iterasi Mundur dari Finish
        reversed_path = list(reversed(full_path_ids)) 
        
        current_accumulated_cost = 0 
        
        for i, node in enumerate(reversed_path):
            # node is a dict
            node_id = node['id']
            stage = node['stage_prioritas'] if 'stage_prioritas' in node else 0
            nama = node['nama_lokasi']
            
            # Logika Deskripsi & Biaya
            if i == 0: # FINISH
                deskripsi = "🏁 Titik Akhir Misi"
                biaya_display = "Rp 0"
                status = "TARGET"
                current_accumulated_cost = 0 
            
            elif node_id == 'START' or i == len(reversed_path) - 1: # START
                deskripsi = "✅ KEPUTUSAN FINAL: Pintu masuk paling efisien."
                biaya_display = f"Rp {total_cost_final:,.0f}" # Total biaya global
                status = "START"
                
            else: # STAGE ANTARA
                deskripsi = f"Pintu keluar terbaik di Stage {stage}."
                status = "TRANSISI"
                biaya_display = "Lihat Detail" 

            # Menyusun Baris Tabel
            table_data.append({
                "Urutan Logika": f"Langkah {i+1} (Mundur)",
                "Tahap": f"Stage {stage}" if stage > 0 else ("Finish" if i==0 else "START"),
                "Lokasi Terpilih": nama,
                "Status": status,
                "Keterangan": deskripsi
            })

        # 3. Buat DataFrame
        df_summary = pd.DataFrame(table_data)
        
        # 4. Tampilkan dengan Styler agar cantik (Highlight Baris Akhir/Awal)
        st.dataframe(
            df_summary,
            column_config={
                "Urutan Logika": st.column_config.TextColumn("Alur Pikir"),
                "Tahap": st.column_config.TextColumn("Zona"),
                "Lokasi Terpilih": st.column_config.TextColumn("Lokasi Pemenang ⭐"),
                "Status": st.column_config.TextColumn("Peran Node"),
                "Keterangan": st.column_config.TextColumn("Alasan Algoritma")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Tampilkan Total Biaya Besar di Bawah Tabel
        st.metric("💰 Total Biaya Logistik Terhemat (Best Route)", f"Rp {total_cost_final:,.0f}")
        
    else:
        st.warning("Silakan jalankan simulasi rute terlebih dahulu.")

# --- TAB 2: BEDAH LOGIKA (DYNAMIC STORY) ---
with tab_detail:
    st.markdown("### 🕵️ Analisis Langkah-demi-Langkah (Dynamic Visualization)")
    
    if 'solver_instance' in locals() and top_k_solutions:
        # Define logs here so it is available
        logs = solver_instance.steps_log if hasattr(solver_instance, 'steps_log') else []
        
        best_sol = top_k_solutions[0]
        path_nodes = best_sol['full_path'] # [Start, Stage1, ..., Stage4]
        
        # Show logic from Last Stage (4) down to Start (0) - Backward
        # We need to find the node index in the path
        
        path_reversed = path_nodes[::-1]
        
        for i, node in enumerate(path_reversed):
            stage = node.get('stage_prioritas', 0)
            name = node['nama_lokasi']
            
            with st.container():
                st.markdown(f"#### {'🏁' if i==0 else '🔙'} LANGKAH {i+1}: Stage {stage} - {name}")
                
                if i == 0:
                    st.write(f"**Posisi:** Titik Akhir (Finish). **Biaya Sisa:** Rp 0.")
                    st.write("Misi selesai di sini.")
                else:
                     # Find the relevant log
                     # Log for node 'name' at 'stage'
                     relevant_log = next((l for l in logs if l['stage'] == stage and l['node'] == name), None)
                     
                     if relevant_log:
                         st.write(f"**Keputusan:** {relevant_log['detail']}")
                         
                         math_str = relevant_log['math']
                         math_str = math_str.replace("Biaya Lokal", "Biaya Keliling").replace("Lokal", "Biaya Keliling")
                         math_str = math_str.replace("Transisi", "Biaya Nyebrang")
                         math_str = math_str.replace("Future", "Biaya Sisa")
                         math_str = math_str.replace("Transport Awal", "Tiket Masuk")
                         
                         st.code(math_str, language="text")
                         
                         if "WINNER" in relevant_log['detail'] or "termurah" in relevant_log['detail']:
                             st.success(f"✅ TERPILIH: {name}")
                     else:
                         st.warning(f"Log detail tidak ditemukan untuk {name}")

            st.divider()

    else:
        st.write("Silakan jalankan simulasi.")

# --- TAB 3: STRUKTUR DP TABLE (MATRIX) ---
with tab_struktur:
    st.info("Ini adalah **Data Mentah Algoritma Dynamic Programming**. Tabel ini menunjukkan semua kemungkinan state (Simpul) yang dihitung oleh komputer.")
    
    if 'solver_instance' in locals() and hasattr(solver_instance, 'dp_table') and solver_instance.dp_table:
        dp_table = solver_instance.dp_table
        
        # Build Rows
        dp_rows = []
        # Sort keys to show Stages in order (Start -> Finish or Finish -> Start?)
        # Let's show Ascending sequence (0, 1, 2)
        
        stages = sorted(dp_table.keys())
        
        for i, stage in enumerate(stages):
            entries = dp_table[stage]
            for entry_id, val in entries.items():
                
                # Get Node Name
                node_row = df[df['id'] == entry_id]
                node_name = node_row.iloc[0]['nama_lokasi'] if not node_row.empty else str(entry_id)
                
                cost_finish = val.get('total_cost', 0)
                next_node_id = val.get('next_entry', '-')
                
                # Get Next Node Name
                next_name = "-"
                if next_node_id:
                     next_row = df[df['id'] == next_node_id]
                     next_name = next_row.iloc[0]['nama_lokasi'] if not next_row.empty else str(next_node_id)
                
                dp_rows.append({
                    "State (Tahapan Ke)": i, # Sequence
                    "Stage ID": stage,
                    "Titik (Node)": node_name,
                    "Cost to Finish (Future)": f"Rp {cost_finish:,.0f}",
                    "Target Selanjutnya": next_name
                })
                
        st.dataframe(pd.DataFrame(dp_rows), use_container_width=True)
    else:
        st.write("DP Table data not available yet.")
