import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { STATUS_COLOR } from '../utils/colors';
import { n0 } from '../utils/format';

const MAHARASHTRA_BOUNDS = [[15.6, 72.6], [21.4, 80.9]];

/**
 * Leaflet + OpenStreetMap district bubble map.
 * Each bubble is placed at the demo district coordinates (not district boundary polygons).
 * Bubble size = demand, colour = SHORTAGE / BALANCED / SURPLUS.
 */
export default function GapMap({ districts, basis, selectedId, onSelect, links, centres }) {
  const elRef = useRef(null);
  const mapRef = useRef(null);
  const groups = useRef({});
  const selectRef = useRef(onSelect);
  selectRef.current = onSelect;

  useEffect(() => {
    const map = L.map(elRef.current, { scrollWheelZoom: false, zoomControl: true });
    map.fitBounds(MAHARASHTRA_BOUNDS);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    groups.current = {
      centres: L.layerGroup().addTo(map),
      links: L.layerGroup().addTo(map),
      districts: L.layerGroup().addTo(map),
    };
    mapRef.current = map;
    setTimeout(() => map.invalidateSize(), 50);
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const g = groups.current.districts;
    if (!g) return;
    g.clearLayers();
    const maxDemand = Math.max(1, ...(districts || []).map((d) => d.demand));
    (districts || []).forEach((d) => {
      const status = basis === 'forecast' ? d.forecast_status : d.status;
      const demand = basis === 'forecast' ? d.forecast_demand : d.demand;
      const capacity = basis === 'forecast' ? d.forecast_capacity : d.capacity;
      const selected = d.district_id === selectedId;
      const marker = L.circleMarker([d.latitude, d.longitude], {
        radius: 9 + 20 * Math.sqrt(demand / maxDemand),
        color: selected ? '#0f172a' : '#ffffff',
        weight: selected ? 4 : 1.5,
        fillColor: STATUS_COLOR[status] || '#64748b',
        fillOpacity: 0.78,
      });
      marker.bindTooltip(
        `<b>${d.district_name}</b><br/>${status}<br/>Demand ${n0(demand)} / capacity ${n0(capacity)}`,
        { direction: 'top' },
      );
      marker.on('click', () => selectRef.current && selectRef.current(d.district_id));
      marker.addTo(g);
    });
  }, [districts, basis, selectedId]);

  useEffect(() => {
    const g = groups.current.links;
    if (!g) return;
    g.clearLayers();
    (links || []).forEach((l) => {
      const line = L.polyline([l.from, l.to], { color: '#2563eb', weight: 3, dashArray: '8 6' });
      line.bindTooltip(l.label, { sticky: true });
      line.addTo(g);
    });
  }, [links]);

  useEffect(() => {
    const g = groups.current.centres;
    if (!g) return;
    g.clearLayers();
    (centres || []).forEach((c) => {
      L.circleMarker([c.latitude, c.longitude], { radius: 4, color: '#334155', weight: 1, fillColor: '#f8fafc', fillOpacity: 1 })
        .bindTooltip(`${c.name}<br/>${n0(c.available_for_skill)} of ${n0(c.seats_for_skill)} seats available`)
        .addTo(g);
    });
  }, [centres]);

  return (
    <div>
      <div ref={elRef} className="h-[460px] w-full rounded-lg border border-slate-200" role="application" aria-label="Interactive map of Maharashtra districts showing skill shortage or surplus" />
      <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-slate-600">
        {Object.entries(STATUS_COLOR).map(([k, v]) => (
          <span key={k} className="inline-flex items-center gap-1.5">
            <span className="inline-block h-3 w-3 rounded-full" style={{ background: v }} /> {k}
          </span>
        ))}
        <span>Bubble size = demand &middot; positions are demo district coordinates</span>
      </div>
    </div>
  );
}
