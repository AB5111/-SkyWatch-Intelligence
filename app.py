import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import time
# --- 1. HUD & Military Theme Configuration ---
st.set_page_config(layout="wide", page_title="SKYWATCH | JOC COMMAND", page_icon="🛡️")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    * { font-family: 'Share Tech Mono', monospace; }
    .main { background-color: #05070a; color: #00ffcc; }
    .stMetric { background: rgba(16, 25, 40, 0.9); border-left: 4px solid #00ffcc; padding: 15px; border-radius: 5px; }
    div[data-testid="stExpander"] { background: #0a111a; border: 1px solid #1a365d; }
    .red-alert { background: #450a0a; color: #ff4b4b; padding: 15px; border: 2px solid #ff4b4b; text-align: center; 
                 animation: pulse 2s infinite; font-weight: bold; font-size: 20px; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)
# --- 2. Intelligent Data Fusion (Fixed KeyErrors) ---
def get_ops_data():
    try:
        url = "https://opensky-network.org/api/states/all"
        # نطاق المملكة العربية السعودية والخليج
        params = {'lamin': 15.0, 'lamax': 32.0, 'lomin': 35.0, 'lomax': 56.0}
        res = requests.get(url, params=params, timeout=5).json()
        raw = pd.DataFrame(res['states'])
        # تأكد من وجود الأعمدة المطلوبة وتسميتها
        df = raw.iloc[:, [1, 5, 6, 7, 9, 10]].copy()
        df.columns = ['callsign', 'lon', 'lat', 'alt', 'vel', 'deg']
        df['Class'] = 'CIVILIAN'
    except:
        df = pd.DataFrame(columns=['callsign', 'lon', 'lat', 'alt', 'vel', 'deg', 'Class'])
    # إضافة أهداف عسكرية محاكية (Tactical Overlay)
    tactical_targets = pd.DataFrame({
        'callsign': ['STLTH-01', 'BOGEY-X', 'UAV-INT'],
        'lon': [46.7, 50.1, 48.5], 'lat': [24.7, 26.3, 25.5],
        'alt': [150, 4500, 800], 'vel': [320, 950, 120], 'deg': [270, 45, 180],
        'Class': 'HOSTILE/UNKNOWN'
    })
    return pd.concat([df, tactical_targets], ignore_index=True).fillna(0)
# --- 3. Dashboard HUD Header ---
st.markdown("<h1 style='text-align: center; color: #00ffcc; text-shadow: 0 0 10px #00ffcc;'>S K Y W A T C H : JOINT OPERATIONS CENTER</h1>", unsafe_allow_html=True)
data = get_ops_data()
hostile_count = len(data[data['Class'] != 'CIVILIAN'])
if hostile_count > 0:
    st.markdown(f"<div class='red-alert'>⚠️ DEFCON 3: {hostile_count} UNIDENTIFIED TRACKS DETECTED</div>", unsafe_allow_html=True)
# HUD Metrics
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("TOTAL TRACKS", len(data))
c2.metric("THREAT LEVEL", "ELEVATED" if hostile_count > 0 else "LOW")
c3.metric("RADAR SWEEP", "ACTIVE", "S-BAND")
c4.metric("AI ANALYSIS", "STABLE", "96%")
c5.metric("SIGINT LOCK", "ESTABLISHED")
st.write("---")
# --- 4. Main Command Display ---
col_map, col_radar, col_ops = st.columns([2, 1, 1])
with col_map:
    st.subheader("🛰️ GEOINT: Satellite Surveillance")
    # خريطة قمر صناعي بنمط عسكري داكن
    m = folium.Map(location=[25.0, 45.0], zoom_start=6, tiles='CartoDB dark_matter')
    for _, r in data.iterrows():
        color = '#ff4b4b' if r['Class'] != 'CIVILIAN' else '#00ffcc'
        folium.CircleMarker(
            location=[r['lat'], r['lon']], radius=6, color=color, fill=True,
            popup=f"ID: {r['callsign']} | SPD: {r['vel']}m/s"
        ).add_to(m)
    st_folium(m, width="100%", height=500)
with col_radar:
    st.subheader("📡 Tactical Vector Scan")
    # رادار دائري يظهر اتجاه وسرعة الأهداف
    fig_radar = go.Figure()
    for _, r in data.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[r['vel']], theta=[r['deg']], mode='markers+text', text=[r['callsign']],
            marker=dict(size=10, color='#ff4b4b' if r['Class'] != 'CIVILIAN' else '#00ffcc', symbol='triangle-up'),
            name=r['callsign']
        ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True), bgcolor="#05070a"),
                            paper_bgcolor="#05070a", showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_radar, use_container_width=True)
with col_ops:
    st.subheader("🛠️ Tactical Command")
    with st.container():
        st.button("🚀 SCRAMBLE INTERCEPTORS", use_container_width=True)
        st.button("📡 ELECTRONIC WARFARE (JAM)", use_container_width=True)
        st.button("🔒 TARGET DESIGNATION", use_container_width=True)
        st.button("🛡️ POINT DEFENSE ACTIVE", use_container_width=True)
        st.button("📶 BATTLEFIELD SIGINT", use_container_width=True)
        st.button("🌑 STEALTH COUNTERMEASURES", use_container_width=True)
# --- 5. Tactical Log (Safe Rendering) ---
st.subheader("📋 Operations Log")
# عرض الأعمدة المتاحة فقط لتجنب KeyError
display_cols = ['callsign', 'Class', 'alt', 'vel', 'deg']
st.dataframe(data[display_cols].style.highlight_max(axis=0, color='#2d1a1a'), use_container_width=True)
# Auto-refresh logic
time.sleep(10)
st.rerun()
