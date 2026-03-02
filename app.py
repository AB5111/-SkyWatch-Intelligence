import streamlit as st
import numpy as np
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import pandas as pd
import math, random, sqlite3, time
from datetime import datetime
# =========================================================
# 1. إعدادات الصفحة والتصميم التكتيكي
# =========================================================
st.set_page_config(layout="wide", page_title="SkyWatch Sovereign Platform v3.0")
# إضفاء الطابع العسكري الداكن (Dark Tactical Theme)
st.markdown("""
    <style>
    .stApp {background-color:#0b0f17; color:#00ff99;}
    .stMetric {background-color: #1a1f29; border-radius: 10px; padding: 10px; border: 1px solid #00ff99;}
    </style>
    """, unsafe_allow_html=True)
CITIES = {
    "Riyadh": (24.7136, 46.6753),
    "Jeddah": (21.4858, 39.1925),
    "Dammam": (26.4207, 50.0888)
}
PROTECTED_RADIUS = 2000  # بالمتر
NUM_DRONES = 5
# =========================================================
# 2. القائمة الجانبية للتحكم
# =========================================================
st.sidebar.title("🎮 Command & Control")
mode = st.sidebar.selectbox("Operation Mode", ["🛰️ Tactical", "💼 Executive"])
city_name = st.sidebar.selectbox("Select City", list(CITIES.keys()))
auto_refresh = st.sidebar.toggle("Live Radar Feed", True)
BASE_LAT, BASE_LON = CITIES[city_name]
# نقطة الهدف المحمي (مركز المدينة)
TARGET_LAT, TARGET_LON = BASE_LAT, BASE_LON
st.title("🛰️ SkyWatch: Sovereign Airspace Platform")
st.caption(f"Currently Monitoring: {city_name} Airspace")
# =========================================================
# 3. محاكي حركة الدرونات (State Management)
# =========================================================
if "drones" not in st.session_state:
    st.session_state.drones = []
    for i in range(NUM_DRONES):
        st.session_state.drones.append({
            "id": i+1,
            "lat": BASE_LAT + random.uniform(-0.05, 0.05),
            "lon": BASE_LON + random.uniform(-0.05, 0.05),
            "speed": random.randint(40, 120),
            "type": random.choice(["Fixed Wing", "Quadrotor"])
        })
# تحديث المواقع (حركة عشوائية باتجاه المركز)
for drone in st.session_state.drones:
    drone["lat"] += (TARGET_LAT - drone["lat"]) * 0.01 + random.uniform(-0.001, 0.001)
    drone["lon"] += (TARGET_LON - drone["lon"]) * 0.01 + random.uniform(-0.001, 0.001)
# =========================================================
# 4. لوحة المؤشرات الحيوية
# =========================================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tracked Objects", len(st.session_state.drones))
col2.metric("Radar Range", "50 KM")
col3.metric("System Load", "24%", delta="-2%")
col4.metric("Status", "SECURE", delta="Normal")
# =========================================================
# 5. شاشة الرادار (Radar Sweep Visualization)
# =========================================================
st.subheader("🎯 Active Radar Sweep")
fig = go.Figure()
# رسم دوائر الرادار
for r in [0.2, 0.4, 0.6, 0.8, 1.0]:
    fig.add_trace(go.Scatterpolar(r=[r]*360, theta=list(range(360)), mode='lines', 
                                 line=dict(color="#00ff99", width=1, dash='dot'), showlegend=False))
# إضافة الأهداف على الرادار
for drone in st.session_state.drones:
    dist = math.sqrt((drone['lat']-BASE_LAT)**2 + (drone['lon']-BASE_LON)**2) * 10
    fig.add_trace(go.Scatterpolar(r=[min(dist, 1)], theta=[random.randint(0, 360)],
                                 mode='markers', marker=dict(size=12, color='red', symbol='triangle-up'),
                                 name=f"Target {drone['id']}"))
fig.update_layout(polar=dict(bgcolor="#0b0f17", radialaxis=dict(visible=False), angularaxis=dict(showticklabels=False)),
                  margin=dict(l=0, r=0, t=30, b=0), height=400)
st.plotly_chart(fig, use_container_width=True)
# =========================================================
# 6. الخريطة العملياتية (Interactive Map)
# =========================================================
st.subheader("🗺️ Operational Geospatial View")
m = folium.Map(location=[BASE_LAT, BASE_LON], zoom_start=12, tiles="CartoDB dark_matter")
# منطقة الحماية
folium.Circle(location=[TARGET_LAT, TARGET_LON], radius=PROTECTED_RADIUS, 
              color="red", fill=True, fill_opacity=0.2, popup="Restricted Zone").add_to(m)
# رسم الدرونات على الخريطة
for drone in st.session_state.drones:
    folium.Marker([drone["lat"], drone["lon"]], 
                  icon=folium.Icon(color="red", icon="plane"),
                  tooltip=f"Drone ID: {drone['id']}").add_to(m)
st_folium(m, width="100%", height=500)
# =========================================================
# 7. جدول البيانات الاستخباراتي
# =========================================================
st.subheader("📋 Intelligence Data Feed")
df = pd.DataFrame(st.session_state.drones)
df['Status'] = df['speed'].apply(lambda x: "⚠️ HIGH SPEED" if x > 100 else "✅ STEADY")
st.table(df[['id', 'type', 'speed', 'Status']])
# =========================================================
# 8. التحديث التلقائي
# =========================================================
if auto_refresh:
    time.sleep(2)
    st.rerun()
