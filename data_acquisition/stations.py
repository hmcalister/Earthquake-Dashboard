# %% Imports

import pathlib
import sqlite3

import aiosql
from obspy.clients.fdsn import Client

DATABASE = pathlib.Path("../data/earthquakes.sqlite")
QUERIES_FILE = pathlib.Path("../data/queries.sql")

queries = aiosql.from_path(QUERIES_FILE, "sqlite3")

# %% Make Requests

client = Client("GEONET")
station_inventory = client.get_stations(level="channel")
if station_inventory is None:
    print("client did not respond")
    exit()

# %% Process and Write to Database

station_rows = []
channel_rows = []
for network in station_inventory:
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
                "start_date": station.start_date.datetime.isoformat()
                if station.start_date
                else None,
                "end_date": station.end_date.datetime.isoformat()
                if station.end_date
                else None,
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
                    "active": 1 if channel.is_active() else 0,
                    "start_date": channel.start_date.datetime.isoformat()
                    if channel.start_date
                    else None,
                    "end_date": channel.end_date.datetime.isoformat()
                    if channel.end_date
                    else None,
                    "sample_rate": channel.sample_rate,
                    "azimuth": channel.azimuth,
                    "depth": channel.depth,
                    "dip": channel.dip,
                    "restricted_status": channel.restricted_status,
                }
            )

with sqlite3.connect(DATABASE) as conn:
    queries.upsert_station(conn, station_rows)
    queries.upsert_channel(conn, channel_rows)

print(f"Upserted {len(station_rows)} stations and {len(channel_rows)} channels")

# %%
