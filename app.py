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
st.markdown("**Faktor: Interest, Skill, Nilai, Pengaruh Teman** | 3 Skenario: Pasif, Reaktif, Preventif")

# ========== PARAMETER TETAP (tidak ditampilkan ke user) ==========
NUM_AGENTS = 200
NUM_STEPS = 4          # internal, tidak disebut
MONTE_CARLO_ITER = 1000
JURUSAN = ["Teknik Informatika", "Manajemen", "Psikologi"]

# ========== KELAS AGENT ==========
class Student:
    def __init__(self, agent_id, custom_profile=None):
        self.id = agent_id
        if custom_profile:
            self.interest = custom_profile["interest"]
            self.skill = custom_profile["skill"]
            self.nilai = custom_profile["nilai"]
        else:
            self.interest = {j: random.uniform(0.2, 0.9) for j in JURUSAN}
            self.skill = {j: random.uniform(0.2, 0.9) for j in JURUSAN}
            self.nilai = {j: random.uniform(0.3, 1.0) for j in JURUSAN}
        self.state = "Belum Memilih"
        self.exploration_progress = 0.0
        self.final_choice = None
        self.teman = random.sample(range(NUM_AGENTS), k=random.randint(2,5))
        self.teman = [t for t in self.teman if t != self.id]

    def hitung_skor(self, pengaruh_teman):
        skor = {}
        for j in JURUSAN:
            skor[j] = (0.4 * self.interest[j] +
                       0.3 * self.skill[j] +
                       0.2 * self.nilai[j] +
                       0.1 * pengaruh_teman.get(j, 0))
        return skor

def pilih_jurusan(agent, pengaruh_teman):
    skor = agent.hitung_skor(pengaruh_teman)
    probs = np.array([skor[j] + random.uniform(0, 0.1) for j in JURUSAN])
    probs = probs / probs.sum()
    return np.random.choice(JURUSAN, p=probs)

def hitung_pengaruh_teman(agents, agent_id):
    pengaruh = {j: 0 for j in JURUSAN}
    agent = agents[agent_id]
    for tid in agent.teman:
        if tid < len(agents) and agents[tid].final_choice:
            jurusan_teman = agents[tid].final_choice
            pengaruh[jurusan_teman] += 0.2
    total = sum(pengaruh.values())
    if total > 0:
        for j in pengaruh:
            pengaruh[j] = min(pengaruh[j] / total, 1.0)
    return pengaruh

def run_simulation(intervention_type, custom_profiles=None):
    agents = []
    for i in range(NUM_AGENTS):
        if custom_profiles and i < len(custom_profiles):
            agents.append(Student(i, custom_profiles[i]))
        else:
            agents.append(Student(i))
    for _ in range(NUM_STEPS):
        for ag in agents:
            if ag.state == "Memutuskan":
                continue
            if ag.state == "Belum Memilih" and random.random() < 0.3:
                ag.state = "Eksplorasi"
            if ag.state == "Eksplorasi":
                gain = 0.2 + random.uniform(-0.05, 0.05)
                if intervention_type == "preventif":
                    gain += 0.2
                elif intervention_type == "reaktif" and ag.state == "Belum Memilih":
                    gain += 0.15
                ag.exploration_progress += gain
                if ag.exploration_progress >= 1.0:
                    pengaruh = hitung_pengaruh_teman(agents, ag.id)
                    ag.final_choice = pilih_jurusan(ag, pengaruh)
                    ag.state = "Memutuskan"
    return Counter(ag.state for ag in agents), Counter(ag.final_choice for ag in agents if ag.final_choice)

def monte_carlo(intervention_type, custom_profiles=None):
    all_state, all_choice = [], []
    for _ in range(MONTE_CARLO_ITER):
        sc, cc = run_simulation(intervention_type, custom_profiles)
        all_state.append(sc)
        all_choice.append(cc)
    avg_state = {s: np.mean([d.get(s,0) for d in all_state]) / NUM_AGENTS * 100 
                 for s in ["Belum Memilih","Eksplorasi","Memutuskan"]}
    avg_choice = {j: np.mean([d.get(j,0) for d in all_choice]) / NUM_AGENTS * 100 
                  for j in JURUSAN}
    return avg_state, avg_choice

# ========== SIDEBAR ==========
st.sidebar.header("Upload Data Profil Siswa (Opsional)")
uploaded_file = st.sidebar.file_uploader("CSV (interest, skill, nilai)", type="csv")
custom_profiles = None
if uploaded_file:
    df_custom = pd.read_csv(uploaded_file)
    required = ["interest_TI","interest_Manajemen","interest_Psikologi",
                "skill_TI","skill_Manajemen","skill_Psikologi",
                "nilai_TI","nilai_Manajemen","nilai_Psikologi"]
    if all(col in df_custom.columns for col in required):
        custom_profiles = []
        for _, row in df_custom.iterrows():
            profile = {
                "interest": {JURUSAN[0]: row["interest_TI"], JURUSAN[1]: row["interest_Manajemen"], JURUSAN[2]: row["interest_Psikologi"]},
                "skill": {JURUSAN[0]: row["skill_TI"], JURUSAN[1]: row["skill_Manajemen"], JURUSAN[2]: row["skill_Psikologi"]},
                "nilai": {JURUSAN[0]: row["nilai_TI"], JURUSAN[1]: row["nilai_Manajemen"], JURUSAN[2]: row["nilai_Psikologi"]}
            }
            custom_profiles.append(profile)
        st.sidebar.success("Data profil berhasil dimuat")
    else:
        st.sidebar.error("Format CSV salah")

if st.sidebar.button("🚀 Jalankan Simulasi (1000 iterasi Monte Carlo)"):
    with st.spinner("Menjalankan Monte Carlo..."):
        results = {}
        for scenario in ["pasif", "reaktif", "preventif"]:
            avg_state, avg_choice = monte_carlo(scenario, custom_profiles)
            results[scenario] = {"state": avg_state, "choice": avg_choice}
        st.session_state['results'] = results
        st.success("Simulasi selesai!")

# ========== DASHBOARD ==========
if 'results' in st.session_state:
    res = st.session_state['results']

    st.sidebar.markdown("---")
    st.sidebar.subheader("🧭 Navigasi")
    menu = st.sidebar.radio("Pilih tampilan", ["Ringkasan", "Visualisasi", "Analisis Statistik", "Data Mentah", "Detail Final State Agent"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎛️ Kontrol Tampilan")
    show_threshold = st.sidebar.checkbox("Tampilkan ambang batas 70%", value=True)
    show_labels = st.sidebar.checkbox("Tampilkan label angka pada grafik", value=False)

    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Sumber Data")
    st.sidebar.info("Data dari 1000 iterasi Monte Carlo, 200 agent.")

    # ========== RINGKASAN ==========
    if menu == "Ringkasan":
        st.header("📋 Ringkasan Hasil Simulasi")
        best_scenario = max(res.keys(), key=lambda s: res[s]["state"]["Memutuskan"])
        best_choice = min(res.keys(), key=lambda s: res[s]["state"]["Belum Memilih"])
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎯 Skenario dengan % Memutuskan Tertinggi", best_scenario.capitalize(), delta=f"{res[best_scenario]['state']['Memutuskan']:.1f}%")
        with col2:
            st.metric("✅ Skenario Paling Efektif (% Belum Memilih terendah)", best_choice.capitalize(), delta=f"{res[best_choice]['state']['Belum Memilih']:.1f}%")
        with col3:
            st.metric("🔁 Iterasi Monte Carlo", f"{MONTE_CARLO_ITER}")

        st.subheader("📊 Tabel Ringkasan State per Skenario")
        df_summary = pd.DataFrame({
            "Skenario": ["Pasif", "Reaktif", "Preventif"],
            "Memutuskan (%)": [res["pasif"]["state"]["Memutuskan"], res["reaktif"]["state"]["Memutuskan"], res["preventif"]["state"]["Memutuskan"]],
            "Belum Memilih (%)": [res["pasif"]["state"]["Belum Memilih"], res["reaktif"]["state"]["Belum Memilih"], res["preventif"]["state"]["Belum Memilih"]],
            "Eksplorasi (%)": [res["pasif"]["state"]["Eksplorasi"], res["reaktif"]["state"]["Eksplorasi"], res["preventif"]["state"]["Eksplorasi"]]
        })
        st.dataframe(df_summary)

        st.subheader("💡 Inti Temuan")
        st.markdown(f"""
        - **Skenario Preventif** menghasilkan persentase siswa yang berhasil memutuskan jurusan tertinggi ({res['preventif']['state']['Memutuskan']:.1f}%).
        - **Skenario Pasif** (tanpa intervensi) menyebabkan {res['pasif']['state']['Belum Memilih']:.1f}% siswa masih belum memutuskan.
        - **Intervensi Reaktif** efektif menurunkan jumlah siswa yang belum memutuskan menjadi {res['reaktif']['state']['Belum Memilih']:.1f}%.
        """)

        st.subheader("📊 Perbandingan Metrik Utama")
        df_metrics = pd.DataFrame({
            "Skenario": ["Pasif", "Reaktif", "Preventif"],
            "% Memutuskan": [res["pasif"]["state"]["Memutuskan"], res["reaktif"]["state"]["Memutuskan"], res["preventif"]["state"]["Memutuskan"]],
            "% Belum Memilih": [res["pasif"]["state"]["Belum Memilih"], res["reaktif"]["state"]["Belum Memilih"], res["preventif"]["state"]["Belum Memilih"]]
        })
        fig, ax = plt.subplots(figsize=(10,6))
        df_metrics.plot(x="Skenario", y=["% Memutuskan", "% Belum Memilih"], kind="bar", ax=ax, color=['green','red'])
        ax.set_ylabel("Persen Agent")
        if show_labels:
            for container in ax.containers:
                ax.bar_label(container, fmt='%.1f')
        if show_threshold:
            ax.axhline(y=70, color='blue', linestyle='--', label='Batas 70%')
            ax.legend()
        st.pyplot(fig)

    # ========== VISUALISASI ==========
    elif menu == "Visualisasi":
        st.header("📈 Grafik Analitik")
        st.subheader("Perbandingan % Agent yang Memutuskan")
        fig1, ax1 = plt.subplots(figsize=(8,6))
        scenarios = list(res.keys())
        decided = [res[s]["state"]["Memutuskan"] for s in scenarios]
        bars = ax1.bar(scenarios, decided, color=['red','orange','green'])
        ax1.set_ylabel("Persen Agent")
        ax1.set_ylim(0,100)
        if show_labels:
            for bar in bars:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{bar.get_height():.1f}%', ha='center')
        if show_threshold:
            ax1.axhline(y=70, color='blue', linestyle='--', label='Batas 70%')
            ax1.legend()
        st.pyplot(fig1)

        st.subheader("Distribusi Pilihan Jurusan per Skenario")
        df_choice = pd.DataFrame()
        for s in res:
            for j in JURUSAN:
                df_choice = pd.concat([df_choice, pd.DataFrame({"Skenario": [s.capitalize()], "Jurusan": [j], "Persen": [res[s]["choice"][j]]})])
        df_choice = df_choice.reset_index(drop=True)
        fig2, ax2 = plt.subplots(figsize=(10,6))
        sns.barplot(data=df_choice, x="Skenario", y="Persen", hue="Jurusan", ax=ax2)
        ax2.set_ylabel("Persen Agent")
        if show_labels:
            for container in ax2.containers:
                ax2.bar_label(container, fmt='%.1f')
        st.pyplot(fig2)

        st.subheader("Distribusi Jurusan - Skenario Preventif")
        fig3, ax3 = plt.subplots()
        ax3.pie(res["preventif"]["choice"].values(), labels=res["preventif"]["choice"].keys(), autopct="%1.1f%%", startangle=90)
        ax3.axis('equal')
        st.pyplot(fig3)

    # ========== ANALISIS STATISTIK ==========
    elif menu == "Analisis Statistik":
        st.header("📐 Analisis Statistik")
        st.subheader("Variabilitas Jumlah Agent per State (30 sampel Monte Carlo)")
        box_data = []
        for scenario in res.keys():
            for _ in range(30):
                sc, _ = run_simulation(scenario, custom_profiles)
                for s in ["Belum Memilih", "Eksplorasi", "Memutuskan"]:
                    box_data.append({"Skenario": scenario, "State": s, "Jumlah": sc.get(s,0)})
        df_box = pd.DataFrame(box_data)
        fig, ax = plt.subplots(figsize=(12,6))
        sns.boxplot(data=df_box, x="Skenario", y="Jumlah", hue="State", ax=ax)
        ax.set_ylabel("Jumlah Agent")
        st.pyplot(fig)

        st.subheader("Korelasi Persentase Pilihan Jurusan antar Skenario")
        df_corr = pd.DataFrame({
            "Pasif": [res["pasif"]["choice"][j] for j in JURUSAN],
            "Reaktif": [res["reaktif"]["choice"][j] for j in JURUSAN],
            "Preventif": [res["preventif"]["choice"][j] for j in JURUSAN]
        }, index=JURUSAN)
        fig2, ax2 = plt.subplots(figsize=(8,6))
        sns.heatmap(df_corr.T.corr(), annot=True, cmap="coolwarm", ax=ax2)
        st.pyplot(fig2)

        st.subheader("Tabel Ringkasan Hasil")
        stats_df = pd.DataFrame({
            "Skenario": ["Pasif", "Reaktif", "Preventif"],
            "Memutuskan (%)": [res["pasif"]["state"]["Memutuskan"], res["reaktif"]["state"]["Memutuskan"], res["preventif"]["state"]["Memutuskan"]],
            "Belum Memilih (%)": [res["pasif"]["state"]["Belum Memilih"], res["reaktif"]["state"]["Belum Memilih"], res["preventif"]["state"]["Belum Memilih"]],
            "Eksplorasi (%)": [res["pasif"]["state"]["Eksplorasi"], res["reaktif"]["state"]["Eksplorasi"], res["preventif"]["state"]["Eksplorasi"]],
            "TI (%)": [res["pasif"]["choice"]["Teknik Informatika"], res["reaktif"]["choice"]["Teknik Informatika"], res["preventif"]["choice"]["Teknik Informatika"]],
            "Manajemen (%)": [res["pasif"]["choice"]["Manajemen"], res["reaktif"]["choice"]["Manajemen"], res["preventif"]["choice"]["Manajemen"]],
            "Psikologi (%)": [res["pasif"]["choice"]["Psikologi"], res["reaktif"]["choice"]["Psikologi"], res["preventif"]["choice"]["Psikologi"]]
        })
        st.dataframe(stats_df)

    # ========== DATA MENTAH (ringkasan agregat) ==========
    elif menu == "Data Mentah":
        st.header("📄 Data Hasil Simulasi (Ringkasan Agregat)")
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
        st.dataframe(df_export)
        csv_buffer = BytesIO()
        df_export.to_csv(csv_buffer, index=False)
        st.download_button("📥 Download CSV Ringkasan", data=csv_buffer.getvalue(), file_name="hasil_monte_carlo.csv", mime="text/csv")

    # ========== DETAIL FINAL STATE AGENT (scrollable per skenario) ==========
    elif menu == "Detail Final State Agent":
        st.header("📋 Detail Final State Seluruh Agent (Scrollable)")
        scenario_selected = st.selectbox("Pilih skenario", options=["pasif", "reaktif", "preventif"], format_func=lambda x: x.capitalize())
        
        def get_agents_detail(intervention_type, custom_profiles=None):
            agents = []
            for i in range(NUM_AGENTS):
                if custom_profiles and i < len(custom_profiles):
                    agents.append(Student(i, custom_profiles[i]))
                else:
                    agents.append(Student(i))
            for _ in range(NUM_STEPS):
                for ag in agents:
                    if ag.state == "Memutuskan":
                        continue
                    if ag.state == "Belum Memilih" and random.random() < 0.3:
                        ag.state = "Eksplorasi"
                    if ag.state == "Eksplorasi":
                        gain = 0.2 + random.uniform(-0.05, 0.05)
                        if intervention_type == "preventif":
                            gain += 0.2
                        elif intervention_type == "reaktif" and ag.state == "Belum Memilih":
                            gain += 0.15
                        ag.exploration_progress += gain
                        if ag.exploration_progress >= 1.0:
                            pengaruh = hitung_pengaruh_teman(agents, ag.id)
                            ag.final_choice = pilih_jurusan(ag, pengaruh)
                            ag.state = "Memutuskan"
            return agents
        
        with st.spinner("Menjalankan simulasi untuk mendapatkan detail agent..."):
            agents_detail = get_agents_detail(scenario_selected, custom_profiles)
            data_rows = []
            for ag in agents_detail:
                row = {
                    "Agent ID": ag.id,
                    "State": ag.state,
                    "Final Choice": ag.final_choice if ag.final_choice else "-",
                    "Interest TI": f"{ag.interest['Teknik Informatika']:.2f}",
                    "Interest Manajemen": f"{ag.interest['Manajemen']:.2f}",
                    "Interest Psikologi": f"{ag.interest['Psikologi']:.2f}",
                    "Skill TI": f"{ag.skill['Teknik Informatika']:.2f}",
                    "Skill Manajemen": f"{ag.skill['Manajemen']:.2f}",
                    "Skill Psikologi": f"{ag.skill['Psikologi']:.2f}",
                }
                data_rows.append(row)
            df_agents = pd.DataFrame(data_rows)
            st.dataframe(df_agents, use_container_width=True, height=500)
            st.caption(f"Menampilkan {len(df_agents)} agent. Gunakan scroll untuk melihat semua kolom dan baris.")
else:
    st.info("👈 Klik 'Jalankan Simulasi' di sidebar untuk memulai.")
