import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time

# --- LOGIKA AGENT (Disesuaikan dari kode Anda) ---
class Agent:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.state = "CONFUSED"
        self.confidence = np.random.rand()
        self.chosen_major = None

    def move(self, grid_size):
        self.x = (self.x + np.random.choice([-1, 0, 1])) % grid_size
        self.y = (self.y + np.random.choice([-1, 0, 1])) % grid_size

    def interact(self, nearby_decided_count):
        if self.state == "CONFUSED":
            # Semakin banyak teman yang sudah memilih, confidence naik
            self.confidence += nearby_decided_count * 0.05
            if self.confidence > 0.8:
                self.state = "DECIDED"
                self.chosen_major = np.random.choice(["TI", "Psikologi", "DKV"])

# --- STREAMLIT UI ---
st.set_page_config(page_title="Career Simulation Dashboard", layout="wide")
st.title("🎓 Dashboard Simulasi Pemilihan Jurusan")

# Sidebar - Parameter
st.sidebar.header("Parameter Simulasi")
num_agents = st.sidebar.slider("Jumlah Mahasiswa", 10, 200, 50)
grid_size = st.sidebar.slider("Ukuran Lingkungan (Grid)", 10, 50, 20)
steps = st.sidebar.slider("Jumlah Langkah (Steps)", 10, 100, 50)
run_btn = st.sidebar.button("Run Simulation")

if run_btn:
    # Inisialisasi Agen
    agents = [Agent(i, np.random.randint(0, grid_size), np.random.randint(0, grid_size)) for i in range(num_agents)]
    
    # Placeholder untuk Grafik Live
    chart_placeholder = st.empty()
    stats_placeholder = st.empty()
    
    history = []

    # Loop Simulasi
    for t in range(steps):
        decided_count = 0
        major_counts = {"TI": 0, "Psikologi": 0, "DKV": 0}
        
        # Simulasikan interaksi sederhana (sebagai contoh dashboard)
        for a in agents:
            a.move(grid_size)
            # Logika interaksi: hitung agen sekitar yang DECIDED (randomized for demo)
            nearby = np.random.randint(0, 3) 
            a.interact(nearby)
            
            if a.state == "DECIDED":
                decided_count += 1
                major_counts[a.chosen_major] += 1
        
        # Simpan data history
        history.append({"Step": t, "Decided": decided_count, "Confused": num_agents - decided_count})
        df_history = pd.DataFrame(history)

        # Update Visualisasi
        with chart_placeholder.container():
            col1, col2 = st.columns(2)
            with col1:
                fig_line = px.line(df_history, x="Step", y=["Decided", "Confused"], 
                                   title="Trend Keputusan Mahasiswa", color_discrete_sequence=["#deff9a", "#f87171"])
                st.plotly_chart(fig_line, use_container_width=True)
            with col2:
                df_major = pd.DataFrame(list(major_counts.items()), columns=["Major", "Count"])
                fig_bar = px.bar(df_major, x="Major", y="Count", title="Distribusi Jurusan Terpilih", color="Major")
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Update Metrics
        stats_placeholder.metric("Convergence Rate", f"{(decided_count/num_agents)*100:.1f}%")
        
        time.sleep(0.05) # Animasi pelan

    st.success("Simulasi Selesai!")

Slide deck Anda mengenai Dashboard Simulasi ini sudah siap! Silakan dipelajari dan beri tahu saya jika ada bagian yang ingin disesuaikan untuk kebutuhan UAS Anda.