CREATE TABLE IF NOT EXISTS earthquakes (
    event_id        TEXT PRIMARY KEY,
    datetime        DATETIME NOT NULL,
    latitude        REAL NOT NULL,
    longitude       REAL NOT NULL,
    depth_m         REAL NOT NULL,
    magnitude       REAL NOT NULL,
    magnitude_type  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stations (
    network_code        TEXT NOT NULL,
    station_code        TEXT NOT NULL,
    station_name        TEXT,
    latitude            REAL NOT NULL,
    longitude           REAL NOT NULL,
    elevation_m         REAL,
    total_channels      INTEGER,
    start_date          DATETIME,
    end_date            DATETIME,
    description         TEXT,
    restricted_status   TEXT,
    PRIMARY KEY (network_code, station_code)
);

CREATE TABLE IF NOT EXISTS channels (
    network_code        TEXT NOT NULL,
    station_code        TEXT NOT NULL,
    channel_code        TEXT NOT NULL,
    location_code       TEXT NOT NULL,
    active              INTEGER NOT NULL,
    start_date          DATETIME,
    end_date            DATETIME,
    sample_rate         REAL,
    azimuth             REAL,
    depth               REAL,
    dip                 REAL,
    restricted_status   TEXT,
    PRIMARY KEY (network_code, station_code, channel_code, location_code)
);

CREATE TABLE IF NOT EXISTS channel_waveforms (
    id              INTEGER PRIMARY KEY,
    network_code    TEXT NOT NULL,
    station_code    TEXT NOT NULL,
    channel_code    TEXT NOT NULL,
    location_code   TEXT NOT NULL,
    start_time      DATETIME NOT NULL,
    end_time        DATETIME NOT NULL,
    sample_rate     REAL NOT NULL,
    num_samples     INTEGER NOT NULL,
    waveform        BLOB NOT NULL,
    UNIQUE (network_code, station_code, channel_code, location_code)
);

CREATE INDEX IF NOT EXISTS idx_channel_waveforms_lookup
    ON channel_waveforms (network_code, station_code, channel_code, location_code);
