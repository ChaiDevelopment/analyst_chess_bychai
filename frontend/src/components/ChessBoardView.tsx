import { Chessboard } from 'react-chessboard'
import type { Square } from 'chess.js'
import type { MoveAnalysis } from '../types/chess'

interface Props {
  fen: string
  currentMove: MoveAnalysis | null
  showBestMove: boolean
  boardWidth: number
}

function squareStyle(color: string) {
  return {
    background: color,
  }
}

export default function ChessBoardView({ fen, currentMove, showBestMove, boardWidth }: Props) {
  const customSquareStyles: Record<string, React.CSSProperties> = {}

  if (currentMove) {
    const from = currentMove.uci.slice(0, 2)
    const to = currentMove.uci.slice(2, 4)
    customSquareStyles[from] = squareStyle('rgba(201, 162, 39, 0.35)')
    customSquareStyles[to] = squareStyle('rgba(201, 162, 39, 0.45)')
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
        animationDuration={200}
      />
    </div>
  )
}
