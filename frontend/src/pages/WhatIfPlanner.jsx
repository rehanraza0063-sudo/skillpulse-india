import { useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../services/api';
import { useApi, useDebounced } from '../hooks/useApi';
import { Card, DemoNote, ErrorState, Explain, Loading, Mono, PageHeader, Select, StatusBadge } from '../components/ui';
import { C } from '../utils/colors';
import { n0, signed, yearLabel } from '../utils/format';

const axis = { fontSize: 12, fill: C.text };

export default function WhatIfPlanner() {
  const [skillId, setSkillId] = useState('S01');
  const [districtId, setDistrictId] = useState('D04'); // Pune: 1000 demand vs 700 capacity in the demo data
  const [year, setYear] = useState('2026');
  const [g, setG] = useState(0);
  const [c, setC] = useState(0);
  const dg = useDebounced(g, 150);
  const dc = useDebounced(c, 150);

  const lists = useApi(async (s) => {
    const [sk, d] = await Promise.all([api.skills(s), api.districts(s)]);
    return { skills: sk.skills, districts: d.districts };
  }, []);

  const res = useApi(
    (signal) => api.whatIf({ skill_id: skillId, district_id: districtId || null, year: Number(year), demand_growth_pct: dg, capacity_change_pct: dc }, signal),
    [skillId, districtId, year, dg, dc],
  );

  const r = res.data;
  const bars = r && [
    { name: 'Demand', before: r.before.demand, after: r.after.demand },
    { name: 'Training capacity', before: r.before.capacity, after: r.after.capacity },
    { name: 'Gap', before: r.before.gap, after: r.after.gap },
  ];

  return (
    <div>
      <PageHeader title="What-If Scenario Planner" subtitle="Change industry demand growth and training capacity. Results recalculate instantly, without reloading the page.">
        <DemoNote />
      </PageHeader>

      <Card className="mb-4" title="Scenario controls">
        {lists.error ? <ErrorState error={lists.error} onRetry={lists.reload} /> : !lists.data ? <Loading /> : (
          <>
            <div className="grid gap-3 sm:grid-cols-3">
              <Select label="Skill" value={skillId} onChange={setSkillId} options={lists.data.skills.map((s) => ({ value: s.skill_id, label: s.skill_name }))} />
              <Select label="District" value={districtId} onChange={setDistrictId} placeholder="All demo districts" options={lists.data.districts.map((d) => ({ value: d.district_id, label: d.district_name }))} />
              <Select label="Year" value={year} onChange={setYear} options={[2026, 2027, 2028].map((y) => ({ value: String(y), label: yearLabel(y) }))} />
            </div>
            <div className="mt-5 grid gap-6 md:grid-cols-2">
              <Slider id="g" label="Industry demand growth" value={g} onChange={setG} />
              <Slider id="c" label="Training capacity change" value={c} onChange={setC} />
            </div>
            <button type="button" className="btn-secondary mt-4" onClick={() => { setG(0); setC(0); }}>Reset to baseline</button>
          </>
        )}
      </Card>

      {res.error && <ErrorState error={res.error} onRetry={res.reload} />}
      {!r && res.loading && <Loading label="Calculating..." />}

      {r && (
        <div className={res.loading ? 'opacity-70 transition-opacity' : ''}>
          <div className="mb-4 grid gap-4 md:grid-cols-2">
            <ResultCard title="Before (baseline)" tone="border-slate-300" s={r.before} />
            <ResultCard title="After (your scenario)" tone="border-brand-400" s={r.after} delta={r.gap_change} />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Before / after" subtitle={`${r.skill_name}, ${r.district_name}, ${yearLabel(r.year)}`}>
              <div role="img" aria-label="Grouped bar chart comparing demand, capacity and gap before and after the scenario" style={{ height: 280 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={bars} margin={{ left: 8, right: 8, top: 8 }}>
                    <CartesianGrid stroke={C.grid} />
                    <XAxis dataKey="name" tick={axis} />
                    <YAxis tick={axis} tickFormatter={n0} width={60} />
                    <ReferenceLine y={0} stroke="#64748b" />
                    <Tooltip formatter={(v) => n0(v)} />
                    <Legend />
                    <Bar dataKey="before" name="Before" fill="#94a3b8" />
                    <Bar dataKey="after" name="After" fill={C.demand} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
            <Card title="Gap over time" subtitle="Applying the same % change to each year (2027-2028 are Prototype Forecast)">
              <div role="img" aria-label="Line chart of the demand-supply gap by year, before and after the scenario" style={{ height: 280 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={r.years} margin={{ left: 8, right: 16, top: 8 }}>
                    <CartesianGrid stroke={C.grid} />
                    <XAxis dataKey="year" tick={axis} />
                    <YAxis tick={axis} tickFormatter={n0} width={60} />
                    <ReferenceLine y={0} stroke="#64748b" />
                    <Tooltip formatter={(v) => n0(v)} />
                    <Legend />
                    <Line dataKey="before_gap" name="Gap before" stroke="#64748b" strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
                    <Line dataKey="after_gap" name="Gap after" stroke={C.gap} strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          <Card className="mt-4" title="Preset scenarios" subtitle="Computed on the same baseline. Click Apply to load one into the sliders.">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {r.scenarios.map((s) => (
                <div key={s.id} className="rounded-lg border border-slate-200 p-3">
                  <div className="text-xs font-bold uppercase text-slate-500">Scenario {s.id}</div>
                  <div className="text-sm font-semibold">{s.name}</div>
                  <div className="mt-1 text-xs text-slate-600">Demand {s.demand_growth_pct > 0 ? '+' : ''}{s.demand_growth_pct}% &middot; capacity {s.capacity_change_pct > 0 ? '+' : ''}{s.capacity_change_pct}%</div>
                  <div className="mt-2 flex items-center justify-between text-sm">
                    <span>Gap <b>{n0(s.gap)}</b> <span className="text-xs text-slate-500">({signed(s.gap_change)})</span></span>
                    <StatusBadge value={s.status} />
                  </div>
                  <button type="button" className="btn-secondary mt-2 w-full" onClick={() => { setG(s.demand_growth_pct); setC(s.capacity_change_pct); }}>Apply</button>
                </div>
              ))}
            </div>
          </Card>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <Card title="Calculation"><Mono>{r.after.calculation}</Mono><p className="mt-2 text-xs text-slate-500">{r.before.calculation}</p></Card>
            <Explain data={r.explainability} />
          </div>
          <DemoNote className="mt-4" />
        </div>
      )}
    </div>
  );
}

function Slider({ id, label, value, onChange }) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <label htmlFor={id} className="label !mb-0">{label}</label>
        <span className="text-sm font-bold text-brand-800">{value > 0 ? '+' : ''}{value}%</span>
      </div>
      <input id={id} type="range" min={-50} max={100} step={1} value={value} onChange={(e) => onChange(Number(e.target.value))} className="mt-2 w-full accent-brand-700" />
      <div className="flex justify-between text-[11px] text-slate-400"><span>-50%</span><span>0</span><span>+100%</span></div>
    </div>
  );
}

function ResultCard({ title, s, tone, delta }) {
  return (
    <div className={`card border-2 p-4 ${tone}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">{title}</h2>
        <StatusBadge value={s.status} />
      </div>
      <dl className="mt-3 grid grid-cols-3 gap-3">
        <div><dt className="text-xs text-slate-500">Demand</dt><dd className="text-xl font-bold">{n0(s.demand)}</dd></div>
        <div><dt className="text-xs text-slate-500">Capacity</dt><dd className="text-xl font-bold">{n0(s.capacity)}</dd></div>
        <div><dt className="text-xs text-slate-500">Gap</dt><dd className="text-xl font-bold">{n0(s.gap)}</dd>
          {delta !== undefined && <dd className={`text-xs ${delta > 0 ? 'text-red-700' : delta < 0 ? 'text-green-700' : 'text-slate-500'}`}>{signed(delta)} vs baseline</dd>}</div>
      </dl>
    </div>
  );
}
