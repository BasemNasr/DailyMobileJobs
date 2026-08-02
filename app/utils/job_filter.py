import re
from typing import List, Optional
from app.models.job import Job
from app.utils.config import settings
from app.utils.logger import logger


class JobFilter:
    """
    Utility providing strict mobile role relevance validation and location-based filtering.
    """

    # Exact word-boundary regex matching mobile developer terms
    MOBILE_REGEX = re.compile(
        r"\b(android|ios|flutter|swift|swiftui|kotlin|kmp|react-native|react\s+native|mobile)\b",
        re.IGNORECASE
    )

    # Excluded job titles (e.g. AI Engineer, Data Scientist, Copywriter, Marketing, DevOps, etc.)
    NON_MOBILE_TITLES_REGEX = re.compile(
        r"\b(ai engineer|artificial intelligence|data scientist|data engineer|copywriter|marketing|devops|sysadmin|sales|qa tester|graphic designer|content reviewer)\b",
        re.IGNORECASE
    )

    # Location Keyword Categories
    EGYPT_KEYWORDS = {"egypt", "cairo", "alexandria", "giza", "مصر", "القاهرة"}
    MENA_KEYWORDS = {
        "middle east", "mena", "uae", "dubai", "saudi", "saudi arabia", "ksa",
        "riyadh", "qatar", "doha", "kuwait", "bahrain", "oman", "jordan",
        "amman", "lebanon", "beirut", "turkey", "istanbul", "north africa"
    }.union(EGYPT_KEYWORDS)

    GLOBAL_KEYWORDS = {
        "worldwide", "anywhere", "remote", "global", "work from anywhere",
        "wfa", "latam", "europe", "us", "usa", "emea", "apac", "americas",
        "flexible", "everywhere"
    }

    @classmethod
    def is_strictly_mobile_job(cls, title: str, tags: Optional[List[str]] = None) -> bool:
        """
        Verify if a job position is strictly a mobile developer role.
        """
        tags_str = " ".join(tags) if tags else ""
        combined_text = f"{title} {tags_str}".strip()

        # Reject explicitly non-mobile titles (e.g. Senior AI Engineer) unless title has explicit mobile keyword
        if cls.NON_MOBILE_TITLES_REGEX.search(title) and not cls.MOBILE_REGEX.search(title):
            return False

        # Require exact word boundary match for mobile developer terms
        return bool(cls.MOBILE_REGEX.search(combined_text))

    @classmethod
    def is_matching_location(cls, location: str, location_setting: Optional[str] = None) -> bool:
        """
        Check if job location matches user's preferred location settings.
        Supports: 'GLOBAL', 'MENA', 'EGYPT' or comma-separated list 'GLOBAL,MENA,EGYPT' or 'ALL'.
        """
        setting = (location_setting or settings.LOCATION_FILTER).upper().strip()

        if setting == "ALL" or not setting:
            return True

        loc_lower = location.lower()
        requested_regions = [r.strip() for r in setting.split(",") if r.strip()]

        for region in requested_regions:
            if region == "EGYPT":
                if any(kw in loc_lower for kw in cls.EGYPT_KEYWORDS):
                    return True
            elif region == "MENA":
                if any(kw in loc_lower for kw in cls.MENA_KEYWORDS):
                    return True
            elif region == "GLOBAL":
                if any(kw in loc_lower for kw in cls.GLOBAL_KEYWORDS):
                    return True

        # Default fallback: if location contains "remote" or is blank, treat as Global match
        if ("remote" in loc_lower or not loc_lower) and "GLOBAL" in requested_regions:
            return True

        return False

    @classmethod
    def filter_job(cls, job: Job) -> bool:
        """
        Validate both role relevance and location criteria for a Job object.
        """
        if not cls.is_strictly_mobile_job(job.title):
            logger.debug(f"Filter rejected non-mobile title: '{job.title}'")
            return False

        if not cls.is_matching_location(job.location):
            logger.debug(f"Filter rejected location '{job.location}' for title '{job.title}'")
            return False

        return True
