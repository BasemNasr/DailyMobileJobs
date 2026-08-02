import requests
from typing import Dict, List, Optional, Callable
from bs4 import BeautifulSoup
from app.collectors.base_collector import BaseCollector
from app.models.job import Job
from app.utils.logger import logger


class CompanySitesCollector(BaseCollector):
    """
    Collector framework for company career websites.
    Supports modular scrapers/integrations for major target companies:
    Google, Microsoft, Amazon, Meta, Careem, Talabat, Noon, Instabug, Vodafone, Valeo, IBM, Dell, Oracle.
    """

    TARGET_COMPANIES = [
        "Google", "Microsoft", "Amazon", "Meta", "Careem",
        "Talabat", "Noon", "Instabug", "Vodafone", "Valeo",
        "IBM", "Dell", "Oracle"
    ]

    MOBILE_KEYWORDS = {
        "mobile", "android", "ios", "flutter", "kotlin", "swift",
        "kmp", "react native", "react-native", "dart", "swiftui"
    }

    def __init__(self):
        # Dispatch registry mapping company name to custom scraper handler
        self._scrapers: Dict[str, Callable[[], List[Job]]] = {
            company: self._make_placeholder_scraper(company)
            for company in self.TARGET_COMPANIES
        }

    @property
    def source_name(self) -> str:
        return "Company Careers"

    def register_company_scraper(self, company_name: str, handler: Callable[[], List[Job]]) -> None:
        """
        Register or override a scraper handler for a specific company.
        """
        self._scrapers[company_name] = handler
        logger.info(f"[{self.source_name}] Registered scraper handler for '{company_name}'.")

    def fetch_jobs(self) -> List[Job]:
        """
        Run all registered company career site scrapers safely.
        """
        logger.info(f"[{self.source_name}] Starting company sites collection for {len(self._scrapers)} targets...")
        all_jobs: List[Job] = []

        for company_name, scraper_fn in self._scrapers.items():
            try:
                jobs = scraper_fn()
                all_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"[{self.source_name}] Failed to collect jobs for '{company_name}': {e}")
                continue

        logger.info(f"[{self.source_name}] Total company site jobs fetched: {len(all_jobs)}.")
        return all_jobs

    def _make_placeholder_scraper(self, company_name: str) -> Callable[[], List[Job]]:
        """
        Factory method returning a stub scraper ready for future HTML/API integration per company.
        """
        def _stub() -> List[Job]:
            # Prepared placeholder hook for company direct career integrations
            logger.debug(f"[{self.source_name}] Scraper ready for '{company_name}'. (No active API active for stub)")
            return []
        return _stub
