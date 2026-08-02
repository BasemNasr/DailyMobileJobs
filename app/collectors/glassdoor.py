import json
import requests
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import quote_plus
from app.collectors.base_collector import BaseCollector
from app.models.job import Job
from app.utils.job_filter import JobFilter
from app.utils.logger import logger


class GlassdoorCollector(BaseCollector):
    """
    Collector for Glassdoor job postings via structured JSON-LD data extraction.
    """

    BASE_URL = "https://www.glassdoor.com/Job/jobs.htm"
    KEYWORDS = ["Android Developer", "iOS Developer", "Flutter Developer", "Mobile Engineer"]

    @property
    def source_name(self) -> str:
        return "Glassdoor"

    def fetch_jobs(self) -> List[Job]:
        """
        Fetch jobs from Glassdoor, extract structured JSON-LD job items, and normalize into Job objects.
        """
        logger.info(f"[{self.source_name}] Starting job collection...")
        jobs: List[Job] = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        for keyword in self.KEYWORDS:
            url = f"{self.BASE_URL}?sc.keyword={quote_plus(keyword)}"
            try:
                response = requests.get(url, headers=headers, timeout=12)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                scripts = soup.find_all("script", type="application/ld+json")

                for script in scripts:
                    try:
                        data = json.loads(script.string or "{}")
                        if not isinstance(data, dict) or "itemListElement" not in data:
                            continue

                        items = data.get("itemListElement", [])
                        for item in items:
                            if not isinstance(item, dict) or "name" not in item or "url" not in item:
                                continue

                            title = item.get("name", "").strip()
                            raw_url = item.get("url", "")

                            if not raw_link_valid(raw_url):
                                continue

                            # Try extracting company name from URL structure (e.g. /job-listing/title-company-JV_...)
                            company = extract_company_from_glassdoor_url(raw_url) or "Glassdoor Partner"

                            if not JobFilter.is_strictly_mobile_job(title):
                                continue

                            job = Job(
                                title=title,
                                company=company,
                                location="Remote / Global",
                                employment_type="Full-time",
                                url=raw_url,
                                source=self.source_name,
                                posted_at="Recently"
                            )
                            jobs.append(job)

                    except Exception as json_err:
                        logger.debug(f"[{self.source_name}] JSON parsing error: {json_err}")
                        continue

            except Exception as e:
                logger.error(f"[{self.source_name}] Failed to fetch '{keyword}': {e}")
                continue

        logger.info(f"[{self.source_name}] Fetched and normalized {len(jobs)} mobile jobs.")
        return jobs


def raw_link_valid(url: str) -> bool:
    return bool(url and url.startswith("http") and "glassdoor.com/job-listing/" in url)


def extract_company_from_glassdoor_url(url: str) -> str:
    """
    Extract company slug from Glassdoor job listing URL.
    e.g. 'https://www.glassdoor.com/job-listing/mobile-developer-senior-saic-JV_...' -> 'SAIC'
    """
    try:
        path = url.split("glassdoor.com/job-listing/")[1].split("-JV_")[0]
        parts = path.split("-")
        if len(parts) >= 2:
            return parts[-1].upper()
    except Exception:
        pass
    return "Glassdoor Employer"
