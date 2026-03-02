import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from datetime import datetime
import time
import base64
# --- 1. إعدادات الواجهة والأنيميشن الصوتي ---
st.set_page_config(layout="wide", page_title="THE BEAST | SONIC RADAR", page_icon="👹")
def add_radar_sound():
    # هذا الكود يضيف صوت "رادار" مخفي يعمل بشكل متكرر مع الأنيميشن
    # يمكنك استبدال الرابط برابط ملف صواري (ping) خاص بك
    sound_url = "https://www.soundjay.com/buttons/beep-07.mp3" 
    st.markdown(
        f"""
        <audio autoplay loop>
            <source src="{sound_url}" type="audio/mp3">
        </audio>
        """,
        unsafe_allow_html=True
    )
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    * { font-family: 'Orbitron', sans-serif; }
    .main { background-color: #000000; color: #00ffcc; }
    /* أنيميشن الرادار مع نبضة ضوئية متوافقة مع الصوت */
    .radar-container {
        position: relative;
        width: 300px; height: 300px;
        margin: auto;
        border: 2px solid #00ffcc;
        border-radius: 50%;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.2);
    }
    .radar-beam {
        position: absolute;
        width: 50%; height: 50%;
        top: 0; left: 50%;
        background: linear-gradient(90deg, rgba(0,255,204,0.5) 0%, transparent 100%);
        transform-origin: bottom left;
        animation: rotate-beam 2s linear infinite;
    }
    @keyframes rotate-beam {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    /* نبضة التنبيه عند كل لفة */
    .radar-pulse {
        position: absolute;
        width: 100%; height: 100%;
        border-radius: 50%;
        animation: radar-pulse-anim 2s ease-out infinite;
        border: 2px solid #00ffcc;
        opacity: 0;
    }
    @keyframes radar-pulse-anim {
        0% { transform: scale(0.1); opacity: 1; }
        100% { transform: scale(1.2); opacity: 0; }
    }
    </style>
    """, unsafe_allow_html=True)
# تفعيل الصوت
add_radar_sound()

# --- 2. محرك البيانات ---
@st.cache_data(ttl=15)
def get_beast_data():
    try:
        url = "https://opensky-network.org/api/states/all"
        params = {'lamin': 12.0, 'lamax': 35.0, 'lomin': 33.0, 'lomax': 60.0}
        res = requests.get(url, params=params, timeout=5).json()
        df = pd.DataFrame(res['states']).iloc[:, [1, 5, 6, 7, 9, 10]]
        df.columns = ['id', 'lon', 'lat', 'alt', 'vel', 'deg']
        return df.dropna()
    except:
        return pd.DataFrame(columns=['id', 'lon', 'lat', 'alt', 'vel', 'deg'])
# --- 3. العرض المرئي ---
st.markdown("<h1 style='text-align: center; color: #00ffcc; text-shadow: 0 0 15px #00ffcc;'>👹 SONIC BEAST: ACTIVE ENGAGEMENT</h1>", unsafe_allow_html=True)
col_info, col_scanner = st.columns([1, 1])
with col_scanner:
    st.markdown("""
        <div class="radar-container">
            <div class="radar-beam"></div>
            <div class="radar-pulse"></div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-top: 10px;'>🔊 AUDIO PING: SYNCHRONIZED</p>", unsafe_allow_html=True)
with col_info:
    data = get_beast_data()
    st.metric("TARGETS ACQUIRED", len(data))
    st.warning("SYSTEM NOTE: Audio feedback is active. Ensure browser volume is ON.")
# --- 4. الخريطة والرادار التكتيكي ---
c1, c2 = st.columns([2, 1])
with c1:
    m = folium.Map(location=[24.0, 45.0], zoom_start=5, tiles='CartoDB dark_matter')
    for _, r in data.head(30).iterrows():
        folium.CircleMarker([r['lat'], r['lon']], radius=4, color='#00ffcc', fill=True).add_to(m)
    st_folium(m, width="100%", height=450)
with c2:
    fig = go.Figure(go.Scatterpolar(
        r=data['vel'].head(15), theta=data['deg'].head(15),
        mode='markers', marker=dict(color='#ff0000', size=12, symbol='x')
    ))
    fig.update_layout(polar=dict(bgcolor="#000000"), paper_bgcolor="#000000", font_color="#00ffcc", height=450)
    st.plotly_chart(fig, use_container_width=True)

# تحديث تلقائي
time.sleep(10)
st.rerun()
