import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { DEMO_PASS, DEMO_USER, isLoggedIn, login } from '../utils/auth';
import { DEMO_LABEL } from '../utils/format';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(DEMO_USER);
  const [pass, setPass] = useState('');
  const [error, setError] = useState('');
  const dest = location.state?.from || '/dashboard';

  if (isLoggedIn()) return <Navigate to={dest} replace />;

  const submit = (e) => {
    e.preventDefault();
    if (login(user, pass)) navigate(dest, { replace: true });
    else setError('Incorrect username or password. Use the demo credentials shown below.');
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-100">
      <div className="bg-amber-100 px-4 py-1.5 text-center text-xs font-semibold text-amber-900">
        DEMO MODE &middot; Using prototype/demo data
      </div>
      <div className="flex flex-1 items-center justify-center p-4">
        <form onSubmit={submit} className="card w-full max-w-sm p-6" aria-labelledby="login-title">
          <h1 id="login-title" className="text-xl font-bold">SKILLPULSE INDIA</h1>
          <p className="mt-1 text-sm text-slate-600">Planner sign-in (prototype)</p>
          <div className="mt-5 space-y-4">
            <label className="block">
              <span className="label">Username</span>
              <input className="input" value={user} onChange={(e) => setUser(e.target.value)} autoComplete="username" />
            </label>
            <label className="block">
              <span className="label">Password</span>
              <input className="input" type="password" value={pass} onChange={(e) => setPass(e.target.value)} autoComplete="current-password" />
            </label>
            {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
            <button type="submit" className="btn-primary w-full">Sign in</button>
          </div>
          <div className="mt-4 rounded bg-slate-50 p-3 text-xs text-slate-600">
            Demo credentials: <b>{DEMO_USER}</b> / <b>{DEMO_PASS}</b>
            <br />
            This is a demo gate in the browser, not real authentication.
          </div>
          <div className="mt-4 flex items-center justify-between text-xs text-slate-500">
            <Link to="/" className="text-brand-700 underline">Back to introduction</Link>
            <span>{DEMO_LABEL}</span>
          </div>
        </form>
      </div>
    </div>
  );
}
