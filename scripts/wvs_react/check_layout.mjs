import fs from 'node:fs';
import { assertLayout } from './src/layout.js';

const path = process.argv[2] ?? '../../docs/wvs/wvs_map_data.json';
const data = JSON.parse(fs.readFileSync(path));
const { labels, geometry } = assertLayout(data);
const kinds = Object.values(labels).reduce((count, label) => ({ ...count, [label.kind]: (count[label.kind] ?? 0) + 1 }), {});
console.log(JSON.stringify({
  labels: Object.keys(labels).length,
  kinds,
  bounds: geometry.bounds,
  policy: 'expanding rings, increasing steps, marker obstacles, pairwise overlap and bounds assertions',
}, null, 2));
