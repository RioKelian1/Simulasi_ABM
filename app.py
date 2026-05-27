import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time

# --- PENGATURAN HALAMAN DASHBOARD (MINGGU 16) ---
st.set_page_config(
    page_title="Simulasi ABM - Koping Kecemasan CBT", 
    page_icon="🧠", 
    layout="wide"
)

st.title("🧠 Dashboard Simulasi Dinamika Kecemasan Mahasiswa")
st.subtitle("Pendekatan Agent-Based Modeling dengan Evaluasi Protokol CBT")
st.markdown("""
Dashboard ini dirancang sesuai dengan pedoman UAS untuk mensimulasikan bagaimana intervensi 
*Cognitive Behavioral Therapy* (CBT) dapat meredam tingkat kecemasan mahasiswa terhadap stresor lingkungan.
""")

# --- 1. DEFINISI AGEN & FORMULASI MATEMATIS (MINGGU 4 & MINGGU 6) ---
class MahasiswaAgent:
    def __init__(self, agent_id, skenario):
        self.id = agent_id
        # Atribut Internal Agen (Halaman 1 PDF)
        self.anxiety = np.random.uniform(0.1, 0.4)       # Anxiety Level (A) awal: tenang
        self.resilience = np.random.uniform(0.2, 0.5)    # Resilience (R)
        
        # Skenario 4: Distorsi Kognitif Tinggi
        if skenario == "Skenario 4: Distorsi Kognitif Tinggi":
            self.distortion = np.random.uniform(1.8, 2.5) # D diperburuk (Catastrophizing)
        else:
            self.distortion = np.random.uniform(1.0, 1.4) # D Normal (Distortion Factor)
            
        self.state = "TENANG" # State Chart awal (Minggu 2)

    def update_anxiety(self, skenario, stressor_S, cbt_P_base):
        # Menentukan nilai Protokol CBT (P) berdasarkan Skenario "What-If" (Minggu 12 & Halaman 2 PDF)
        cbt_P = 0.0
        
        if skenario == "Skenario 1: Tanpa Intervensi":
            cbt_P = 0.0 # Agen dibiarkan stres tanpa koping
            
        elif skenario == "Skenario 2: Reaktif":
            # Intervensi CBT hanya diberikan secara reaktif jika tingkat kecemasan kritis (A > 0.8)
            if self.anxiety > 0.8:
                cbt_P = cbt_P_base
            else:
                cbt_P = 0.0
                
        elif skenario == "Skenario 3: Preventif":
            # Latihan koping rutin dilakukan di setiap iterasi waktu
            cbt_P = cbt_P_base * 0.6
            
        elif skenario == "Skenario 4: Distorsi Kognitif Tinggi":
            # Mendapat intervensi standar namun faktor distorsi internalnya tinggi
            cbt_P = cbt_P_base

        # --- ATURAN TRANSISI PERSAMAAN MATEMATIKA (Halaman 1 PDF) ---
        # A_(t+1) = A_t + (S * D) - (R * P)
        delta_A = (stressor_S * self.distortion) - (self.resilience * cbt_P)
        self.anxiety += delta_A
        
        # Batasi nilai kecemasan pada skala numerik 0.0 - 1.0
        self.anxiety = max(0.0, min(1.0, self.anxiety))

        # --- UPDATE STATE CHART AGEN (MINGGU 2) ---
        if self.anxiety > 0.8:
            self.state = "PANIK"
        elif self.anxiety > 0.5:
            self.state = "CEMAS"
        else:
            self.state = "TENANG"

# --- 2. SIDEBAR KONTROL PARAMETER DAN SLIDER (MINGGU 16 / HALAMAN 3 PDF) ---
st.sidebar.header("⚙️ Kontrol Parameter Simulasi")

skenario_terpilih = st.sidebar.selectbox(
    "Pilih Skenario Pengujian:",
    [
        "Skenario 1: Tanpa Intervensi",
        "Skenario 2: Reaktif",
        "Skenario 3: Preventif",
        "Skenario 4: Distorsi Kognitif Tinggi"
    ]
)

# Slider Tingkat Stresor Lingkungan yang diminta wajib ada di halaman 3 dokumen PDF
stressor_S = st.sidebar.slider("Tingkat Stresor Lingkungan (S)", 0.0, 0.5, 0.2, 0.05)
cbt_P_base = st.sidebar.slider("Kekuatan Protokol Intervensi CBT (P)", 0.1, 1.0, 0.5, 0.05)
num_agents = st.sidebar.slider("Jumlah Mahasiswa (Populasi Agen)", 20, 300, 100, 10)
steps = st.sidebar.slider("Durasi Waktu Pengamatan (Iterasi/Steps)", 50, 1000, 150, 50)

run_simulation = st.sidebar.button("▶️ Jalankan Simulasi Koping CBT")

# --- 3. JALANNYA EKSEKUSI MODEL RUNNER & VISUALISASI ---
if run_simulation:
    # Bangun populasi awal agen mahasiswa
    populasi = [MahasiswaAgent(i, skenario_terpilih) for i in range(num_agents)]
    
    st.subheader(f"📊 Analisis Data Real-Time: {skenario_terpilih}")
    
    # Bungkus metrik ringkasan atas
    col_m1, col_m2, col_m3 = st.columns(3)
    m1 = col_m1.empty()
    m2 = col_m2.empty()
    m3 = col_m3.empty()
    
    chart_placeholder = st.empty()
    history_data = []
    progress_bar = st.progress(0)

    # Loop Iterasi Waktu Utama (Monte Carlo Engine)
    for t in range(steps):
        tenang_count = sum(1 for a in populasi if a.state == "TENANG")
        cemas_count = sum(1 for a in populasi if a.state == "CEMAS")
        panik_count = sum(1 for a in populasi if a.state == "PANIK")
        
        # Hitung rata-rata tingkat kecemasan populasi saat ini
        avg_anxiety = np.mean([a.anxiety for a in populasi])
        
        # Isi Kartu Indikator Utama
        m1.metric("Rata-rata Kecemasan Akut", f"{avg_anxiety:.2f}")
        m2.metric("Jumlah Mahasiswa Panik (A > 0.8)", f"{panik_count}")
        m3.metric("Kondisi Pulih/Tenang", f"{tenang_count}")
        
        # Rekam perkembangan data analisis (Minggu 14)
        history_data.append({
            "Waktu (Step)": t,
            "Tenang": tenang_count,
            "Cemas": cemas_count,
            "Panik": panik_count,
            "Rata-rata Kecemasan": avg_anxiety
        })
        df_history = pd.DataFrame(history_data)
        
        # Render Grafik Interaktif Plotly
        with chart_placeholder.container():
            col_graph_left, col_graph_right = st.columns(2)
            
            with col_graph_left:
                # Tren Tingkat Kecemasan Rata-rata Sesuai UTS/UAS
                fig_line = px.line(
                    df_history, x="Waktu (Step)", y="Rata-rata Kecemasan",
                    title="Kurva Fluktuasi Tingkat Kecemasan Populasi",
                    color_discrete_sequence=["#3b82f6"]
                )
                fig_line.update_yaxes(range=[0, 1])
                st.plotly_chart(fig_line, use_container_width=True)
                
            with col_graph_right:
                # Sebaran Transisi Kondisi Mental Mahasiswa
                df_state = pd.DataFrame({
                    "Kondisi Mental": ["Tenang", "Cemas", "Panik"],
                    "Jumlah Mahasiswa": [tenang_count, cemas_count, panik_count]
                })
                fig_bar = px.bar(
                    df_state, x="Kondisi Mental", y="Jumlah Mahasiswa",
                    title="Distribusi Perubahan Kondisi Psikologis Mahasiswa",
                    color="Kondisi Mental", color_discrete_sequence=["#22c55e", "#eab308", "#ef4444"]
                )
                st.plotly_chart(fig_bar, use_container_width=True)
                
        # Perbarui kondisi kecemasan agen berdasarkan rumus matematika utama
        for agent in populasi:
            agent.update_anxiety(skenario_terpilih, stressor_S, cbt_P_base)
            
        progress_bar.progress((t + 1) / steps)
        time.sleep(0.02)
        
    st.success(f"🎉 Pengujian {skenario_terpilih} berhasil divalidasi. Grafik menunjukkan efektivitas koping CBT secara berkala.")
else:
    st.info("💡 Atur variabel 'Tingkat Stresor' di panel sidebar kiri, lalu klik **Jalankan Simulasi Koping CBT** untuk melihat grafik interaktif.")
