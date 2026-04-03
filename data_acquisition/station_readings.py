# %% Imports
import gc
import pathlib
import sqlite3
import zlib
from collections import namedtuple

import aiosql
import numpy as np
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException

# Settings
DATABASE = pathlib.Path("../data/earthquakes.sqlite")
QUERIES_FILE = pathlib.Path("../data/queries.sql")

queries = aiosql.from_path(QUERIES_FILE, "sqlite3")

REQUEST_BATCH_SIZE = 16
REQUEST_TIMEOUT_SECONDS = 600.0

Station = namedtuple("Station", ["network_code", "station_code"])

# %% Helpers

def load_active_stations() -> list:
    with sqlite3.connect(DATABASE) as conn:
        rows = queries.get_active_stations(conn)
    return [Station(network_code=r[0], station_code=r[1]) for r in rows]


def make_batches(station_list: list, batch_size: int) -> list[list]:
    return [
        station_list[i : i + batch_size]
        for i in range(0, len(station_list), batch_size)
    ]


def trace_to_row(tr) -> dict:
    samples = tr.data.astype(np.float32)
    waveform_blob = zlib.compress(samples.tobytes())
    return {
        "network_code": tr.stats.network,
        "station_code": tr.stats.station,
        "channel_code": tr.stats.channel,
        "location_code": tr.stats.location,
        "start_time": tr.stats.starttime.datetime.isoformat(),
        "end_time": tr.stats.endtime.datetime.isoformat(),
        "sample_rate": tr.stats.sampling_rate,
        "num_samples": tr.stats.npts,
        "waveform": waveform_blob,
    }


# Only these channels will be saved
CHANNEL_PRIORITY = {"HHZ": 0, "HHN": 1, "HHE": 2, "HNZ": 3, "HNN": 4, "HNE": 5}

# %% Continuous acquisition loop

client = Client("https://service-nrt.geonet.org.nz", timeout=REQUEST_TIMEOUT_SECONDS)

station_list = load_active_stations()
batches = make_batches(station_list, REQUEST_BATCH_SIZE)
num_batches = len(batches)

# Fetch the preceding full hour
now = UTCDateTime()
end_time = UTCDateTime(now.year, now.month, now.day, now.hour)
start_time = end_time - 3600

print(f"Fetching station readings from {start_time} to {end_time} | {num_batches} batches")

for batch_idx, batch in enumerate(batches):
    bulk = [
        (s.network_code, s.station_code, "*", "*", start_time, end_time)
        for s in batch
    ]

    try:
        stream = client.get_waveforms_bulk(bulk)

        rows = []
        for station in batch:
            station_stream = stream.select(station=station.station_code)

            if not station_stream:
                continue

            station_stream.detrend("demean")
            station_stream.traces.sort(
                key=lambda tr: CHANNEL_PRIORITY.get(tr.stats.channel, 99)
            )

            written_traces = 0
            for tr in station_stream:
                if tr.stats.channel not in CHANNEL_PRIORITY:
                    continue
                written_traces += 1
                rows.append(trace_to_row(tr))

            print(f"  Processed {station.station_code} ({len(station_stream)} traces found, {written_traces} traces saved)")

        if rows:
            with sqlite3.connect(DATABASE) as conn:
                queries.upsert_channel_waveform(conn, rows)

        del stream
        gc.collect()

    except FDSNNoDataException:
        print(f"  [batch {batch_idx + 1}] No data")
    except Exception as e:
        print(f"  [batch {batch_idx + 1}] Error: {e}")

# %%
