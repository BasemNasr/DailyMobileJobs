from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class Job(BaseModel):
    """
    Pydantic data model representing a Mobile Developer Job opportunity.
    """
    id: Optional[int] = None
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(default="Remote", description="Job location or remote status")
    employment_type: str = Field(default="Full-time", description="Full-time, Part-time, Contract, etc.")
    url: str = Field(..., description="Direct application link")
    source: str = Field(..., description="Source platform name (e.g. RemoteOK, Remotive)")
    published: bool = Field(default=False, description="Flag indicating if published to Telegram")
    posted_at: str = Field(default="", description="Human-readable or ISO posted timestamp")
    created_at: Optional[str] = Field(default=None, description="Database record insertion timestamp")

    @field_validator("title", "company", "location", "employment_type", "source", mode="before")
    @classmethod
    def strip_whitespaces(cls, value: str) -> str:
        """Strip unnecessary whitespace and newlines from text fields."""
        if isinstance(value, str):
            return " ".join(value.split())
        return value

    def generate_hashtags(self) -> str:
        """
        Generate relevant technology hashtags based on job title and tags.
        """
        text = f"{self.title} {self.source}".lower()
        tags = set()

        if "android" in text:
            tags.add("#Android")
        if "kotlin" in text:
            tags.add("#Kotlin")
        if "compose" in text or "jetpack" in text:
            tags.add("#Compose")
        if "ios" in text or "iphone" in text or "ipad" in text:
            tags.add("#iOS")
        if "swift" in text:
            tags.add("#Swift")
        if "flutter" in text or "dart" in text:
            tags.add("#Flutter")
        if "kmp" in text or "kotlin multiplatform" in text:
            tags.add("#KMP")
        if "react native" in text or "react-native" in text:
            tags.add("#ReactNative")

        # Default fallback tags if no specific tech tag matched
        if not tags:
            tags.add("#MobileDev")
            tags.add("#RemoteJobs")

        return " ".join(sorted(list(tags)))
