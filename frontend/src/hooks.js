import { useCallback, useEffect, useState } from 'react';
import { api } from './api.js';

// Fetch one or more API paths together; returns data keyed the same way.
export function useResources(paths) {
  const key = JSON.stringify(paths);
  const [state, setState] = useState({ data: null, loading: true, error: null });

  const reload = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const entries = Object.entries(JSON.parse(key));
      const results = await Promise.all(entries.map(([, p]) => api.get(p)));
      setState({ data: Object.fromEntries(entries.map(([k], i) => [k, results[i]])), loading: false, error: null });
    } catch (err) {
      setState((s) => ({ ...s, loading: false, error: err.message }));
    }
  }, [key]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { ...state, reload };
}

// Wrap a mutating action: tracks busy state and surfaces errors as a flash message.
export function useAction(onDone) {
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState(null);

  const run = useCallback(
    async (fn, successMsg) => {
      setBusy(true);
      setFlash(null);
      try {
        await fn();
        if (successMsg) setFlash({ kind: 'ok', text: successMsg });
        await onDone?.();
        return true;
      } catch (err) {
        setFlash({ kind: 'err', text: err.message });
        return false;
      } finally {
        setBusy(false);
      }
    },
    [onDone],
  );

  return { busy, flash, setFlash, run };
}
