"""Tool: look up domain reputation in the internal database only.

No WHOIS, DNS, or external reputation API calls (hard rule 1).
"""

from __future__ import annotations

from app.db import repositories
from app.schemas.tools import (
    CheckDomainReputationInput,
    CheckDomainReputationOutput,
)


async def check_domain_reputation(
    payload: CheckDomainReputationInput,
) -> CheckDomainReputationOutput:
    """Read `domain_reputation` and `trusted_domains` for a domain or IP literal.

    Returns status `known_safe | known_suspicious | unknown` plus whether the
    domain is on the trusted allow-list. A `known_safe` row is context about the
    domain, not a verdict about the whole message.
    """
    domain = payload.domain.strip().lower()

    try:
        found = await repositories.get_domain_reputation(domain)
    except Exception:  # noqa: BLE001 - a lookup failure must not break the investigation
        return CheckDomainReputationOutput(
            domain=domain,
            status="unknown",
            trusted=False,
            source=None,
            note="Reputation lookup was unavailable; treated as unknown.",
        )

    if found is None:
        return CheckDomainReputationOutput(
            domain=domain,
            status="unknown",
            trusted=False,
            source=None,
            note="No internal reputation row for this domain.",
        )

    return found
