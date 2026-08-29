from enum import IntEnum
from urllib.parse import urlparse


class SourceReliability(IntEnum):
    UNKNOWN = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    PRIMARY = 4


PRIMARY_DOMAINS = {
    # Russia
    "cbr.ru",
    "rosstat.gov.ru",
    "government.ru",
    "nalog.gov.ru",
    "mof.gov.ru",

    # Germany
    "destatis.de",
    "bundesbank.de",
    "bundesregierung.de",
    "bundesfinanzministerium.de",
    "gesetze-im-internet.de",

    # European Union
    "ecb.europa.eu",
    "ec.europa.eu",
    "eurostat.ec.europa.eu",

    # United States
    "sec.gov",
    "treasury.gov",
    "federalreserve.gov",
    "nasdaq.com",

    # International institutions
    "worldbank.org",
    "imf.org",
    "oecd.org",
    "bis.org",

    # Markets
    "moex.com",
}


HIGH_RELIABILITY_DOMAINS = {
    "reuters.com",
    "bloomberg.com",
    "ft.com",
    "wsj.com",
    "apnews.com",
    "bbc.com",
}


def _normalize_hostname(
    url: str | None,
) -> str | None:

    if not url:
        return None

    try:
        hostname = urlparse(url).hostname
    except ValueError:
        return None

    if not hostname:
        return None

    return hostname.lower().removeprefix("www.")


def classify_source(
    url: str | None,
) -> SourceReliability:

    hostname = _normalize_hostname(url)

    if not hostname:
        return SourceReliability.UNKNOWN

    if hostname in PRIMARY_DOMAINS:
        return SourceReliability.PRIMARY

    if hostname in HIGH_RELIABILITY_DOMAINS:
        return SourceReliability.HIGH

    # Government domains
    if (
        hostname.endswith(".gov")
        or hostname.endswith(".gov.uk")
    ):
        return SourceReliability.PRIMARY

    # European Union institutional domains
    if hostname.endswith(".europa.eu"):
        return SourceReliability.PRIMARY

    return SourceReliability.MEDIUM


def reliability_label(
    reliability: SourceReliability,
) -> str:

    return reliability.name.lower()
