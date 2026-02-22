import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from typing import List

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

class RequestBody(BaseModel):
    regions: List[str]
    threshold_ms: int

# Load data (bundled with deployment)
with open("q-vercel-latency.json") as f:
    DATA = json.load(f)

@app.post("/")
async def get_metrics(body: RequestBody):
    selected = [r for r in DATA if r["region"] in body.regions]
    
    latencies = np.array([r["latency_ms"] for r in selected])
    uptimes = np.array([r["uptime"] for r in selected])  # Assume uptime field exists
    
    breaches = np.sum(latencies > body.threshold_ms)
    
    # Group by region
    results = {}
    for region in body.regions:
        region_data = [r for r in selected if r["region"] == region]
        if not region_data:
            results[region] = {"avg_latency": 0, "p95_latency": 0, "avg_uptime": 0, "breaches": 0}
            continue
        
        r_lat = np.array([r["latency_ms"] for r in region_data])
        r_up = np.array([r["uptime"] for r in region_data])
        
        results[region] = {
            "avg_latency": float(np.mean(r_lat)),
            "p95_latency": float(np.percentile(r_lat, 95)),
            "avg_uptime": float(np.mean(r_up)),
            "breaches": np.sum(r_lat > body.threshold_ms)
        }
    
    return results
