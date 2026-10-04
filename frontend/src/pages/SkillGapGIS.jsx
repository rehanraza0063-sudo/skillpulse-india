import { useEffect, useMemo, useState } from 'react';
import { api } from '../services/api';
import { useApi, useDebounced } from '../hooks/useApi';
import GapMap from '../maps/GapMap';
import { Arrow, Card, DemoNote, EmptyState, ErrorState, Loading, Mono, PageHeader, Select, StatusBadge } from '../components/ui';
import { n0, pct, yearLabel } from '../utils/format';

export default function SkillGapGIS() {
  const [skillId, setSkillId] = useState('S01');
  const [year, setYear] = useState('2026');
  const [fyear, setFyear] = useState('2028');
  const [districtId, setDistrictId] = useState('');
  const [basis, setBasis] = useState('current');
  const [shortPct, setShortPct] = useState('10');
  const [surPct, setSurPct] = useState('-10');
  const [showCentres, setShowCentres] = useState(false);
  const [nearby, setNearby] = useState({ loading: false, error: null, data: null });

  const dShort = useDebounced(shortPct, 400);
  const dSur = useDebounced(surPct, 400);
  const thrOk = dShort !== '' && dSur !== '' && !Number.isNaN(+dShort) && !Number.isNaN(+dSur) && +dSur < +dShort;
  const thr = thrOk ? { shortage_threshold: +dShort / 100, surplus_threshold: +dSur / 100 } : {};
  const thrKey = thrOk ? `${dShort}|${dSur}` : 'default';

  const skills = useApi((s) => api.skills(s), []);
  const map = useApi((s) => api.skillGap({ skill_id: skillId, year, forecast_year: fyear, ...thr }, s), [skillId, year, fyear, thrKey]);
  const detail = useApi(
    (s) => (districtId ? api.skillGapDistrict({ skill_id: skillId, district_id: districtId, year, forecast_year: fyear, ...thr }, s) : Promise.resolve(null)),
    [skillId, districtId, year, fyear, thrKey],
  );
  const centres = useApi((s) => (showCentres ? api.trainingCentres({ skill_id: skillId }, s) : Promise.resolve(null)), [showCentres, skillId]);

  // results of "find nearby surplus" are tied to one selection; clear them when it changes
  useEffect(() => setNearby({ loading: false, error: null, data: null }), [skillId, districtId, year, thrKey]);

  const findNearby = async () => {
    setNearby({ loading: true, error: null, data: null });
    try {
      const data = await api.nearbySurplus({ skill_id: skillId, district_id: districtId, year, ...thr });
      setNearby({ loading: false, error: null, data });
    } catch (error) {
      setNearby({ loading: false, error, data: null });
    }
  };

  const districts = map.data?.districts || [];
  const selected = districts.find((d) => d.district_id === districtId);
  const links = useMemo(() => {
    if (!nearby.data || !selected) return [];
    return nearby.data.candidates.map((c) => {
      const to = districts.find((d) => d.district_id === c.district_id);
      return to ? { from: [selected.latitude, selected.longitude], to: [to.latitude, to.longitude], label: `${c.district_name}: ${c.distance_km} km, ${n0(c.surplus_seats)} surplus seats` } : null;
    }).filter(Boolean);
  }, [nearby.data, selected, districts]);

  const centreMarkers = useMemo(() => {
    if (!showCentres || !centres.data) return [];
    return centres.data.training_centres.map((c) => ({
      ...c,
      seats_for_skill: seatsFor(c, skillId, 'seats_by_skill'),
      available_for_skill: seatsFor(c, skillId, 'available_by_skill'),
    }));
  }, [showCentres, centres.data, skillId]);

  const det = detail.data;
  const years = [2023, 2024, 2025, 2026];

  return (
    <div>
      <PageHeader title="Skill Gap GIS" subtitle="District-level demand versus training capacity. Pick a skill, click a district, then find the nearest surplus training capacity.">
        <DemoNote />
      </PageHeader>

      <Card className="mb-4" title="Selection">
        {skills.error ? <ErrorState error={skills.error} onRetry={skills.reload} /> : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <Select label="Skill" value={skillId} onChange={setSkillId}
              options={(skills.data?.skills || []).map((s) => ({ value: s.skill_id, label: s.skill_name }))} />
            <Select label="District" value={districtId} onChange={setDistrictId} placeholder="Click the map or choose"
              options={districts.map((d) => ({ value: d.district_id, label: d.district_name }))} />
            <Select label="Current year" value={year} onChange={setYear} options={years.map((y) => ({ value: String(y), label: String(y) }))} />
            <Select label="Forecast year" value={fyear} onChange={setFyear} options={[2027, 2028].map((y) => ({ value: String(y), label: yearLabel(y) }))} />
            <Select label="Map colours show" value={basis} onChange={setBasis}
              options={[{ value: 'current', label: `Current year (${year})` }, { value: 'forecast', label: `Prototype Forecast (${fyear})` }]} />
          </div>
        )}
        <details className="mt-3 text-sm">
          <summary className="cursor-pointer font-medium text-slate-700">Gap thresholds and options</summary>
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <label className="block"><span className="label">SHORTAGE if gap ratio above (%)</span>
              <input className="input" type="number" value={shortPct} onChange={(e) => setShortPct(e.target.value)} /></label>
            <label className="block"><span className="label">SURPLUS if gap ratio below (%)</span>
              <input className="input" type="number" value={surPct} onChange={(e) => setSurPct(e.target.value)} /></label>
            <label className="mt-6 flex items-center gap-2 text-sm"><input type="checkbox" checked={showCentres} onChange={(e) => setShowCentres(e.target.checked)} />
              Show training centres offering this skill</label>
          </div>
          {!thrOk && <p className="mt-2 text-xs text-red-700">Surplus threshold must be lower than the shortage threshold; defaults are used meanwhile.</p>}
          <p className="mt-2 text-xs text-slate-500">gap ratio = (demand - training capacity) / demand</p>
        </details>
      </Card>

      {map.error && <ErrorState error={map.error} onRetry={map.reload} />}
      {!map.data && map.loading && <Loading label="Loading map data..." />}

      {map.data && (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="space-y-4 lg:col-span-2">
            <Card title={`${map.data.skill_name}: district gaps`} subtitle={`State total ${year}: demand ${n0(map.data.state_total.demand)}, capacity ${n0(map.data.state_total.capacity)}`}
              actions={<StatusBadge value={map.data.state_total.status} />}>
              <GapMap districts={districts} basis={basis} selectedId={districtId} onSelect={setDistrictId} links={links} centres={centreMarkers} />
              <p className="mt-2 text-xs text-slate-500">Map tiles need an internet connection (OpenStreetMap). The table below shows the same data.</p>
            </Card>

            <Card title="All districts (same data as the map)" pad={false}>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead><tr>
                    <th className="th">District</th><th className="th">Demand {year}</th><th className="th">Capacity</th><th className="th">Gap</th><th className="th">Status</th>
                    <th className="th">Forecast {fyear}</th><th className="th">Forecast status</th></tr></thead>
                  <tbody>
                    {districts.map((d) => (
                      <tr key={d.district_id} onClick={() => setDistrictId(d.district_id)} className={`cursor-pointer hover:bg-slate-50 ${d.district_id === districtId ? 'bg-brand-50' : ''}`}>
                        <td className="td font-medium"><button type="button" className="text-left underline-offset-2 hover:underline" onClick={() => setDistrictId(d.district_id)}>{d.district_name}</button></td>
                        <td className="td">{n0(d.demand)}</td><td className="td">{n0(d.capacity)}</td><td className="td">{n0(d.gap)}</td>
                        <td className="td"><StatusBadge value={d.status} /></td>
                        <td className="td">{n0(d.forecast_demand)}</td><td className="td"><StatusBadge value={d.forecast_status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>

          <div className="space-y-4">
            {!districtId && <EmptyState title="No district selected" message="Click a bubble on the map, a table row, or use the District selector to see demand, capacity, gap and nearby training centres." />}
            {districtId && detail.error && <ErrorState error={detail.error} onRetry={detail.reload} />}
            {districtId && !det && detail.loading && <Loading />}
            {det && (
              <>
                <Card title={det.district_name} subtitle={`${det.skill_name} · ${det.region}`} actions={<StatusBadge value={det.status} />}>
                  <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
                    <Stat label={`Current demand (${det.year})`} value={n0(det.demand)} />
                    <Stat label="Training capacity" value={n0(det.capacity)} />
                    <Stat label="Demand-supply gap" value={n0(det.gap)} sub={`${pct(det.gap_ratio)} of demand`} />
                    <Stat label="Status" value={<StatusBadge value={det.status} />} />
                    <Stat label={`Forecast demand (${det.forecast_year})`} value={n0(det.forecast_demand)} sub={`range ${n0(det.forecast_lower)} - ${n0(det.forecast_upper)}`} />
                    <Stat label="Forecast gap" value={n0(det.forecast_gap)} sub={<StatusBadge value={det.forecast_status} />} />
                    <Stat label="Confidence" value={<StatusBadge kind="level" value={det.confidence_label} />} sub="Prototype Forecast, 4 demo points" />
                  </dl>
                  <div className="mt-3 space-y-2">
                    <Mono>{det.calculation}</Mono>
                    <Mono>{det.forecast_calculation}</Mono>
                  </div>
                  <button type="button" className="btn-primary mt-4 w-full" onClick={findNearby} disabled={nearby.loading}>
                    {nearby.loading ? 'Searching...' : 'Find Nearby Surplus Capacity'}
                  </button>
                </Card>

                {nearby.error && <ErrorState error={nearby.error} />}
                {nearby.data && (
                  <Card title="Nearest surplus training capacity" subtitle={`Within ${nearby.data.radius_km} km (straight-line distance)`}>
                    {nearby.data.message && <p className="mb-3 rounded bg-slate-50 p-2 text-xs text-slate-600">{nearby.data.message}</p>}
                    <div className="rounded border border-red-200 bg-red-50 p-2 text-center text-sm font-medium text-red-800">
                      {nearby.data.district_name}: {nearby.data.status}{nearby.data.shortage_seats > 0 && ` (${n0(nearby.data.shortage_seats)} seats short)`}
                    </div>
                    <Arrow />
                    {nearby.data.candidates.length === 0 ? (
                      <EmptyState title="No surplus district found" message={`No district classified SURPLUS for ${nearby.data.skill_name} within ${nearby.data.radius_km} km in ${nearby.data.year}.`} />
                    ) : (
                      <ol className="space-y-3">
                        {nearby.data.candidates.map((c, i) => (
                          <li key={c.district_id} className="rounded border border-blue-200 bg-blue-50 p-3">
                            <div className="flex items-center justify-between">
                              <div className="font-semibold text-blue-900">{c.district_name} {i === 0 && <span className="badge ml-1 border-blue-300 bg-white text-blue-800">Nearest</span>}</div>
                              <div className="text-xs text-slate-600">{c.distance_km} km</div>
                            </div>
                            <div className="mt-1 text-sm text-slate-700">Surplus capacity: <b>{n0(c.surplus_seats)}</b> seats (capacity {n0(c.capacity)} vs demand {n0(c.demand)}). Could cover up to <b>{n0(c.transferable_seats)}</b> of the shortage.</div>
                            {c.centres.length > 0 && (
                              <ul className="mt-2 space-y-1 text-xs text-slate-600">
                                {c.centres.map((t) => <li key={t.centre_id}>{t.name}: {n0(t.available_for_skill)} of {n0(t.seats_for_skill)} seats available</li>)}
                              </ul>
                            )}
                          </li>
                        ))}
                      </ol>
                    )}
                    <p className="mt-3 text-xs text-slate-500">{nearby.data.method}</p>
                  </Card>
                )}

                <Card title="Nearby training centres" subtitle={`Offering ${det.skill_name} within ${det.centre_radius_km} km`}>
                  {det.nearby_centres.length === 0 ? <p className="text-sm text-slate-500">No centres in range.</p> : (
                    <ul className="divide-y divide-slate-100 text-sm">
                      {det.nearby_centres.map((c) => (
                        <li key={c.centre_id} className="flex items-start justify-between gap-2 py-2">
                          <span><span className="font-medium">{c.name}</span><br /><span className="text-xs text-slate-500">{c.distance_km} km &middot; {c.district_name}</span></span>
                          <span className="whitespace-nowrap text-xs text-slate-700">{n0(c.available_for_skill)} / {n0(c.seats_for_skill)} seats free</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function seatsFor(centre, skillId, field) {
  const hit = String(centre[field] || '').split(';').find((p) => p.startsWith(`${skillId}=`));
  return hit ? Number(hit.split('=')[1]) : 0;
}

function Stat({ label, value, sub }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="text-base font-semibold text-slate-900">{value}</dd>
      {sub && <dd className="text-xs text-slate-500">{sub}</dd>}
    </div>
  );
}
