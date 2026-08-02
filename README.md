# 📱 Mobile Dev Jobs Bot

A production-ready, modular, and scalable Python bot that automatically collects high-quality mobile developer job opportunities (Android, iOS, Flutter, Kotlin Multiplatform, React Native) from multiple job boards and publishes them to a Telegram channel.

---

## 🌟 Architecture & Project Structure

```
mobile-dev-jobs-bot/
│
├── app/
│   ├── collectors/
│   │   ├── base_collector.py     # Base abstract collector interface
│   │   ├── remoteok.py           # RemoteOK API collector
│   │   ├── remotive.py           # Remotive API collector
│   │   ├── company_sites.py      # Company careers collector registry
│   │   └── __init__.py
│   │
│   ├── database/
│   │   ├── db.py                 # SQLite database service & schema
│   │   └── __init__.py
│   │
│   ├── models/
│   │   ├── job.py                # Pydantic Job model & hashtag generator
│   │   └── __init__.py
│   │
│   ├── services/
│   │   ├── telegram_service.py   # Telegram bot broadcast service
│   │   ├── duplicate_service.py  # In-memory & DB duplicate filter
│   │   ├── scheduler.py          # APScheduler pipeline orchestrator
│   │   └── __init__.py
│   │
│   ├── utils/
│   │   ├── config.py             # Settings & environment parser
│   │   ├── logger.py             # Loguru structured logging
│   │   └── __init__.py
│   │
│   └── __init__.py
│
├── .github/
│   └── workflows/
│       └── job_bot.yml           # GitHub Actions automated workflow
├── .env.example                  # Environment template
├── .gitignore
├── jobs.db                       # SQLite database
├── main.py                       # Main application entry point
├── README.md                     # Documentation
└── requirements.txt              # Project dependencies
```

---

## 🛢️ Database Schema (`jobs.db`)

```sql
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT DEFAULT 'Remote',
    employment_type TEXT DEFAULT 'Full-time',
    url TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    published INTEGER DEFAULT 0,
    posted_at TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_company_title ON jobs(company, title);
```

---

## 🔁 Duplicate Detection Rules

A job is considered a duplicate and skipped if:
1. **URL Match**: The job URL already exists in SQLite or current batch.
2. **Company + Title Match**: A record with the exact same `(company, title)` tuple already exists in SQLite or current batch.

---

## 🚀 Setup & Local Execution

### 1. Clone & Setup Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and insert your Telegram Bot details:
```ini
BOT_TOKEN=8689117610:AAHDULx37yRoVX5a_P9luLIGYBx0PlzUPU4
CHANNEL=https://t.me/dailymobiledevjobs
DATABASE_PATH=jobs.db
FETCH_INTERVAL_MINUTES=30
LOG_LEVEL=INFO
```

### 3. Run Locally

- **Single-Shot Mode (Run once & exit):**
  ```bash
  python main.py --run-once
  ```

- **Daemon Mode (Background scheduler every 30 mins):**
  ```bash
  python main.py
  ```

---

## ☁️ Free GitHub Actions Deployment

The repository includes a pre-configured GitHub Actions workflow in `.github/workflows/job_bot.yml` configured to run every 30 minutes for free.

### GitHub Secrets Setup:
Navigate to your repository **Settings > Secrets and variables > Actions** and add:
- `BOT_TOKEN`: Telegram bot HTTP API token
- `CHANNEL`: Target channel link or handle (e.g., `https://t.me/dailymobiledevjobs` or `@dailymobiledevjobs`)

---

## 🔌 How to Add New Collectors

All collectors inherit from `BaseCollector` in `app/collectors/base_collector.py`.

To add a new platform (e.g. `Wuzzuf`, `Bayt`, `GulfTalent`, `Wellfound`, `Glassdoor`, `LinkedIn`, RSS feeds):

1. Create a new file in `app/collectors/wuzzuf.py`:
```python
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models.job import Job

class WuzzufCollector(BaseCollector):
    @property
    def source_name(self) -> str:
        return "Wuzzuf"

    def fetch_jobs(self) -> List[Job]:
        # Implement scraping/fetching logic
        return []
```
2. Register the new collector instance in `app/services/scheduler.py`:
```python
self.collectors = [
    RemoteOKCollector(),
    RemotiveCollector(),
    CompanySitesCollector(),
    WuzzufCollector(),
]
```

---

## 🔮 Future Design Extensions

### 1. AI Categorization Engine
A planned module `app/services/ai_classifier.py` leveraging LLMs/embeddings to:
- Classify jobs automatically into categories: `Android`, `Flutter`, `iOS`, `React Native`, `Kotlin Multiplatform`, `Frontend`, `Backend`.
- Filter out non-mobile software engineering positions automatically.

### 2. User & Admin Telegram Bot Commands

#### User Commands:
- `/start` - Welcome message & bot overview.
- `/help` - User command guide.
- `/android` - Fetch latest Android developer jobs.
- `/flutter` - Fetch latest Flutter jobs.
- `/ios` - Fetch latest iOS jobs.
- `/kmp` - Fetch latest Kotlin Multiplatform jobs.
- `/remote` - Fetch remote-only mobile jobs.

#### Admin Commands:
- `/stats` - Total jobs collected, published, and source statistics.
- `/test` - Trigger manual job collection cycle.
- `/repost <id>` - Force re-publish job by ID.
- `/lastjobs` - Show last 10 posted jobs.

---

## 📄 License
MIT License
