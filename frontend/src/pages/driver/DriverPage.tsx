import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { usePolling } from '@/lib/usePolling'

type ZoneSummary = { floor: number; zone: string; free: number; total: number }

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
    </section>
  )
}
