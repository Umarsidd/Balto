"""Mock Slack client and welcome-message generator."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, List

from config import Settings
from validators import ValidatedHire


LOGGER = logging.getLogger(__name__)


@dataclass
class MockSlackClient:
    """Slack-like client for local testing.

    The OpenAI call is optional and uses minimal employee context. This avoids
    sending sensitive HR data that is not needed for a friendly welcome message.
    """

    settings: Settings
    posted_messages: List[Dict[str, object]] = field(default_factory=list)

    def generate_welcome_message(self, hire: ValidatedHire) -> Dict[str, object]:
        """Generate a Slack welcome message with OpenAI or fallback text."""

        if not self.settings.openai_api_key:
            return {
                "message": fallback_welcome_message(hire),
                "fallback_used": True,
                "reason": "OPENAI_API_KEY is not configured.",
            }

        prompt = (
            "Write a short, friendly Slack welcome message for a new Balto employee. "
            "Do not include private personal details. "
            f"Name: {hire.full_name}. Department: {hire.department}. Role: {hire.job_title}."
        )

        try:
            message = self._call_openai(prompt)
            return {"message": message, "fallback_used": False, "reason": ""}
        except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
            LOGGER.warning("OpenAI welcome generation failed; using fallback: %s", exc)
            return {
                "message": fallback_welcome_message(hire),
                "fallback_used": True,
                "reason": str(exc),
            }

    def send_message(self, channel: str, text: str) -> Dict[str, object]:
        """Record a mock Slack message."""

        payload = {"channel": channel, "text": text, "dry_run": self.settings.dry_run}
        self.posted_messages.append(payload)
        return {"status": "posted", "payload": payload}

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI Chat Completions with standard library HTTP."""

        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {"role": "system", "content": "You write concise workplace welcome messages."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read().decode("utf-8"))

        return str(body["choices"][0]["message"]["content"]).strip()


def fallback_welcome_message(hire: ValidatedHire) -> str:
    """Return deterministic welcome text when AI is unavailable."""

    return (
        f"Welcome to Balto, {hire.first_name}! "
        f"We're excited to have you joining the {hire.department} team as {hire.job_title}."
    )
