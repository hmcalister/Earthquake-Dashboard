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

REQUEST_TIMEOUT_SECONDS = 600.0
BATCH_SIZE = 32

CHANNEL_PRIORITY = {"HHZ": 0, "HHN": 1, "HHE": 2, "HNZ": 3, "HNN": 4, "HNE": 5}
Station = namedtuple("Station", ["network_code", "station_code"])

# %% Helpers

def load_active_stations() -> list:
    with sqlite3.connect(DATABASE) as conn:
        rows = queries.get_active_stations_with_target_channels(conn)
    return [Station(network_code=r[0], station_code=r[1]) for r in rows]

def batch_stations(all_stations: list) -> list[list]:
    batched_stations = []
    for index in range(0, len(all_stations), BATCH_SIZE):
        batched_stations.append(all_stations[index:min(index+BATCH_SIZE, len(all_stations))])
    return batched_stations

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

client = Client("https://service-nrt.geonet.org.nz", timeout=REQUEST_TIMEOUT_SECONDS)
station_list = load_active_stations()
batched_station_list = batch_stations(station_list)

# Fetch the preceding full hour
now = UTCDateTime()
end_time = UTCDateTime(now.year, now.month, now.day, now.hour)
start_time = end_time - 3600

print(f"Fetching station readings from {start_time} to {end_time} | {len(station_list)} stations | {len(batched_station_list)} batches")

for batch_index, batch in enumerate(batched_station_list):
    print(f"Batch {batch_index+1:03d} / {len(batched_station_list):03d}")

    bulk = [
        (s.network_code, s.station_code, "*", "H??", start_time, end_time)
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
                written_traces += 1
                rows.append(trace_to_row(tr))

            print(f"  Processed {station.station_code} ({len(station_stream)} traces found, {written_traces} traces saved)")

        if rows:
            with sqlite3.connect(DATABASE) as conn:
                queries.upsert_channel_waveform(conn, rows)

        del stream
        gc.collect()

    except FDSNNoDataException:
        print("No data")
    except Exception as e:
        print(f"Error: {e}")
