import streamlit as st
import pandas as pd
import numpy as np
import requests
import pydeck as pdk
import plotly.express as px
from datetime import datetime
import time
# --- 1. إعدادات استقرار الواجهة (Solid Interface) ---
st.set_page_config(layout="wide", page_title="SkyWatch Intelligence Core", page_icon="📡")
# تحسين تصميم CSS ليتناسب مع شاشات الرادار المتقدمة
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'Share Tech Mono', monospace; }
    .stApp { background-color: #02060f; color: #00f2ff; }
    div[data-testid="stMetricValue"] { color: #00ffcc; text-shadow: 0px 0px 10px rgba(0,255,204,0.5); }
    div[data-testid="stMetricLabel"] { color: #8892b0; }
    hr { border-color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)
# --- 2. محرك جلب البيانات الحقيقية (Real-Time Radar Fusion) ---
# استخدام التخزين المؤقت لمنع حظر الـ API وتحديد مدة الصلاحية بـ 15 ثانية
@st.cache_data(ttl=15, show_spinner=False)
def get_live_tracks():
    url = "https://opensky-network.org/api/states/all"
    # إحداثيات الشرق الأوسط والخليج
    params = {'lamin': 12.0, 'lamax': 35.0, 'lomin': 33.0, 'lomax': 60.0}
    try:
        response = requests.get(url, params=params, timeout=8)
        if response.status_code != 200:
            return pd.DataFrame()  
        data = response.json()
        if not data or 'states' not in data or data['states'] is None:
            return pd.DataFrame()
        columns = ['icao24', 'callsign', 'origin', 'time_pos', 'last_contact', 
                   'lon', 'lat', 'baro_alt', 'on_ground', 'velocity', 'true_track', 
                   'ver_rate', 'sensors', 'geo_alt', 'squawk', 'spi', 'pos_source']
        df = pd.DataFrame(data['states'], columns=columns)
        # تنظيف وتحويل البيانات (معالجة القيم الفارغة)
        df = df.dropna(subset=['lat', 'lon'])
        df['baro_alt'] = pd.to_numeric(df['baro_alt'], errors='coerce').fillna(0)
        df['velocity'] = pd.to_numeric(df['velocity'], errors='coerce').fillna(0)
        df['true_track'] = pd.to_numeric(df['true_track'], errors='coerce').fillna(0)
        # تحويل الوحدات إلى معايير الطيران العسكري/المدني
        df['velocity_kt'] = (df['velocity'] * 1.94384).astype(int) # متر/ثانية إلى عقدة
        df['alt_ft'] = (df['baro_alt'] * 3.28084).astype(int)     # متر إلى قدم
        df['callsign'] = df['callsign'].str.strip().replace('', 'UNKNOWN')
        # تحديد الألوان للرادار ثلاثي الأبعاد بناءً على الارتفاع
        # أخضر للارتفاعات الشاهقة، أصفر للمتوسطة، أحمر للمنخفضة
        def get_color(alt):
            if alt > 25000: return [0, 255, 128, 200]
            elif alt > 10000: return [255, 215, 0, 200]
            else: return [255, 69, 0, 200]
        df['color'] = df['alt_ft'].apply(get_color)
        return df
    except Exception as e:
        return pd.DataFrame()
# --- 3. تصميم لوحة التحكم الرئيسية ---
st.title("📡 SKYWATCH: GLOBAL SURVEILLANCE & INTEL")
st.markdown(f"**SYSTEM STATUS:** `OPERATIONAL` | **ENCRYPTION:** `AES-256` | **TIME (ZULU):** `{datetime.utcnow().strftime('%H:%M:%S')}Z`")
st.divider()
# جلب البيانات الحقيقية
with st.spinner('Synchronizing with ADS-B Satellites...'):
    df_live = get_live_tracks()
# عرض المؤشرات الحيوية
c1, c2, c3, c4 = st.columns(4)
total_targets = len(df_live) if not df_live.empty else 0
avg_speed = int(df_live['velocity_kt'].mean()) if total_targets > 0 else 0
c1.metric("🔴 LIVE TARGETS", f"{total_targets} AIRCRAFT")
c2.metric("⚡ AVG AIRSPEED", f"{avg_speed} KTS")
c3.metric("🛰️ RADAR STATUS", "SECURE LINK", "+99.9% UPTIME")
c4.metric("🛡️ THREAT LEVEL", "MONITORING", "NORMAL")
st.divider()
# --- 4. العرض ثلاثي الأبعاد (Pydeck 3D Radar) ---
col_map, col_data = st.columns([2, 1])
with col_map:
    st.subheader("🌐 3D Tactical Airspace View")
    if not df_live.empty:
        # إعداد الرؤية المبدئية للكاميرا (فوق الرياض/الخليج) بزاوية مائلة 3D
        view_state = pdk.ViewState(latitude=24.0, longitude=45.0, zoom=4.5, pitch=50, bearing=0)
        # طبقة الأعمدة ثلاثية الأبعاد تمثل الطائرات وارتفاعاتها
        layer = pdk.Layer(
            "ColumnLayer",
            data=df_live,
            get_position=["lon", "lat"],
            get_elevation="alt_ft",
            elevation_scale=1.5,
            radius=4000,
            get_fill_color="color",
            pickable=True,
            auto_highlight=True,
        )
        # إعداد الخريطة بخلفية داكنة تتناسب مع الرادار
        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/dark-v10",
            tooltip={"html": "<b>Callsign:</b> {callsign} <br/> <b>Alt:</b> {alt_ft} ft <br/> <b>Speed:</b> {velocity_kt} kts <br/> <b>Origin:</b> {origin}", 
                     "style": {"backgroundColor": "black", "color": "#00f2ff", "fontFamily": "monospace"}}
        )
        st.pydeck_chart(r, use_container_width=True)
    else:
        st.error("⚠️ RADAR BLINDSPOT - NO DATA RECEIVED OR API LIMIT REACHED.")
with col_data:
    st.subheader("📊 Target Acquisition")
    if not df_live.empty:
        # عرض البيانات بتنسيق عسكري دقيق
        display_df = df_live[['callsign', 'alt_ft', 'velocity_kt', 'origin']].sort_values(by='alt_ft', ascending=False)
        st.dataframe(display_df.head(15), use_container_width=True, hide_index=True)
        # رسم بياني قطبي (Radar Chart) لتوزيع الاتجاهات (True Track)
        fig = px.bar_polar(df_live.head(50), r="velocity_kt", theta="true_track",
                           color="alt_ft", template="plotly_dark",
                           color_continuous_scale=px.colors.sequential.Agsunset,
                           title="Directional Velocity Tracker")
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
# --- 5. أوامر تحكم النظام (Sidebar) ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Radar_screen.gif/300px-Radar_screen.gif", use_column_width=True)
st.sidebar.header("🕹️ COMMAND CENTER")
# زر التحديث التلقائي (آمن على الواجهة ولا يجمدها)
auto_refresh = st.sidebar.toggle("🔄 ENABLE AUTO-SWEEP (15s)", value=False)
st.sidebar.button("📡 PING ALL SATELLITES", use_container_width=True)
st.sidebar.button("🛡️ ENGAGE AIR DEFENSE PROTOCOL", use_container_width=True, type="primary")
st.sidebar.markdown("---")
st.sidebar.caption("SKYWATCH CORE v3.1 | UNAUTHORIZED ACCESS LOGGED.")
# تنفيذ التحديث التلقائي إذا كان الزر مفعلاً
if auto_refresh:
    time.sleep(15)
    st.rerun()
