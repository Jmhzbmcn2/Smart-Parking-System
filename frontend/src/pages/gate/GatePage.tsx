import { useEffect, useState, type FormEvent } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { api, ApiError } from '@/lib/api'
import {
  barrierOpen,
  formatTime,
  isValidPlate,
  manualPrefill,
  normalizePlate,
  pendingPaymentId,
  type GateEvent,
  type Payment,
} from '@/lib/gate'
import { formatVnd } from '@/lib/money'
import { usePolling } from '@/lib/usePolling'

const GATES = ['IN-1', 'OUT-1']
const SELECT_CLASS = 'h-8 rounded-lg border border-input bg-background px-2.5 text-sm'

function GateSelect({ id, value, onChange }: { id: string; value: string; onChange: (v: string) => void }) {
  // An event from another gate (e.g. IN-2) must stay selectable, not silently fall back to IN-1.
  const gates = GATES.includes(value) ? GATES : [...GATES, value]
  return (
    <select id={id} className={SELECT_CLASS} value={value} onChange={(e) => onChange(e.target.value)}>
      {gates.map((g) => (
        <option key={g}>{g}</option>
      ))}
    </select>
  )
}

function errorText(e: unknown): string {
  return e instanceof ApiError ? e.message : 'Request failed'
}

/** SP-3.3: after a paid exit the driver can ask for the invoice by email. */
function InvoiceCard({ paymentId }: { paymentId: number }) {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState<string | null>(null)

  async function submit(event: FormEvent) {
    event.preventDefault()
    try {
      await api(`/payments/${paymentId}/invoice`, {
        method: 'POST',
        body: JSON.stringify({ email }),
      })
      setMessage('Đã gửi hóa đơn')
    } catch (e) {
      setMessage(errorText(e))
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Hóa đơn điện tử</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={submit} className="flex flex-wrap items-end gap-3">
          <div className="space-y-2">
            <Label htmlFor="invoice-email">Email</Label>
            <Input
              id="invoice-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <Button type="submit">Gửi hóa đơn</Button>
          {message && <p className="text-sm text-muted-foreground">{message}</p>}
        </form>
      </CardContent>
    </Card>
  )
}

export default function GatePage() {
  const { data: events, refresh } = usePolling<GateEvent[]>('/gate-events?limit=20', 2000)
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  const newest = events?.[0]
  const paymentId = pendingPaymentId(events)
  const { data: payment } = usePolling<Payment>(
    paymentId === null ? null : `/payments/${paymentId}`,
    2000,
  )
  const [payMessage, setPayMessage] = useState<string | null>(null)
  const needsManual = newest?.action === 'manual_required'

  const prefill = manualPrefill(newest)
  const [gateDraft, setGateDraft] = useState<string | null>(null)
  const [plateDraft, setPlateDraft] = useState<string | null>(null)
  const entryGate = gateDraft ?? prefill.gate
  const plate = plateDraft ?? prefill.plate
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
      setGateDraft(null)
      setPlateDraft(null)
      setEntryMessage('Recorded')
      refresh()
    } catch (e) {
      setEntryMessage(errorText(e))
    }
  }

  async function settle(path: string, body?: unknown) {
    try {
      await api(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })
      setPayMessage(null)
      refresh()
    } catch (e) {
      setPayMessage(errorText(e))
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
        {newest?.action === 'entered' && (
          <Badge variant="secondary">
            Gợi ý: {newest.suggested_slot ?? 'hết chỗ'}
          </Badge>
        )}
      </div>

      {needsManual && (
        <p role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">
          LPR is not sure about plate {newest.plate || '(unreadable)'} at {newest.gate_id}. Enter it by hand below.
        </p>
      )}

      {payment && payment.id === paymentId && payment.status !== 'paid' && (
        <Card>
          <CardHeader>
            <CardTitle>
              Payment · {payment.plate} · {payment.gate_id}
              {payment.status === 'failed' && ' · QR payment failed'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-3xl font-semibold">{formatVnd(payment.amount)}</p>
            <pre className="rounded-lg bg-muted p-3 font-mono text-sm">{payment.qr_payload}</pre>
            <div className="flex flex-wrap gap-2">
              <Button onClick={() => settle(`/payments/${payment.id}/mock`, { success: true })}>
                Mô phỏng thành công
              </Button>
              <Button
                variant="outline"
                onClick={() => settle(`/payments/${payment.id}/mock`, { success: false })}
              >
                Mô phỏng thất bại
              </Button>
              <Button variant="secondary" onClick={() => settle(`/payments/${payment.id}/cash`)}>
                Thu tiền mặt
              </Button>
            </div>
            {payMessage && <p className="text-sm text-destructive">{payMessage}</p>}
          </CardContent>
        </Card>
      )}

      {newest?.action === 'exited' && newest.payment_id !== null && (
        <InvoiceCard key={newest.payment_id} paymentId={newest.payment_id} />
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
                <GateSelect id="entry-gate" value={entryGate} onChange={setGateDraft} />
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
