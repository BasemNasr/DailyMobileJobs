import sqlite3
from datetime import datetime, timezone
from typing import List, Optional
from app.models.job import Job
from app.utils.config import settings
from app.utils.logger import logger


class DatabaseService:
    """
    SQLite Database Service managing persistent storage for job listings.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH

    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a new SQLite database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_database(self) -> None:
        """
        Initialize the SQLite database schema if not already present.
        """
        schema_sql = """
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
        """
        try:
            with self._get_connection() as conn:
                conn.executescript(schema_sql)
                conn.commit()
            logger.info(f"Database initialized successfully at '{self.db_path}'.")
        except Exception as e:
            logger.error(f"Error initializing database at '{self.db_path}': {e}")
            raise

    def insert_job(self, job: Job) -> Optional[int]:
        """
        Insert a new Job record into the SQLite database.
        Returns the inserted job's ID if successful, None otherwise.
        """
        created_at = datetime.now(timezone.utc).isoformat()
        insert_sql = """
        INSERT INTO jobs (title, company, location, employment_type, url, source, published, posted_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    insert_sql,
                    (
                        job.title,
                        job.company,
                        job.location,
                        job.employment_type,
                        job.url,
                        job.source,
                        1 if job.published else 0,
                        job.posted_at,
                        created_at,
                    ),
                )
                conn.commit()
                job_id = cursor.lastrowid
                logger.info(f"Database insert successful: '{job.title}' @ '{job.company}' [ID: {job_id}]")
                return job_id
        except sqlite3.IntegrityError:
            logger.warning(f"Database insert skipped (duplicate URL): {job.url}")
            return None
        except Exception as e:
            logger.error(f"Failed to insert job '{job.title}': {e}")
            return None

    def job_exists(self, url: str, company: str, title: str) -> bool:
        """
        Check if a job already exists in the database by URL OR by (company AND title).
        """
        check_sql = """
        SELECT 1 FROM jobs 
        WHERE url = ? 
           OR (LOWER(company) = LOWER(?) AND LOWER(title) = LOWER(?))
        LIMIT 1
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(check_sql, (url, company, title))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking job existence for '{title}' @ '{company}': {e}")
            return False

    def get_unpublished_jobs(self) -> List[Job]:
        """
        Retrieve all jobs that have not been published to Telegram yet.
        """
        select_sql = """
        SELECT id, title, company, location, employment_type, url, source, published, posted_at, created_at
        FROM jobs
        WHERE published = 0
        ORDER BY id ASC
        """
        jobs: List[Job] = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(select_sql)
                rows = cursor.fetchall()
                for row in rows:
                    job = Job(
                        id=row["id"],
                        title=row["title"],
                        company=row["company"],
                        location=row["location"],
                        employment_type=row["employment_type"],
                        url=row["url"],
                        source=row["source"],
                        published=bool(row["published"]),
                        posted_at=row["posted_at"],
                        created_at=row["created_at"],
                    )
                    jobs.append(job)
            return jobs
        except Exception as e:
            logger.error(f"Error retrieving unpublished jobs: {e}")
            return []

    def mark_as_published(self, job_id: int) -> bool:
        """
        Mark a job as published in the database given its ID.
        """
        update_sql = "UPDATE jobs SET published = 1 WHERE id = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(update_sql, (job_id,))
                conn.commit()
                logger.info(f"Marked job ID {job_id} as published.")
                return True
        except Exception as e:
            logger.error(f"Error marking job ID {job_id} as published: {e}")
            return False


# Global database service instance
db_service = DatabaseService()
