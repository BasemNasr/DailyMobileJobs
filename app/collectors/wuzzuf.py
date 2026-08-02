import re
import requests
from bs4 import BeautifulSoup
from typing import List
from app.collectors.base_collector import BaseCollector
from app.models.job import Job
from app.utils.job_filter import JobFilter
from app.utils.logger import logger


class WuzzufCollector(BaseCollector):
    """
    Collector for Wuzzuf (Egypt & MENA job platform - https://wuzzuf.net).
    """

    TARGET_URLS = [
        "https://wuzzuf.net/a/Mobile-Developer-Jobs-in-Egypt",
        "https://wuzzuf.net/a/Android-Developer-Jobs-in-Egypt",
        "https://wuzzuf.net/a/iOS-Developer-Jobs-in-Egypt",
        "https://wuzzuf.net/a/Flutter-Developer-Jobs-in-Egypt",
    ]

    @property
    def source_name(self) -> str:
        return "Wuzzuf"

    def fetch_jobs(self) -> List[Job]:
        """
        Fetch mobile developer jobs from Wuzzuf, extract details, and normalize into Job objects.
        """
        logger.info(f"[{self.source_name}] Starting job collection...")
        jobs: List[Job] = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        }

        seen_urls = set()

        for url in self.TARGET_URLS:
            try:
                response = requests.get(url, headers=headers, timeout=12)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                job_links = soup.find_all("a", href=re.compile(r"/jobs/p/"))

                for a in job_links:
                    title = a.text.strip()
                    href = a.get("href", "")
                    if not title or not href:
                        continue

                    if not href.startswith("http"):
                        href = f"https://wuzzuf.net{href}"

                    clean_url = href.split("?")[0]
                    if clean_url in seen_urls:
                        continue
                    seen_urls.add(clean_url)

                    # Extract company and location from URL path (e.g. /jobs/p/id-title-company-cairo-egypt)
                    location = "Egypt"
                    if "cairo" in clean_url.lower():
                        location = "Cairo, Egypt"
                    elif "alexandria" in clean_url.lower():
                        location = "Alexandria, Egypt"
                    elif "giza" in clean_url.lower():
                        location = "Giza, Egypt"

                    company = extract_company_from_wuzzuf_url(clean_url)

                    # Verify strict mobile developer role relevance
                    if not JobFilter.is_strictly_mobile_job(title):
                        continue

                    job = Job(
                        title=title,
                        company=company,
                        location=location,
                        employment_type="Full-time",
                        url=clean_url,
                        source=self.source_name,
                        posted_at="Recently"
                    )
                    jobs.append(job)

            except Exception as e:
                logger.error(f"[{self.source_name}] Failed to fetch from '{url}': {e}")
                continue

        logger.info(f"[{self.source_name}] Fetched and normalized {len(jobs)} mobile jobs.")
        return jobs


def extract_company_from_wuzzuf_url(url: str) -> str:
    """Extract company slug from Wuzzuf URL structure."""
    try:
        slug = url.split("/jobs/p/")[1]
        parts = slug.split("-")
        if len(parts) >= 3:
            return parts[-3].replace("-", " ").title()
    except Exception:
        pass
    return "Wuzzuf Employer"
