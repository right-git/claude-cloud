// Layout linter for 1080×1920 compositions (HyperFrames / any HTML render).
// Load into the page at a scene's rest frame, then call window.__layoutLint().
// Expected result: [] — any entry means the scene is not ready.
//
// Markup contract:
//   data-box="name"     every visible block that must respect the grid
//   data-pad="48"       container: minimum inner padding for its data-box children
//   data-overlay="1"    modal/overlay allowed to overlap other blocks
//
// Options: window.__layoutLint({ left: 64, right: 1016 })
window.__layoutLint = (opts = {}) => {
  const L = opts.left ?? 64, R = opts.right ?? 1016, out = [];
  const visible = (e) => {
    const s = getComputedStyle(e);
    return s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > 0.05;
  };
  const boxes = [...document.querySelectorAll('[data-box]')].filter(visible);

  for (const e of boxes) {
    const r = e.getBoundingClientRect(), n = e.dataset.box;
    if (r.left < L - 1 || r.right > R + 1) out.push(`margin: ${n} ${r.left | 0}–${r.right | 0}`);
    if (e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1) out.push(`overflow: ${n}`);
    const p = e.parentElement && e.parentElement.closest('[data-box]');
    if (p) {
      const q = p.getBoundingClientRect(), pad = +(p.dataset.pad || 0);
      if (r.left - q.left < pad - 1 || q.right - r.right < pad - 1 ||
          r.top - q.top < pad - 1 || q.bottom - r.bottom < pad - 1) {
        out.push(`padding: ${n} in ${p.dataset.box} (min ${pad})`);
      }
    }
  }

  for (let i = 0; i < boxes.length; i++) {
    for (let j = i + 1; j < boxes.length; j++) {
      const a = boxes[i], b = boxes[j];
      if (a.contains(b) || b.contains(a) || a.dataset.overlay || b.dataset.overlay) continue;
      const x = a.getBoundingClientRect(), y = b.getBoundingClientRect();
      if (x.left < y.right - 1 && y.left < x.right - 1 && x.top < y.bottom - 1 && y.top < x.bottom - 1) {
        out.push(`overlap: ${a.dataset.box} × ${b.dataset.box}`);
      }
    }
  }
  return out;
};
