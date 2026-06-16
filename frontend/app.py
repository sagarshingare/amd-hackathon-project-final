import json
import requests
import streamlit as st
import matplotlib.pyplot as plt

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Agentic Logistics AI", layout="wide")

st.title("Agentic AI Logistics Optimization")

with st.sidebar:
    st.header("Demo Flow")
    st.markdown("1. Generate delivery network")
    st.markdown("2. Run initial optimization")
    st.markdown("3. Show routes + cost")
    st.markdown("4. Trigger disruption")
    st.markdown("5. Rerun optimization")
    st.markdown("6. Show updated cost difference")
    if st.button("Run initial optimization"):
        response = requests.post(f"{API_URL}/optimize")
        st.session_state["optimize"] = response.json()
    if st.button("Trigger disruption"):
        response = requests.get(f"{API_URL}/simulate")
        st.session_state["simulate"] = response.json()

optimize_result = st.session_state.get("optimize")
simulate_result = st.session_state.get("simulate")


def plot_routes(locations, routes, title):
    fig, ax = plt.subplots(figsize=(6, 6))
    for route in routes:
        xs = [locations[node][0] for node in route]
        ys = [locations[node][1] for node in route]
        ax.plot(xs, ys, marker="o", label=f"Route {routes.index(route)+1}")
        for idx, node in enumerate(route):
            ax.text(locations[node][0], locations[node][1], str(node), fontsize=9)
    ax.set_title(title)
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")
    ax.legend()
    ax.grid(True)
    return fig

if optimize_result:
    st.subheader("Initial Optimization")
    st.write("Fuel price:", optimize_result["summary"]["fuel_price"])
    st.write("Total cost:", optimize_result["cost_before"])
    st.write("Routes:")
    st.json(optimize_result["routes"])
    fig = plot_routes(optimize_result["locations"], optimize_result["routes"], "Initial Optimized Routes")
    st.pyplot(fig)

if simulate_result:
    st.subheader("Disruption Simulation")
    st.write("Disruption:", simulate_result["disruption"])
    st.write("Fuel before:", simulate_result["summary"]["fuel_price_before"])
    st.write("Fuel after:", simulate_result["summary"]["fuel_price_after"])
    st.write("Delay multiplier:", simulate_result["summary"]["delay_multiplier"])

    col1, col2 = st.columns(2)
    col1.metric("Cost before", simulate_result["cost_before"])
    col2.metric("Cost after", simulate_result["cost_after"])

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["Before", "After"], [simulate_result["cost_before"], simulate_result["cost_after"]], color=["#2E86AB", "#F29E4C"])
    ax.set_title("Cost before vs after disruption")
    ax.set_ylabel("Cost")
    st.pyplot(fig)

    st.write("Updated routes:")
    st.json(simulate_result["routes_after"])
    fig = plot_routes(simulate_result["locations"], simulate_result["routes_after"], "Routes After Disruption")
    st.pyplot(fig)
    if "routes_before" in simulate_result:
        fig2 = plot_routes(simulate_result["locations"], simulate_result["routes_before"], "Routes Before Disruption")
        st.pyplot(fig2)
