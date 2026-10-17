const PLATE_RE = /^\d{2}[A-Z][A-Z0-9]?-\d{3}\.?\d{2}$/

export type GateEvent = {
  id: number
  gate_id: string
  plate: string | null
  confidence: number | null
  source: string
  received_at: string
  action: 'entered' | 'exited' | 'manual_required'
  session_id: number | null
  barrier_opened_at: string | null
}

export function normalizePlate(plate: string): string {
  return plate.trim().toUpperCase()
}

export function isValidPlate(plate: string): boolean {
  return PLATE_RE.test(normalizePlate(plate))
}

/** The barrier badge shows "open" for 5 s after the newest event opened it. */
export function barrierOpen(event: { barrier_opened_at: string | null } | undefined, now: number) {
  if (!event?.barrier_opened_at) return false
  return now - Date.parse(event.barrier_opened_at) < 5000
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', hour12: false })
}
