export const VIEW = { width: 1200, height: 900, pad: { left: 76, right: 46, top: 55, bottom: 82 } };

// Ported from ml-bench: try near each anchor before growing an expanding ring.
export const RINGS = [[0, -1], [0, 1], [-1, 0], [1, 0], [-1, -1], [1, -1], [-1, 1], [1, 1]];
export const LABEL_STEPS = [22, 34, 48, 64, 82, 104, 130, 160, 196];

export const box = (cx, cy, width, height) => ({ cx, cy, width, height });
export const hits = (a, b) => Math.abs(a.cx - b.cx) * 2 < a.width + b.width && Math.abs(a.cy - b.cy) * 2 < a.height + b.height;
export const inside = (candidate, bounds) => candidate.cx - candidate.width / 2 >= bounds.left &&
  candidate.cx + candidate.width / 2 <= bounds.right && candidate.cy - candidate.height / 2 >= bounds.top &&
  candidate.cy + candidate.height / 2 <= bounds.bottom;

export function projectGeometry(data) {
  const points = [...data.countries, ...data.models];
  const minX = Math.min(...points.map(point => point.x));
  const maxX = Math.max(...points.map(point => point.x));
  const minY = Math.min(...points.map(point => point.y));
  const maxY = Math.max(...points.map(point => point.y));
  const xMargin = (maxX - minX) * 0.17;
  const yMargin = (maxY - minY) * 0.17;
  const limits = { x0: minX - xMargin, x1: maxX + xMargin, y0: minY - yMargin, y1: maxY + yMargin * 1.22 };
  const bounds = { left: VIEW.pad.left, right: VIEW.width - VIEW.pad.right, top: VIEW.pad.top, bottom: VIEW.height - VIEW.pad.bottom };
  const x = value => bounds.left + (value - limits.x0) / (limits.x1 - limits.x0) * (bounds.right - bounds.left);
  const y = value => bounds.bottom - (value - limits.y0) / (limits.y1 - limits.y0) * (bounds.bottom - bounds.top);
  return { x, y, bounds, limits };
}

function labelSize(text, kind) {
  const font = kind === 'zone' ? 15 : kind === 'model' ? 13 : 11;
  return { width: text.length * font * 0.59 + 10, height: font + 7 };
}

export function placeLabels(data, geometry) {
  const { x, y, bounds } = geometry;
  const taken = [
    ...data.countries.map(point => box(x(point.x), y(point.y), 10, 10)),
    ...data.models.map(point => box(x(point.x), y(point.y), 22, 22)),
  ];
  const labels = [
    ...data.models.filter(point => point.label).map(point => ({ id: `model:${point.name}`, point, text: point.label, kind: 'model' })),
    ...data.countries.filter(point => point.label).map(point => ({ id: `country:${point.name}`, point, text: point.name, kind: 'country' })),
    ...data.zone_hulls.map(zone => ({ id: `zone:${zone.name}`, point: { x: zone.label_anchor[0], y: zone.label_anchor[1] }, text: zone.name, kind: 'zone' })),
  ];
  const placements = {};
  for (const label of labels) {
    const anchor = { x: x(label.point.x), y: y(label.point.y) };
    const size = labelSize(label.text, label.kind);
    let found = null;
    for (const step of LABEL_STEPS) {
      for (const [dx, dy] of RINGS) {
        const candidate = box(anchor.x + dx * (step + size.width / 3), anchor.y + dy * step, size.width, size.height);
        if (inside(candidate, bounds) && !taken.some(obstacle => hits(candidate, obstacle))) {
          found = candidate;
          break;
        }
      }
      if (found) break;
    }
    if (!found) throw new Error(`no collision-free label location for ${label.id}`);
    placements[label.id] = { ...found, anchor, kind: label.kind, text: label.text };
    taken.push(found);
  }
  return placements;
}

export function roundedHull(points, geometry) {
  const p = points.slice(0, -1).map(([x, y]) => ({ x: geometry.x(x), y: geometry.y(y) }));
  if (p.length < 3) throw new Error('a closed hull needs three points');
  const at = index => p[(index + p.length) % p.length];
  const distance = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
  const toward = (a, b, amount) => ({ x: a.x + (b.x - a.x) * amount, y: a.y + (b.y - a.y) * amount });
  const corner = index => {
    const previous = at(index - 1), current = at(index), next = at(index + 1);
    const radius = Math.min(0.24, 14 / distance(previous, current), 14 / distance(current, next));
    return { before: toward(current, previous, radius), current, after: toward(current, next, radius) };
  };
  const first = corner(0);
  let path = `M ${first.after.x} ${first.after.y}`;
  for (let index = 1; index <= p.length; index += 1) {
    const c = corner(index % p.length);
    path += ` L ${c.before.x} ${c.before.y} Q ${c.current.x} ${c.current.y} ${c.after.x} ${c.after.y}`;
  }
  return `${path} Z`;
}

export function assertLayout(data) {
  const geometry = projectGeometry(data);
  const labels = placeLabels(data, geometry);
  const entries = Object.entries(labels);
  for (const [id, candidate] of entries) {
    if (!inside(candidate, geometry.bounds)) throw new Error(`label out of bounds: ${id}`);
  }
  for (let i = 0; i < entries.length; i += 1) {
    for (let j = i + 1; j < entries.length; j += 1) {
      if (hits(entries[i][1], entries[j][1])) throw new Error(`label overlap: ${entries[i][0]}, ${entries[j][0]}`);
    }
  }
  return { labels, geometry };
}
