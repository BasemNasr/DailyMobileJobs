import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import quote_plus
from app.collectors.base_collector import BaseCollector
from app.models.job import Job
from app.utils.job_filter import JobFilter
from app.utils.logger import logger


class IndeedCollector(BaseCollector):
    """
    Collector for Indeed job platform via RSS feeds and public syndication endpoints.
    """

    SEARCH_KEYWORDS = ["Android Developer", "iOS Developer", "Flutter Developer", "Mobile Engineer"]

    @property
    def source_name(self) -> str:
        return "Indeed"

    def fetch_jobs(self) -> List[Job]:
        """
        Fetch jobs from Indeed RSS feeds, extract job details, and normalize into Job objects.
        """
        logger.info(f"[{self.source_name}] Starting job collection...")
        jobs: List[Job] = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

        seen_urls = set()

        for kw in self.SEARCH_KEYWORDS:
            feed_url = f"https://www.indeed.jobs/rss?q={quote_plus(kw)}"
            try:
                response = requests.get(feed_url, headers=headers, timeout=12)
                if response.status_code != 200:
                    continue

                feed = feedparser.parse(response.text)
                for entry in feed.entries:
                    title = entry.get("title", "").strip()
                    url = entry.get("link", "").strip()
                    if not title or not url:
                        continue

                    clean_url = url.split("?")[0]
                    if clean_url in seen_urls:
                        continue
                    seen_urls.add(clean_url)

                    # Extract company and location from entry metadata or summary HTML
                    summary_html = entry.get("summary", "")
                    soup = BeautifulSoup(summary_html, "html.parser")
                    company = entry.get("source", {}).get("title") or "Indeed Employer"
                    location = entry.get("location") or "Remote / Global"

                    if not JobFilter.is_strictly_mobile_job(title):
                        continue

                    job = Job(
                        title=title,
                        company=str(company),
                        location=str(location),
                        employment_type="Full-time",
                        url=clean_url,
                        source=self.source_name,
                        posted_at="Recently"
                    )
                    jobs.append(job)

            except Exception as e:
                logger.error(f"[{self.source_name}] Failed to fetch '{kw}': {e}")
                continue

        logger.info(f"[{self.source_name}] Fetched and normalized {len(jobs)} mobile jobs.")
        return jobs
