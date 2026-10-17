import { useEffect, useState, type FormEvent } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { api, ApiError } from '@/lib/api'
import { barrierOpen, formatTime, isValidPlate, normalizePlate, type GateEvent } from '@/lib/gate'
import { usePolling } from '@/lib/usePolling'

const GATES = ['IN-1', 'OUT-1']
const SELECT_CLASS = 'h-8 rounded-lg border border-input bg-background px-2.5 text-sm'

function GateSelect({ id, value, onChange }: { id: string; value: string; onChange: (v: string) => void }) {
  return (
    <select id={id} className={SELECT_CLASS} value={value} onChange={(e) => onChange(e.target.value)}>
      {GATES.map((g) => (
        <option key={g}>{g}</option>
      ))}
    </select>
  )
}

function errorText(e: unknown): string {
  return e instanceof ApiError ? e.message : 'Request failed'
}

export default function GatePage() {
  const { data: events, refresh } = usePolling<GateEvent[]>('/gate-events?limit=20', 2000)
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const newest = events?.[0]
  const needsManual = newest?.action === 'manual_required'

  const [entryGate, setEntryGate] = useState('IN-1')
  const [plateDraft, setPlateDraft] = useState<string | null>(null)
  const plate = plateDraft ?? (needsManual ? (newest?.plate ?? '') : '')
  const [entryMessage, setEntryMessage] = useState<string | null>(null)

  const [openGate, setOpenGate] = useState('OUT-1')
  const [reason, setReason] = useState('')
  const [openMessage, setOpenMessage] = useState<string | null>(null)

  async function submitEntry(event: FormEvent) {
    event.preventDefault()
    if (!isValidPlate(plate)) {
      setEntryMessage('Invalid plate, example 30A-123.45')
      return
    }
    try {
      await api('/gate/manual-entry', {
        method: 'POST',
        body: JSON.stringify({ gate_id: entryGate, plate: normalizePlate(plate) }),
      })
      setPlateDraft(null)
      setEntryMessage('Recorded')
      refresh()
    } catch (e) {
      setEntryMessage(errorText(e))
    }
  }

  async function submitOpen(event: FormEvent) {
    event.preventDefault()
    try {
      await api('/barrier/manual-open', {
        method: 'POST',
        body: JSON.stringify({ gate_id: openGate, reason }),
      })
      setReason('')
      setOpenMessage('Barrier opened and logged')
    } catch (e) {
      setOpenMessage(errorText(e))
    }
  }

  return (
    <section className="space-y-6">
      <div className="flex items-center gap-3">
        <h2 className="text-xl font-semibold">Gate</h2>
        <Badge variant={barrierOpen(newest, now) ? 'default' : 'outline'}>
          Barrier: {barrierOpen(newest, now) ? 'Mở' : 'Đóng'}
        </Badge>
      </div>

      {needsManual && (
        <p role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">
          LPR is not sure about plate {newest.plate || '(unreadable)'} at {newest.gate_id}. Enter it by hand below.
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Manual plate entry</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={submitEntry} className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="entry-gate">Gate</Label>
                <GateSelect id="entry-gate" value={entryGate} onChange={setEntryGate} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="plate">Plate</Label>
                <Input
                  id="plate"
                  placeholder="30A-123.45"
                  value={plate}
                  onChange={(e) => setPlateDraft(e.target.value)}
                />
              </div>
              <Button type="submit">Submit</Button>
              {entryMessage && <p className="text-sm text-muted-foreground">{entryMessage}</p>}
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Manual barrier open</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={submitOpen} className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="open-gate">Gate</Label>
                <GateSelect id="open-gate" value={openGate} onChange={setOpenGate} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reason">Reason</Label>
                <Input id="reason" value={reason} onChange={(e) => setReason(e.target.value)} required />
              </div>
              <Button type="submit" disabled={!reason.trim()}>
                Open barrier
              </Button>
              {openMessage && <p className="text-sm text-muted-foreground">{openMessage}</p>}
            </form>
          </CardContent>
        </Card>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time (UTC+7)</TableHead>
            <TableHead>Gate</TableHead>
            <TableHead>Plate</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events?.map((e) => (
            <TableRow key={e.id}>
              <TableCell>{formatTime(e.received_at)}</TableCell>
              <TableCell>{e.gate_id}</TableCell>
              <TableCell>{e.plate ?? '—'}</TableCell>
              <TableCell>{e.source}</TableCell>
              <TableCell>{e.action}</TableCell>
            </TableRow>
          ))}
          {events?.length === 0 && (
            <TableRow>
              <TableCell colSpan={5} className="text-muted-foreground">
                No gate events yet.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </section>
  )
}
