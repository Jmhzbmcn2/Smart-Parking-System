import { useEffect, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api, ApiError } from '@/lib/api'
import { clearSession, getSession, tabsFor, type Session, type Tab } from '@/lib/auth'
import AdminPage from '@/pages/admin/AdminPage'
import DriverPage from '@/pages/driver/DriverPage'
import GatePage from '@/pages/gate/GatePage'
import LoginPage from '@/pages/login/LoginPage'

const TAB_LABEL: Record<Tab, string> = { driver: 'Driver', gate: 'Gate', admin: 'Admin' }
const TAB_PAGE: Record<Tab, () => React.JSX.Element> = {
  driver: DriverPage,
  gate: GatePage,
  admin: AdminPage,
}

export default function App() {
  const [online, setOnline] = useState(false)
  const [session, setSession] = useState<Session | null>(getSession)

  useEffect(() => {
    api<{ status: string }>('/health')
      .then(() => setOnline(true))
      .catch((error: unknown) => {
        if (error instanceof ApiError) setOnline(false)
      })
  }, [])

  useEffect(() => {
    const onLogout = () => setSession(null)
    window.addEventListener('spms:logout', onLogout)
    return () => window.removeEventListener('spms:logout', onLogout)
  }, [])

  async function logout() {
    // Invalidate the token on the server first; log out locally even if that call fails.
    await api('/auth/logout', { method: 'POST' }).catch(() => undefined)
    clearSession()
    setSession(null)
  }

  const tabs = session ? tabsFor(session.role) : []

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="border-b bg-background">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-5">
          <h1 className="text-2xl font-semibold tracking-tight">SPMS</h1>
          <div className="flex items-center gap-3">
            {session && (
              <>
                <span className="text-sm text-muted-foreground">
                  {session.username} ({session.role})
                </span>
                <Button variant="outline" size="sm" onClick={logout}>
                  Log out
                </Button>
              </>
            )}
            <Badge variant={online ? 'secondary' : 'outline'} role="status">
              API: {online ? 'online' : 'offline'}
            </Badge>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        {session ? (
          // key resets the active tab when another user logs in.
          <Tabs key={session.username} defaultValue={tabs[0]} className="gap-6">
            <TabsList aria-label="Parking roles">
              {tabs.map((tab) => (
                <TabsTrigger key={tab} value={tab}>
                  {TAB_LABEL[tab]}
                </TabsTrigger>
              ))}
            </TabsList>
            {tabs.map((tab) => {
              const Page = TAB_PAGE[tab]
              return (
                <TabsContent key={tab} value={tab}>
                  <Page />
                </TabsContent>
              )
            })}
          </Tabs>
        ) : (
          <LoginPage onLogin={setSession} />
        )}
      </main>
    </div>
  )
}
