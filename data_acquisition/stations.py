# %% Imports

import pathlib
import pickle

import pandas as pd
from obspy.clients.fdsn import Client

REQUESTS_BASE_DIR = pathlib.Path("../data/station_requests")

# %% Make Requests

client = Client("GEONET")
station_inventory = client.get_stations(level="channel")

with open(REQUESTS_BASE_DIR.joinpath("stations.pkl"), "wb") as f:
    pickle.dump(station_inventory, f)

# %% Process to DataFrame

with open(REQUESTS_BASE_DIR.joinpath("stations.pkl"), "rb") as f:
    inventory = pickle.load(f)

station_rows = []
channel_rows = []
for network in inventory:
    for station in network:
        station_rows.append(
            {
                "network_code": network.code,
                "station_code": station.code,
                "station_name": station.site.name,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "elevation_m": station.elevation,
                "total_channels": station.total_number_of_channels,
                "start_date": station.start_date.datetime
                if station.start_date
                else None,
                "end_date": station.end_date.datetime if station.end_date else None,
                "description": station.description,
                "restricted_status": station.restricted_status,
            }
        )

        for channel in station.channels:
            channel_rows.append(
                {
                    "network_code": network.code,
                    "station_code": station.code,
                    "channel_code": channel.code,
                    "location_code": channel.location_code,
                    "active": channel.is_active(),
                    "start_date": channel.start_date.datetime
                    if channel.start_date
                    else None,
                    "end_date": channel.end_date.datetime if channel.end_date else None,
                    "sample_rate": channel.sample_rate,
                    "azimuth": channel.azimuth,
                    "depth": channel.depth,
                    "dip": channel.dip,
                    "restricted_status": channel.restricted_status,
                }
            )

station_df = pd.DataFrame(station_rows)
station_df["start_date"] = pd.to_datetime(station_df["start_date"], utc=True)
station_df["end_date"] = pd.to_datetime(station_df["end_date"], utc=True)
station_df.to_parquet("../data/stations.parquet", index=False)
print(station_df)

channel_df = pd.DataFrame(channel_rows)
channel_df["start_date"] = pd.to_datetime(channel_df["start_date"], utc=True)
channel_df["end_date"] = pd.to_datetime(channel_df["end_date"], utc=True)
channel_df.to_parquet("../data/channels.parquet", index=False)
print(channel_df)


# %%
