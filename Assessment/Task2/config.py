"""Runtime configuration for the onboarding automation.

Secrets are read from environment variables or a local .env file. This keeps
credentials out of source control and supports SOC2 expectations around secret
management and least privilege.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Set


LOGGER = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required runtime configuration is invalid."""


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    email_domain: str = "balto.com"
    allowed_countries: Set[str] = field(
        default_factory=lambda: {
            "United States",
            "Canada",
            "United Kingdom",
            "Ireland",
            "Germany",
            "Netherlands",
            "India",
            "Australia",
        }
    )
    dry_run: bool = True
    log_level: str = "INFO"
    okta_org_url: str = ""
    okta_api_token: str = ""
    google_customer_id: str = ""
    google_admin_subject: str = ""
    iru_api_url: str = ""
    iru_api_token: str = ""
    slack_webhook_url: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"


def load_settings(env_file: str | Path = ".env") -> Settings:
    """Load settings from .env and process environment variables.

    python-dotenv is optional at runtime. If it is not installed, the automation
    still works with normal environment variables.
    """

    load_dotenv_if_available(env_file)

    return Settings(
        email_domain=os.getenv("BALTO_EMAIL_DOMAIN", "balto.com").strip().lower(),
        allowed_countries=parse_csv_set(
            os.getenv(
                "ALLOWED_COUNTRIES",
                "United States,Canada,United Kingdom,Ireland,Germany,Netherlands,India,Australia",
            )
        ),
        dry_run=parse_bool(os.getenv("DRY_RUN", "true")),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        okta_org_url=os.getenv("OKTA_ORG_URL", ""),
        okta_api_token=os.getenv("OKTA_API_TOKEN", ""),
        google_customer_id=os.getenv("GOOGLE_CUSTOMER_ID", ""),
        google_admin_subject=os.getenv("GOOGLE_ADMIN_SUBJECT", ""),
        iru_api_url=os.getenv("IRU_API_URL", ""),
        iru_api_token=os.getenv("IRU_API_TOKEN", ""),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )


def load_dotenv_if_available(env_file: str | Path) -> None:
    """Load a .env file when python-dotenv is installed."""

    path = Path(env_file)
    if not path.exists():
        return

    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        LOGGER.debug("python-dotenv not installed; relying on process environment.")
        return

    load_dotenv(path)


def parse_csv_set(value: str | Iterable[str]) -> Set[str]:
    """Parse comma-separated values into a normalized set."""

    if isinstance(value, str):
        items = value.split(",")
    else:
        items = list(value)
    return {item.strip() for item in items if item and item.strip()}


def parse_bool(value: str | bool) -> bool:
    """Parse human-friendly boolean values."""

    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def configure_logging(level: str) -> None:
    """Configure console logging for CLI usage."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
