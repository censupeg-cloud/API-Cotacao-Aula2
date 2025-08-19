import os, time, random, json
from typing import Optional
import requests
from fastapi import FastAPI, HTTPException, Query
from redis import Redis

APP_NAME = "api"
PROVIDER_URL = os.getenv("PROVIDER_URL", "http://provider:9000/cotacao")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "60"))

# retry/backoff
RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
RETRY_BASE = float(os.getenv("RETRY_BASE_SECONDS", "0.2"))  # 0.2, 0.4, 0.8...

app = FastAPI(title="API de Cotação", version="1.0.0")
rds: Optional[Redis] = None

@app.on_event("startup")
def _startup():
    global rds
    rds = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    app.logger = print  # simplão: usa print como logger

@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME}

def _cache_key(moeda: str) -> str:
    return f"cotacao:{moeda.upper()}"

def get_from_cache(moeda: str) -> Optional[dict]:
    data = rds.get(_cache_key(moeda))
    return json.loads(data) if data else None

def set_cache(moeda: str, payload: dict):
    rds.setex(_cache_key(moeda), CACHE_TTL, json.dumps(payload))

def fetch_from_provider(moeda: str, timeout: float = 1.2) -> dict:
    url = f"{PROVIDER_URL}?moeda={moeda}"
    last_exc = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_exc = e
            # backoff exponencial + jitter
            delay = (RETRY_BASE * (2 ** attempt)) + random.random() * 0.05
            app.logger(f"[retry] tentativa {attempt+1}/{RETRY_ATTEMPTS} falhou: {e} – aguardando {delay:.2f}s")
            time.sleep(delay)
    raise last_exc or RuntimeError("Falha desconhecida ao consultar provider")

@app.get("/cotacao")
def cotacao(
    moeda: str = Query("USD", min_length=3, max_length=5),
    nocache: bool = Query(False, description="Ignora cache se true")
):
    moeda = moeda.upper()

    # 1) tenta cache (se não pediram nocache)
    if not nocache:
        cached = get_from_cache(moeda)
        if cached:
            cached["fonte"] = "cache"
            return cached

    # 2) tenta provider com timeout + retry/backoff
    try:
        data = fetch_from_provider(moeda)
        # opcional: validação mínima
        if "cotacao" not in data:
            raise ValueError("Resposta do provider sem campo 'cotacao'")
        # 3) salva em cache e retorna
        set_cache(moeda, data)
        data["fonte"] = "externa"
        return data
    except Exception as e:
        app.logger(f"[fallback] provider indisponível: {e}")

        # 3a) fallback para cache “stale” se houver
        cached = get_from_cache(moeda)
        if cached:
            cached["fonte"] = "stale-cache"
            return cached

        # 3b) último fallback: valor padrão
        fallback_value = float(os.getenv("FALLBACK_VALUE", "5.00"))
        return {"moeda": moeda, "cotacao": fallback_value, "fonte": "fallback"}
