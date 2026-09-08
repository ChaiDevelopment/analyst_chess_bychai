# Chess Review

A free, local-first chess game analysis app — paste a PGN and get a
move-by-move review with evaluations, best moves, classifications
(Brilliant / Best / Excellent / Good / Book / Inaccuracy / Mistake /
Blunder), tactical tags, and a game summary with accuracy scores.

It's inspired by chess.com's Game Review, but every core feature runs
locally and free, on your own machine, powered by the open-source
**Stockfish** engine. No account, no database, no paid API required.

## 1. Requirements

- Python 3.10+
- Node.js 18+
- [Stockfish](https://stockfishchess.org/download/) installed and on your
  PATH (or a known path you set in `.env`)
- (Optional) an OpenAI API key, only if you want AI-written explanations
  instead of the built-in template explanations

## 2. Install Stockfish

- **macOS**: `brew install stockfish`
- **Ubuntu/Debian**: `sudo apt-get install stockfish`
- **Windows**: download a binary from
  [stockfishchess.org/download](https://stockfishchess.org/download/) and
  note the path to `stockfish.exe`
- **Docker**: handled automatically — see [Docker](#7-docker) below.

Verify it works:

```bash
stockfish
# type "uci" and press enter - it should print engine info, then "uciok"
# Ctrl+C to exit
```

## 3. Backend setup

macOS/Linux:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8010
```

Windows PowerShell:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8010
```

The API is now running at `http://localhost:8010` (interactive docs at
`http://localhost:8010/docs`).

## 4. Frontend setup

In a separate terminal:

```bash
cd frontend
npm ci
# macOS/Linux: cp .env.example .env
# Windows PowerShell: Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`. In development, Vite proxies `/api/*`
requests to `http://localhost:8010` (configured in `vite.config.ts`), so
you don't need to configure CORS by hand.

## 5. Environment variables

**Backend (`backend/.env`)**

| Variable          | Default                  | Notes                                                              |
|-------------------|---------------------------|----------------------------------------------------------------------|
| `OPENAI_API_KEY`  | *(empty)*                 | Optional. If unset, explanations fall back to a built-in template.  |
| `STOCKFISH_PATH`  | *(auto-detected)*         | Set this if Stockfish isn't found automatically.                    |
| `ANALYSIS_DEPTH`  | `16`                      | Higher = stronger & slower analysis. Lower it on slower machines.   |
| `MAX_PLIES`       | `300`                     | Upper bound on game length accepted per request.                    |
| `CORS_ORIGINS`    | `http://localhost:5173,...` | Comma-separated list of allowed frontend origins.                 |

**Frontend (`frontend/.env`)**

| Variable       | Default | Notes                                                            |
|----------------|---------|-------------------------------------------------------------------|
| `VITE_API_URL` | `/api`  | Set to a full URL if the frontend and backend are hosted separately. |

## 6. Running locally (quick reference)

```bash
# Terminal 1
cd backend && uvicorn app.main:app --reload --port 8010

# Terminal 2
cd frontend && npm run dev
```

Then open `http://localhost:5173`, paste a PGN (or click **Try Example
Game**), and click **Analyze Game**.

## 7. Docker

Runs the whole stack (backend + Stockfish + frontend) in containers:

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

Set `OPENAI_API_KEY` in your shell (or a `.env` file next to
`docker-compose.yml`) before running `docker compose up` if you want AI
explanations enabled.

The frontend waits for the backend health check before it starts. The Nginx
proxy allows up to six minutes for a deeper Stockfish review to finish.

## Railway backend + Vercel frontend deployment

The Vercel browser app calls the Railway API directly. A Railway private domain
(`*.railway.internal`) works only between Railway services, so it must **not**
be used as `VITE_API_URL`.

1. In Railway, open the **backend** service and create/copy its public domain,
   e.g. `https://caturchaibackend.com`. Confirm that opening
   `https://caturchaibackend.com/api/health` returns JSON. Railway's target
   port may be `8080`, but a custom public domain normally uses HTTPS port 443;
   do not append `:8080` to the browser URL unless you deliberately exposed
   that non-standard public port.
2. In Railway **Variables**, set `CORS_ORIGINS` to the exact Vercel production
   origin, without `/api` or a trailing slash, e.g.
   `https://your-project.vercel.app`. Redeploy the backend after saving it.
3. In Vercel, open the **frontend** project > **Settings** > **Environment
   Variables**. Add this for the Production environment (and Preview too if
   required):

   ```text
   VITE_API_URL=https://caturchaibackend.com/api
   ```

4. Redeploy the Vercel project. Vite inserts `VITE_*` values at build time, so
   changing the variable without a new deployment does not update the live app.

The code markers in `frontend/src/services/api.ts`, `frontend/.env.example`,
and `backend/.env.example` identify these two settings. Do not put API keys in
`VITE_*` variables: they are exposed to every browser.

## 8. API usage

### `POST /api/analyze`

```json
{ "pgn": "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 ...", "depth": 16 }
```

Returns `{ game, moves, summary, ai_explanations_enabled, engine_depth }`.
Each entry in `moves` includes `san`, `uci`, `fen_before`/`fen_after`,
`evaluation_before`/`evaluation_after` (pawns, White's perspective),
`best_move`, `centipawn_loss`, `classification`, `tactical_tags`,
`variation`, and an optional `explanation`.

### `GET /api/health`

```json
{ "status": "ok", "engine_available": true, "ai_explanations_enabled": false }
```

For local development, full interactive docs (OpenAPI/Swagger) are available
at `http://localhost:8010/docs` while the backend is running.

## 9. How analysis works

```
PGN
 └─ python-chess parses & validates moves
     └─ Stockfish evaluates the position before and after every move
         └─ centipawn loss = eval_before(mover) − eval_after(mover)
             └─ classification engine combines CPL + book status +
                tactical signals (sacrifice, hanging piece, etc.)
                 └─ optional OpenAI call turns the engine data into a
                    short, human explanation (only for noteworthy moves)
                     └─ accuracy = f(average CPL), summary aggregated
```

Stockfish runs as a single reusable engine process per analysis request
(not spawned per move), evaluating each position once at the configured
depth. All chess decisions — best move, evaluation, classification,
accuracy — come from Stockfish and the classification engine. **OpenAI is
never consulted for chess decisions**, only for phrasing an explanation of
a decision the engine already made. If `OPENAI_API_KEY` is unset, or the
OpenAI call fails for any reason, the app automatically falls back to a
template explanation and continues to work fully.

## 10. Limitations

- **Classification is a heuristic MVP**, not a claim to reproduce
  chess.com's (undisclosed, proprietary) classifier. In particular, the
  "Brilliant" detector is a simple sacrifice+evaluation heuristic and will
  sometimes disagree with other tools.
- **Accuracy formula** is a simple, isolated function
  (`backend/app/services/accuracy.py`) mapping average centipawn loss to a
  0–100 score. It is not claimed to match any specific product's formula.
- **Opening detection** uses a small local ECO book (~40 lines covering
  common openings). Anything outside it shows "Opening detection coming
  soon" rather than guessing.
- **No accounts, database, multiplayer, or online-game import** — this is
  intentionally scoped to PGN → Analyze → Review for the MVP (see
  `MVP LIMITATIONS` in the project brief).
- The `/api/analyze` endpoint is synchronous; the frontend shows a
  simulated progress readout while it waits. For very long games this
  means one long-running HTTP request rather than incremental streaming.

## Project structure

```
chess-review/
├── frontend/          React + Vite + TypeScript + Tailwind + chess.js + react-chessboard
├── backend/            FastAPI + python-chess + Stockfish
│   └── app/
│       ├── api/        HTTP routes
│       ├── chess/       PGN parsing, classification, opening book
│       ├── engine/     Stockfish process wrapper
│       ├── services/    Analysis pipeline, accuracy, AI explanations
│       └── models/      Pydantic schemas
├── docker-compose.yml
└── README.md
```

## Testing

```bash
# Backend
cd backend && python -m pytest -q

# Frontend
cd frontend && npm run test && npm run lint && npm run build
```
# analyst_chess_bychai
