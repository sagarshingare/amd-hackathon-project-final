import streamlit as st
import requests
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
from pathlib import Path
import os

BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(layout="wide", page_title="Logistics VRP Demo")

st.title("Agentic AI — Logistics Optimization (Demo)")

# Data loading: prefer Kaggle/local file, otherwise ask backend to generate
data_file = Path("data/deliveries.csv")
if data_file.exists():
    df = pd.read_csv(data_file)
    st.success(f"Loaded local data: {data_file} ({len(df)} rows)")
else:
    st.info("No local data/deliveries.csv found — using backend generator on optimize.")
    df = None

col1, col2 = st.columns([1, 2])
with col1:
    st.header("Controls")
    num_vehicles = st.number_input("Num vehicles", value=3, min_value=1, max_value=10)
    fuel_price = st.number_input("Fuel price (per unit distance)", value=1.0, step=0.1)
    run_opt = st.button("Run initial optimization")
    run_sim = st.button("Simulate disruption (traffic / fuel spike)")
    show_map = st.checkbox("Show map (Folium)", value=True)

with col2:
    st.header("Dataset preview")
    if df is not None:
        st.dataframe(df.head())
    else:
        st.markdown("No local dataset found. Click 'Run initial optimization' to generate synthetic demo data.")

def plot_routes_on_map(routes_before, routes_after=None, center=None):
    if center is None:
        # compute center
        all_coords = []
        for r in (routes_before or []) + (routes_after or []):
            for p in r.get("coords", []):
                all_coords.append(p)
        if not all_coords:
                center = [0.0, 0.0]
        else:
                lat = float(np.mean([c[0] for c in all_coords]))
                lon = float(np.mean([c[1] for c in all_coords]))
                center = [lat, lon]

    m = folium.Map(location=center, zoom_start=12)
    # draw before routes (blue)
    for i, r in enumerate(routes_before or []):
        coords = r.get("coords", [])
        if not coords: continue
        clean_coords = [[float(pt[0]), float(pt[1])] for pt in coords]
        folium.PolyLine(locations=clean_coords, color="blue", weight=4, opacity=0.7, tooltip=f"Before - Vehicle {i}").add_to(m)
        folium.Marker(location=clean_coords[0], icon=folium.Icon(color="green"), popup=f"Start V{i}").add_to(m)
    # draw after routes (red)
    for i, r in enumerate(routes_after or []):
        coords = r.get("coords", [])
        if not coords: continue
        clean_coords = [[float(pt[0]), float(pt[1])] for pt in coords]
        folium.PolyLine(locations=clean_coords, color="red", weight=4, opacity=0.7, tooltip=f"After - Vehicle {i}").add_to(m)
        folium.Marker(location=clean_coords[0], icon=folium.Icon(color="darkred"), popup=f"Start After V{i}").add_to(m)
    return m

def show_cost_charts(cost_before, cost_after):
    labels = ["Before", "After"]
    vals = [cost_before or 0, cost_after or 0]
    fig, ax = plt.subplots()
    ax.bar(labels, vals, color=["blue", "red"])
    ax.set_ylabel("Total cost")
    ax.set_title("Cost before vs after")
    st.pyplot(fig)

# handle initial optimize
if run_opt:
    payload = {"num_vehicles": int(num_vehicles), "fuel_price": float(fuel_price)}
    try:
        resp = requests.post(f"{BASE_URL}/optimize", json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        st.error(f"Optimize API error: {e}")
        st.stop()

    # API may return 'routes' (before) and optionally cost_before
    routes_before = data.get("routes") or data.get("routes_before") or []
    cost_before = data.get("cost_before") or data.get("cost") or 0

    st.subheader("Initial optimization")
    st.metric("Total cost (initial)", f"{cost_before:.2f}")
    st.write("Routes (initial):")
    st.json(routes_before)

    if show_map:
        m = plot_routes_on_map(routes_before, routes_after=None)
        folium_static(m, width=900, height=600)

# handle simulate / disruption
if run_sim:
    try:
        resp = requests.get(f"{BASE_URL}/simulate", params={"fuel_spike": 1}, timeout=10)
        resp.raise_for_status()
        sim = resp.json()
    except Exception as e:
        st.error(f"Simulate API error: {e}")
        st.stop()

    # expected keys: routes (after), cost_before, cost_after, disruption
    routes_after = sim.get("routes") or sim.get("routes_after") or []
    cost_before = sim.get("cost_before") or sim.get("cost") or 0
    cost_after = sim.get("cost_after") or sim.get("updated_cost") or 0
    disruption = sim.get("disruption", "unknown")
    decision_details = sim.get("decision_details", "No decision details provided.")

    st.subheader(f"Simulation: {disruption}")
    st.subheader("🚨 Real-Time Disruption Simulated")
    st.warning(f"**Disruption Event:** {disruption}")
    st.info(f"**Agent Decision & Rationale:** {decision_details}")
    
    st.metric("Cost before", f"{cost_before:.2f}")
    st.metric("Cost after", f"{cost_after:.2f}", delta=f"{(cost_after-cost_before):+.2f}")
    st.write("Routes (after disruption):")
    st.json(routes_after)

    if show_map:
        # get previous routes if available from endpoint (some backends return routes_before)
        routes_before = sim.get("routes_before") or []
        m = plot_routes_on_map(routes_before, routes_after, center=None)
        folium_static(m, width=900, height=600)

    show_cost_charts(cost_before, cost_after)

st.markdown("---")
st.markdown("Notes: This demo uses Folium/OpenStreetMap for maps to avoid paid APIs. To use a Kaggle dataset, place CSV at data/deliveries.csv (see README).")
