# %% Imports

import concurrent.futures
import pathlib
import time

import pandas as pd
from obspy import Stream, UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNNoDataException

SAVE_BASE_DIR = pathlib.Path("../data/current_readings")
STATIONS_DATA_FILE_PATH = pathlib.Path("../data/stations.parquet")
CHANNELS_DATA_FILE_PATH = pathlib.Path("../data/channels.parquet")

REQUEST_BATCH_SIZE = 32
REQUEST_TIMEOUT_SECONDS = 300.0
REQUEST_COURTESY_DELAY_SECONDS = 100.0

# %% Prepare stations for querying

stations_df = pd.read_parquet(STATIONS_DATA_FILE_PATH)
channels_df = pd.read_parquet(CHANNELS_DATA_FILE_PATH)
now = pd.Timestamp.now(tz="UTC")
active_stations = stations_df[
    stations_df["end_date"].isna() | (stations_df["end_date"] > now)
]
active_channels = channels_df[
    channels_df["end_date"].isna() | (channels_df["end_date"] > now)
]
active_channels_df = pd.merge(
    active_stations, active_channels, on=["network_code", "station_code"]
)

# %% Query Recent Readings

client = Client("https://service-nrt.geonet.org.nz")
end_time = UTCDateTime()
start_time = end_time - 3600

station_list = list(active_stations.itertuples(index=False))
batches = [
    station_list[i : i + REQUEST_BATCH_SIZE]
    for i in range(0, len(station_list), REQUEST_BATCH_SIZE)
]

# %% Query Recent Readings

for batch_idx, batch in enumerate(batches):
    bulk = [
        (station.network_code, station.station_code, "*", "*", start_time, end_time)
        for station in batch
    ]
    batch_label = ", ".join(f"{s.network_code}.{s.station_code}" for s in batch)
    print(f"[batch {batch_idx + 1}/{len(batches)}] Requesting {batch_label}")

    try:
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(client.get_waveforms_bulk, bulk)
        try:
            stream: Stream = future.result(timeout=REQUEST_TIMEOUT_SECONDS)
        finally:
            executor.shutdown(wait=False)
        for station in batch:
            station_stream = stream.select(station=station.station_code)
            if len(station_stream) == 0:
                continue
            station_stream.detrend("demean")
            channel_priority = {
                "HHZ": 0,
                "HHN": 1,
                "HHE": 2,
                "HNZ": 3,
                "HNN": 4,
                "HNE": 5,
            }
            station_stream.traces.sort(
                key=lambda tr: channel_priority.get(tr.stats.channel, 99)
            )
            save_path = SAVE_BASE_DIR.joinpath(
                f"{station.network_code}.{station.station_code}.mseed"
            )
            station_stream.write(str(save_path), format="MSEED")
            print(f"  Saved {len(station_stream)} trace(s) -> {save_path.name}")
    except concurrent.futures.TimeoutError:
        print("  Request timed out")
        continue
    except FDSNNoDataException:
        print("  No Data Available")
        continue
    except Exception as e:
        print(f"  Error: {e}")
        continue

    if batch_idx < len(batches) - 1:
        time.sleep(REQUEST_COURTESY_DELAY_SECONDS)
