"""Tool: inspect deterministic indicators in message text.

Text-only. Never fetch, visit, or resolve URLs (hard rule 1).
"""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

from app.schemas.common import Evidence, Indicator, IndicatorStatus
from app.schemas.tools import InspectIndicatorsInput, InspectIndicatorsOutput
from app.services.evidence import find_all_evidence, first_evidence

# --- Patterns --------------------------------------------------------------
# Accepts both live-looking URLs and pre-defanged ones (hxxps://host[.]tld).
_URL_RE = re.compile(
    r"(?:hxxps?|https?|ftp)://[^\s<>\"'{}]+",
    re.IGNORECASE,
)

_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")

# --- Keyword sets ----------------------------------------------------------
_URGENCY = [
    "immediately",
    "urgent",
    "urgently",
    "act now",
    "as soon as possible",
    "asap",
    "right away",
    "within 24 hours",
    "within 48 hours",
    "final notice",
    "last warning",
    "expires today",
    "expires tomorrow",
    "today",
    "deadline",
    "time-sensitive",
]

_CREDENTIAL = [
    "password",
    "reset your",
    "reset it",
    "sign in",
    "sign-in",
    "log in",
    "login",
    "log-in",
    "verify your account",
    "verify your identity",
    "confirm your identity",
    "confirm your account",
    "username and password",
    "one-time code",
    "one time code",
    "otp",
    "mfa",
    "2fa",
    "two-factor",
    "credentials",
    "authenticate",
]

_PAYMENT = [
    "bank details",
    "bank account",
    "account number",
    "sort code",
    "iban",
    "swift",
    "wire transfer",
    "bank transfer",
    "remittance",
    "change of bank",
    "payment details",
    "invoice",
    "pay the attached",
    "payment",
]

_ATTACHMENT = [
    "attached",
    "attachment",
    "see the file",
    "open the file",
    "download the file",
    ".pdf",
    ".docx",
    ".doc",
    ".xlsx",
    ".zip",
    ".rar",
    ".iso",
]


def is_assessable_text(message: str, *, min_chars: int = 25) -> bool:
    """True when there is enough text to assess responsibly.

    Below the threshold the agent must ask a clarifying question instead of
    guessing (see the system prompt's rule 8).
    """
    stripped = message.strip()
    if len(stripped) < min_chars:
        return False
    return any(char.isalpha() for char in stripped)


def normalize_url(token: str) -> str:
    """Undo common defanging so a pasted URL can be parsed structurally."""
    return (
        token.strip()
        .replace("[.]", ".")
        .replace("(.)", ".")
        .replace("{.}", ".")
        .replace("[at]", "@")
        .replace("hxxps://", "https://")
        .replace("hxxp://", "http://")
    )


def extract_urls(message: str) -> list[str]:
    """Return every URL-like token in the message, normalised for parsing."""
    urls: list[str] = []
    for match in _URL_RE.finditer(message):
        token = match.group(0)
        # Skip obviously broken defanged forms that end with "[.]" and nothing after
        if token.rstrip().endswith("[.]"):
            continue
        urls.append(normalize_url(token))
    return urls


def _url_host(url: str) -> str:
    """Return the host of a URL, lower-cased, or '' when it cannot be parsed."""
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def is_ip_literal(host: str) -> bool:
    """True when the host is an IPv4/IPv6 literal rather than a domain name."""
    if not host:
        return False
    if _IPV4_RE.match(host):
        try:
            ipaddress.IPv4Address(host)
        except ValueError:
            return False
        return True
    try:
        ipaddress.IPv6Address(host)
    except ValueError:
        return False
    return True


def registrable_domain(host: str) -> str:
    """Approximate the registrable domain (last two labels) of a host."""
    if not host or is_ip_literal(host):
        return host
    labels = host.split(".")
    return ".".join(labels[-2:]) if len(labels) >= 2 else host


def _keyword_indicator(
    message: str,
    *,
    indicator_id: str,
    label: str,
    keywords: list[str],
    detail_when_detected: str,
    detail_when_absent: str,
) -> Indicator:
    """Build an indicator from a keyword list plus its quoted evidence."""
    evidence = first_evidence(message, keywords, limit=2)
    if evidence:
        return Indicator(
            id=indicator_id,
            label=label,
            status=IndicatorStatus.DETECTED,
            detail=detail_when_detected,
            evidence=evidence,
        )
    return Indicator(
        id=indicator_id,
        label=label,
        status=IndicatorStatus.NOT_DETECTED,
        detail=detail_when_absent,
        evidence=[],
    )


async def inspect_indicators(payload: InspectIndicatorsInput) -> InspectIndicatorsOutput:
    """Return the four core indicators plus extras, each with evidence offsets.

    Core indicators:
    - link_present: any URL-like token in the text;
    - sender_domain_mismatch: display name/domain disagrees with the link host;
    - urgency_language: deadlines, threats, "immediately", etc.;
    - credential_request: password/MFA/payment-detail requests.

    Extras: payment_change, attachment_present, ip_literal_host.

    This is heuristic and deliberately conservative: a keyword that is not
    present is `not_detected`, and anything that cannot be decided from the text
    alone is `not_assessable`. It never emits a "safe" status.
    """
    message = payload.message
    sender = (payload.sender or "").strip()

    if not is_assessable_text(message):
        not_assessable = [
            Indicator(
                id=indicator_id,
                label=label,
                status=IndicatorStatus.NOT_ASSESSABLE,
                detail="Not assessable: the message is too short to analyse.",
                evidence=[],
            )
            for indicator_id, label in (
                ("link_present", "Link present"),
                ("sender_domain_mismatch", "Sender/domain mismatch"),
                ("urgency_language", "Urgency language"),
                ("credential_request", "Credential request"),
            )
        ]
        return InspectIndicatorsOutput(
            indicators=not_assessable,
            urls=[],
            notes=["Message is too short for reliable indicator extraction."],
        )

    urls = extract_urls(message)
    hosts = [host for host in (_url_host(url) for url in urls) if host]

    # --- link_present ------------------------------------------------------
    if urls:
        evidence: list[Evidence] = []
        for match in _URL_RE.finditer(message):
            span = Evidence(start=match.start(), end=match.end(), text=match.group(0))
            if span not in evidence:
                evidence.append(span)
        link_indicator = Indicator(
            id="link_present",
            label="Link present",
            status=IndicatorStatus.DETECTED,
            detail=f"{len(urls)} link(s) found in the text. None were opened.",
            evidence=evidence[:2],
        )
    else:
        link_indicator = Indicator(
            id="link_present",
            label="Link present",
            status=IndicatorStatus.NOT_DETECTED,
            detail="No URL-like text was found.",
            evidence=[],
        )

    # --- sender_domain_mismatch -------------------------------------------
    mismatch_indicator = _sender_mismatch_indicator(message, sender, urls, hosts)

    # --- keyword indicators ------------------------------------------------
    urgency = _keyword_indicator(
        message,
        indicator_id="urgency_language",
        label="Urgency language",
        keywords=_URGENCY,
        detail_when_detected="The message pressures the reader to act quickly.",
        detail_when_absent="No urgency or deadline wording was found.",
    )
    credential = _keyword_indicator(
        message,
        indicator_id="credential_request",
        label="Credential request",
        keywords=_CREDENTIAL,
        detail_when_detected="The message asks for sign-in details, a password, or a code.",
        detail_when_absent="No request for credentials was found.",
    )
    payment = _keyword_indicator(
        message,
        indicator_id="payment_change",
        label="Payment or bank-detail change",
        keywords=_PAYMENT,
        detail_when_detected="The message mentions payment or bank-detail changes.",
        detail_when_absent="No payment or bank-detail wording was found.",
    )
    attachment = _keyword_indicator(
        message,
        indicator_id="attachment_present",
        label="Attachment mentioned",
        keywords=_ATTACHMENT,
        detail_when_detected="The message refers to an attachment or a file to open.",
        detail_when_absent="No attachment was mentioned.",
    )

    # --- ip_literal_host ---------------------------------------------------
    ip_hosts = [host for host in hosts if is_ip_literal(host)]
    if ip_hosts:
        ip_evidence = [
            Evidence(start=match.start(), end=match.end(), text=match.group(0))
            for match in _URL_RE.finditer(message)
            if is_ip_literal(_url_host(normalize_url(match.group(0))))
        ]
        ip_indicator = Indicator(
            id="ip_literal_host",
            label="Link uses a raw IP address",
            status=IndicatorStatus.DETECTED,
            detail="A link points at an IP address instead of a named domain.",
            evidence=ip_evidence[:2],
        )
    else:
        ip_indicator = Indicator(
            id="ip_literal_host",
            label="Link uses a raw IP address",
            status=IndicatorStatus.NOT_DETECTED,
            detail="No link pointed at a raw IP address.",
            evidence=[],
        )

    return InspectIndicatorsOutput(
        indicators=[
            link_indicator,
            mismatch_indicator,
            urgency,
            credential,
            payment,
            attachment,
            ip_indicator,
        ],
        urls=urls,
        notes=[],
    )


def _sender_mismatch_indicator(
    message: str, sender: str, urls: list[str], hosts: list[str]
) -> Indicator:
    """Compare the sender's domain with the hosts linked in the message."""
    indicator_id = "sender_domain_mismatch"
    label = "Sender/domain mismatch"

    if not urls:
        return Indicator(
            id=indicator_id,
            label=label,
            status=IndicatorStatus.NOT_ASSESSABLE,
            detail="No link to compare against the sender.",
            evidence=[],
        )

    sender_host = ""
    if "@" in sender:
        sender_host = sender.rsplit("@", 1)[1].strip().strip(">").lower()
    if not sender_host:
        return Indicator(
            id=indicator_id,
            label=label,
            status=IndicatorStatus.NOT_ASSESSABLE,
            detail="No sender address was provided, so it cannot be compared with the link.",
            evidence=[],
        )

    sender_domain = registrable_domain(sender_host)
    mismatched = [
        host for host in hosts if registrable_domain(host) and registrable_domain(host) != sender_domain
    ]

    if mismatched:
        evidence: list[Evidence] = []
        for match in _URL_RE.finditer(message):
            if registrable_domain(_url_host(normalize_url(match.group(0)))) in mismatched:
                span = Evidence(start=match.start(), end=match.end(), text=match.group(0))
                if span not in evidence:
                    evidence.append(span)
        return Indicator(
            id=indicator_id,
            label=label,
            status=IndicatorStatus.DETECTED,
            detail=(
                f"The sender claims to be {sender_host} but the link points at "
                f"{', '.join(sorted(set(mismatched)))}."
            ),
            evidence=evidence[:2],
        )

    return Indicator(
        id=indicator_id,
        label=label,
        status=IndicatorStatus.NOT_DETECTED,
        detail=f"The link host matches the sender domain ({sender_domain}).",
        evidence=[],
    )


__all__ = [
    "extract_urls",
    "find_all_evidence",
    "inspect_indicators",
    "is_assessable_text",
    "is_ip_literal",
    "normalize_url",
    "registrable_domain",
]
