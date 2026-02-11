# n8n RSS Pipeline + FastAPI WordCloud

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.116-009688?logo=fastapi&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white">
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white">
  <img alt="n8n" src="https://img.shields.io/badge/n8n-Queue%20Mode-EA4B71">
</p>

---

## Overview

This project provides an integrated setup for the following pipeline:

1. Collect RSS articles in n8n and store them in the database  
2. Send keyword aggregation results to FastAPI  
3. Generate period-based word cloud images (`wordcloud_output/`)

---

## Project Structure

```text
.
├─ app.py                         # FastAPI server (POST /wordclouds/generate)
├─ requirements.txt               # Dependencies for API/WordCloud/RSS parser
├─ docker-compose-api.yml         # FastAPI container
├─ docker-compose-n8n.yml         # n8n + postgres + redis
├─ docker-compose-db.yml          # Separate DB + Flyway migrate
├─ deploy_image.sh                # Service-based redeploy script
├─ migrate_db.sh                  # Run Flyway migrations
├─ db/migration/                  # SQL migrations
└─ wordcloud_output/              # Output folder for generated images
```

---

## Services

| Service | Compose File | Port | Description |
|---|---|---:|---|
| FastAPI | `docker-compose-api.yml` | `8100` | Word cloud generation API |
| n8n Main | `docker-compose-n8n.yml` | `5678` | Workflow execution/UI |
| n8n DB (internal) | `docker-compose-n8n.yml` | - | Internal Postgres for n8n |
| DB + Flyway | `docker-compose-db.yml` | `5432` | Separate Postgres + migration |

---

## Environment Variables

Create a `.env` file in the project root with values like the following:

```env
N8N_ENCRYPTION_KEY=your_random_secret_key

# docker-compose-db.yml
N8N_DB_NAME=n8n_db
N8N_DB_USER=your_db_user
N8N_DB_PASSWORD=your_db_password

# docker-compose-n8n.yml (internal n8n postgres)
N8N_POSTGRES_DB=n8n
N8N_POSTGRES_USER=n8n
N8N_POSTGRES_PASSWORD=n8n
```

Make sure this file is not committed to Git.

---

## Quick Start

### 0) Download Korean Font (Required for WordCloud)

Download a Korean font from the official link below and place it in the project root:

- `http://font.woowahan.com/dohyeon/`

Example expected file:

- `BMDOHYEON_ttf.ttf`

### 1) Start FastAPI

```bash
docker compose -f docker-compose-api.yml up -d
```

### 2) Start n8n

```bash
docker compose -f docker-compose-n8n.yml up -d
```

### 3) Run DB migrations

```bash
bash migrate_db.sh
```

### 4) Redeploy by service

```bash
bash deploy_image.sh api
bash deploy_image.sh n8n
bash deploy_image.sh db
```

---

## API Spec

### Endpoint

`POST /wordclouds/generate`

### Request Body

Send the payload as a root-level JSON array.

```json
[
  {
    "period": "3day",
    "frequencies": {
      "메타 AI": 1,
      "아보카도(Avocado)": 1
    }
  },
  {
    "period": "7day",
    "frequencies": {
      "시리(Siri)": 1,
      "제미나이": 1
    }
  },
  {
    "period": "1month",
    "frequencies": {
      "GPT-5.3-코덱스": 1,
      "xAI": 1
    }
  }
]
```

### Behavior

- Generates word clouds by `period`
- Output paths:
  - `wordcloud_output/3days_wordcloud.png`
  - `wordcloud_output/7days_wordcloud.png`
  - `wordcloud_output/1month_wordcloud.png`

---

## n8n HTTP Request Node Tips

- API URL (Docker-based n8n -> host API):
  - `http://host.docker.internal:8100/wordclouds/generate`
- The request body must be sent as a **raw JSON array**.
- Example expression:

```text
{{ $items("Code").map(i => i.json) }}
```

---

## Database Notes

- Migration files are managed in `db/migration/` with sequential versions (`V1__...sql`).
- `schedule_logs` is used to store the latest execution time by service.
- `rss_article_keyword` is used to store keyword rows.

---

## Requirements

`requirements.txt` keeps only minimal direct dependencies used by the current codebase.

- FastAPI / Pydantic
- Uvicorn
- WordCloud
- Feedparser

---

## Git Ignore Policy

- Keep the `wordcloud_output/` folder tracked
- Ignore only these generated files:
  - `wordcloud_output/3days_wordcloud.png`
  - `wordcloud_output/7days_wordcloud.png`
  - `wordcloud_output/1month_wordcloud.png`
