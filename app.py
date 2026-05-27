import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random

# =========================================================
# CONFIG DASHBOARD
# =========================================================
st.set_page_config(
    page_title="Simulasi Pemilihan Jurusan ABM",
    page_icon="🎓",
    layout="wide"
)

# =========================================================
# CSS MARUN ELEGAN WIDGET UI
# =========================================================
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

# =========================================================
# KONSTANTA MODEL
# =========================================================
TOTAL_ITERATIONS = 1000
STABLE_WINDOW = 3

# =========================================================
# CLASS AGENT (BERBASIS MULTIPLE INTELLIGENCES)
# =========================================================
class StudentAgent:
    def __init__(self, profile):
        self.agent_id = profile["student_id"]
        self.interest = profile["interest"]
        self.ability = profile["ability"]
        self.confidence = profile["confidence"]
        self.influence = profile["influence"]
        self.resilience = profile.get("resilience", 0.5)
        self.distortion = profile.get("distortion", 0.3)

        # Posisi Agen pada Grid Spasial Toroidal (20x20)
        self.x = random.randint(0, 19)
        self.y = random.randint(0, 19)

        # State Awal Sistem Manajemen Keputusan
        self.state = "CONFUSED"
        self.decision_streak = 0
        self.chosen_major = None

        # Pemetaan Parameter Ke Teori Kecerdasan Majemuk (Multiple Intelligences)
        # Menghubungkan bakat & minat bawaan dari profil CSV menjadi klaster kecerdasan siswa
        self.intel_logical = round(self.ability * 0.9, 2)       # Untuk Teknik Informatika
        self.intel_linguistic = round(self.interest * 0.85, 2)  # Untuk Psikologi
        self.intel_spatial = round((self.ability + self.interest) / 2, 2) # Untuk DKV

    def move(self):
        # Pergerakan acak agen di lingkungan sekolah (Grid Spasial)
        self.x = (self.x + random.choice([-1, 0, 1])) % 20
        self.y = (self.y + random.choice([-1, 0, 1])) % 20

    def interact(self, nearby_agents):
        # Dampak konformitas sosial lokal terhadap tingkat kemantapan pilihan siswa
        decided_neighbors = sum(1 for agent in nearby_agents if agent.state == "DECIDED")
        self.confidence += decided_neighbors * 0.005
        self.confidence = max(0.0, min(1.0, self.confidence))

    def choose_major(self):
        # Pembobotan keputusan program studi berdasarkan dominasi Kecerdasan Majemuk
        scores = {
            "Teknik Informatika": (self.intel_logical * 0.5 + self.interest * 0.3 + self.confidence * 0.2),
            "Psikologi": (self.intel_linguistic * 0.5 + self.confidence * 0.3 + (1 - self.distortion) * 0.2),
            "DKV": (self.intel_spatial * 0.45 + (1 - self.influence) * 0.25 + self.confidence * 0.30)
        }
        self.chosen_major = max(scores, key=scores.get)

    def update_state(self, info_level, recommendation):
        # Tekanan Sosial / Kebisingan Informasi (Bandwagon Effect)
        social_pressure = self.influence * self.distortion * 0.03

        # Dukungan Intervensi Guru BK / Konseling Karir (Coping Pengarah Keputusan)
        bk_guidance = self.resilience * recommendation * 0.04

        # Rumus Pertumbuhan Kemantapan Keputusan Karir (Confidence) Siswa
        delta = ((self.interest * self.ability * info_level * 0.06) - social_pressure + bk_guidance)
        self.confidence = max(0.0, min(1.0, self.confidence + delta))

        # Aturan Transisi State Diagram
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

# =========================================================
# SIDEBAR CONTROLLER
# =========================================================
st.sidebar.header("🧭 Navigasi Menu")
tampilan_terpilih = st.sidebar.radio(
    "Pilih Tampilan Dashboard:",
    ["Ringkasan", "Visualisasi", "Analisis Statistik", "Data Mentah"]
)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Kontrol Grafik")
tampilkan_ambang = st.sidebar.checkbox("Tampilkan Batas Kestabilan (80%)", value=True)
tampilkan_label = st.sidebar.checkbox("Gunakan Titik Marker Garis", value=False)

st.sidebar.markdown("---")
st.sidebar.header("📁 Unggah Data & Skenario")
uploaded_file = st.sidebar.file_uploader("Upload CSV Data Siswa Baru:", type=["csv"])

scenario_type = st.sidebar.selectbox(
    "Pilih Skenario Intervensi:",
    ["Pasif", "Reaktif", "Preventif"]
)

run_btn = st.sidebar.button("▶️ Jalankan Simulasi 1000 Iterasi")

# =========================================================
# HEADER DASHBOARD
# =========================================================
st.markdown("""
    <div class="maroon-card">
        <h1>🎓 Dashboard Simulasi Dinamika Pemilihan Jurusan Kuliah</h1>
        <p>
        Implementasi Komputasi Spasial Agent-Based Modeling Menggunakan Teori Kombinasi Kecerdasan Majemuk (Multiple Intelligences)
        </p>
    </div>
""", unsafe_allow_html=True)

st.caption("Dashboard ini memproses visualisasi analitik spasial agen siswa dalam 1000 iterasi runtun waktu.")
st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# DATA SEED & GENERIC GENERATOR DETECTOR
# =========================================================
student_profiles = []

if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file)
        required_cols = ["student_id", "interest", "ability", "confidence", "influence", "resilience", "distortion"]
        
        if all(col in df_upload.columns for col in required_cols):
            student_profiles = df_upload[required_cols].to_dict(orient="records")
            st.sidebar.success(f"✅ Berhasil memuat {len(student_profiles)} siswa dari CSV!")
        else:
            st.sidebar.error("❌ Format kolom CSV tidak cocok dengan kebutuhan model!")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca file: {e}")

# Sintesis data cadangan jika file belum diunggah pengguna
if not student_profiles:
    random.seed(42)
    student_profiles = [
        {
            "student_id": i,
            "interest": random.uniform(0.4, 1.0),
            "ability": random.uniform(0.4, 1.0),
            "confidence": random.uniform(0.2, 0.5),
            "influence": random.uniform(0.1, 0.7),
            "resilience": random.uniform(0.3, 0.9),
            "distortion": random.uniform(0.1, 0.6)
        }
        for i in range(120)
    ]

# =========================================================
# CORE ENGINE SIMULASI RUNNER (1000 ITERASI)
# =========================================================
if run_btn or 'history_df' not in st.session_state:
    with st.spinner("Memproses Agen Spasial Menuju 1000 Iterasi..."):
        agents = [StudentAgent(profile) for profile in student_profiles]
        history_records = []

        # Loop penjelajahan waktu 1000 Iterasi penuh
        for step in range(TOTAL_ITERATIONS):
            
            # Penetapan Aturan Skenario Kebijakan BK
            if scenario_type == "Pasif":
                info_level, recommendation = 0.3, 0.0
            elif scenario_type == "Reaktif":
                info_level = 0.5
                last_decided = history_records[-1]["DECIDED"] if len(history_records) > 0 else 0
                recommendation = 0.8 if last_decided < (len(agents) * 0.5) else 0.2
            elif scenario_type == "Preventif":
                info_level, recommendation = 0.9, 0.8

            # Iterasi perilaku masing-masing agen dalam grid ruang
            for agent in agents:
                agent.move()
                
                # Optimasi pencarian tetangga lokal radius Manhattan jarak <= 2
                neighbors = [other for other in agents if other.agent_id != agent.agent_id and 
                             (abs(other.x - agent.x) + abs(other.y - agent.y)) <= 2]
                
                agent.interact(neighbors)
                agent.update_state(info_level, recommendation)

            # Hitung agregat status berkala pada akhir iterasi saat ini
            confused_count = sum(1 for a in agents if a.state == "CONFUSED")
            matching_count = sum(1 for a in agents if a.state == "MATCHING")
            decided_count = sum(1 for a in agents if a.state == "DECIDED")

            ti_count = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "Teknik Informatika")
            psi_count = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "Psikologi")
            dkv_count = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "DKV")

            history_records.append({
                "Iterasi": step + 1,
                "CONFUSED": confused_count,
                "MATCHING": matching_count,
                "DECIDED": decided_count,
                "Teknik Informatika": ti_count,
                "Psikologi": psi_count,
                "DKV": dkv_count
            })

        # Amankan luaran komputasi ke dalam cache aplikasi Streamlit
        st.session_state['history_df'] = pd.DataFrame(history_records)
        st.session_state['final_distribution'] = {
            "Teknik Informatika": ti_count,
            "Psikologi": psi_count,
            "DKV": dkv_count
        }
        st.session_state['current_scenario'] = scenario_type

# Penarikan data dari cache session state
df_res = st.session_state['history_df']
dist_res = st.session_state['final_distribution']
scen_res = st.session_state['current_scenario']

# =========================================================
# PANEL INTERFACE UTAMA BERDASARKAN MENU PILIHAN
# =========================================================

if tampilan_terpilih == "Ringkasan":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Skenario Aktif", value=scen_res)
    col2.metric(label="Total Langkah Waktu Run", value=f"{len(df_res)} Iterasi")
    col3.metric(label="Siswa Berhasil Kunci Jurusan", value=f"{df_res['DECIDED'].iloc[-1]} Siswa")
    col4.metric(label="Siswa Masih Bingung", value=f"{df_res['CONFUSED'].iloc[-1]} Siswa")

    st.markdown("---")
    st.subheader("📋 Interpretasi Analitik Model")
    st.info(f"""
    **Hasil Pemodelan Spasial:** Melalui pengujian sepanjang **{len(df_res)} iterasi**, sistem intervensi tipe **{scen_res}** berhasil mengarahkan kecenderungan siswa untuk memilih program studi secara rasional berdasarkan bakat bawaannya. 
    Hal ini ditandai dengan perubahan kurva kestabilan keputusan kelompok pada titik akhir simulasi.
    """)

elif tampilan_terpilih == "Visualisasi":
    st.subheader("📊 Grafik Tren Perubahan Status Pengambilan Keputusan")
    
    fig_line = px.line(
        df_res, x="Iterasi", y=["CONFUSED", "MATCHING", "DECIDED"],
        title="Dinamika Status Siswa Sepanjang Waktu",
        color_discrete_map={"CONFUSED": "#ef4444", "MATCHING": "#eab308", "DECIDED": "#22c55e"}
    )
    
    if tampilkan_ambang:
        total_students = len(student_profiles)
        fig_line.add_hline(y=total_students * 0.8, line_dash="dash", line_color="blue", annotation_text="Target Kelompok 80%")
        
    fig_line.update_traces(mode='lines+markers' if tampilkan_label else 'lines')
    st.plotly_chart(fig_line, use_container_width=True)

    # Grafik Batang Distribusi Program Studi Akhir
    st.markdown("---")
    st.subheader("🎯 Distribusi Peminat Program Studi Akhir")
    df_bar = pd.DataFrame({
        "Program Studi": list(dist_res.keys()),
        "Jumlah Pemiant": list(dist_res.values())
    })
    
    fig_bar = px.bar(
        df_bar, x="Program Studi", y="Jumlah Pemiant",
        color="Program Studi",
        color_discrete_sequence=["#3b82f6", "#a855f7", "#f59e0b"]
    )
    st.plotly_chart(fig_bar, use_container_width=True)

elif tampilan_terpilih == "Analisis Statistik":
    st.subheader("📈 Analisis Deskriptif Hasil Agregat Simulasi")
    st.write("Statistik deskriptif sekuensial transisi dari seluruh iterasi berjalan:")
    st.dataframe(df_res.describe(), use_container_width=True)

elif tampilan_terpilih == "Data Mentah":
    st.subheader("🗂️ Tabel Log Matriks Hasil Simulasi")
    st.write("Silakan periksa lembar baris mentah per iterasi di bawah ini untuk kebutuhan pelaporan draft jurnal:")
    st.dataframe(df_res, use_container_width=True)
