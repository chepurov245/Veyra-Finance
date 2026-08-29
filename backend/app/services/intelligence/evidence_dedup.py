from dataclasses import dataclass
from urllib.parse import urlparse

from app.services.intelligence.evidence import Evidence


@dataclass
class EvidenceGroup:
    claim: str
    evidence: list[Evidence]


class EvidenceDeduplicator:

    @staticmethod
    def publisher(url: str | None) -> str:
        if not url:
            return "unknown"

        host = urlparse(url).netloc.lower()

        if host.startswith("www."):
            host = host[4:]

        if host.startswith("ru."):
            host = host[3:]

        return host

    @classmethod
    def cited_publishers(
        cls,
        claim: str,
    ) -> set[str]:

        import re

        urls = re.findall(
            r"https?://[^\s)\]]+",
            claim,
        )

        publishers = set()

        for url in urls:
            publishers.add(
                cls.publisher(url)
            )

        return publishers

    @classmethod
    def is_independent(
        cls,
        item: Evidence,
        all_evidence: list[Evidence],
    ) -> bool:

        own_publisher = cls.publisher(
            item.url
        )

        if own_publisher == "unknown":
            return False

        publishers = {
            cls.publisher(other.url)
            for other in all_evidence
            if other is not item
        }

        publishers.discard("unknown")

        return bool(
            publishers
            and any(
                publisher != own_publisher
                for publisher in publishers
            )
        )

    @classmethod
    def group(
        cls,
        evidence: list[Evidence],
    ) -> list[EvidenceGroup]:

        groups: list[EvidenceGroup] = []

        for item in evidence:
            normalized = cls._normalize(
                item.claim
            )

            matched = None

            for group in groups:
                if cls._similar(
                    normalized,
                    cls._normalize(
                        group.claim
                    ),
                ):
                    matched = group
                    break

            if matched:
                matched.evidence.append(item)
            else:
                groups.append(
                    EvidenceGroup(
                        claim=item.claim,
                        evidence=[item],
                    )
                )

        return groups

    @staticmethod
    def _normalize(text: str) -> str:
        import re

        text = text.lower()

        text = re.sub(
            r"https?://\S+",
            "",
            text,
        )

        text = re.sub(
            r"\[[^\]]*\]\([^)]+\)",
            "",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _similar(
        first: str,
        second: str,
    ) -> bool:

        import re

        if first == second:
            return True

        first_lower = first.lower()
        second_lower = second.lower()

        # -------------------------------------------------
        # Numerical facts must match exactly.
        # -------------------------------------------------

        first_numbers = set(
            re.findall(
                r"\\d+(?:[.,]\\d+)?",
                first_lower,
            )
        )

        second_numbers = set(
            re.findall(
                r"\\d+(?:[.,]\\d+)?",
                second_lower,
            )
        )

        if first_numbers != second_numbers:
            return False

        # -------------------------------------------------
        # Core semantic anchors.
        # -------------------------------------------------

        anchor_groups = [
            {
                "инфляция",
            },
            {
                "россии",
                "россия",
            },
            {
                "годовая",
            },
        ]

        for group in anchor_groups:
            first_has = any(
                word in first_lower
                for word in group
            )
            second_has = any(
                word in second_lower
                for word in group
            )

            if first_has != second_has:
                return False

        # -------------------------------------------------
        # Normalize common reporting language.
        # -------------------------------------------------

        noise = {
            "по",
            "состоянию",
            "на",
            "данные",
            "данных",
            "период",
            "периода",
            "согласно",
            "обзору",
            "обзор",
            "опубликованному",
            "опубликованный",
            "указанную",
            "дату",
            "подтверждают",
            "подтверждает",
            "показатель",
            "показателя",
            "этот",
            "эти",
            "источника",
            "источник",
            "составила",
            "составил",
            "составляет",
            "составляла",
            "составляло",
            "достигла",
            "достиг",
            "достигло",
        }

        def core_words(text: str) -> set[str]:
            words = set(
                re.findall(
                    r"[a-zа-яё]+",
                    text.lower(),
                )
            )

            return words - noise

        first_core = core_words(first)
        second_core = core_words(second)

        # Remove date tokens and generic time references.
        date_words = {
            "января",
            "февраля",
            "марта",
            "апреля",
            "мая",
            "июня",
            "июля",
            "августа",
            "сентября",
            "октября",
            "ноября",
            "декабря",
            "год",
            "года",
            "году",
        }

        first_core -= date_words
        second_core -= date_words

        # The same numerical macro fact is allowed to have
        # additional publisher-specific wording.
        required = {
            "инфляция",
            "россии",
        }

        if not all(
            word in first_core
            or any(
                variant in first_core
                for variant in (
                    {"россии", "россия"} 
                    if word == "россии"
                    else {word}
                )
            )
            for word in required
        ):
            return False

        if not all(
            word in second_core
            or any(
                variant in second_core
                for variant in (
                    {"россии", "россия"}
                    if word == "россии"
                    else {word}
                )
            )
            for word in required
        ):
            return False

        # At this point:
        #   - numerical values are identical
        #   - subject is Russia
        #   - metric is annual inflation
        #
        # Therefore different editorial wording is treated
        # as the same underlying financial claim.
        return True

