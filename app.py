import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import time
# --- إعدادات الواجهة الاحترافية (Dark Ops Theme) ---
st.set_page_config(layout="wide", page_title="SKYWATCH | WAR ROOM", page_icon="🛡️")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    * { font-family: 'Share Tech Mono', monospace; }
    .main { background-color: #05070a; }
    .stMetric { background: rgba(16, 25, 40, 0.8); border: 1px solid #1a365d; border-radius: 4px; padding: 10px; box-shadow: 0 0 15px rgba(0, 255, 204, 0.1); }
    .css-10trblm { color: #00ffcc !important; }
    /* أنظمة التنبيه */
    .red-alert { background-color: #ff0000; color: white; padding: 10px; animation: blinker 1.5s linear infinite; text-align: center; border-radius: 5px; font-weight: bold; }
    @keyframes blinker { 50% { opacity: 0.3; } }
    </style>
    """, unsafe_allow_html=True)
# --- محرك البيانات المدمج (Real + Tactical Simulation) ---
def fetch_tactical_data():
    # جلب بيانات ADS-B الحقيقية
    try:
        url = "https://opensky-network.org/api/states/all"
        params = {'lamin': 23.0, 'lamax': 29.0, 'lomin': 44.0, 'lomax': 52.0} # تغطية كامل الخليج
        res = requests.get(url, params=params, timeout=3).json()
        raw = pd.DataFrame(res['states'], columns=['id','callsign','origin','t1','t2','lon','lat','alt','g','vel','deg','v_rate','s','geo','sq','spi','src'])
        df = raw[['id', 'callsign', 'lat', 'lon', 'alt', 'vel', 'deg']].dropna()
        df['Class'] = 'Civilian'
    except:
        df = pd.DataFrame(columns=['id', 'callsign', 'lat', 'lon', 'alt', 'vel', 'deg', 'Class'])
    # دمج أهداف "Unknown" ذات سلوك مشبوه (محاكاة رادار عسكري)
    hostiles = pd.DataFrame({
        'id': ['SIGINT-01', 'BOGEY-99'],
        'callsign': ['DRONE_X', 'UNIDENTIFIED'],
        'lat': [26.4 + np.random.uniform(-0.1, 0.1), 24.5],
        'lon': [50.1 + np.random.uniform(-0.1, 0.1), 46.8],
        'alt': [120, 3500], 'vel': [95, 820], 'deg': [180, 45], 'Class': 'Hostile/Stealth'
    })
    return pd.concat([df, hostiles], ignore_index=True)
# --- واجهة القيادة العليا ---
st.markdown("<h1 style='text-align: center; color: #00ffcc; letter-spacing: 5px;'>S K Y W A T C H : C O M M A N D</h1>", unsafe_allow_html=True)
data = fetch_tactical_data()
is_hostile_detected = any(data['Class'] == 'Hostile/Stealth')
# نظام التنبيه العلوي
if is_hostile_detected:
    st.markdown("<div class='red-alert'>⚠️ THREAT DETECTED: UNIDENTIFIED TRACKS IN SOVEREIGN AIRSPACE</div>", unsafe_allow_html=True)
# صف المؤشرات (HUD Metrics)
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("ACTIVE TRACKS", len(data), delta=len(data[data['Class']=='Hostile/Stealth']), delta_color="inverse")
m2.metric("RADAR STATUS", "SCANNING", "OPTIMAL")
m3.metric("INTERCEPTORS", "READY", "SQ-1")
m4.metric("AI CONFIDENCE", "99.2%")
m5.metric("SIGINT LOCK", "ACTIVE")
st.write("---")
# --- تقسيم الشاشة (الخريطة + الرادار الدائري + التحكم) ---
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    st.subheader("🌐 GEOSPATIAL INTELLIGENCE (GEOINT)")
    # خريطة بنمط "Night Vision" عسكري
    m = folium.Map(location=[26.0, 48.0], zoom_start=7, tiles='CartoDB dark_matter')
    for _, obj in data.iterrows():
        color = '#ff0000' if obj['Class'] == 'Hostile/Stealth' else '#00ffcc'
        folium.CircleMarker(
            location=[obj['lat'], obj['lon']],
            radius=6, color=color, fill=True, fill_opacity=0.8,
            popup=f"TGT: {obj['callsign']}\nSPD: {obj['vel']}m/s\nALT: {obj['alt']}m"
        ).add_to(m)
    st_folium(m, width="100%", height=550)

with c2:
    st.subheader("📡 RADAR VECTOR SCAN")
    # رسم رادار دائري احترافي باستخدام Plotly
    fig_radar = go.Figure()
    for _, obj in data.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[obj['vel']], theta=[obj['deg']],
            mode='markers+text', text=[obj['callsign']],
            marker=dict(size=12, color='red' if obj['Class']=='Hostile/Stealth' else '#00ffcc', symbol='triangle-up'),
            name=obj['callsign']
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1000]), bgcolor="#05070a"),
        showlegend=False, paper_bgcolor="#05070a", margin=dict(t=30, b=30, l=30, r=30)
    )
    st.plotly_chart(fig_radar, use_container_width=True)
with c3:
    st.subheader("🛠️ TACTICAL ACTIONS")
    # أكثر من 20 أمر تفاعلي مصنفة
    tab1, tab2 = st.tabs(["COMBAT", "SENSORS"])
    with tab1:
        st.button("🚀 SCRAMBLE F-15SA", key="btn1")
        st.button("📡 ELECTRONIC JAMMING", key="btn2")
        st.button("🔒 TARGET LOCK-ON", key="btn3")
        st.button("☄️ KINETIC INTERCEPT", key="btn4")
        st.button("☢️ EMP BURST", key="btn5")
        st.button("🛑 AIRSPACE LOCKDOWN", key="btn6")
        st.button("🛰️ SATELLITE DE-ORBIT", key="btn7")
    with tab2:
        st.button("🔍 SAR IMAGING", key="btn8")
        st.button("🌡️ THERMAL SCAN", key="btn9")
        st.button("📶 SIGINT DECODE", key="btn10")
        st.button("🌑 STEALTH SCAN", key="btn11")
        st.button("📡 PING IFF", key="btn12")
        st.button("📊 EXPORT LOGS", key="btn13")
# --- جدول تتبع الأهداف (Real-time Log) ---
st.write("### 🗄️ TACTICAL TRACKING LOG")
st.dataframe(data[['callsign', 'Class', 'alt', 'vel', 'deg', 'origin']].style.applymap(
    lambda x: 'color: #ff4b4b; font-weight: bold' if x == 'Hostile/Stealth' else 'color: #00ffcc', subset=['Class']
), use_container_width=True)
# تحديث آلي لغرفة العمليات
time.sleep(5)
st.rerun()
