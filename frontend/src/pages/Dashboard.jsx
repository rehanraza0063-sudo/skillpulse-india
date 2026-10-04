import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Card, DemoNote, EmptyState, ErrorState, KpiCard, Loading, PageHeader, Select, StatusBadge } from '../components/ui';
import { DemandCapacityChart, IndustryGrowthChart, RankedBarChart, TrendChart } from '../charts/DashboardCharts';
import { C } from '../utils/colors';
import { YEARS_ALL, yearLabel } from '../utils/format';

const EMPTY = { district_id: '', industry_id: '', occupation_id: '', skill_id: '', year: '2026' };

export default function Dashboard() {
  const [f, setF] = useState(EMPTY);
  const set = (k) => (v) => setF((s) => ({ ...s, [k]: v }));

  const opts = useApi(async (signal) => {
    const [d, s, o] = await Promise.all([api.districts(signal), api.skills(signal), api.occupations(signal)]);
    const industries = [...new Map(s.skills.map((x) => [x.industry_id, x.industry_name])).entries()];
    return { districts: d.districts, skills: s.skills, occupations: o.occupations, industries };
  }, []);

  const dash = useApi((signal) => api.dashboard(f, signal), [f.district_id, f.industry_id, f.occupation_id, f.skill_id, f.year]);

  const d = dash.data;
  const m = d?.meta;
  const k = d?.kpis;
  const filtersActive = f.district_id || f.industry_id || f.occupation_id || f.skill_id || f.year !== '2026';

  return (
    <div>
      <PageHeader title="Planner Dashboard" subtitle="Overall labour-market and training situation for the Maharashtra pilot. All values update with the filters.">
        <DemoNote />
      </PageHeader>

      <div className="card mb-4 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
        <Meta label="Region" value="Maharashtra Pilot" />
        <Meta label="Dataset" value="Demo Dataset" />
        <Meta label="Last updated" value={m?.last_updated || '-'} />
        <div>
          <div className="label">Data confidence</div>
          {m?.data_confidence ? (
            <div className="flex items-center gap-2" title={m.data_confidence.note}>
              <StatusBadge kind="level" value={m.data_confidence.label} />
              <span className="text-xs text-slate-500">prototype model, demo data</span>
            </div>
          ) : <span className="text-sm text-slate-400">-</span>}
        </div>
      </div>

      <Card className="mb-4" title="Filters" actions={filtersActive && <button type="button" className="btn-secondary" onClick={() => setF(EMPTY)}>Reset filters</button>}>
        {opts.error ? <ErrorState error={opts.error} onRetry={opts.reload} /> : opts.loading && !opts.data ? <Loading /> : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Select label="District" value={f.district_id} onChange={set('district_id')} placeholder="All districts"
              options={opts.data.districts.map((x) => ({ value: x.district_id, label: x.district_name }))} />
            <Select label="Industry" value={f.industry_id} onChange={set('industry_id')} placeholder="All industries"
              options={opts.data.industries.map(([v, l]) => ({ value: v, label: l }))} />
            <Select label="Occupation" value={f.occupation_id} onChange={set('occupation_id')} placeholder="All occupations"
              options={opts.data.occupations.map((x) => ({ value: x.occupation_id, label: x.occupation_name }))} />
            <Select label="Skill" value={f.skill_id} onChange={set('skill_id')} placeholder="All skills"
              options={opts.data.skills.map((x) => ({ value: x.skill_id, label: x.skill_name }))} />
            <Select label="Year" value={f.year} onChange={set('year')}
              options={YEARS_ALL.map((y) => ({ value: String(y), label: yearLabel(y) }))} />
          </div>
        )}
      </Card>

      {dash.error && <ErrorState error={dash.error} onRetry={dash.reload} />}
      {!d && dash.loading && <Loading label="Computing dashboard..." />}
      {d?.empty && <EmptyState title="No data for these filters" message={d.message + ' Try resetting one of the filters (an occupation belongs to one skill and one industry).'}>
        <button type="button" className="btn-primary" onClick={() => setF(EMPTY)}>Reset filters</button></EmptyState>}

      {d && !d.empty && (
        <div className={dash.loading ? 'opacity-60 transition-opacity' : ''}>
          {m.is_forecast_year && <p className="mb-3 rounded border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900">Showing {m.year} values from the <b>Prototype Forecast</b> (linear trend on 2023-2026 demo data; training capacity held at the 2026 level).</p>}
          <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            <KpiCard label="Districts covered" value={k.districts_covered} />
            <KpiCard label="Skills tracked" value={k.skills_tracked} />
            <KpiCard label="Shortage skills" value={k.shortage_skills} tone="text-red-700" hint={`gap ratio > ${d.thresholds.shortage_above * 100}%`} />
            <KpiCard label="Surplus skills" value={k.surplus_skills} tone="text-blue-700" hint={`gap ratio < ${d.thresholds.surplus_below * 100}%`} />
            <KpiCard label="Growing industries" value={k.growing_industries} tone="text-green-700" hint="forecast growth above 8%/yr" />
            <KpiCard label="Transition opportunities" value={k.transition_opportunities} tone="text-brand-700" hint="declining to growing roles" />
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            <Card title="A. Demand vs training capacity" subtitle={`By skill, ${yearLabel(m.year)}`} className="xl:col-span-2">
              <DemandCapacityChart data={d.demand_vs_capacity} />
            </Card>
            <Card title="B. Top skill shortages" subtitle="Largest gaps (forecast demand minus capacity), seats">
              <RankedBarChart data={d.top_shortages} valueKey="gap" color={C.gap} name="Shortage (seats)" empty="No skills are classified as SHORTAGE for this selection." />
            </Card>
            <Card title="C. Top skill surplus" subtitle="Training capacity above demand, seats">
              <RankedBarChart data={d.top_surplus} valueKey="surplus" color={C.surplus} name="Surplus (seats)" empty="No skills are classified as SURPLUS for this selection." />
            </Card>
            <Card title="D. Future demand trend" subtitle="Historical 2023-2026 and Prototype Forecast 2027-2028 (80% range)">
              <TrendChart data={d.future_trend} />
            </Card>
            <Card title="E. Industry growth / decline" subtitle="Forecast demand growth per year, 2026 to 2028 (Prototype Forecast)">
              <IndustryGrowthChart data={d.industry_growth} />
            </Card>
            <Card title="F. Early warning skills" subtitle="Prototype Early Warning, top skills by 2028 gap" className="xl:col-span-2"
              actions={<Link to="/early-warning" className="text-xs font-medium text-brand-700 underline">Open Early Warning</Link>}>
              {d.early_warning.length === 0 ? <p className="text-sm text-slate-500">No skills to show.</p> : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead><tr><th className="th">Skill</th><th className="th">2026</th><th className="th">2027</th><th className="th">2028</th></tr></thead>
                    <tbody>
                      {d.early_warning.map((s) => (
                        <tr key={s.skill_id}>
                          <td className="td font-medium">{s.skill_name}</td>
                          {['2026', '2027', '2028'].map((y) => <td key={y} className="td"><StatusBadge kind="ew" value={s.statuses[y]} /></td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Card>
          </div>
          <DemoNote className="mt-4" />
        </div>
      )}
    </div>
  );
}

function Meta({ label, value }) {
  return (
    <div>
      <div className="label">{label}</div>
      <div className="text-sm font-semibold text-slate-900">{value}</div>
    </div>
  );
}
