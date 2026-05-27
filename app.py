import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random

# =========================================================
# INITIAL CONFIGURATION & THEME STYLING
# =========================================================
st.set_page_config(
    page_title="Dashboard ABM Pemilihan Jurusan",
    page_icon="🎓",
    layout="wide"
)

# Custom Elegant Maroon Professional UI styling Container
st.markdown("""
    <style>
    .maroon-header {
        background-color: #6b1d24;
        color: white;
        padding: 30px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    .maroon-header h1 { color: white !important; font-weight: 700; margin: 0; }
    .maroon-header p { color: #f4e3e3 !important; font-size: 1rem; margin-top: 8px; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# AGENT DEFINITION WITH MULTIPLE INTELLIGENCES THEORY
# =========================================================
class StudentAgent:
    def __init__(self, agent_id, b_it, b_psi, b_dkv, inf, conf):
        self.id = agent_id
        self.bakat_it = b_it
        self.bakat_psikologi = b_psi
        self.bakat_dkv = b_dkv
        self.influence = inf
        self.confidence = conf
        
        self.x = random.randint(0, 19)
        self.y = random.randint(0, 19)
        self.state = "CONFUSED"
        self.chosen_major = None
        self.streak = 0

    def move(self):
        self.x = (self.x + random.choice([-1, 0, 1])) % 20
        self.y = (self.y + random.choice([-1, 0, 1])) % 20

    def update_logic(self, nearby_count, info_lvl, guidance, distortion):
        social_pressure = nearby_count * distortion * 0.02
        
        # Evaluasi kecocokan bakat internal
        scores = {"Teknik Informatika": self.bakat_it, "Psikologi": self.bakat_psikologi, "DKV": self.bakat_dkv}
        self.chosen_major = max(scores, key=scores.get)
        talent_match = scores[self.chosen_major]
        
        # Perubahan nilai kemantapan (Confidence)
        delta = (talent_match * info_lvl * 0.08) - (social_pressure * self.influence) + (guidance * 0.05)
        self.confidence = max(0.0, min(1.0, self.confidence + delta))
        
        if self.confidence >= 0.8:
            self.streak += 1
            if self.streak >= 3: self.state = "DECIDED"
        elif self.confidence >= 0.5:
            self.state = "MATCHING"
            self.streak = 0
        else:
            self.state = "CONFUSED"
            self.streak = 0

# =========================================================
# SIDEBAR CONTROLLER INTERACTION
# =========================================================
st.sidebar.header("🕹️ Kontrol Parameter Simulasi")
selected_scenario = st.sidebar.selectbox(
    "Pilih Skenario Intervensi:",
    [
        "Pasif (Tanpa Intervensi)", 
        "Reaktif (Bimbingan Saat Bingung)", 
        "Preventif (Edukasi Rutin Berbasis Bakat)", 
        "Distorsi Sosial Tinggi (Tren Ikut Teman)"
    ]
)

pop_size = st.sidebar.slider("Jumlah Populasi Agen Siswa", min_value=50, max_value=300, value=150, step=10)
simulation_steps = st.sidebar.slider("Batas Iterasi Waktu (Steps)", min_value=50, max_value=500, value=150, step=10)

run_btn = st.sidebar.button("▶️ Jalankan Komputasi Model")

# =========================================================
# HEADER COMPONENT
# =========================================================
st.markdown("""
    <div class="maroon-header">
        <h1>🎓 Dashboard Simulasi Pemilihan Jurusan Kuliah Berbasis Kecerdasan Majemuk</h1>
        <p>Implementasi Komputasi Spasial Agent-Based Modeling — Progres Evaluasi Akhir Minggu 16</p>
    </div>
""", unsafe_allow_html=True)

# =========================================================
# CORE SIMULATION ENGINE RUNNER
# =========================================================
if 'initialized' not in st.session_state or run_btn:
    # Membangkitkan populasi data awal secara independen dan heterogen
    np.random.seed(42)
    agents_pool = []
    for i in range(pop_size):
        agents_pool.append(StudentAgent(
            agent_id=i,
            b_it=round(random.uniform(0.3, 1.0), 2),
            b_psi=round(random.uniform(0.3, 1.0), 2),
            b_dkv=round(random.uniform(0.3, 1.0), 2),
            inf=round(random.uniform(0.2, 0.8), 2),
            conf=round(random.uniform(0.1, 0.4), 2)
        ))
        
    history_records = []
    
    # Looping jalannya langkah sekuensial waktu simulasi
    for step in range(simulation_steps):
        for agent in agents_pool:
            agent.move()
            
            # Deteksi kepadatan tetangga lokal dalam jangkauan grid
            neighbors_count = sum(
                1 for p in agents_pool 
                if p.id != agent.id and (abs(p.x - agent.x) + abs(p.y - agent.y)) <= 2 and p.state == "DECIDED"
            )
            
            # Pengkondisian logika parameter berdasarkan tipe skenario yang dipilih
            if selected_scenario == "Pasif (Tanpa Intervensi)":
                info_lvl, guidance, distortion = 0.2, 0.0, 0.4
            elif selected_scenario == "Reaktif (Bimbingan Saat Bingung)":
                info_lvl, distortion = 0.4, 0.3
                guidance = 0.7 if agent.confidence < 0.4 else 0.1
            elif selected_scenario == "Preventif (Edukasi Rutin Berbasis Bakat)":
                info_lvl, guidance, distortion = 0.8, 0.6, 0.2
            elif selected_scenario == "Distorsi Sosial Tinggi (Tren Ikut Teman)":
                info_lvl, guidance, distortion = 0.3, 0.1, 0.9
                
            agent.update_logic(neighbors_count, info_lvl, guidance, distortion)
            
        history_records.append({
            "Iterasi": step + 1,
            "CONFUSED": sum(1 for a in agents_pool if a.state == "CONFUSED"),
            "MATCHING": sum(1 for a in agents_pool if a.state == "MATCHING"),
            "DECIDED": sum(1 for a in agents_pool if a.state == "DECIDED"),
            "Teknik Informatika": sum(1 for a in agents_pool if a.state == "DECIDED" and a.chosen_major == "Teknik Informatika"),
            "Psikologi": sum(1 for a in agents_pool if a.state == "DECIDED" and a.chosen_major == "Psikologi"),
            "DKV": sum(1 for a in agents_pool if a.state == "DECIDED" and a.chosen_major == "DKV")
        })
        
    st.session_state['df_log'] = pd.DataFrame(history_records)
    st.session_state['initialized'] = True
    st.session_state['last_scenario'] = selected_scenario

# Load data hasil eksekusi simulasi dari session state cache
df_res = st.session_state['df_log']
scen_active = st.session_state['last_scenario']

# =========================================================
# VISUAL RENDERING PLATFORM (TAMPILAN UTAMA)
# =========================================================
col1, col2, col3 = st.columns(3)
col1.metric("Skenario Aktif", scen_active)
col2.metric("Siswa Berhasil Decided", f"{df_res['DECIDED'].iloc[-1]} / {pop_size} Agen")
col3.metric("Stabilitas Kelompok", "Konvergen" if df_res['DECIDED'].iloc[-1] > (pop_size * 0.5) else "Fluktuatif/Ambigur")

st.markdown("---")

# Layout Grafik Dua Kolom
g_col1, g_col2 = st.columns(2)

with g_col1:
    st.subheader("📈 Tren Transisi Perubahan Status Psikologis")
    fig_line = px.line(
        df_res, x="Iterasi", y=["CONFUSED", "MATCHING", "DECIDED"],
        color_discrete_map={"CONFUSED": "#ef4444", "MATCHING": "#eab308", "DECIDED": "#22c55e"},
        labels={"value": "Jumlah Siswa", "variable": "Status"}
    )
    st.plotly_chart(fig_line, use_container_width=True)

with g_col2:
    st.subheader("📊 Distribusi Pilihan Program Studi Akhir")
    final_counts = {
        "Program Studi": ["Teknik Informatika", "Psikologi", "DKV"],
        "Jumlah Peminat": [df_res["Teknik Informatika"].iloc[-1], df_res["Psikologi"].iloc[-1], df_res["DKV"].iloc[-1]]
    }
    fig_bar = px.bar(
        final_counts, x="Program Studi", y="Jumlah Peminat",
        color="Program Studi", color_discrete_sequence=["#3b82f6", "#a855f7", "#f59e0b"]
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("🗂️ Data Mentah Log Hasil Simulasi Terakhir")
st.dataframe(df_res, use_container_width=True)
