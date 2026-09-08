import { useRef, useState } from 'react'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import ReviewPage from './pages/ReviewPage'
import { analyzeGame, ApiRequestError } from './services/api'
import type { AnalyzeResponse } from './types/chess'

export default function App() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<{ current: number; total: number } | null>(null)
  const progressTimer = useRef<ReturnType<typeof setInterval> | null>(null)

  async function handleAnalyze(pgn: string) {
    setError(null)
    setLoading(true)
    setResult(null)

    // The backend endpoint is synchronous for the MVP, so we simulate a
    // smooth progress readout client-side based on a rough ply estimate
    // while the request is in flight (spec section 21).
    const estimatedPlies = Math.max(10, (pgn.match(/\d+\./g)?.length ?? 10) * 2)
    let fakeCurrent = 0
    setProgress({ current: 0, total: estimatedPlies })
    progressTimer.current = setInterval(() => {
      fakeCurrent = Math.min(estimatedPlies - 1, fakeCurrent + 1)
      setProgress({ current: fakeCurrent, total: estimatedPlies })
    }, 180)

    try {
      const data = await analyzeGame(pgn)
      setResult(data)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.message)
      } else {
        setError('Something went wrong while analyzing the game. Please try again.')
      }
    } finally {
      if (progressTimer.current) clearInterval(progressTimer.current)
      setProgress(null)
      setLoading(false)
    }
  }

  function goHome() {
    setResult(null)
    setError(null)
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar page={result ? 'review' : 'home'} onNavigateHome={goHome} />
      <main className="flex-1">
        {result ? (
          <ReviewPage data={result} />
        ) : (
          <HomePage onAnalyze={handleAnalyze} loading={loading} error={error} progress={progress} />
        )}
      </main>
    </div>
  )
}
