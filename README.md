# URL Shortener with Analytics

A **URL Shortener** built with **FastAPI** that allows users to create short URLs, track click analytics, and manage expirations. Includes an asynchronous analytics flow using **RabbitMQ**, caching with **Redis**, and a **PostgreSQL** database for persistence.

## Table of Contents

- [Features](#features)  
- [Architecture](#architecture)  
- [Tech Stack](#tech-stack)  
- [Project Structure](#project-structure)  
- [Installation & Setup](#installation--setup)  
  - [Local Setup (Without Docker)](#local-setup-without-docker)  
  - [Docker Compose Setup](#docker-compose-setup)  
- [API Usage](#api-usage)  
  - [Shorten URL](#1-shorten-url)  
  - [Redirect](#2-redirect)  
  - [Get Analytics](#3-get-analytics)  
- [Worker (Analytics Consumer)](#worker-analytics-consumer)   
- [License](#license)

---

## Features

1. **URL Shortening**  
   - Generate a short code (via hashing or random base62).  
   - (Optional) Support link expiration after 8 days or user-defined expiry.

2. **Redirect Logic**  
   - `GET /{short_code}` will look up the original URL (cached in Redis) and redirect.  
   - Checks if a link is expired (returns 410 Gone if so).

3. **Analytics**  
   - Records each click with IP address, user agent, referrer, and timestamp.  
   - Asynchronous logging to the `analytics` table via RabbitMQ worker.  
   - Endpoints to retrieve aggregated stats or the last N visits.

4. **Caching**  
   - Uses Redis for quick short_code → long_url lookups to reduce DB load.

5. **Expiration**  
   - Simple logic to set `expire_at` in the DB. If `expire_at < now`, link is considered expired.

6. **Docker-Compose**  
   - Launches FastAPI, Worker, PostgreSQL, Redis, and RabbitMQ in one go.

---

## Architecture

```
    ┌──────────────────┐
    │   POST /shorten  │
    └──────────────────┘
             |
┌─────────────────────────────────────────────────────────┐
│                 FastAPI (Web Container)                │
│   - Insert short URL into DB (PostgreSQL) + Redis      │
│   - On redirect, publish analytics to RabbitMQ          │
└─────────────────────────────────────────────────────────┘
             |                         |
             |                         |
             |  Redis Cache (for lookups)
             |                         |
             |                         V
┌─────────────────────┐      ┌───────────────────────────┐
│PostgreSQL (DB)      │      │ RabbitMQ (Message Broker) │
│ - urls table         │      │ Queue for analytics       │
│ - analytics table    │      └───────────────────────────┘
└─────────────────────┘               |
                                      |
                         ┌─────────────────────────┐
                         │  Worker (Consumer)      │
                         │  - Subscribes to queue  │
                         │  - Inserts analytics    │
                         └─────────────────────────┘
```

---

## Tech Stack

- **Language/Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)  
- **Database**: [PostgreSQL](https://www.postgresql.org/)  
- **Cache**: [Redis](https://redis.io/)  
- **Message Queue**: [RabbitMQ](https://www.rabbitmq.com/)  
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/)  
- **Containerization**: [Docker](https://www.docker.com/) + [docker-compose](https://docs.docker.com/compose/)  

---

## Project Structure

```
.
├─ app/
│  ├─ main.py            # FastAPI entry point
│  ├─ db.py              # DB connection (SQLAlchemy)
│  ├─ redis_conn.py      # Redis client
│  ├─ models.py          # SQLAlchemy models
│  ├─ routers/
│  │   ├─ shorten.py     # /shorten endpoint
│  │   ├─ redirect.py    # /{short_code} endpoint
│  │   └─ analytics.py   # /analytics/{short_code} endpoint
│  └─ ...
├─ worker/
│  └─ worker.py          # RabbitMQ consumer that inserts analytics
├─ requirements.txt      # Python dependencies
├─ Dockerfile            # Docker build definition
├─ docker-compose.yml    # Orchestrates multi-container setup
├─ .env                  # Environment variables (optional)
└─ README.md             # This file
```

*(Names and exact layout can vary.)*

---

## Installation & Setup

### Local Setup (Without Docker)

1. **Install Redis & PostgreSQL** on your machine (or use Docker for them).  
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up DB** (create a PostgreSQL database, run migrations or create the tables):
   ```sql
   CREATE DATABASE short_db;
   ```
5. **Run Redis server** (e.g. `redis-server`)  
6. **Run Worker** (if using RabbitMQ for analytics). Ensure RabbitMQ is running. Then:
   ```bash
   python worker/worker.py
   ```
7. **Start FastAPI (Uvicorn)**:
   ```bash
   uvicorn app.main:app --reload
   ```
8. Access the API at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Docker Compose Setup

1. **Install Docker & docker-compose**.  
2. **Build and run** everything:
   ```bash
   docker-compose up -d
   ```
3. This will start:
   - **web** container (FastAPI + Uvicorn)  
   - **worker** container (consumes from RabbitMQ)  
   - **PostgreSQL**  
   - **Redis**  
   - **RabbitMQ** (with management UI at [http://localhost:15672](http://localhost:15672), default user: guest / pass: guest)

4. Visit [http://localhost:8000/docs](http://localhost:8000/docs) to test the API.

---

## API Usage

### 1) Shorten URL

- **Endpoint**: `POST /shorten`  
- **Body** (JSON):
  ```json
  {
    "long_url": "https://www.example.com/some/long/path",
    "expire_at": "2025-01-01T00:00:00"
  }
  ```
  (If your service auto-sets an 8-day expiry, `expire_at` might be optional.)

- **Response**:
  ```json
  {
    "short_code": "Ab12Xy",
    "long_url": "https://www.example.com/some/long/path",
    "created_at": "2025-02-01T12:34:56.789Z",
    "expire_at": "2025-01-01T00:00:00"
  }
  ```

### 2) Redirect

- **Endpoint**: `GET /{short_code}`  
- **Behavior**: 302/307 redirect to the original URL if valid and not expired.  
- **If not found or expired**, returns 404 or 410 JSON error.

### 3) Get Analytics

- **Endpoint**: `GET /analytics/{short_code}`  
- **Query params**: `?group_by=day|week|...` (optional)  
- **Response** (example for no grouping):
  ```json
  {
    "short_code": "Ab12Xy",
    "long_url": "https://www.example.com/...",
    "recent_visits": [
      {
        "clicked_at": "2025-02-01T13:00:00Z",
        "ip_address": "127.0.0.1",
        "user_agent": "Mozilla/5.0 ...",
        "referrer": "...",
        "geo": {...}
      },
      ...
    ]
  }
  ```

---

## Worker (Analytics Consumer)

- **Location**: `worker/worker.py` (or a similar path).  
- **Role**:  
  1. Subscribe to RabbitMQ queue (e.g. `analytics_queue`).  
  2. Parse analytics messages (short_code, IP, user_agent).  
  3. Insert into `analytics` table in PostgreSQL.

**How to run**:
```bash
python worker/worker.py
```
(Or automatically via Docker Compose.)

---

## License

This project is available under the [MIT License](LICENSE). Feel free to modify and distribute as needed.

---

**Happy shortening & analyzing!** If you have any questions or issues, feel free to open an issue or contribute a pull request.
