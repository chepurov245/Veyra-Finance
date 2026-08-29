from app.services.intelligence.task_types import (
    AnalysisTask,
    TaskDomain,
)


class TaskRouter:
    def route(
        self,
        message: str,
        has_workspace: bool = False,
    ) -> AnalysisTask:
        text = message.lower()

        financial_words = (
            "деньги",
            "доход",
            "расход",
            "расходы",
            "прибыль",
            "выручка",
            "бюджет",
            "налог",
            "зарплата",
            "затраты",
            "ликвидность",
            "cash flow",
            "ebitda",
            "баланс",
            "потратил",
            "потратил",
            "трат",
            "транзакц",
        )

        market_words = (
            "рынок",
            "индекс",
            "акции",
            "акция",
            "s&p",
            "nasdaq",
            "мосбиржа",
            "облигации",
        )

        crypto_words = (
            "крипто",
            "bitcoin",
            "биткоин",
            "ethereum",
            "эфир",
            "defi",
            "токен",
        )

        liquidity_pool_words = (
            "пул ликвидности",
            "пулы ликвидности",
            "liquidity pool",
            "liquidity pools",
            "ликвидити пул",
            "ликвидити пулы",
            "lp pool",
        )

        macro_words = (
            "инфляция",
            "ввп",
            "ставка",
            "центробанк",
            "курс валют",
            "доллар",
            "евро",
            "рубль",
            "безработица",
            "экономика",
        )

        geopolitical_words = (
            "политика",
            "геополитика",
            "санкции",
            "война",
            "конфликт",
            "выборы",
            "пошлины",
        )

        forecast_words = (
            "прогноз",
            "прогнозируй",
            "спрогнозируй",
            "перспектив",
            "будет",
            "ожидается",
            "сценарий",
            "прогнозировать",
            "что будет",
        )

        # Прогноз имеет приоритет над тематическим доменом.
        if any(word in text for word in forecast_words):
            return AnalysisTask(
                TaskDomain.FORECASTING,
                requires_web=True,
                requires_market_data=True,
                requires_internal_data=has_workspace,
            )

        # Пулы ликвидности имеют приоритет над общим crypto.
        if any(word in text for word in liquidity_pool_words):
            return AnalysisTask(
                TaskDomain.LIQUIDITY_POOLS,
                requires_web=True,
                requires_market_data=True,
            )

        if any(word in text for word in geopolitical_words):
            return AnalysisTask(
                TaskDomain.GEOPOLITICS,
                requires_web=True,
                requires_market_data=True,
            )

        if any(word in text for word in crypto_words):
            return AnalysisTask(
                TaskDomain.CRYPTO,
                requires_web=True,
                requires_market_data=True,
            )

        if any(word in text for word in market_words):
            return AnalysisTask(
                TaskDomain.STOCKS,
                requires_web=True,
                requires_market_data=True,
            )

        if any(word in text for word in macro_words):
            return AnalysisTask(
                TaskDomain.MACROECONOMICS,
                requires_web=True,
                requires_market_data=True,
            )

        if any(word in text for word in financial_words):
            return AnalysisTask(
                TaskDomain.COMPANY_FINANCE
                if has_workspace
                else TaskDomain.PERSONAL_FINANCE,
                requires_internal_data=has_workspace,
            )

        return AnalysisTask(
            TaskDomain.GENERAL,
            requires_web=False,
        )
