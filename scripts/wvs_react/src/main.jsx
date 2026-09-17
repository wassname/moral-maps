import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { VIEW, assertLayout, roundedHull } from './layout.js';
import './style.css';

function Tooltip({ active, geometry, data, id = 'model-tooltip' }) {
  if (!active) return null;
  const { provenance } = active;
  const left = active.tooltipLeft ?? `${Math.min(86, geometry.x(active.x) / VIEW.width * 100)}%`;
  const top = active.tooltipTop ?? `${Math.min(82, geometry.y(active.y) / VIEW.height * 100)}%`;
  const samples = provenance.items === null ? 'historical coordinate' : `${provenance.items} items x ${provenance.samples} samples`;
  return <aside id={id} className="tooltip" style={{ left, top }} role="status">
    <strong>{active.name}</strong>
    <span>{active.family}</span>
    <span>{data.axis.x[0]} {'->'} {data.axis.x[1]}: {active.x.toFixed(3)}</span>
    <span>{data.axis.y[0]} {'->'} {data.axis.y[1]}: {active.y.toFixed(3)}</span>
    <span>{provenance.readout}, {samples}</span>
    <span>{provenance.release_created ? `release ${provenance.release_created}` : provenance.release_source}</span>
  </aside>;
}

function ModelMarker({ model, placement, geometry, setActive, clearActive, markerRef, logo }) {
  const cx = geometry.x(model.x), cy = geometry.y(model.y);
  const label = model.label ? placement[`model:${model.name}`] : null;
  const leader = label && Math.hypot(label.cx - cx, label.cy - cy) > 20;
  return <g ref={markerRef} className="model-mark" data-family={model.family} data-model={model.name} data-x={model.x} data-y={model.y}
    tabIndex="0" role="button" aria-label={`${model.name}, ${model.family}`} aria-describedby="model-tooltip"
    onPointerEnter={() => setActive(model)} onPointerLeave={clearActive}
    onFocus={() => setActive(model)} onBlur={clearActive}>
    {leader && <line className="leader" x1={cx} y1={cy} x2={label.cx} y2={label.cy} />}
    <circle className="model-ring" cx={cx} cy={cy} r="11" stroke={model.color} />
    <image href={`../${logo}`} x={cx - 7} y={cy - 7} width="14" height="14" preserveAspectRatio="xMidYMid meet" />
    {label && <text className="model-label" x={label.cx} y={label.cy + 4} textAnchor="middle">{model.label}</text>}
  </g>;
}

function ReleaseScatter({ data, hidden, field, title }) {
  const dated = useMemo(() => data.models.filter(model => Number.isFinite(Date.parse(model.provenance.release_created ?? '')))
    .toSorted((a, b) => a.provenance.release_created.localeCompare(b.provenance.release_created) || a.name.localeCompare(b.name)), [data]);
  const [active, setActive] = useState(null);
  const width = 1200, height = 320, left = 74, right = 35, top = 42, bottom = 48;
  const dates = dated.map(model => Date.parse(model.provenance.release_created));
  const values = dated.map(model => model[field]);
  const minDate = Math.min(...dates), maxDate = Math.max(...dates);
  const minValue = Math.min(...values), maxValue = Math.max(...values);
  const dateX = date => left + (date - minDate) / (maxDate - minDate) * (width - left - right);
  const valueY = value => top + (maxValue - value) / (maxValue - minValue || 1) * (height - top - bottom);
  const activate = (model, event) => {
    const box = event.currentTarget.closest('.scatter-shell').getBoundingClientRect();
    const point = event.currentTarget.getBoundingClientRect();
    setActive({ ...model, tooltipLeft: `${Math.min(82, (point.left - box.left) / box.width * 100)}%`, tooltipTop: `${Math.min(78, (point.top - box.top) / box.height * 100)}%` });
  };
  return <section className="release-panel" data-coordinate={field} aria-labelledby={`release-${field}`}>
    <h2 id={`release-${field}`}>{title}</h2>
    <p>Dated releases only. Positions are descriptive, not a capability trend.</p>
    <div className="scatter-shell">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title} data-panel-model-count={dated.length}>
        <rect className="canvas" width={width} height={height} />
        <g className="scatter-grid">{Array.from({ length: 5 }, (_, index) => <line key={index} x1={left} x2={width - right} y1={top + index * (height - top - bottom) / 4} y2={top + index * (height - top - bottom) / 4} />)}</g>
        <line className="scatter-axis" x1={left} x2={width - right} y1={height - bottom} y2={height - bottom} />
        <line className="scatter-axis" x1={left} x2={left} y1={top} y2={height - bottom} />
        <text className="scatter-tick" x={left} y={height - 18}>{new Date(minDate).toISOString().slice(0, 10)}</text>
        <text className="scatter-tick" x={width - right} y={height - 18} textAnchor="end">{new Date(maxDate).toISOString().slice(0, 10)}</text>
        <text className="scatter-tick" x={left - 8} y={top + 4} textAnchor="end">{maxValue.toFixed(2)}</text>
        <text className="scatter-tick" x={left - 8} y={height - bottom} textAnchor="end">{minValue.toFixed(2)}</text>
        {dated.map(model => <g key={model.name} className="release-mark" data-family={model.family} data-release-model={model.name} data-release-date={model.provenance.release_created} display={hidden.has(model.family) ? 'none' : 'inline'}
          tabIndex="0" role="button" aria-label={`${model.name}, ${model.family}, ${model.provenance.release_created}`} aria-describedby="release-tooltip"
          onPointerEnter={event => activate(model, event)} onPointerLeave={() => setActive(null)} onFocus={event => activate(model, event)} onBlur={() => setActive(null)}>
          <circle className="model-ring" cx={dateX(Date.parse(model.provenance.release_created))} cy={valueY(model[field])} r="10" stroke={model.color} />
          <image href={`../${data.logos[model.family]}`} x={dateX(Date.parse(model.provenance.release_created)) - 6.5} y={valueY(model[field]) - 6.5} width="13" height="13" preserveAspectRatio="xMidYMid meet" />
        </g>)}
      </svg>
      <Tooltip active={active} geometry={null} data={data} id="release-tooltip" />
    </div>
  </section>;
}

function ReleaseScatters({ data, hidden }) {
  return <section className="release-panels" aria-label="Release-date scatter panels">
    <ReleaseScatter data={data} hidden={hidden} field="y" title="Release date vs Secular-Rational" />
    <ReleaseScatter data={data} hidden={hidden} field="x" title="Release date vs Self-expression" />
  </section>;
}

function Map({ data }) {
  const query = new URLSearchParams(location.search);
  const [hidden, setHidden] = useState(() => new Set(query.get('hide')?.split(',').filter(Boolean)));
  const [active, setActive] = useState(() => data.models.find(model => model.name === (query.get('tooltip') || query.get('focus'))) ?? null);
  const focusName = query.get('focus');
  const focusRef = useRef(null);
  const groups = useMemo(() => Object.groupBy(data.models, model => model.family), [data]);
  const { labels, geometry } = useMemo(() => assertLayout(data), [data]);

  useEffect(() => {
    if (focusName) focusRef.current?.focus();
  }, [focusName]);

  const clearActive = event => {
    if (event.currentTarget.matches(':focus')) return;
    setActive(null);
  };
  const toggle = family => setHidden(old => {
    const next = new Set(old);
    if (next.has(family)) next.delete(family); else next.add(family);
    return next;
  });
  const xMedian = geometry.x(data.median.x), yMedian = geometry.y(data.median.y);
  return <>
    <section className="controls" aria-label="Model-family visibility">{Object.entries(groups).map(([family, models]) => {
      const visible = !hidden.has(family);
      return <button key={family} className="chip" type="button" aria-pressed={visible} onClick={() => toggle(family)}>
        <img src={`../${data.logos[family]}`} alt="" />{family}
      </button>;
    })}</section>
    <div className="chart-shell">
      <svg viewBox={`0 0 ${VIEW.width} ${VIEW.height}`} role="img" aria-label="Frontier LLMs on the World Values Survey" data-median-x={data.median.x} data-median-y={data.median.y}>
        <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" className="arrow" /></marker></defs>
        <rect className="canvas" width={VIEW.width} height={VIEW.height} />
        <g className="grid">{Array.from({ length: 8 }, (_, index) => <line key={`v${index}`} x1={geometry.bounds.left + index * (geometry.bounds.right - geometry.bounds.left) / 7} y1={geometry.bounds.top} x2={geometry.bounds.left + index * (geometry.bounds.right - geometry.bounds.left) / 7} y2={geometry.bounds.bottom} />)}{Array.from({ length: 6 }, (_, index) => <line key={`h${index}`} x1={geometry.bounds.left} y1={geometry.bounds.top + index * (geometry.bounds.bottom - geometry.bounds.top) / 5} x2={geometry.bounds.right} y2={geometry.bounds.top + index * (geometry.bounds.bottom - geometry.bounds.top) / 5} />)}</g>
        <line className="median" x1={geometry.bounds.left} y1={yMedian} x2={geometry.bounds.right} y2={yMedian} />
        <line className="median" x1={xMedian} y1={geometry.bounds.top} x2={xMedian} y2={geometry.bounds.bottom} />
        {data.zone_hulls.map(zone => <path key={zone.name} className="zone" d={roundedHull(zone.points, geometry)} stroke={zone.color} />)}
        {data.countries.map(country => <g key={country.name}><circle className="country" data-country={country.name} data-x={country.x} data-y={country.y} cx={geometry.x(country.x)} cy={geometry.y(country.y)} r="3.5" fill={country.color} />{country.label && <text className="country-label" x={labels[`country:${country.name}`].cx} y={labels[`country:${country.name}`].cy + 4} textAnchor="middle">{country.name}</text>}</g>)}
        {data.zone_hulls.map(zone => <text key={zone.name} className="zone-label" x={labels[`zone:${zone.name}`].cx} y={labels[`zone:${zone.name}`].cy + 5} textAnchor="middle" fill={zone.color}>{zone.name}</text>)}
        {Object.entries(groups).map(([family, models]) => <g key={family} data-family={family} display={hidden.has(family) ? 'none' : 'inline'}>{models.map(model => <ModelMarker key={model.name} model={model} placement={labels} geometry={geometry} setActive={setActive} clearActive={clearActive} markerRef={model.name === focusName ? focusRef : null} logo={data.logos[model.family]} />)}</g>)}
        <g className="poles"><line x1={xMedian} y1="62" x2={xMedian} y2={geometry.bounds.top} markerEnd="url(#arrow)" /><line x1={xMedian} y1={geometry.bounds.bottom} x2={xMedian} y2="838" markerEnd="url(#arrow)" /><line x1="64" y1={yMedian} x2={geometry.bounds.left} y2={yMedian} markerEnd="url(#arrow)" /><line x1={geometry.bounds.right} y1={yMedian} x2="1184" y2={yMedian} markerEnd="url(#arrow)" /><text x={xMedian} y="40" textAnchor="middle">{data.axis.y[1]}</text><text x={xMedian} y="870" textAnchor="middle">{data.axis.y[0]}</text><text x="25" y={yMedian + 7}>{data.axis.x[0]}</text><text x="1136" y={yMedian + 7} textAnchor="end">{data.axis.x[1]}</text></g>
        <text className="map-title" x={geometry.bounds.left + 8} y={geometry.bounds.bottom - 34}>{data.title.split('\n').map((line, index) => <tspan key={line} x={geometry.bounds.left + 8} dy={index ? 17 : 0}>{line}</tspan>)}</text>
        <text className="map-note" x={geometry.bounds.right - 8} y={geometry.bounds.bottom - 20} textAnchor="end">{data.note.split('\n').map((line, index) => <tspan key={line} x={geometry.bounds.right - 8} dy={index ? 11 : 0}>{line}</tspan>)}</text>
      </svg>
      <Tooltip active={active} geometry={geometry} data={data} />
    </div>
    <ReleaseScatters data={data} hidden={hidden} />
  </>;
}

function App() {
  const [data, setData] = useState(null);
  useEffect(() => { fetch('../wvs_map_data.json').then(response => response.json()).then(setData); }, []);
  return <main><h1>Frontier LLMs on the World Values Survey</h1><p className="lede">React/SVG rendering of the shared WVS coordinate artifact. White-ring marks use locally saved lab logos. Focus or hover a model for its measured readout and release provenance.</p>{data && <Map data={data} />}</main>;
}

createRoot(document.getElementById('root')).render(<App/>);
