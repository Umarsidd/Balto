"""Mock Google Workspace client for local onboarding tests."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from validators import ValidatedHire


LOGGER = logging.getLogger(__name__)


@dataclass
class MockGoogleClient:
    """In-memory Google Workspace-like client."""

    dry_run: bool = True
    users_by_email: Dict[str, Dict[str, object]] = field(default_factory=dict)
    groups_by_email: Dict[str, set[str]] = field(default_factory=dict)

    def create_workspace_user(self, hire: ValidatedHire) -> Dict[str, object]:
        """Create or return a mock Google Workspace user."""

        if hire.work_email in self.users_by_email:
            return {"status": "exists", "user": self.users_by_email[hire.work_email], "idempotent": True}

        user = {
            "primaryEmail": hire.work_email,
            "name": {"givenName": hire.first_name, "familyName": hire.last_name},
            "orgUnitPath": f"/{hire.department}",
            "suspended": False,
            "changePasswordAtNextLogin": True,
            "dry_run": self.dry_run,
        }
        self.users_by_email[hire.work_email] = user
        LOGGER.info("Mock Google user prepared for %s", hire.work_email)
        return {"status": "created", "user": user, "idempotent": False}

    def assign_license(self, email: str, employment_type: str) -> Dict[str, object]:
        """Assign a mock license based on employment type."""

        license_name = "Google Workspace Business Standard"
        if employment_type.lower() == "contractor":
            license_name = "Google Workspace Starter Contractor"

        return {
            "email": email,
            "license": license_name,
            "status": "assigned",
            "dry_run": self.dry_run,
        }

    def add_to_groups(self, email: str, groups: Sequence[str]) -> List[Dict[str, object]]:
        """Add a user to mock Google groups idempotently."""

        current_groups = self.groups_by_email.setdefault(email, set())
        responses: List[Dict[str, object]] = []

        for group in groups:
            if group in current_groups:
                responses.append({"group": group, "status": "already_member", "idempotent": True})
                continue
            current_groups.add(group)
            responses.append({"group": group, "status": "added", "idempotent": False})

        return responses
