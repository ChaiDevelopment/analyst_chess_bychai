import { describe, expect, it } from 'vitest'
import { evalToBarPercent, formatEval, CLASSIFICATION_META } from '../utils/classification'

describe('formatEval', () => {
  it('formats positive evaluations with a leading plus', () => {
    expect(formatEval(1.23)).toBe('+1.23')
  })

  it('formats negative evaluations without a double sign', () => {
    expect(formatEval(-0.5)).toBe('-0.50')
  })

  it('formats zero without a sign', () => {
    expect(formatEval(0)).toBe('0.00')
  })
})

describe('evalToBarPercent', () => {
  it('returns 50 for a dead-even position', () => {
    expect(evalToBarPercent(0)).toBe(50)
  })

  it('increases with a bigger white advantage', () => {
    const low = evalToBarPercent(1)
    const high = evalToBarPercent(5)
    expect(high).toBeGreaterThan(low)
  })

  it('is clamped within [2, 98]', () => {
    expect(evalToBarPercent(999)).toBeLessThanOrEqual(98)
    expect(evalToBarPercent(-999)).toBeGreaterThanOrEqual(2)
  })
})

describe('CLASSIFICATION_META', () => {
  it('has an entry for every classification the backend can send', () => {
    const expected = [
      'BOOK', 'BRILLIANT', 'GREAT', 'BEST', 'EXCELLENT', 'GOOD', 'INACCURACY', 'MISTAKE', 'BLUNDER', 'MISS',
    ]
    for (const key of expected) {
      expect(CLASSIFICATION_META).toHaveProperty(key)
    }
  })
})
