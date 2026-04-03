import { openStationPanel, resetStationPanel } from "./station-panel.js";
import { openEventPanel, resetEventPanel, magnitudeColor } from "./event-panel.js";

const map = L.map("map").setView([-41.5, 172.5], 5);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap",
  maxZoom: 18,
}).addTo(map);

const stationPanel = document.getElementById("station-panel");
const eventPanel = document.getElementById("event-panel");
const navStations = document.getElementById("nav-stations");
const navEvents = document.getElementById("nav-events");

function getMode() {
  return new URLSearchParams(location.search).get("mode") === "events"
    ? "events"
    : "stations";
}

function applyMode() {
  const mode = getMode();
  if (mode === "events") {
    stationPanel.style.display = "none";
    eventPanel.style.display = "flex";
    navEvents.classList.add("nav-active");
    navStations.classList.remove("nav-active");
    if (map.hasLayer(stationCluster)) map.removeLayer(stationCluster);
    if (!map.hasLayer(eventMarkers)) map.addLayer(eventMarkers);
  } else {
    eventPanel.style.display = "none";
    stationPanel.style.display = "flex";
    navStations.classList.add("nav-active");
    navEvents.classList.remove("nav-active");
    if (map.hasLayer(eventMarkers)) map.removeLayer(eventMarkers);
    if (!map.hasLayer(stationCluster)) map.addLayer(stationCluster);
  }
}

// ----------------------------------------------------------------------------
// Stations

const stationCluster = L.markerClusterGroup({ maxClusterRadius: 40 });
const stationsByCode = {};
const stationMarkersByCode = {};
let activeStationMarker = null;

const defaultStationStyle = { fillColor: "#2a8a9a" };
const activeStationStyle = { fillColor: "#2a4a8a" };

function selectStation(stationCode) {
  const s = stationsByCode[stationCode];
  if (!s) return;
  if (activeStationMarker) activeStationMarker.setStyle(defaultStationStyle);
  activeStationMarker = stationMarkersByCode[stationCode];
  activeStationMarker.setStyle(activeStationStyle);
  openStationPanel(s);
  map.setView([s.latitude, s.longitude]);
}

function applyStationURLParam() {
  const stationCode = new URLSearchParams(location.search).get("station");
  if (stationCode) {
    selectStation(decodeURIComponent(stationCode));
  } else {
    if (activeStationMarker) {
      activeStationMarker.setStyle(defaultStationStyle);
      activeStationMarker = null;
    }
    resetStationPanel();
  }
}

fetch("/api/stations")
  .then((r) => r.json())
  .then((stations) => {
    stations.forEach((s) => {
      stationsByCode[s.station_code] = s;
      const marker = L.circleMarker([s.latitude, s.longitude], {
        radius: 10,
        color: "#111",
        fillColor: "#2a8a9a",
        fillOpacity: 1.0,
        weight: 1.5,
      }).on("click", () => selectStation(s.station_code));
      stationMarkersByCode[s.station_code] = marker;
      marker.addTo(stationCluster);
    });
    applyMode();
    if (getMode() === "stations") applyStationURLParam();
  });

// ----------------------------------------------------------------------------
// Events

const eventMarkers = L.layerGroup();
const eventMarkersByID = {};
const eventsByShortID = {};
let activeEventMarker = null;

function eventShortID(eventId) {
  return eventId.split("/").pop();
}

function applyEventURLParam() {
  const shortId = new URLSearchParams(location.search).get("event");
  if (shortId && eventsByShortID[shortId]) {
    selectEvent(eventsByShortID[shortId]);
  }
}

function selectEvent(eventId) {
  const marker = eventMarkersByID[eventId];
  if (!marker) return;
  if (activeEventMarker) {
    activeEventMarker.closeTooltip();
    activeEventMarker.closePopup();
  }
  activeEventMarker = marker;
  map.setView(marker.getLatLng());
  marker.openPopup();

  const params = new URLSearchParams(location.search);
  params.set("event", eventShortID(eventId));
  history.replaceState(null, "", "?" + params.toString());
}

const timeframeSelect = document.getElementById("event-timeframe");

function loadEvents(timeframe) {
  eventMarkers.clearLayers();
  Object.keys(eventMarkersByID).forEach((k) => delete eventMarkersByID[k]);
  Object.keys(eventsByShortID).forEach((k) => delete eventsByShortID[k]);
  activeEventMarker = null;

  const params = new URLSearchParams(location.search);
  params.set("timeframe", timeframe);
  history.replaceState(null, "", "?" + params.toString());

  fetch(`/api/events?timeframe=${timeframe}`)
    .then((r) => r.json())
    .then((events) => {
      events.forEach((e) => {
        const event_string = String(`
          Event ID: ${e.event_id} <br>
          Datetime: ${e.datetime}UTC <br>
          Magnitude: ${e.magnitude.toFixed(1)} <br>
          Location: ${e.latitude.toFixed(5)}, ${e.longitude.toFixed(5)} <br>
          Depth: ${(e.depth_m / 1000).toFixed(2)} km <br>
        `).trim();

        if (e.longitude < 0) {
          e.longitude += 360;
        }
        const marker = L.circleMarker([e.latitude, e.longitude], {
          radius: Math.max(5, e.magnitude * 3),
          color: "#111",
          fillColor: magnitudeColor(e.magnitude),
          fillOpacity: 0.8,
          weight: 1.5,
        })
          .bindTooltip(event_string)
          .bindPopup(event_string)
          .on("click", () => selectEvent(e.event_id));
        eventsByShortID[eventShortID(e.event_id)] = e.event_id;
        eventMarkersByID[e.event_id] = marker;
        marker.addTo(eventMarkers);
      });
      openEventPanel(events, (eventId) => selectEvent(eventId));
      applyMode();
      applyEventURLParam();
    });
}

timeframeSelect.addEventListener("change", () => loadEvents(timeframeSelect.value));

const initialTimeframe = new URLSearchParams(location.search).get("timeframe") || "1h";
timeframeSelect.value = initialTimeframe;
loadEvents(initialTimeframe);

window.addEventListener("popstate", () => {
  if (getMode() === "stations") applyStationURLParam();
  if (getMode() === "events") applyEventURLParam();
});
