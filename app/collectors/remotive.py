import requests
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models.job import Job
from app.utils.job_filter import JobFilter
from app.utils.logger import logger


class RemotiveCollector(BaseCollector):
    """
    Collector for Remotive job board API (https://remotive.com/api/remote-jobs).
    """

    API_URL = "https://remotive.com/api/remote-jobs?search=mobile"
    MOBILE_KEYWORDS = {
        "mobile", "android", "ios", "flutter", "kotlin", "swift",
        "kmp", "react native", "react-native", "dart", "swiftui"
    }

    @property
    def source_name(self) -> str:
        return "Remotive"

    def fetch_jobs(self) -> List[Job]:
        """
        Fetch jobs from Remotive API, filter mobile positions, and normalize into Job models.
        """
        logger.info(f"[{self.source_name}] Starting job collection...")
        jobs: List[Job] = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) MobileDevJobsBot/1.0"
        }

        try:
            response = requests.get(self.API_URL, headers=headers, timeout=15)
            response.raise_for_status()

            payload = response.json()
            raw_jobs = payload.get("jobs", []) if isinstance(payload, dict) else []

            for item in raw_jobs:
                title = str(item.get("title", "")).strip()
                company = str(item.get("company_name", "")).strip()
                tags = [str(t).lower() for t in item.get("tags", [])]

                # Check strict mobile developer role relevance
                if not JobFilter.is_strictly_mobile_job(title, tags):
                    continue

                url = item.get("url") or f"https://remotive.com/remote-jobs/{item.get('id')}"
                location = item.get("candidate_required_location") or "Remote"
                job_type = item.get("job_type", "Full-time").replace("_", " ").title()
                pub_date = str(item.get("publication_date", ""))[:10]

                job = Job(
                    title=title,
                    company=company or "Unknown Company",
                    location=location,
                    employment_type=job_type,
                    url=url,
                    source=self.source_name,
                    posted_at=pub_date if pub_date else "Recently"
                )
                jobs.append(job)

            logger.info(f"[{self.source_name}] Fetched and normalized {len(jobs)} mobile jobs.")
            return jobs

        except Exception as e:
            logger.error(f"[{self.source_name}] Failed to fetch jobs: {e}")
            return []
