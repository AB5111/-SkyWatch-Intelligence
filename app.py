import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import time
# --- 1. إعدادات الواجهة مع الأنيميشن الحركي للرادار ---
st.set_page_config(layout="wide", page_title="THE BEAST | RADAR MOTION", page_icon="👹")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    * { font-family: 'Orbitron', sans-serif; }
    .main { background-color: #000000; color: #00ffcc; }
    /* أنيميشن خط المسح الراداري */
    .radar-scanner {
        width: 300px; height: 300px;
        background: transparent;
        border-radius: 50%;
        border: 2px solid #00ffcc;
        position: relative;
        overflow: hidden;
        margin: auto;
    }
    .radar-scanner:before {
        content: "";
        display: block;
        position: absolute;
        top: 50%; left: 50%;
        width: 150px; height: 150px;
        background: linear-gradient(45deg, rgba(0,255,204,0.5) 0%, transparent 100%);
        transform-origin: top left;
        animation: radar-beam 2s linear infinite;
    }
    @keyframes radar-beam {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)
# --- 2. محرك جلب البيانات ---
@st.cache_data(ttl=15)
def get_beast_data():
    try:
        url = "https://opensky-network.org/api/states/all"
        params = {'lamin': 12.0, 'lamax': 35.0, 'lomin': 33.0, 'lomax': 60.0}
        res = requests.get(url, params=params, timeout=5).json()
        df = pd.DataFrame(res['states']).iloc[:, [1, 5, 6, 7, 9, 10]]
        df.columns = ['id', 'lon', 'lat', 'alt', 'vel', 'deg']
        df['Status'] = 'SECURE'
        return df.dropna()
    except:
        return pd.DataFrame(columns=['id', 'lon', 'lat', 'alt', 'vel', 'deg', 'Status'])
# --- 3. العرض المرئي للرادار المتحرك ---
st.markdown("<h1 style='text-align: center; color: #00ffcc;'>👹 BEAST MODE: ACTIVE SCANNING</h1>", unsafe_allow_html=True)
col_info, col_scanner = st.columns([2, 1])
with col_scanner:
    # هذا الكود يولد الدائرة المتحركة التي طلبتها
    st.markdown('<div class="radar-scanner"></div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>📡 SCANNING FREQUENCY: 9.4 GHz</p>", unsafe_allow_html=True)
with col_info:
    data = get_beast_data()
    st.metric("OBJECTS DETECTED", len(data), "LIVE FEED")
    st.info("System is tracing real-time vectors from ADS-B receivers.")
# --- 4. الخريطة والرادار التكتيكي ---
col_map, col_plot = st.columns([2, 1])
with col_map:
    m = folium.Map(location=[24.0, 45.0], zoom_start=5, tiles='CartoDB dark_matter')
    for _, r in data.head(50).iterrows():
        folium.CircleMarker([r['lat'], r['lon']], radius=5, color='#00ffcc', fill=True).add_to(m)
    st_folium(m, width="100%", height=400)
with col_plot:
    # رسم الرادار البياني الذي يتحرك مع تحديث البيانات
    fig = go.Figure(go.Scatterpolar(
        r=data['vel'].head(20), theta=data['deg'].head(20),
        mode='markers', marker=dict(color='#00ffcc', symbol='triangle-up', size=10)
    ))
    fig.update_layout(polar=dict(bgcolor="#000000"), paper_bgcolor="#000000", font_color="#00ffcc", height=400)
    st.plotly_chart(fig, use_container_width=True)

# التحديث التلقائي لمحاكاة الحركة
time.sleep(10)
st.rerun()
