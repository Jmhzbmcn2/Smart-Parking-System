import { describe, expect, it } from 'vitest'

import { formatVnd } from './money'

describe('formatVnd', () => {
  it('groups thousands with dots and adds the dong sign', () => {
    expect(formatVnd(40000)).toBe('40.000 ₫')
    expect(formatVnd(1250000)).toBe('1.250.000 ₫')
  })

  it('formats zero', () => {
    expect(formatVnd(0)).toBe('0 ₫')
  })
})
