# API de Cotação com Docker e Redis

## Descrição

API de cotação de moedas composta por três serviços:

* **API**: expõe endpoints de consulta e implementa cache, retry, timeout e fallback.
* **Provider (simulado)**: emula um serviço externo com latência variável e falhas controladas.
* **Redis**: armazena cotações em cache com TTL.

Objetivo: demonstrar, de ponta a ponta, containerização, padronização de ambiente e resiliência sob falhas controladas.

---

## Arquitetura

```
Host (porta 8000)  ->  api  ->  provider
                         |
                         ->  redis
```

Portas expostas:

* API: 8000
* Provider: 9000
* Redis: 6379

Descoberta de serviços no Compose por nome de serviço: `provider`, `redis`.

---

## Requisitos

* Docker
* Docker Compose (CLI `docker compose`)

---

## Como executar

1. Opcional: copie e ajuste variáveis

   ```bash
   cp .env.example .env
   ```
2. Suba os serviços

   ```bash
   docker compose up -d --build
   ```
3. Verifique saúde

   ```bash
   curl http://localhost:8000/health
   curl http://localhost:9000/health
   ```
4. Faça uma consulta

   ```bash
   curl "http://localhost:8000/cotacao?moeda=USD"
   ```

---

## Endpoints

### API

* `GET /health`
  Verifica a saúde do serviço.
  Exemplo:

  ```
  http://localhost:8000/health
  ```

* `GET /cotacao?moeda=USD&nocache=false`
  Retorna a cotação.
  Possíveis respostas:

  * `fonte: "externa"` quando o provider responde
  * `fonte: "cache"` quando atende a partir do cache recente
  * `fonte: "stale-cache"` quando o provider falha e existe cache antigo
  * `fonte: "fallback"` quando não há cache disponível

### Provider

* `GET /health`

  ```
  http://localhost:9000/health
  ```
* `GET /cotacao?moeda=USD`
  Retorna cotação simulada com latência e falhas controladas.

---

## Variáveis de ambiente

### API

* `REDIS_HOST` padrão `redis`
* `REDIS_PORT` padrão `6379`
* `PROVIDER_URL` padrão `http://provider:9000/cotacao`
* `CACHE_TTL_SECONDS` padrão `60`
* `RETRY_ATTEMPTS` padrão `3`
* `RETRY_BASE_SECONDS` padrão `0.2`
* `FALLBACK_VALUE` padrão `5.00`

### Provider

* `FAIL_PROB` probabilidade de falha. Padrão `0.25`
* `MIN_DELAY_MS` latência mínima. Padrão `50`
* `MAX_DELAY_MS` latência máxima. Padrão `400`
* `FORCE_FAIL` força falha quando `1`. Padrão `0`
* `BASE_USD` valor base. Padrão `5.00`

Use `.env` na raiz do projeto para configurar valores. Consulte `.env.example`.

---

## Estrutura do projeto

```
.
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.provider
├── requirements.txt
├── src/
│   ├── api/
│   │   └── main.py
│   └── provider/
│       └── main.py
└── README.md
```

---

## Fluxo da rota `/cotacao`

1. Verifica cache no Redis quando `nocache=false`.
2. Se não houver cache, chama o provider com timeout e retry com backoff exponencial.
3. Valida e grava resposta no cache com TTL.
4. Em caso de falha no provider, tenta `stale-cache`. Se não houver, retorna `fallback` com valor padrão.

Benefícios:

* Resposta previsível sob falhas.
* Redução de latência e menor acoplamento ao serviço externo.
* Reprodutibilidade entre ambientes.

---

## Healthchecks

Os Dockerfiles da API e do Provider incluem `HEALTHCHECK` que consulta seus respectivos endpoints `/health`.
No Compose, é possível condicionar a inicialização de serviços ao estado de saúde:

```yaml
depends_on:
  provider:
    condition: service_healthy
```

---

## Testes de falha e evidências

Simule falhas para coletar evidências de resiliência.

1. Baseline

   ```bash
   time curl -s -o /dev/null -w "%{http_code} %{time_total}\n" \
     "http://localhost:8000/cotacao?moeda=USD"
   ```

2. Parar o provider

   ```bash
   docker compose stop provider
   curl "http://localhost:8000/cotacao?moeda=USD"   # espera-se stale-cache ou fallback
   docker compose logs -f api                       # observar retries e fallback
   ```

3. Recuperação

   ```bash
   docker compose start provider
   curl "http://localhost:8000/cotacao?moeda=USD"
   ```

Registre:

* Trechos de logs com mensagens de retry e fallback
* Linhas do `curl -w` com código HTTP e tempo de resposta antes, durante e após a falha

---

## Comandos úteis

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f provider
docker compose down
docker compose down -v   # remove volumes. use com cautela
```

---

## Boas práticas

* Use `.dockerignore` para evitar copiar arquivos desnecessários.
* Fixe versões de imagens e dependências. Evite `latest`.
* Garanta que o servidor web escute em `0.0.0.0`.
* Considere usuário não root no container.
* Não versione segredos. Utilize `.env.example` para documentação.
* Avalie inclusão de pipeline de CI para build, testes e scan de vulnerabilidades.

---

## Licença

Apache License 2.0. Consulte o arquivo `LICENSE`.
