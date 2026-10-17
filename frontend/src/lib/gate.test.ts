import { describe, expect, it } from 'vitest'

import { barrierOpen, formatTime, isValidPlate } from './gate'

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
