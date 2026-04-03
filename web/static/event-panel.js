const panelSubtitle = document.getElementById("event-panel-subtitle");
const panelBody = document.getElementById("event-panel-body");

let activeRow = null;

export function resetEventPanel() {
  panelSubtitle.textContent = "";
  panelBody.innerHTML = "";
  activeRow = null;
}

export function getEventDescriptionString(event) {
  return String(`
    Event ID: ${event.event_id} <br>
    Datetime: ${event.datetime.split('.')[0]} UTC <br>
    Magnitude: ${event.magnitude.toFixed(1)} <br>
    Location: ${event.latitude.toFixed(5)}, ${event.longitude.toFixed(5)} <br>
    Depth: ${(event.depth_m / 1000).toFixed(2)} km <br>
  `).trim();
}

export function openEventPanel(events, onSelect) {
  activeRow = null;

  if (events.length === 0) {
    panelSubtitle.textContent = "";
    panelBody.innerHTML = `<p style="color:var(--text-color-light-secondary)">No events in the selected timeframe.</p>`;
    return;
  }

  panelSubtitle.textContent = `${events.length} event${events.length === 1 ? "" : "s"} found`;
  panelBody.innerHTML = "";

  events.forEach((e) => {
    const row = document.createElement("div");
    row.className = "event-row";
    row.addEventListener("click", () => {
      if (activeRow) activeRow.classList.remove("event-row-active");
      activeRow = row;
      row.classList.add("event-row-active");
      onSelect(e.event_id);
    });

    const mag = document.createElement("div");
    mag.className = "event-magnitude";
    mag.textContent = e.magnitude.toFixed(1);
    mag.dataset.magClass = magnitudeClass(e.magnitude);

    const info = document.createElement("div");
    info.className = "event-info";

    const event_id_header = document.createElement("div");
    event_id_header.className = "event-id-header";
    event_id_header.textContent = `Event ID: ${e.event_id}`;

    const detail = document.createElement("div");
    detail.className = "event-detail";
    detail.innerHTML = `Datetime: ${e.datetime.split('.')[0]} UTC<br>Location: ${e.latitude.toFixed(5)}, ${e.longitude.toFixed(5)}<br>Depth: ${(e.depth_m / 1000).toFixed(2)} km`;

    info.appendChild(event_id_header);
    info.appendChild(detail);
    row.appendChild(mag);
    row.appendChild(info);
    panelBody.appendChild(row);
  });
}

export function magnitudeClass(mag) {
  if (mag >= 5) return "major";
  if (mag >= 3) return "moderate";
  return "minor";
}

export function magnitudeColor(mag) {
  if (mag >= 5) return "#e74c3c";
  if (mag >= 3) return "#e67e22";
  return "#f1c40f";
}
