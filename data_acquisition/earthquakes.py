# %% Imports
import pathlib
import pickle

import pandas as pd
from obspy import Catalog, UTCDateTime
from obspy.clients.fdsn import Client

REQUESTS_BASE_DIR = pathlib.Path("../data/requests")

# %% Make Requests

client = Client("GEONET")
date_strs = [
    "2025-01-01",
    "2025-02-01",
    "2025-03-01",
    "2025-04-01",
    "2025-05-01",
    "2025-06-01",
    "2025-07-01",
    "2025-08-01",
    "2025-09-01",
    "2025-10-01",
    "2025-11-01",
    "2025-12-01",
    "2026-01-01",
]

for start_date_str, end_date_str in zip(date_strs, date_strs[1:]):
    print(f"REQUESTING DATA {start_date_str}")

    request_response = client.get_events(
        starttime=UTCDateTime(start_date_str),
        endtime=UTCDateTime(end_date_str),
        minmagnitude=5.0,
    )

    if request_response is None:
        print("\tREQUEST FAILED")
        continue

    month_catalog: Catalog = request_response

    print("\tREQUEST COMPLETE")

    with open(REQUESTS_BASE_DIR.joinpath(f"{start_date_str}.pkl"), "wb") as f:
        pickle.dump(month_catalog, f)

# %% Process to Events

rows = []
for filepath in REQUESTS_BASE_DIR.glob("*.pkl"):
    with open(filepath, "rb") as f:
        month_catalog: Catalog = pickle.load(f)

    for event in month_catalog:
        origin = event.preferred_origin()
        magnitude = event.preferred_magnitude()
        if origin is None or magnitude is None:
            continue
        rows.append(
            {
                "event_id": str(event.resource_id),
                "time": origin.time.datetime,
                "latitude": origin.latitude,
                "longitude": origin.longitude,
                "depth_m": origin.depth,
                "magnitude": magnitude.mag,
                "magnitude_type": magnitude.magnitude_type,
            }
        )

df = pd.DataFrame(rows)
df["time"] = pd.to_datetime(df["time"], utc=True)
print(df)

# %%
