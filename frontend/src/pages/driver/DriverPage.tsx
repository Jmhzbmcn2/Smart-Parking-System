import { useEffect, useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api, ApiError } from '@/lib/api'
import { isValidPlate, normalizePlate } from '@/lib/gate'
import { formatCountdown, secondsLeft } from '@/lib/reservation'
import { usePolling } from '@/lib/usePolling'

type ZoneSummary = { floor: number; zone: string; free: number; total: number }
type Slot = { id: string; floor: number; zone: string; status: string }
type Reservation = { id: number; slot_id: string; plate: string; expires_at: string }

const SELECT_CLASS = 'h-8 rounded-lg border border-input bg-background px-2.5 text-sm'

function ReservationCard() {
  const [floor, setFloor] = useState(1)
  const [zone, setZone] = useState('A')
  const [slotId, setSlotId] = useState<string | null>(null)
  const [plate, setPlate] = useState('')
  const [message, setMessage] = useState<string | null>(null)
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const { data: mine, refresh: refreshMine } = usePolling<Reservation | null>(
    '/reservations/me',
    3000,
  )
  const { data: free, refresh: refreshFree } = usePolling<Slot[]>(
    `/slots?floor=${floor}&zone=${zone}&status=available`,
    3000,
  )

  function refresh() {
    refreshMine()
    refreshFree()
  }

  async function reserve(event: FormEvent) {
    event.preventDefault()
    if (!slotId) return setMessage('Pick a slot first')
    if (!isValidPlate(plate)) return setMessage('Invalid plate, example 30A-123.45')
    try {
      await api('/reservations', {
        method: 'POST',
        body: JSON.stringify({ slot_id: slotId, plate: normalizePlate(plate) }),
      })
      setMessage(null)
      setSlotId(null)
      refresh()
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : 'Request failed')
    }
  }

  async function cancel() {
    try {
      await api('/reservations/me', { method: 'DELETE' })
      refresh()
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : 'Request failed')
    }
  }

  if (mine) {
    const left = secondsLeft(mine.expires_at, now)
    return (
      <Card>
        <CardHeader>
          <CardTitle>Your reservation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-3xl font-semibold">{mine.slot_id}</p>
          <p className="text-sm text-muted-foreground">
            Plate {mine.plate} · held for{' '}
            <span className="font-mono">{formatCountdown(left)}</span>
          </p>
          <Button variant="outline" onClick={cancel}>
            Cancel reservation
          </Button>
          {message && <p className="text-sm text-destructive">{message}</p>}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Reserve a slot (held 10 minutes)</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={reserve} className="space-y-3">
          <div className="flex gap-3">
            <div className="space-y-2">
              <Label htmlFor="floor">Floor</Label>
              <select
                id="floor"
                className={SELECT_CLASS}
                value={floor}
                onChange={(e) => setFloor(Number(e.target.value))}
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="zone">Zone</Label>
              <select
                id="zone"
                className={SELECT_CLASS}
                value={zone}
                onChange={(e) => setZone(e.target.value)}
              >
                <option>A</option>
                <option>B</option>
              </select>
            </div>
          </div>
          <div className="flex max-h-32 flex-wrap gap-1 overflow-y-auto" role="group" aria-label="Free slots">
            {free?.map((s) => (
              <Button
                key={s.id}
                type="button"
                size="sm"
                variant={s.id === slotId ? 'default' : 'outline'}
                onClick={() => setSlotId(s.id)}
              >
                {s.id}
              </Button>
            ))}
            {free?.length === 0 && <p className="text-sm text-muted-foreground">No free slot here.</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="res-plate">Plate</Label>
            <Input
              id="res-plate"
              placeholder="30A-123.45"
              value={plate}
              onChange={(e) => setPlate(e.target.value)}
            />
          </div>
          <Button type="submit">Giữ chỗ{slotId ? ` ${slotId}` : ''}</Button>
          {message && <p className="text-sm text-destructive">{message}</p>}
        </form>
      </CardContent>
    </Card>
  )
}

export default function DriverPage() {
  const { data } = usePolling<ZoneSummary[]>('/slots/summary', 3000)

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">Free slots</h2>
      {data === null && <p className="text-sm text-muted-foreground">Loading…</p>}
      <div className="grid gap-4 sm:grid-cols-2">
        {data?.map((z) => (
          <Card key={`${z.floor}-${z.zone}`}>
            <CardHeader>
              <CardTitle>
                Floor {z.floor} · Zone {z.zone}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-semibold">
                {z.free} <span className="text-base font-normal text-muted-foreground">/ {z.total} free</span>
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
      <ReservationCard />
    </section>
  )
}
