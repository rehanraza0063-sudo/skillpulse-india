import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Card, DemoNote, EmptyState, ErrorState, Explain, Loading, PageHeader, Select, StatusBadge } from '../components/ui';
import { n0, yearLabel } from '../utils/format';

const fmt = (k, v) => {
  if (Array.isArray(v)) return v.join(', ');
  if (typeof v === 'number') return /pct|score|km/.test(k) ? String(v) : n0(v);
  return String(v);
};

export default function Recommendations() {
  const [year, setYear] = useState('2027');
  const [districtId, setDistrictId] = useState('');
  const [type, setType] = useState('');
  const lists = useApi((s) => api.districts(s), []);
  const rec = useApi((s) => api.recommendations({ year, district_id: districtId }, s), [year, districtId]);

  const d = rec.data;
  const types = useMemo(() => (d ? [...new Set(d.recommendations.map((r) => r.type))] : []), [d]);
  const shown = d ? d.recommendations.filter((r) => !type || r.type === type) : [];
  const count = (p) => (d ? d.recommendations.filter((r) => r.priority === p).length : 0);

  return (
    <div>
      <PageHeader title="Recommendations" subtitle="Prototype Decision Support: planning suggestions generated from gaps, forecasts, nearby surplus capacity and transition fit.">
        <DemoNote />
      </PageHeader>

      <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900" role="note">
        <b>Prototype Decision Support.</b> {d?.disclaimer || 'These suggestions are not automatic government decisions or official recommendations.'}
      </div>

      <Card className="mb-4" title="Selection">
        <div className="grid gap-3 sm:grid-cols-3">
          <Select label="Planning year" value={year} onChange={setYear} options={[2026, 2027, 2028].map((y) => ({ value: String(y), label: yearLabel(y) }))} />
          <Select label="District focus (geographic balancing)" value={districtId} onChange={setDistrictId} placeholder="All demo districts"
            options={(lists.data?.districts || []).map((x) => ({ value: x.district_id, label: x.district_name }))} />
          <Select label="Type" value={type} onChange={setType} placeholder="All types" options={types.map((t) => ({ value: t, label: t }))} />
        </div>
      </Card>

      {rec.error && <ErrorState error={rec.error} onRetry={rec.reload} />}
      {!d && rec.loading && <Loading label="Generating recommendations..." />}

      {d && (
        <div className={rec.loading ? 'opacity-70 transition-opacity' : ''}>
          <div className="mb-3 flex flex-wrap items-center gap-3 text-sm">
            <span className="font-semibold">{shown.length} of {d.count} suggestions</span>
            <span className="flex items-center gap-1"><StatusBadge kind="priority" value="HIGH" /> {count('HIGH')}</span>
            <span className="flex items-center gap-1"><StatusBadge kind="priority" value="MEDIUM" /> {count('MEDIUM')}</span>
            <span className="flex items-center gap-1"><StatusBadge kind="priority" value="LOW" /> {count('LOW')}</span>
          </div>
          {shown.length === 0 ? <EmptyState title="No suggestions" message="Nothing matches this selection." /> : (
            <ol className="space-y-3">
              {shown.map((r) => (
                <li key={r.id} className="card p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-400">{r.id}</span>
                      <span className="badge border-brand-200 bg-brand-50 text-brand-800">{r.type}</span>
                      <StatusBadge kind="priority" value={r.priority} />
                    </div>
                    <span className="text-xs text-slate-500">{r.label}</span>
                  </div>
                  <h2 className="mt-2 text-sm font-semibold">{r.title}</h2>
                  <p className="mt-1 text-sm text-slate-700">{r.text}</p>
                  <details className="mt-2 text-xs">
                    <summary className="cursor-pointer font-medium text-slate-600">Evidence</summary>
                    <dl className="mt-2 grid gap-x-4 gap-y-1 sm:grid-cols-[200px_1fr]">
                      {Object.entries(r.evidence).map(([k, v]) => (
                        <div key={k} className="contents"><dt className="text-slate-500">{k.replaceAll('_', ' ')}</dt><dd className="text-slate-800">{fmt(k, v)}</dd></div>
                      ))}
                    </dl>
                  </details>
                  <div className="mt-2 flex gap-4 text-xs">
                    {r.type === 'Geographic balancing' && <Link className="text-brand-700 underline" to="/gis">Open in Skill Gap GIS</Link>}
                    {r.type === 'Introduce bridge training' && <Link className="text-brand-700 underline" to="/transition">Open Workforce Transition</Link>}
                    {['Increase training seats', 'Redirect training capacity'].includes(r.type) && <Link className="text-brand-700 underline" to="/what-if">Try it in the What-If Planner</Link>}
                  </div>
                </li>
              ))}
            </ol>
          )}
          <div className="mt-4"><Explain data={d.explainability} /></div>
          <DemoNote className="mt-3" />
        </div>
      )}
    </div>
  );
}
