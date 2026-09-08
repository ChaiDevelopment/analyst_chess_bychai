import { evalToBarPercent, formatEval } from '../utils/classification'

interface Props {
  evaluation: number
  mateIn?: number | null
  orientation?: 'vertical' | 'horizontal'
}

export default function EvaluationBar({ evaluation, mateIn, orientation = 'vertical' }: Props) {
  const whitePercent = evalToBarPercent(evaluation)
  const label = mateIn
    ? `M${Math.abs(mateIn)}`
    : formatEval(evaluation)

  if (orientation === 'horizontal') {
    return (
      <div className="w-full h-3 rounded-full overflow-hidden bg-ink-800 flex">
        <div
          className="h-full bg-board-light transition-all duration-500 ease-out"
          style={{ width: `${whitePercent}%` }}
        />
        <div className="h-full bg-ink-900 flex-1 transition-all duration-500 ease-out" />
      </div>
    )
  }

  return (
    <div className="relative w-8 h-full min-h-[280px] rounded-md overflow-hidden bg-ink-900 border border-ink-700 flex flex-col-reverse shrink-0">
      <div
        className="w-full bg-board-light transition-[height] duration-500 ease-out"
        style={{ height: `${whitePercent}%` }}
      />
      <span
        className="absolute left-1/2 -translate-x-1/2 text-[10px] font-semibold font-sans tracking-tight px-1 rounded"
        style={{
          top: whitePercent > 50 ? 'auto' : '4px',
          bottom: whitePercent > 50 ? '4px' : 'auto',
          color: whitePercent > 50 ? '#1B1F24' : '#EDE3CC',
        }}
      >
        {label}
      </span>
    </div>
  )
}
