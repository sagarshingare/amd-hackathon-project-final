import streamlit as st
import requests
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
import altair as alt
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

# Initialize session state for holding the API session_id
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'results' not in st.session_state:
    st.session_state.results = None

col1, col2 = st.columns([1, 2])
with col1:
    st.header("Controls")
    num_vehicles = st.number_input("Num vehicles", value=4, min_value=1, max_value=20)
    vehicle_capacity = st.number_input("Vehicle capacity", value=150, min_value=10, max_value=500)
    num_orders = st.number_input("Num orders (destinations)", value=25, min_value=5, max_value=150)
    fuel_price = st.number_input("Fuel price (per unit distance)", value=1.0, step=0.1)
    driver_hourly_wage = st.number_input("Driver Hourly Wage ($)", value=25.0, step=1.0)
    scenario_options = ["Random", "Accident on Route", "Severe Weather", "Road Block / Protest", "Fuel Price Spike"]
    selected_scenario = st.selectbox("Disruption Scenario", scenario_options)
    run_opt = st.button("Run initial optimization")
    run_sim = st.button("Simulate selected disruption")

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

def show_comparison_charts(metrics_data):
    """Renders separate interactive line charts for each metric."""
    if not metrics_data:
        return

    df = pd.DataFrame(metrics_data)
    
    # Use columns for a better side-by-side layout
    cols = st.columns(len(df['Metric'].unique()))
    
    for i, metric in enumerate(df['Metric'].unique()):
        with cols[i]:
            metric_df = df[df['Metric'] == metric]
            metric_df_melted = metric_df.melt(id_vars=['Metric'], value_vars=['Before', 'After'], var_name='Scenario', value_name='Value')

            chart = alt.Chart(metric_df_melted).mark_bar().encode(
                x=alt.X('Scenario:N', title=None, axis=alt.Axis(labelAngle=0, grid=False)),
                y=alt.Y('Value:Q', title=None, scale=alt.Scale(zero=False)),
                color=alt.Color('Scenario:N', 
                              scale=alt.Scale(domain=['Before', 'After'], range=['#1f77b4', '#d62728']), # Blue for Before, Red for After
                              legend=None), # Legend is redundant with x-axis
                tooltip=[alt.Tooltip('Value:Q', format='.2f')]
            ).properties(
                title=alt.TitleParams(text=metric, anchor='middle')
            ).interactive()
            
            st.altair_chart(chart, use_container_width=True)

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

def calculate_total_distance(routes, locations):
    """Calculates the total distance for a set of routes."""
    total_distance = 0
    if not routes or not locations:
        return 0
    for route in routes:
        sequence = route.get("route", [])
        for j in range(len(sequence) - 1):
            if sequence[j] < len(locations) and sequence[j+1] < len(locations):
                loc1 = locations[sequence[j]]
                loc2 = locations[sequence[j+1]]
                total_distance += haversine_distance(loc1[0], loc1[1], loc2[0], loc2[1])
    return total_distance

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

def calculate_capacity_utilization(routes, orders, vehicle_capacity):
    """Calculates the average capacity utilization across all vehicles."""
    if not routes:
        return 0
    
    total_utilization = 0
    order_demands = {order['location_index']: order['demand'] for order in orders}
    
    for route in routes:
        route_demand = sum(order_demands.get(node, 0) for node in route.get("route", []))
        utilization = (route_demand / vehicle_capacity) * 100 if vehicle_capacity > 0 else 0
        total_utilization += utilization
        
    return total_utilization / len(routes)

def display_results(results_data):
    """Renders the entire results dashboard using tabs."""
    
    # Extract data with defaults
    cost_before = results_data.get("cost_before", 0)
    cost_after = results_data.get("cost_after", cost_before) # Default to cost_before if no disruption
    disruption = results_data.get("disruption")
    decision_details = results_data.get("decision_details")
    routes_before = results_data.get("routes_before") or results_data.get("routes", [])
    routes_after = results_data.get("routes_after") if disruption else None
    locations = results_data.get("locations", [])
    orders = results_data.get("orders", [])
    depot_time_window = results_data.get("depot_time_window")

    # --- Main Dashboard Area ---
    st.header("📊 Optimization Dashboard")

    # Display disruption info if it exists
    if disruption:
        st.warning(f"**Disruption Event:** {disruption}")
        st.info(f"**Agent Decision & Rationale:** {decision_details}")

    # KPI Metrics
    total_distance_before = calculate_total_distance(routes_before, locations)
    total_distance_after = calculate_total_distance(routes_after, locations) if routes_after else total_distance_before
    num_vehicles_after = len(routes_after) if routes_after else len(routes_before)
    utilization_before = calculate_capacity_utilization(routes_before, orders, int(vehicle_capacity))
    utilization_after = calculate_capacity_utilization(routes_after, orders, int(vehicle_capacity)) if routes_after else utilization_before
    
    # Extract total_cost from the cost dictionaries
    total_cost_before_val = cost_before.get("total_cost", 0)
    total_cost_after_val = cost_after.get("total_cost", total_cost_before_val)

    kpi_cols = st.columns(6)
    kpi_cols[0].metric("Initial Cost", f"{total_cost_before_val:.2f}")
    kpi_cols[1].metric("Optimized Cost", f"{total_cost_after_val:.2f}", delta=f"{(total_cost_after_val - total_cost_before_val):.2f}")
    kpi_cols[2].metric("Total Distance", f"{total_distance_after:.1f} mi", delta=f"{(total_distance_after - total_distance_before):.1f} mi")
    kpi_cols[3].metric("Vehicles Used", num_vehicles_after, delta=num_vehicles_after - len(routes_before))
    kpi_cols[4].metric("Avg. Capacity Use", f"{utilization_after:.1f}%", delta=f"{(utilization_after - utilization_before):.1f}%")
    kpi_cols[5].metric("Total Deliveries", len(orders))

    # --- Tabs for Detailed Views ---
    map_tab, details_tab, chart_tab, data_tab = st.tabs(["🗺️ Route Map", "⚙️ Route Details", "📈 Comparison Chart", "📋 Raw Data"])

    with map_tab:
        st.subheader("Vehicle Route Visualization")
        m = plot_routes_on_map(
            routes_before, 
            routes_after, 
            locations=locations, 
            orders=orders,
            depot_time_window=depot_time_window
        )
        folium_static(m, width=950, height=600)

    with details_tab:
        if routes_after:
            col_before, col_after = st.columns(2)
            with col_before:
                display_route_details("Route Analysis (Before Disruption)", routes_before, locations)
            with col_after:
                display_route_details("Route Analysis (After Disruption)", routes_after, locations)
        else:
            display_route_details("Initial Route Plan", routes_before, locations)

    with chart_tab:
        st.subheader("Metric Comparison")
        # Calculate metrics for charting
        num_orders_val = len(orders) if len(orders) > 0 else 1 # Avoid division by zero

        num_vehicles_before = len(routes_before)
        avg_dist_before = total_distance_before / num_orders_val

        # If there's no 'after' route, use the 'before' values for comparison
        if routes_after:
            avg_dist_after = total_distance_after / num_orders_val
        else:
            avg_dist_after = avg_dist_before

        # Extract cost breakdown if available
        cost_details_before = results_data.get("cost_before", {})
        cost_details_after = results_data.get("cost_after", cost_details_before)

        metrics_to_plot = [
            {'Metric': 'Total Cost ($)', 'Before': cost_details_before.get("total_cost", 0), 'After': cost_details_after.get("total_cost", 0)},
            {'Metric': 'Total Distance (miles)', 'Before': total_distance_before, 'After': total_distance_after},
            {'Metric': 'Fuel Cost ($)', 'Before': cost_details_before.get("fuel_cost", 0), 'After': cost_details_after.get("fuel_cost", 0)},
            {'Metric': 'Labor Cost ($)', 'Before': cost_details_before.get("labor_cost", 0), 'After': cost_details_after.get("labor_cost", 0)},
        ]
        show_comparison_charts(metrics_to_plot)

    with data_tab:
        st.subheader("Raw Route Output")
        if routes_after:
            st.write("Routes Before Disruption:")
            st.json(routes_before)
            st.write("Routes After Disruption:")
            st.json(routes_after)
        else:
            st.write("Initial Routes:")
            st.json(routes_before)


# handle initial optimize
if run_opt:
    payload = {
        "num_vehicles": int(num_vehicles),
        "vehicle_capacity": int(vehicle_capacity),
        "fuel_price": float(fuel_price),
        "driver_hourly_wage": float(driver_hourly_wage),
        "num_orders": int(num_orders),
        "source": "NYC"
    }
    try:
        with st.spinner("Running initial optimization... This may take a moment for large datasets."):
            resp = requests.post(f"{BASE_URL}/optimize", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            st.session_state.session_id = data.get("session_id")
            st.session_state.results = data
    except Exception as e:
        st.error(f"Optimize API error: {e}")
        st.stop()

# handle simulate / disruption
if run_sim:
    try:
        if not st.session_state.session_id:
            st.error("Please run an initial optimization first to start a session.")
            st.stop()
        with st.spinner(f"Simulating '{selected_scenario}' disruption and replanning..."):
            params = {"session_id": st.session_state.session_id}
            if selected_scenario != "Random":
                params["scenario"] = selected_scenario
            resp = requests.get(f"{BASE_URL}/simulate", params=params, timeout=60)
            resp.raise_for_status()
            sim_data = resp.json()
            st.session_state.results = sim_data
    except Exception as e:
        st.error(f"Simulate API error: {e}")
        st.stop()


# --- Main Display Area ---
if st.session_state.results:
    display_results(st.session_state.results)
else:
    st.info("Click 'Run initial optimization' to begin.")

st.markdown("---")
st.markdown("Notes: This system uses Folium/OpenStreetMap for maps to avoid paid APIs. Ensure a production Kaggle dataset is placed at data/deliveries.csv (see README).")
