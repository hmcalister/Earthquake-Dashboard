import { openStationPanel } from "./station-panel.js";

const map = L.map("map").setView([-41.5, 172.5], 5);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap",
    maxZoom: 18,
}).addTo(map);

const stationCluster = L.markerClusterGroup({
    maxClusterRadius: 40,
});

fetch("/api/stations")
    .then((r) => r.json())
    .then((stations) => {
        stations.forEach((s) => {
            L.circleMarker([s.latitude, s.longitude], {
                radius: 10,
                color: "#111",
                fillColor: "#2a8a9a",
                fillOpacity: 1.0,
                weight: 2.5,
            })
                .on("click", () => openStationPanel(s))
                .addTo(stationCluster);
        });
        map.addLayer(stationCluster);
    });
