import streamlit as st
import pandas as pd
import numpy as np
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime

# --- إعدادات النظام المتقدمة ---
st.set_page_config(layout="wide", page_title="SkyWatch Command & Control (C2)")

# تصغير الهوامش لإعطاء مظهر الشاشات العسكرية
st.markdown("""
    <style>
    .reportview-container .main .block-container{ padding-top: 1rem; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #262730; color: white; }
    .stButton>button:hover { background-color: #ff4b4b; border: 1px solid white; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- محرك الرادارات المدمج ---
def get_integrated_radar():
    # 1. رادار ADS-B (حقيقي)
    url = "https://opensky-network.org/api/states/all"
    params = {'lamin': 24.0, 'lamax': 27.0, 'lomin': 45.0, 'lomax': 51.0} # منطقة الرياض والشرقية
    try:
        res = requests.get(url, params=params, timeout=3).json()
        real_df = pd.DataFrame(res['states'], columns=['id','callsign','origin','time','contact','lon','lat','alt','ground','vel','deg','ver','sensors','geo','sq','spi','src'])
        real_df['type'] = 'CIVILIAN'
    except:
        real_df = pd.DataFrame()

    # 2. رادار الكشف السلبي (محاكاة للأهداف المتسللة/درونات)
    stealth_data = {
        'id': ['UFO-99', 'DRN-02'], 'callsign': ['UNKNOWN', 'GHOST_01'], 
        'lat': [26.3, 24.8], 'lon': [50.1, 46.5], 'alt': [150, 450], 
        'vel': [120, 310], 'type': 'STEALTH/HOSTILE'
    }
    stealth_df = pd.DataFrame(stealth_data)
    
    return pd.concat([real_df, stealth_df], fill_value=0)

# --- واجهة القيادة ---
st.title("🛡️ SkyWatch C2: Integrated Air Defense Command")

radar_data = get_integrated_radar()

# --- القائمة الجانبية: لوحة الأوامر (20+ أمر) ---
with st.sidebar:
    st.header("🎮 Tactical Command Board")
    
    with st.expander("📡 إدارة الرادارات (5 أوامر)", expanded=True):
        if st.button("Full Sweep (إرسال نبضة كاملة)"): st.toast("جاري المسح الكهرومغناطيسي...")
        st.button("Toggle Stealth Detection (كشف التسلل)")
        st.button("Jamming Resistance (مقاومة التشويش)")
        st.button("SPS Optimization (تحسين دقة القمر)")
        st.button("Link-16 Data Sharing (مشاركة البيانات)")

    with st.expander("⚔️ إجراءات الاشتباك (5 أوامر)"):
        st.button("Scramble Interceptors (إقلاع اعتراض طوارئ)")
        st.button("Electronic Warfare (حرب إلكترونية)")
        st.button("Target Lock-On (تثبيت الهدف)")
        st.button("Laser Dazzler (إعماء بصري)")
        st.button("EMP Burst (نبضة كهرومغناطيسية)")

    with st.expander("🛰️ تتبع الأقمار (5 أوامر)"):
        st.button("Satellite Re-entry Tracking")
        st.button("Optical Zoom (Satellite-5)")
        st.button("Thermal Overlay (مسح حراري)")
        st.button("SAR Imaging (رادار الفتحة الاصطناعية)")
        st.button("GPS Anti-Spoofing")

    with st.expander("📋 إدارة النظام (5 أوامر)"):
        st.button("Broadcast Warning (بث تحذير)")
        st.button("Airspace Lockdown (إغلاق المجال)")
        st.button("Export Blackbox Logs")
        st.button("AI Threat Prediction")
        st.button("System Self-Destruct (Emergency)")

# --- العرض المركزي ---
c1, c2 = st.columns([3, 1])

with c1:
    # خريطة القمر الصناعي مع طبقة رادارية
    m = folium.Map(location=[25.5, 48.5], zoom_start=7, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri')
    for _, obj in radar_data.iterrows():
        color = 'red' if obj['type'] == 'STEALTH/HOSTILE' else 'cyan'
        folium.Marker(
            [obj['lat'], obj['lon']], 
            icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/575/575440.png", icon_size=(30,30)) if color=='red' else None,
            popup=f"ID: {obj['id']} | Type: {obj['type']}"
        ).add_to(m)
    
    st_folium(m, width="100%", height=600)

with c2:
    st.subheader("⚠️ Alerts & AI Analysis")
    for _, obj in radar_data[radar_data['type'] == 'STEALTH/HOSTILE'].iterrows():
        st.error(f"ALERT: {obj['id']} detected at {obj['alt']}m!")
        st.write(f"Confidence: 98% | Vector: South-East")
        if st.button(f"Intercept {obj['id']}"):
            st.warning(f"Interceptor dispatched to {obj['lat']}, {obj['lon']}")

    st.markdown("---")
    st.info("AI Prediction: Unidentified drone likely heading to industrial zone.")

# --- الرسوم البيانية ---
st.subheader("📈 Airspace Analytics")
fig = px.bar(radar_data.head(10), x='id', y='vel', color='type', template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)
