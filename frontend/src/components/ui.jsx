import { DEMO_LABEL } from '../utils/format';

const TONES = {
  gap: {
    SHORTAGE: 'bg-red-50 text-red-800 border-red-300',
    BALANCED: 'bg-green-50 text-green-800 border-green-300',
    SURPLUS: 'bg-blue-50 text-blue-800 border-blue-300',
  },
  ew: {
    LOW: 'bg-green-50 text-green-800 border-green-300',
    GROWING: 'bg-amber-50 text-amber-800 border-amber-300',
    CRITICAL: 'bg-red-50 text-red-800 border-red-300',
  },
  outlook: {
    GROWING: 'bg-green-50 text-green-800 border-green-300',
    STABLE: 'bg-slate-100 text-slate-700 border-slate-300',
    DECLINING: 'bg-red-50 text-red-800 border-red-300',
  },
  level: {
    HIGH: 'bg-green-50 text-green-800 border-green-300',
    MODERATE: 'bg-amber-50 text-amber-800 border-amber-300',
    MEDIUM: 'bg-amber-50 text-amber-800 border-amber-300',
    LOW: 'bg-red-50 text-red-800 border-red-300',
  },
  priority: {
    HIGH: 'bg-red-50 text-red-800 border-red-300',
    MEDIUM: 'bg-amber-50 text-amber-800 border-amber-300',
    LOW: 'bg-slate-100 text-slate-700 border-slate-300',
  },
};
const FALLBACK = 'bg-slate-100 text-slate-700 border-slate-300';

export function StatusBadge({ value, kind = 'gap', className = '' }) {
  if (!value) return null;
  const tone = (TONES[kind] && TONES[kind][value]) || FALLBACK;
  return <span className={`badge ${tone} ${className}`}>{value}</span>;
}

export function Card({ title, subtitle, actions, children, className = '', pad = true }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="flex flex-wrap items-start justify-between gap-2 border-b border-slate-100 px-4 py-3">
          <div>
            {title && <h2 className="text-sm font-semibold text-slate-900">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {actions}
        </header>
      )}
      <div className={pad ? 'p-4' : ''}>{children}</div>
    </section>
  );
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-bold tracking-tight sm:text-2xl">{title}</h1>
        {subtitle && <p className="mt-1 max-w-3xl text-sm text-slate-600">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

export function KpiCard({ label, value, hint, tone = 'text-slate-900' }) {
  return (
    <div className="card p-4">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-3xl font-bold ${tone}`}>{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

export function Loading({ label = 'Loading...' }) {
  return (
    <div role="status" aria-live="polite" className="flex items-center justify-center gap-3 p-8 text-sm text-slate-500">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
      {label}
    </div>
  );
}

export function ErrorState({ error, onRetry }) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <div className="font-semibold">Something went wrong</div>
      <p className="mt-1">{error?.message || 'Unknown error'}</p>
      {onRetry && (
        <button type="button" className="btn-secondary mt-3" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title = 'Nothing to show', message, children }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
      <div className="text-sm font-semibold text-slate-700">{title}</div>
      {message && <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">{message}</p>}
      {children && <div className="mt-3">{children}</div>}
    </div>
  );
}

export function Field({ label, children, className = '' }) {
  return (
    <label className={`block ${className}`}>
      <span className="label">{label}</span>
      {children}
    </label>
  );
}

export function Select({ label, value, onChange, options, className = '', placeholder }) {
  return (
    <Field label={label} className={className}>
      <select className="input" value={value ?? ''} onChange={(e) => onChange(e.target.value)}>
        {placeholder !== undefined && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </Field>
  );
}

export function Explain({ data, title = 'Explainability' }) {
  if (!data) return null;
  const rows = [
    ['Method', data.method],
    ['Inputs', data.inputs],
    ['Output', data.output],
    ['Confidence / limitations', data.limitations],
  ];
  return (
    <details className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm" open>
      <summary className="cursor-pointer text-sm font-semibold text-slate-800">{title}</summary>
      <dl className="mt-2 grid gap-x-4 gap-y-2 sm:grid-cols-[170px_1fr]">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="font-medium text-slate-500">{k}</dt>
            <dd className="text-slate-700">{v}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}

export function Chips({ items, tone = 'bg-slate-100 text-slate-700 border-slate-300', empty = 'None' }) {
  if (!items || items.length === 0) return <span className="text-sm text-slate-400">{empty}</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((i) => (
        <span key={typeof i === 'string' ? i : i.label} className={`badge ${tone}`}>
          {typeof i === 'string' ? i : i.label}
        </span>
      ))}
    </div>
  );
}

export function DemoNote({ className = '' }) {
  return <p className={`text-xs text-slate-500 ${className}`}>{DEMO_LABEL}</p>;
}

export function Mono({ children }) {
  return <code className="block whitespace-pre-wrap rounded bg-slate-100 p-2 text-xs leading-relaxed text-slate-700">{children}</code>;
}

export function Arrow({ className = '' }) {
  return (
    <div aria-hidden="true" className={`flex justify-center text-slate-400 ${className}`}>
      <svg width="20" height="24" viewBox="0 0 20 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M10 2v18M4 14l6 7 6-7" />
      </svg>
    </div>
  );
}
