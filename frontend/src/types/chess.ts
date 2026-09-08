export type Classification =
  | 'BOOK'
  | 'BRILLIANT'
  | 'GREAT'
  | 'BEST'
  | 'EXCELLENT'
  | 'GOOD'
  | 'INACCURACY'
  | 'MISTAKE'
  | 'BLUNDER'
  | 'MISS'

export type Color = 'white' | 'black'

export interface GameInfo {
  event?: string | null
  site?: string | null
  date?: string | null
  white?: string | null
  black?: string | null
  result?: string | null
  eco?: string | null
  opening?: string | null
  total_plies: number
}

export interface MoveAnalysis {
  ply: number
  move_number: number
  color: Color
  san: string
  uci: string
  fen_before: string
  fen_after: string
  evaluation_before: number
  evaluation_after: number
  mate_before?: number | null
  mate_after?: number | null
  best_move: string
  best_move_san: string
  centipawn_loss: number
  classification: Classification
  is_book: boolean
  tactical_tags: string[]
  variation: string[]
  explanation?: string | null
}

export interface MoveStats {
  brilliant: number
  great: number
  best: number
  excellent: number
  good: number
  book: number
  inaccuracy: number
  mistake: number
  blunder: number
  miss: number
}

export interface PlayerSummary {
  accuracy: number
  average_centipawn_loss: number
  stats: MoveStats
}

export interface CriticalMoment {
  ply: number
  move_number: number
  color: Color
  san: string
  classification: Classification
  evaluation_swing: number
}

export interface GameSummary {
  white: PlayerSummary
  black: PlayerSummary
  biggest_mistake?: CriticalMoment | null
  best_move_played?: CriticalMoment | null
  most_critical_position?: CriticalMoment | null
  opening: string
  result?: string | null
}

export interface AnalyzeResponse {
  game: GameInfo
  moves: MoveAnalysis[]
  summary: GameSummary
  ai_explanations_enabled: boolean
  engine_depth: number
}

export interface ApiError {
  detail: string
}
