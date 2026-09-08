interface Props {
  current: number
  total: number
}

export default function AnalysisProgress({ current, total }: Props) {
  const percent = total > 0 ? Math.round((current / total) * 100) : 0
  return (
    <div className="flex flex-col items-center gap-4 py-16 font-sans">
      <div className="w-10 h-10 border-2 border-ink-700 border-t-brass-500 rounded-full animate-spin" />
      <div className="text-ink-300 text-sm">
        {total > 0 ? `Analyzing move ${current}/${total}…` : 'Analyzing game…'}
      </div>
      <div className="w-64 h-1.5 bg-ink-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-brass-500 transition-all duration-300"
          style={{ width: `${Math.max(6, percent)}%` }}
        />
      </div>
    </div>
  )
}
