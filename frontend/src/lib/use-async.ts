import { useCallback, useEffect, useState } from 'react'

export interface AsyncState<T> {
  data: T | undefined
  error: Error | undefined
  loading: boolean
  reload: () => void
}

interface Settled<T> {
  deps: React.DependencyList
  nonce: number
  data?: T
  error?: Error
}

const sameDeps = (a: React.DependencyList, b: React.DependencyList) =>
  a.length === b.length && a.every((value, i) => Object.is(value, b[i]))

/**
 * Runs `fn` on mount and whenever `deps` change (or `reload()` is called).
 * `loading` is derived: a result only counts if it belongs to the current deps, so results from
 * stale runs are never shown and no state is set synchronously inside the effect.
 */
export function useAsync<T>(fn: () => Promise<T>, deps: React.DependencyList): AsyncState<T> {
  const [settled, setSettled] = useState<Settled<T>>()
  const [nonce, setNonce] = useState(0)

  useEffect(() => {
    let cancelled = false
    fn()
      .then((data) => {
        if (!cancelled) setSettled({ deps, nonce, data })
      })
      .catch((err: unknown) => {
        if (!cancelled) setSettled({ deps, nonce, error: err instanceof Error ? err : new Error(String(err)) })
      })
    return () => {
      cancelled = true
    }
    // `fn` is intentionally not a dependency: callers list what it depends on in `deps`.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce])

  const current = settled && settled.nonce === nonce && sameDeps(settled.deps, deps) ? settled : undefined
  const reload = useCallback(() => setNonce((n) => n + 1), [])

  return { data: current?.data, error: current?.error, loading: !current, reload }
}
