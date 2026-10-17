const PLATE_RE = /^\d{2}[A-Z][A-Z0-9]?-\d{3}\.?\d{2}$/

export type GateEvent = {
  id: number
  gate_id: string
  plate: string | null
  confidence: number | null
  source: string
  received_at: string
  action: 'entered' | 'exited' | 'manual_required' | 'payment_required' | 'payment_failed'
  session_id: number | null
  barrier_opened_at: string | null
  suggested_slot: string | null
  payment_id: number | null
}

export type Payment = {
  id: number
  session_id: number
  plate: string
  gate_id: string
  amount: number
  status: 'pending' | 'paid' | 'failed'
  method: 'qr' | 'cash' | null
  qr_payload: string
}

/**
 * The payment of the newest payment_required / payment_failed event (events are newest first).
 * Other gate events must not hide it; the caller hides it once the payment status is "paid".
 */
export function pendingPaymentId(events: GateEvent[] | null | undefined): number | null {
  const event = events?.find((e) => e.action === 'payment_required' || e.action === 'payment_failed')
  return event?.payment_id ?? null
}

export function normalizePlate(plate: string): string {
  return plate.trim().toUpperCase()
}

export function isValidPlate(plate: string): boolean {
  return PLATE_RE.test(normalizePlate(plate))
}

/** Manual entry form defaults: a `manual_required` event pre-fills its own gate and plate. */
export function manualPrefill(event: GateEvent | undefined): { gate: string; plate: string } {
  if (event?.action !== 'manual_required') return { gate: 'IN-1', plate: '' }
  return { gate: event.gate_id, plate: event.plate ?? '' }
}

/** The barrier badge shows "open" for 5 s after the newest event opened it. */
export function barrierOpen(event: { barrier_opened_at: string | null } | undefined, now: number) {
  if (!event?.barrier_opened_at) return false
  return now - Date.parse(event.barrier_opened_at) < 5000
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', hour12: false })
}
