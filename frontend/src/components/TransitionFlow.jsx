import { Link } from 'react-router-dom';
import { Arrow, Chips } from './ui';

function Step({ tag, tone, children }) {
  return (
    <div className={`rounded-lg border p-3 ${tone}`}>
      <div className="text-[11px] font-bold uppercase tracking-wider opacity-80">{tag}</div>
      <div className="mt-1 text-sm">{children}</div>
    </div>
  );
}

/** DECLINING INDUSTRY -> TRANSFERABLE SKILLS -> GROWING INDUSTRY -> BRIDGE TRAINING -> TARGET OCCUPATION */
export default function TransitionFlow({ path }) {
  if (!path) return null;
  const transferable = [...path.matched_skills, ...path.partial_skills.filter((s) => !path.matched_skills.includes(s))];
  return (
    <div>
      <Step tag="Declining industry" tone="border-red-200 bg-red-50 text-red-900">
        <b>{path.from_industry}</b>
        <div className="text-xs">Occupation: {path.from_occupation}</div>
      </Step>
      <Arrow />
      <Step tag="Transferable skills" tone="border-slate-300 bg-white text-slate-800">
        <Chips items={path.matched_skills} tone="bg-green-50 text-green-800 border-green-300" empty="No directly matching skills" />
        {path.partial_skills.length > 0 && (
          <div className="mt-2">
            <div className="mb-1 text-xs text-slate-500">Partly transferable (related skill held)</div>
            <Chips items={path.partial_skills} tone="bg-amber-50 text-amber-800 border-amber-300" />
          </div>
        )}
        {transferable.length === 0 && <div className="mt-1 text-xs text-slate-500">Little overlap: expect a longer bridge.</div>}
      </Step>
      <Arrow />
      <Step tag="Growing industry" tone="border-green-200 bg-green-50 text-green-900">
        <b>{path.to_industry}</b>
      </Step>
      <Arrow />
      <Step tag="Bridge training" tone="border-amber-200 bg-amber-50 text-amber-900">
        <b>{path.bridge_programme}</b> <span className="text-xs">(about {path.bridge_weeks} weeks, illustrative)</span>
        <div className="mt-2"><Chips items={path.missing_skills} tone="bg-white text-red-800 border-red-300" empty="No missing skills" /></div>
      </Step>
      <Arrow />
      <Step tag="Target occupation" tone="border-brand-200 bg-brand-50 text-brand-900">
        <b>{path.to_occupation}</b>
        <div className="text-xs">Transfer Fit Score (prototype): {path.fit_score.toFixed(0)}%</div>
        <Link className="mt-1 inline-block text-xs font-medium text-brand-700 underline"
          to={`/transition?from=${encodeURIComponent(path.from_occupation)}&to=${encodeURIComponent(path.to_occupation)}`}>
          Analyze this transition
        </Link>
      </Step>
    </div>
  );
}
