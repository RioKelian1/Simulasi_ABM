import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
from collections import Counter
from io import BytesIO

# ========== SETUP ==========
st.set_page_config(page_title="ABM Pemilihan Jurusan", layout="wide")
st.title("🎓 Simulasi Pemilihan Jurusan Kuliah dengan ABM")
st.markdown("**Faktor: Interest, Skill, Nilai, dan Pengaruh Teman**")
st.markdown("3 Skenario: Pasif | Reaktif | Preventif | Monte Carlo 1000 iterasi | 200 Agent")

# ========== PARAMETER TETAP ==========
NUM_AGENTS = 200
NUM_SEMESTERS = 10          # internal, tidak ditampilkan
MONTE_CARLO_ITER = 1000
JURUSAN = ["Teknik Informatika", "Manajemen", "Psikologi"]

# ========== KELAS AGENT (dengan atribut lengkap) ==========
class Student:
    def __init__(self, agent_id, custom_profile=None):
        self.id = agent_id
        if custom_profile:
            self.interest = custom_profile["interest"]
            self.skill = custom_profile["skill"]
            self.nilai = custom_profile["nilai"]
        else:
            # Inisialisasi random untuk masing-masing jurusan
            self.interest = {j: random.uniform(0.2, 0.9) for j in JURUSAN}
            self.skill = {j: random.uniform(0.2, 0.9) for j in JURUSAN}
            self.nilai = {j: random.uniform(0.3, 1.0) for j in JURUSAN}   # nilai akademik per jurusan
        
        self.state = "Belum Memilih"
        self.exploration_progress = 0.0
        self.final_choice = None
        self.teman = random.sample(range(NUM_AGENTS), k=random.randint(2,5))  # 2-5 teman
        self.teman = [t for t in self.teman if t != self.id]  # tidak termasuk diri sendiri

    def hitung_skor_jurusan(self, pengaruh_teman):
        """
        Menghitung skor untuk setiap jurusan berdasarkan:
        - interest (bobot 0.4)
        - skill (bobot 0.3)
        - nilai (bobot 0.2)
        - pengaruh teman (bobot 0.1)
        """
        skor = {}
        for j in JURUSAN:
            skor[j] = (0.4 * self.interest[j] +
                       0.3 * self.skill[j] +
                       0.2 * self.nilai[j] +
                       0.1 * pengaruh_teman.get(j, 0))
        return skor

# ========== FUNGSI MENGHITUNG PENGARUH TEMAN ==========
def hitung_pengaruh_teman(agents, agent_id):
    """Melihat pilihan final dari teman-teman agent, lalu mengembalikan dictionary probabilitas boost per jurusan"""
    pengaruh = {j: 0 for j in JURUSAN}
    agent = agents[agent_id]
    for tid in agent.teman:
        if tid < len(agents) and agents[tid].final_choice:
            jurusan_teman = agents[tid].final_choice
            pengaruh[jurusan_teman] += 0.2   # setiap teman yang sudah memutuskan memberi boost 0.2
    # Normalisasi (max 1.0)
    total = sum(pengaruh.values())
    if total > 0:
        for j in pengaruh:
            pengaruh[j] = min(pengaruh[j] / total, 1.0) if total > 0 else 0
    return pengaruh

# ========== FUNGSI PILIH JURUSAN BERDASARKAN SKOR ==========
def pilih_jurusan(agent, pengaruh_teman):
    skor = agent.hitung_skor_jurusan(pengaruh_teman)
    # Tambahkan noise agar tidak deterministik
    probs = np.array([skor[j] + random.uniform(0, 0.1) for j in JURUSAN])
    probs = probs / probs.sum()
    return np.random.choice(JURUSAN, p=probs)

# ========== SIMULASI SATU RUN (dengan semua faktor) ==========
def run_simulation(intervention_type, custom_profiles=None):
    # Inisialisasi agent
    agents = []
    for i in range(NUM_AGENTS):
        if custom_profiles and i < len(custom_profiles):
            agents.append(Student(i, custom_profiles[i]))
        else:
            agents.append(Student(i))
    
    for sem in range(NUM_SEMESTERS):
        # Update pengaruh teman berdasarkan pilihan final (dinamis)
        for ag in agents:
            if ag.state == "Memutuskan":
                continue
            # Hitung pengaruh dari teman yang sudah memutuskan
            pengaruh = hitung_pengaruh_teman(agents, ag.id)
            
            # State transition
            if ag.state == "Belum Memilih" and random.random() < 0.3:
                ag.state = "Eksplorasi"
            
            if ag.state == "Eksplorasi":
                gain = 0.2 + random.uniform(-0.05, 0.05)
                # Intervensi
                if intervention_type == "preventif":
                    gain += 0.2
                elif intervention_type == "reaktif" and sem >= 3 and ag.state == "Belum Memilih":
                    gain += 0.15
                ag.exploration_progress += gain
                if ag.exploration_progress >= 1.0:
                    ag.final_choice = pilih_jurusan(ag, pengaruh)
                    ag.state = "Memutuskan"
    
    state_counts = Counter(ag.state for ag in agents)
    choice_counts = Counter(ag.final_choice for ag in agents if ag.final_choice)
    return state_counts, choice_counts

# ========== MONTE CARLO WRAPPER ==========
def monte_carlo(intervention_type, custom_profiles=None):
    all_state, all_choice = [], []
    for _ in range(MONTE_CARLO_ITER):
        sc, cc = run_simulation(intervention_type, custom_profiles)
        all_state.append(sc)
        all_choice.append(cc)
    avg_state = {s: np.mean([d.get(s,0) for d in all_state]) / NUM_AGENTS * 100 for s in ["Belum Memilih","Eksplorasi","Memutuskan"]}
    avg_choice = {j: np.mean([d.get(j,0) for d in all_choice]) / NUM_AGENTS * 100 for j in JURUSAN}
    return avg_state, avg_choice

# ========== SIDEBAR: UPLOAD DATA PROFIL SISWA (opsional) ==========
st.sidebar.header("Upload Data Profil Siswa (Opsional)")
uploaded_file = st.sidebar.file_uploader("CSV dengan kolom: interest_TI, interest_Manajemen, interest_Psikologi, skill_TI, skill_Manajemen, skill_Psikologi, nilai_TI, nilai_Manajemen, nilai_Psikologi", type="csv")

custom_profiles = None
if uploaded_file:
    df_custom = pd.read_csv(uploaded_file)
    required_cols = [f"{prefix}_{jurusan}" for prefix in ["interest","skill","nilai"] for jurusan in ["TI","Manajemen","Psikologi"]]
    if all(col in df_custom.columns for col in required_cols):
        custom_profiles = []
        for _, row in df_custom.iterrows():
            profile = {
                "interest": {JURUSAN[0]: row["interest_TI"], JURUSAN[1]: row["interest_Manajemen"], JURUSAN[2]: row["interest_Psikologi"]},
                "skill": {JURUSAN[0]: row["skill_TI"], JURUSAN[1]: row["skill_Manajemen"], JURUSAN[2]: row["skill_Psikologi"]},
                "nilai": {JURUSAN[0]: row["nilai_TI"], JURUSAN[1]: row["nilai_Manajemen"], JURUSAN[2]: row["nilai_Psikologi"]}
            }
            custom_profiles.append(profile)
        st.sidebar.success("Profil siswa berhasil dimuat")
    else:
        st.sidebar.error("Format CSV salah. Gunakan kolom: interest_TI, interest_Manajemen, interest_Psikologi, skill_TI, ... , nilai_Psikologi")

if st.sidebar.button("🚀 Jalankan Simulasi"):
    with st.spinner("Menjalankan Monte Carlo (1000 iterasi)..."):
        results = {}
        for scenario in ["pasif", "reaktif", "preventif"]:
            avg_state, avg_choice = monte_carlo(scenario, custom_profiles)
            results[scenario] = {"state": avg_state, "choice": avg_choice}
        st.session_state['results'] = results
        st.success("Simulasi selesai!")

# ========== DASHBOARD ==========
if 'results' in st.session_state:
    res = st.session_state['results']
    st.header("📊 Hasil Simulasi Pemilihan Jurusan")

    col1, col2, col3 = st.columns(3)
    for i, (scenario, data) in enumerate(res.items()):
        with [col1, col2, col3][i]:
            st.metric(f"{scenario.capitalize()}", f"{data['state']['Memutuskan']:.1f}% memutuskan")

    # Barplot state per skenario
    fig, ax = plt.subplots(1,3, figsize=(18,5))
    for i, (scenario, data) in enumerate(res.items()):
        states = list(data["state"].keys())
        vals = list(data["state"].values())
        ax[i].bar(states, vals, color=['red','orange','green'])
        ax[i].set_title(scenario.capitalize())
        ax[i].set_ylim(0,100)
        ax[i].set_ylabel("Persen Agent")
    st.pyplot(fig)

    # Pie chart untuk skenario preventif
    st.subheader("Distribusi State - Skenario Preventif")
    pie_data = res["preventif"]["state"]
    fig2, ax2 = plt.subplots()
    ax2.pie(pie_data.values(), labels=pie_data.keys(), autopct="%1.1f%%", startangle=90)
    st.pyplot(fig2)

    # Distribusi pilihan jurusan
    st.subheader("Perbandingan Pilihan Jurusan per Skenario")
    df_choice = pd.DataFrame([
        {"Skenario": s, "Jurusan": j, "Persen": v}
        for s, d in res.items() for j, v in d["choice"].items()
    ])
    fig3, ax3 = plt.subplots(figsize=(10,6))
    sns.barplot(data=df_choice, x="Skenario", y="Persen", hue="Jurusan", ax=ax3)
    ax3.set_ylabel("Persen Agent (%)")
    ax3.set_title("Persentase Pemilihan Jurusan")
    st.pyplot(fig3)

    # Boxplot variabilitas (30 sampel per skenario)
    st.subheader("Variabilitas Jumlah Agent per State (30 sampel)")
    box_data = []
    for scenario in res.keys():
        for _ in range(30):
            sc, _ = run_simulation(scenario, custom_profiles)
            for s in ["Belum Memilih", "Eksplorasi", "Memutuskan"]:
                box_data.append({"Skenario": scenario, "State": s, "Jumlah": sc.get(s,0)})
    df_box = pd.DataFrame(box_data)
    fig4, ax4 = plt.subplots(figsize=(12,6))
    sns.boxplot(data=df_box, x="Skenario", y="Jumlah", hue="State", ax=ax4)
    ax4.set_ylabel("Jumlah Agent")
    st.pyplot(fig4)

    # Export CSV
    st.subheader("📥 Download Hasil Simulasi")
    df_export = pd.DataFrame({
        "Skenario": [],
        "Belum_Memilih_%": [],
        "Eksplorasi_%": [],
        "Memutuskan_%": [],
        "Teknik_Informatika_%": [],
        "Manajemen_%": [],
        "Psikologi_%": []
    })
    for scenario, data in res.items():
        df_export.loc[len(df_export)] = [
            scenario,
            data["state"]["Belum Memilih"],
            data["state"]["Eksplorasi"],
            data["state"]["Memutuskan"],
            data["choice"]["Teknik Informatika"],
            data["choice"]["Manajemen"],
            data["choice"]["Psikologi"]
        ]
    csv_buffer = BytesIO()
    df_export.to_csv(csv_buffer, index=False)
    st.download_button("Download CSV", data=csv_buffer.getvalue(), file_name="hasil_simulasi_jurusan.csv", mime="text/csv")
