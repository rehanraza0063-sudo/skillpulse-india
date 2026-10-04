import { useCallback, useEffect, useState } from 'react';

/**
 * Runs `fetcher(signal)` whenever `deps` change. Keeps the previous data visible while reloading
 * (so filters feel instant) and ignores results of superseded requests.
 */
export function useApi(fetcher, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const ctrl = new AbortController();
    let alive = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    fetcher(ctrl.signal)
      .then((data) => alive && setState({ data, loading: false, error: null }))
      .catch((error) => {
        if (alive && error.name !== 'AbortError') setState({ data: null, loading: false, error });
      });
    return () => {
      alive = false;
      ctrl.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, reload };
}

export function useDebounced(value, delay = 250) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return v;
}
