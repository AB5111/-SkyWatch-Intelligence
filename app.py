# app_advanced.py
"""
SkyWatch AI - Advanced Simulated Version
Features: Kalman tracking, sensor fusion (simulated), anomaly detection,
explainable scoring, audit log, modular structure, unit-testable components.
All actions are simulation-only and require human review for any real-world use.
"""
import streamlit as st
import pandas as pd
import numpy as np
import math
import random
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import plotly.express as px
import logging
import json
from copy import deepcopy
# ---------- Configuration ----------
CONFIG = {
    "n_initial_drones": 8,
    "max_history": 120,
    "predict_seconds": 30,
    "fusion_weights": {"gps": 0.7, "radar": 0.3},
    "anomaly_threshold_mahalanobis": 3.5,
    "kalman_process_var": 1e-2,
    "kalman_measure_var": 1e-1,
    "max_decision_log": 1000
}
# ---------- Utilities ----------
def now_utc():
    return datetime.utcnow()
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))
# ---------- Simple Kalman Filter (2D position + velocity) ----------
class SimpleKalman2D:
    def __init__(self, dt=1.0, process_var=1e-2, measure_var=1e-1):
        # state: [lat, lon, v_lat, v_lon]
        self.dt = dt
        self.x = np.zeros((4,1))
        self.P = np.eye(4) * 1.0
        # state transition
        self.F = np.array([[1,0,dt,0],
                           [0,1,0,dt],
                           [0,0,1,0],
                           [0,0,0,1]])
        # measurement: lat, lon
        self.H = np.array([[1,0,0,0],
                           [0,1,0,0]])
        self.Q = np.eye(4) * process_var
        self.R = np.eye(2) * measure_var
    def init_state(self, lat, lon, speed_kmh, heading_deg):
        # approximate velocity components (deg/sec) using small-angle approx
        # convert speed km/h to deg/sec approx: 1 deg lat ~ 111 km
        v_km_s = speed_kmh / 3600.0
        v_lat = v_km_s / 111.0 * math.cos(math.radians(heading_deg))
        v_lon = v_km_s / (111.0 * math.cos(math.radians(lat))) * math.sin(math.radians(heading_deg))
        self.x = np.array([[lat],[lon],[v_lat],[v_lon]])
        self.P = np.eye(4) * 0.5
    def predict(self, dt=None):
        if dt is None:
            dt = self.dt
        F = np.array([[1,0,dt,0],
                      [0,1,0,dt],
                      [0,0,1,0],
                      [0,0,0,1]])
        self.F = F
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q
        return self.x.copy()
    def update(self, lat_meas, lon_meas):
        z = np.array([[lat_meas],[lon_meas]])
        y = z - (self.H @ self.x)
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P
        return self.x.copy()
    def current_state(self):
        return self.x.flatten().tolist()
# ---------- Anomaly detection (Mahalanobis on selected features) ----------
def mahalanobis_distance(x, data_cov_inv, mean_vec):
    delta = x - mean_vec
    return float(np.sqrt(delta.T @ data_cov_inv @ delta))
def compute_mahalanobis_for_df(df_features):
    # df_features: numpy array shape (n, k)
    mean = np.mean(df_features, axis=0)
    cov = np.cov(df_features, rowvar=False)
    # regularize
    cov += np.eye(cov.shape[0]) * 1e-6
    cov_inv = np.linalg.inv(cov)
    dists = [mahalanobis_distance(row, cov_inv, mean) for row in df_features]
    return np.array(dists), mean, cov_inv
# ---------- Simulation initialization ----------
CITIES = {"Riyadh": [24.7136, 46.6753], "Jeddah": [21.4858, 39.1925], "Dammam": [26.4207, 50.0888]}
if 'city' not in st.session_state:
    st.session_state.city = "Riyadh"
center = CITIES[st.session_state.city]
def init_drones_df(center, n=CONFIG["n_initial_drones"]):
    rows = []
    for i in range(n):
        lat = center[0] + random.uniform(-0.04, 0.04)
        lon = center[1] + random.uniform(-0.04, 0.04)
        speed = random.uniform(10, 160)
        heading = random.uniform(0, 360)
        alt = random.uniform(50, 1200)
        rows.append({
            "id": f"Drone-{100+i}",
            "lat": lat,
            "lon": lon,
            "speed": speed,
            "heading": heading,
            "alt": alt,
            "last_update": now_utc()
        })
    return pd.DataFrame(rows)
if 'drones' not in st.session_state:
    st.session_state.drones = init_drones_df(center)
    st.session_state.kalman = {}
    st.session_state.tracks = {}
    st.session_state.decision_log = []
    st.session_state.audit_log = []
    # init kalman per drone
    for _, r in st.session_state.drones.iterrows():
        k = SimpleKalman2D(dt=1.0, process_var=CONFIG["kalman_process_var"], measure_var=CONFIG["kalman_measure_var"])
        k.init_state(r['lat'], r['lon'], r['speed'], r['heading'])
        st.session_state.kalman[r['id']] = k
        st.session_state.tracks[r['id']] = [(r['lat'], r['lon'], r['last_update'])]
# ---------- Sensor fusion (simulated) ----------
def fused_measurement(gps_lat, gps_lon, radar_lat, radar_lon, weights):
    lat = gps_lat * weights['gps'] + radar_lat * weights['radar']
    lon = gps_lon * weights['gps'] + radar_lon * weights['radar']
    return lat, lon
# ---------- Threat scoring (explainable) ----------
def explainable_score(features, weights):
    # features: dict of feature_name -> value (normalized expected ranges)
    # weights: dict of feature_name -> weight
    score = 0.0
    contributions = {}
    for k,v in features.items():
        w = weights.get(k, 0.0)
        contrib = w * v
        contributions[k] = contrib
        score += contrib
    return score, contributions
# ---------- Main simulation step ----------
def simulate_step(dt_seconds=3):
    now = now_utc()
    # simulate radar noise positions
    for idx, row in st.session_state.drones.iterrows():
        # simulate small random changes
        speed = max(0.0, row['speed'] + random.uniform(-6,6))
        heading = (row['heading'] + random.uniform(-10,10)) % 360
        alt = max(20.0, row['alt'] + random.uniform(-20,20))
        # compute new GPS position (simple move_point using haversine approx)
        # convert speed km/h to km per dt
        dist_km = speed * dt_seconds / 3600.0
        bearing = math.radians(heading)
        lat1 = math.radians(row['lat'])
        lon1 = math.radians(row['lon'])
        R = 6371.0
        lat2 = math.asin(math.sin(lat1)*math.cos(dist_km/R) + math.cos(lat1)*math.sin(dist_km/R)*math.cos(bearing))
        lon2 = lon1 + math.atan2(math.sin(bearing)*math.sin(dist_km/R)*math.cos(lat1),
                                 math.cos(dist_km/R)-math.sin(lat1)*math.sin(lat2))
        gps_lat = math.degrees(lat2) + random.uniform(-1e-4, 1e-4)  # GPS noise
        gps_lon = math.degrees(lon2) + random.uniform(-1e-4, 1e-4)
        # radar simulated with larger noise
        radar_lat = math.degrees(lat2) + random.uniform(-3e-4, 3e-4)
        radar_lon = math.degrees(lon2) + random.uniform(-3e-4, 3e-4)
        # fusion
        fused_lat, fused_lon = fused_measurement(gps_lat, gps_lon, radar_lat, radar_lon, CONFIG['fusion_weights'])
        # Kalman predict/update
        kf = st.session_state.kalman[row['id']]
        kf.predict(dt=dt_seconds)
        kf.update(fused_lat, fused_lon)
        state = kf.current_state()
        # update dataframe
        st.session_state.drones.at[idx, 'lat'] = state[0]
        st.session_state.drones.at[idx, 'lon'] = state[1]
        # approximate speed from velocity components
        v_lat, v_lon = state[2], state[3]
        # convert back to km/h approx
        speed_est = math.sqrt((v_lat*111.0)**2 + (v_lon*111.0*math.cos(math.radians(state[0])))**2) * 3600.0
        st.session_state.drones.at[idx, 'speed'] = speed_est
        st.session_state.drones.at[idx, 'heading'] = heading
        st.session_state.drones.at[idx, 'alt'] = alt
        st.session_state.drones.at[idx, 'last_update'] = now
        # append track
        tr = st.session_state.tracks.setdefault(row['id'], [])
        tr.append((state[0], state[1], now))
        if len(tr) > CONFIG['max_history']:
            st.session_state.tracks[row['id']] = tr[-CONFIG['max_history']:]
    # compute features matrix for anomaly detection
    df = st.session_state.drones.copy()
    features = df[['speed','alt']].to_numpy()
    # add distance to center as feature
    df['distance_km'] = df.apply(lambda r: haversine_km(r['lat'], r['lon'], center[0], center[1]), axis=1)
    features = np.hstack([features, df[['distance_km']].to_numpy()])
    dists, mean_vec, cov_inv = compute_mahalanobis_for_df(features)
    # scoring weights (normalized)
    score_weights = {"proximity": 0.5, "speed": 0.25, "altitude": 0.15, "behavior": 0.1}
    # behavior score: simple recent heading/speed variance
    for i, (idx, row) in enumerate(st.session_state.drones.iterrows()):
        behavior = 0.0
        tr = st.session_state.tracks.get(row['id'], [])
        if len(tr) >= 4:
            # compute heading variance proxy via successive vectors
            vecs = []
            for a,b,_ in tr[-4:]:
                vecs.append((a,b))
            # crude variance
            lats = [v[0] for v in vecs]
            lons = [v[1] for v in vecs]
            behavior = float(np.std(lats) + np.std(lons))
            behavior = min(1.0, behavior * 1000.0)  # normalize
        # normalized features for explainable scoring
        proximity_norm = max(0.0, 1.0 - (row['distance_km'] / 10.0))  # within 10km -> high
        speed_norm = min(1.0, row['speed'] / 300.0)
        alt_norm = max(0.0, 1.0 - (row['alt'] / 2000.0))
        feat_dict = {"proximity": proximity_norm, "speed": speed_norm, "altitude": alt_norm, "behavior": behavior}
        score, contribs = explainable_score(feat_dict, score_weights)
        # anomaly flag
        is_anomaly = dists[i] > CONFIG['anomaly_threshold_mahalanobis']
        # label
        label = "🔴 CRITICAL" if (score > 0.7 and is_anomaly) else ("🟠 SUSPICIOUS" if score > 0.45 else "🟢 CLEAR")
        # confidence heuristic
        confidence = min(0.99, 0.3 + 0.15 * len(tr))
        # update
        st.session_state.drones.at[idx, 'risk_score'] = round(score*100,1)
        st.session_state.drones.at[idx, 'status'] = label
        st.session_state.drones.at[idx, 'confidence'] = round(confidence,2)
        st.session_state.drones.at[idx, 'mahalanobis'] = round(float(dists[i]),3)
        st.session_state.drones.at[idx, 'contribs'] = json.dumps(contribs)
        # decision log entry
        st.session_state.decision_log.insert(0, {
            "time": now.isoformat(),
            "id": row['id'],
            "label": label,
            "score": round(score*100,1),
            "confidence": round(confidence,2),
            "mahalanobis": round(float(dists[i]),3)
        })
    # trim logs
    st.session_state.decision_log = st.session_state.decision_log[:CONFIG['max_decision_log']]
# ---------- Streamlit UI ----------
st.set_page_config(layout="wide", page_title="SkyWatch AI - Ultimate Simulated")
st.title("SkyWatch AI | Ultimate Simulated Edition (Human-in-Loop)")
# Sidebar controls
with st.sidebar:
    st.header("Controls")
    city_sel = st.selectbox("Active Surveillance Zone", list(CITIES.keys()), index=list(CITIES.keys()).index(st.session_state.city))
    st.session_state.city = city_sel
    update_rate = st.slider("Update rate (s)", 1, 10, 3)
    auto_refresh = st.checkbox("Auto refresh", value=True)
    if st.button("Reset Simulation"):
        st.session_state.clear()
        st.experimental_rerun()
# run step if needed
if 'last_tick' not in st.session_state:
    st.session_state.last_tick = now_utc() - timedelta(seconds=update_rate+1)
if auto_refresh and (now_utc() - st.session_state.last_tick).total_seconds() >= update_rate:
    simulate_step(dt_seconds=update_rate)
    st.session_state.last_tick = now_utc()
# Layout: map + side panel
c1, c2 = st.columns([2,1])
with c1:
    st.subheader("Tactical Map (Simulated)")
    m = folium.Map(location=CITIES[st.session_state.city], zoom_start=12, tiles="CartoDB dark_matter")
    folium.Circle(location=CITIES[st.session_state.city], radius=2000, color='cyan', fill=True, fill_opacity=0.05).add_to(m)
    for _, r in st.session_state.drones.iterrows():
        tr = st.session_state.tracks.get(r['id'], [])
        coords = [(p[0], p[1]) for p in tr]
        color = 'red' if "CRITICAL" in r['status'] else ('orange' if "SUSPICIOUS" in r['status'] else 'lightblue')
        if len(coords) > 1:
            folium.PolyLine(coords, color=color, weight=2, opacity=0.7).add_to(m)
        pred_kf = deepcopy(st.session_state.kalman[r['id']])
        pred_kf.predict(dt=CONFIG['predict_seconds'])
        pred_state = pred_kf.current_state()
        folium.CircleMarker(location=(pred_state[0], pred_state[1]), radius=3, color=color, fill=True,
                            popup=f"Predicted (s={CONFIG['predict_seconds']}) {r['id']}").add_to(m)
        popup = folium.Popup(f"<b>{r['id']}</b><br>Status: {r['status']}<br>Score: {r['risk_score']}<br>Conf: {r['confidence']}<br>Mah: {r['mahalanobis']}", max_width=300)
        folium.Marker([r['lat'], r['lon']], popup=popup, icon=folium.Icon(color='red' if color=='red' else 'blue')).add_to(m)
    st_folium(m, width=900, height=520)
with c2:
    st.subheader("Decision & Audit")
    df_log = pd.DataFrame(st.session_state.decision_log)
    if not df_log.empty:
        st.dataframe(df_log.head(200), use_container_width=True)
    else:
        st.write("No decisions yet.")
    st.markdown("---")
    st.subheader("Aircraft Summary")
    st.dataframe(st.session_state.drones[['id','status','risk_score','confidence','mahalanobis','speed','alt','distance_km']].sort_values('risk_score', ascending=False), use_container_width=True)
# Human review actions
st.subheader("Human Review Actions (Simulation)")
sel = st.selectbox("Select drone", options=list(st.session_state.drones['id']))
act = st.radio("Action", options=["No action", "Flag for review", "Mark CLEAR", "Mark SUSPICIOUS", "Escalate to CRITICAL"])
if st.button("Apply action"):
    idx = st.session_state.drones.index[st.session_state.drones['id'] == sel][0]
    prev = st.session_state.drones.at[idx, 'status']
    if act != "No action":
        st.session_state.drones.at[idx, 'status'] = f"👤 HUMAN: {act}"
        st.session_state.audit_log.insert(0, {
            "time": now_utc().isoformat(),
            "actor": "operator_sim",
            "id": sel,
            "action": act,
            "prev_status": prev
        })
        st.success(f"Action applied to {sel}")
# Risk overview chart
st.subheader("Risk Overview")
fig = px.bar(st.session_state.drones.sort_values('risk_score', ascending=False), x='id', y='risk_score', color='risk_score', color_continuous_scale='Reds', template='plotly_dark')
st.plotly_chart(fig, use_container_width=True)
# Explainability panel for selected drone
st.subheader("Explainability")
sel2 = st.selectbox("Select drone for explainability", options=list(st.session_state.drones['id']), key="explain_sel")
row = st.session_state.drones[st.session_state.drones['id']==sel2].iloc[0]
contribs = json.loads(row['contribs']) if 'contribs' in row and row['contribs'] else {}
st.write("Feature contributions (normalized):")
for k,v in contribs.items():
    st.write(f"- **{k}** — {v:.3f}")
st.markdown("---")
st.markdown("**Important:** Simulation-only. Any operational integration requires formal approvals, safety checks, and human-in-the-loop gating.")
# ---------- End of app ----------
