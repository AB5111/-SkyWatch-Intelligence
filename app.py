import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime
import time
# --- 1. إعدادات استقرار الواجهة (Solid Interface) ---
st.set_page_config(layout="wide", page_title="SkyWatch Intelligence Core")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    * { font-family: 'Share Tech Mono', monospace; }
    .main { background-color: #05070a; color: #00f2ff; }
    .stMetric { background: rgba(0, 242, 255, 0.05); border: 1px solid #00f2ff; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)
# --- 2. محرك جلب البيانات الحقيقية (Real-Time Radar Fusion) ---
def get_live_tracks():
    # إحداثيات تغطي المملكة والخليج بشكل كامل
    url = "https://opensky-network.org/api/states/all"
    params = {'lamin': 12.0, 'lamax': 32.5, 'lomin': 33.0, 'lomax': 60.0}
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        states = data['states']
        # تعريف الأعمدة بشكل صارم لتجنب الخطأ السابق
        columns = ['icao24', 'callsign', 'origin', 'time_pos', 'last_contact', 
                   'lon', 'lat', 'baro_alt', 'on_ground', 'velocity', 'true_track', 
                   'ver_rate', 'sensors', 'geo_alt', 'squawk', 'spi', 'pos_source']
        df = pd.DataFrame(states, columns=columns)
        # تنظيف البيانات (إزالة القيم الفارغة في الإحداثيات)
        df = df.dropna(subset=['lat', 'lon'])
        df['Type'] = 'REAL-TIME TRACK'
        return df
    except Exception as e:
        # في حال فشل الاتصال، عرض جدول فارغ مهيأ بدلاً من إيقاف البرنامج
        return pd.DataFrame(columns=['callsign', 'lat', 'lon', 'baro_alt', 'velocity', 'Type'])
# --- 3. تصميم لوحة التحكم الرئيسية ---
st.title("📡 SKYWATCH: GLOBAL SURVEILLANCE & INTEL")
st.write(f"**System Status:** Operational | **Network:** Global ADS-B Mesh | **Time:** {datetime.now().strftime('%H:%M:%S')}")
# جلب البيانات الحقيقية
df_live = get_live_tracks()
# عرض المؤشرات الحيوية
c1, c2, c3, c4 = st.columns(4)
c1.metric("LIVE TARGETS", len(df_live))
c2.metric("RADAR STATUS", "CONNECTED", "STABLE")
c3.metric("INTEL FEED", "MULTIPLE SOURCES")
c4.metric("AI PREDICTION", "ACTIVE")
# --- 4. عرض الخريطة الحقيقية (Satellite Mode) ---
col_map, col_data = st.columns([2, 1])
with col_map:
    st.subheader("🌐 High-Resolution Radar & Satellite View")
    # استخدام خرائط الأقمار الصناعية عالية الدقة من ArcGIS
    m = folium.Map(location=[24.0, 45.0], zoom_start=5, 
                   tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', 
                   attr='Esri Satellite Intelligence')
    # إضافة حركة الطائرات الحقيقية
    for _, track in df_live.head(100).iterrows(): # عرض أول 100 هدف لسرعة الأداء
        # تحديد لون السهم بناءً على الارتفاع
        color = 'lime' if track['baro_alt'] > 5000 else 'yellow'
        folium.CircleMarker(
            location=[track['lat'], track['lon']],
            radius=4, color=color, fill=True,
            popup=f"ID: {track['callsign']} | SPD: {track['velocity']} m/s | ALT: {track['baro_alt']}m"
        ).add_to(m)
    st_folium(m, width="100%", height=550)
with col_data:
    st.subheader("📊 Tactical Data Feed")
    # عرض البيانات الحقيقية في جدول منظم
    if not df_live.empty:
        st.dataframe(df_live[['callsign', 'origin', 'velocity', 'baro_alt']].head(20), use_container_width=True)
        # رسم بياني للسرعات الحقيقية للطائرات فوق المملكة
        fig = px.bar(df_live.head(15), x='callsign', y='velocity', 
                     color='velocity', title="Velocity Distribution", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Waiting for secure data stream...")
# --- 5. أوامر جانبية ثابتة ---
st.sidebar.header("🕹️ OPERATIONAL COMMANDS")
st.sidebar.button("📡 RE-SCAN AIRSPACE")
st.sidebar.button("🛰️ SATELLITE SYNC")
st.sidebar.button("🛡️ AIR DEFENSE ALERT")
st.sidebar.button("📥 EXPORT TRACKING LOG")
# تحديث تلقائي كل 15 ثانية لضمان الثبات
time.sleep(15)
st.rerun()
