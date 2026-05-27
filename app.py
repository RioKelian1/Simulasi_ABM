import streamlit as st
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
import seaborn as sns

# ==========================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(
    page_title="Simulasi Pemilihan Jurusan Kuliah (ABM)",
    page_icon="🎯",
    layout="wide"
)

# Set tema visualisasi dasar
sns.set_theme(style="whitegrid")

# ==========================================
# 2. BLUEPRINT AGEN & LINGKUNGAN SIMULASI
# ==========================================
STABLE_WINDOW = 3

class StudentAgent:
    def __init__(self, profile_data):
        self.agent_id = profile_data["student_id"]
        self.interest = profile_data["interest"]
        self.ability = profile_data["ability"]
        self.confidence = profile_data["confidence"]
        self.influence = profile_data["influence"]
        self.resilience = profile_data.get("resilience", 0.5)
        self.distortion = profile_data.get("distortion", 0.3)
        
        # Posisi Spasial Awal (Grid Sekolah 20x20)
        self.x = random.randint(0, 19)
        self.y = random.randint(0, 19)
        
        self.state = "CONFUSED"
        self.decision_streak = 0
        self.chosen_major = None
        self.decision_time = None

        # Atribut Kecerdasan Majemuk (Multiple Intelligences)
        self.intel_logical = round(self.ability * 0.9, 2)
        self.intel_linguistic = round(self.interest * 0.85, 2)
        self.intel_spatial = round((self.ability + self.interest) / 2, 2)

    def move(self):
        self.x = (self.x + random.choice([-1, 0, 1])) % 20
        self.y = (self.y + random.choice([-1, 0, 1])) % 20

    def interact(self, nearby_agents):
        if self.state == "DECIDED":
            return
        decided_neighbors = sum(1 for agent in nearby_agents if agent.state == "DECIDED")
        self.confidence += decided_neighbors * 0.005
        self.confidence = max(0.0, min(1.0, self.confidence))

    def choose_major(self):
        scores = {
            "Teknik Informatika": (self.intel_logical * 0.5 + self.interest * 0.3 + self.confidence * 0.2),
            "Psikologi": (self.intel_linguistic * 0.5 + self.confidence * 0.3 + (1 - self.distortion) * 0.2),
            "DKV": (self.intel_spatial * 0.45 + (1 - self.influence) * 0.25 + self.confidence * 0.30)
        }
        self.chosen_major = max(scores, key=scores.get)

    def update_state(self, info_level, recommendation, current_step):
        if self.state == "DECIDED":
            return

        social_pressure = self.influence * self.distortion * 0.03
        bk_guidance = self.resilience * recommendation * 0.04
        
        delta = ((self.interest * self.ability * info_level * 0.06) - social_pressure + bk_guidance)
        self.confidence = max(0.0, min(1.0, self.confidence + delta))

        if self.confidence >= 0.8:
            self.decision_streak += 1
            if self.decision_streak >= STABLE_WINDOW:
                self.state = "DECIDED"
                self.choose_major()
                self.decision_time = current_step
            else:
                self.state = "MATCHING"
        elif self.confidence >= 0.5:
            self.decision_streak = 0
            self.state = "MATCHING"
        else:
            self.decision_streak = 0
            self.state = "CONFUSED"


class MajorSelectionModel:
    def __init__(self, data_input, scenario_type="Pasif"):
        self.scenario_type = scenario_type
        self.history = []
        
        scenario_map = {"Pasif": 1, "Reaktif": 2, "Preventif": 3}
        target_code = scenario_map.get(scenario_type, 1)
        
        # Filter sub-populasi 1000 agen berdasarkan skenario aktif
        filtered_profiles = [d for d in data_input if d.get("scenario") == target_code]
        
        if len(filtered_profiles) == 0:
            filtered_profiles = data_input[:1000]
            
        self.agents = [StudentAgent(profile) for profile in filtered_profiles]

    def evaluate_bk_intervention(self, agent):
        if self.scenario_type == "Pasif":
            return 0.3, 0.0
        elif self.scenario_type == "Reaktif":
            info_level = 0.5
            recommendation = 0.8 if agent.confidence < 0.5 else 0.2
            return info_level, recommendation
        elif self.scenario_type == "Preventif":
            return 0.9, 0.8
        return 0.5, 0.3

    def step(self, current_step):
        for agent in self.agents:
            agent.move()
            nearby_agents = [
                other for other in self.agents 
                if other.agent_id != agent.agent_id and (abs(other.x - agent.x) + abs(other.y - agent.y)) <= 2
            ]
            agent.interact(nearby_agents)
            info_level, recommendation = self.evaluate_bk_intervention(agent)
            agent.update_state(info_level, recommendation, current_step)
        
        # Ambil metrik agregat kelompok
        confused = sum(1 for a in self.agents if a.state == "CONFUSED")
        matching = sum(1 for a in self.agents if a.state == "MATCHING")
        decided = sum(1 for a in self.agents if a.state == "DECIDED")
        
        ti = sum(1 for a in self.agents if a.state == "DECIDED" and a.chosen_major == "Teknik Informatika")
        psi = sum(1 for a in self.agents if a.state == "DECIDED" and a.chosen_major == "Psikologi")
        dkv = sum(1 for a in self.agents if a.state == "DECIDED" and a.chosen_major == "DKV")
        
        metrics = {
            "Step": current_step,
            "CONFUSED": confused,
            "MATCHING": matching,
            "DECIDED": decided,
            "Teknik Informatika": ti,
            "Psikologi": psi,
            "DKV": dkv
        }
        self.history.append(metrics)
        return metrics

# ==========================================
# 3. FUNGSI PEMBANGKIT DATA DEFAULT (FALLBACK)
# ==========================================
def generate_default_data():
    results = []
    student_counter = 1
    for scenario_id in [1, 2, 3]:
        for iteration_idx in range(1000):
            results.append({
                "student_id": f"STU_{student_counter:04d}",
                "scenario": scenario_id,
                "iteration": iteration_idx,
                "interest": round(random.uniform(0.4, 1.0), 2),
                "ability": round(random.uniform(0.4, 1.0), 2),
                "confidence": round(random.uniform(0.2, 0.6), 2),
                "influence": round(random.uniform(0.1, 0.8), 2),
                "resilience": round(random.uniform(0.3, 0.9), 2),
                "distortion": round(random.uniform(0.1, 0.7), 2)
            })
            student_counter += 1
    return results

# ==========================================
# 4. ANTARMUKA PENGGUNA (UI STREAMLIT)
# ==========================================
st.title("🎯 Aplikasi Simulasi Manajemen Keputusan Karier Siswa")
st.markdown("Aplikasi simulasi berbasis agen untuk mengevaluasi dampak Skenario Intervensi Bimbingan Konseling (BK) terhadap kemantapan penentuan program studi menggunakan teori Kecerdasan Majemuk.")

# --- SIDEBAR PANEL CONTROL ---
st.sidebar.header("📁 Pengaturan Data & Simulasi")

# Fitur Upload CSV
uploaded_file = st.sidebar.file_uploader("Unggah Dataset Agen (Format CSV)", type=["csv"])

if uploaded_file is not None:
    try:
        df_uploaded = pd.read_csv(uploaded_file)
        # Memastikan format data sesuai ekspektasi kamus
        student_raw_data = df_uploaded.to_dict(orient="records")
        st.sidebar.success(f"✅ Berhasil memuat {len(df_uploaded)} data siswa dari CSV!")
    except Exception as e:
        st.sidebar.error(f"Gagal membaca file CSV: {e}")
        student_raw_data = generate_default_data()
else:
    st.sidebar.info("💡 Menggunakan dataset sintetis bawaan (Default).")
    student_raw_data = generate_default_data()

# Pengaturan Skenario Kebijakan BK
selected_scenario = st.sidebar.selectbox(
    "Pilih Skenario Kebijakan BK:",
    ["Pasif", "Reaktif", "Preventif"]
)

# Pengaturan Batas Iterasi (Maksimal 1000)
total_steps = st.sidebar.slider("Jumlah Iterasi (Langkah Waktu):", min_value=50, max_value=1000, value=1000, step=50)

# Tombol Pemicu Simulasi
start_sim = st.sidebar.button("▶️ Jalankan Simulasi")

# --- MAIN CONTENT WINDOW ---
if start_sim:
    st.header(f"📊 Laporan Hasil Eksekusi: Skenario {selected_scenario}")
    
    # Inisialisasi Model Lingkungan
    model = MajorSelectionModel(student_raw_data, scenario_type=selected_scenario)
    
    # Progress bar interaktif
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Ruang penyimpanan data real-time langkah waktu
    step_records = []
    
    # Loop Eksekusi Simulasi 1000 Iterasi
    for current_s in range(1, total_steps + 1):
        metrics = model.step(current_s)
        step_records.append(metrics)
        
        # Update progress bar berkala agar tidak membebani render browser
        if current_s % 100 == 0 or current_s == total_steps:
            progress_bar.progress(current_s / total_steps)
            status_text.text(f"Memproses iterasi: {current_s} / {total_steps}...")
            
    df_history = pd.DataFrame(step_records)
    status_text.text("✅ Simulasi Selesai Diakumulasikan!")

    # --- BLOCK DISPLAY METRIK RINGKASAN AKHIR ---
    last_metrics = df_history.iloc[-1]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="🔴 Total Siswa Bingung (Confused)", value=int(last_metrics["CONFUSED"]))
    with col2:
        st.metric(label="🟡 Total Siswa Menimbang (Matching)", value=int(last_metrics["MATCHING"]))
    with col3:
        st.metric(label="🟢 Total Keputusan Final (Decided)", value=int(last_metrics["DECIDED"]))

    # --- BLOCK VISUALISASI ---
    st.subheader("📈 Analisis Perubahan Grafik Tren Kelompok Runtun Waktu")
    
    # Plot 1: Garis Tren Fluktuasi Status
    fig1, ax1 = plt.subplots(figsize=(10, 4.5))
    ax1.plot(df_history["Step"], df_history["CONFUSED"], label="Confused (Bingung)", color="#ef4444", lw=2)
    ax1.plot(df_history["Step"], df_history["MATCHING"], label="Matching (Menimbang)", color="#eab308", lw=2)
    ax1.plot(df_history["Step"], df_history["DECIDED"], label="Decided (Kunci Pilihan)", color="#22c55e", lw=2.5)
    ax1.axhline(y=800, color="blue", linestyle="--", alpha=0.5, label="Target Stabilitas (80%)")
    ax1.set_xlabel("Langkah Waktu (Iterasi)")
    ax1.set_ylabel("Jumlah Siswa")
    ax1.set_title(f"Tren Perubahan Status Psikologis Siswa - Skenario {selected_scenario}", fontweight="bold")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1)

    # Plot 2: Distribusi Jurusan Akhir (Bar Chart)
    st.subheader("🎯 Sebaran Minat Pemilihan Program Studi Akhir")
    
    majors = ["Teknik Informatika", "Psikologi", "DKV"]
    values = [last_metrics["Teknik Informatika"], last_metrics["Psikologi"], last_metrics["DKV"]]
    
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    bars = ax2.bar(majors, values, color=["#3b82f6", "#a855f7", "#f59e0b"], width=0.5)
    ax2.set_ylabel("Jumlah Peminat (Siswa)")
    ax2.set_title("Distribusi Pemilihan Jurusan Akhir Berdasarkan Bakat Dominan", fontweight="bold")
    ax2.grid(axis='y', alpha=0.3)
    
    # Berikan label angka di atas barchart
    for bar in bars:
        height = bar.get_height()
        ax2.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  
                    textcoords="offset points",
                    ha='center', va='bottom')
                    
    st.pyplot(fig2)

    # --- DOWNLOAD DATASET SIMULASI ---
    st.subheader("📥 Unduh Riwayat Log Simulasi")
    csv_logs = df_history.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Hasil Simulasi (.CSV)",
        data=csv_logs,
        file_name=f"hasil_simulasi_{selected_scenario}.csv",
        mime="text/csv"
    )
else:
    st.info("👈 Silakan pilih parameter kebijakan BK di panel kiri, kemudian klik tombol **Jalankan Simulasi** untuk memproses data analisis.")
