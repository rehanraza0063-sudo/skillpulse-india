import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Arrow, Card, DemoNote, ErrorState, Loading, Mono, PageHeader } from '../components/ui';

const STEPS = [
  ['Data ingestion', 'Source adapters load tables. The prototype reads local demo CSV/JSON files; official adapters are documented stubs.', 'services/ingestion.py'],
  ['Data cleaning', 'Trim text, coerce numbers, drop duplicates and invalid rows, tag every row with source_type.', 'services/ingestion.py'],
  ['Normalization', 'Skill aliases (BMS, Battery Management) map to one canonical skill through the taxonomy.', 'ml/taxonomy.py'],
  ['Skill extraction', 'Rule-based phrase matching finds taxonomy skills in job descriptions. Not an LLM; replaceable behind an interface.', 'ml/nlp.py'],
  ['Occupation mapping', 'Occupations are scored by weighted coverage of their required skills (plus title mention).', 'ml/nlp.py'],
  ['Demand estimation', 'Demand per district, skill and year from the historical demand table.', 'services/engine.py'],
  ['Supply estimation', 'Training capacity (seats per year) per district and skill; centres hold seats and availability.', 'services/engine.py'],
  ['Forecasting', 'Linear regression of demand on year with an 80% prediction interval. Labelled Prototype Forecast.', 'ml/forecast.py'],
  ['Skill-gap calculation', 'Gap = forecast demand - training capacity; ratio = gap / demand; configurable SHORTAGE / BALANCED / SURPLUS thresholds.', 'services/engine.py'],
  ['GIS matching', 'Haversine distance between demo district coordinates finds the nearest SURPLUS district.', 'utils/geo.py'],
  ['Workforce transition', 'Weighted skill overlap with partial credit gives the Transfer Fit Score and the bridge skills.', 'ml/transition.py'],
  ['Scenario analysis', 'What-if arithmetic applies % changes to demand and capacity and reclassifies the gap.', 'services/planning.py'],
  ['Early warning', 'LOW / GROWING / CRITICAL (prototype classes) on the gap ratio for 2026-2028.', 'services/planning.py'],
  ['Planning recommendations', 'Rules over gaps, surplus, fit scores and trends produce Prototype Decision Support.', 'services/planning.py'],
];

const PROPOSED = [
  ['PLFS', 'Employment structure and labour-force indicators'],
  ['NCS', 'Job postings and vacancy signals'],
  ['e-Shram', 'Aggregated worker-registry supply data'],
  ['NCO-2015', 'Occupation classification backbone'],
  ['Industry hiring signals', 'Sector hiring outlook feeds'],
  ['Training / NSQF data', 'Training-centre seats, enrolment and qualification levels'],
];

function Box({ children, tone }) {
  return <div className={`rounded-lg border px-4 py-2.5 text-center text-sm font-semibold ${tone}`}>{children}</div>;
}

function FlowDiagram() {
  const input = 'border-slate-300 bg-slate-100 text-slate-800';
  const proc = 'border-brand-300 bg-brand-50 text-brand-900';
  const ana = 'border-brand-500 bg-brand-100 text-brand-900';
  const out = 'border-green-400 bg-green-50 text-green-900';
  return (
    <div className="mx-auto max-w-xl" role="img" aria-label="Architecture diagram from job market, training and industry data through ingestion, normalisation, mapping, forecasting and gap engine to dashboards and decision support">
      <div className="grid gap-2 sm:grid-cols-3">
        <Box tone={input}>Job Market Data</Box><Box tone={input}>Training Data</Box><Box tone={input}>Industry Signals</Box>
      </div>
      {[
        ['Data Ingestion', proc], ['Cleaning & Normalization', proc], ['NLP Skill / Occupation Mapping', proc], ['Demand + Supply Engine', proc],
        ['AI / ML Forecasting', ana], ['Skill Gap Engine', ana], ['GIS + Industry Radar + Transition Engine', ana], ['What-If + Early Warning', ana],
        ['Planner Dashboard', out], ['Decision Support (Prototype)', out],
      ].map(([t, tone]) => (
        <div key={t}><Arrow /><Box tone={tone}>{t}</Box></div>
      ))}
    </div>
  );
}

export default function Methodology() {
  const ds = useApi((s) => api.dataSources(s), []);
  const proposedApi = (ds.data?.sources || []).filter((s) => s.category !== 'DEMO');

  return (
    <div className="space-y-4">
      <PageHeader title="About / Methodology" subtitle="How SkillPulse turns labour-market signals into planning decisions, and what is real versus demo in this prototype.">
        <DemoNote />
      </PageHeader>

      <Card title="Pipeline architecture"><FlowDiagram /></Card>

      <Card title="The 14 pipeline steps">
        <ol className="grid gap-3 md:grid-cols-2">
          {STEPS.map(([t, d, where], i) => (
            <li key={t} className="flex gap-3 rounded-lg border border-slate-200 p-3">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-700 text-sm font-bold text-white">{i + 1}</span>
              <div><div className="text-sm font-semibold">{t}</div><p className="text-sm text-slate-600">{d}</p><code className="text-xs text-slate-500">backend/app/{where}</code></div>
            </li>
          ))}
        </ol>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Proposed official data sources" subtitle="NOT connected. Listed as the sources envisaged for a validated deployment.">
          <ul className="space-y-2">
            {PROPOSED.map(([n, d]) => {
              const hit = proposedApi.find((s) => s.name.startsWith(n.split(' ')[0]));
              return (
                <li key={n} className="rounded-lg border border-slate-200 p-3">
                  <div className="flex items-center justify-between"><span className="text-sm font-semibold">{n}</span>
                    <span className="badge border-slate-300 bg-slate-100 text-slate-700">Proposed, not connected</span></div>
                  <p className="text-sm text-slate-600">{d}</p>
                  {hit && <p className="mt-1 text-xs text-slate-500">{hit.integration_note}</p>}
                </li>
              );
            })}
          </ul>
        </Card>

        <Card title="Current prototype demo data" subtitle="What this prototype actually uses">
          <div className="rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            <b>Prototype/Demo Data &mdash; Not official statistics.</b> Fictional Maharashtra pilot dataset generated by <code>scripts/generate_demo_data.py</code>.
            No figure is taken from or claims to match any official source.
          </div>
          {ds.error && <div className="mt-3"><ErrorState error={ds.error} onRetry={ds.reload} /></div>}
          {!ds.data && ds.loading && <Loading />}
          {ds.data && (
            <>
              <p className="mt-3 text-xs text-slate-500">Database: {ds.data.database}</p>
              <table className="mt-2 w-full">
                <thead><tr><th className="th">Table</th><th className="th">Rows loaded</th><th className="th">Dropped</th><th className="th">Steps</th></tr></thead>
                <tbody>
                  {ds.data.ingestion_log.map((l) => (
                    <tr key={l.table}><td className="td font-medium">{l.table}</td><td className="td">{l.rows_loaded}</td>
                      <td className="td">{(l.dropped_duplicates || 0) + (l.dropped_invalid || 0)}</td><td className="td text-xs text-slate-500">{l.steps.join(', ')}</td></tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Formulas">
          <div className="space-y-2">
            <Mono>{'Forecast: OLS linear regression, demand ~ year (2023-2026), 80% prediction interval\nCapacity in forecast years: held at the 2026 level (configurable growth)'}</Mono>
            <Mono>{'Skill gap = forecast demand - training capacity\nGap ratio = gap / forecast demand\nSHORTAGE if ratio > 10%, SURPLUS if ratio < -10%, else BALANCED (configurable)'}</Mono>
            <Mono>{'Early warning (prototype): LOW <= 10%, GROWING <= 25%, CRITICAL above'}</Mono>
            <Mono>{'Transfer Fit = 100 x sum(weight x credit) / sum(weight)\ncredit = 1 (held), similarity (related skill), 0 (missing)\nBasic overlap = matched / target skills x 100'}</Mono>
          </div>
        </Card>
        <Card title="Honest limitations">
          <ul className="list-disc space-y-1.5 pl-5 text-sm text-slate-700">
            <li>All data is fictional demo data; results illustrate the method, not the real labour market.</li>
            <li>Forecasts use four yearly points and a linear trend. They are labelled Prototype Forecast and are not validated.</li>
            <li>The skill extractor is rule-based phrase matching, not a trained NLP model or LLM.</li>
            <li>Fit scores, similarity weights and bridge hours are illustrative placeholders.</li>
            <li>Distances are straight-line between district centre points, not road distances.</li>
            <li>Recommendations are Prototype Decision Support, not official government recommendations.</li>
            <li>The sign-in is a browser-side demo gate, not real authentication.</li>
            <li>Pilot first: Maharashtra pilot, then validation with official datasets, then scaling.</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
