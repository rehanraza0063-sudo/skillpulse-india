import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { useApi, useDebounced } from '../hooks/useApi';
import { Card, DemoNote, EmptyState, ErrorState, Loading, PageHeader, Select } from '../components/ui';

const TABLES = [
  ['jobs', 'Jobs'], ['training_centres', 'Training Centres'], ['skills', 'Skills'], ['occupations', 'Occupations'],
  ['industries', 'Industries'], ['districts', 'Districts'], ['historical_demand', 'Historical Demand'], ['training_capacity', 'Training Capacity'],
];
const NOFILTER = { district_id: '', skill_id: '', industry_id: '', year: '' };

export default function DataExplorer() {
  const [table, setTable] = useState('jobs');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [order, setOrder] = useState('asc');
  const [page, setPage] = useState(1);
  const [f, setF] = useState(NOFILTER);
  const dsearch = useDebounced(search, 300);

  const lists = useApi(async (s) => {
    const [d, k] = await Promise.all([api.districts(s), api.skills(s)]);
    return {
      districts: d.districts,
      skills: k.skills,
      industries: [...new Map(k.skills.map((x) => [x.industry_id, x.industry_name])).entries()],
    };
  }, []);

  useEffect(() => { setPage(1); }, [table, dsearch, f, sortBy, order]);
  useEffect(() => { setSortBy(''); setOrder('asc'); setF(NOFILTER); setSearch(''); }, [table]);

  const data = useApi(
    (s) => api.data(table, { search: dsearch, sort_by: sortBy, order, page, page_size: 20, ...f }, s),
    [table, dsearch, sortBy, order, page, f.district_id, f.skill_id, f.industry_id, f.year],
  );

  const d = data.data;
  const cols = d?.columns || [];
  const pages = d ? Math.max(1, Math.ceil(d.total / d.page_size)) : 1;
  const sort = (c) => { if (sortBy === c) setOrder(order === 'asc' ? 'desc' : 'asc'); else { setSortBy(c); setOrder('asc'); } };
  const L = lists.data;

  return (
    <div>
      <PageHeader title="Data Explorer" subtitle="Inspect the underlying demo records. Every row carries a source_type; DEMO means fictional prototype data, not an official record.">
        <DemoNote />
      </PageHeader>

      <div role="tablist" aria-label="Tables" className="mb-4 flex flex-wrap gap-1">
        {TABLES.map(([k, l]) => (
          <button key={k} type="button" role="tab" aria-selected={table === k} onClick={() => setTable(k)}
            className={`rounded-md border px-3 py-1.5 text-sm font-medium ${table === k ? 'border-brand-700 bg-brand-700 text-white' : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-100'}`}>{l}</button>
        ))}
      </div>

      <Card className="mb-4" title="Search and filter">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <label className="block lg:col-span-2"><span className="label">Search all columns</span>
            <input className="input" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="e.g. EV, Pune, battery" /></label>
          {L && cols.includes('district_id') && (
            <Select label="District" value={f.district_id} onChange={(v) => setF({ ...f, district_id: v })} placeholder="All"
              options={L.districts.map((x) => ({ value: x.district_id, label: x.district_name }))} />)}
          {L && cols.includes('skill_id') && (
            <Select label="Skill" value={f.skill_id} onChange={(v) => setF({ ...f, skill_id: v })} placeholder="All"
              options={L.skills.map((x) => ({ value: x.skill_id, label: x.skill_name }))} />)}
          {L && cols.includes('industry_id') && (
            <Select label="Industry" value={f.industry_id} onChange={(v) => setF({ ...f, industry_id: v })} placeholder="All"
              options={L.industries.map(([v, l]) => ({ value: v, label: l }))} />)}
          {cols.includes('year') && (
            <Select label="Year" value={f.year} onChange={(v) => setF({ ...f, year: v })} placeholder="All"
              options={[2023, 2024, 2025, 2026].map((y) => ({ value: String(y), label: String(y) }))} />)}
        </div>
      </Card>

      {data.error && <ErrorState error={data.error} onRetry={data.reload} />}
      {!d && data.loading && <Loading />}
      {d && (
        <Card pad={false} title={`${TABLES.find((t) => t[0] === table)[1]} · ${d.total.toLocaleString('en-IN')} rows`} subtitle={d.source_note}>
          {d.rows.length === 0 ? (
            <div className="p-4"><EmptyState title="No matching rows" message="Try a different search term or clear the filters." /></div>
          ) : (
            <div className={`overflow-x-auto ${data.loading ? 'opacity-60' : ''}`}>
              <table className="w-full">
                <thead>
                  <tr>
                    {cols.map((c) => (
                      <th key={c} className="th" aria-sort={sortBy === c ? (order === 'asc' ? 'ascending' : 'descending') : 'none'}>
                        <button type="button" onClick={() => sort(c)} className="inline-flex items-center gap-1 font-semibold uppercase">
                          {c.replaceAll('_', ' ')}{sortBy === c && <span aria-hidden="true">{order === 'asc' ? '▲' : '▼'}</span>}
                        </button>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {d.rows.map((row, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      {cols.map((c) => (
                        <td key={c} className="td max-w-[320px] truncate" title={String(row[c] ?? '')}>
                          {c === 'source_type' ? <span className="badge border-amber-300 bg-amber-50 text-amber-900">{row[c]}</span> : String(row[c] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="flex items-center justify-between border-t border-slate-100 p-3 text-sm">
            <span className="text-slate-500">Page {d.page} of {pages}</span>
            <div className="flex gap-2">
              <button type="button" className="btn-secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
              <button type="button" className="btn-secondary" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
