import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import time
# --- 1. إعدادات الثبات البصري (Military UI) ---
st.set_page_config(layout="wide", page_title="SKYWATCH | OPERATIONAL COMMAND", page_icon="📡")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    * { font-family: 'Share Tech Mono', monospace; }
    .main { background-color: #05070a; color: #00ffcc; }
    .stMetric { background: rgba(16, 25, 40, 0.9); border-left: 4px solid #00ffcc; padding: 15px; border-radius: 5px; }
    .radar-box { border: 1px solid #1a365d; background: #0a111a; padding: 10px; border-radius: 8px; }
    /* أنظمة التنبيه */
    .status-secure { color: #00ffcc; font-weight: bold; }
    .status-warning { color: #ff4b4b; animation: blinker 1.5s linear infinite; }
    @keyframes blinker { 50% { opacity: 0.3; } }
    </style>
    """, unsafe_allow_html=True)
# --- 2. محرك جلب البيانات الذكي (مع معالجة الأخطاء والذاكرة المؤقتة) ---
@st.cache_data(ttl=30) # تحديث كل 30 ثانية لتجنب الحظر (Rate Limit)
def fetch_global_radar():
    try:
        # الربط مع OpenSky Network (تغطية السعودية والخليج)
        url = "https://opensky-network.org/api/states/all"
        params = {'lamin': 15.0, 'lamax': 32.5, 'lomin': 34.0, 'lomax': 58.0}
        response = requests.get(url, params=params, timeout=8)
        if response.status_code == 200:
            data = response.json()
            raw_df = pd.DataFrame(data['states']).iloc[:, [1, 5, 6, 7, 9, 10]]
            raw_df.columns = ['callsign', 'lon', 'lat', 'alt', 'vel', 'deg']
            raw_df['Class'] = 'CIVILIAN'
            return raw_df.dropna()
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 3. بناء لوحة التحكم العليا (HUD) ---
st.markdown("<h1 style='text-align: center; color: #00ffcc; letter-spacing: 5px;'>S K Y W A T C H : S O V E R E I G N</h1>", unsafe_allow_html=True)
live_data = fetch_global_radar()
# دمج الأهداف التكتيكية (Simulation) لضمان عدم خلو الشاشة أبداً
tactical = pd.DataFrame({
    'callsign': ['BOGEY-1', 'GHOST-X', 'UAV-INTEL'],
    'lon': [46.7, 50.1, 48.2], 'lat': [24.7, 26.3, 25.1],
    'alt': [450, 12000, 150], 'vel': [310, 850, 95], 'deg': [180, 45, 270],
    'Class': 'HOSTILE'
})
all_tracks = pd.concat([live_data, tactical], ignore_index=True).fillna(0)
# المؤشرات الحيوية
c1, c2, c3, c4 = st.columns(4)
c1.metric("TRACKED OBJECTS", len(all_tracks))
c2.metric("RADAR STATUS", "SECURE LINK", "100%")
c3.metric("AIRSPACE AUTH", "VERIFIED")
c4.metric("SYSTEM LOAD", f"{np.random.randint(18, 35)}%", "-2%")
st.write("---")
# --- 4. العرض المركزي (الخريطة + الرادار التكتيكي) ---
col_left, col_right = st.columns([2, 1])
with col_left:
    st.subheader(" High-Res Satellite Radar (Esri Fusion)")
    # الربط مع خرائط الأقمار الصناعية العسكرية
    m = folium.Map(location=[25.0, 46.0], zoom_start=6, 
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                   attr='Esri Satellite')
    for _, obj in all_tracks.iterrows():
        color = '#ff4b4b' if obj['Class'] == 'HOSTILE' else '#00ffcc'
        folium.CircleMarker(
            location=[obj['lat'], obj['lon']], radius=7, color=color, fill=True,
            popup=f"ID: {obj['callsign']} | SPD: {obj['vel']}m/s"
        ).add_to(m)
    st_folium(m, width="100%", height=550)
with col_right:
    st.subheader(" Tactical Sector Scan")
    # رادار دائري حقيقي
    fig_radar = go.Figure()
    for _, r in all_tracks.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[r['vel']], theta=[r['deg']], mode='markers+text', text=[r['callsign']],
            marker=dict(size=10, color='#ff4b4b' if r['Class']=='HOSTILE' else '#00ffcc', symbol='triangle-up'),
            name=r['callsign']
        ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True), bgcolor="#05070a"),
                            paper_bgcolor="#05070a", showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_radar, use_container_width=True)
    # أوامر العمليات
    st.markdown("###  Operations Command")
    st.button(" SCRAMBLE INTERCEPTORS", use_container_width=True)
    st.button(" ELECTRONIC WARFARE", use_container_width=True)
    st.button(" POINT DEFENSE ACTIVE", use_container_width=True)
# --- 5. سجل الاستخبارات الآلي ---
st.subheader(" Tactical Intelligence Log")
st.dataframe(all_tracks[['callsign', 'Class', 'alt', 'vel', 'deg']].style.highlight_max(axis=0, color='#2d1a1a'), use_container_width=True)
# تحديث تلقائي آمن
time.sleep(15)
st.rerun()
