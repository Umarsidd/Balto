"""Mock Iru client for endpoint blueprint assignment."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict

from validators import ValidatedHire


LOGGER = logging.getLogger(__name__)


@dataclass
class MockIruClient:
    """In-memory Iru-like endpoint provisioning client."""

    dry_run: bool = True
    assignments_by_email: Dict[str, Dict[str, object]] = field(default_factory=dict)

    def assign_blueprint(self, hire: ValidatedHire, blueprint: str) -> Dict[str, object]:
        """Assign an endpoint blueprint to a hire."""

        existing = self.assignments_by_email.get(hire.work_email)
        if existing and existing["blueprint"] == blueprint:
            return {"status": "already_assigned", "assignment": existing, "idempotent": True}

        assignment = {
            "email": hire.work_email,
            "employee_name": hire.full_name,
            "country": hire.country,
            "blueprint": blueprint,
            "ship_to_country": hire.country,
            "dry_run": self.dry_run,
        }
        self.assignments_by_email[hire.work_email] = assignment
        LOGGER.info("Mock Iru blueprint %s prepared for %s", blueprint, hire.work_email)
        return {"status": "assigned", "assignment": assignment, "idempotent": False}
