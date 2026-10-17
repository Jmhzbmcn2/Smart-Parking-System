export type Role = 'driver' | 'attendant' | 'admin'
export type Tab = 'driver' | 'gate' | 'admin'
export type Session = { token: string; username: string; role: Role }

const KEY = 'spms.session'

export function getSession(): Session | null {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as Session) : null
  } catch {
    return null
  }
}

export function saveSession(session: Session): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(session))
  } catch {
    // Storage can be blocked; the user just has to log in again after a reload.
  }
}

export function clearSession(): void {
  try {
    localStorage.removeItem(KEY)
  } catch {
    // Nothing stored, nothing to clear.
  }
}

const TABS: Record<Role, Tab[]> = {
  driver: ['driver'],
  attendant: ['gate', 'driver'],
  admin: ['admin', 'gate', 'driver'],
}

export function tabsFor(role: string): Tab[] {
  return TABS[role as Role] ?? []
}
