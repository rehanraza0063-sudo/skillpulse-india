import { useEffect, useMemo, useState } from 'react';
import { CartesianGrid, Cell, LabelList, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import TransitionFlow from '../components/TransitionFlow';
import { Card, Chips, DemoNote, ErrorState, Explain, Loading, PageHeader, StatusBadge } from '../components/ui';
import { C, TREND_COLOR } from '../utils/colors';
import { n0 } from '../utils/format';

const COLS = [
  { key: 'GROWING', tone: 'border-green-300 bg-green-50' },
  { key: 'STABLE', tone: 'border-slate-300 bg-slate-100' },
  { key: 'DECLINING', tone: 'border-red-300 bg-red-50' },
];

export default function IndustryRadar() {
  const { data, error, loading, reload } = useApi((s) => api.industries(s), []);
  const [selId, setSelId] = useState('I05'); // Traditional ICE Automotive: the demo storyline starts here
  const [pathIdx, setPathIdx] = useState(0);
  useEffect(() => setPathIdx(0), [selId]);

  const inds = data?.industries || [];
  const sel = inds.find((i) => i.industry_id === selId) || inds[0];

  const paths = useMemo(() => {
    if (!sel || !data) return [];
    if (sel.future_outlook === 'DECLINING') return sel.transition_pathways;
    if (sel.future_outlook === 'GROWING') return data.opportunities.filter((o) => o.to_industry === sel.industry_name).slice(0, 4);
    return [];
  }, [sel, data]);

  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return <Loading label="Loading industry signals..." />;

  const scatter = inds.map((i) => ({ ...i, x: i.forecast_cagr_pct, y: i.demand_2026 }));

  return (
    <div>
      <PageHeader title="Industry Transition Radar" subtitle="Which industries are growing, stable or declining, which skills they need, and how workers can bridge from one to another.">
        <DemoNote />
      </PageHeader>

      <div className="grid gap-4 md:grid-cols-3" role="list" aria-label="Industry outlook board">
        {COLS.map((col) => {
          const items = inds.filter((i) => i.future_outlook === col.key).sort((a, b) => b.forecast_cagr_pct - a.forecast_cagr_pct);
          return (
            <div key={col.key} role="listitem" className={`rounded-lg border p-3 ${col.tone}`}>
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-sm font-bold tracking-wide">{col.key}</h2>
                <span className="text-xs text-slate-600">{items.length} industries</span>
              </div>
              <div className="space-y-2">
                {items.length === 0 && <p className="text-xs text-slate-500">None</p>}
                {items.map((i) => (
                  <button key={i.industry_id} type="button" onClick={() => setSelId(i.industry_id)} aria-pressed={i.industry_id === sel?.industry_id}
                    className={`block w-full rounded-md border bg-white p-3 text-left shadow-sm transition-shadow hover:shadow ${i.industry_id === sel?.industry_id ? 'border-brand-600 ring-2 ring-brand-500' : 'border-slate-200'}`}>
                    <div className="text-sm font-semibold">{i.industry_name}</div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-slate-600">
                      <span>Demand trend</span>
                      <b style={{ color: TREND_COLOR[i.computed_trend] }}>{i.forecast_cagr_pct > 0 ? '+' : ''}{i.forecast_cagr_pct}%/yr</b>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-5">
        {sel && (
          <Card className="xl:col-span-3" title={sel.industry_name} subtitle="Click another industry above to compare"
            actions={<div className="flex gap-2 text-xs"><span>Now <StatusBadge kind="outlook" value={sel.current_outlook} /></span><span>Future <StatusBadge kind="outlook" value={sel.future_outlook} /></span></div>}>
            <dl className="grid gap-4 sm:grid-cols-3">
              <div><dt className="label">Demand 2023</dt><dd className="text-lg font-semibold">{n0(sel.demand_2023)}</dd><dd className="text-xs text-slate-500">{sel.hist_cagr_pct}%/yr to 2026</dd></div>
              <div><dt className="label">Demand 2026</dt><dd className="text-lg font-semibold">{n0(sel.demand_2026)}</dd><dd className="text-xs text-slate-500">capacity {n0(sel.capacity_2026)}</dd></div>
              <div><dt className="label">2028 (Prototype Forecast)</dt><dd className="text-lg font-semibold">{n0(sel.demand_2028_forecast)}</dd><dd className="text-xs text-slate-500">{sel.forecast_cagr_pct}%/yr</dd></div>
            </dl>
            <p className="mt-3 rounded bg-slate-50 p-2 text-xs text-slate-600">
              Demo signal: {sel.signal_note}. Computed trend <b>{sel.computed_trend}</b>. {data.trend_rule}.
            </p>
            <div className="mt-4"><div className="label">Required skills (importance 1-3)</div>
              <Chips items={sel.required_skills.map((s) => ({ label: `${s.competency} (${s.weight})` }))} tone="bg-brand-50 text-brand-800 border-brand-200" /></div>
            <div className="mt-4"><div className="label">Related occupations</div><Chips items={sel.related_occupations} /></div>
            <div className="mt-4">
              <div className="label">Skill tracks, 2027 (Prototype Forecast)</div>
              <ul className="divide-y divide-slate-100 text-sm">
                {sel.skill_tracks.map((t) => (
                  <li key={t.skill_id} className="flex items-center justify-between py-1.5">
                    <span>{t.skill_name}</span>
                    <span className="flex items-center gap-3 text-xs text-slate-600">demand {n0(t.demand_2027)} / capacity {n0(t.capacity_2027)} <StatusBadge value={t.status_2027} /></span>
                  </li>
                ))}
              </ul>
            </div>
          </Card>
        )}

        <Card className="xl:col-span-2" title="Transition view"
          subtitle={sel?.future_outlook === 'DECLINING' ? `From ${sel.industry_name} into growing industries` : sel?.future_outlook === 'GROWING' ? `Who could move into ${sel.industry_name}` : 'Select a declining or growing industry'}>
          {paths.length === 0 ? (
            <p className="text-sm text-slate-500">Stable industries have no transition pathway in this view. Select <b>Traditional ICE Automotive</b> or <b>Textiles &amp; Garments</b> (declining), or a growing industry.</p>
          ) : (
            <>
              <label className="mb-3 block"><span className="label">Pathway</span>
                <select className="input" value={pathIdx} onChange={(e) => setPathIdx(Number(e.target.value))}>
                  {paths.map((p, i) => <option key={`${p.from_occupation}-${p.to_occupation}`} value={i}>{p.from_occupation} to {p.to_occupation} (fit {p.fit_score.toFixed(0)}%)</option>)}
                </select></label>
              <TransitionFlow path={paths[Math.min(pathIdx, paths.length - 1)]} />
            </>
          )}
        </Card>
      </div>

      <Card className="mt-4" title="Industry matrix" subtitle="Forecast growth per year (x) against current demand (y). Prototype Forecast on demo data.">
        <div role="img" aria-label="Scatter plot of industries by forecast growth and current demand" style={{ height: 340 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 40, bottom: 24, left: 8 }}>
              <CartesianGrid stroke={C.grid} />
              <XAxis type="number" dataKey="x" name="Forecast growth" unit="%" tick={{ fontSize: 12, fill: C.text }} label={{ value: 'Forecast demand growth per year (%)', position: 'insideBottom', offset: -12, fontSize: 12, fill: C.text }} />
              <YAxis type="number" dataKey="y" name="Demand 2026" tick={{ fontSize: 12, fill: C.text }} tickFormatter={n0} width={64} />
              <ReferenceLine x={0} stroke="#64748b" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={(v, n) => [n === 'Demand 2026' ? n0(v) : v, n]} labelFormatter={() => ''} />
              <Scatter data={scatter} isAnimationActive={false}>
                {scatter.map((d) => <Cell key={d.industry_id} fill={TREND_COLOR[d.computed_trend]} />)}
                <LabelList dataKey="industry_name" position="top" style={{ fontSize: 11, fill: C.text }} />
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="mt-4">
        <Explain data={{
          method: 'Outlook labels come from demo industry signals; the demand trend is computed from the Prototype Forecast (linear regression on demo demand history). Fit scores use the weighted skill-overlap method.',
          inputs: 'Demo industry signals, demo demand and capacity history, occupation skill requirements',
          output: 'GROWING / STABLE / DECLINING board, required skills, related occupations, transition pathways',
          limitations: 'Signals and forecasts are illustrative demo values; requires validation with official datasets.',
        }} />
      </div>
    </div>
  );
}
