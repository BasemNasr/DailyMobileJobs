import argparse
import signal
import sys
import time
from app.database.db import db_service
from app.services.scheduler import job_scheduler
from app.utils.config import settings
from app.utils.logger import logger


def signal_handler(signum, frame):
    """Handle graceful shutdown on SIGINT or SIGTERM."""
    logger.info(f"Received signal {signum}. Shutting down application gracefully...")
    job_scheduler.stop_scheduler()
    sys.exit(0)


def main():
    """
    Main entry point for Mobile Dev Jobs Bot.
    """
    parser = argparse.ArgumentParser(description="Mobile Dev Jobs Bot")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run the collection and publishing pipeline once immediately and exit.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=settings.FETCH_INTERVAL_MINUTES,
        help="Polling interval in minutes for background scheduler (default: 30).",
    )
    args = parser.parse_args()

    logger.info("Initializing Mobile Dev Jobs Bot MVP...")

    # 1. Initialize SQLite Database
    db_service.initialize_database()

    # 2. Check configuration
    if not settings.BOT_TOKEN:
        logger.warning("BOT_TOKEN is missing in environment! Telegram publishing will fail until configured.")
    if not settings.CHANNEL:
        logger.warning("CHANNEL is missing in environment! Target channel must be set.")

    # 3. Handle execution mode
    if args.run_once:
        logger.info("Running pipeline in single-shot mode (--run-once)...")
        job_scheduler.run_pipeline()
        logger.info("Single-shot pipeline execution finished successfully.")
        return

    # 4. Daemon mode with APScheduler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Running initial pipeline on startup...")
    job_scheduler.run_pipeline()

    logger.info(f"Starting background scheduler (interval={args.interval} minutes)... Press Ctrl+C to stop.")
    job_scheduler.start_scheduler(interval_minutes=args.interval)

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Termination requested. Exiting...")
        job_scheduler.stop_scheduler()


if __name__ == "__main__":
    main()
