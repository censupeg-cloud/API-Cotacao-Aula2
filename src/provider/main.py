import os, time, random
from fastapi import FastAPI, HTTPException, Query

APP_NAME = "provider"
# controla falhas/latência para simular mundo real
FAIL_PROB = float(os.getenv("FAIL_PROB", "0.25"))         # 25% falha
MIN_DELAY_MS = int(os.getenv("MIN_DELAY_MS", "50"))       # 50ms
MAX_DELAY_MS = int(os.getenv("MAX_DELAY_MS", "400"))      # 400ms
FORCE_FAIL = os.getenv("FORCE_FAIL", "0") == "1"

BASE_USD = float(os.getenv("BASE_USD", "5.00"))           # base da cotação

app = FastAPI(title="Provider Simulado", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}

@app.get("/cotacao")
def cotacao(moeda: str = Query("USD", min_length=3, max_length=5)):
    # Simula latência variável
    delay_ms = random.randint(MIN_DELAY_MS, MAX_DELAY_MS)
    time.sleep(delay_ms / 1000.0)

    # Simula falha
    if FORCE_FAIL or random.random() < FAIL_PROB:
        raise HTTPException(status_code=503, detail="Serviço temporariamente indisponível")

    moeda = moeda.upper()
    base = BASE_USD if moeda == "USD" else BASE_USD * 0.2  # exemplo bobo para outras moedas
    # Variação leve para parecer “real”
    valor = round(base * random.uniform(0.98, 1.02), 4)
    return {"moeda": moeda, "cotacao": valor, "fonte": "provider", "latencia_ms": delay_ms}
