
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# (region, latency_ms, uptime_pct)
TELEMETRY = [
    ("apac", 104.03, 97.236),
    ("apac", 124.67, 97.306),
    ("apac", 153.65, 97.426),
    ("apac", 158.66, 98.744),
    ("apac", 161.37, 99.163),
    ("apac", 152.43, 97.167),
    ("apac", 121.41, 99.235),
    ("apac", 135.41, 99.291),
    ("apac", 193.14, 99.107),
    ("apac", 165.96, 98.282),
    ("apac", 141.60, 97.716),
    ("apac", 129.88, 99.372),

    ("emea", 210.99, 97.258),
    ("emea", 161.35, 98.042),
    ("emea", 189.44, 97.640),
    ("emea", 120.89, 99.029),
    ("emea", 153.22, 99.197),
    ("emea", 119.01, 98.104),
    ("emea", 168.28, 97.745),
    ("emea", 197.86, 98.937),
    ("emea", 137.33, 98.926),
    ("emea", 226.84, 97.236),
    ("emea", 209.08, 97.531),
    ("emea", 123.86, 98.701),

    ("amer", 161.83, 97.160),
    ("amer", 188.79, 97.215),
    ("amer", 190.21, 98.659),
    ("amer", 154.27, 97.270),
    ("amer", 171.46, 97.575),
    ("amer", 169.04, 97.172),
    ("amer", 171.65, 99.088),
    ("amer", 193.70, 97.137),
    ("amer", 176.83, 97.263),
    ("amer", 193.30, 98.761),
    ("amer", 224.82, 97.746),
    ("amer", 100.93, 99.464),
]


class AnalyticsRequest(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile_95(values):
    values = sorted(values)

    if len(values) == 1:
        return values[0]

    # Linear interpolation at the 95th percentile.
    position = 0.95 * (len(values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)

    return (
        values[lower]
        + (values[upper] - values[lower])
        * (position - lower)
    )


@app.post("/api/latency")
def latency_analytics(request: AnalyticsRequest):
    response = []

    for region in request.regions:
        records = [
            (latency, uptime)
            for record_region, latency, uptime in TELEMETRY
            if record_region == region
        ]

        if not records:
            raise HTTPException(
                status_code=404,
                detail=f"No telemetry found for region: {region}",
            )

        latencies = [latency for latency, _ in records]
        uptimes = [uptime for _, uptime in records]

        response.append({
            "region": region,
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": percentile_95(latencies),
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(
                latency > request.threshold_ms
                for latency in latencies
            ),
        })

    return {"regions": response}
