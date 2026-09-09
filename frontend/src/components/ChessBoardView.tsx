import { Chessboard } from 'react-chessboard'
import { Chess, type Square } from 'chess.js'
import { useMemo, useState, type CSSProperties } from 'react'
import type { MoveAnalysis } from '../types/chess'

interface Props {
  fen: string
  currentMove: MoveAnalysis | null
  showBestMove: boolean
  boardWidth: number
  onExploreMove?: (uci: string, fenAfter: string) => void
}

function squareStyle(color: string) {
  return {
    background: color,
  }
}

export default function ChessBoardView({ fen, currentMove, showBestMove, boardWidth, onExploreMove }: Props) {
  const customSquareStyles: Record<string, CSSProperties> = {}
  const [selectedSquare, setSelectedSquare] = useState<Square | null>(null)
  const chess = useMemo(() => new Chess(fen), [fen])

  if (currentMove) {
    const from = currentMove.uci.slice(0, 2)
    const to = currentMove.uci.slice(2, 4)
    customSquareStyles[from] = squareStyle('rgba(201, 162, 39, 0.35)')
    customSquareStyles[to] = squareStyle('rgba(201, 162, 39, 0.45)')
  }
  if (selectedSquare) {
    customSquareStyles[selectedSquare] = squareStyle('rgba(95, 163, 122, 0.55)')
    for (const legalMove of chess.moves({ square: selectedSquare, verbose: true })) {
      customSquareStyles[legalMove.to] = squareStyle('rgba(95, 163, 122, 0.28)')
    }
  }

  function onSquareClick(square: Square) {
    if (!onExploreMove) return
    const piece = chess.get(square)
    if (!selectedSquare) {
      if (piece?.color === chess.turn()) setSelectedSquare(square)
      return
    }
    const isLegalDestination = chess.moves({ square: selectedSquare, verbose: true })
      .some((legalMove) => legalMove.to === square)
    if (isLegalDestination) {
      const move = chess.move({ from: selectedSquare, to: square, promotion: 'q' })
      setSelectedSquare(null)
      onExploreMove(move.from + move.to + (move.promotion ?? ''), chess.fen())
      return
    }
    setSelectedSquare(piece?.color === chess.turn() ? square : null)
  }

  const arrows: [Square, Square, string?][] = []
  if (currentMove) {
    const played: [Square, Square, string?] = [
      currentMove.uci.slice(0, 2) as Square,
      currentMove.uci.slice(2, 4) as Square,
      '#C9573F',
    ]
    if (
      showBestMove &&
      currentMove.best_move &&
      currentMove.best_move !== currentMove.uci &&
      currentMove.classification !== 'BEST' &&
      currentMove.classification !== 'BOOK'
    ) {
      arrows.push([
        currentMove.best_move.slice(0, 2) as Square,
        currentMove.best_move.slice(2, 4) as Square,
        '#5FA37A',
      ])
      arrows.push(played)
    }
  }

  return (
    <div className="rounded-lg overflow-hidden border border-ink-700 shadow-2xl shadow-black/40">
      <Chessboard
        position={fen}
        arePiecesDraggable={false}
        boardWidth={boardWidth}
        customBoardStyle={{ borderRadius: '0' }}
        customDarkSquareStyle={{ backgroundColor: '#6B5A45' }}
        customLightSquareStyle={{ backgroundColor: '#EDE3CC' }}
        customSquareStyles={customSquareStyles}
        customArrows={arrows}
        onSquareClick={onSquareClick}
        animationDuration={200}
      />
    </div>
  )
}
