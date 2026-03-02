import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
# إعداد الصفحة
st.set_page_config(layout="wide", page_title="SkyWatch C2 System")
# تصميم الواجهة العسكرية
st.markdown("""
    <style>
    .main { background-color: #0b0f14; }
    .stButton>button { width: 100%; background-color: #1a202c; color: #00ffcc; border: 1px solid #374151; }
    .stButton>button:hover { background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)
# وظيفة جلب الرادار الموحد (تجنب خطأ التنسيق)
def get_radar_data():
    # 1. محاولة جلب بيانات حقيقية
    try:
        url = "https://opensky-network.org/api/states/all"
        params = {'lamin': 24.0, 'lamax': 28.0, 'lomin': 45.0, 'lomax': 51.0}
        res = requests.get(url, params=params, timeout=3).json()
        real_df = pd.DataFrame(res['states'], columns=['id','callsign','origin','time','contact','lon','lat','alt','ground','vel','deg','ver','sensors','geo','sq','spi','src'])
        real_df = real_df[['id', 'callsign', 'lat', 'lon', 'alt', 'vel']].dropna()
        real_df['Type'] = 'CIVILIAN'
    except:
        real_df = pd.DataFrame(columns=['id', 'callsign', 'lat', 'lon', 'alt', 'vel', 'Type'])
    # 2. إضافة أهداف مجهولة (Stealth/Hostile) للمحاكاة والتدريب
    stealth_data = pd.DataFrame({
        'id': ['TGT-99', 'UAV-X'],
        'callsign': ['BOGEY1', 'GHOST'],
        'lat': [26.3, 25.1],
        'lon': [50.1, 46.7],
        'alt': [250, 500],
        'vel': [140, 280],
        'Type': 'HOSTILE'
    })
    return pd.concat([real_df, stealth_data], ignore_index=True)
# العنوان العلوي
st.title("🛡️ SkyWatch C2: Integrated Air Defense Command")
st.write(f"System Time: {datetime.now().strftime('%H:%M:%S')} | Status: Operational")
data = get_radar_data()
# --- لوحة الأوامر الجانبية (أكثر من 20 أمر) ---
with st.sidebar:
    st.header("🎮 Tactical Control Unit")
    with st.expander("📡 Radar & Sensor Suite", expanded=True):
        cols = st.columns(2)
        cols[0].button("Full Sweep")
        cols[1].button("Active Ping")
        cols[0].button("Stealth Mode")
        cols[1].button("Freq. Hop")
        st.button("Link-16 Data Sync")
    with st.expander("⚔️ Engagement & Defense"):
        st.button("Scramble Jets")
        st.button("SAM Lock-on")
        st.button("EW Jamming")
        st.button("Directed Energy")
        st.button("Point Defense")
    with st.expander("🛰️ Satellite Intelligence"):
        st.button("SAR Imaging")
        st.button("Thermal Scan")
        st.button("Signal Intel")
        st.button("Orbit Adjust")
        st.button("Deep Zoom")
    with st.expander("📋 System Management"):
        st.button("Airspace Lock")
        st.button("Warning Broadcast")
        st.button("Mission Log")
        st.button("AI Prognosis")
        st.error("SYSTEM RESET")
# --- عرض الخريطة والبيانات ---
col_map, col_info = st.columns([2, 1])
with col_map:
    st.subheader("🌐 High-Res Satellite Radar")
    m = folium.Map(location=[26.0, 48.0], zoom_start=7, 
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                   attr='Esri Satellite')
    for _, obj in data.iterrows():
        color = 'red' if obj['Type'] == 'HOSTILE' else 'blue'
        folium.CircleMarker(
            location=[obj['lat'], obj['lon']],
            radius=7, color=color, fill=True,
            popup=f"ID: {obj['callsign']} | Vel: {obj['vel']}m/s"
        ).add_to(m)
    st_folium(m, width="100%", height=500)
with col_info:
    st.subheader("⚠️ Intelligence Feed")
    st.dataframe(data[['callsign', 'Type', 'alt', 'vel']], height=300)
    # تنبيه الأهداف المعادية
    hostiles = data[data['Type'] == 'HOSTILE']
    if not hostiles.empty:
        st.warning(f"DETECTED: {len(hostiles)} Unidentified Targets!")
        for _, h in hostiles.iterrows():
            if st.button(f"Intercept {h['callsign']}"):
                st.snow()
                st.success(f"Interceptor vectoring to {h['callsign']}...")
# تحليل السرعة
fig = px.line(data, x='callsign', y='vel', title="Target Velocity Tracking", template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)
