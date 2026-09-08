interface Props {
  onFirst: () => void
  onPrev: () => void
  onNext: () => void
  onLast: () => void
  isPlaying: boolean
  onTogglePlay: () => void
  disabled: boolean
}

function IconButton({
  onClick,
  label,
  disabled,
  children,
}: {
  onClick: () => void
  label: string
  disabled?: boolean
  children: React.ReactNode
}) {
  return (
    <button
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
      className="w-9 h-9 flex items-center justify-center rounded-md bg-ink-800 hover:bg-ink-700 disabled:opacity-30 disabled:cursor-not-allowed text-ink-100 transition-colors"
    >
      {children}
    </button>
  )
}

export default function BoardControls({
  onFirst,
  onPrev,
  onNext,
  onLast,
  isPlaying,
  onTogglePlay,
  disabled,
}: Props) {
  return (
    <div className="flex items-center justify-center gap-2">
      <IconButton onClick={onFirst} label="First move" disabled={disabled}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M4 3v10M13 3 6 8l7 5V3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        </svg>
      </IconButton>
      <IconButton onClick={onPrev} label="Previous move" disabled={disabled}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M11 3 4 8l7 5V3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        </svg>
      </IconButton>
      <IconButton onClick={onTogglePlay} label={isPlaying ? 'Pause' : 'Autoplay'} disabled={disabled}>
        {isPlaying ? (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <rect x="4" y="3" width="3" height="10" fill="currentColor" />
            <rect x="9" y="3" width="3" height="10" fill="currentColor" />
          </svg>
        ) : (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M5 3.5v9l8-4.5-8-4.5Z" fill="currentColor" />
          </svg>
        )}
      </IconButton>
      <IconButton onClick={onNext} label="Next move" disabled={disabled}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M5 3l7 5-7 5V3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        </svg>
      </IconButton>
      <IconButton onClick={onLast} label="Last move" disabled={disabled}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M12 3v10M3 3l7 5-7 5V3Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        </svg>
      </IconButton>
    </div>
  )
}
