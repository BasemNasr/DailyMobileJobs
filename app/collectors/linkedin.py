import requests
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import quote_plus
from app.collectors.base_collector import BaseCollector
from app.models.job import Job
from app.utils.job_filter import JobFilter
from app.utils.logger import logger


class LinkedInCollector(BaseCollector):
    """
    Collector for public LinkedIn job search results (via LinkedIn Jobs Guest API).
    """

    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    SEARCH_QUERIES = [
        ("Android Developer", "Worldwide"),
        ("iOS Developer", "Worldwide"),
        ("Flutter Developer", "Worldwide"),
        ("React Native", "Worldwide"),
        ("Kotlin Multiplatform", "Worldwide"),
        ("Mobile Developer", "Egypt"),
        ("Mobile Developer", "Middle East"),
    ]

    @property
    def source_name(self) -> str:
        return "LinkedIn"

    def fetch_jobs(self) -> List[Job]:
        """
        Fetch jobs from LinkedIn guest search API, filter for mobile positions, and normalize into Job objects.
        """
        logger.info(f"[{self.source_name}] Starting job collection...")
        jobs: List[Job] = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        for keyword, location in self.SEARCH_QUERIES:
            url = f"{self.BASE_URL}?keywords={quote_plus(keyword)}&location={quote_plus(location)}&start=0"
            try:
                response = requests.get(url, headers=headers, timeout=12)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.find_all("li")

                for card in cards:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    loc_elem = card.find("span", class_="job-search-card__location")
                    link_elem = card.find("a", class_="base-card__full-link") or card.find("a")

                    if not title_elem or not company_elem or not link_elem:
                        continue

                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    job_loc = loc_elem.text.strip() if loc_elem else location
                    raw_link = link_elem.get("href", "").split("?")[0]

                    if not raw_link.startswith("http"):
                        continue

                    # Verify strict mobile role
                    if not JobFilter.is_strictly_mobile_job(title):
                        continue

                    job = Job(
                        title=title,
                        company=company,
                        location=job_loc,
                        employment_type="Full-time",
                        url=raw_link,
                        source=self.source_name,
                        posted_at="Recently"
                    )
                    jobs.append(job)

            except Exception as e:
                logger.error(f"[{self.source_name}] Failed to query '{keyword}' in '{location}': {e}")
                continue

        logger.info(f"[{self.source_name}] Fetched and normalized {len(jobs)} mobile jobs.")
        return jobs
