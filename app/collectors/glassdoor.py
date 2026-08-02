import re
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
    Collector for Glassdoor job postings via HTML parsing & structured card extraction.
    Extracts real job titles, companies, actual city/country locations, and direct application links.
    """

    BASE_URL = "https://www.glassdoor.com/Job/jobs.htm"
    KEYWORDS = ["Android Developer", "iOS Developer", "Flutter Developer", "Mobile Engineer"]

    @property
    def source_name(self) -> str:
        return "Glassdoor"

    def fetch_jobs(self) -> List[Job]:
        """
        Fetch jobs from Glassdoor, extract exact title, company, true location, and application URL.
        """
        logger.info(f"[{self.source_name}] Starting job collection...")
        jobs: List[Job] = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        seen_urls = set()

        for keyword in self.KEYWORDS:
            url = f"{self.BASE_URL}?sc.keyword={quote_plus(keyword)}"
            try:
                response = requests.get(url, headers=headers, timeout=12)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                cards = soup.find_all(
                    lambda tag: tag.get("class") and any("JobCard_jobCardWrapper" in c or "jobCard" in c for c in tag.get("class"))
                )

                for card in cards:
                    title_elem = card.find(lambda t: t.get("class") and any("jobTitle" in c for c in t.get("class")))
                    company_elem = card.find(lambda t: t.get("class") and any("employerName" in c or "company" in c for c in t.get("class")))
                    loc_elem = card.find(lambda t: t.get("class") and any("location" in c.lower() for c in t.get("class")))
                    link_elem = card.find("a", href=True)

                    if not title_elem or not link_elem:
                        continue

                    title = title_elem.text.strip()
                    raw_company = company_elem.text.strip() if company_elem else "Glassdoor Employer"
                    # Strip trailing rating digits (e.g. 'Capgemini4.2' -> 'Capgemini')
                    company = re.sub(r"\s*\d+(\.\d+)?$", "", raw_company).strip()

                    location = loc_elem.text.strip() if loc_elem else "Remote / Worldwide"
                    raw_link = link_elem["href"]

                    if not raw_link.startswith("http"):
                        raw_link = f"https://www.glassdoor.com{raw_link}"

                    clean_url = raw_link.split("?")[0]
                    if clean_url in seen_urls:
                        continue
                    seen_urls.add(clean_url)

                    # Check strict mobile role relevance
                    if not JobFilter.is_strictly_mobile_job(title):
                        continue

                    job = Job(
                        title=title,
                        company=company or "Glassdoor Employer",
                        location=location,
                        employment_type="Full-time",
                        url=clean_url,
                        source=self.source_name,
                        posted_at="Recently"
                    )
                    jobs.append(job)

            except Exception as e:
                logger.error(f"[{self.source_name}] Failed to fetch '{keyword}': {e}")
                continue

        logger.info(f"[{self.source_name}] Fetched and normalized {len(jobs)} mobile jobs with true locations.")
        return jobs
