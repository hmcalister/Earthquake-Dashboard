# %% Imports
import pathlib
import sqlite3

import aiosql
from obspy import Catalog, UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException

# Settings
DATABASE = pathlib.Path("../data/earthquakes.sqlite")
QUERIES_FILE = pathlib.Path("../data/queries.sql")

queries = aiosql.from_path(QUERIES_FILE, "sqlite3")

REQUEST_TIMEOUT_SECONDS = 300.0
INTERVAL_SAFETY_FACTOR = 1.5

# %% Make Requests

client = Client("GEONET", timeout=REQUEST_TIMEOUT_SECONDS)

# Fetch the preceding full hour
now = UTCDateTime()
end_time = UTCDateTime(now.year, now.month, now.day, now.hour)
start_time = end_time - 3600 * INTERVAL_SAFETY_FACTOR

print(f"Fetching earthquakes from {start_time} to {end_time}")

try:
    request_response = client.get_events(
        starttime=start_time,
        endtime=end_time,
    )

    if request_response is None:
        print("Request failed!")
    else:
        catalog: Catalog = request_response

        rows = []
        for event in catalog:
            origin = event.preferred_origin()
            magnitude = event.preferred_magnitude()
            if origin is None or magnitude is None:
                continue
            rows.append(
                {
                    "event_id": str(event.resource_id),
                    "datetime": origin.time.datetime,
                    "latitude": origin.latitude,
                    "longitude": origin.longitude,
                    "depth_m": origin.depth,
                    "magnitude": magnitude.mag,
                    "magnitude_type": magnitude.magnitude_type,
                }
            )

        with sqlite3.connect(DATABASE) as conn:
            queries.insert_earthquake(conn, rows)

        print(f"Inserted {len(rows)} events")

except FDSNNoDataException:
    print("Error: no data in request")
except Exception as e:
    print(f"Error: {e}")

# %%
