// Thin client for the SkillPulse FastAPI backend. In development Vite proxies /api to port 8000.
const BASE = import.meta.env.VITE_API_BASE || '';

export class ApiError extends Error {
  constructor(message, status = 0, body = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

function describe(body, status) {
  const d = body && body.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((x) => `${(x.loc || []).slice(1).join('.')}: ${x.msg}`).join('; ');
  return `Request failed (HTTP ${status})`;
}

async function request(path, { method = 'GET', body, params, signal } = {}) {
  let qs = '';
  if (params) {
    const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== '');
    if (entries.length) qs = '?' + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString();
  }
  let res;
  try {
    res = await fetch(`${BASE}/api${path}${qs}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    throw new ApiError('Cannot reach the SkillPulse backend. Start it with: uvicorn app.main:app --reload (port 8000).');
  }
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON body */
  }
  if (!res.ok) throw new ApiError(describe(data, res.status), res.status, data);
  return data;
}

export const api = {
  health: (signal) => request('/health', { signal }),
  dashboard: (params, signal) => request('/dashboard', { params, signal }),
  districts: (signal) => request('/districts', { signal }),
  skills: (signal) => request('/skills', { signal }),
  occupations: (signal) => request('/occupations', { signal }),
  industries: (signal) => request('/industries', { signal }),
  trainingCentres: (params, signal) => request('/training-centres', { params, signal }),
  skillGap: (params, signal) => request('/skill-gap', { params, signal }),
  skillGapDistrict: (params, signal) => request('/skill-gap/district', { params, signal }),
  nearbySurplus: (params, signal) => request('/skill-gap/nearby-surplus', { params, signal }),
  forecast: (params, signal) => request('/forecast', { params, signal }),
  transition: (body, signal) => request('/transition', { method: 'POST', body, signal }),
  extractSkills: (body, signal) => request('/nlp/extract-skills', { method: 'POST', body, signal }),
  nlpSample: (signal) => request('/nlp/sample', { signal }),
  whatIf: (body, signal) => request('/what-if', { method: 'POST', body, signal }),
  earlyWarning: (params, signal) => request('/early-warning', { params, signal }),
  recommendations: (params, signal) => request('/recommendations', { params, signal }),
  dataSources: (signal) => request('/data-sources', { signal }),
  data: (table, params, signal) => request(`/data/${table}`, { params, signal }),
};
