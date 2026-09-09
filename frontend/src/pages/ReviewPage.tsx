import { useCallback, useEffect, useState } from 'react'
import type { AnalyzeResponse, Classification, Color, PositionAnalyzeResponse } from '../types/chess'
import ChessBoardView from '../components/ChessBoardView'
import EvaluationBar from '../components/EvaluationBar'
import BoardControls from '../components/BoardControls'
import MoveList from '../components/MoveList'
import AnalysisPanel from '../components/AnalysisPanel'
import GameSummaryView from '../components/GameSummaryView'
import { analyzePosition } from '../services/api'

const STARTING_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

interface Props {
  data: AnalyzeResponse
}

type Tab = 'moves' | 'summary'
type MoveFilter = { classification: Classification; color: Color }

export default function ReviewPage({ data }: Props) {
  const { moves, summary, game } = data
  const [ply, setPly] = useState(moves.length > 0 ? 0 : 0) // 0 = starting position
  const [showBestMove, setShowBestMove] = useState(true)
  const [isPlaying, setIsPlaying] = useState(false)
  const [tab, setTab] = useState<Tab>('moves')
  const [moveFilter, setMoveFilter] = useState<MoveFilter | null>(null)
  const [exploration, setExploration] = useState<PositionAnalyzeResponse | null>(null)
  const [exploreFen, setExploreFen] = useState<string | null>(null)
  const [exploreLoading, setExploreLoading] = useState(false)
  const [exploreError, setExploreError] = useState<string | null>(null)

  const visibleMoves = moveFilter
    ? moves.filter((move) => move.classification === moveFilter.classification && move.color === moveFilter.color)
    : moves

  const currentMove = exploration?.move ?? (ply > 0 ? moves[ply - 1] : null)
  const currentFen = exploreFen ?? (currentMove ? currentMove.fen_after : STARTING_FEN)

  const goTo = useCallback(
    (newPly: number) => {
      setPly(Math.max(0, Math.min(moves.length, newPly)))
    },
    [moves.length]
  )

  const selectByPly = useCallback((targetPly: number) => {
    setExploration(null)
    setExploreFen(null)
    setTab('moves')
    setPly(targetPly)
  }, [])

  const exploreMove = useCallback(async (uci: string, fenAfter: string) => {
    setIsPlaying(false)
    setExploreError(null)
    setExploreFen(fenAfter)
    setExploreLoading(true)
    try {
      const result = await analyzePosition(currentFen, uci)
      setExploration(result)
      setTab('moves')
    } catch (error) {
      setExploreError(error instanceof Error ? error.message : 'Could not analyse this move.')
    } finally {
      setExploreLoading(false)
    }
  }, [currentFen])

  const selectClassification = useCallback((classification: Classification, color: Color) => {
    const firstMatch = moves.find((move) => move.classification === classification && move.color === color)
    setMoveFilter({ classification, color })
    setTab('moves')
    if (firstMatch) setPly(firstMatch.ply)
  }, [moves])

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return
      if (e.key === 'ArrowLeft') goTo(ply - 1)
      else if (e.key === 'ArrowRight') goTo(ply + 1)
      else if (e.key === 'Home') goTo(0)
      else if (e.key === 'End') goTo(moves.length)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [ply, moves.length, goTo])

  useEffect(() => {
    if (!isPlaying) return
    if (ply >= moves.length) {
      setIsPlaying(false)
      return
    }
    const timer = setTimeout(() => setPly((p) => p + 1), 900)
    return () => clearTimeout(timer)
  }, [isPlaying, ply, moves.length])

  const [boardWidth, setBoardWidth] = useState(() => Math.min(520, window.innerWidth - 48))

  useEffect(() => {
    const updateBoardWidth = () => setBoardWidth(Math.max(280, Math.min(520, window.innerWidth - 48)))
    updateBoardWidth()
    window.addEventListener('resize', updateBoardWidth)
    return () => window.removeEventListener('resize', updateBoardWidth)
  }, [])

  const evalPawns = currentMove
    ? currentMove.evaluation_after
    : moves[0]?.evaluation_before ?? 0
  const mateIn = currentMove?.mate_after ?? null

  const title = [game.white, game.black].filter(Boolean).join(' vs ') || 'Game Review'

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <div className="mb-4 flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="font-display text-2xl text-ink-50">{title}</h1>
        <span className="text-sm text-ink-500 font-sans">
          {game.result} · {summary.opening}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[auto_1fr_360px] gap-6 items-start">
        {/* LEFT: board */}
        <div className="flex gap-3 justify-center lg:justify-start">
          <EvaluationBar evaluation={evalPawns} mateIn={mateIn} />
          <div className="flex flex-col gap-3">
            <ChessBoardView
              fen={currentFen}
              currentMove={currentMove}
              showBestMove={showBestMove}
              boardWidth={boardWidth}
              onExploreMove={exploreMove}
            />
            <BoardControls
              onFirst={() => goTo(0)}
              onPrev={() => goTo(ply - 1)}
              onNext={() => goTo(ply + 1)}
              onLast={() => goTo(moves.length)}
              isPlaying={isPlaying}
              onTogglePlay={() => setIsPlaying((p) => !p)}
              disabled={moves.length === 0}
            />
          </div>
        </div>

        {/* CENTER: move list */}
        <div className="bg-ink-900/60 border border-ink-800 rounded-lg h-[420px] lg:h-[560px] flex flex-col">
          <div className="px-3 py-2 border-b border-ink-800 text-xs font-sans text-ink-500 uppercase tracking-wide flex items-center justify-between">
            <span>{moveFilter ? `${moveFilter.color} · ${moveFilter.classification} (${visibleMoves.length})` : 'Moves'}</span>
            {moveFilter && (
              <button
                type="button"
                onClick={() => setMoveFilter(null)}
                className="text-brass-400 hover:text-brass-300 normal-case"
              >
                Show all
              </button>
            )}
          </div>
          <MoveList moves={visibleMoves} currentPly={ply} onSelect={selectByPly} />
        </div>

        {/* RIGHT: analysis / summary */}
        <div className="bg-ink-900/60 border border-ink-800 rounded-lg h-[420px] lg:h-[560px] flex flex-col">
          <div className="flex border-b border-ink-800 font-sans text-sm shrink-0">
            <button
              onClick={() => setTab('moves')}
              className={`flex-1 py-2.5 transition-colors ${
                tab === 'moves' ? 'text-brass-400 border-b-2 border-brass-500' : 'text-ink-400 hover:text-ink-200'
              }`}
            >
              Analysis
            </button>
            <button
              onClick={() => setTab('summary')}
              className={`flex-1 py-2.5 transition-colors ${
                tab === 'summary' ? 'text-brass-400 border-b-2 border-brass-500' : 'text-ink-400 hover:text-ink-200'
              }`}
            >
              Summary
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            {tab === 'moves' ? (
              <>
                <AnalysisPanel
                  move={currentMove}
                  showBestMove={showBestMove}
                  onToggleShowBestMove={() => setShowBestMove((v) => !v)}
                  candidates={exploration?.candidates}
                  loading={exploreLoading}
                  error={exploreError}
                />
              {exploreLoading && <div className="px-4 pb-3 text-xs text-brass-400">Engine is analysing your move…</div>}
              </>
            ) : (
              <div className="h-full overflow-y-auto p-4">
                <GameSummaryView
                  summary={summary}
                  onJumpToPly={selectByPly}
                  onSelectClassification={selectClassification}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
