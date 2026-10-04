import { useState } from 'react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';
import { Arrow, Card, Chips, EmptyState, ErrorState, Explain, Mono } from './ui';

const SAMPLE =
  'Looking for an EV technician with experience in battery management systems, vehicle diagnostics, electrical systems and high-voltage safety.';

function Highlighted({ text, spans }) {
  const out = [];
  let pos = 0;
  spans.forEach((s, i) => {
    if (s.start > pos) out.push(<span key={`t${i}`}>{text.slice(pos, s.start)}</span>);
    out.push(
      <mark key={`m${i}`} className="rounded bg-amber-200 px-0.5 text-slate-900" title={`${s.canonical} (${s.category})`}>
        {text.slice(s.start, s.end)}
      </mark>,
    );
    pos = s.end;
  });
  if (pos < text.length) out.push(<span key="end">{text.slice(pos)}</span>);
  return <p className="rounded border border-slate-200 bg-white p-3 text-sm leading-relaxed">{out}</p>;
}

export default function SkillExtractor() {
  const [text, setText] = useState(SAMPLE);
  const [state, setState] = useState({ loading: false, error: null, data: null });
  const sample = useApi((s) => api.nlpSample(s), []);
  const [demoIdx, setDemoIdx] = useState(0);

  const run = async () => {
    setState({ loading: true, error: null, data: state.data });
    try {
      const data = await api.extractSkills({ text });
      setState({ loading: false, error: null, data });
    } catch (error) {
      setState({ loading: false, error, data: null });
    }
  };

  const loadDemoJob = () => {
    const jobs = sample.data?.demo_job_descriptions || [];
    if (jobs.length === 0) return;
    setText(jobs[demoIdx % jobs.length].description);
    setDemoIdx((i) => i + 1);
  };

  const r = state.data;
  return (
    <div className="space-y-4">
      <Card title="Job Description Skill Extractor" subtitle="Demonstration of the NLP pipeline: rule-based phrase matching against a skill taxonomy (not an LLM).">
        <label className="block">
          <span className="label">Job description</span>
          <textarea className="input min-h-[110px]" value={text} onChange={(e) => setText(e.target.value)} maxLength={5000} />
        </label>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" className="btn-primary" onClick={run} disabled={state.loading || text.trim().length < 3}>
            {state.loading ? 'Extracting...' : 'Extract Skills'}
          </button>
          <button type="button" className="btn-secondary" onClick={() => setText(SAMPLE)}>Use example</button>
          <button type="button" className="btn-secondary" onClick={loadDemoJob} disabled={!sample.data}>Load a demo job posting</button>
        </div>
      </Card>

      {state.error && <ErrorState error={state.error} />}
      {!r && !state.error && <EmptyState title="No extraction yet" message="Click Extract Skills to run the pipeline on the text above." />}

      {r && (
        <>
          <Card title="Processing pipeline">
            <ol className="grid gap-2 md:grid-cols-4">
              {r.stages.map((s, i) => (
                <li key={s.stage} className="relative rounded-lg border border-brand-200 bg-brand-50 p-3">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-brand-700">Step {i + 1}</div>
                  <div className="text-sm font-semibold">{s.stage}</div>
                  <div className="mt-0.5 text-xs text-slate-600">{s.detail}</div>
                </li>
              ))}
            </ol>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="Extracted phrases" subtitle="Highlighted in the analysed text">
              <Highlighted text={r.input_text} spans={r.extracted} />
              {r.extracted.length === 0 && <p className="mt-2 text-sm text-slate-500">No taxonomy phrases were found in this text.</p>}
              <table className="mt-3 w-full">
                <thead><tr><th className="th">Phrase in text</th><th className="th">Normalised skill</th></tr></thead>
                <tbody>
                  {r.extracted.map((s) => (
                    <tr key={`${s.start}-${s.alias}`}><td className="td">{s.matched_text}</td><td className="td font-medium">{s.canonical}</td></tr>
                  ))}
                </tbody>
              </table>
            </Card>

            <Card title="Normalized skills &rarr; occupation mapping">
              <Chips items={r.normalized_skills} tone="bg-brand-50 text-brand-800 border-brand-200" empty="No skills found" />
              <Arrow className="my-2" />
              {r.occupations.length === 0 ? <p className="text-sm text-slate-500">No occupation matched.</p> : (
                <ol className="space-y-3">
                  {r.occupations.map((o, i) => (
                    <li key={o.occupation} className={`rounded border p-3 ${i === 0 ? 'border-green-300 bg-green-50' : 'border-slate-200 bg-white'}`}>
                      <div className="flex items-center justify-between">
                        <div className="font-semibold">{o.occupation} {i === 0 && <span className="badge ml-1 border-green-300 bg-white text-green-800">Best match</span>}</div>
                        <div className="text-sm font-bold">{o.score}%</div>
                      </div>
                      <div className="mt-1 h-2 rounded bg-slate-200"><div className="h-2 rounded bg-brand-600" style={{ width: `${Math.min(o.score, 100)}%` }} /></div>
                      <div className="mt-2 text-xs text-slate-600">Matched: {o.matched_competencies.join(', ') || 'none'}</div>
                      <div className="mt-1"><Mono>{o.calculation}</Mono></div>
                    </li>
                  ))}
                </ol>
              )}
            </Card>
          </div>
          <Explain data={r.explainability} />
        </>
      )}
    </div>
  );
}
