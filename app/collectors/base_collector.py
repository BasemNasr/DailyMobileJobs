from abc import ABC, abstractmethod
from typing import List
from app.models.job import Job


class BaseCollector(ABC):
    """
    Abstract Base Class for all Job Collectors.
    Every collector implementation must inherit from BaseCollector and implement fetch_jobs.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return human readable identifier for the job collector source."""
        pass

    @abstractmethod
    def fetch_jobs(self) -> List[Job]:
        """
        Fetch jobs from source API or scraper, normalize into Job models, and return a list.
        Must catch internal errors gracefully and return an empty list on failure.
        """
        pass
