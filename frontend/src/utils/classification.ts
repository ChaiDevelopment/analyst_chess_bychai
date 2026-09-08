import type { Classification } from '../types/chess'

interface ClassificationMeta {
  label: string
  color: string // tailwind text color class
  bg: string // tailwind bg color class (subtle)
  symbol: string
}

export const CLASSIFICATION_META: Record<Classification, ClassificationMeta> = {
  BRILLIANT: { label: 'Brilliant', color: 'text-brilliant', bg: 'bg-brilliant/15', symbol: '!!' },
  BEST: { label: 'Best', color: 'text-good', bg: 'bg-good/15', symbol: '★' },
  EXCELLENT: { label: 'Excellent', color: 'text-good', bg: 'bg-good/10', symbol: '!' },
  GOOD: { label: 'Good', color: 'text-brass-400', bg: 'bg-brass-500/10', symbol: '' },
  BOOK: { label: 'Book', color: 'text-ink-200', bg: 'bg-ink-700/60', symbol: '□' },
  INACCURACY: { label: 'Inaccuracy', color: 'text-amber-400', bg: 'bg-amber-400/10', symbol: '?!' },
  MISTAKE: { label: 'Mistake', color: 'text-orange-400', bg: 'bg-orange-400/10', symbol: '?' },
  BLUNDER: { label: 'Blunder', color: 'text-bad', bg: 'bg-bad/15', symbol: '??' },
}

export function formatEval(pawns: number, mateIn?: number | null): string {
  if (mateIn !== null && mateIn !== undefined && Math.abs(mateIn) <= 40) {
    // We only get here if the caller has real mate info; otherwise pawns is used.
  }
  const clamped = Math.max(-99, Math.min(99, pawns))
  const sign = clamped > 0 ? '+' : ''
  return `${sign}${clamped.toFixed(2)}`
}

export function evalToBarPercent(pawns: number): number {
  // Maps an evaluation in pawns to a 0-100 white-share percentage for the
  // vertical eval bar, using a soft saturating curve like most review UIs.
  const clamped = Math.max(-15, Math.min(15, pawns))
  const percent = 50 + (clamped / 15) * 50 * 0.92
  return Math.max(2, Math.min(98, percent))
}
