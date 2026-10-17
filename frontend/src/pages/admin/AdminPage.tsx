import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { api, ApiError } from '@/lib/api'
import { formatTime } from '@/lib/gate'
import { formatVnd } from '@/lib/money'
import { usePolling } from '@/lib/usePolling'

type AuditRow = {
  id: number
  at: string
  username: string
  action: string
  gate_id: string
  reason: string
  plate: string | null
}

type Price = { id: number; first_hours: number; first_price: number; per_hour: number }

type DailyReport = {
  date: string
  paid_count: number
  total: number
  by_method: { qr: number; cash: number }
}

/** Today's date in UTC+7 as YYYY-MM-DD (the Swedish locale formats dates that way). */
const todayVn = () => new Date().toLocaleDateString('sv-SE', { timeZone: 'Asia/Ho_Chi_Minh' })

function PriceCard() {
  const { data: price, refresh } = usePolling<Price>('/prices/current', 5000)
  const [draft, setDraft] = useState<Record<string, string>>({})
  const [message, setMessage] = useState<string | null>(null)

  const field = (key: 'first_hours' | 'first_price' | 'per_hour') =>
    draft[key] ?? String(price?.[key] ?? '')

  async function submit(event: FormEvent) {
    event.preventDefault()
    try {
      await api('/prices', {
        method: 'POST',
        body: JSON.stringify({
          first_hours: Number(field('first_hours')),
          first_price: Number(field('first_price')),
          per_hour: Number(field('per_hour')),
        }),
      })
      setDraft({})
      setMessage('Saved. The new price applies to sessions that start from now on.')
      refresh()
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : 'Request failed')
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Price</CardTitle>
      </CardHeader>
      <CardContent>
        {price && (
          <p className="mb-3 text-sm text-muted-foreground">
            Now: {formatVnd(price.first_price)} for the first {price.first_hours} h, then{' '}
            {formatVnd(price.per_hour)} per started hour.
          </p>
        )}
        <form onSubmit={submit} className="space-y-3">
          {(
            [
              ['first_hours', 'First block (hours)'],
              ['first_price', 'First block price (VND)'],
              ['per_hour', 'Price per started hour (VND)'],
            ] as const
          ).map(([key, label]) => (
            <div key={key} className="space-y-2">
              <Label htmlFor={key}>{label}</Label>
              <Input
                id={key}
                type="number"
                min={key === 'first_hours' ? 1 : 0}
                step={1}
                value={field(key)}
                onChange={(e) => setDraft({ ...draft, [key]: e.target.value })}
                required
              />
            </div>
          ))}
          <Button type="submit">Save price</Button>
          {message && <p className="text-sm text-muted-foreground">{message}</p>}
        </form>
      </CardContent>
    </Card>
  )
}

function ReportCard() {
  const [date, setDate] = useState(todayVn)
  const { data: report } = usePolling<DailyReport>(
    date ? `/reports/daily?date=${date}` : null,
    5000,
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle>Daily revenue</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-2">
          <Label htmlFor="report-date">Date</Label>
          <Input id="report-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
        {report && report.date === date && (
          <>
            <p className="text-3xl font-semibold">{formatVnd(report.total)}</p>
            <p className="text-sm text-muted-foreground">
              {report.paid_count} paid · QR {formatVnd(report.by_method.qr)} · Cash{' '}
              {formatVnd(report.by_method.cash)}
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}

export default function AdminPage() {
  const { data } = usePolling<AuditRow[]>('/audit-log?limit=50', 5000)

  return (
    <section className="space-y-6">
      <h2 className="text-xl font-semibold">Admin</h2>
      <div className="grid gap-4 md:grid-cols-2">
        <PriceCard />
        <ReportCard />
      </div>
      <h3 className="text-lg font-semibold">Audit log</h3>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time (UTC+7)</TableHead>
            <TableHead>User</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Gate</TableHead>
            <TableHead>Plate</TableHead>
            <TableHead>Reason</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.map((row) => (
            <TableRow key={row.id}>
              <TableCell>{formatTime(row.at)}</TableCell>
              <TableCell>{row.username}</TableCell>
              <TableCell>{row.action}</TableCell>
              <TableCell>{row.gate_id}</TableCell>
              <TableCell>{row.plate ?? '—'}</TableCell>
              <TableCell>{row.reason}</TableCell>
            </TableRow>
          ))}
          {data?.length === 0 && (
            <TableRow>
              <TableCell colSpan={6} className="text-muted-foreground">
                No audited actions yet.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </section>
  )
}
