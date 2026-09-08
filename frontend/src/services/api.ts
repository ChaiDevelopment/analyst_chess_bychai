import type { AnalyzeResponse } from '../types/chess'

// On Vercel, VITE_API_URL is baked in during the build. Set it to the PUBLIC
// Railway URL plus /api; a *.railway.internal host only works inside Railway.
const BASE_URL = (import.meta.env.VITE_API_URL ?? '/api').replace(/\/$/, '')
const REQUEST_TIMEOUT_MS = 5 * 60 * 1000

export class ApiRequestError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function analyzeGame(pgn: string, depth?: number): Promise<AnalyzeResponse> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  let res: Response
  try {
    res = await fetch(`${BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pgn, depth }),
      signal: controller.signal,
    })
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiRequestError('Analysis timed out. Try a shorter game or lower the engine depth.', 408)
    }
    throw new ApiRequestError('Cannot reach the API. Make sure the backend is running.', 0)
  } finally {
    window.clearTimeout(timeout)
  }

  if (!res.ok) {
    let message = `Request failed with status ${res.status}`
    try {
      const body = await res.json()
      if (body?.detail) message = body.detail
    } catch {
      // ignore parse failure, keep default message
    }
    if (res.status >= 500 && message === `Request failed with status ${res.status}`) {
      message = 'Backend tidak dapat dihubungi. Periksa VITE_API_URL (Vercel) dan CORS_ORIGINS (Railway), lalu coba lagi.'
    }
    throw new ApiRequestError(message, res.status)
  }

  return res.json()
}

export async function checkHealth(): Promise<{
  status: string
  engine_available: boolean
  ai_explanations_enabled: boolean
} | null> {
  try {
    const res = await fetch(`${BASE_URL}/health`)
    if (!res.ok) return null
    return await res.json()
  } catch {
    return null
  }
}
