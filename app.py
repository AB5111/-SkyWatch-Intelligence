import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import time
# --- 1. إعدادات واجهة "الوحش" (Ultra-Dark Tactical UI) ---
st.set_page_config(layout="wide", page_title="THE BEAST | SOVEREIGN CONTROL", page_icon="👹")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    * { font-family: 'Orbitron', sans-serif; }
    .main { background-color: #000000; color: #00ffcc; }
    .stMetric { background: rgba(0, 255, 204, 0.05); border: 1px solid #00ffcc; padding: 20px; border-radius: 0px; box-shadow: 0 0 20px rgba(0, 255, 204, 0.2); }
    .red-alert-beast { background: #660000; color: #ffffff; padding: 20px; border: 3px solid #ff0000; text-align: center; font-size: 24px; font-weight: bold; animation: pulse-red 1s infinite; }
    @keyframes pulse-red { 0% { box-shadow: 0 0 0px #ff0000; } 50% { box-shadow: 0 0 40px #ff0000; } 100% { box-shadow: 0 0 0px #ff0000; } }
    </style>
    """, unsafe_allow_html=True)
# --- 2. محرك البيانات الهجين (Hybrid Radar Engine) ---
@st.cache_data(ttl=20)
def get_beast_radar():
    # المصدر 1: رادار OpenSky (بيانات حقيقية)
    try:
        url = "https://opensky-network.org/api/states/all"
        params = {'lamin': 12.0, 'lamax': 35.0, 'lomin': 33.0, 'lomax': 60.0} # تغطية إقليمية شاملة
        res = requests.get(url, params=params, timeout=5).json()
        raw = pd.DataFrame(res['states']).iloc[:, [1, 5, 6, 7, 9, 10]]
        raw.columns = ['id', 'lon', 'lat', 'alt', 'vel', 'deg']
        raw['Status'] = 'SECURE'
    except:
        raw = pd.DataFrame(columns=['id', 'lon', 'lat', 'alt', 'vel', 'deg', 'Status'])
    # المصدر 2: طبقة الأهداف التكتيكية (Simulation لضمان استمرار الحركة)
    tactical_data = pd.DataFrame({
        'id': ['X-WARRIOR', 'STLTH-09', 'UAV-INTEL'],
        'lon': [46.7, 50.1, 48.5], 'lat': [24.7, 26.3, 25.0],
        'alt': [200, 15000, 50], 'vel': [450, 2200, 80], 'deg': [90, 45, 180],
        'Status': 'HOSTILE'
    })
    return pd.concat([raw, tactical_data], ignore_index=True).fillna(0)
# --- 3. لوحة القيادة العليا ---
st.markdown("<h1 style='text-align: center; color: #ff0000; text-shadow: 0 0 30px #ff0000;'>👹 T H E  B E A S T : V 9 . 0</h1>", unsafe_allow_html=True)
data = get_beast_radar()
hostiles = data[data['Status'] == 'HOSTILE']
if not hostiles.empty:
    st.markdown("<div class='red-alert-beast'> CRITICAL THREAT: UNKNOWN TRACKS IN SOVEREIGN SECTOR</div>", unsafe_allow_html=True)
# عدادات HUD
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("LIVE TRACKS", len(data), delta=len(hostiles), delta_color="inverse")
m2.metric("RADAR SWEEP", "360° ACTIVE")
m3.metric("THREAT LEVEL", "RED" if len(hostiles) > 0 else "GREEN")
m4.metric("AI CORE", "ENGAGED")
m5.metric("ENCRYPTION", "AES-512")
st.write("---")
# --- 4. مركز العمليات (الخريطة والرادار) ---
col_map, col_ctrl = st.columns([2.5, 1])
with col_map:
    st.subheader(" Global Satellite Intelligence")
    # استخدام خريطة الأقمار الصناعية العسكرية مع ربط Esri
    m = folium.Map(location=[24.5, 46.5], zoom_start=6, 
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                   attr='Esri Military Intelligence')
    for _, r in data.iterrows():
        color = 'red' if r['Status'] == 'HOSTILE' else '#00ffcc'
        folium.CircleMarker(
            location=[r['lat'], r['lon']], radius=8 if r['Status'] == 'HOSTILE' else 5,
            color=color, fill=True, fill_opacity=0.8,
            popup=f"TGT: {r['id']} | SPD: {r['vel']}m/s"
        ).add_to(m)
    st_folium(m, width="100%", height=600)
with col_ctrl:
    st.subheader(" Tactical Vector Scan")
    # رادار دائري متطور
    fig_radar = go.Figure()
    for _, r in data.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[r['vel']], theta=[r['deg']], mode='markers+text', text=[r['id']],
            marker=dict(size=12, color='red' if r['Status'] == 'HOSTILE' else '#00ffcc', symbol='cross'),
            name=r['id']
        ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 2500]), bgcolor="#000000"),
                            paper_bgcolor="#000000", showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig_radar, use_container_width=True)
    # 20+ أوامر جانبية بنظام الضغط السريع
    st.markdown("###  Command Matrix")
    tabs = st.tabs([" Attack", " Defense", " Sensors"])
    with tabs[0]:
        st.button(" LAUNCH INTERCEPTORS")
        st.button(" LOCK-ON ALL HOSTILES")
        st.button(" KINETIC STRIKE")
        st.button(" EMP BURST")
    with tabs[1]:
        st.button("🛑 LOCK AIRSPACE")
        st.button("🌑 STEALTH CLOAK")
        st.button(" SIGNAL JAMMING")
        st.button(" POINT DEFENSE")
    with tabs[2]:
        st.button(" DEEP SCAN")
        st.button(" THERMAL OVERLAY")
        st.button(" SAT SYNC")
        st.button(" SIGINT DECODE")
# --- 5. سجل البيانات الاستخباراتي ---
st.subheader(" Mission Critical Log")
st.dataframe(data.sort_values(by='Status', ascending=False), use_container_width=True)
# تحديث آلي ثابت كل 15 ثانية
time.sleep(15)
st.rerun()
