// DEMO login only: credentials are checked in the browser. This is NOT real authentication.
const KEY = 'skillpulse_demo_session';
export const DEMO_USER = 'planner';
export const DEMO_PASS = 'demo123';

export function isLoggedIn() {
  try {
    return localStorage.getItem(KEY) === 'planner';
  } catch {
    return false;
  }
}
export function login(user, pass) {
  if (user.trim() === DEMO_USER && pass === DEMO_PASS) {
    try { localStorage.setItem(KEY, 'planner'); } catch { /* ignore */ }
    return true;
  }
  return false;
}
export function logout() {
  try { localStorage.removeItem(KEY); } catch { /* ignore */ }
}
