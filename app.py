%%writefile app.py

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random

# =====================================
# CONFIG
# =====================================

st.set_page_config(
    page_title="ABM Pemilihan Jurusan",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Simulasi Pemilihan Jurusan Kuliah")
st.subheader("Agent-Based Modeling + Monte Carlo")

# =====================================
# SIDEBAR
# =====================================

st.sidebar.header("⚙️ Pengaturan")

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
    "Upload CSV",
    type=["csv"]
)

# =====================================
# GENERATE DATASET
# =====================================

states = [
    "Bingung",
    "Eksplorasi",
    "Yakin",
    "Salah Jurusan",
    "Cocok Jurusan"
]

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

            "state": random.choice(states)
        })

    return pd.DataFrame(data)

# =====================================
# LOAD DATA
# =====================================

if uploaded_file is not None:

    df_agents = pd.read_csv(uploaded_file)

else:

    df_agents = generate_agents(num_agents)

# =====================================
# JURUSAN
# =====================================

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

# =====================================
# FUNCTION
# =====================================

def calculate_match(agent, major_profile):

    score = (
        (agent["logic"] * major_profile["logic"]) +
        (agent["creativity"] * major_profile["creativity"]) +
        (agent["social"] * major_profile["social"])
    ) / 3

    return score

def parental_pressure_effect(base_score, pressure):

    noise = np.random.normal(0, 0.05)

    final_score = base_score - (pressure * 0.2) + noise

    return max(0, min(1, final_score))

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

    agent["confidence"] = min(
        agent["confidence"],
        1.0
    )

    agent["pressure_parent"] = min(
        agent["pressure_parent"],
        1.0
    )

    return agent

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

# =====================================
# SIMULATION
# =====================================

simulation_history = []

progress = st.progress(0)

for iteration in range(iterations):

    for _, row in df_agents.iterrows():

        agent = row.to_dict()

        updated_agent = intervention(
            agent,
            scenario
        )

        major, scores = choose_major(updated_agent)

        simulation_history.append({

            "iteration": iteration,

            "agent_id": updated_agent["id"],

            "scenario": scenario,

            "selected_major": major,

            "score": max(scores.values()),

            "confidence": updated_agent["confidence"],

            "pressure_parent": updated_agent["pressure_parent"]
        })

    progress.progress((iteration+1)/iterations)

df_simulation = pd.DataFrame(simulation_history)

# =====================================
# DASHBOARD
# =====================================

st.subheader("📋 Dataset Agent")

st.dataframe(df_agents.head(10))

# =====================================
# COUNT PLOT
# =====================================

st.subheader("📊 Distribusi Jurusan")

fig1, ax1 = plt.subplots(figsize=(10,5))

sns.countplot(
    data=df_simulation,
    x="selected_major",
    ax=ax1
)

plt.xticks(rotation=15)

st.pyplot(fig1)

# =====================================
# SUMMARY
# =====================================

summary = df_simulation.groupby(
    "selected_major"
)["score"].agg([
    "mean",
    "max",
    "min",
    "std"
])

st.subheader("📈 Statistik")

st.dataframe(summary)

# =====================================
# TREND
# =====================================

trend = df_simulation.groupby(
    "iteration"
)["score"].mean()

fig2, ax2 = plt.subplots(figsize=(12,5))

ax2.plot(trend)

ax2.set_title("Trend Monte Carlo")

st.pyplot(fig2)

# =====================================
# HEATMAP
# =====================================

pivot = pd.pivot_table(
    df_simulation,
    values="score",
    index="selected_major",
    aggfunc=np.mean
)

fig3, ax3 = plt.subplots(figsize=(7,4))

sns.heatmap(
    pivot,
    annot=True,
    cmap="viridis",
    ax=ax3
)

st.pyplot(fig3)

# =====================================
# PIE CHART
# =====================================

st.subheader("🥧 Persentase Jurusan")

major_counts = df_simulation[
    "selected_major"
].value_counts()

fig4, ax4 = plt.subplots(figsize=(7,7))

ax4.pie(
    major_counts,
    labels=major_counts.index,
    autopct='%1.1f%%'
)

st.pyplot(fig4)

# =====================================
# DOWNLOAD CSV
# =====================================

csv = df_simulation.to_csv(index=False)

st.download_button(
    label="⬇️ Download CSV",
    data=csv,
    file_name="simulation_results.csv",
    mime="text/csv"
)

# =====================================
# FOOTER
# =====================================

st.markdown("---")

st.markdown("""
### Project Information

- Agent-Based Modeling
- Monte Carlo Simulation
- 200 Agent
- 1000 Iterasi
- Multi Scenario Simulation
- Upload CSV Dinamis

Tema:
Simulasi Pemilihan Jurusan Kuliah
""")
