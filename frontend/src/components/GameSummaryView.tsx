import type { Classification, Color, GameSummary, MoveStats } from '../types/chess'
import { CLASSIFICATION_META } from '../utils/classification'

interface Props {
  summary: GameSummary
  onJumpToPly: (ply: number) => void
  onSelectClassification: (classification: Classification, color: Color) => void
}

const STAT_ORDER: (keyof MoveStats)[] = [
  'brilliant',
  'great',
  'best',
  'excellent',
  'good',
  'book',
  'inaccuracy',
  'mistake',
  'blunder',
  'miss',
]

const STAT_TO_CLASSIFICATION: Record<keyof MoveStats, keyof typeof CLASSIFICATION_META> = {
  brilliant: 'BRILLIANT',
  great: 'GREAT',
  best: 'BEST',
  excellent: 'EXCELLENT',
  good: 'GOOD',
  book: 'BOOK',
  inaccuracy: 'INACCURACY',
  mistake: 'MISTAKE',
  blunder: 'BLUNDER',
  miss: 'MISS',
}

function StatRow({
  stats,
  color,
  onSelectClassification,
}: {
  stats: MoveStats
  color: Color
  onSelectClassification: (classification: Classification, color: Color) => void
}) {
  return (
    <div className="flex flex-col gap-1">
      {STAT_ORDER.map((key) => {
        const count = stats[key]
        const meta = CLASSIFICATION_META[STAT_TO_CLASSIFICATION[key]]
        return (
          <button
            key={key}
            type="button"
            onClick={() => onSelectClassification(STAT_TO_CLASSIFICATION[key], color)}
            className="flex items-center justify-between text-sm font-sans rounded px-1.5 py-1 -mx-1.5 hover:bg-ink-800 transition-colors text-left"
            title={`Show ${count} ${meta.label.toLowerCase()} move${count === 1 ? '' : 's'}`}
          >
            <span className={meta.color}>{meta.label}</span>
            <span className="text-ink-100 tabular-nums">{count}</span>
          </button>
        )
      })}
    </div>
  )
}

function AccuracyDial({ label, accuracy }: { label: string; accuracy: number }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div className="font-display text-4xl text-ink-50 tabular-nums">{accuracy.toFixed(1)}</div>
      <div className="text-xs text-ink-500 font-sans">{label} accuracy</div>
    </div>
  )
}

export default function GameSummaryView({ summary, onJumpToPly, onSelectClassification }: Props) {
  return (
    <div className="flex flex-col gap-6 font-sans">
      <div className="flex items-center justify-around bg-ink-800/60 rounded-lg py-6">
        <AccuracyDial label="White" accuracy={summary.white.accuracy} />
        <div className="w-px h-12 bg-ink-700" />
        <AccuracyDial label="Black" accuracy={summary.black.accuracy} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-ink-500 mb-2">White moves</div>
          <StatRow stats={summary.white.stats} color="white" onSelectClassification={onSelectClassification} />
        </div>
        <div>
          <div className="text-xs text-ink-500 mb-2">Black moves</div>
          <StatRow stats={summary.black.stats} color="black" onSelectClassification={onSelectClassification} />
        </div>
      </div>

      <div className="text-sm text-ink-300 flex justify-between">
        <span>Opening</span>
        <span className="text-ink-100">{summary.opening}</span>
      </div>

      {summary.biggest_mistake && (
        <button
          onClick={() => onJumpToPly(summary.biggest_mistake!.ply)}
          className="text-left bg-ink-800/60 hover:bg-ink-800 transition-colors rounded-md p-3"
        >
          <div className="text-xs text-ink-500 mb-1">Biggest mistake</div>
          <div className="text-bad text-sm">
            {summary.biggest_mistake.move_number}
            {summary.biggest_mistake.color === 'black' ? '...' : '.'} {summary.biggest_mistake.san}
          </div>
        </button>
      )}

      {summary.best_move_played && (
        <button
          onClick={() => onJumpToPly(summary.best_move_played!.ply)}
          className="text-left bg-ink-800/60 hover:bg-ink-800 transition-colors rounded-md p-3"
        >
          <div className="text-xs text-ink-500 mb-1">Standout move</div>
          <div className="text-good text-sm">
            {summary.best_move_played.move_number}
            {summary.best_move_played.color === 'black' ? '...' : '.'} {summary.best_move_played.san}
          </div>
        </button>
      )}

      {summary.most_critical_position && (
        <button
          onClick={() => onJumpToPly(summary.most_critical_position!.ply)}
          className="text-left bg-ink-800/60 hover:bg-ink-800 transition-colors rounded-md p-3"
        >
          <div className="text-xs text-ink-500 mb-1">Most critical position</div>
          <div className="text-brass-400 text-sm">
            {summary.most_critical_position.move_number}
            {summary.most_critical_position.color === 'black' ? '...' : '.'}{' '}
            {summary.most_critical_position.san}
          </div>
        </button>
      )}
    </div>
  )
}
