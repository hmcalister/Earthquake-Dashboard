import pathlib
from datetime import datetime

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Earthquake Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")

STATIONS_PATH = "../data/stations.parquet"
READINGS_DIR = pathlib.Path("../data/current_readings")
MAX_PLOT_POINTS = 1000


@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")


@app.get("/api/stations")
def get_stations():
    df = pd.read_parquet(
        STATIONS_PATH,
        columns=[
            "station_code",
            "station_name",
            "latitude",
            "longitude",
            "elevation_m",
            "end_date",
        ],
    )
    now = pd.Timestamp.now(tz="UTC")
    df = df[df["end_date"].isna() | (df["end_date"] > now)]
    df = df.drop(columns=["end_date"])
    return df.to_dict(orient="records")


@app.get("/api/stations/{station_code}/readings")
def get_station_readings(station_code: str):

    matches = list(READINGS_DIR.glob(f"*.{station_code}.mseed"))
    if not matches:
        return {"error": "No readings found for this station.", "traces": []}

    try:
        measured_at = datetime.fromtimestamp(matches[0].stat().st_mtime).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        from obspy import read as obspy_read

        stream = obspy_read(str(matches[0]))
        traces = []
        for tr in stream:
            data = tr.data.tolist()
            # Downsample to MAX_PLOT_POINTS by taking evenly spaced indices
            if len(data) > MAX_PLOT_POINTS:
                step = len(data) / MAX_PLOT_POINTS
                data = [data[int(i * step)] for i in range(MAX_PLOT_POINTS)]
            traces.append(
                {
                    "channel": tr.stats.channel,
                    "sampling_rate": tr.stats.sampling_rate,
                    "start_time": str(tr.stats.starttime),
                    "end_time": str(tr.stats.endtime),
                    "data": data,
                }
            )
        return {"measured_at": measured_at, "traces": traces}
    except Exception as e:
        return {"error": str(e), "traces": []}
