"""Tool: analyse URL structure without any network access.

HARD RULE 1: this module must never call httpx, requests, socket, DNS, or a
headless browser. It only parses the string the user pasted.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from app.schemas.tools import AnalyzeUrlStructureInput, AnalyzeUrlStructureOutput
from app.tools.inspect_indicators import is_ip_literal, normalize_url

# Words attackers commonly put in a host or path to look trustworthy.
_LURE_WORDS = ("login", "log-in", "signin", "sign-in", "secure", "verify", "account", "update", "payroll", "billing", "invoice", "reset", "password", "wallet")

# Homoglyph-style digit substitutions seen in lookalike domains.
_DIGIT_LOOKALIKES = ("0", "1", "3", "5")

_MAX_SUBDOMAINS = 3
_MAX_HOST_LENGTH = 40


def defang(url: str) -> str:
    """Return a non-clickable display form, e.g. `hxxps://host[.]tld/path`."""
    text = url.strip()
    if text.lower().startswith("https://"):
        text = f"hxxps://{text[8:]}"
    elif text.lower().startswith("http://"):
        text = f"hxxp://{text[7:]}"
    return text.replace(".", "[.]").replace("@", "[at]")


async def analyze_url_structure(
    payload: AnalyzeUrlStructureInput,
) -> AnalyzeUrlStructureOutput:
    """Parse scheme/host/port/path and produce a defanged display form.

    Observations flag, without resolving anything:
    - IP-literal hosts (e.g. 192.0.2.45);
    - punycode (xn--) or mixed-script lookalikes;
    - excessive subdomains or a very long hostname;
    - userinfo tricks (user@host) and non-default ports;
    - a host or path that contradicts the visible anchor text;
    - plain http on a message that asks for sign-in or payment.
    """
    raw = payload.url.strip()
    normalized = normalize_url(raw)
    observations: list[str] = []

    try:
        parts = urlsplit(normalized)
    except ValueError:
        return AnalyzeUrlStructureOutput(
            url=raw,
            defanged=defang(raw),
            observations=["The URL could not be parsed as a valid address."],
        )

    host = (parts.hostname or "").lower()
    scheme = parts.scheme.lower()
    port = parts.port
    path = parts.path or ""

    # --- structural observations ------------------------------------------
    if is_ip_literal(host):
        observations.append(
            "The host is a raw IP address, not a domain name - unusual for a "
            "legitimate service."
        )

    if "xn--" in host:
        observations.append(
            "The host uses punycode (xn--), which can hide lookalike characters."
        )

    if host.count(".") > _MAX_SUBDOMAINS:
        observations.append(
            f"The host has {host.count('.')} labels; deep subdomains are often used to "
            "push the real domain out of view."
        )

    if len(host) > _MAX_HOST_LENGTH:
        observations.append(f"The hostname is unusually long ({len(host)} characters).")

    if "@" in normalized.split("://", 1)[-1].split("/", 1)[0]:
        observations.append(
            "The URL contains userinfo (user@host); the part before @ is not the real host."
        )

    if port is not None and port not in (80, 443):
        observations.append(f"The URL uses a non-standard port ({port}).")

    lowered_host_and_path = f"{host}{path}".lower()
    lure_hits = sorted({word for word in _LURE_WORDS if word in lowered_host_and_path})
    if lure_hits:
        observations.append(
            "The host or path contains sign-in or payment wording ("
            + ", ".join(lure_hits)
            + "), which is common in credential-harvesting pages."
        )

    if scheme == "http" and lure_hits:
        observations.append(
            "The link uses plain http (no encryption) while asking for sensitive details."
        )

    if any(char in host for char in _DIGIT_LOOKALIKES) and not is_ip_literal(host):
        observations.append(
            "The host contains digits, which can mimic letters in a lookalike domain."
        )

    # --- visible text vs real host ----------------------------------------
    visible = (payload.visible_text or "").strip()
    if visible:
        visible_normalized = normalize_url(visible)
        if "://" in visible_normalized:
            visible_host = (urlsplit(visible_normalized).hostname or "").lower()
            if visible_host and visible_host != host:
                observations.append(
                    f"The visible link text points at {visible_host} but the address is {host}."
                )
        elif visible.lower() not in normalized.lower():
            observations.append(
                "The visible link text does not match the address it points at."
            )

    return AnalyzeUrlStructureOutput(
        url=raw,
        defanged=defang(raw),
        scheme=scheme,
        host=host,
        port=port,
        path=path,
        is_ip_literal=is_ip_literal(host),
        observations=observations,
    )
