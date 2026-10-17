import { describe, expect, it } from 'vitest'

import { formatCountdown, secondsLeft } from './reservation'

const EXPIRES = '2026-10-19T08:10:00+07:00'
const at = (clock: string) => Date.parse(`2026-10-19T${clock}+07:00`)

describe('secondsLeft', () => {
  it('counts down to the expiry', () => {
    expect(secondsLeft(EXPIRES, at('08:00:00'))).toBe(600)
    expect(secondsLeft(EXPIRES, at('08:09:30'))).toBe(30)
  })

  it('rounds a partial second up', () => {
    expect(secondsLeft(EXPIRES, at('08:09:59') + 500)).toBe(1)
  })

  it('is never negative', () => {
    expect(secondsLeft(EXPIRES, at('08:10:00'))).toBe(0)
    expect(secondsLeft(EXPIRES, at('08:11:00'))).toBe(0)
  })
})

describe('formatCountdown', () => {
  it('shows mm:ss', () => {
    expect(formatCountdown(600)).toBe('10:00')
    expect(formatCountdown(65)).toBe('01:05')
    expect(formatCountdown(0)).toBe('00:00')
  })
})
