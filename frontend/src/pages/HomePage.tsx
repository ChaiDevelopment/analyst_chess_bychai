import PgnInput from '../components/PgnInput'
import AnalysisProgress from '../components/AnalysisProgress'

interface Props {
  onAnalyze: (pgn: string) => void
  loading: boolean
  error: string | null
  progress: { current: number; total: number } | null
}

export default function HomePage({ onAnalyze, loading, error, progress }: Props) {
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-24 flex flex-col items-center text-center">
      <h1 className="font-display text-4xl sm:text-5xl text-ink-50 max-w-2xl leading-tight">
        Review your chess game
      </h1>
      <p className="mt-4 text-ink-300 font-sans text-lg max-w-md">
        Analyze every move for free with Stockfish.
      </p>

      <div className="mt-10 w-full flex justify-center">
        {loading ? (
          <AnalysisProgress current={progress?.current ?? 0} total={progress?.total ?? 0} />
        ) : (
          <PgnInput onAnalyze={onAnalyze} loading={loading} error={error} />
        )}
      </div>
    </div>
  )
}
