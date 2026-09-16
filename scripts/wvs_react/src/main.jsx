import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';

const hull = points => {
  const p = [...points].sort((a, b) => a.x - b.x || a.y - b.y);
  const cross = (o, a, b) => (a.x-o.x)*(b.y-o.y) - (a.y-o.y)*(b.x-o.x);
  const half = xs => { const out = []; for (const point of xs) { while (out.length > 1 && cross(out.at(-2), out.at(-1), point) <= 0) out.pop(); out.push(point); } return out; };
  return [...half(p), ...half([...p].reverse()).slice(1, -1)];
};

function Map({ data }) {
  const [hidden, setHidden] = useState(() => new Set(new URLSearchParams(location.search).get('hide')?.split(',').filter(Boolean)));
  const all = [...data.countries, ...data.models];
  const [minX, maxX] = [Math.min(...all.map(p => p.x)), Math.max(...all.map(p => p.x))];
  const [minY, maxY] = [Math.min(...all.map(p => p.y)), Math.max(...all.map(p => p.y))];
  const x = v => 70 + (v-minX)/(maxX-minX)*860, y = v => 650 - (v-minY)/(maxY-minY)*580;
  const groups = useMemo(() => Object.groupBy(data.models, model => model.family), [data]);
  const offsets = { grok:{dx:-72,dy:-30}, muse:{dx:12,dy:-11}, mistral:{dx:-96,dy:-26}, llama:{dx:-96,dy:12} };
  return <><div className="controls">{Object.entries(groups).map(([family, models]) => <button key={family} className={hidden.has(family) ? 'off' : ''} style={{'--color': models[0].color}} onClick={() => setHidden(old => { const next = new Set(old); next.has(family) ? next.delete(family) : next.add(family); return next; })}>{family}: {data.latest_by_family[family].name}</button>)}</div>
  <svg viewBox="0 0 1000 720" aria-label="React WVS cultural map"><line x1="70" y1={y(data.median.y)} x2="930" y2={y(data.median.y)} className="axis"/><line x1={x(data.median.x)} y1="70" x2={x(data.median.x)} y2="650" className="axis"/>
    {Object.entries(data.zones).map(([name, names]) => { const h=hull(data.countries.filter(p=>names.includes(p.name))); const c=h.reduce((s,p)=>({x:s.x+p.x/h.length,y:s.y+p.y/h.length}),{x:0,y:0}); return <g key={name}><polygon points={h.map(p=>`${x(p.x)},${y(p.y)}`).join(' ')} className="zone"/><text x={x(c.x)} y={y(c.y)} className="zoneLabel">{name}</text></g>; })}
    {data.countries.map(p => <circle key={p.name} cx={x(p.x)} cy={y(p.y)} r="3" className="country"><title>{p.name}</title></circle>)}
    {Object.entries(groups).map(([family, models]) => <g key={family} display={hidden.has(family) ? 'none' : 'inline'}>{models.map(p => { const o=offsets[family] ?? {dx:11,dy:-11}; return <g key={p.name}><path d={`M ${x(p.x)} ${y(p.y)-8} L ${x(p.x)+2.4} ${y(p.y)-2.4} L ${x(p.x)+8} ${y(p.y)-2.4} L ${x(p.x)+3.6} ${y(p.y)+1.6} L ${x(p.x)+5.2} ${y(p.y)+7} L ${x(p.x)} ${y(p.y)+4} L ${x(p.x)-5.2} ${y(p.y)+7} L ${x(p.x)-3.6} ${y(p.y)+1.6} L ${x(p.x)-8} ${y(p.y)-2.4} L ${x(p.x)-2.4} ${y(p.y)-2.4} Z`} fill={p.color} className="star"><title>{p.name}</title></path>{p.label && <><line x1={x(p.x)} y1={y(p.y)} x2={x(p.x)+o.dx*.82} y2={y(p.y)+o.dy*.82} stroke={p.color}/><text x={x(p.x)+o.dx} y={y(p.y)+o.dy} fill={p.color} className="modelLabel">{p.label}</text></>}</g>; })}</g>)}
    <text x="70" y="690" className="axisLabel">{data.axis.x[0]}</text><text x="930" y="690" textAnchor="end" className="axisLabel">{data.axis.x[1]}</text><text x="500" y="30" textAnchor="middle" className="axisLabel">{data.axis.y[1]}</text><text x="500" y="710" textAnchor="middle" className="axisLabel">{data.axis.y[0]}</text>
  </svg></>;
}
function App() { const [data, setData] = useState(null); useEffect(() => { fetch('../wvs_map_data.json').then(r=>r.json()).then(setData); }, []); return <main><h1>Frontier LLMs on the World Values Survey</h1><p>React/SVG renderer using the shared WVS coordinate artifact. Filled chips show a family; outlined chips hide its stars and latest label.</p>{data && <Map data={data}/>}</main>; }
createRoot(document.getElementById('root')).render(<App/>);
