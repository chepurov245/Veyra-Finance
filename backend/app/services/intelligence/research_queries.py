from __future__ import annotations

from app.services.intelligence.task_types import TaskDomain


class ResearchQueryBuilder:

    def build(
        self,
        message: str,
        domain: TaskDomain,
        has_workspace: bool = False,
    ) -> list[str]:

        message = message.strip()

        if not message:
            return []

        queries: list[str] = []

        if domain == TaskDomain.COMPANY_FINANCE:
            queries.extend([
                self._company_macro(message),
                self._company_market(message),
                self._company_regulation(message),
                self._company_industry(message),
            ])

            if has_workspace:
                queries.append(
                    self._company_external_risks(message)
                )

        elif domain == TaskDomain.PERSONAL_FINANCE:
            queries.extend([
                self._personal_economy(message),
                self._personal_rates(message),
                self._personal_regulation(message),
            ])

        elif domain == TaskDomain.MACROECONOMICS:
            queries.extend([
                f"{message} официальная статистика текущие данные",
                f"{message} центральный банк официальные данные",
                f"{message} экономический контекст последние данные",
            ])

        elif domain == TaskDomain.STOCKS:
            queries.extend([
                f"{message} текущая цена рынок финансовые показатели",
                f"{message} официальная отчетность фундаментальные показатели",
                f"{message} текущий рыночный и экономический контекст",
            ])

        elif domain == TaskDomain.CRYPTO:
            queries.extend([
                f"{message} текущая цена объем капитализация",
                f"{message} blockchain on-chain data current",
                f"{message} текущий рынок регулирование риски",
            ])

        elif domain == TaskDomain.LIQUIDITY_POOLS:
            queries.extend([
                f"{message} TVL liquidity volume fees current",
                f"{message} yield historical performance",
                f"{message} impermanent loss smart contract risk",
            ])

        elif domain == TaskDomain.GEOPOLITICS:
            queries.extend([
                f"{message} последние подтвержденные события",
                f"{message} экономические последствия текущие данные",
                f"{message} влияние на рынки и бизнес",
            ])

        elif domain == TaskDomain.FORECASTING:
            queries.extend([
                f"{message} historical data",
                f"{message} current economic market conditions",
                f"{message} current risks scenarios",
            ])

        else:
            queries.append(message)

        return self._deduplicate(queries)

    @staticmethod
    def _company_macro(message: str) -> str:
        return (
            f"{message}\n\n"
            "Исследуй внешнюю макроэкономическую среду, "
            "которая может повлиять на компанию. "
            "Используй актуальные фактические данные: "
            "инфляция, процентные ставки, ВВП, рынок труда, "
            "валютные курсы и другие релевантные показатели. "
            "Приоритет официальным источникам."
        )

    @staticmethod
    def _company_market(message: str) -> str:
        return (
            f"{message}\n\n"
            "Исследуй текущие рыночные условия, "
            "которые могут повлиять на бизнес компании: "
            "спрос, цены, стоимость капитала, финансовые рынки, "
            "валюты и другие релевантные факторы."
        )

    @staticmethod
    def _company_regulation(message: str) -> str:
        return (
            f"{message}\n\n"
            "Исследуй актуальные регуляторные, налоговые "
            "и законодательные изменения, которые могут "
            "материально повлиять на компанию. "
            "Используй официальные государственные источники "
            "и первичные публикации."
        )

    @staticmethod
    def _company_industry(message: str) -> str:
        return (
            f"{message}\n\n"
            "Исследуй текущую ситуацию в отрасли компании: "
            "рост рынка, спрос, конкуренцию, ключевые тренды, "
            "изменения стоимости ресурсов и другие факторы, "
            "которые могут повлиять на финансовый результат."
        )

    @staticmethod
    def _company_external_risks(message: str) -> str:
        return (
            f"{message}\n\n"
            "Выяви внешние риски для компании: "
            "экономические, рыночные, регуляторные, "
            "геополитические и отраслевые факторы. "
            "Используй актуальные подтвержденные данные."
        )

    @staticmethod
    def _personal_economy(message: str) -> str:
        return (
            f"{message}\n\n"
            "Исследуй актуальную экономическую среду, "
            "которая может повлиять на личные финансы."
        )

    @staticmethod
    def _personal_rates(message: str) -> str:
        return (
            f"{message}\n\n"
            "Исследуй актуальные процентные ставки, "
            "инфляцию и валютные факторы, релевантные "
            "для личных финансов."
        )

    @staticmethod
    def _personal_regulation(message: str) -> str:
        return (
            f"{message}\n\n"
            "Исследуй актуальные налоговые и регуляторные "
            "изменения, релевантные для личных финансов."
        )

    @staticmethod
    def _deduplicate(
        queries: list[str],
    ) -> list[str]:

        result: list[str] = []
        seen: set[str] = set()

        for query in queries:
            normalized = " ".join(
                query.lower().split()
            )

            if normalized in seen:
                continue

            seen.add(normalized)
            result.append(query)

        return result
