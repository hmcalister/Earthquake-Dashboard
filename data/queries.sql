-- name: upsert_station(network_code, station_code, station_name, latitude, longitude, elevation_m, total_channels, start_date, end_date, description, restricted_status)*!
-- :param network_code:
-- :param station_code:
-- :param station_name:
-- :param latitude:
-- :param longitude:
-- :param elevation_m:
-- :param total_channels:
-- :param start_date:
-- :param end_date:
-- :param description:
-- :param restricted_status:
INSERT INTO stations (network_code, station_code, station_name, latitude, longitude, elevation_m, total_channels, start_date, end_date, description, restricted_status)
VALUES (:network_code, :station_code, :station_name, :latitude, :longitude, :elevation_m, :total_channels, :start_date, :end_date, :description, :restricted_status)
ON CONFLICT(network_code, station_code) DO UPDATE SET
    station_name      = excluded.station_name,
    latitude          = excluded.latitude,
    longitude         = excluded.longitude,
    elevation_m       = excluded.elevation_m,
    total_channels    = excluded.total_channels,
    start_date        = excluded.start_date,
    end_date          = excluded.end_date,
    description       = excluded.description,
    restricted_status = excluded.restricted_status;

-- name: upsert_channel(network_code, station_code, channel_code, location_code, active, start_date, end_date, sample_rate, azimuth, depth, dip, restricted_status)*!
-- :param network_code:
-- :param station_code:
-- :param channel_code:
-- :param location_code:
-- :param active:
-- :param start_date:
-- :param end_date:
-- :param sample_rate:
-- :param azimuth:
-- :param depth:
-- :param dip:
-- :param restricted_status:
INSERT INTO channels (network_code, station_code, channel_code, location_code, active, start_date, end_date, sample_rate, azimuth, depth, dip, restricted_status)
VALUES (:network_code, :station_code, :channel_code, :location_code, :active, :start_date, :end_date, :sample_rate, :azimuth, :depth, :dip, :restricted_status)
ON CONFLICT(network_code, station_code, channel_code, location_code) DO UPDATE SET
    active            = excluded.active,
    start_date        = excluded.start_date,
    end_date          = excluded.end_date,
    sample_rate       = excluded.sample_rate,
    azimuth           = excluded.azimuth,
    depth             = excluded.depth,
    dip               = excluded.dip,
    restricted_status = excluded.restricted_status;

-- name: get_active_stations()
SELECT network_code, station_code, station_name, latitude, longitude, elevation_m
FROM stations
WHERE end_date IS NULL OR end_date > CURRENT_TIMESTAMP;

-- name: get_active_stations_with_target_channels()
SELECT DISTINCT s.network_code, s.station_code, s.station_name, s.latitude, s.longitude, s.elevation_m
FROM stations s
INNER JOIN channels c ON c.network_code = s.network_code AND c.station_code = s.station_code
WHERE (s.end_date IS NULL OR s.end_date > CURRENT_TIMESTAMP)
  AND c.active = 1
  AND c.channel_code IN ('HHZ', 'HHN', 'HHE', 'HNZ', 'HNN', 'HNE');

-- name: get_stations_with_readings()
SELECT DISTINCT s.network_code, s.station_code, s.station_name, s.latitude, s.longitude, s.elevation_m
FROM stations s
INNER JOIN channel_waveforms cw ON cw.station_code = s.station_code AND cw.network_code = s.network_code
WHERE s.end_date IS NULL OR s.end_date > CURRENT_TIMESTAMP;

-- name: upsert_channel_waveform(network_code, station_code, channel_code, location_code, start_time, end_time, sample_rate, num_samples, waveform)*!
-- :param network_code:
-- :param station_code:
-- :param channel_code:
-- :param location_code:
-- :param start_time: ISO 8601 start of this waveform chunk
-- :param end_time: ISO 8601 end of this waveform chunk
-- :param sample_rate:
-- :param num_samples:
-- :param waveform: zlib-compressed float32 numpy array bytes
INSERT INTO channel_waveforms (network_code, station_code, channel_code, location_code, start_time, end_time, sample_rate, num_samples, waveform)
VALUES (:network_code, :station_code, :channel_code, :location_code, :start_time, :end_time, :sample_rate, :num_samples, :waveform)
ON CONFLICT(network_code, station_code, channel_code, location_code) DO UPDATE SET
    start_time  = excluded.start_time,
    end_time    = excluded.end_time,
    sample_rate = excluded.sample_rate,
    num_samples = excluded.num_samples,
    waveform    = excluded.waveform;

-- name: get_station_waveforms(station_code)
-- :param station_code: Station code to fetch waveforms for
SELECT channel_code, location_code, start_time, end_time, sample_rate, num_samples, waveform
FROM channel_waveforms
WHERE station_code = :station_code
ORDER BY channel_code;

-- name: get_recent_earthquakes(interval)
-- :param interval: SQLite modifier string e.g. '-1 hour', '-24 hours', '-7 days'
SELECT event_id, datetime, latitude, longitude, depth_m, magnitude, magnitude_type
FROM earthquakes
WHERE datetime >= datetime('now', :interval)
ORDER BY datetime DESC;

-- name: insert_earthquake(event_id, datetime, latitude, longitude, depth_m, magnitude, magnitude_type)*!
-- :param event_id: The event resource ID
-- :param datetime: ISO 8601 event time
-- :param latitude:
-- :param longitude:
-- :param depth_m:
-- :param magnitude:
-- :param magnitude_type:
INSERT INTO earthquakes (event_id, datetime, latitude, longitude, depth_m, magnitude, magnitude_type)
VALUES (:event_id, :datetime, :latitude, :longitude, :depth_m, :magnitude, :magnitude_type)
ON CONFLICT(event_id) DO NOTHING;
