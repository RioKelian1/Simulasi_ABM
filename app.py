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
st.subheader("Agent-Based Modeling + Monte Carlo")

# =====================================================
# SIDEBAR
# =====================================================

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
        "Preventif"
    ]
)

uploaded_file = st.sidebar.file_uploader(
    "Upload Dataset CSV",
    type=["csv"]
)

# =====================================================
# STATE
# =====================================================

states = [

    "Belum Memilih",

    "Eksplorasi",

    "Konsultasi",

    "Memutuskan",

    "Cocok Jurusan",

    "Salah Jurusan"
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

            "confidence": random.uniform(0.3,1.0),

            "motivation": random.uniform(0.3,1.0),

            "information_access": random.uniform(0.3,1.0),

            "state": "Belum Memilih"
        })

    return pd.DataFrame(data)

# =====================================================
# LOAD DATA
# =====================================================

if uploaded_file is not None:

    df_agents = pd.read_csv(uploaded_file)

    st.success("Dataset berhasil diupload")

else:

    df_agents = generate_agents(num_agents)

# =====================================================
# MAJORS
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
# SCORE
# =====================================================

def monte_carlo_noise():

    return np.random.normal(0, 0.05)

def calculate_match(agent, profile):

    score = (

        (agent["logic"] * profile["logic"]) +

        (agent["creativity"] * profile["creativity"]) +

        (agent["social"] * profile["social"]) +

        (agent["motivation"] * 0.8) +

        (agent["information_access"] * 0.7)

    ) / 5

    score += monte_carlo_noise()

    return max(0, min(1, score))

# =====================================================
# INTERVENTION
# =====================================================

def intervention(agent, scenario):

    if scenario == "Tanpa Intervensi":

        return agent

    elif scenario == "Reaktif":

        if agent["confidence"] < 0.5:

            agent["confidence"] += 0.2

        if agent["information_access"] < 0.5:

            agent["information_access"] += 0.2

    elif scenario == "Preventif":

        agent["confidence"] += 0.1

        agent["motivation"] += 0.1

        agent["information_access"] += 0.1

    agent["confidence"] = min(
        agent["confidence"],
        1.0
    )

    agent["motivation"] = min(
        agent["motivation"],
        1.0
    )

    agent["information_access"] = min(
        agent["information_access"],
        1.0
    )

    return agent

# =====================================================
# CHOOSE MAJOR
# =====================================================

def choose_major(agent):

    scores = {}

    for major_name, profile in majors.items():

        score = calculate_match(
            agent,
            profile
        )

        scores[major_name] = score

    best_major = max(scores, key=scores.get)

    best_score = max(scores.values())

    return best_major, best_score

# =====================================================
# UPDATE STATE
# =====================================================

def update_state(agent, best_score):

    current_state = agent["state"]

    if current_state == "Belum Memilih":

        if (
            agent["confidence"] > 0.4 and
            random.random() < 0.8
        ):

            agent["state"] = "Eksplorasi"

    elif current_state == "Eksplorasi":

        if (
            agent["information_access"] < 0.5 and
            random.random() < 0.6
        ):

            agent["state"] = "Konsultasi"

        elif random.random() < 0.7:

            agent["state"] = "Memutuskan"

    elif current_state == "Konsultasi":

        if (
            agent["confidence"] > 0.6 and
            random.random() < 0.75
        ):

            agent["state"] = "Memutuskan"

    elif current_state == "Memutuskan":

        if (
            best_score > 0.75 and
            random.random() < 0.8
        ):

            agent["state"] = "Cocok Jurusan"

        elif random.random() < 0.5:

            agent["state"] = "Salah Jurusan"

    return agent

# =====================================================
# RUN SIMULATION
# =====================================================

simulation_history = []

simulation_agents = df_agents.copy()

progress_bar = st.progress(0)

for iteration in range(iterations):

    for idx, row in simulation_agents.iterrows():

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

        simulation_agents.at[idx, "state"] = updated_agent["state"]

        simulation_agents.at[idx, "confidence"] = updated_agent["confidence"]

        simulation_agents.at[idx, "motivation"] = updated_agent["motivation"]

        simulation_agents.at[idx, "information_access"] = updated_agent["information_access"]

        simulation_history.append({

            "iteration": iteration,

            "agent_id": updated_agent["id"],

            "scenario": scenario,

            "state": updated_agent["state"],

            "selected_major": major,

            "score": best_score
        })

    progress_bar.progress(
        (iteration + 1) / iterations
    )

df_simulation = pd.DataFrame(
    simulation_history
)

# =====================================================
# STATUS AGENT
# =====================================================

st.subheader("🧠 Status Agent")

state_counts = df_simulation["state"].value_counts()

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Belum Memilih",
        int(state_counts.get("Belum Memilih",0))
    )

    st.metric(
        "Eksplorasi",
        int(state_counts.get("Eksplorasi",0))
    )

with col2:

    st.metric(
        "Konsultasi",
        int(state_counts.get("Konsultasi",0))
    )

    st.metric(
        "Memutuskan",
        int(state_counts.get("Memutuskan",0))
    )

with col3:

    st.metric(
        "Cocok Jurusan",
        int(state_counts.get("Cocok Jurusan",0))
    )

    st.metric(
        "Salah Jurusan",
        int(state_counts.get("Salah Jurusan",0))
    )

# =====================================================
# PIE CHART
# =====================================================

st.subheader("🥧 Persentase State Agent")

fig1, ax1 = plt.subplots(figsize=(7,7))

ax1.pie(
    state_counts,
    labels=state_counts.index,
    autopct='%1.1f%%'
)

st.pyplot(fig1)

# =====================================================
# COUNT MAJOR
# =====================================================

st.subheader("📊 Distribusi Jurusan")

fig2, ax2 = plt.subplots(figsize=(10,5))

sns.countplot(
    data=df_simulation,
    x="selected_major",
    ax=ax2
)

plt.xticks(rotation=15)

st.pyplot(fig2)

# =====================================================
# TREND
# =====================================================

st.subheader("📈 Trend Monte Carlo")

trend = df_simulation.groupby(
    "iteration"
)["score"].mean()

fig3, ax3 = plt.subplots(figsize=(12,5))

ax3.plot(trend)

st.pyplot(fig3)

# =====================================================
# DOWNLOAD
# =====================================================

csv = df_simulation.to_csv(index=False)

st.download_button(
    label="⬇️ Download CSV",
    data=csv,
    file_name="simulation_results.csv",
    mime="text/csv"
)
