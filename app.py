import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="ABM Pemilihan Jurusan",
    page_icon="🎓",
    layout="wide"
)

# =====================================================
# TITLE
# =====================================================

st.title("🎓 Simulasi Pemilihan Jurusan Kuliah")
st.subheader("Agent-Based Modeling (ABM) + Monte Carlo Simulation")

st.markdown("""
Dashboard simulasi pemilihan jurusan kuliah menggunakan:

- Agent-Based Modeling (ABM)
- Monte Carlo Simulation
- Multi Scenario Simulation
- Dynamic State Transition
""")

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("⚙️ Pengaturan Simulasi")

num_agents = st.sidebar.slider(
    "Jumlah Agent",
    50,
    1000,
    200
)

iterations = st.sidebar.slider(
    "Monte Carlo Iteration",
    100,
    5000,
    1000
)

scenario = st.sidebar.selectbox(
    "Pilih Skenario",
    [
        "Tanpa Intervensi",
        "Reaktif",
        "Preventif",
        "Tekanan Orang Tua Tinggi"
    ]
)

uploaded_file = st.sidebar.file_uploader(
    "Upload Dataset CSV",
    type=["csv"]
)

# =====================================================
# STATE AGENT
# =====================================================

states = [

    "Belum Memilih",

    "Eksplorasi",

    "Konsultasi",

    "Memutuskan",

    "Salah Jurusan",

    "Cocok Jurusan"
]

# =====================================================
# GENERATE AGENT
# =====================================================

def generate_agents(total_agent):

    data = []

    for i in range(total_agent):

        data.append({

            "id": i,

            "logic": random.uniform(0,1),

            "creativity": random.uniform(0,1),

            "social": random.uniform(0,1),

            "economy": random.uniform(0,1),

            "pressure_parent": random.uniform(0,1),

            "confidence": random.uniform(0.4,1.0),

            "state": "Belum Memilih"
        })

    return pd.DataFrame(data)

# =====================================================
# LOAD DATA
# =====================================================

if uploaded_file is not None:

    df_agents = pd.read_csv(uploaded_file)

    st.success("Dataset berhasil diupload!")

else:

    df_agents = generate_agents(num_agents)

# =====================================================
# MAJOR PROFILE
# =====================================================

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

# =====================================================
# MATCH SCORE
# =====================================================

def calculate_match(agent, major_profile):

    score = (

        (agent["logic"] * major_profile["logic"]) +

        (agent["creativity"] * major_profile["creativity"]) +

        (agent["social"] * major_profile["social"])

    ) / 3

    return score

# =====================================================
# PARENTAL PRESSURE EFFECT
# =====================================================

def parental_pressure_effect(base_score, pressure):

    noise = np.random.normal(0, 0.05)

    final_score = base_score - (pressure * 0.2) + noise

    return max(0, min(1, final_score))

# =====================================================
# INTERVENTION
# =====================================================

def intervention(agent, scenario):

    if scenario == "Tanpa Intervensi":

        return agent

    elif scenario == "Reaktif":

        if agent["confidence"] < 0.5:

            agent["confidence"] += 0.2

    elif scenario == "Preventif":

        agent["confidence"] += 0.1

    elif scenario == "Tekanan Orang Tua Tinggi":

        agent["pressure_parent"] += 0.3

    # batas nilai

    agent["confidence"] = min(
        agent["confidence"],
        1.0
    )

    agent["pressure_parent"] = min(
        agent["pressure_parent"],
        1.0
    )

    return agent

# =====================================================
# CHOOSE MAJOR
# =====================================================

def choose_major(agent):

    scores = {}

    for major_name, profile in majors.items():

        base = calculate_match(
            agent,
            profile
        )

        adjusted = parental_pressure_effect(
            base,
            agent["pressure_parent"]
        )

        scores[major_name] = adjusted

    best_major = max(scores, key=scores.get)

    best_score = max(scores.values())

    return best_major, best_score

# =====================================================
# UPDATE STATE
# =====================================================

def update_state(agent, best_score):

    # =========================================
    # BELUM MEMILIH
    # =========================================

    if agent["state"] == "Belum Memilih":

        if agent["confidence"] > 0.4:

            agent["state"] = "Eksplorasi"

    # =========================================
    # EKSPLORASI
    # =========================================

    elif agent["state"] == "Eksplorasi":

        if agent["confidence"] < 0.5:

            agent["state"] = "Konsultasi"

        else:

            agent["state"] = "Memutuskan"

    # =========================================
    # KONSULTASI
    # =========================================

    elif agent["state"] == "Konsultasi":

        if agent["confidence"] > 0.7:

            agent["state"] = "Memutuskan"

    # =========================================
    # MEMUTUSKAN
    # =========================================

    elif agent["state"] == "Memutuskan":

        if (
            best_score > 0.75 and
            agent["pressure_parent"] < 0.7
        ):

            agent["state"] = "Cocok Jurusan"

        else:

            agent["state"] = "Salah Jurusan"

    return agent

# =====================================================
# RUN SIMULATION
# =====================================================

st.subheader("🚀 Menjalankan Simulasi...")

simulation_history = []

progress_bar = st.progress(0)

for iteration in range(iterations):

    for _, row in df_agents.iterrows():

        agent = row.to_dict()

        updated_agent = intervention(
            agent,
            scenario
        )

        major, best_score = choose_major(
            updated_agent
        )

        updated_agent = update_state(
            updated_agent,
            best_score
        )

        simulation_history.append({

            "iteration": iteration,

            "agent_id": updated_agent["id"],

            "scenario": scenario,

            "state": updated_agent["state"],

            "selected_major": major,

            "score": best_score,

            "confidence": updated_agent["confidence"],

            "pressure_parent": updated_agent["pressure_parent"]
        })

    progress_bar.progress(
        (iteration + 1) / iterations
    )

df_simulation = pd.DataFrame(
    simulation_history
)

st.success("Simulasi selesai!")

# =====================================================
# DATASET
# =====================================================

st.subheader("📋 Dataset Agent")

st.dataframe(df_agents.head(10))

# =====================================================
# STATUS AGENT
# =====================================================

st.subheader("🧠 Status Agent")

state_counts = df_simulation["state"].value_counts()

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Belum Memilih",
        int(state_counts.get("Belum Memilih", 0))
    )

    st.metric(
        "Eksplorasi",
        int(state_counts.get("Eksplorasi", 0))
    )

with col2:

    st.metric(
        "Konsultasi",
        int(state_counts.get("Konsultasi", 0))
    )

    st.metric(
        "Memutuskan",
        int(state_counts.get("Memutuskan", 0))
    )

with col3:

    st.metric(
        "Cocok Jurusan",
        int(state_counts.get("Cocok Jurusan", 0))
    )

    st.metric(
        "Salah Jurusan",
        int(state_counts.get("Salah Jurusan", 0))
    )

# =====================================================
# PIE CHART STATE
# =====================================================

st.subheader("🥧 Persentase State Agent")

fig_state, ax_state = plt.subplots(figsize=(7,7))

ax_state.pie(
    state_counts,
    labels=state_counts.index,
    autopct='%1.1f%%'
)

st.pyplot(fig_state)

# =====================================================
# DISTRIBUSI JURUSAN
# =====================================================

st.subheader("📊 Distribusi Pemilihan Jurusan")

fig1, ax1 = plt.subplots(figsize=(10,5))

sns.countplot(
    data=df_simulation,
    x="selected_major",
    ax=ax1
)

plt.xticks(rotation=15)

st.pyplot(fig1)

# =====================================================
# DISTRIBUSI STATE
# =====================================================

st.subheader("📈 Distribusi State Agent")

fig2, ax2 = plt.subplots(figsize=(10,5))

sns.countplot(
    data=df_simulation,
    x="state",
    ax=ax2
)

plt.xticks(rotation=15)

st.pyplot(fig2)

# =====================================================
# MONTE CARLO SUMMARY
# =====================================================

summary = df_simulation.groupby(
    ["scenario", "state"]
)["score"].agg([
    "mean",
    "max",
    "min",
    "std"
])

st.subheader("📉 Statistik Monte Carlo")

st.dataframe(summary)

# =====================================================
# TREND GRAPH
# =====================================================

st.subheader("📈 Trend Monte Carlo")

trend = df_simulation.groupby(
    "iteration"
)["score"].mean()

fig3, ax3 = plt.subplots(figsize=(12,5))

ax3.plot(trend)

ax3.set_xlabel("Iteration")

ax3.set_ylabel("Average Score")

ax3.set_title("Monte Carlo Trend")

st.pyplot(fig3)

# =====================================================
# HEATMAP
# =====================================================

st.subheader("🔥 Heatmap Average Score")

pivot = pd.pivot_table(
    df_simulation,
    values="score",
    index="state",
    aggfunc=np.mean
)

fig4, ax4 = plt.subplots(figsize=(7,4))

sns.heatmap(
    pivot,
    annot=True,
    cmap="viridis",
    ax=ax4
)

st.pyplot(fig4)

# =====================================================
# BOXPLOT
# =====================================================

st.subheader("📦 Perbandingan Skenario")

fig5, ax5 = plt.subplots(figsize=(10,5))

sns.boxplot(
    data=df_simulation,
    x="scenario",
    y="score",
    ax=ax5
)

plt.xticks(rotation=10)

st.pyplot(fig5)

# =====================================================
# DOWNLOAD CSV
# =====================================================

st.subheader("💾 Download Hasil Simulasi")

csv = df_simulation.to_csv(index=False)

st.download_button(
    label="⬇️ Download CSV",
    data=csv,
    file_name="simulation_results.csv",
    mime="text/csv"
)

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

st.markdown("""
### Project Information

✅ Agent-Based Modeling  
✅ Monte Carlo Simulation  
✅ 200 Agent  
✅ 1000 Iterasi  
✅ Dynamic State Transition  
✅ Multi Scenario Simulation  
✅ Upload CSV Dinamis  
✅ Download CSV  

Tema:
**Simulasi Pemilihan Jurusan Kuliah**
""")
