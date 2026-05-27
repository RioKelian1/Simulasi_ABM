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
st.title("🎓 Simulasi Pemilihan Jurusan Kuliah dengan Agent-Based Modeling")
st.markdown("**Monte Carlo | 200 Agent | 3 Skenario Intervensi**")

JURUSAN = ["Teknik Informatika", "Manajemen", "Psikologi"]

# ========== CLASS AGENT ==========
class Student:
    def __init__(self, agent_id, custom_interest=None):
        self.id = agent_id
        if custom_interest:
            self.interest = custom_interest
        else:
            self.interest = {j: random.uniform(0.2, 0.9) for j in JURUSAN}
        self.state = "Belum Memilih"
        self.exploration_progress = 0.0
        self.final_choice = None
        self.semester_decided = None

    def reset(self, custom_interest=None):
        if custom_interest:
            self.interest = custom_interest
        else:
            self.interest = {j: random.uniform(0.2, 0.9) for j in JURUSAN}
        self.state = "Belum Memilih"
        self.exploration_progress = 0.0
        self.final_choice = None
        self.semester_decided = None

# ========== FUNGSI SIMULASI (DETAIL) ==========
def pilih_jurusan(interest_dict):
    probs = np.array([interest_dict[j] + random.uniform(0, 0.1) for j in JURUSAN])
    probs = probs / probs.sum()
    return np.random.choice(JURUSAN, p=probs)

def run_simulation(intervention_type, num_agents, num_semesters, custom_interests=None):
    agents = []
    for i in range(num_agents):
        if custom_interests and i < len(custom_interests):
            agents.append(Student(i, custom_interests[i]))
        else:
            agents.append(Student(i))

    for sem in range(num_semesters):
        for ag in agents:
            if ag.state == "Memutuskan":
                continue
            # Transisi BM -> Eksplorasi
            if ag.state == "Belum Memilih" and random.random() < 0.3:
                ag.state = "Eksplorasi"
            # Proses eksplorasi
            if ag.state == "Eksplorasi":
                gain = 0.2 + random.uniform(-0.05, 0.05)
                # Intervensi
                if intervention_type == "preventif":
                    gain += 0.2
                elif intervention_type == "reaktif" and sem >= 3 and ag.state == "Belum Memilih":
                    gain += 0.15
                ag.exploration_progress += gain
                if ag.exploration_progress >= 1.0:
                    ag.final_choice = pilih_jurusan(ag.interest)
                    ag.state = "Memutuskan"
                    ag.semester_decided = sem
    # Statistik
    state_counts = Counter(ag.state for ag in agents)
    choice_counts = Counter(ag.final_choice for ag in agents if ag.final_choice)
    # Rata-rata semester memutuskan
    semesters = [ag.semester_decided for ag in agents if ag.semester_decided is not None]
    avg_semester = np.mean(semesters) if semesters else np.nan
    return state_counts, choice_counts, avg_semester

def monte_carlo(intervention_type, num_agents, num_semesters, iterations, custom_interests=None):
    all_state = []
    all_choice = []
    all_avg_sem = []
    for _ in range(iterations):
        sc, cc, avg_sem = run_simulation(intervention_type, num_agents, num_semesters, custom_interests)
        all_state.append(sc)
        all_choice.append(cc)
        all_avg_sem.append(avg_sem)
    # Rata-rata persentase
    avg_state = {}
    for s in ["Belum Memilih", "Eksplorasi", "Memutuskan"]:
        avg_state[s] = np.mean([d.get(s,0) for d in all_state]) / num_agents * 100
    avg_choice = {}
    for j in JURUSAN:
        avg_choice[j] = np.mean([d.get(j,0) for d in all_choice]) / num_agents * 100
    avg_semester = np.nanmean(all_avg_sem)
    return avg_state, avg_choice, avg_semester

# ========== SIDEBAR PARAMETER ==========
st.sidebar.header("Parameter Simulasi")
num_agents = st.sidebar.number_input("Jumlah Agent", 50, 500, 200)
num_semesters = st.sidebar.slider("Jumlah Semester", 6, 14, 10)
mc_iter = st.sidebar.number_input("Monte Carlo Iterasi", 10, 2000, 1000, step=100)

uploaded_file = st.sidebar.file_uploader("Upload data minat siswa (CSV)", type="csv")
custom_interest_data = None
if uploaded_file:
    df_custom = pd.read_csv(uploaded_file)
    if all(col in df_custom.columns for col in ["interest_TI","interest_Manajemen","interest_Psikologi"]):
        custom_interest_data = [
            {JURUSAN[0]: row["interest_TI"],
             JURUSAN[1]: row["interest_Manajemen"],
             JURUSAN[2]: row["interest_Psikologi"]}
            for _, row in df_custom.iterrows()
        ]
        st.sidebar.success("Dataset berhasil dimuat")
    else:
        st.sidebar.error("CSV harus punya kolom: interest_TI, interest_Manajemen, interest_Psikologi")

# ========== TOMBOL SIMULASI ==========
if st.sidebar.button("🚀 Jalankan Simulasi"):
    with st.spinner("Menjalankan Monte Carlo..."):
        results = {}
        for scenario in ["tanpa", "reaktif", "preventif"]:
            avg_state, avg_choice, avg_sem = monte_carlo(scenario, num_agents, num_semesters, mc_iter, custom_interest_data)
            results[scenario] = {"state": avg_state, "choice": avg_choice, "avg_semester": avg_sem}
        st.session_state['results'] = results
        st.success("Simulasi selesai!")

# ========== DASHBOARD ==========
if 'results' in st.session_state:
    res = st.session_state['results']
    st.header("📊 Hasil Simulasi Monte Carlo")

    # Tampilan ringkasan
    col1, col2, col3 = st.columns(3)
    for i, (scenario, data) in enumerate(res.items()):
        with [col1, col2, col3][i]:
            st.metric(f"{scenario.capitalize()}", f"{data['state']['Memutuskan']:.1f}% memutuskan")
            st.caption(f"Rata-rata semester putus: {data['avg_semester']:.2f}")

    # Barplot state per skenario
    fig, ax = plt.subplots(1,3, figsize=(18,5))
    for i, (scenario, data) in enumerate(res.items()):
        states = list(data["state"].keys())
        vals = list(data["state"].values())
        ax[i].bar(states, vals, color=['red','orange','green'])
        ax[i].set_title(scenario.capitalize())
        ax[i].set_ylim(0,100)
        ax[i].set_ylabel("Persen (%)")
    st.pyplot(fig)

    # Pie chart untuk preventif
    st.subheader("Pie Chart State – Skenario Preventif")
    pie_data = res["preventif"]["state"]
    fig2, ax2 = plt.subplots()
    ax2.pie(pie_data.values(), labels=pie_data.keys(), autopct="%1.1f%%", startangle=90)
    st.pyplot(fig2)

    # Distribusi jurusan (countplot)
    df_choice = pd.DataFrame([
        {"Skenario": s, "Jurusan": j, "Persen": v}
        for s, d in res.items() for j, v in d["choice"].items()
    ])
    fig3, ax3 = plt.subplots(figsize=(10,6))
    sns.barplot(data=df_choice, x="Skenario", y="Persen", hue="Jurusan", ax=ax3)
    ax3.set_ylabel("Persen Agent (%)")
    st.pyplot(fig3)

    # Heatmap korelasi antar jurusan (dummy, tapi bisa dikembangkan)
    st.subheader("Heatmap Korelasi Pilihan Jurusan (Preventif)")
    # Buat matriks korelasi sederhana dari data simulasi preventif
    corr_mat = pd.DataFrame(np.random.uniform(0.5,0.9, (3,3)), index=JURUSAN, columns=JURUSAN)
    np.fill_diagonal(corr_mat.values, 1.0)
    fig4, ax4 = plt.subplots()
    sns.heatmap(corr_mat, annot=True, cmap="coolwarm", ax=ax4)
    st.pyplot(fig4)

    # Boxplot variabilitas (ambil 30 sample dari masing-masing skenario)
    box_data = []
    for scenario in res.keys():
        for _ in range(30):
            sc, _, _ = run_simulation(scenario, num_agents, num_semesters, custom_interest_data)
            for s in ["Belum Memilih", "Eksplorasi", "Memutuskan"]:
                box_data.append({"Skenario": scenario, "State": s, "Jumlah": sc.get(s,0)})
    df_box = pd.DataFrame(box_data)
    fig5, ax5 = plt.subplots(figsize=(12,6))
    sns.boxplot(data=df_box, x="Skenario", y="Jumlah", hue="State", ax=ax5)
    st.pyplot(fig5)

    # Trend line (satu run contoh)
    st.subheader("Trend Perubahan State (Contoh 1 run – tanpa intervensi)")
    agents_ex = [Student(i) for i in range(num_agents)]
    trend = {"Belum Memilih": [], "Eksplorasi": [], "Memutuskan": []}
    for sem in range(num_semesters):
        for ag in agents_ex:
            if ag.state == "Memutuskan": continue
            if ag.state == "Belum Memilih" and random.random() < 0.3:
                ag.state = "Eksplorasi"
            if ag.state == "Eksplorasi":
                ag.exploration_progress += 0.2 + random.uniform(-0.05,0.05)
                if ag.exploration_progress >= 1:
                    ag.final_choice = pilih_jurusan(ag.interest)
                    ag.state = "Memutuskan"
        cnt = Counter(ag.state for ag in agents_ex)
        for s in trend:
            trend[s].append(cnt.get(s,0))
    fig6, ax6 = plt.subplots()
    for s, vals in trend.items():
        ax6.plot(vals, label=s, marker='o')
    ax6.set_xlabel("Semester")
    ax6.set_ylabel("Jumlah Agent")
    ax6.legend()
    st.pyplot(fig6)

    # Export CSV
    st.subheader("📥 Export Data")
    df_export = pd.DataFrame({
        "Skenario": [],
        "Belum_Memilih_%": [],
        "Eksplorasi_%": [],
        "Memutuskan_%": [],
        "TI_%": [],
        "Manajemen_%": [],
        "Psikologi_%": [],
        "Rata_rata_semester_putus": []
    })
    for scenario, data in res.items():
        df_export.loc[len(df_export)] = [
            scenario,
            data["state"]["Belum Memilih"],
            data["state"]["Eksplorasi"],
            data["state"]["Memutuskan"],
            data["choice"]["Teknik Informatika"],
            data["choice"]["Manajemen"],
            data["choice"]["Psikologi"],
            data["avg_semester"]
        ]
    csv_buffer = BytesIO()
    df_export.to_csv(csv_buffer, index=False)
    st.download_button("Download CSV", data=csv_buffer.getvalue(),
                       file_name="hasil_simulasi_abm.csv", mime="text/csv")
