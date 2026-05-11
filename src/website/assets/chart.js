function renderSparkline(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !data || data.length === 0) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 20, right: 20, bottom: 30, left: 40 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const scores = data.map(d => d.score);
  const minScore = Math.min(...scores, 1);
  const maxScore = Math.max(...scores, 5);
  const range = maxScore - minScore || 1;

  function x(i) { return padding.left + (i / (data.length - 1)) * chartW; }
  function y(score) { return padding.top + chartH - ((score - minScore) / range) * chartH; }

  // Clear
  ctx.clearRect(0, 0, width, height);

  // Grid lines (subtle)
  ctx.strokeStyle = 'rgba(255,255,255,0.04)';
  ctx.lineWidth = 1;
  for (let s = Math.ceil(minScore); s <= Math.floor(maxScore); s++) {
    ctx.beginPath();
    ctx.moveTo(padding.left, y(s));
    ctx.lineTo(width - padding.right, y(s));
    ctx.stroke();
    ctx.fillStyle = 'rgba(136,146,160,0.5)';
    ctx.font = '11px SF Mono, Monaco, monospace';
    ctx.textAlign = 'right';
    ctx.fillText(s.toFixed(1), padding.left - 8, y(s) + 3);
  }

  // Gradient fill under line
  const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
  gradient.addColorStop(0, 'rgba(59, 130, 246, 0.15)');
  gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

  ctx.beginPath();
  ctx.moveTo(x(0), y(data[0].score));
  for (let i = 1; i < data.length; i++) {
    const xc = (x(i - 1) + x(i)) / 2;
    const yc = (y(data[i - 1].score) + y(data[i].score)) / 2;
    ctx.quadraticCurveTo(x(i - 1), y(data[i - 1].score), xc, yc);
  }
  ctx.lineTo(x(data.length - 1), y(data[data.length - 1].score));
  ctx.lineTo(x(data.length - 1), padding.top + chartH);
  ctx.lineTo(x(0), padding.top + chartH);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // Smooth line
  ctx.beginPath();
  ctx.strokeStyle = '#3b82f6';
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.shadowColor = 'rgba(59, 130, 246, 0.4)';
  ctx.shadowBlur = 12;
  ctx.moveTo(x(0), y(data[0].score));
  for (let i = 1; i < data.length; i++) {
    const xc = (x(i - 1) + x(i)) / 2;
    const yc = (y(data[i - 1].score) + y(data[i].score)) / 2;
    ctx.quadraticCurveTo(x(i - 1), y(data[i - 1].score), xc, yc);
  }
  ctx.lineTo(x(data.length - 1), y(data[data.length - 1].score));
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Points with glow
  data.forEach((d, i) => {
    const px = x(i);
    const py = y(d.score);

    // Outer glow
    ctx.beginPath();
    ctx.arc(px, py, 8, 0, Math.PI * 2);
    ctx.fillStyle = d.score <= 2 ? 'rgba(239, 68, 68, 0.2)' : d.score <= 3 ? 'rgba(249, 115, 22, 0.2)' : 'rgba(34, 197, 94, 0.2)';
    ctx.fill();

    // Inner point
    ctx.beginPath();
    ctx.arc(px, py, 4, 0, Math.PI * 2);
    ctx.fillStyle = d.score <= 2 ? '#ef4444' : d.score <= 3 ? '#f97316' : '#22c55e';
    ctx.fill();

    // White center
    ctx.beginPath();
    ctx.arc(px, py, 2, 0, Math.PI * 2);
    ctx.fillStyle = '#fff';
    ctx.fill();
  });

  // X labels (every few points)
  ctx.fillStyle = 'rgba(136,146,160,0.6)';
  ctx.font = '11px SF Mono, Monaco, monospace';
  ctx.textAlign = 'center';
  data.forEach((d, i) => {
    if (i % Math.ceil(data.length / 6) === 0 || i === data.length - 1) {
      const label = d.date.slice(5);
      ctx.fillText(label, x(i), height - 8);
    }
  });

  // Current value label (last point)
  const last = data[data.length - 1];
  const lx = x(data.length - 1);
  const ly = y(last.score);
  ctx.fillStyle = '#f0f2f5';
  ctx.font = 'bold 13px SF Mono, Monaco, monospace';
  ctx.textAlign = 'right';
  ctx.fillText(last.score.toFixed(1), lx - 12, ly - 12);
}
