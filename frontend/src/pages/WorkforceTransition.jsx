import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import SkillExtractor from '../components/SkillExtractor';
import { Arrow, Card, Chips, DemoNote, EmptyState, ErrorState, Explain, Loading, Mono, PageHeader, Select, StatusBadge } from '../components/ui';

const CREDIT_TONE = { MATCHED: 'text-green-700', PARTIAL: 'text-amber-700', MISSING: 'text-red-700' };

export default function WorkforceTransition() {
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') === 'extractor' ? 'extractor' : 'transition';
  const setTab = (t) => setParams(t === 'extractor' ? { tab: 'extractor' } : {});

  return (
    <div>
      <PageHeader title="Workforce Transition Engine" subtitle="Can workers in declining occupations move into growing ones? Transparent fit scoring, missing skills and bridge training.">
        <DemoNote />
      </PageHeader>
      <div role="tablist" aria-label="Workforce tools" className="mb-4 inline-flex rounded-lg border border-slate-300 bg-white p-1">
        {[['transition', 'Transition analysis'], ['extractor', 'Job description skill extractor']].map(([k, l]) => (
          <button key={k} type="button" role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
            className={`rounded-md px-4 py-1.5 text-sm font-medium ${tab === k ? 'bg-brand-700 text-white' : 'text-slate-700 hover:bg-slate-100'}`}>{l}</button>
        ))}
      </div>
      {tab === 'extractor' ? <SkillExtractor /> : <TransitionTool params={params} />}
    </div>
  );
}

function TransitionTool({ params }) {
  const occ = useApi((s) => api.occupations(s), []);
  const [current, setCurrent] = useState(params.get('from') || 'ICE Technician');
  const [target, setTarget] = useState(params.get('to') || 'EV Technician');
  const [skills, setSkills] = useState([]);
  const [extra, setExtra] = useState('');
  const [state, setState] = useState({ loading: false, error: null, data: null });

  const occByName = useMemo(() => Object.fromEntries((occ.data?.occupations || []).map((o) => [o.occupation_name, o])), [occ.data]);

  // the worker's skill profile starts from the current occupation's skills and can be edited
  useEffect(() => {
    const o = occByName[current];
    if (o) setSkills(o.competencies.map((c) => c.competency));
  }, [current, occByName]);

  const run = async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await api.transition({ current_occupation: current, target_occupation: target, current_skills: skills });
      setState({ loading: false, error: null, data });
    } catch (error) {
      setState({ loading: false, error, data: null });
    }
  };

  if (occ.error) return <ErrorState error={occ.error} onRetry={occ.reload} />;
  if (!occ.data) return <Loading />;

  const names = occ.data.occupations.map((o) => ({ value: o.occupation_name, label: o.occupation_name }));
  const addable = occ.data.competencies.filter((c) => !skills.includes(c.name));
  const r = state.data;

  return (
    <div className="space-y-4">
      <Card title="Worker profile">
        <div className="grid gap-3 sm:grid-cols-2">
          <Select label="Current occupation" value={current} onChange={setCurrent} options={names} />
          <Select label="Target occupation" value={target} onChange={setTarget} options={names} />
        </div>
        <div className="mt-4">
          <div className="label">Current skills (remove or add to customise the worker)</div>
          <div className="flex flex-wrap gap-1.5">
            {skills.map((s) => (
              <span key={s} className="badge gap-1 border-brand-200 bg-brand-50 text-brand-800">
                {s}
                <button type="button" aria-label={`Remove ${s}`} className="ml-1 font-bold text-brand-700 hover:text-red-700" onClick={() => setSkills(skills.filter((x) => x !== s))}>&times;</button>
              </span>
            ))}
            {skills.length === 0 && <span className="text-sm text-slate-400">No skills selected</span>}
          </div>
          <div className="mt-3 flex max-w-md gap-2">
            <select className="input" value={extra} onChange={(e) => setExtra(e.target.value)} aria-label="Add a skill">
              <option value="">Add another skill...</option>
              {addable.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
            <button type="button" className="btn-secondary" disabled={!extra} onClick={() => { setSkills([...skills, extra]); setExtra(''); }}>Add</button>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button type="button" className="btn-primary" onClick={run} disabled={state.loading}>{state.loading ? 'Analyzing...' : 'Analyze Transition'}</button>
          {current === target && <span className="text-xs text-amber-700">Current and target occupation are the same.</span>}
        </div>
      </Card>

      {state.error && <ErrorState error={state.error} />}
      {!r && !state.error && <EmptyState title="No analysis yet" message="Choose a current and target occupation, then click Analyze Transition." />}

      {r && (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            <Card title="Transfer Fit Score" subtitle="Prototype similarity measure" className="lg:col-span-1">
              <div className="flex items-end gap-3">
                <div className="text-5xl font-bold text-brand-800">{r.fit_score.toFixed(0)}<span className="text-2xl">%</span></div>
                <StatusBadge kind="level" value={r.fit_band} className="mb-2" />
              </div>
              <div className="mt-3 h-3 overflow-hidden rounded bg-slate-200" role="img" aria-label={`Fit score ${r.fit_score} percent`}>
                <div className="h-3 bg-brand-600" style={{ width: `${r.fit_score}%` }} />
              </div>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div><dt className="text-xs text-slate-500">Basic overlap</dt><dd className="font-semibold">{r.basic_overlap_pct.toFixed(0)}%</dd></div>
                <div><dt className="text-xs text-slate-500">Skill distance</dt><dd className="font-semibold">{r.skill_distance.toFixed(0)}</dd></div>
                <div><dt className="text-xs text-slate-500">Matched</dt><dd className="font-semibold text-green-700">{r.matched_skills.length}</dd></div>
                <div><dt className="text-xs text-slate-500">Missing / bridge</dt><dd className="font-semibold text-red-700">{r.missing_skills.length}</dd></div>
              </dl>
              <p className="mt-3 text-xs text-slate-500">Does not represent guaranteed employability.</p>
            </Card>

            <Card title="Employment pathway" className="lg:col-span-2">
              <div className="grid items-center gap-2 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
                {r.pathway.map((p, i) => (
                  <div key={p} className="contents">
                    <div className={`rounded-lg border p-3 text-center text-sm font-semibold ${i === 0 ? 'border-slate-300 bg-slate-50' : i === r.pathway.length - 1 ? 'border-green-300 bg-green-50 text-green-900' : 'border-amber-300 bg-amber-50 text-amber-900'}`}>{p}</div>
                    {i < r.pathway.length - 1 && <div aria-hidden="true" className="text-center text-xl text-slate-400">&rarr;</div>}
                  </div>
                ))}
              </div>
              <div className="mt-4 rounded border border-amber-200 bg-amber-50 p-3 text-sm">
                <div className="font-semibold text-amber-900">{r.bridge_training.name}</div>
                <div className="mt-1 text-xs text-amber-900">
                  About {r.bridge_training.duration_weeks} weeks &middot; roughly {r.bridge_training.estimated_bridge_hours} learning hours &middot; {r.bridge_training.source}
                </div>
                <div className="mt-2"><Chips items={r.bridge_training.modules} tone="bg-white text-amber-900 border-amber-300" empty="No bridge needed" /></div>
                <div className="mt-2 text-xs text-slate-600">{r.bridge_training.note}</div>
              </div>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <Card title="Matched skills"><Chips items={r.matched_skills} tone="bg-green-50 text-green-800 border-green-300" /></Card>
            <Card title="Partly transferable" subtitle="A related skill is held">
              {r.partial_skills.length === 0 ? <span className="text-sm text-slate-400">None</span> : (
                <ul className="space-y-1 text-sm">
                  {r.breakdown.filter((b) => b.status === 'PARTIAL').map((b) => (
                    <li key={b.competency}><b>{b.competency}</b><br /><span className="text-xs text-slate-500">from {b.related_skill_used} (credit {b.credit})</span></li>
                  ))}
                </ul>
              )}
            </Card>
            <Card title="Missing / bridge skills"><Chips items={r.missing_skills} tone="bg-red-50 text-red-800 border-red-300" empty="None" /></Card>
          </div>

          <Card title="How the score is calculated" subtitle="Every figure below is computed by code from the taxonomy data">
            <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-700">
              <li>Each target skill has an importance weight from 1 to 3.</li>
              <li>A skill the worker holds earns full credit (1.0). A related skill earns partial credit equal to its similarity (0 to 1). Otherwise 0.</li>
              <li>Fit = 100 &times; &Sigma;(weight &times; credit) / &Sigma;(weight). Skill distance = 100 &minus; Fit.</li>
            </ol>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full">
                <thead><tr><th className="th">Target skill</th><th className="th">Weight</th><th className="th">Status</th><th className="th">Credit</th><th className="th">Weight &times; credit</th><th className="th">Bridge hours</th></tr></thead>
                <tbody>
                  {r.breakdown.map((b) => (
                    <tr key={b.competency}>
                      <td className="td font-medium">{b.competency}</td><td className="td">{b.weight}</td>
                      <td className={`td font-semibold ${CREDIT_TONE[b.status]}`}>{b.status}</td>
                      <td className="td">{b.credit}</td><td className="td">{b.weighted_credit}</td><td className="td">{b.bridge_hours}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              <Mono>{`${r.calculation.formula}\n= ${r.calculation.result}`}</Mono>
              <Mono>{`${r.calculation.basic_formula}\n= ${r.calculation.basic_result}`}</Mono>
            </div>
          </Card>
          <Explain data={r.explainability} />
        </>
      )}
    </div>
  );
}
