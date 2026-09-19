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
| `MAX_IMAGE_SIZE_MB` | integer | `5` | Maximum allowable upload file size in megabytes. |
| `HTTP_PORT` | integer | `8000` | HTTP port for FastAPI server. |
| `MAX_NUTRITION_CONCURRENCY` | integer | `10` | Maximum concurrent USDA lookup queries. |
| `RETRY_ATTEMPTS` | integer | `3` | Maximum retry attempts for transient errors. |
| `RETRY_MIN_WAIT_SECONDS` | float | `1.0` | Initial exponential backoff wait time in seconds. |
| `RETRY_MAX_WAIT_SECONDS` | float | `10.0` | Maximum exponential backoff cap in seconds. |

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
