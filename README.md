# 🥗 Calivora AI Food Analyzer

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-95%20passed-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Calivora AI Food Analyzer** is an end-to-end nutritional analysis platform that combines state-of-the-art Vision-Language Models (VLMs), USDA FoodData Central integration, and a production-grade Software Engineering (SE) layer.

Users upload a photo of any meal (JPEG/PNG). The system identifies ingredients with estimated portions, retrieves nutritional facts in parallel, calculates comprehensive macronutrient and caloric totals, logs analysis history into PostgreSQL, and surfaces the results via an asynchronous **HTTP REST API** and a **Command-Line Interface (CLI)**.

---

## 🏛️ System Architecture

The application is structured into two strict architectural zones: an **immutable AI foundation core** and a **robust Software Engineering orchestration layer**.

```
                           +-------------------------------------+
                           |            Client Layer             |
                           |    (FastAPI HTTP / CLI Terminal)    |
                           +------------------+------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |      Input Validation & Safety      |
                           | (MIME, Max Size, Pillow byte check) |
                           +------------------+------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |    Core Analyzer Orchestration      |
                           |         (src/core/analyzer.py)      |
                           +--------+-------------------+--------+
                                    |                   |
            +-----------------------+                   +-----------------------+
            v                                                                   v
+-----------------------+                                           +-----------------------+
|  VLM Identification   |                                           |  Parallel Nutrition   |
| (Anthropic / OpenAI / |                                           |        Pipeline       |
|    Gemini / Offline)  |                                           |  (asyncio.Semaphore)  |
+-----------+-----------+                                           +-----------+-----------+
            |                                                                   |
            v                                                                   v
+-----------------------+                                           +-----------------------+
| Exponential Backoff   |                                           |  Thread-Safe In-Memory|
|     Retry Layer       |                                           |       TTL Cache       |
| (tenacity decorator)  |                                           |   (24h default TTL)   |
+-----------------------+                                           +-----------+-----------+
                                                                                |
                                                                                v
                                                                    +-----------------------+
                                                                    |  USDA FoodData Central|
                                                                    |    REST API Client    |
                                                                    +-----------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |    Nutrition Totals Calculation     |
                           |   (kcal, protein, carbs, fat sums)  |
                           +------------------+------------------+
                                              |
                                              v
                           +-------------------------------------+
                           |       PostgreSQL Persistence        |
                           | (asyncpg connection pool & history) |
                           +-------------------------------------+
```

---

## ✨ Core Features

- **Multi-Provider Vision AI:** Supports Anthropic Claude (`claude-sonnet-4-6`), OpenAI (`gpt-4o-mini`), and Google Gemini via a unified VLM adapter interface, plus a zero-dependency offline mock mode.
- **Parallel Nutrition Lookup:** Concurrently queries nutritional databases for $N$ identified ingredients using `asyncio.Semaphore(10)` to maximize throughput while honoring API rate limits.
- **Thread-Safe In-Memory TTL Cache:** Caches nutritional lookups with key normalization (case-insensitive, whitespace-trimmed) to prevent redundant USDA API calls.
- **Resilience & Fault Tolerance:** Automatic exponential backoff retries via `tenacity` on transient network and provider failures; structured graceful fallback for unrecognized meals.
- **Strict Image Validation:** Validates MIME headers, verifies actual image bitstreams via Pillow to prevent corrupted uploads, and enforces size thresholds (default $\le$ 5MB).
- **Asynchronous Database History:** Persists analysis records, individual ingredients with confidence scores, and macronutrient breakdowns to PostgreSQL via `asyncpg`.
- **Dual Client Interfaces:**
  - High-performance asynchronous **FastAPI** web service with OpenAPI/Swagger documentation.
  - Interactive **CLI** utility (`python -m foodanalyzer`) with formatted ASCII summary tables and history inspection.
- **Extensive Test Coverage:** 95 automated offline unit and integration tests achieving **95% code coverage**.

---

## 📂 Repository Structure

```
Calivora-food-analyzer/
├── ai/                              # IMMUTABLE AI MODULE (Contract: do not edit)
│   ├── calculator.py                # Pure totals summation logic
│   ├── nutrition.py                 # NutritionProvider ABC and USDA client
│   ├── schemas.py                   # Ingredient, NutritionFacts, Nutrition models
│   ├── vlm.py                       # VLM prompt formatting and invocation
│   └── providers/                   # Anthropic, OpenAI, Gemini adapters
├── src/                             # SOFTWARE ENGINEERING LAYER
│   ├── api.py                       # FastAPI HTTP REST endpoints
│   ├── cli.py                       # Terminal CLI interface and table renderer
│   ├── config.py                    # Pydantic Settings and env loader
│   ├── logging_config.py            # Centralized logging configuration
│   ├── models.py                    # AnalysisResponse and AnalysisRecord models
│   ├── concurrency/
│   │   └── pipeline.py              # Bounded parallel asyncio nutrition lookup
│   ├── core/
│   │   └── analyzer.py              # Business logic orchestrator
│   ├── services/
│   │   ├── ai_service.py            # Tenacity retry and logging wrappers
│   │   └── nutrition_cache.py       # Thread-safe TTL cache wrapper
│   ├── storage/
│   │   └── repository.py            # Asyncpg PostgreSQL persistence
│   └── utils/
│       └── images.py                # Image type, size, and integrity validator
├── foodanalyzer/
│   └── __main__.py                  # CLI entrypoint (python -m foodanalyzer)
├── tests/                           # 95 UNIT, INTEGRATION & SMOKE TESTS
│   ├── conftest.py                  # Pytest fixtures (FakeVLM, FakeNutrition)
│   ├── test_ai_smoke.py             # 26 offline base smoke tests
│   ├── test_analyzer.py             # Analyzer orchestration and edge cases
│   ├── test_api.py                  # FastAPI HTTP endpoint tests
│   ├── test_cache.py                # TTL cache and thread safety tests
│   ├── test_cli.py                  # CLI commands and rendering tests
│   ├── test_concurrency.py          # Parallel lookup and error pipeline tests
│   ├── test_config.py               # Pydantic settings and env override tests
│   ├── test_logging.py              # Logging level and formatting tests
│   ├── test_repository.py           # PostgreSQL repository mock tests
│   ├── test_src_repository.py       # Repository SQL execution tests
│   └── test_validation.py           # Image format and corruption tests
├── data/                            # 16 synthetic PNG test meal images
├── Dockerfile                       # Production container definition
├── docker-compose.yml               # Multi-container app + db stack
├── requirements.txt                 # Complete project dependencies
├── requirements-ai.txt              # Immutable AI base requirements
└── .env.example                     # Sample environment configuration
```

---

## 📋 Prerequisites

- **Python:** Version 3.11 or higher.
- **PostgreSQL:** Version 15 or 16 (or Docker to run PostgreSQL).
- **API Keys (Optional for local testing / offline demo):**
  - **USDA FoodData Central:** Free key from [api.data.gov](https://fdc.nal.usda.gov/api-key-signup).
  - **LLM Provider:** Anthropic, OpenAI, or Google Gemini API key.

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/MahdiTaghizada/Calivora-food-analyzer.git
cd Calivora-food-analyzer
```

### 2. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your environment settings as needed:

| Variable | Type | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | string | `anthropic` | Chosen VLM provider (`anthropic`, `openai`, `gemini`). |
| `LLM_MODEL` | string | `claude-sonnet-4-6` | VLM model identifier. |
| `ANTHROPIC_API_KEY` | string | `""` | API key for Anthropic Claude. |
| `OPENAI_API_KEY` | string | `""` | API key for OpenAI GPT. |
| `GOOGLE_API_KEY` | string | `""` | API key for Google Gemini. |
| `NUTRITION_PROVIDER` | string | `usda` | Nutrition provider adapter (`usda`). |
| `USDA_API_KEY` | string | `""` | API key from USDA FoodData Central. |
| `LOG_LEVEL` | string | `INFO` | Application log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `DATABASE_URL` | string | `postgresql+asyncpg://foodanalyzer:dev@localhost:5432/foodanalyzer` | PostgreSQL connection URI. |
| `NUTRITION_CACHE_TTL_SECONDS` | integer | `86400` | TTL in seconds for nutrition cache entries (default: 24h). |
| `CACHE_BACKEND` | string | `memory` | Cache implementation: `memory` for a process-local cache or `redis` for a shared Redis cache. |
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis connection URI used when `CACHE_BACKEND=redis`. |
| `MAX_IMAGE_SIZE_MB` | integer | `5` | Maximum allowable upload file size in megabytes. |
| `HTTP_PORT` | integer | `8000` | HTTP port for FastAPI server. |
| `MAX_NUTRITION_CONCURRENCY` | integer | `10` | Maximum concurrent USDA lookup queries. |
| `RETRY_ATTEMPTS` | integer | `3` | Maximum retry attempts for transient errors. |
| `RETRY_MIN_WAIT_SECONDS` | float | `1.0` | Initial exponential backoff wait time in seconds. |
| `RETRY_MAX_WAIT_SECONDS` | float | `10.0` | Maximum exponential backoff cap in seconds. |

The Docker Compose stack includes Redis 7 and configures the application to use
it automatically. For local non-container runs, use `CACHE_BACKEND=memory` or
start Redis separately before selecting `CACHE_BACKEND=redis`.

---

## 🗄️ Database Setup

### Option A: Using Docker Compose (Recommended)

Start an isolated PostgreSQL instance in the background:

```bash
docker compose up -d db
```

### Option B: Using Standalone Docker

```bash
docker run -d \
  --name foodanalyzer-postgres \
  -e POSTGRES_USER=foodanalyzer \
  -e POSTGRES_PASSWORD=dev \
  -e POSTGRES_DB=foodanalyzer \
  -p 5432:5432 \
  postgres:16-alpine
```

The database schema and tables (`analysis_history`) are **automatically created** upon initial connection by `src/storage/repository.py`.

---

## 🌐 HTTP REST API (FastAPI)

### Starting the Server

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### API Endpoints

#### 1. Health Check
- **Route:** `GET /health`
- **Description:** Basic liveness probe.

```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok"
}
```

#### 2. Meal Analysis
- **Route:** `POST /analyze`
- **Content-Type:** `multipart/form-data`
- **Field:** `image` (file binary)

```bash
curl -X POST http://localhost:8000/analyze \
  -F "image=@data/rice_chicken_broccoli.png"
```

**Successful Response (200 OK):**
```json
{
  "image_name": "rice_chicken_broccoli.png",
  "meal_recognized": true,
  "status": "completed",
  "ingredients": [
    {
      "ingredient": {
        "name": "white rice (cooked)",
        "estimated_grams": 180.0,
        "confidence": 0.95
      },
      "nutrition": {
        "kcal": 234.0,
        "protein_g": 4.9,
        "carbs_g": 50.4,
        "fat_g": 0.5
      },
      "nutrition_source": "usda",
      "error": null
    },
    {
      "ingredient": {
        "name": "grilled chicken breast",
        "estimated_grams": 150.0,
        "confidence": 0.92
      },
      "nutrition": {
        "kcal": 248.0,
        "protein_g": 46.5,
        "carbs_g": 0.0,
        "fat_g": 5.4
      },
      "nutrition_source": "usda",
      "error": null
    },
    {
      "ingredient": {
        "name": "broccoli",
        "estimated_grams": 80.0,
        "confidence": 0.88
      },
      "nutrition": {
        "kcal": 27.0,
        "protein_g": 2.2,
        "carbs_g": 5.6,
        "fat_g": 0.3
      },
      "nutrition_source": "usda",
      "error": null
    }
  ],
  "totals": {
    "kcal": 509.0,
    "protein_g": 53.6,
    "carbs_g": 56.0,
    "fat_g": 6.3
  },
  "warnings": [],
  "timestamp": "2026-09-19T12:00:00Z"
}
```

#### 3. Unrecognized Meal Response
When the uploaded image contains no detectable food (e.g. `data/no_meal_blue.png`), the system gracefully responds without crashing:

```json
{
  "image_name": "no_meal_blue.png",
  "meal_recognized": false,
  "status": "unknown_meal",
  "ingredients": [],
  "totals": {
    "kcal": 0.0,
    "protein_g": 0.0,
    "carbs_g": 0.0,
    "fat_g": 0.0
  },
  "warnings": [],
  "timestamp": "2026-09-19T12:00:00Z"
}
```

#### 4. API Error Handling

| HTTP Code | Condition | Response Body |
|---|---|---|
| `400 Bad Request` | Empty file or corrupt image data | `{"detail": "Image file is empty"}` |
| `413 Payload Too Large` | Image exceeds `MAX_IMAGE_SIZE_MB` | `{"detail": "Image exceeds the 5 MB size limit"}` |
| `415 Unsupported Media Type`| Non-JPEG/PNG format | `{"detail": "Only JPEG and PNG images are supported"}` |
| `503 Service Unavailable` | VLM or external provider outage | `{"detail": "AI provider temporarily unavailable"}` |

---

## 💻 CLI Interface (`foodanalyzer`)

The application provides a command-line interface under the `foodanalyzer` module:

### 1. Analyze Meal Image

```bash
python -m foodanalyzer analyze data/rice_chicken_broccoli.png
```

**Output:**
```
ingredient              g    kcal  protein  carbs  fat
------------------------------------------------------
white rice (cooked)     180  234   4.9      50.4   0.5
grilled chicken breast  150  248   46.5     0.0    5.4
broccoli                80   27    2.2      5.6    0.3
------------------------------------------------------
TOTAL                   410  509   53.6     56.0   6.3
```

### 2. View Analysis History

```bash
python -m foodanalyzer history
```

**Output:**
```
1 | data/rice_chicken_broccoli.png | 2026-09-19 12:05:32.418291+00
2 | data/bread_cheese.png          | 2026-09-19 12:14:10.129482+00
```

---

## ⚡ Concurrency & Caching Performance

### Bounded Parallelism (`asyncio.Semaphore`)
When the VLM identifies $N$ ingredients in a dish, retrieving nutritional values sequentially takes $O(N \cdot T)$ time, where $T$ is network latency to the USDA API ($\approx 250$ms per request).

Using `src/concurrency/pipeline.py`:
- All $N$ lookups execute concurrently via `asyncio.gather`.
- Concurrency is bounded by an `asyncio.Semaphore(10)` to protect the USDA free-tier rate limits (1000 req/hour).
- For a typical meal with 5 ingredients, wall-clock latency drops from **~1250ms to ~260ms** (approx. **5x speedup**).

### Thread-Safe In-Memory TTL Cache
`src/services/nutrition_cache.py` caches all ingredient lookups:
- Thread synchronization via `threading.RLock`.
- Normalizes query strings (`"  White  RICE "` $\rightarrow$ `"white rice"`).
- Evicts expired records when elapsed time exceeds `NUTRITION_CACHE_TTL_SECONDS` (24h).
- Subsequent analyses containing common ingredients (e.g. rice, chicken, eggs) achieve instant **0ms cache hits**.

---

## 🧪 Running Tests & Code Coverage

The test suite includes 95 automated offline tests with **zero network dependencies**:

### Run All Tests

```bash
pytest -v
```

### Run Tests with Coverage Report

```bash
pytest --cov=src --cov-report=term-missing
```

**Coverage Summary:**
```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
src\__init__.py                       0      0   100%
src\api.py                           35      0   100%
src\cli.py                           97      4    96%   140-143
src\concurrency\pipeline.py          25      0   100%
src\config.py                        24      0   100%
src\core\analyzer.py                 64      0   100%
src\logging_config.py                 7      0   100%
src\models.py                        26      0   100%
src\services\ai_service.py           22      0   100%
src\services\nutrition_cache.py      35      0   100%
src\storage\repository.py            82     19    77%   24, 48-50, 92-94...
src\utils\images.py                  42      0   100%
---------------------------------------------------------------
TOTAL                               459     23    95%
```

### Run Provided Smoke Tests

```bash
pytest tests/test_ai_smoke.py -v
```

---

## 🐳 Docker Deployment

### Run Entire Stack (App + Database)

Build and run both the web API and PostgreSQL database using Docker Compose:

```bash
docker compose up --build
```

The application will be accessible at `http://localhost:8000`.

### Build & Run Container Independently

```bash
docker build -t calivora-foodanalyzer .
docker run -p 8000:8000 --env-file .env calivora-foodanalyzer
```

---

## 🔒 Contract Compliance

As stipulated in the project specification:
1. **The `ai/` module is strictly immutable:** No files under `ai/` are modified. All custom engineering is layered in `src/`.
2. **Provider interfaces:** Business logic interacts solely with `ai.identify_ingredients`, `ai.compute_totals`, and `ai.NutritionProvider`.
3. **Smoke test integrity:** All 26 provided baseline smoke tests in `tests/test_ai_smoke.py` remain unmodified and passing.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
