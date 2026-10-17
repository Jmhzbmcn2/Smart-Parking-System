import { describe, expect, it } from 'vitest'

import { getSession, tabsFor } from './auth'

describe('tabsFor', () => {
  it('gives a driver only the driver tab', () => {
    expect(tabsFor('driver')).toEqual(['driver'])
  })

  it('gives an attendant gate then driver', () => {
    expect(tabsFor('attendant')).toEqual(['gate', 'driver'])
  })

  it('gives an admin every tab, admin first', () => {
    expect(tabsFor('admin')).toEqual(['admin', 'gate', 'driver'])
  })

  it('gives an unknown role no tabs', () => {
    expect(tabsFor('stranger')).toEqual([])
  })
})

describe('getSession', () => {
  it('returns null when localStorage is unavailable', () => {
    expect(getSession()).toBeNull()
  })
})
