from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Agentic AI Logistics Optimization")
app.include_router(router)

@app.get("/")
def read_root():
    return {"status": "Agentic AI Logistics Optimization API is running"}
