const utcClock = document.getElementById("utc-clock");

function updateClock() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    utcClock.textContent =
        `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())} ` +
        `${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())} UTC`;
}

updateClock();
setInterval(updateClock, 1000);
