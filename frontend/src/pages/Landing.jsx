import { Link } from 'react-router-dom';
import { DEMO_LABEL } from '../utils/format';

const MODULES = [
  { to: '/gis', title: 'Skill Gap GIS', text: 'District-level demand vs training capacity on a Maharashtra map, with nearest surplus capacity.' },
  { to: '/radar', title: 'Industry Transition Radar', text: 'Growing, stable and declining industries and the bridge from one to another.' },
  { to: '/transition', title: 'Workforce Transition Engine', text: 'Transparent Transfer Fit Score, matched and missing skills, bridge training. Includes the job-description skill extractor.' },
  { to: '/what-if', title: 'What-If Scenario Planner', text: 'Change demand growth and training capacity and watch the gap recalculate live.' },
  { to: '/early-warning', title: 'Early Warning System', text: 'Prototype LOW / GROWING / CRITICAL signals for 2026-2028 per skill.' },
];

const STORY = [
  ['Dashboard', '/dashboard', 'Maharashtra pilot overview'],
  ['Skill Gap GIS', '/gis', 'EV Technician in Pune: shortage'],
  ['Find nearby surplus', '/gis', 'Nashik has spare training capacity'],
  ['Industry Radar', '/radar', 'ICE declining, EV / Battery growing'],
  ['Workforce Transition', '/transition', 'ICE Technician to EV Technician'],
  ['What-If Planner', '/what-if', 'Raise demand, then raise capacity'],
  ['Early Warning', '/early-warning', 'EV Technician: LOW, GROWING, CRITICAL'],
  ['Recommendations', '/recommendations', 'Actionable planning suggestions'],
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="bg-amber-100 px-4 py-1.5 text-center text-xs font-semibold text-amber-900">
        DEMO MODE &middot; Using prototype/demo data &middot; {DEMO_LABEL}
      </div>
      <header className="bg-brand-900 text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="text-lg font-bold tracking-wide">SKILLPULSE INDIA</div>
          <Link to="/login" className="rounded border border-brand-300 px-3 py-1 text-sm hover:bg-brand-800">Planner sign-in</Link>
        </div>
        <div className="mx-auto max-w-6xl px-4 pb-14 pt-8">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-200">Smart India Hackathon 2026 &middot; Maharashtra pilot prototype</p>
          <h1 className="mt-2 text-3xl font-bold text-white sm:text-4xl">SKILLPULSE INDIA</h1>
          <p className="mt-2 text-xl text-brand-100">From Labour Market Signals to Actionable Skill Planning</p>
          <p className="mt-4 max-w-3xl text-sm leading-relaxed text-brand-100">
            SkillPulse combines job-market signals, training capacity and industry signals to identify skill gaps, forecast future
            demand, support workforce transitions and help planners make evidence-based training decisions.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/dashboard" className="btn bg-white text-brand-900 hover:bg-brand-50">Explore Dashboard</Link>
            <Link to="/gis" className="btn border border-white/60 text-white hover:bg-brand-800">View Skill Gaps</Link>
            <Link to="/transition" className="btn border border-white/60 text-white hover:bg-brand-800">Run Transition Analysis</Link>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-10 px-4 py-10">
        <section aria-labelledby="modules">
          <h2 id="modules" className="text-lg font-bold">Five planning modules</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {MODULES.map((m) => (
              <Link key={m.to} to={m.to} className="card block p-4 transition-shadow hover:shadow-md">
                <div className="font-semibold text-brand-800">{m.title}</div>
                <p className="mt-1 text-sm text-slate-600">{m.text}</p>
              </Link>
            ))}
            <Link to="/methodology" className="card block p-4 transition-shadow hover:shadow-md">
              <div className="font-semibold text-brand-800">Methodology</div>
              <p className="mt-1 text-sm text-slate-600">The full pipeline from data ingestion to decision support, and what is demo versus proposed official data.</p>
            </Link>
          </div>
        </section>

        <section aria-labelledby="story">
          <h2 id="story" className="text-lg font-bold">3-5 minute demo walkthrough</h2>
          <ol className="mt-4 grid gap-3 sm:grid-cols-2">
            {STORY.map(([t, to, d], i) => (
              <li key={t}>
                <Link to={to} className="card flex items-start gap-3 p-3 hover:shadow-md">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-700 text-sm font-bold text-white">{i + 1}</span>
                  <span>
                    <span className="block text-sm font-semibold">{t}</span>
                    <span className="block text-xs text-slate-600">{d}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ol>
        </section>

        <section className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
          <b>Please note.</b> Every number in this prototype comes from a fictional demo dataset. Nothing here is sourced from PLFS, NCS,
          e-Shram, MSDE, NSQF or any other official dataset. Forecasts are &ldquo;Prototype Forecast&rdquo; and recommendations are
          &ldquo;Prototype Decision Support&rdquo;; all of it requires validation with official datasets before real use.
        </section>
      </main>
    </div>
  );
}
