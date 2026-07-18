"""Role, department, country, and device blueprint mapping.

Mappings are intentionally allowlist based. The automation never accepts group
names from the CSV because that would allow a bad or malformed file to assign
privileged access.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set


BASELINE_OKTA_GROUPS = ("okta-group-all-employees",)
BASELINE_GOOGLE_GROUPS = ("all@balto.com", "security-training@balto.com")


@dataclass(frozen=True)
class RoleAccess:
    """Access profile derived from job title and department."""

    name: str
    okta_groups: Sequence[str]
    privileged: bool
    requires_manager_approval: bool
    rationale: str


@dataclass(frozen=True)
class DepartmentAccess:
    """Google groups and endpoint blueprint derived from department."""

    department: str
    google_groups: Sequence[str]
    iru_blueprint: str
    privileged_department: bool
    rationale: str


@dataclass(frozen=True)
class CountryPolicy:
    """Country support policy used by HR and IT onboarding checks."""

    country: str
    supported: bool
    requires_review: bool
    notes: str


ROLE_PATTERNS: List[tuple[re.Pattern[str], str, RoleAccess]] = [
    (
        re.compile(r"\b(engineering manager|software engineering manager)\b", re.I),
        "Engineering",
        RoleAccess(
            name="Engineering Manager",
            okta_groups=(
                *BASELINE_OKTA_GROUPS,
                "okta-group-engineering-baseline",
                "okta-group-github-standard",
                "okta-group-eng-manager",
            ),
            privileged=True,
            requires_manager_approval=True,
            rationale="Engineering managers need engineering systems but should not receive production admin by default.",
        ),
    ),
    (
        re.compile(r"\b(senior software engineer|software engineer|backend engineer|frontend engineer)\b", re.I),
        "Engineering",
        RoleAccess(
            name="Software Engineer",
            okta_groups=(
                *BASELINE_OKTA_GROUPS,
                "okta-group-engineering-baseline",
                "okta-group-github-standard",
                "okta-group-dev-tools",
            ),
            privileged=True,
            requires_manager_approval=True,
            rationale="Engineering access can include source code and development systems.",
        ),
    ),
    (
        re.compile(r"\b(account executive|sales development representative|sdr)\b", re.I),
        "Sales",
        RoleAccess(
            name="Sales",
            okta_groups=(
                *BASELINE_OKTA_GROUPS,
                "okta-group-sales-baseline",
                "okta-group-crm-standard",
            ),
            privileged=False,
            requires_manager_approval=False,
            rationale="Sales users need standard CRM access without admin privileges.",
        ),
    ),
    (
        re.compile(r"\b(customer success manager|implementation manager|support specialist)\b", re.I),
        "Customer Success",
        RoleAccess(
            name="Customer Success",
            okta_groups=(
                *BASELINE_OKTA_GROUPS,
                "okta-group-cs-baseline",
                "okta-group-support-standard",
            ),
            privileged=False,
            requires_manager_approval=False,
            rationale="Customer-facing teams need customer workflow tools with standard permissions.",
        ),
    ),
    (
        re.compile(r"\b(finance|accounting|controller)\b", re.I),
        "Finance",
        RoleAccess(
            name="Finance",
            okta_groups=(
                *BASELINE_OKTA_GROUPS,
                "okta-group-finance-baseline",
                "okta-group-expense-standard",
            ),
            privileged=True,
            requires_manager_approval=True,
            rationale="Finance systems contain sensitive business and employee data.",
        ),
    ),
    (
        re.compile(r"\b(people|hr|human resources|recruiter)\b", re.I),
        "People",
        RoleAccess(
            name="People Operations",
            okta_groups=(
                *BASELINE_OKTA_GROUPS,
                "okta-group-people-baseline",
                "okta-group-hris-standard",
            ),
            privileged=True,
            requires_manager_approval=True,
            rationale="People systems contain personal employee data.",
        ),
    ),
    (
        re.compile(r"\b(it operations|systems administrator|security engineer)\b", re.I),
        "IT",
        RoleAccess(
            name="IT Operations",
            okta_groups=(*BASELINE_OKTA_GROUPS, "okta-group-it-baseline"),
            privileged=True,
            requires_manager_approval=True,
            rationale="IT access is high impact and must be explicitly approved outside automation.",
        ),
    ),
]


DEPARTMENT_ACCESS: Dict[str, DepartmentAccess] = {
    "Engineering": DepartmentAccess(
        department="Engineering",
        google_groups=(*BASELINE_GOOGLE_GROUPS, "engineering@balto.com", "product-engineering@balto.com"),
        iru_blueprint="iru-blueprint-engineering",
        privileged_department=True,
        rationale="Engineering devices need developer tooling and stronger endpoint controls.",
    ),
    "Sales": DepartmentAccess(
        department="Sales",
        google_groups=(*BASELINE_GOOGLE_GROUPS, "sales@balto.com", "revenue@balto.com"),
        iru_blueprint="iru-blueprint-sales",
        privileged_department=False,
        rationale="Sales needs revenue communications and sales tooling.",
    ),
    "Customer Success": DepartmentAccess(
        department="Customer Success",
        google_groups=(*BASELINE_GOOGLE_GROUPS, "customer-success@balto.com", "customers@balto.com"),
        iru_blueprint="iru-blueprint-customer-success",
        privileged_department=False,
        rationale="Customer Success needs customer operations communications.",
    ),
    "Finance": DepartmentAccess(
        department="Finance",
        google_groups=(*BASELINE_GOOGLE_GROUPS, "finance@balto.com", "g-and-a@balto.com"),
        iru_blueprint="iru-blueprint-finance",
        privileged_department=True,
        rationale="Finance devices and groups require stricter handling due to sensitive data.",
    ),
    "People": DepartmentAccess(
        department="People",
        google_groups=(*BASELINE_GOOGLE_GROUPS, "people@balto.com", "g-and-a@balto.com"),
        iru_blueprint="iru-blueprint-people",
        privileged_department=True,
        rationale="People Operations handles personal employee data.",
    ),
    "IT": DepartmentAccess(
        department="IT",
        google_groups=(*BASELINE_GOOGLE_GROUPS, "it@balto.com", "security-alerts@balto.com"),
        iru_blueprint="iru-blueprint-it",
        privileged_department=True,
        rationale="IT endpoint access requires strict approval and auditability.",
    ),
}


COUNTRY_ALIASES: Dict[str, str] = {
    "us": "United States",
    "usa": "United States",
    "united states": "United States",
    "canada": "Canada",
    "ca": "Canada",
    "uk": "United Kingdom",
    "united kingdom": "United Kingdom",
    "ireland": "Ireland",
    "germany": "Germany",
    "de": "Germany",
    "netherlands": "Netherlands",
    "india": "India",
    "in": "India",
    "australia": "Australia",
    "au": "Australia",
}


def resolve_role_access(job_title: str, department: str) -> RoleAccess:
    """Resolve the least-privilege access profile for a job title."""

    normalized_department = normalize_department(department)
    for pattern, expected_department, access in ROLE_PATTERNS:
      if pattern.search(job_title) and (normalized_department == expected_department or expected_department == "Any"):
          return access

    return RoleAccess(
        name="Unknown role",
        okta_groups=BASELINE_OKTA_GROUPS,
        privileged=False,
        requires_manager_approval=True,
        rationale="Unknown roles receive baseline access only until a manager confirms required systems.",
    )


def resolve_department_access(department: str) -> DepartmentAccess:
    """Resolve Google groups and Iru blueprint for a department."""

    normalized = normalize_department(department)
    return DEPARTMENT_ACCESS.get(
        normalized,
        DepartmentAccess(
            department="Unknown",
            google_groups=BASELINE_GOOGLE_GROUPS,
            iru_blueprint="iru-blueprint-baseline",
            privileged_department=False,
            rationale="Unknown departments receive baseline access only.",
        ),
    )


def normalize_department(department: str) -> str:
    """Normalize common department aliases."""

    normalized = " ".join(department.strip().split()).lower()
    aliases = {
        "eng": "Engineering",
        "engineering": "Engineering",
        "sales": "Sales",
        "customer success": "Customer Success",
        "cs": "Customer Success",
        "support": "Customer Success",
        "finance": "Finance",
        "accounting": "Finance",
        "people": "People",
        "hr": "People",
        "human resources": "People",
        "it": "IT",
        "information technology": "IT",
        "security": "IT",
    }
    return aliases.get(normalized, department.strip())


def normalize_country(country: str) -> str:
    """Normalize country aliases used in HR exports."""

    key = " ".join(country.strip().split()).lower()
    return COUNTRY_ALIASES.get(key, country.strip())


def resolve_country_policy(country: str, allowed_countries: Iterable[str]) -> CountryPolicy:
    """Return the support policy for a country."""

    normalized = normalize_country(country)
    allowed: Set[str] = {normalize_country(item) for item in allowed_countries}
    supported = normalized in allowed
    requires_review = not supported

    if normalized in {"Ireland", "Germany", "Netherlands"}:
        return CountryPolicy(
            country=normalized,
            supported=supported,
            requires_review=requires_review,
            notes="EU privacy considerations apply; confirm regional policy acknowledgement.",
        )

    if normalized in {"India", "Australia"}:
        return CountryPolicy(
            country=normalized,
            supported=supported,
            requires_review=requires_review,
            notes="Confirm device logistics and regional policy acknowledgement.",
        )

    return CountryPolicy(
        country=normalized,
        supported=supported,
        requires_review=requires_review,
        notes="Standard onboarding country." if supported else "Country requires HR, Legal, Finance, and IT review.",
    )


def unique_preserving_order(values: Sequence[str]) -> List[str]:
    """Deduplicate group names while preserving order for readable reports."""

    seen: Set[str] = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result
