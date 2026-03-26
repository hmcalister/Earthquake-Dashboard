import { openStationPanel, closeStationPanel } from "./station-panel.js";

const map = L.map("map").setView([-41.5, 172.5], 5);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap",
  maxZoom: 18,
}).addTo(map);

const stationCluster = L.markerClusterGroup({
  maxClusterRadius: 40,
});

const stationsByCode = {};
const markersByCode = {};
let activeMarker = null;

const defaultStyle = { fillColor: "#2a8a9a" };
const activeStyle = { fillColor: "#2a4a8a" };

function selectStation(code) {
  const s = stationsByCode[code];
  if (s) {
    if (activeMarker) activeMarker.setStyle(defaultStyle);
    activeMarker = markersByCode[code];
    activeMarker.setStyle(activeStyle);
    map.setView([s.latitude, s.longitude]);
    openStationPanel(s);
  }
}

function applyHash() {
  const match = location.hash.match(/^#station=(.+)$/);
  if (match) {
    selectStation(decodeURIComponent(match[1]));
  } else {
    if (activeMarker) {
      activeMarker.setStyle(defaultStyle);
      activeMarker = null;
    }
    closeStationPanel();
  }
}

window.addEventListener("hashchange", applyHash);

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
        weight: 2.5,
      }).on("click", () => selectStation(s.station_code));
      markersByCode[s.station_code] = marker;
      marker.addTo(stationCluster);
    });
    map.addLayer(stationCluster);
    applyHash();
  });
