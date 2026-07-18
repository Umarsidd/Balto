"""Mock Okta client used for local testing and assessment review."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from validators import ValidatedHire


LOGGER = logging.getLogger(__name__)


@dataclass
class MockOktaClient:
    """In-memory Okta-like client with idempotent create and group assignment."""

    dry_run: bool = True
    users_by_email: Dict[str, Dict[str, object]] = field(default_factory=dict)
    assigned_groups_by_user: Dict[str, set[str]] = field(default_factory=dict)

    def create_user(self, hire: ValidatedHire) -> Dict[str, object]:
        """Create or return a mock Okta user."""

        if hire.work_email in self.users_by_email:
            return {
                "status": "exists",
                "user": self.users_by_email[hire.work_email],
                "idempotent": True,
            }

        user_id = f"00u_mock_{len(self.users_by_email) + 1:04d}"
        user = {
            "id": user_id,
            "profile": {
                "firstName": hire.first_name,
                "lastName": hire.last_name,
                "email": hire.work_email,
                "login": hire.work_email,
                "department": hire.department,
                "title": hire.job_title,
                "manager": hire.manager_email,
                "country": hire.country,
            },
            "activate": False,
            "dry_run": self.dry_run,
        }
        self.users_by_email[hire.work_email] = user
        self.assigned_groups_by_user[user_id] = set()
        LOGGER.info("Mock Okta user prepared for %s", hire.work_email)
        return {"status": "created", "user": user, "idempotent": False}

    def assign_groups(self, user_id: str, groups: Sequence[str]) -> List[Dict[str, object]]:
        """Assign allowlisted groups to a mock user.

        The caller supplies only groups from role_mapping.py. This preserves
        least privilege by avoiding direct CSV-to-group assignment.
        """

        assigned = self.assigned_groups_by_user.setdefault(user_id, set())
        responses: List[Dict[str, object]] = []

        for group in groups:
            if group in assigned:
                responses.append({"group": group, "status": "already_assigned", "idempotent": True})
                continue

            assigned.add(group)
            responses.append({"group": group, "status": "assigned", "idempotent": False})

        return responses
