import { describe, expect, it } from 'vitest'

import {
  barrierOpen,
  formatTime,
  isValidPlate,
  manualPrefill,
  pendingPaymentId,
  type GateEvent,
} from './gate'

const NOW = Date.parse('2026-10-19T08:00:10+07:00')

describe('barrierOpen', () => {
  it('is open when the barrier opened less than 5 s ago', () => {
    expect(barrierOpen({ barrier_opened_at: '2026-10-19T08:00:06+07:00' }, NOW)).toBe(true)
  })

  it('is closed after 5 s', () => {
    expect(barrierOpen({ barrier_opened_at: '2026-10-19T08:00:04+07:00' }, NOW)).toBe(false)
  })

  it('is closed without an event or without a barrier opening', () => {
    expect(barrierOpen(undefined, NOW)).toBe(false)
    expect(barrierOpen({ barrier_opened_at: null }, NOW)).toBe(false)
  })
})

describe('isValidPlate', () => {
  it('accepts Vietnamese plates after trim and upper-casing', () => {
    expect(isValidPlate('30A-123.45')).toBe(true)
    expect(isValidPlate(' 30a-12345 ')).toBe(true)
    expect(isValidPlate('51F1-234.56')).toBe(true)
  })

  it('rejects other shapes', () => {
    expect(isValidPlate('')).toBe(false)
    expect(isValidPlate('ABC-123')).toBe(false)
  })
})

describe('formatTime', () => {
  it('shows UTC+7 wall-clock time', () => {
    expect(formatTime('2026-10-19T01:00:00Z')).toContain('08:00:00')
  })
})

describe('manualPrefill', () => {
  const event = (action: GateEvent['action'], gate_id: string): GateEvent => ({
    id: 1,
    gate_id,
    plate: '30A-123.45',
    confidence: 0.6,
    source: 'lpr',
    received_at: '2026-10-19T08:00:00+07:00',
    action,
    session_id: null,
    barrier_opened_at: null,
    payment_id: null,
  })

  it('uses the gate and plate of a manual_required event, including an exit gate', () => {
    expect(manualPrefill(event('manual_required', 'OUT-1'))).toEqual({ gate: 'OUT-1', plate: '30A-123.45' })
  })

  it('falls back to IN-1 and an empty plate otherwise', () => {
    expect(manualPrefill(event('entered', 'OUT-1'))).toEqual({ gate: 'IN-1', plate: '' })
    expect(manualPrefill(undefined)).toEqual({ gate: 'IN-1', plate: '' })
  })
})

describe('pendingPaymentId', () => {
  const event = (action: GateEvent['action'], payment_id: number | null) =>
    ({ action, payment_id }) as GateEvent

  it('returns the payment of a payment_required or payment_failed event', () => {
    expect(pendingPaymentId(event('payment_required', 7))).toBe(7)
    expect(pendingPaymentId(event('payment_failed', 7))).toBe(7)
  })

  it('returns null once the exit completed or for other events', () => {
    expect(pendingPaymentId(event('exited', 7))).toBeNull()
    expect(pendingPaymentId(event('entered', null))).toBeNull()
    expect(pendingPaymentId(undefined)).toBeNull()
  })
})
