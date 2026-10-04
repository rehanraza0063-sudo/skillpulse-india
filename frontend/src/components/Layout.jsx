import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { logout } from '../utils/auth';
import { DEMO_LABEL } from '../utils/format';

export const NAV = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/gis', label: 'Skill Gap GIS' },
  { to: '/radar', label: 'Industry Radar' },
  { to: '/transition', label: 'Workforce Transition' },
  { to: '/what-if', label: 'What-If Planner' },
  { to: '/early-warning', label: 'Early Warning' },
  { to: '/data', label: 'Data Explorer' },
  { to: '/recommendations', label: 'Recommendations' },
  { to: '/methodology', label: 'Methodology' },
];

const linkClass = ({ isActive }) =>
  `block whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium ${
    isActive ? 'bg-brand-700 text-white' : 'text-slate-700 hover:bg-slate-200'
  }`;

export default function Layout() {
  const navigate = useNavigate();
  const onLogout = () => {
    logout();
    navigate('/');
  };
  return (
    <div className="flex min-h-screen flex-col">
      <div role="note" className="bg-amber-100 px-4 py-1.5 text-center text-xs font-semibold text-amber-900">
        DEMO MODE &middot; Using prototype/demo data &middot; {DEMO_LABEL}
      </div>
      <header className="border-b border-slate-200 bg-brand-900 text-white">
        <div className="mx-auto flex max-w-[1500px] items-center justify-between gap-4 px-4 py-3">
          <NavLink to="/" className="block">
            <div className="text-lg font-bold tracking-wide">SKILLPULSE INDIA</div>
            <div className="text-xs text-brand-200">From Labour Market Signals to Actionable Skill Planning</div>
          </NavLink>
          <div className="flex items-center gap-3 text-xs">
            <span className="hidden rounded bg-brand-800 px-2 py-1 sm:inline">Maharashtra Pilot</span>
            <span className="hidden sm:inline">Planner</span>
            <button type="button" onClick={onLogout} className="rounded border border-brand-400 px-3 py-1 hover:bg-brand-800">
              Sign out
            </button>
          </div>
        </div>
      </header>
      <nav aria-label="Primary" className="overflow-x-auto border-b border-slate-200 bg-white p-2 lg:hidden">
        <div className="flex gap-1">
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} className={linkClass}>
              {n.label}
            </NavLink>
          ))}
        </div>
      </nav>
      <div className="mx-auto flex w-full max-w-[1500px] flex-1 gap-5 px-4 py-5">
        <aside className="hidden w-56 shrink-0 lg:block">
          <nav aria-label="Primary" className="sticky top-4 space-y-1">
            {NAV.map((n) => (
              <NavLink key={n.to} to={n.to} className={linkClass}>
                {n.label}
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
      <footer className="border-t border-slate-200 bg-white px-4 py-3 text-center text-xs text-slate-500">
        {DEMO_LABEL} &middot; Forecasts are &ldquo;Prototype Forecast&rdquo; &middot; Recommendations are &ldquo;Prototype Decision Support&rdquo; &middot; Requires validation with official datasets
      </footer>
    </div>
  );
}
