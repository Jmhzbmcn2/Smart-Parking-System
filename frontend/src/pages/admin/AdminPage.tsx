import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { formatTime } from '@/lib/gate'
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

export default function AdminPage() {
  const { data } = usePolling<AuditRow[]>('/audit-log?limit=50', 5000)

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold">Audit log</h2>
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
                No manual actions yet.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </section>
  )
}
