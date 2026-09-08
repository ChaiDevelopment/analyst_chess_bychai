import type { MoveAnalysis } from '../types/chess'
import { CLASSIFICATION_META, formatEval } from '../utils/classification'

interface Props {
  move: MoveAnalysis | null
  showBestMove: boolean
  onToggleShowBestMove: () => void
}

export default function AnalysisPanel({ move, showBestMove, onToggleShowBestMove }: Props) {
  if (!move) {
    return (
      <div className="h-full flex items-center justify-center text-ink-500 text-sm px-4 text-center">
        Select a move to see its evaluation and analysis.
      </div>
    )
  }

  const meta = CLASSIFICATION_META[move.classification]
  const moveLabel = `${move.move_number}.${move.color === 'black' ? '..' : ''} ${move.san}`
  const swing = Math.round((move.evaluation_after - move.evaluation_before) * 100) / 100

  return (
    <div className="flex flex-col gap-4 p-4 overflow-y-auto h-full">
      <div>
        <div className="flex items-center gap-2">
          <h2 className="font-display text-xl text-ink-50">{moveLabel}</h2>
          <span className={`text-xs font-sans font-semibold px-2 py-0.5 rounded-full ${meta.bg} ${meta.color}`}>
            {meta.label}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 font-sans text-sm">
        <div className="bg-ink-800/60 rounded-md p-3">
          <div className="text-ink-500 text-xs mb-1">Evaluation</div>
          <div className="text-ink-50 tabular-nums">
            {formatEval(move.evaluation_before)} → {formatEval(move.evaluation_after)}
          </div>
        </div>
        <div className="bg-ink-800/60 rounded-md p-3">
          <div className="text-ink-500 text-xs mb-1">Loss</div>
          <div className={`tabular-nums ${move.centipawn_loss > 0 ? 'text-bad' : 'text-good'}`}>
            {move.centipawn_loss > 0 ? '-' : ''}{Math.abs(swing).toFixed(2)} pawns
          </div>
        </div>
      </div>

      {move.classification !== 'BEST' &&
        move.classification !== 'BOOK' &&
        move.best_move_san && (
          <div className="bg-ink-800/60 rounded-md p-3 font-sans text-sm flex items-center justify-between">
            <div>
              <div className="text-ink-500 text-xs mb-1">Best move</div>
              <div className="text-good">{move.best_move_san}</div>
            </div>
            <label className="flex items-center gap-2 text-xs text-ink-400 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={showBestMove}
                onChange={onToggleShowBestMove}
                className="accent-brass-500"
              />
              Show on board
            </label>
          </div>
        )}

      {move.tactical_tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {move.tactical_tags.map((tag) => (
            <span
              key={tag}
              className="text-xs font-sans px-2 py-0.5 rounded-full bg-ink-700/60 text-ink-200"
            >
              {tag.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      {move.explanation && (
        <div className="font-sans text-sm text-ink-200 leading-relaxed border-l-2 border-brass-500/50 pl-3">
          {move.explanation}
        </div>
      )}

      {move.variation.length > 0 && (
        <div>
          <div className="text-ink-500 text-xs mb-1.5 font-sans">Best line</div>
          <div className="font-sans text-sm text-ink-200 bg-ink-800/60 rounded-md p-3 leading-relaxed">
            {move.variation.join(' ')}
          </div>
        </div>
      )}
    </div>
  )
}
