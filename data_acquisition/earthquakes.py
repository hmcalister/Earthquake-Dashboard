# %% Imports
import pathlib
import sqlite3
import time

import aiosql
from obspy import Catalog, UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException

# Settings
DATABASE = pathlib.Path("../data/earthquakes.sqlite")
QUERIES_FILE = pathlib.Path("../data/queries.sql")

queries = aiosql.from_path(QUERIES_FILE, "sqlite3")

REQUEST_PERIOD = 5 * 60
DATA_WINDOW_SECONDS = 10 * REQUEST_PERIOD
REQUEST_TIMEOUT_SECONDS = 300.0

# %% Make Requests

client = Client("GEONET", timeout=REQUEST_TIMEOUT_SECONDS)
cycle = 0

while True:
    end_time = UTCDateTime()
    start_time = end_time - DATA_WINDOW_SECONDS

    print(f"\n=== Cycle {cycle + 1}, Datetime {end_time} ===")


    print("Sending request")

    try:
        request_response = client.get_events(
            starttime=start_time,
            endtime=end_time,
        )

        if request_response is None:
            print("Request failed!")
            continue


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

    time.sleep(REQUEST_PERIOD)
    cycle += 1

# %%
