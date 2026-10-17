import { useEffect, useState } from 'react'

import { api } from '@/lib/api'

/** Fetch `path` now and every `ms`; keeps the last data when a request fails. */
export function usePolling<T>(path: string, ms: number) {
  const [data, setData] = useState<T | null>(null)
  const [tick, setTick] = useState(0)

  useEffect(() => {
    let alive = true
    const load = () =>
      api<T>(path)
        .then((d) => alive && setData(d))
        .catch(() => undefined) // The header badge already shows an offline API.
    load()
    const id = setInterval(load, ms)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [path, ms, tick])

  return { data, refresh: () => setTick((t) => t + 1) }
}
