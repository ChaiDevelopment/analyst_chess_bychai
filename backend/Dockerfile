FROM python:3.12-slim

# Stockfish is packaged in Debian/Ubuntu's repos, so we can install it
# directly instead of building from source.
RUN apt-get update \
    && apt-get install -y --no-install-recommends stockfish \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV STOCKFISH_PATH=/usr/games/stockfish
ENV ANALYSIS_DEPTH=16
ENV MAX_PLIES=300

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
