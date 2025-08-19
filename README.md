# aula2-api

## Descrição

Este projeto é uma API de cotação de moedas com dois serviços principais: um provedor simulado e uma API de cotação. O provedor simula um serviço externo com latência e falhas, enquanto a API de cotação consome esses dados, implementa cache com Redis e possui mecanismos de retry e fallback.

## Estrutura do Projeto

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

## Componentes

### API de Cotação (`src/api/main.py`)

- **Endpoint**: `/cotacao`
  - Parâmetros:
    - `moeda`: Código da moeda (padrão: "USD")
    - `nocache`: Ignora cache se verdadeiro
- **Funcionalidades**:
  - Cache com Redis
  - Retry com backoff exponencial
  - Fallback para cache "stale" ou valor padrão

### Provedor Simulado (`src/provider/main.py`)

- **Endpoint**: `/cotacao`
  - Parâmetros:
    - `moeda`: Código da moeda (padrão: "USD")
- **Funcionalidades**:
  - Simula latência variável
  - Simula falhas aleatórias
  - Retorna cotação simulada

## Configuração

### Variáveis de Ambiente

#### API de Cotação
- `REDIS_HOST`: Host do Redis (padrão: "redis")
- `REDIS_PORT`: Porta do Redis (padrão: 6379)
- `PROVIDER_URL`: URL do provedor (padrão: "http://provider:9000/cotacao")
- `CACHE_TTL_SECONDS`: Tempo de vida do cache em segundos (padrão: 60)
- `RETRY_ATTEMPTS`: Número de tentativas de retry (padrão: 3)
- `RETRY_BASE_SECONDS`: Base do backoff exponencial (padrão: 0.2)
- `FALLBACK_VALUE`: Valor de fallback (padrão: 5.00)

#### Provedor Simulado
- `FAIL_PROB`: Probabilidade de falha (padrão: 0.25)
- `MIN_DELAY_MS`: Latência mínima em milissegundos (padrão: 50)
- `MAX_DELAY_MS`: Latência máxima em milissegundos (padrão: 400)
- `FORCE_FAIL`: Força falha se verdadeiro (padrão: 0)
- `BASE_USD`: Valor base para USD (padrão: 5.00)

### Arquivo `.env`

Para facilitar a configuração, você pode criar um arquivo `.env` na raiz do projeto com as variáveis de ambiente desejadas. Um exemplo de arquivo `.env` está disponível em `.env.example`.

### Docker Compose

O projeto utiliza Docker Compose para orquestrar os serviços. O arquivo `docker-compose.yml` define os serviços `api`, `provider` e `redis`.

## Como Executar

1. **Pré-requisitos**:
   - Docker
   - Docker Compose

2. **Passos**:
   ```bash
   docker-compose up --build
   ```

3. **Acessar**:
   - API de Cotação: `http://localhost:8000`
   - Provedor Simulado: `http://localhost:9000`

## Endpoints

### API de Cotação

- **GET /cotacao**: Retorna a cotação da moeda especificada.
  - Exemplo: `http://localhost:8000/cotacao?moeda=USD`

- **GET /health**: Verifica a saúde do serviço.
  - Exemplo: `http://localhost:8000/health`

### Provedor Simulado

- **GET /cotacao**: Retorna a cotação simulada da moeda especificada.
  - Exemplo: `http://localhost:9000/cotacao?moeda=USD`

- **GET /health**: Verifica a saúde do serviço.
  - Exemplo: `http://localhost:9000/health`

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
