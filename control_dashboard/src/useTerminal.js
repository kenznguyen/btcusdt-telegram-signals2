import { useEffect, useState } from 'react';
import { candleWindow, requestJson } from './api.js';

const empty = { system: null, intelligence: null, decision: null, paper: null, candles: null };
export function useTerminal(connection) {
  const [data, setData] = useState(empty), [errors, setErrors] = useState([]);
  const [busy, setBusy] = useState(false), [updatedAt, setUpdatedAt] = useState(null), [version, setVersion] = useState(0);
  useEffect(() => {
    setData(empty); setErrors([]); setUpdatedAt(null);
    if (!connection) { setBusy(false); return; }
    let stopped = false, running = false, controller;
    const load = async () => {
      if (stopped || running || document.hidden) return;
      running = true; controller = new AbortController(); setBusy(true);
      const endpoints = { system: '/v1/system', intelligence: '/v1/intelligence', decision: '/v1/decision', paper: '/v1/paper', candles: candleWindow(Date.now()) };
      const entries = Object.entries(endpoints);
      try {
        const results = await Promise.allSettled(entries.map(([, path]) => requestJson(connection.base, path, connection.readToken, { signal: controller.signal })));
        if (stopped || controller.signal.aborted) return;
        const next = { ...empty }, problems = [];
        results.forEach((result, index) => {
          if (result.status === 'fulfilled') next[entries[index][0]] = result.value;
          else problems.push(`${entries[index][0]}: ${result.reason.name === 'AbortError' ? 'Hết thời gian chờ' : result.reason.message}`);
        });
        setData(next); setErrors(problems); setUpdatedAt(Object.values(next).some(Boolean) ? Date.now() : null);
      } finally { running = false; if (!stopped) setBusy(false); }
    };
    const visibility = () => document.hidden ? controller?.abort() : load();
    load(); const timer = setInterval(load, 5000);
    document.addEventListener('visibilitychange', visibility);
    return () => { stopped = true; clearInterval(timer); controller?.abort(); document.removeEventListener('visibilitychange', visibility); };
  }, [connection, version]);
  return { data, errors, busy, updatedAt, refresh: () => setVersion(value => value + 1) };
}
