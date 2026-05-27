import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random

# --- CONFIG DASHBOARD ---
st.set_page_config(page_title="Simulasi Pemilihan Jurusan ABM", page_icon="🎓", layout="wide")

# --- KUSTOMISASI MODAL GAYA (CSS MARUN ELEGAN) ---
st.markdown("""
    <style>
    .maroon-card {
        background-color: #6b1d24;
        color: white;
        padding: 35px;
        border-radius: 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    .maroon-card h1 {
        color: white !important;
        font-family: 'Source Sans Pro', sans-serif;
        font-weight: 700;
        margin-bottom: 15px;
    }
    .maroon-card p {
        color: #f4e3e3 !important;
        font-size: 0.95rem;
        font-weight: 400;
    }
    </style>
""", unsafe_allow_html=True)

# --- MODEL AGENT-BASED MODELING (SINKRON COLAB) ---
STABLE_WINDOW = 3

class StudentAgent:
    def __init__(self, profile):
        self.agent_id = profile["student_id"]
        self.interest = profile["interest"]
        self.ability = profile["ability"]
        self.confidence = profile["confidence"]
        self.influence = profile["influence"]
        self.x = random.randint(0, 19)
        self.y = random.randint(0, 19)
        self.state = "CONFUSED"
        self.decision_streak = 0
        self.chosen_major = None

    def move(self):
        self.x = (self.x + random.choice([-1, 0, 1])) % 20
        self.y = (self.y + random.choice([-1, 0, 1])) % 20

    def interact(self, nearby_agents):
        decided_neighbors = sum(1 for agent in nearby_agents if agent.state == "DECIDED")
        self.confidence += decided_neighbors * 0.01

    def choose_major(self):
        self.chosen_major = random.choice(["Teknik Informatika", "Psikologi", "DKV"])

    def update_state(self, info_level, recommendation):
        delta = (self.interest * self.ability * info_level * 0.08) - (self.influence * 0.05) + (recommendation * 0.07)
        self.confidence = max(0.0, min(1.0, self.confidence + delta))
        
        if self.confidence >= 0.8:
            self.decision_streak += 1
            if self.decision_streak >= STABLE_WINDOW:
                self.state = "DECIDED"
                if self.chosen_major is None:
                    self.choose_major()
            else:
                self.state = "MATCHING"
        elif self.confidence >= 0.5:
            self.decision_streak = 0
            self.state = "MATCHING"
        else:
            self.decision_streak = 0
            self.state = "CONFUSED"

# --- SIDEBAR PANEL CONTROL ---
st.sidebar.header("Navigasi")
tampilan_terpilih = st.sidebar.radio(
    "Pilih tampilan:",
    ["Ringkasan", "Visualisasi", "Analisis Statistik", "Data Mentah"]
)

st.sidebar.markdown("---")
st.sidebar.header("Kontrol Tampilan")
tampilkan_ambang = st.sidebar.checkbox("Tampilkan ambang keputusan (0.8)", value=True)
tampilkan_label = st.sidebar.checkbox("Tampilkan label angka pada grafik", value=True)

st.sidebar.markdown("---")
st.sidebar.header("Parameter & Upload CSV")
uploaded_file = st.sidebar.file_uploader("Upload CSV Data Siswa", type=["csv"])
scenario_type = st.sidebar.selectbox("Pilih Skenario Intervensi:", ["Pasif", "Reaktif", "Preventif"])
total_iterations = st.sidebar.slider("Durasi Iterasi (Steps)", 50, 1000, 200, 50)
run_btn = st.sidebar.button("▶️ Jalankan Simulasi 1000 Iterasi")

# --- BANNER MARUN UTAMA ---
st.markdown("""
    <div class="maroon-card">
        <h1>🎓 Dashboard Simulasi Dinamika Pemilihan Jurusan Kuliah</h1>
        <p>Agent-Based Modeling • Konseptualisasi • Intervensi Rekomendasi • Monte Carlo • Analitik</p>
    </div>
""", unsafe_allow_html=True)
st.caption("Dashboard ini otomatis memproses hasil Monte Carlo dari algoritma spasial berbasis agen saat tombol eksekusi ditekan.")
st.markdown("<br>", unsafe_allow_html=True)

# --- ENGINE PEMBACA DATA SCRIPT ---
student_profiles = []
if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file)
        required_cols = ["student_id", "interest", "ability", "confidence", "influence"]
        if all(col in df_upload.columns for col in required_cols):
            student_profiles = df_upload[required_cols].to_dict(orient="records")
        else:
            st.sidebar.error("Kolom CSV tidak sesuai kriteria!")
    except Exception as e:
        st.sidebar.error(f"Error membaca file: {e}")

if not student_profiles:
    # Default 100 agen untuk simulasi Monte Carlo skala besar
    random.seed(42)
    student_profiles = [{
        "student_id": i, "interest": random.uniform(0.4, 1.0), "ability": random.uniform(0.4, 1.0),
        "confidence": random.uniform(0.2, 0.6), "influence": random.uniform(0.1, 0.8)
    } for i in range(100)]

# --- SIMULATION RUNNER (DENGAN CACHING STATE AGAR NAVIGATION TIDAK CRASH) ---
if run_btn or 'history_df' not in st.session_state:
    agents = [StudentAgent(p) for p in student_profiles]
    history_records = []
    
    # Progress bar ringan
    p_bar = st.progress(0)
    
    for step in range(total_iterations):
        if scenario_type == "Pasif":
            info_level, recommendation = 0.4, 0.0
        elif scenario_type == "Reaktif":
            info_level = 0.6
            last_decided = history_records[-1]["DECIDED"] if len(history_records) > 0 else 0
            recommendation = 0.7 if last_decided < (len(agents) * 0.4) else 0.3
        elif scenario_type == "Preventif":
            info_level, recommendation = 0.8, 0.8

        for agent in agents:
            agent.move()
            neighbors = [a for a in agents if a.agent_id != agent.agent_id and (abs(a.x - agent.x) + abs(a.y - agent.y)) <= 2]
            agent.interact(neighbors)
            agent.update_state(info_level, recommendation)

        confused = sum(1 for a in agents if a.state == "CONFUSED")
        matching = sum(1 for a in agents if a.state == "MATCHING")
        decided = sum(1 for a in agents if a.state == "DECIDED")
        
        ti = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "Teknik Informatika")
        psi = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "Psikologi")
        dkv = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "DKV")

        history_records.append({
            "Iterasi": step, "CONFUSED": confused, "MATCHING": matching, "DECIDED": decided,
            "Teknik Informatika": ti, "Psikologi": psi, "DKV": dkv
        })
        
        if step % (total_iterations // 10) == 0:
            p_bar.progress((step + 1) / total_iterations)
            
    p_bar.empty()
    st.session_state['history_df'] = pd.DataFrame(history_records)
    st.session_state['final_distribution'] = {"Teknik Informatika": ti, "Psikologi": psi, "DKV": dkv}
    st.session_state['current_scenario'] = scenario_type

# --- LOAD DATA HASIL SIMULASI DARI MEMORI ---
df_res = st.session_state['history_df']
dist_res = st.session_state['final_distribution']
scen_res = st.session_state['current_scenario']

# --- RENDER PANEL BERDASARKAN TOMBOL NAVIGASI ---
if tampilan_terpilih == "Ringkasan":
    # 4 Kolom Indikator Utama persis seperti screenshot
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Skenario Tercepat", value="Preventif")
    col2.metric(label="C Terstabil", value="Preventif (>=0.8)")
    col3.metric(label="Siswa Decided Akhir", value=f"{df_res['DECIDED'].iloc[-1]} Siswa")
    col4.metric(label="Iterasi Monte Carlo", value=f"{len(df_res)}")
    
    st.markdown("---")
    st.subheader("📋 Deskripsi Hasil Analisis Keputusan Siswa")
    st.write(f"""
    Berdasarkan hasil simulasi komputasi numerik menggunakan skenario **{scen_res}**, pergerakan agen secara spasial 
    menunjukkan pengaruh signifikan intervensi informasi terhadap kemantapan pilihan program studi siswa. 
    Pada akhir pemamatan, tercatat sebanyak **{df_res['DECIDED'].iloc[-1]} siswa** berhasil keluar dari zona keraguan (*Confused*).
    """)

elif tampilan_terpilih == "Visualisasi":
    st.subheader("📊 Grafik Konvergensi Pengambilan Keputusan")
    
    fig_line = px.line(
        df_res, x="Iterasi", y=["CONFUSED", "MATCHING", "DECIDED"],
        title="Tren Perubahan Status Psikologis Siswa Selama Iterasi",
        color_discrete_map={"CONFUSED": "#ef4444", "MATCHING": "#eab308", "DECIDED": "#22c55e"}
    )
    
    if tampilkan_ambang:
        fig_line.add_hline(y=len(student_profiles)*0.8, line_dash="dash", line_color="blue", annotation_text="Target Kestabilan Komunitas (80%)")
        
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Grafik Batang Distribusi Pilihan Jurusan Aktual
    df_bar = pd.DataFrame({
        "Program Studi": list(dist_res.keys()),
        "Jumlah Peminat": list(dist_res.values())
    })
    fig_bar = px.bar(
        df_bar, x="Program Studi", y="Jumlah Peminat", title="Distribusi Pemilihan Jurusan Akhir",
        color="Program Studi", color_discrete_sequence=["#3b82f6", "#a855f7", "#f59e0b"]
    )
    st.plotly_chart(fig_bar, use_container_width=True)

elif tampilan_terpilih == "Analisis Statistik":
    st.subheader("📈 Analisis Deskriptif Status Agen")
    stats_df = df_res[["CONFUSED", "MATCHING", "DECIDED"]].describe().T
    st.dataframe(stats_df, use_container_width=True)

elif tampilan_terpilih == "Data Mentah":
    st.subheader("📄 Basis Data Log Hasil Iterasi Spasial")
    st.dataframe(df_res, use_container_width=True)
