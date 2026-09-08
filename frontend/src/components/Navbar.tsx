interface Props {
  page: 'home' | 'review'
  onNavigateHome: () => void
}

export default function Navbar({ page, onNavigateHome }: Props) {
  return (
    <header className="border-b border-ink-800 sticky top-0 z-20 bg-ink-950/90 backdrop-blur">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <button
          onClick={onNavigateHome}
          className="flex items-center gap-2 font-display text-lg text-ink-50"
        >
          <span className="text-brass-500">♞</span>
          Chess Review
        </button>
        <nav className="flex items-center gap-5 font-sans text-sm text-ink-300">
          <button
            onClick={onNavigateHome}
            className={page === 'home' ? 'text-brass-400' : 'hover:text-ink-100 transition-colors'}
          >
            Analyze
          </button>
          <span className="hidden sm:inline text-ink-500">Local Stockfish analysis</span>
        </nav>
      </div>
    </header>
  )
}
