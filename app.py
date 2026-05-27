import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="ABM Pemilihan Jurusan Kuliah",
    page_icon="🎓",
    layout="wide"
)

# ==========================================
# TITLE
# ==========================================

st.title("🎓 Simulasi Pemilihan Jurusan Kuliah")
st.subheader("Agent-Based Modeling (ABM) + Monte Carlo Simulation")

st.markdown("""
Dashboard ini mensimulasikan bagaimana siswa memilih jurusan kuliah
berdasarkan kemampuan logika, kreativitas, sosial,
tekanan orang tua, ekonomi, dan tingkat kepercayaan diri.
""")

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.header("⚙️ Pengaturan Simulasi")

num_agents = st.sidebar.slider(
    "Jumlah Agent",
    50,
    1000,
    200
)

iterations = st.sidebar.slider(
    "Jumlah Monte Carlo Iteration",
    100,
    5000,
    1000
)

noise_level = st.sidebar.slider(
    "Noise / Randomness",
    0.0,
    0.5,
    0.05
)

# ==========================================
# UPLOAD CSV
# ==========================================

st.sidebar.subheader("📂 Upload Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV Baru",
    type=["csv"]
)

# ==========================================
# DEFAULT DATASET
# ==========================================

def generate_agents(total_agent):

    data = []

    for i in range(total_agent):

        agent = {
            "id": i,

            "logic": random.uniform(0, 1),

            "creativity": random.uniform(0, 1),

            "social": random.uniform(0, 1),

            "economy": random.uniform(0, 1),

            "pressure_parent": random.uniform(0, 1),

            "confidence": random.uniform(0.4, 1.0)
        }

        data.append(agent)

    return pd.DataFrame(data)

# ==========================================
# LOAD DATA
# ==========================================

if uploaded_file is not None:

    df_agents = pd.read_csv(uploaded_file)

    st.success("Dataset berhasil diupload!")

else:

    df_agents = generate_agents(num_agents)

# ==========================================
# TAMPILKAN DATASET
# ==========================================

st.subheader("📋 Dataset Agent")

st.dataframe(df_agents.head(10))

st.write("Jumlah Agent:", len(df_agents))

# ==========================================
# DEFINISI JURUSAN
# ==========================================

majors = {

    "Teknik Informatika": {
        "logic": 0.95,
        "creativity": 0.70,
        "social": 0.40
    },

    "Desain Komunikasi Visual": {
        "logic": 0.40,
        "creativity": 0.95,
        "social": 0.60
    },

    "Psikologi": {
        "logic": 0.55,
        "creativity": 0.65,
        "social": 0.95
    },

    "Manajemen": {
        "logic": 0.70,
        "creativity": 0.60,
        "social": 0.80
    },

    "Kedokteran": {
        "logic": 0.95,
        "creativity": 0.50,
        "social": 0.85
    }
}

# ==========================================
# FUNCTION MATCH SCORE
# ==========================================

def calculate_match(agent, major_profile):

    score = (
        (agent["logic"] * major_profile["logic"]) +
        (agent["creativity"] * major_profile["creativity"]) +
        (agent["social"] * major_profile["social"])
    ) / 3

    return score

# ==========================================
# PARENTAL PRESSURE
# ==========================================

def parental_pressure_effect(base_score, pressure):

    noise = np.random.normal(0, noise_level)

    final_score = base_score - (pressure * 0.2) + noise

    return max(0, min(1, final_score))

# ==========================================
# CHOOSE MAJOR
# ==========================================

def choose_major(agent):

    scores = {}

    for major_name, profile in majors.items():

        base = calculate_match(agent, profile)

        adjusted = parental_pressure_effect(
            base,
            agent["pressure_parent"]
        )

        scores[major_name] = adjusted

    best_major = max(scores, key=scores.get)

    return best_major, scores

# ==========================================
# RUN SIMULATION
# ==========================================

st.subheader("🚀 Menjalankan Simulasi Monte Carlo...")

simulation_history = []

progress_bar = st.progress(0)

for iteration in range(iterations):

    for _, agent in df_agents.iterrows():

        major, scores = choose_major(agent)

        simulation_history.append({

            "iteration": iteration,

            "agent_id": agent["id"],

            "selected_major": major,

            "score": max(scores.values()),

            "confidence": agent["confidence"],

            "pressure_parent": agent["pressure_parent"]
        })

    progress_bar.progress((iteration + 1) / iterations)

df_simulation = pd.DataFrame(simulation_history)

st.success("Simulasi selesai!")

# ==========================================
# DISTRIBUSI JURUSAN
# ==========================================

st.subheader("📊 Distribusi Pemilihan Jurusan")

fig1, ax1 = plt.subplots(figsize=(10,5))

sns.countplot(
    data=df_simulation,
    x="selected_major",
    ax=ax1
)

plt.xticks(rotation=15)

st.pyplot(fig1)

# ==========================================
# RATA-RATA SCORE
# ==========================================

st.subheader("📈 Rata-rata Match Score")

summary = df_simulation.groupby(
    "selected_major"
)["score"].agg([
    "mean",
    "max",
    "min",
    "std"
])

st.dataframe(summary)

# ==========================================
# TREND MONTE CARLO
# ==========================================

st.subheader("📉 Trend Monte Carlo Simulation")

trend = df_simulation.groupby(
    "iteration"
)["score"].mean()

fig2, ax2 = plt.subplots(figsize=(12,5))

ax2.plot(trend)

ax2.set_xlabel("Iteration")

ax2.set_ylabel("Average Score")

ax2.set_title("Trend Monte Carlo")

st.pyplot(fig2)

# ==========================================
# HEATMAP
# ==========================================

st.subheader("🔥 Heatmap Average Score")

pivot = pd.pivot_table(
    df_simulation,
    values="score",
    index="selected_major",
    aggfunc=np.mean
)

fig3, ax3 = plt.subplots(figsize=(6,4))

sns.heatmap(
    pivot,
    annot=True,
    cmap="viridis",
    ax=ax3
)

st.pyplot(fig3)

# ==========================================
# HISTOGRAM CONFIDENCE
# ==========================================

st.subheader("🧠 Distribusi Confidence Agent")

fig4, ax4 = plt.subplots(figsize=(8,4))

ax4.hist(
    df_agents["confidence"],
    bins=20
)

ax4.set_xlabel("Confidence")

ax4.set_ylabel("Jumlah Agent")

st.pyplot(fig4)

# ==========================================
# PIE CHART
# ==========================================

st.subheader("🥧 Persentase Jurusan")

major_counts = df_simulation["selected_major"].value_counts()

fig5, ax5 = plt.subplots(figsize=(7,7))

ax5.pie(
    major_counts,
    labels=major_counts.index,
    autopct='%1.1f%%'
)

st.pyplot(fig5)

# ==========================================
# EXPORT CSV
# ==========================================

st.subheader("💾 Download Hasil Simulasi")

csv = df_simulation.to_csv(index=False)

st.download_button(
    label="⬇️ Download CSV Hasil Simulasi",
    data=csv,
    file_name="simulation_results.csv",
    mime="text/csv"
)

# ==========================================
# DOWNLOAD SUMMARY
# ==========================================

summary_csv = summary.to_csv()

st.download_button(
    label="⬇️ Download Summary CSV",
    data=summary_csv,
    file_name="montecarlo_summary.csv",
    mime="text/csv"
)

# ==========================================
# FOOTER
# ==========================================

st.markdown("---")

st.markdown("""
### Tentang Project

Project ini menggunakan:

- Agent-Based Modeling (ABM)
- Monte Carlo Simulation
- 200+ Agent
- 1000 Iterasi
- Streamlit Dashboard
- Upload CSV Dinamis

Tema:
**Simulasi Pemilihan Jurusan Kuliah**
""")
