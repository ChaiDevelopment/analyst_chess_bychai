import { useRef, useState } from 'react'
import { EXAMPLE_PGN } from '../utils/examplePgn'

interface Props {
  onAnalyze: (pgn: string) => void
  loading: boolean
  error: string | null
}

export default function PgnInput({ onAnalyze, loading, error }: Props) {
  const [pgn, setPgn] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setPgn(String(reader.result ?? ''))
    reader.readAsText(file)
  }

  return (
    <div className="flex flex-col gap-4 w-full max-w-2xl">
      <textarea
        value={pgn}
        onChange={(e) => setPgn(e.target.value)}
        placeholder="Paste your PGN here..."
        rows={10}
        spellCheck={false}
        className="w-full resize-y rounded-lg bg-ink-900 border border-ink-700 focus:border-brass-500/60 px-4 py-3 font-mono text-sm text-ink-100 placeholder:text-ink-500 outline-none transition-colors"
      />

      {error && (
        <div className="text-sm text-bad bg-bad/10 border border-bad/30 rounded-md px-3 py-2 font-sans">
          {error}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3 font-sans text-sm">
        <button
          onClick={() => onAnalyze(pgn)}
          disabled={loading || !pgn.trim()}
          className="px-5 py-2.5 rounded-md bg-brass-500 hover:bg-brass-600 disabled:opacity-40 disabled:cursor-not-allowed text-ink-950 font-semibold transition-colors"
        >
          {loading ? 'Analyzing…' : 'Analyze Game'}
        </button>

        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          className="px-4 py-2.5 rounded-md bg-ink-800 hover:bg-ink-700 text-ink-100 transition-colors disabled:opacity-40"
        >
          Upload PGN
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pgn,.txt"
          onChange={handleFile}
          className="hidden"
        />

        <button
          onClick={() => setPgn(EXAMPLE_PGN)}
          disabled={loading}
          className="px-4 py-2.5 rounded-md text-brass-400 hover:text-brass-300 underline underline-offset-4 decoration-brass-500/40 transition-colors disabled:opacity-40"
        >
          Try Example Game
        </button>
      </div>
    </div>
  )
}
