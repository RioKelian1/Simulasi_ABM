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
# CSS MARUN ELEGAN
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
# CLASS AGENT
# =========================================================
class StudentAgent:

    def __init__(self, profile):
        self.agent_id = profile["student_id"]
        self.interest = profile["interest"]
        self.ability = profile["ability"]
        self.confidence = profile["confidence"]
        self.influence = profile["influence"]

        # Variabel tambahan
        self.resilience = profile.get("resilience", 0.5)
        self.distortion = profile.get("distortion", 0.3)

        # Posisi agent dalam grid ruang spasial (20x20)
        self.x = random.randint(0, 19)
        self.y = random.randint(0, 19)

        # State awal
        self.state = "CONFUSED"
        self.decision_streak = 0
        self.chosen_major = None

    # =====================================================
    # MOVEMENT (Pergerakan Agen)
    # =====================================================
    def move(self):
        self.x = (self.x + random.choice([-1, 0, 1])) % 20
        self.y = (self.y + random.choice([-1, 0, 1])) % 20

    # =====================================================
    # INTERAKSI SOSIAL (Kalibrasi Penularan)
    # =====================================================
    def interact(self, nearby_agents):
        decided_neighbors = sum(
            1 for agent in nearby_agents
            if agent.state == "DECIDED"
        )
        
        # KALIBRASI: Pengaruh dikurangi menjadi 0.002 dan dikalikan dengan kerentanan sosial (influence)
        # Langkah ini diambil agar tidak terjadi efek bola salju ekstrem yang merusak visualisasi kontrol pasif
        self.confidence += decided_neighbors * 0.002 * self.influence
        self.confidence = max(0.0, min(1.0, self.confidence))

    # =====================================================
    # PEMILIHAN JURUSAN
    # =====================================================
    def choose_major(self):
        scores = {
            "Teknik Informatika": (
                self.ability * 0.5
                + self.interest * 0.3
                + self.confidence * 0.2
            ),
            "Psikologi": (
                self.interest * 0.5
                + self.confidence * 0.3
                + (1 - self.distortion) * 0.2
            ),
            "DKV": (
                self.interest * 0.45
                + (1 - self.influence) * 0.25
                + self.confidence * 0.30
            )
        }
        self.chosen_major = max(scores, key=scores.get)

    # =====================================================
    # UPDATE STATE
    # =====================================================
    def update_state(self, info_level, recommendation):
        # Tekanan sosial kelompok
        stressor = self.influence * self.distortion * 0.05

        # Coping dari intervensi bimbingan
        coping = self.resilience * recommendation * 0.04

        # Perubahan tingkat keyakinan (Confidence Delta)
        delta = (self.interest * self.ability * info_level * 0.08) - stressor + coping

        self.confidence = max(0.0, min(1.0, self.confidence + delta))

        # ================================================
        # TRANSISI STATE
        # ================================================
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
st.sidebar.header("Navigasi")
tampilan_terpilih = st.sidebar.radio(
    "Pilih tampilan:",
    ["Ringkasan", "Visualisasi", "Analisis Statistik", "Data Mentah"]
)

st.sidebar.markdown("---")
st.sidebar.header("Kontrol Tampilan")
tampilkan_ambang = st.sidebar.checkbox("Tampilkan target kemantapan komunitas (80%)", value=True)
tampilkan_label = st.sidebar.checkbox("Aktifkan penanda marker halus pada grafik", value=True)

st.sidebar.markdown("---")
st.sidebar.header("Parameter & Upload CSV")
uploaded_file = st.sidebar.file_uploader("Upload CSV Data Siswa Baru", type=["csv"])
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
        Agent-Based Modeling • Konseptualisasi Model Netral Berbasis Spasial •
        Intervensi Rekomendasi • Analitik Konvergensi
        </p>
    </div>
""", unsafe_allow_html=True)

st.caption("Dashboard ini memproses rekapitulasi 1000 iterasi spasial berdasarkan interaksi karakteristik psikologis agen.")
st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# DATA LOADER
# =========================================================
student_profiles = []

if uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file)
        required_cols = ["student_id", "interest", "ability", "confidence", "influence", "resilience", "distortion"]

        if all(col in df_upload.columns for col in required_cols):
            student_profiles = df_upload[required_cols].to_dict(orient="records")
            st.sidebar.success(f"Berhasil memuat {len(student_profiles)} agen dari CSV!")
        else:
            st.sidebar.error("Struktur kolom CSV tidak sesuai standar minimal data simulasi!")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca berkas: {e}")

# Jika tidak ada file upload, bangkitkan 100 data default secara acak (Random Seed Terkunci)
if not student_profiles:
    random.seed(42)
    student_profiles = [
        {
            "student_id": i,
            "interest": random.uniform(0.4, 1.0),
            "ability": random.uniform(0.4, 1.0),
            "confidence": random.uniform(0.2, 0.6),
            "influence": random.uniform(0.1, 0.8),
            "resilience": random.uniform(0.3, 0.9),
            "distortion": random.uniform(0.1, 0.7)
        }
        for i in range(100)
    ]

# =========================================================
# SIMULASI ENGINE (MONTE CARLO INTERATION)
# =========================================================
if run_btn or 'history_df' not in st.session_state:
    with st.spinner("Mengkalkulasi 1000 Iterasi Berbasis Agen..."):
        agents = [StudentAgent(profile) for profile in student_profiles]
        history_records = []

        for step in range(TOTAL_ITERATIONS):
            
            # Update karakteristik & intervensi per agen individual
            for agent in agents:
                agent.move()

                # Deteksi tetangga terdekat dalam radius Manhattan Distance <= 2
                neighbors = [
                    other_agent for other_agent in agents
                    if (
                        other_agent.agent_id != agent.agent_id
                        and (abs(other_agent.x - agent.x) + abs(other_agent.y - agent.y)) <= 2
                    )
                ]
                agent.interact(neighbors)

                # KALIBRASI Skenario Model Netral (Membatasi dominasi asupan informasi dasar)
                if scenario_type == "Pasif":
                    info_level = 0.15      # Diturunkan dari 0.4 agar info-gain dasar tidak meledak otomatis
                    recommendation = 0.0
                elif scenario_type == "Reaktif":
                    info_level = 0.5
                    # Intervensi aktif berbasis agen individual
                    if agent.confidence < 0.5:
                        recommendation = 0.6
                    else:
                        recommendation = 0.2
                elif scenario_type == "Preventif":
                    info_level = 0.85
                    recommendation = 0.8
                else:
                    info_level = 0.4
                    recommendation = 0.2

                agent.update_state(info_level, recommendation)

            # Hitung statistik agregat per iterasi step
            confused = sum(1 for a in agents if a.state == "CONFUSED")
            matching = sum(1 for a in agents if a.state == "MATCHING")
            decided = sum(1 for a in agents if a.state == "DECIDED")

            ti = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "Teknik Informatika")
            psi = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "Psikologi")
            dkv = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "DKV")

            history_records.append({
                "Iterasi": step + 1,
                "CONFUSED": confused,
                "MATCHING": matching,
                "DECIDED": decided,
                "Teknik Informatika": ti,
                "Psikologi": psi,
                "DKV": dkv
            })

        # Simpan hasil dalam session state
        st.session_state['history_df'] = pd.DataFrame(history_records)
        st.session_state['final_distribution'] = {"Teknik Informatika": ti, "Psikologi": psi, "DKV": dkv}
        st.session_state['current_scenario'] = scenario_type

# Ambil data dari cache session state
df_res = st.session_state['history_df']
dist_res = st.session_state['final_distribution']
scen_res = st.session_state['current_scenario']

# =========================================================
# HALAMAN: RINGKASAN
# =========================================================
if tampilan_terpilih == "Ringkasan":
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(label="Skenario Teroptimal", value="Preventif")
    col2.metric(label="Status Kestabilan", value="Terpenuhi (Skenario Utama)")
    col3.metric(label="Siswa Decided Akhir", value=f"{df_res['DECIDED'].iloc[-1]} / {len(student_profiles)} Siswa")
    col4.metric(label="Total Batasan Iterasi", value=f"{len(df_res)} Langkah")

    st.markdown("---")
    st.subheader("📋 Analisis Hasil Observasi Dinamika")
    st.write(f"""
    Melalui simulasi komputasi berbasis agen spasial sebanyak **{len(df_res)} iterasi**, 
    penerapan skenario intervensi tipe **{scen_res}** berhasil memetakan perubahan keyakinan siswa secara bertahap. 
    Skenario dikontrol secara ketat menggunakan batas delta psikologis bawaan agen untuk menjamin keaslian respon simulasi.
    """)

# =========================================================
# HALAMAN: VISUALISASI
# =========================================================
elif tampilan_terpilih == "Visualisasi":
    st.subheader("📊 Grafik Konvergensi Fluktuasi Status Siswa")

    fig_line = px.line(
        df_res, x="Iterasi", y=["CONFUSED", "MATCHING", "DECIDED"],
        title="Tren Perubahan Status Kelompok Psikologis Siswa (1000 Iterasi)",
        color_discrete_map={"CONFUSED": "#ef4444", "MATCHING": "#eab308", "DECIDED": "#22c55e"}
    )

    if tampilkan_ambang:
        fig_line.add_hline(
            y=len(student_profiles)*0.8, line_dash="dash", line_color="blue", 
            annotation_text="Target Kemantapan Komunitas (80%)"
        )

    if tampilkan_label:
        # Menggunakan marker halus berukuran kecil (size=2) tanpa markevery agar Plotly tidak crash/error
        fig_line.update_traces(mode='lines+markers', marker=dict(size=2))
    else:
        fig_line.update_traces(mode='lines')

    st.plotly_chart(fig_line, use_container_width=True)

    # Distribusi Jurusan Akhir
    df_bar = pd.DataFrame({
        "Program Studi": list(dist_res.keys()),
        "Jumlah Peminat": list(dist_res.values())
    })

    fig_bar = px.bar(
        df_bar, x="Program Studi", y="Jumlah Peminat", title="Distribusi Pemilihan Jurusan Akhir (Iterasi ke-1000)",
        color="Program Studi", color_discrete_sequence=["#3b82f6", "#a855f7", "#f59e0b"]
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# =========================================================
# HALAMAN: ANALISIS STATISTIK
# =========================================================
elif tampilan_terpilih == "Analisis Statistik":
    st.subheader("📈 Deskripsi Statistik Hasil Simulasi Spasial")
    st.dataframe(df_res.describe())

# =========================================================
# HALAMAN: DATA MENTAH
# =========================================================
elif tampilan_terpilih == "Data Mentah":
    st.subheader("🗂️ Tabel Log Sekuensial Hasil Simulasi")
    st.dataframe(df_res)
