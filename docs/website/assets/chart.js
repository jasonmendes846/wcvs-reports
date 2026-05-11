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
  const padding = { top: 10, right: 10, bottom: 20, left: 30 };
  const chartW = width - padding.left - padding.right;
  const chartH = height - padding.top - padding.bottom;

  const scores = data.map(d => d.score);
  const minScore = Math.min(...scores, 1);
  const maxScore = Math.max(...scores, 5);
  const range = maxScore - minScore || 1;

  function x(i) { return padding.left + (i / (data.length - 1)) * chartW; }
  function y(score) { return padding.top + chartH - ((score - minScore) / range) * chartH; }

  // Grid lines
  ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--border').trim() || '#e0e0e0';
  ctx.lineWidth = 1;
  for (let s = Math.ceil(minScore); s <= Math.floor(maxScore); s++) {
    ctx.beginPath();
    ctx.moveTo(padding.left, y(s));
    ctx.lineTo(width - padding.right, y(s));
    ctx.stroke();
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim() || '#555';
    ctx.font = '10px sans-serif';
    ctx.fillText(s.toFixed(1), 0, y(s) + 3);
  }

  // Line
  ctx.beginPath();
  ctx.strokeStyle = '#1a3a5c';
  ctx.lineWidth = 2;
  data.forEach((d, i) => {
    if (i === 0) ctx.moveTo(x(i), y(d.score));
    else ctx.lineTo(x(i), y(d.score));
  });
  ctx.stroke();

  // Area fill
  ctx.beginPath();
  ctx.fillStyle = 'rgba(26, 58, 92, 0.1)';
  data.forEach((d, i) => {
    if (i === 0) ctx.moveTo(x(i), y(d.score));
    else ctx.lineTo(x(i), y(d.score));
  });
  ctx.lineTo(x(data.length - 1), padding.top + chartH);
  ctx.lineTo(padding.left, padding.top + chartH);
  ctx.closePath();
  ctx.fill();

  // Points
  data.forEach((d, i) => {
    ctx.beginPath();
    ctx.fillStyle = d.score <= 2 ? '#cc3333' : d.score <= 3 ? '#ff9933' : '#66aa66';
    ctx.arc(x(i), y(d.score), 3, 0, Math.PI * 2);
    ctx.fill();
  });

  // X labels (every 5th)
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--text-secondary').trim() || '#555';
  ctx.font = '10px sans-serif';
  data.forEach((d, i) => {
    if (i % 5 === 0 || i === data.length - 1) {
      const label = d.date.slice(5); // MM-DD
      ctx.fillText(label, x(i) - 12, height - 4);
    }
  });
}
