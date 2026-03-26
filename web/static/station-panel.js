import { drawTrace } from "./trace-canvas.js";

const stationPanel = document.getElementById("station-panel");
const panelTitle = document.getElementById("station-panel-title");
const panelSubtitle = document.getElementById("station-panel-subtitle");
const panelMeasuredAt = document.getElementById("station-panel-measured-at");
const panelBody = document.getElementById("station-panel-body");

document
  .getElementById("station-panel-close")
  .addEventListener("click", () => closeStationPanel());

export function closeStationPanel() {
  stationPanel.classList.remove("open");
  history.replaceState(null, "", location.pathname + location.search);
}

export function openStationPanel(s) {
  history.replaceState(
    null,
    "",
    `#station=${encodeURIComponent(s.station_code)}`,
  );
  stationPanel.classList.add("open");
  panelTitle.textContent = `${s.station_code} — ${s.station_name}`;
  panelSubtitle.textContent = `${s.latitude.toFixed(4)}, ${s.longitude.toFixed(4)}  ·  ${s.elevation_m} m`;
  panelMeasuredAt.textContent = "";
  panelBody.innerHTML = `<em style="color:var(--text-color-light-secondary)">Loading readings…</em>`;

  fetch(`/api/stations/${s.station_code}/readings`)
    .then((r) => r.json())
    .then((data) => {
      if (data.error) {
        panelBody.innerHTML = `<p style="color:var(--text-color-light-secondary)">${data.error}</p>`;
        return;
      }
      panelMeasuredAt.textContent = `Measured At: ${data.measured_at} UTC`;
      panelBody.innerHTML = "";
      data.traces.forEach((t) => {
        const block = document.createElement("div");
        block.className = "channel-block";

        const label = document.createElement("div");
        label.className = "channel-label";
        label.textContent = `${t.channel}  ·  ${t.sampling_rate} Hz`;

        const canvas = document.createElement("canvas");
        canvas.className = "channel-canvas";

        block.appendChild(label);
        block.appendChild(canvas);
        panelBody.appendChild(block);

        requestAnimationFrame(() =>
          drawTrace(canvas, t.data, t.start_time, t.end_time),
        );
      });
    })
    .catch(() => {
      panelBody.innerHTML = `<p style="color:var(--text-color-light-secondary)">Failed to load readings.</p>`;
    });
}
