from typing import List, Tuple, Set
from app.models.job import Job
from app.database.db import db_service
from app.utils.logger import logger


class DuplicateService:
    """
    Service responsible for deduplicating job listings against the database
    and in-memory collected batches.
    """

    def filter_duplicates(self, jobs: List[Job]) -> List[Job]:
        """
        Filter out duplicates from a list of collected jobs.
        A job is a duplicate if:
        1. Its URL or (Company + Title) already exists in the database.
        2. Its URL or (Company + Title) was already seen in the current batch.
        """
        unique_jobs: List[Job] = []
        seen_urls: Set[str] = set()
        seen_company_titles: Set[Tuple[str, str]] = set()

        skipped_count = 0

        for job in jobs:
            normalized_url = job.url.strip().lower()
            company_title_key = (job.company.strip().lower(), job.title.strip().lower())

            # Check in-memory batch duplicates
            if normalized_url in seen_urls or company_title_key in seen_company_titles:
                skipped_count += 1
                logger.debug(f"Duplicate skipped (in-batch): '{job.title}' @ '{job.company}'")
                continue

            # Check database duplicates
            if db_service.job_exists(url=job.url, company=job.company, title=job.title):
                skipped_count += 1
                logger.debug(f"Duplicate skipped (in-DB): '{job.title}' @ '{job.company}'")
                continue

            # Mark as seen and retain
            seen_urls.add(normalized_url)
            seen_company_titles.add(company_title_key)
            unique_jobs.append(job)

        logger.info(f"Duplicate filter complete: {len(unique_jobs)} new jobs retained, {skipped_count} duplicates skipped.")
        return unique_jobs


duplicate_service = DuplicateService()
