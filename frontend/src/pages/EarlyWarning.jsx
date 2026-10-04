import { useState } from 'react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Card, DemoNote, EmptyState, ErrorState, Explain, Loading, Mono, PageHeader, Select, StatusBadge } from '../components/ui';
import { EW_COLOR } from '../utils/colors';
import { n0, pct } from '../utils/format';

const SEV = { CRITICAL: 'border-red-300 bg-red-50', GROWING: 'border-amber-300 bg-amber-50' };

export default function EarlyWarning() {
  const [skillId, setSkillId] = useState('S01');
  const [districtId, setDistrictId] = useState('');
  const lists = useApi(async (s) => {
    const [d] = await Promise.all([api.districts(s)]);
    return d.districts;
  }, []);
  const ew = useApi((s) => api.earlyWarning({ district_id: districtId }, s), [districtId]);

  const d = ew.data;
  const focus = d?.skills.find((s) => s.skill_id === skillId);
  const cards = d ? (skillId ? d.cards.filter((c) => c.skill_id === skillId) : d.cards.slice(0, 18)) : [];

  return (
    <div>
      <PageHeader title="Early Warning System" subtitle="Prototype Early Warning: forecast demand compared with available training capacity for 2026, 2027 and 2028.">
        <DemoNote />
      </PageHeader>

      <Card className="mb-4" title="Selection">
        <div className="grid gap-3 sm:grid-cols-2">
          <Select label="Skill" value={skillId} onChange={setSkillId} placeholder="All skills (cards for the top 18 warnings)"
            options={(d?.skills || []).map((s) => ({ value: s.skill_id, label: s.skill_name })).sort((a, b) => a.label.localeCompare(b.label))} />
          <Select label="District" value={districtId} onChange={setDistrictId} placeholder="All demo districts"
            options={(lists.data || []).map((x) => ({ value: x.district_id, label: x.district_name }))} />
        </div>
      </Card>

      {ew.error && <ErrorState error={ew.error} onRetry={ew.reload} />}
      {!d && ew.loading && <Loading />}

      {d && (
        <div className={ew.loading ? 'opacity-70 transition-opacity' : ''}>
          {focus ? (
            <Card className="mb-4" title={`${focus.skill_name}: ${d.label}`} subtitle={`${d.district_name} · ${focus.industry_name} · demand growth ${focus.demand_cagr_pct}%/yr (2026-2028)`}>
              <div className="grid gap-3 md:grid-cols-3">
                {focus.timeline.map((t) => (
                  <div key={t.year} className="rounded-lg border-2 p-4" style={{ borderColor: EW_COLOR[t.status] }}>
                    <div className="flex items-center justify-between">
                      <div className="text-lg font-bold">{t.year}</div>
                      <StatusBadge kind="ew" value={t.status} />
                    </div>
                    <div className="mt-1 text-xs text-slate-500">{t.is_forecast ? 'Prototype Forecast' : 'Demo data (current)'} &middot; {t.confidence_label}</div>
                    <dl className="mt-3 grid grid-cols-3 gap-2 text-sm">
                      <div><dt className="text-xs text-slate-500">Demand</dt><dd className="font-semibold">{n0(t.demand)}</dd></div>
                      <div><dt className="text-xs text-slate-500">Capacity</dt><dd className="font-semibold">{n0(t.capacity)}</dd></div>
                      <div><dt className="text-xs text-slate-500">Gap</dt><dd className="font-semibold">{n0(t.gap)} <span className="text-xs text-slate-500">({pct(t.gap_ratio, 0)})</span></dd></div>
                    </dl>
                  </div>
                ))}
              </div>
              <div className="mt-3"><Mono>{focus.timeline[focus.timeline.length - 1].calculation}</Mono></div>
            </Card>
          ) : null}

          <div className="mb-4">
            <h2 className="mb-2 text-sm font-semibold text-slate-900">Warning cards</h2>
            {cards.length === 0 ? <EmptyState title="No warnings" message="This skill stays LOW (capacity roughly meets forecast demand) in every year for this selection." /> : (
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {cards.map((c, i) => (
                  <div key={`${c.skill_id}-${c.type}-${i}`} className={`rounded-lg border p-3 ${SEV[c.severity] || 'border-slate-200 bg-white'}`} role="group" aria-label={c.type}>
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-bold">{c.type}</div>
                      <StatusBadge kind="ew" value={c.severity} />
                    </div>
                    <p className="mt-1 text-sm text-slate-800">{c.message}</p>
                    <div className="mt-2 flex gap-1 text-xs text-slate-500">{c.statuses.map((s, j) => <span key={j}>{2026 + j}: {s}</span>)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Card title="All skills" subtitle={d.rule} pad={false}>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr><th className="th">Skill</th><th className="th">Industry</th><th className="th">2026</th><th className="th">2027</th><th className="th">2028</th><th className="th">Demand growth</th></tr></thead>
                <tbody>
                  {d.skills.map((s) => (
                    <tr key={s.skill_id} className={`cursor-pointer hover:bg-slate-50 ${s.skill_id === skillId ? 'bg-brand-50' : ''}`} onClick={() => setSkillId(s.skill_id)}>
                      <td className="td font-medium">{s.skill_name}</td><td className="td text-slate-600">{s.industry_name}</td>
                      {s.timeline.map((t) => <td key={t.year} className="td"><StatusBadge kind="ew" value={t.status} /></td>)}
                      <td className="td">{s.demand_cagr_pct}%/yr</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <div className="mt-4"><Explain data={d.explainability} /></div>
        </div>
      )}
    </div>
  );
}
