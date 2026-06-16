# Agentic AI Logistics Optimization

A production-ready open-source agentic AI system for logistics route optimization, disruption simulation, and real-time rerouting.

## Features

- Multi-vehicle routing with OR-Tools
- Cost optimization for distance, fuel, and delay
- Disruption simulation for traffic and fuel spikes
- ML training pipeline for travel delay prediction
- Streamlit frontend with route plots and cost comparison
- FastAPI backend with `/optimize` and `/simulate`

## Project Structure

```text
app/
├── main.py
├── agents/
│   ├── planner.py
│   ├── optimizer.py
│   ├── disruption.py
│   ├── replanner.py
│   └── orchestrator.py
├── optimization/
│   └── vrp_solver.py
├── ml/
│   ├── train.py
│   └── predict.py
├── data/
│   └── generate_data.py
├── utils/
│   ├── cost.py
│   └── features.py
└── api/
    └── routes.py
frontend/
└── app.py
requirements.txt
README.md
```

## Run Instructions

1. Create and activate a Python environment.
2. Install dependencies:

```bash
cd /Users/sagarshingare/Documents/amd-hackathon-project-final
python3 -m pip install -r requirements.txt
```

3. Start the backend API:

```bash
cd /Users/sagarshingare/Documents/amd-hackathon-project-final
PYTHONPATH=. python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Start the Streamlit frontend:

```bash
cd /Users/sagarshingare/Documents/amd-hackathon-project-final # Use python -m streamlit for robust pathing
python3 -m streamlit run frontend/app.py
```

## Demo Flow

1. Generate delivery network
2. Run initial optimization
3. Show routes + cost
4. Trigger disruption (fuel or traffic)
5. Rerun optimization
6. Show updated routes + cost difference

## API Examples

```bash
curl -X POST "http://127.0.0.1:8000/optimize"
curl "http://127.0.0.1:8000/simulate"
```
