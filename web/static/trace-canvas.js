export function drawTrace(canvas, data, startTime, endTime) {
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = rect.height;

  const marginL = 52;
  const marginB = 18;
  const marginT = 10;
  const marginR = 4;
  const plotW = w - marginL - marginR;
  const plotH = h - marginT - marginB;

  // Symmetric Y axis centred on 0: range is [-peak, +peak]
  const peak =
    Math.max(Math.abs(Math.min(...data)), Math.abs(Math.max(...data))) || 1;
  const toY = (v) => marginT + (1 - (v + peak) / (2 * peak)) * plotH;

  const axisColor = getComputedStyle(document.documentElement).getPropertyValue(
    "--text-color-light",
  );
  ctx.font = "10px system-ui, sans-serif";
  ctx.strokeStyle = axisColor;
  ctx.fillStyle = axisColor;
  ctx.lineWidth = 1;

  // Y axis
  ctx.beginPath();
  ctx.moveTo(marginL, marginT);
  ctx.lineTo(marginL, marginT + plotH);
  ctx.stroke();

  // X axis
  ctx.beginPath();
  ctx.moveTo(marginL, marginT + plotH);
  ctx.lineTo(marginL + plotW, marginT + plotH);
  ctx.stroke();

  // Y axis ticks and labels: +peak, 0, -peak
  [peak, 0, -peak].forEach((v) => {
    const y = toY(v);
    ctx.beginPath();
    ctx.moveTo(marginL - 3, y);
    ctx.lineTo(marginL, y);
    ctx.stroke();
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.fillText(v === 0 ? "0" : v.toExponential(1), marginL - 8, y);
  });

  // X axis labels: start and end time (HH:MM:SS)
  const fmtTime = (iso) => iso.slice(11, 19);
  ctx.textBaseline = "top";
  ctx.textAlign = "left";
  ctx.fillText(fmtTime(startTime), marginL, marginT + plotH + 3);
  ctx.textAlign = "right";
  ctx.fillText(fmtTime(endTime), marginL + plotW, marginT + plotH + 3);

  // Trace
  ctx.strokeStyle = "#2a8a9a";
  ctx.beginPath();
  data.forEach((v, i) => {
    const x = marginL + (i / (data.length - 1)) * plotW;
    const y = toY(v);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.stroke();
}
