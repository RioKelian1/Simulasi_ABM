import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
import random

# --- CONFIG DASHBOARD ---
st.set_page_config(page_title="Simulasi Pemilihan Jurusan ABM", page_icon="🎓", layout="wide")
st.title("🎓 Dashboard Simulasi Pemilihan Jurusan Kuliah (ABM)")
st.markdown("Mengukur efektivitas sistem rekomendasi (*Pasif, Reaktif, Preventif*) terhadap stabilitas keputusan siswa.")

# --- KELAS AGEN & MODEL (SINKRON DENGAN COLAB ANDA) ---
STABLE_WINDOW = 3

class StudentAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.interest = random.uniform(0.4, 1.0)
        self.ability = random.uniform(0.4, 1.0)
        self.confidence = random.uniform(0.2, 0.6)
        self.influence = random.uniform(0.1, 0.8)
        self.x = random.randint(0, 19)
        self.y = random.randint(0, 19)
        self.state = "CONFUSED"
        self.decision_streak = 0
        self.chosen_major = None

    def move(self):
        self.x = (self.x + random.choice([-1, 0, 1])) % 20
        self.y = (self.y + random.choice([-1, 0, 1])) % 20

    def interact(self, nearby_agents):
        decided_neighbors = sum(1 for agent in nearby_agents if agent.state == "DECIDED")
        self.confidence += decided_neighbors * 0.01

    def choose_major(self):
        self.chosen_major = random.choice(["Teknik Informatika", "Psikologi", "DKV"])

    def update_state(self, info_level, recommendation):
        # Formulasi Matematis Minggu 4 dari Colab Anda
        delta = (self.interest * self.ability * info_level * 0.08) - (self.influence * 0.05) + (recommendation * 0.07)
        self.confidence = max(0.0, min(1.0, self.confidence + delta))
        
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

# --- SIDEBAR PARAMETER ---
st.sidebar.header("⚙️ Pengaturan Simulasi")
scenario_type = st.sidebar.selectbox("Pilih Skenario Intervensi:", ["Pasif", "Reaktif", "Preventif"])
total_agents = st.sidebar.slider("Jumlah Siswa (Agent)", 10, 200, 50)
total_iterations = st.sidebar.slider("Durasi Iterasi (Steps)", 10, 200, 100)
run_btn = st.sidebar.button("▶️ Jalankan Simulasi")

# --- ENGINE SIMULASI ---
if run_btn:
    # Inisialisasi populasi agen
    agents = [StudentAgent(i) for i in range(total_agents)]
    history_records = []
    
    chart_placeholder = st.empty()
    metric_placeholder = st.empty()
    progress_bar = st.progress(0)

    for step in range(total_iterations):
        # Seting level parameter berdasarkan aturan Skenario Minggu 12 di Colab Anda
        if scenario_type == "Pasif":
            info_level = 0.4
            recommendation = 0.0
        elif scenario_type == "Reaktif":
            info_level = 0.6
            # Cek status decided terakhir untuk menentukan akselerasi rekomendasi
            last_decided = history_records[-1]["DECIDED"] if len(history_records) > 0 else 0
            recommendation = 0.7 if last_decided < (total_agents * 0.4) else 0.3
        elif scenario_type == "Preventif":
            info_level = 0.8
            recommendation = 0.8

        # Proses Spasial Mobilitas & Interaksi Agen
        for agent in agents:
            agent.move()
            # Hitung tetangga terdekat (jarak Manhattan <= 2)
            neighbors = [a for a in agents if a.agent_id != agent.agent_id and (abs(a.x - agent.x) + abs(a.y - agent.y)) <= 2]
            agent.interact(neighbors)
            agent.update_state(info_level, recommendation)

        # Hitung statistik state step ini
        confused = sum(1 for a in agents if a.state == "CONFUSED")
        matching = sum(1 for a in agents if a.state == "MATCHING")
        decided = sum(1 for a in agents if a.state == "DECIDED")
        
        ti = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "Teknik Informatika")
        psi = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "Psikologi")
        dkv = sum(1 for a in agents if a.state == "DECIDED" and a.chosen_major == "DKV")

        history_records.append({"Step": step, "CONFUSED": confused, "MATCHING": matching, "DECIDED": decided})
        df_history = pd.DataFrame(history_records)

        # Update Live Dashboard
        with metric_placeholder.container():
            col1, col2, col3 = st.columns(3)
            col1.metric("Siswa CONFUSED", confused)
            col2.metric("Siswa MATCHING", matching)
            col3.metric("Siswa DECIDED", decided, delta=f"+{decided}")

        with chart_placeholder.container():
            c1, c2 = st.columns(2)
            with c1:
                fig_line = px.line(df_history, x="Step", y=["CONFUSED", "MATCHING", "DECIDED"],
                                   title="Kurva Perubahan State Pengambilan Keputusan",
                                   color_discrete_map={"CONFUSED": "#ef4444", "MATCHING": "#eab308", "DECIDED": "#22c55e"})
                st.plotly_chart(fig_line, use_container_width=True)
            with c2:
                df_bar = pd.DataFrame({"Jurusan": ["Teknik Informatika", "Psikologi", "DKV"], "Jumlah": [ti, psi, dkv]})
                fig_bar = px.bar(df_bar, x="Jurusan", y="Jumlah", title="Distribusi Pemilihan Jurusan Aktual",
                                 color="Jurusan", color_discrete_sequence=["#3b82f6", "#a855f7", "#f59e0b"])
                st.plotly_chart(fig_bar, use_container_width=True)

        progress_bar.progress((step + 1) / total_iterations)
        time.sleep(0.03)

    st.success(f"🎉 Simulasi skenario {scenario_type} selesai dijalankan!")
else:
    st.info("💡 Pilih skenario di menu sidebar kiri, lalu klik tombol jalankan untuk melihat visualisasi analitik.")
