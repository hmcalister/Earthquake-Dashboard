# %% Imports
import gc  # Added for manual memory management
import pathlib
import time

import pandas as pd
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException

# Settings
SAVE_BASE_DIR = pathlib.Path("../data/current_readings")
STATIONS_DATA_FILE_PATH = pathlib.Path("../data/stations.parquet")
CHANNELS_DATA_FILE_PATH = pathlib.Path("../data/channels.parquet")

SAVE_BASE_DIR.mkdir(parents=True, exist_ok=True)

# REDUCED BATCH SIZE: 32 stations x 1 hour of data is very heavy.
# Reducing this prevents RAM spikes.
REQUEST_BATCH_SIZE = 8
REQUEST_TIMEOUT_SECONDS = 300.0
DATA_WINDOW_SECONDS = 3600.0
STATION_REFRESH_INTERVAL_CYCLES = 24

# %% Helpers


def load_active_stations(
    stations_path: pathlib.Path, channels_path: pathlib.Path
) -> list:
    stations_df = pd.read_parquet(stations_path)
    now = pd.Timestamp.now(tz="UTC")
    active_stations = stations_df[
        stations_df["end_date"].isna() | (stations_df["end_date"] > now)
    ]
    return list(active_stations.itertuples(index=False))


def make_batches(station_list: list, batch_size: int) -> list[list]:
    return [
        station_list[i : i + batch_size]
        for i in range(0, len(station_list), batch_size)
    ]


CHANNEL_PRIORITY = {"HHZ": 0, "HHN": 1, "HHE": 2, "HNZ": 3, "HNN": 4, "HNE": 5}

# %% Continuous acquisition loop

# Initialize client once
client = Client("https://service-nrt.geonet.org.nz", timeout=REQUEST_TIMEOUT_SECONDS)

station_list = load_active_stations(STATIONS_DATA_FILE_PATH, CHANNELS_DATA_FILE_PATH)
batches = make_batches(station_list, REQUEST_BATCH_SIZE)

cycle = 0

while True:
    if cycle > 0 and cycle % STATION_REFRESH_INTERVAL_CYCLES == 0:
        try:
            station_list = load_active_stations(
                STATIONS_DATA_FILE_PATH, CHANNELS_DATA_FILE_PATH
            )
            batches = make_batches(station_list, REQUEST_BATCH_SIZE)
        except Exception as e:
            print(f"[station refresh] Error: {e}")

    num_batches = len(batches)
    inter_batch_delay = DATA_WINDOW_SECONDS / num_batches

    print(f"\n=== Cycle {cycle + 1} | {num_batches} batches ===")

    for batch_idx, batch in enumerate(batches):
        end_time = UTCDateTime()
        start_time = end_time - DATA_WINDOW_SECONDS

        bulk = [
            (s.network_code, s.station_code, "*", "*", start_time, end_time)
            for s in batch
        ]

        try:
            # REMOVED: ThreadPoolExecutor overhead.
            # get_waveforms_bulk is already an optimized network call.
            stream = client.get_waveforms_bulk(bulk)

            for station in batch:
                # Use select to get station traces
                station_stream = stream.select(station=station.station_code)

                if not station_stream:
                    continue

                # Detrending is CPU intensive; doing it per station keeps it manageable
                station_stream.detrend("demean")
                station_stream.traces.sort(
                    key=lambda tr: CHANNEL_PRIORITY.get(tr.stats.channel, 99)
                )

                save_path = (
                    SAVE_BASE_DIR
                    / f"{station.network_code}.{station.station_code}.mseed"
                )
                station_stream.write(str(save_path), format="MSEED")
                print(f"  Saved {station.station_code}")

            # CRITICAL: Clear memory after each batch
            del stream
            gc.collect()

        except FDSNNoDataException:
            print(f"  [batch {batch_idx + 1}] No data")
        except Exception as e:
            print(f"  [batch {batch_idx + 1}] Error: {e}")

        time.sleep(inter_batch_delay)

    cycle += 1
