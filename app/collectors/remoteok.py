import requests
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models.job import Job
from app.utils.job_filter import JobFilter
from app.utils.logger import logger


class RemoteOKCollector(BaseCollector):
    """
    Collector for RemoteOK job board API (https://remoteok.com/api).
    """

    API_URL = "https://remoteok.com/api?tag=mobile"
    MOBILE_KEYWORDS = {
        "mobile", "android", "ios", "flutter", "kotlin", "swift",
        "kmp", "react native", "react-native", "dart", "swiftui"
    }

    @property
    def source_name(self) -> str:
        return "RemoteOK"

    def fetch_jobs(self) -> List[Job]:
        """
        Download jobs from RemoteOK API, filter mobile positions, and normalize into Job objects.
        """
        logger.info(f"[{self.source_name}] Starting job collection...")
        jobs: List[Job] = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) MobileDevJobsBot/1.0 (https://github.com/mobile-dev-jobs-bot)"
        }

        try:
            response = requests.get(self.API_URL, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, list):
                logger.warning(f"[{self.source_name}] Unexpected API payload format.")
                return []

            # RemoteOK's first item is standard legal metadata, skip it if 'position' is missing
            raw_jobs = [item for item in data if isinstance(item, dict) and "position" in item]

            for item in raw_jobs:
                title = item.get("position", "").strip()
                company = item.get("company", "").strip()
                tags = [str(t).lower() for t in item.get("tags", [])]

                # Check strict mobile developer role relevance
                if not JobFilter.is_strictly_mobile_job(title, tags):
                    continue

                url = item.get("url") or item.get("apply_url") or f"https://remoteok.com/job/{item.get('id')}"
                if not url.startswith("http"):
                    url = f"https://remoteok.com{url}"

                location = item.get("location") or "Remote"
                posted_date = item.get("date", "")

                job = Job(
                    title=title,
                    company=company or "Unknown Company",
                    location=location,
                    employment_type="Full-time",
                    url=url,
                    source=self.source_name,
                    posted_at=str(posted_date)[:10] if posted_date else "Recently"
                )
                jobs.append(job)

            logger.info(f"[{self.source_name}] Fetched and normalized {len(jobs)} mobile jobs.")
            return jobs

        except Exception as e:
            logger.error(f"[{self.source_name}] Failed to fetch jobs: {e}")
            return []
