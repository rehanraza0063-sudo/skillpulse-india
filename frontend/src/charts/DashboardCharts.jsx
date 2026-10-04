import {
  Area, Bar, BarChart, CartesianGrid, Cell, ComposedChart, LabelList, Legend, Line, ReferenceLine,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { C, TREND_COLOR } from '../utils/colors';
import { n0 } from '../utils/format';

const axis = { fontSize: 12, fill: C.text };

export function DemandCapacityChart({ data }) {
  const rows = [...data].sort((a, b) => b.demand - a.demand);
  return (
    <div role="img" aria-label="Bar chart comparing demand with training capacity for each skill" style={{ height: Math.max(320, rows.length * 38) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={rows} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
          <CartesianGrid stroke={C.grid} horizontal={false} />
          <XAxis type="number" tick={axis} tickFormatter={n0} />
          <YAxis type="category" dataKey="skill_name" width={180} tick={axis} />
          <Tooltip formatter={(v) => n0(v)} />
          <Legend />
          <Bar dataKey="demand" name="Demand" fill={C.demand} barSize={11} />
          <Bar dataKey="capacity" name="Training capacity" fill={C.capacity} barSize={11} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RankedBarChart({ data, valueKey, color, name, empty }) {
  if (!data || data.length === 0) return <p className="p-6 text-center text-sm text-slate-500">{empty}</p>;
  return (
    <div role="img" aria-label={`Bar chart: ${name}`} style={{ height: Math.max(200, data.length * 46) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 56, top: 4, bottom: 4 }}>
          <CartesianGrid stroke={C.grid} horizontal={false} />
          <XAxis type="number" tick={axis} tickFormatter={n0} />
          <YAxis type="category" dataKey="skill_name" width={180} tick={axis} />
          <Tooltip formatter={(v) => [n0(v), name]} />
          <Bar dataKey={valueKey} name={name} fill={color} barSize={18}>
            <LabelList dataKey={valueKey} position="right" formatter={n0} style={{ fontSize: 12, fill: C.text }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function TrendTip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const p = payload[0].payload;
  return (
    <div className="rounded border border-slate-200 bg-white p-2 text-xs shadow">
      <div className="font-semibold">{label}{p.is_forecast ? ' (Prototype Forecast)' : ''}</div>
      <div>Demand: {n0(p.demand)}</div>
      {p.is_forecast && <div>Range: {n0(p.lower)} - {n0(p.upper)}</div>}
      <div>Training capacity: {n0(p.capacity)}</div>
    </div>
  );
}

export function TrendChart({ data }) {
  const rows = data.map((d) => ({
    ...d,
    hist: d.is_forecast ? null : d.demand,
    fc: d.is_forecast || d.year === 2026 ? d.demand : null,
    band: d.is_forecast ? [d.lower, d.upper] : d.year === 2026 ? [d.demand, d.demand] : null,
  }));
  return (
    <div role="img" aria-label="Line chart of historical demand 2023 to 2026 and prototype forecast 2027 to 2028 with uncertainty band, against training capacity" style={{ height: 300 }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rows} margin={{ left: 8, right: 16, top: 8, bottom: 4 }}>
          <CartesianGrid stroke={C.grid} />
          <XAxis dataKey="year" tick={axis} />
          <YAxis tick={axis} tickFormatter={n0} width={64} />
          <Tooltip content={<TrendTip />} />
          <Legend />
          <ReferenceLine x={2026} stroke="#94a3b8" strokeDasharray="4 4" label={{ value: 'forecast →', position: 'insideTopRight', fontSize: 11, fill: C.text }} />
          <Area dataKey="band" name="Forecast range (80%)" stroke="none" fill={C.demand} fillOpacity={0.15} connectNulls={false} isAnimationActive={false} />
          <Line dataKey="hist" name="Historical demand" stroke={C.demand} strokeWidth={2.5} dot={{ r: 3 }} connectNulls={false} isAnimationActive={false} />
          <Line dataKey="fc" name="Forecast demand" stroke={C.demand} strokeWidth={2.5} strokeDasharray="6 4" dot={{ r: 3 }} connectNulls={false} isAnimationActive={false} />
          <Line dataKey="capacity" name="Training capacity" stroke={C.capacity} strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function IndustryGrowthChart({ data }) {
  return (
    <div role="img" aria-label="Bar chart of forecast yearly demand growth by industry" style={{ height: Math.max(260, data.length * 44) }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 8, right: 56, top: 4, bottom: 4 }}>
          <CartesianGrid stroke={C.grid} horizontal={false} />
          <XAxis type="number" tick={axis} tickFormatter={(v) => `${v}%`} />
          <YAxis type="category" dataKey="industry_name" width={170} tick={axis} />
          <ReferenceLine x={0} stroke="#64748b" />
          <Tooltip formatter={(v) => [`${v}% per year`, 'Forecast growth 2026-2028']} />
          <Bar dataKey="forecast_cagr_pct" name="Forecast growth per year" barSize={18}>
            {data.map((d) => <Cell key={d.industry_id} fill={TREND_COLOR[d.trend]} />)}
            <LabelList dataKey="forecast_cagr_pct" position="right" formatter={(v) => `${v}%`} style={{ fontSize: 12, fill: C.text }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
