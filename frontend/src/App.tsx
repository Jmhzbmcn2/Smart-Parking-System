import { useEffect, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api, ApiError } from '@/lib/api'
import AdminPage from '@/pages/admin/AdminPage'
import DriverPage from '@/pages/driver/DriverPage'
import GatePage from '@/pages/gate/GatePage'

export default function App() {
  const [online, setOnline] = useState(false)

  useEffect(() => {
    api<{ status: string }>('/health')
      .then(() => setOnline(true))
      .catch((error: unknown) => {
        if (error instanceof ApiError) setOnline(false)
      })
  }, [])

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="border-b bg-background">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-5">
          <h1 className="text-2xl font-semibold tracking-tight">SPMS</h1>
          <Badge variant={online ? 'secondary' : 'outline'} role="status">
            API: {online ? 'online' : 'offline'}
          </Badge>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Tabs defaultValue="driver" className="gap-6">
          <TabsList aria-label="Parking roles">
            <TabsTrigger value="driver">Driver</TabsTrigger>
            <TabsTrigger value="gate">Gate</TabsTrigger>
            <TabsTrigger value="admin">Admin</TabsTrigger>
          </TabsList>
          <TabsContent value="driver"><DriverPage /></TabsContent>
          <TabsContent value="gate"><GatePage /></TabsContent>
          <TabsContent value="admin"><AdminPage /></TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
