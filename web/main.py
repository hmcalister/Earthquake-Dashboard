import pathlib
import sqlite3
import zlib

import aiosql
import numpy as np
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Earthquake Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")

DATABASE = pathlib.Path("../data/earthquakes.sqlite")
QUERIES_FILE = pathlib.Path("../data/queries.sql")
MAX_PLOT_POINTS = 1000

queries = aiosql.from_path(QUERIES_FILE, "sqlite3")


@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")


@app.get("/api/stations")
def get_stations():
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        rows = queries.get_stations_with_readings(conn)
    return [dict(r) for r in rows]


TIMEFRAME_INTERVALS = {
    "1h": "-1 hour",
    "24h": "-24 hours",
    "1w": "-7 days",
    "1m": "-30 days",
}


@app.get("/api/events")
def get_events(timeframe: str = "1h"):
    interval = TIMEFRAME_INTERVALS.get(timeframe, TIMEFRAME_INTERVALS["1h"])
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        rows = queries.get_recent_earthquakes(conn, interval=interval)
    return [dict(r) for r in rows]


@app.get("/api/stations/{station_code}/readings")
def get_station_readings(station_code: str):
    with sqlite3.connect(DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        rows = list(queries.get_station_waveforms(conn, station_code=station_code))

    if not rows:
        return {"error": "No readings found for this station.", "traces": []}

    traces = []
    measured_at = None
    for row in rows:
        raw = zlib.decompress(row["waveform"])
        data = np.frombuffer(raw, dtype=np.float32).tolist()
        if len(data) > MAX_PLOT_POINTS:
            step = len(data) / MAX_PLOT_POINTS
            data = [data[int(i * step)] for i in range(MAX_PLOT_POINTS)]
        if measured_at is None or row["end_time"] > measured_at:
            measured_at = row["end_time"]
        traces.append(
            {
                "channel": row["channel_code"],
                "sampling_rate": row["sample_rate"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "data": data,
            }
        )

    return {"measured_at": measured_at, "traces": traces}
