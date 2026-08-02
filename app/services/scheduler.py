import time
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from app.collectors import (
    BaseCollector,
    RemoteOKCollector,
    RemotiveCollector,
    CompanySitesCollector,
)
from app.database.db import db_service
from app.models.job import Job
from app.services.duplicate_service import duplicate_service
from app.services.telegram_service import telegram_service
from app.utils.config import settings
from app.utils.job_filter import JobFilter
from app.utils.logger import logger


class JobScheduler:
    """
    Orchestrates job collection, deduplication, database persistence,
    and Telegram channel publishing using APScheduler.
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.collectors: List[BaseCollector] = [
            RemoteOKCollector(),
            RemotiveCollector(),
            CompanySitesCollector(),
        ]

    def run_pipeline(self) -> None:
        """
        Execute the end-to-end publishing pipeline:
        1. Run all collectors safely
        2. Normalize jobs
        3. Remove duplicates
        4. Save new jobs into SQLite
        5. Publish unpublished jobs to Telegram
        6. Mark jobs as published
        """
        logger.info("=================== PIPELINE STARTED ===================")
        all_collected_jobs: List[Job] = []

        # Step 1 & 2: Run collectors and collect normalized jobs
        for collector in self.collectors:
            try:
                logger.info(f"Collector started: {collector.source_name}")
                jobs = collector.fetch_jobs()
                all_collected_jobs.extend(jobs)
            except Exception as e:
                logger.error(f"Error in collector '{collector.source_name}': {e}")
                # Continue with remaining collectors even if one fails
                continue

        logger.info(f"Total raw jobs collected across all collectors: {len(all_collected_jobs)}")

        # Step 2.5: Filter by strict mobile relevance & location criteria
        relevant_jobs = [job for job in all_collected_jobs if JobFilter.filter_job(job)]
        logger.info(f"Filtered {len(relevant_jobs)} mobile & location matching jobs out of {len(all_collected_jobs)} total raw jobs.")

        # Step 3: Remove duplicates
        unique_jobs = duplicate_service.filter_duplicates(relevant_jobs)

        # Step 4: Save new jobs into SQLite
        inserted_count = 0
        for job in unique_jobs:
            job_id = db_service.insert_job(job)
            if job_id is not None:
                inserted_count += 1

        logger.info(f"Database inserts completed: {inserted_count} new jobs stored.")

        # Step 5 & 6: Fetch unpublished jobs and send to Telegram
        unpublished_jobs = db_service.get_unpublished_jobs()
        logger.info(f"Unpublished jobs pending Telegram broadcast: {len(unpublished_jobs)}")

        published_count = 0
        for job in unpublished_jobs:
            success = telegram_service.send_job(job)
            if success and job.id is not None:
                db_service.mark_as_published(job.id)
                published_count += 1
            else:
                logger.warning(f"Failed to publish job ID {job.id} ('{job.title}'). Will retry next cycle.")
            
            # Rate-limiting pause to respect Telegram API broadcast limits
            time.sleep(2)

        logger.info(f"Telegram messages sent: {published_count} jobs published successfully.")
        logger.info("=================== PIPELINE COMPLETED ===================")

    def start_scheduler(self, interval_minutes: int = 30) -> None:
        """
        Start the background scheduler to run the pipeline periodically.
        """
        logger.info(f"Starting APScheduler with interval={interval_minutes} minutes.")
        self.scheduler.add_job(
            self.run_pipeline,
            trigger="interval",
            minutes=interval_minutes,
            id="job_pipeline_job",
            replace_existing=True,
        )
        self.scheduler.start()

    def stop_scheduler(self) -> None:
        """
        Stop the background scheduler.
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("APScheduler stopped.")


job_scheduler = JobScheduler()
