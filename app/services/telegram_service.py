import html
import time
import requests
from typing import Optional
from app.models.job import Job
from app.utils.config import settings
from app.utils.logger import logger


class TelegramService:
    """
    Service responsible for initializing Telegram Bot integration,
    formatting job postings into clean HTML messages with technology hashtags,
    and broadcasting them to the configured Telegram channel.
    """

    def __init__(self, bot_token: Optional[str] = None, channel: Optional[str] = None):
        self.bot_token = bot_token or settings.BOT_TOKEN
        self.channel = channel or settings.clean_channel()
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_job(self, job: Job) -> bool:
        """
        Format and send a job posting to the Telegram channel.
        Returns True if sent successfully, False otherwise.
        """
        if not self.bot_token:
            logger.error("Telegram bot token is missing! Cannot send message.")
            return False
        if not self.channel:
            logger.error("Telegram target channel is missing! Cannot send message.")
            return False

        formatted_message = self.format_job_message(job)

        payload = {
            "chat_id": self.channel,
            "text": formatted_message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "link_preview_options": {"is_disabled": True},
        }

        try:
            logger.info(f"Sending Telegram message for '{job.title}' to {self.channel}...")
            response = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=15)
            res_data = response.json()

            if response.status_code == 200 and res_data.get("ok"):
                logger.info(f"Telegram message sent successfully for '{job.title}' @ '{job.company}'.")
                return True
            elif response.status_code == 429:
                retry_after = res_data.get("parameters", {}).get("retry_after", 5)
                logger.warning(f"Telegram API 429 Rate Limit hit. Waiting {retry_after} seconds before retry...")
                time.sleep(retry_after + 1)
                retry_resp = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=15)
                retry_data = retry_resp.json()
                if retry_resp.status_code == 200 and retry_data.get("ok"):
                    logger.info(f"Telegram message sent successfully after retry for '{job.title}'.")
                    return True
                else:
                    logger.error(f"Retry failed for '{job.title}': {retry_data.get('description')}")
                    return False
            else:
                description = res_data.get("description", "Unknown Telegram API error")
                logger.error(f"Telegram API Error [{response.status_code}]: {description}")
                return False

        except Exception as e:
            logger.error(f"Failed to send Telegram message for '{job.title}': {e}")
            return False

    def send_photo(self, photo_url_or_file: str, caption: str) -> bool:
        """
        Future expansion support for broadcasting job cards with image attachments.
        """
        if not self.bot_token or not self.channel:
            return False

        payload = {
            "chat_id": self.channel,
            "photo": photo_url_or_file,
            "caption": caption,
            "parse_mode": "HTML",
        }
        try:
            response = requests.post(f"{self.api_url}/sendPhoto", json=payload, timeout=15)
            return response.status_code == 200 and response.json().get("ok", False)
        except Exception as e:
            logger.error(f"Failed to send Telegram photo message: {e}")
            return False

    def format_job_message(self, job: Job) -> str:
        """
        Format a Job object into Telegram HTML text.
        """
        title = html.escape(job.title)
        company = html.escape(job.company)
        location = html.escape(job.location)
        employment_type = html.escape(job.employment_type)
        posted_at = html.escape(job.posted_at or "Recently")
        source = html.escape(job.source)
        url = job.url.strip()
        hashtags = job.generate_hashtags()

        msg = (
            f"📱 <b>{title}</b>\n\n"
            f"🏢 <b>{company}</b>\n\n"
            f"📍 <b>{location}</b>\n\n"
            f"💼 <b>{employment_type}</b>\n\n"
            f"🕒 <b>{posted_at}</b>\n\n"
            f"🌐 Source: <b>{source}</b>\n\n"
            f"🔗 Apply:\n{url}\n\n"
            f"{hashtags}"
        )
        return msg


telegram_service = TelegramService()
