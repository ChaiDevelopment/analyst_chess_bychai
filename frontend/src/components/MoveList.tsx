import { useEffect, useRef } from 'react'
import type { MoveAnalysis } from '../types/chess'
import { CLASSIFICATION_META } from '../utils/classification'

interface Props {
  moves: MoveAnalysis[]
  currentPly: number
  onSelect: (ply: number) => void
}

interface Row {
  moveNumber: number
  white?: MoveAnalysis
  black?: MoveAnalysis
}

function groupByMoveNumber(moves: MoveAnalysis[]): Row[] {
  const rows: Row[] = []
  for (const m of moves) {
    let row = rows[rows.length - 1]
    if (!row || row.moveNumber !== m.move_number) {
      row = { moveNumber: m.move_number }
      rows.push(row)
    }
    if (m.color === 'white') row.white = m
    else row.black = m
  }
  return rows
}

function MoveCell({
  move,
  active,
  onSelect,
}: {
  move?: MoveAnalysis
  active: boolean
  onSelect: (ply: number) => void
}) {
  if (!move) return <span className="flex-1" />

  const meta = CLASSIFICATION_META[move.classification]
  const showBadge = move.classification !== 'BOOK' && move.classification !== 'GOOD'

  return (
    <button
      onClick={() => onSelect(move.ply)}
      className={`flex-1 flex items-center gap-1.5 px-2 py-1 rounded text-left transition-colors ${
        active ? 'bg-brass-500/20 ring-1 ring-brass-500/50' : 'hover:bg-ink-800'
      }`}
    >
      <span className="font-sans text-sm text-ink-100">{move.san}</span>
      {showBadge && (
        <span className={`text-xs font-semibold ${meta.color}`}>{meta.symbol}</span>
      )}
    </button>
  )
}

export default function MoveList({ moves, currentPly, onSelect }: Props) {
  const rows = groupByMoveNumber(moves)
  const activeRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [currentPly])

  return (
    <div className="flex flex-col overflow-y-auto h-full">
      {rows.map((row) => {
        const isActiveRow =
          row.white?.ply === currentPly || row.black?.ply === currentPly
        return (
          <div
            key={row.moveNumber}
            ref={isActiveRow ? activeRef : undefined}
            className="flex items-center gap-1 px-1 py-0.5 border-b border-ink-800/60"
          >
            <span className="w-6 text-xs text-ink-500 font-sans tabular-nums shrink-0">
              {row.moveNumber}.
            </span>
            <MoveCell move={row.white} active={row.white?.ply === currentPly} onSelect={onSelect} />
            <MoveCell move={row.black} active={row.black?.ply === currentPly} onSelect={onSelect} />
          </div>
        )
      })}
    </div>
  )
}
