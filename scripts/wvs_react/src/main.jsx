import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { VIEW, RINGS, LABEL_STEPS, assertLayout, box, hits, inside, roundedHull } from './layout.js';
import './style.css';

const LOGO_ROOT = 'wvs/';

function visibleFamilyNames(groups, hidden) {
  return Object.keys(groups).filter(family => !hidden.has(family));
}

function Tooltip({ active, geometry, id = 'model-tooltip', panel }) {
  if (!active) return null;
  const left = active.tooltipLeft ?? `${Math.min(86, geometry.x(active.x) / VIEW.width * 100)}%`;
  const top = active.tooltipTop ?? `${Math.min(82, geometry.y(active.y) / VIEW.height * 100)}%`;
  const release = active.provenance.release_created && <span>release {active.provenance.release_created}</span>;
  return <aside id={id} className="tooltip" style={{ left, top }} role="status">
    <strong>{active.name}</strong>
    {active.tooltipIndex != null && <span>Intelligence Index: {active.tooltipIndex.toFixed(2)}</span>}
    {panel === 'secular' && <span>Secular-Rational: {active.y.toFixed(3)}</span>}
    {panel === 'self-expression' && <span>Self-expression: {active.tooltipValue.toFixed(3)}</span>}
    {!panel && <><span>Self-expression/Survival: {active.x.toFixed(3)}</span><span>Traditional/Secular-Rational: {active.y.toFixed(3)}</span></>}
    {active.tooltipIndex == null && release}
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
    <circle className="model-ring" cx={cx} cy={cy} r="8" stroke={model.color} />
    <image href={`${LOGO_ROOT}${logo}`} x={cx - 5} y={cy - 5} width="10" height="10" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false" />
    {label && <text className="model-label" x={label.cx} y={label.cy + 4} textAnchor="middle">{model.label}</text>}
  </g>;
}

function ordinaryLeastSquares(models, xValue, yValue) {
  const x = models.map(xValue);
  const y = models.map(yValue);
  const uniqueX = new Set(x);
  if (uniqueX.size < 2) return null;
  const xMean = x.reduce((sum, value) => sum + value, 0) / x.length;
  const yMean = y.reduce((sum, value) => sum + value, 0) / y.length;
  const slope = x.reduce((sum, value, index) => sum + (value - xMean) * (y[index] - yMean), 0)
    / x.reduce((sum, value) => sum + (value - xMean) ** 2, 0);
  const intercept = yMean - slope * xMean;
  const residual = y.reduce((sum, value, index) => sum + (value - (intercept + slope * x[index])) ** 2, 0);
  const total = y.reduce((sum, value) => sum + (value - yMean) ** 2, 0);
  return { slope, intercept, n: models.length, r2: total === 0 ? null : 1 - residual / total };
}

function ReleaseScatter({ data, hidden, field, title, axisMode }) {
  const dated = useMemo(() => data.models.filter(model => Number.isFinite(Date.parse(model.provenance.release_created ?? '')))
    .toSorted((a, b) => a.provenance.release_created.localeCompare(b.provenance.release_created) || a.name.localeCompare(b.name)), [data]);
  const matched = useMemo(() => data.models.filter(model => Number.isFinite(model.provenance.intelligence_index))
    .toSorted((a, b) => a.provenance.intelligence_index - b.provenance.intelligence_index || a.name.localeCompare(b.name)), [data]);
  const plotted = axisMode === 'release-date' ? dated : matched;
  const visible = plotted.filter(model => !hidden.has(model.family));
  const coordinate = model => field === 'x' ? -model.x : model.y;
  const xValue = model => axisMode === 'release-date' ? Date.parse(model.provenance.release_created) : model.provenance.intelligence_index;
  const fit = ordinaryLeastSquares(visible, xValue, coordinate);
  const [active, setActive] = useState(null);
  const width = 1200, height = 320, left = 96, right = 35, top = 42, bottom = 48;
  const xValues = plotted.map(xValue);
  const values = plotted.map(coordinate);
  const minX = Math.min(...xValues), maxX = Math.max(...xValues);
  const minValue = Math.min(...values), maxValue = Math.max(...values);
  const plotX = value => left + (value - minX) / (maxX - minX || 1) * (width - left - right);
  const valueY = value => top + (maxValue - value) / (maxValue - minValue || 1) * (height - top - bottom);
  const panelId = `release-${field}`;
  const tooltipId = `${panelId}-tooltip`;
  const yDirection = field === 'y' ? data.axis.y : [...data.axis.x].reverse();
  const visibleX = visible.map(xValue);
  const fitEnd = fit && [Math.min(...visibleX), Math.max(...visibleX)].map(value => [plotX(value), valueY(fit.intercept + fit.slope * value)]);
  const frontier = useMemo(() => {
    if (axisMode !== 'release-date') return [];
    let high = -Infinity;
    return visible.filter(model => Number.isFinite(model.provenance.intelligence_index)).filter(model => {
      if (model.provenance.intelligence_index <= high) return false;
      high = model.provenance.intelligence_index;
      return true;
    });
  }, [axisMode, visible]);
  const frontierPlacement = useMemo(() => {
    const bounds = { left, right: width - right, top, bottom: height - bottom };
    const taken = plotted.map(model => box(plotX(xValue(model)), valueY(coordinate(model)), 16, 16));
    const placement = {};
    for (const model of frontier) {
      const anchor = { x: plotX(xValue(model)), y: valueY(coordinate(model)) };
      const size = { width: model.name.length * 8 + 12, height: 18 };
      let found = null;
      for (const step of LABEL_STEPS) {
        for (const [dx, dy] of RINGS) {
          const candidate = box(anchor.x + dx * (step + size.width / 3), anchor.y + dy * step, size.width, size.height);
          if (inside(candidate, bounds) && !taken.some(obstacle => hits(candidate, obstacle))) { found = candidate; break; }
        }
        if (found) break;
      }
      if (!found) throw new Error(`no frontier label location for ${model.name}`);
      placement[model.name] = { ...found, anchor };
      taken.push(found);
    }
    return placement;
  }, [frontier, plotted, minX, maxX, minValue, maxValue]);
  const activate = (model, event) => {
    const box = event.currentTarget.closest('.scatter-shell').getBoundingClientRect();
    const point = event.currentTarget.getBoundingClientRect();
    setActive({ ...model, tooltipValue: coordinate(model), tooltipIndex: axisMode === 'capability' ? model.provenance.intelligence_index : null, tooltipLeft: `${Math.min(82, (point.left - box.left) / box.width * 100)}%`, tooltipTop: `${Math.min(78, (point.top - box.top) / box.height * 100)}%` });
  };
  return <section className="release-panel" data-coordinate={field} aria-labelledby={`${panelId}-heading`}>
    <h2 id={`${panelId}-heading`}>{title}</h2>
    <div className="scatter-shell">
      <svg id={`${panelId}-svg`} viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby={`${panelId}-svg-title ${panelId}-svg-desc`} data-axis-mode={axisMode} data-panel-model-count={visible.length} data-omitted-model-count={data.models.length - plotted.length} data-fit-n={fit?.n ?? 0} data-fit-r2={fit?.r2 ?? ''} data-fit-slope={fit?.slope ?? ''}>
        <title id={`${panelId}-svg-title`}>{title}</title>
        <desc id={`${panelId}-svg-desc`}>Scatter plot with {axisMode === 'release-date' ? 'release date' : 'Artificial Analysis Intelligence Index'} on the horizontal axis and {yDirection.join(' to ')} increasing upward on the vertical axis. {visible.length} of {plotted.length} matched models are visible from {visibleFamilyNames(Object.groupBy(data.models, model => model.family), hidden).join(', ') || 'no families'}; {data.models.length - plotted.length} plotted models lack this x value and are omitted only here. Each white-ring logo mark is a model. {fit ? `The thin line is an ordinary least squares descriptive fit to the ${fit.n} currently visible matched models${fit.r2 === null ? '; R squared is unavailable because the y values are constant' : `; R squared is ${fit.r2.toFixed(2)}`}.` : 'The fit is hidden because fewer than two distinct x values are visible.'} Hover or keyboard focus a mark for model-specific details.</desc>
        <defs><marker id={`${panelId}-arrow`} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" className="scatter-arrow" /></marker><clipPath id={`${panelId}-fit-clip`}><rect x={left} y={top} width={width - left - right} height={height - top - bottom} /></clipPath></defs>
        <rect className="canvas" width={width} height={height} />
        <g className="scatter-grid">{Array.from({ length: 5 }, (_, index) => <line key={index} x1={left} x2={width - right} y1={top + index * (height - top - bottom) / 4} y2={top + index * (height - top - bottom) / 4} />)}</g>
        <line className="scatter-axis" x1={left} x2={width - right} y1={height - bottom} y2={height - bottom} />
        <line className="scatter-axis" x1={left} x2={left} y1={height - bottom} y2={top} markerEnd={`url(#${panelId}-arrow)`} />
        <text className="scatter-y-label" x="17" y={(top + height - bottom) / 2} textAnchor="middle" transform={`rotate(-90 17 ${(top + height - bottom) / 2})`}>{yDirection.join(' -> ')} {'↑'}</text>
        <text className="scatter-tick" x={left} y={height - 18}>{axisMode === 'release-date' ? new Date(minX).toISOString().slice(0, 10) : minX.toFixed(1)}</text>
        <text className="scatter-tick" x={width - right} y={height - 18} textAnchor="end">{axisMode === 'release-date' ? new Date(maxX).toISOString().slice(0, 10) : maxX.toFixed(1)}</text>
        <text className="scatter-tick" x={left - 8} y={top + 4} textAnchor="end">{maxValue.toFixed(2)}</text>
        <text className="scatter-tick" x={left - 8} y={height - bottom} textAnchor="end">{minValue.toFixed(2)}</text>
        {fitEnd && <g className="release-fit" data-fit-n={fit.n} data-fit-r2={fit.r2 ?? ''}><line clipPath={`url(#${panelId}-fit-clip)`} x1={fitEnd[0][0]} y1={fitEnd[0][1]} x2={fitEnd[1][0]} y2={fitEnd[1][1]} /> <text x={left + 6} y={top + 13}>OLS, n={fit.n}, R² {fit.r2 === null ? 'unavailable' : fit.r2.toFixed(2)}</text></g>}
        {!fit && <text className="release-fit-unavailable" x={left + 6} y={top + 13}>Fit unavailable: fewer than two release dates</text>}
        {plotted.map(model => <g key={model.name} className="release-mark" data-family={model.family} data-release-model={model.name} data-release-date={model.provenance.release_created} data-capability-score={model.provenance.intelligence_index} data-coordinate-value={coordinate(model)} display={hidden.has(model.family) ? 'none' : 'inline'}
          tabIndex="0" role="button" aria-label={`${model.name}, ${axisMode === 'release-date' ? model.provenance.release_created : `Intelligence Index ${model.provenance.intelligence_index}`}`} aria-describedby={tooltipId}
          onPointerEnter={event => activate(model, event)} onPointerLeave={() => setActive(null)} onFocus={event => activate(model, event)} onBlur={() => setActive(null)}>
          <circle className="model-ring" cx={plotX(xValue(model))} cy={valueY(coordinate(model))} r="8" stroke={model.color} />
          <image href={`${LOGO_ROOT}${data.logos[model.family]}`} x={plotX(xValue(model)) - 5} y={valueY(coordinate(model)) - 5} width="10" height="10" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false" />
        </g>)}
        {axisMode === 'release-date' && frontier.map(model => <g key={`frontier-${model.name}`} className="frontier-label" data-frontier-model={model.name}><line x1={frontierPlacement[model.name].anchor.x} y1={frontierPlacement[model.name].anchor.y} x2={frontierPlacement[model.name].cx} y2={frontierPlacement[model.name].cy} /><text x={frontierPlacement[model.name].cx} y={frontierPlacement[model.name].cy + 4} textAnchor="middle">{model.name}</text></g>)}
      </svg>
      <Tooltip active={active} geometry={null} id={tooltipId} panel={field === 'y' ? 'secular' : 'self-expression'} />
    </div>
  </section>;
}

function ReleaseScatters({ data, hidden, axisMode, setAxisMode }) {
  const xLabel = axisMode === 'release-date' ? 'Release date' : data.capability_x.label;
  return <section className="release-panels" aria-label="Release-date and capability scatter panels">
    <div className="release-axis-selector">
      <label>Release-panel x axis <select aria-label="Release-panel x axis" aria-controls="release-y-svg release-x-svg" value={axisMode} onChange={event => setAxisMode(event.target.value)}>
        <option value="release-date">Release date</option>
        <option value="capability">{data.capability_x.label}</option>
      </select></label>
      <span><a href={data.capability_x.source_url}>{data.capability_x.label}</a>, saved {data.capability_x.fetched_utc.slice(0, 10)}. {axisMode === 'capability' ? `${data.capability_x.matched_models} matched, ${data.models.length - data.capability_x.matched_models} omitted.` : 'Release-date labels mark running Intelligence Index highs among shown mapped models.'}</span>
    </div>
    <ReleaseScatter data={data} hidden={hidden} field="y" axisMode={axisMode} title={`${xLabel} vs Secular-Rational`} />
    <ReleaseScatter data={data} hidden={hidden} field="x" axisMode={axisMode} title={`${xLabel} vs Self-expression`} />
  </section>;
}

function Map({ data }) {
  const query = new URLSearchParams(location.search);
  const [hidden, setHidden] = useState(() => new Set(query.get('hide')?.split(',').filter(Boolean)));
  const [axisMode, setAxisMode] = useState(() => query.get('axis') === 'capability' ? 'capability' : 'release-date');
  const [active, setActive] = useState(() => data.models.find(model => model.name === (query.get('tooltip') || query.get('focus'))) ?? null);
  const focusName = query.get('focus');
  const focusRef = useRef(null);
  const groups = useMemo(() => Object.groupBy(data.models, model => model.family), [data]);
  const { labels, geometry } = useMemo(() => assertLayout(data), [data]);
  const visibleFamilies = visibleFamilyNames(groups, hidden);
  const visibleModelCount = data.models.filter(model => !hidden.has(model.family)).length;

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
    <section className="controls" aria-label="Model-family visibility">{Object.entries(groups).map(([family]) => {
      const visible = !hidden.has(family);
      return <button key={family} className="chip" type="button" aria-pressed={visible} onClick={() => toggle(family)}>
        <img src={`${LOGO_ROOT}${data.logos[family]}`} alt="" aria-hidden="true" />{family}
      </button>;
    })}</section>
    <div className="chart-shell">
      <svg viewBox={`0 0 ${VIEW.width} ${VIEW.height}`} role="img" aria-labelledby="map-svg-title map-svg-desc" data-median-x={data.median.x} data-median-y={data.median.y} data-visible-model-count={visibleModelCount}>
        <title id="map-svg-title">Frontier LLMs on the World Values Survey</title>
        <desc id="map-svg-desc">World Values Survey cultural map. Horizontal direction runs from Self-expression on the left to Survival on the right. Vertical direction runs from Traditional below to Secular-Rational above. Coloured dots are selected WVS countries, outlines are cultural regions, and white-ring logo marks are models. {visibleModelCount} model marks are visible from {visibleFamilies.join(', ') || 'no families'}. Use the family controls to hide marks and labels. Hover or keyboard focus a model for model-specific details.</desc>
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
      <Tooltip active={active} geometry={geometry} />
    </div>
    <p className="map-explanation">Since 1981, the World Values Survey has asked people in about ninety countries the same questions. Its axes run from Traditional to Secular-Rational and from Self-expression to Survival.</p>
    <ReleaseScatters data={data} hidden={hidden} axisMode={axisMode} setAxisMode={setAxisMode} />
    <p className="caption">Use the family controls to compare saved rated coordinates. The lines are weak descriptive correlations for the matched models currently shown; n and R² update with visibility. Hover or keyboard focus a mark for its values. See the <a href="https://github.com/wassname/moral-maps">code and records</a>.</p>
  </>;
}

function App() {
  const [data, setData] = useState(null);
  useEffect(() => { fetch('wvs/wvs_map_data.json').then(response => response.json()).then(setData); }, []);
  return <main>
    <h1>How do AI models score on human values surveys? Which culture are they most similar to? Is it changing over time?</h1>
    <p className="lede">We start with the <a href="https://www.worldvaluessurvey.org/">World Values Survey</a>, a map of human values across about ninety countries.</p>
    {data && <Map data={data} />}
  </main>;
}

createRoot(document.getElementById('root')).render(<App/>);
