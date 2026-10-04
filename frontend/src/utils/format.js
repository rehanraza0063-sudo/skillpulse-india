export const n0 = (v) => (v === null || v === undefined || Number.isNaN(Number(v)) ? '-' : Math.round(Number(v)).toLocaleString('en-IN'));
export const pct = (v, d = 1) => (v === null || v === undefined ? '-' : `${(Number(v) * 100).toFixed(d)}%`);
export const pct1 = (v, d = 1) => (v === null || v === undefined ? '-' : `${Number(v).toFixed(d)}%`);
export const signed = (v) => (v === null || v === undefined ? '-' : `${v > 0 ? '+' : ''}${n0(v)}`);
export const DEMO_LABEL = 'Prototype/Demo Data — Not official statistics';
export const YEARS_ALL = [2023, 2024, 2025, 2026, 2027, 2028];
export const yearLabel = (y) => (y > 2026 ? `${y} (Prototype Forecast)` : `${y}`);
