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

st.set_page_config(layout="wide", page_title="Logistics VRP")

st.title("Agentic AI — Logistics Optimization")

# Data loading: prefer Kaggle/local file, otherwise ask backend to generate
data_file = Path("data/deliveries.csv")
if data_file.exists():
    df = pd.read_csv(data_file)
    st.success(f"Loaded local data: {data_file} ({len(df)} rows)")
else:
    st.warning("No local data/deliveries.csv found. Ensure the dataset is present or optimization may fail.")
    df = None

col1, col2 = st.columns([1, 2])
with col1:
    st.header("Controls")
    num_vehicles = st.number_input("Num vehicles", value=4, min_value=1, max_value=20)
    vehicle_capacity = st.number_input("Vehicle capacity", value=150, min_value=10, max_value=500)
    num_orders = st.number_input("Num orders (destinations)", value=25, min_value=5, max_value=150)
    fuel_price = st.number_input("Fuel price (per unit distance)", value=1.0, step=0.1)
    scenario_options = ["Random", "Accident on Route", "Severe Weather", "Road Block / Protest", "Fuel Price Spike"]
    selected_scenario = st.selectbox("Disruption Scenario", scenario_options)
    run_opt = st.button("Run initial optimization")
    run_sim = st.button("Simulate selected disruption")
    show_map = st.checkbox("Show map (Folium)", value=True)

with col2:
    st.header("Dataset preview")
    if df is not None:
        st.dataframe(df.head())
    else:
        st.markdown("No local dataset found. Please place deliveries.csv in the data directory.")

def format_time(minutes):
    """Converts minutes from midnight to HH:MM format."""
    if minutes is None:
        return "Any"
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h:02d}:{m:02d}"

def plot_routes_on_map(routes_before, routes_after=None, center=None, locations=None, orders=None, depot_time_window=None):
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
    
    fg_before = folium.FeatureGroup(name="Before Disruption (Blue)")
    fg_after = folium.FeatureGroup(name="After Disruption (Red Dashed)")
    fg_locations = folium.FeatureGroup(name="Delivery Locations", show=True)

    # Add markers for all locations with time windows
    if locations and orders:
        # Depot Marker
        if depot_time_window:
            depot_start = format_time(depot_time_window[0])
            depot_end = format_time(depot_time_window[1])
            depot_tooltip = f"Depot (Open: {depot_start} - {depot_end})"
        else:
            depot_tooltip = "Depot"
        folium.Marker(
            location=locations[0],
            icon=folium.Icon(color="green", icon="home"),
            tooltip=depot_tooltip
        ).add_to(fg_locations)

        # Order Markers
        for order in orders:
            loc_idx = order["location_index"]
            start_time = format_time(order.get("time_window_start"))
            end_time = format_time(order.get("time_window_end"))
            tooltip = f"Order {order['order_id']}<br>Window: {start_time} - {end_time}"
            folium.Marker(
                location=locations[loc_idx],
                icon=folium.Icon(color="gray", icon="cube", prefix="fa"),
                tooltip=tooltip
            ).add_to(fg_locations)

    # draw before routes (blue)
    for i, r in enumerate(routes_before or []):
        coords = r.get("coords", [])
        if not coords: continue
        clean_coords = [[float(pt[0]), float(pt[1])] for pt in coords]
        folium.PolyLine(locations=clean_coords, color="blue", weight=4, opacity=0.5, tooltip=f"Before - Vehicle {i}").add_to(fg_before)
    # draw after routes (red)
    for i, r in enumerate(routes_after or []):
        coords = r.get("coords", [])
        if not coords: continue
        clean_coords = [[float(pt[0]), float(pt[1])] for pt in coords]
        folium.PolyLine(locations=clean_coords, color="red", weight=5, opacity=0.9, dash_array='10, 10', tooltip=f"After - Vehicle {i}").add_to(fg_after)
        
    fg_before.add_to(m)
    if routes_after:
        fg_after.add_to(m)
    fg_locations.add_to(m)
    folium.LayerControl().add_to(m)
    return m

def show_cost_charts(cost_before, cost_after):
    labels = ["Before", "After"]
    vals = [cost_before or 0, cost_after or 0]
    fig, ax = plt.subplots()
    ax.bar(labels, vals, color=["blue", "red"])
    ax.set_ylabel("Total cost")
    ax.set_title("Cost before vs after")
    st.pyplot(fig)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in miles using Haversine formula."""
    R = 3959  # Earth radius in miles
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat/2)**2 + 
         np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * 
         np.sin(dlon/2)**2)
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

def display_route_details(title, routes, locations):
    st.subheader(title)
    for i, route in enumerate(routes):
        with st.expander(f"Vehicle {i+1} Details"):
            sequence = route.get("route", [])
            st.write(f"**Sequence:** `{' -> '.join(map(str, sequence))}`")
            
            total_distance = 0
            for j in range(len(sequence) - 1):
                loc1 = locations[sequence[j]]
                loc2 = locations[sequence[j+1]]
                total_distance += haversine_distance(loc1[0], loc1[1], loc2[0], loc2[1])
            st.metric("Route Distance", f"{total_distance:.2f} miles")

# handle initial optimize
if run_opt:
    payload = {
        "num_vehicles": int(num_vehicles),
        "vehicle_capacity": int(vehicle_capacity),
        "fuel_price": float(fuel_price),
        "num_orders": int(num_orders),
        "source": "NYC"
    }
    try:
        resp = requests.post(f"{BASE_URL}/optimize", json=payload, timeout=20)
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
        m = plot_routes_on_map(
            routes_before, 
            routes_after=None, 
            locations=data.get("locations"), 
            orders=data.get("orders"), 
            depot_time_window=data.get("depot_time_window")
        )
        folium_static(m, width=900, height=600)

# handle simulate / disruption
if run_sim:
    try:
        params = {}
        if selected_scenario != "Random":
            params["scenario"] = selected_scenario
        resp = requests.get(f"{BASE_URL}/simulate", params=params, timeout=20)
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

    st.subheader("Disruption Simulation Results")
    st.warning(f"**Disruption Event:** {disruption}")
    st.info(f"**Agent Decision & Rationale:** {decision_details}")
    
    st.metric("Cost before", f"{cost_before:.2f}")
    st.metric("Cost after", f"{cost_after:.2f}", delta=f"{(cost_after-cost_before):+.2f}")
    st.write("Routes (after disruption):")
    st.json(routes_after)

    if show_map:
        # get previous routes if available from endpoint (some backends return routes_before)
        routes_before = sim.get("routes_before") or []
        m = plot_routes_on_map(
            routes_before, 
            routes_after, 
            center=None, 
            locations=sim.get("locations"), 
            orders=sim.get("orders"),
            depot_time_window=sim.get("depot_time_window")
        )
        folium_static(m, width=900, height=600)

    # Display detailed route breakdown
    locations = sim.get("locations", [])
    display_route_details("Route Analysis (Before Disruption)", routes_before, locations)
    display_route_details("Route Analysis (After Disruption)", routes_after, locations)

    show_cost_charts(cost_before, cost_after)

st.markdown("---")
st.markdown("Notes: This system uses Folium/OpenStreetMap for maps to avoid paid APIs. Ensure a production Kaggle dataset is placed at data/deliveries.csv (see README).")
