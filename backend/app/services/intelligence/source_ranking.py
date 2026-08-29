from dataclasses import dataclass
from urllib.parse import urlparse

from app.services.intelligence.task_types import TaskDomain


@dataclass(frozen=True)
class SourceScore:
    score: float
    tier: int
    reason: str


class SourceRanker:

    OFFICIAL_DOMAINS = {
        "ecb.europa.eu": 1.00,
        "destatis.de": 1.00,
        "bundesbank.de": 1.00,
        "eurostat.ec.europa.eu": 1.00,
        "ec.europa.eu": 0.98,
        "bundesregierung.de": 0.98,
        "bundesfinanzministerium.de": 0.98,
        "gesetze-im-internet.de": 0.98,
        "rosstat.gov.ru": 1.00,
        "cbr.ru": 1.00,
        "government.ru": 0.98,
        "nalog.gov.ru": 0.98,
        "mof.gov.ru": 0.98,
        "imf.org": 0.95,
        "worldbank.org": 0.95,
        "oecd.org": 0.95,
        "bis.org": 0.95,
    }

    FINANCIAL_DOMAINS = {
        "reuters.com": 0.90,
        "bloomberg.com": 0.90,
        "ft.com": 0.90,
        "wsj.com": 0.88,
        "marketwatch.com": 0.82,
        "tradingeconomics.com": 0.75,
    }

    CRYPTO_DOMAINS = {
        "coingecko.com": 0.85,
        "coinmarketcap.com": 0.85,
        "defillama.com": 0.90,
        "glassnode.com": 0.88,
    }

    def rank(
        self,
        url: str | None,
        domain: TaskDomain,
    ) -> SourceScore:

        if not url:
            return SourceScore(
                score=0.20,
                tier=5,
                reason="No source URL available.",
            )

        hostname = (
            urlparse(url)
            .hostname
            or ""
        ).lower()

        hostname = hostname.removeprefix("www.")

        if hostname in self.OFFICIAL_DOMAINS:
            score = self.OFFICIAL_DOMAINS[hostname]

            return SourceScore(
                score=score,
                tier=1,
                reason="Official or primary institutional source.",
            )

        if domain == TaskDomain.CRYPTO:
            if hostname in self.CRYPTO_DOMAINS:
                return SourceScore(
                    score=self.CRYPTO_DOMAINS[hostname],
                    tier=2,
                    reason="Relevant crypto data provider.",
                )

        if hostname in self.FINANCIAL_DOMAINS:
            return SourceScore(
                score=self.FINANCIAL_DOMAINS[hostname],
                tier=3,
                reason="Established financial or market source.",
            )

        if hostname.endswith(".gov"):
            return SourceScore(
                score=0.92,
                tier=1,
                reason="Government source.",
            )

        if hostname.endswith(".gov.uk"):
            return SourceScore(
                score=0.92,
                tier=1,
                reason="Government source.",
            )

        if hostname.endswith(".europa.eu"):
            return SourceScore(
                score=0.95,
                tier=1,
                reason="European Union institutional source.",
            )

        if hostname.endswith(".de"):
            return SourceScore(
                score=0.55,
                tier=4,
                reason="German-domain secondary source.",
            )

        return SourceScore(
            score=0.30,
            tier=5,
            reason="Unknown or secondary source.",
        )
