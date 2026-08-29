from dataclasses import dataclass, field

from app.services.intelligence.task_types import TaskDomain


@dataclass(frozen=True)
class ResearchSource:
    name: str
    source_type: str
    required: bool = True


@dataclass(frozen=True)
class ResearchStep:
    name: str
    description: str
    sources: tuple[ResearchSource, ...] = ()


@dataclass
class ResearchPlan:
    domain: TaskDomain
    steps: list[ResearchStep] = field(default_factory=list)
    requires_web: bool = False
    requires_market_data: bool = False
    requires_internal_data: bool = False


class ResearchPlanner:

    def create_plan(
        self,
        domain: TaskDomain,
        message: str,
        has_workspace: bool = False,
    ) -> ResearchPlan:

        if domain == TaskDomain.MACROECONOMICS:
            return self._macro_plan(has_workspace)

        if domain == TaskDomain.STOCKS:
            return self._stocks_plan()

        if domain == TaskDomain.CRYPTO:
            return self._crypto_plan()

        if domain == TaskDomain.LIQUIDITY_POOLS:
            return self._liquidity_pool_plan()

        if domain == TaskDomain.GEOPOLITICS:
            return self._geopolitics_plan()

        if domain == TaskDomain.FORECASTING:
            return self._forecast_plan(has_workspace)

        if domain == TaskDomain.PERSONAL_FINANCE:
            return self._personal_finance_plan(
                has_workspace
            )

        if domain == TaskDomain.COMPANY_FINANCE:
            return self._company_finance_plan(
                has_workspace
            )

        return ResearchPlan(
            domain=TaskDomain.GENERAL,
            steps=[
                ResearchStep(
                    name="web_context",
                    description=(
                        "Search the web for relevant current "
                        "information when the question may "
                        "benefit from external facts."
                    ),
                    sources=(
                        ResearchSource(
                            "web_research",
                            "web",
                        ),
                    ),
                ),
            ],
            requires_web=True,
            requires_internal_data=has_workspace,
        )

    # -----------------------------------------------------
    # MACROECONOMICS
    # -----------------------------------------------------

    def _macro_plan(
        self,
        has_workspace: bool,
    ) -> ResearchPlan:

        steps = [
            ResearchStep(
                name="official_statistics",
                description=(
                    "Collect current official macroeconomic "
                    "indicators relevant to the requested "
                    "country and period."
                ),
                sources=(
                    ResearchSource(
                        "official_statistics",
                        "web",
                    ),
                ),
            ),
            ResearchStep(
                name="central_bank",
                description=(
                    "Collect monetary policy, interest-rate "
                    "and central-bank information."
                ),
                sources=(
                    ResearchSource(
                        "central_bank",
                        "web",
                    ),
                ),
            ),
            ResearchStep(
                name="market_context",
                description=(
                    "Collect relevant market and currency data."
                ),
                sources=(
                    ResearchSource(
                        "market_data",
                        "market",
                    ),
                ),
            ),
            ResearchStep(
                name="economic_context",
                description=(
                    "Identify current economic factors that "
                    "may materially affect the analysis."
                ),
                sources=(
                    ResearchSource(
                        "web_research",
                        "web",
                    ),
                ),
            ),
        ]

        if has_workspace:
            steps.append(
                ResearchStep(
                    name="internal_financial_context",
                    description=(
                        "Use the user's internal financial "
                        "data when relevant."
                    ),
                    sources=(
                        ResearchSource(
                            "workspace_database",
                            "internal",
                        ),
                    ),
                )
            )

        return ResearchPlan(
            domain=TaskDomain.MACROECONOMICS,
            steps=steps,
            requires_web=True,
            requires_market_data=True,
            requires_internal_data=has_workspace,
        )

    # -----------------------------------------------------
    # STOCKS
    # -----------------------------------------------------

    def _stocks_plan(self) -> ResearchPlan:

        return ResearchPlan(
            domain=TaskDomain.STOCKS,
            steps=[
                ResearchStep(
                    name="price_history",
                    description=(
                        "Collect relevant historical and current "
                        "market data."
                    ),
                    sources=(
                        ResearchSource(
                            "market_data",
                            "market",
                        ),
                    ),
                ),
                ResearchStep(
                    name="fundamentals",
                    description=(
                        "Collect company fundamentals and "
                        "financial information."
                    ),
                    sources=(
                        ResearchSource(
                            "financial_data",
                            "web",
                        ),
                    ),
                ),
                ResearchStep(
                    name="market_context",
                    description=(
                        "Analyze broader market and "
                        "economic conditions."
                    ),
                    sources=(
                        ResearchSource(
                            "web_research",
                            "web",
                        ),
                    ),
                ),
            ],
            requires_web=True,
            requires_market_data=True,
        )

    # -----------------------------------------------------
    # CRYPTO
    # -----------------------------------------------------

    def _crypto_plan(self) -> ResearchPlan:

        return ResearchPlan(
            domain=TaskDomain.CRYPTO,
            steps=[
                ResearchStep(
                    name="asset_market_data",
                    description=(
                        "Collect current price, volume and "
                        "market capitalization data."
                    ),
                    sources=(
                        ResearchSource(
                            "crypto_market_data",
                            "market",
                        ),
                    ),
                ),
                ResearchStep(
                    name="onchain_context",
                    description=(
                        "Collect relevant blockchain and "
                        "on-chain information."
                    ),
                    sources=(
                        ResearchSource(
                            "onchain_data",
                            "web",
                        ),
                    ),
                ),
                ResearchStep(
                    name="market_context",
                    description=(
                        "Analyze current crypto market conditions."
                    ),
                    sources=(
                        ResearchSource(
                            "web_research",
                            "web",
                        ),
                    ),
                ),
            ],
            requires_web=True,
            requires_market_data=True,
        )

    # -----------------------------------------------------
    # DEFI
    # -----------------------------------------------------

    def _liquidity_pool_plan(self) -> ResearchPlan:

        return ResearchPlan(
            domain=TaskDomain.LIQUIDITY_POOLS,
            steps=[
                ResearchStep(
                    name="pool_metrics",
                    description=(
                        "Collect TVL, liquidity, volume, "
                        "fees and pool composition."
                    ),
                    sources=(
                        ResearchSource(
                            "defi_market_data",
                            "market",
                        ),
                    ),
                ),
                ResearchStep(
                    name="yield_analysis",
                    description=(
                        "Analyze fees, yield and historical "
                        "performance."
                    ),
                    sources=(
                        ResearchSource(
                            "defi_data",
                            "web",
                        ),
                    ),
                ),
                ResearchStep(
                    name="risk_analysis",
                    description=(
                        "Evaluate impermanent loss, concentration, "
                        "smart-contract and liquidity risks."
                    ),
                    sources=(
                        ResearchSource(
                            "defi_data",
                            "web",
                        ),
                    ),
                ),
            ],
            requires_web=True,
            requires_market_data=True,
        )

    # -----------------------------------------------------
    # GEOPOLITICS
    # -----------------------------------------------------

    def _geopolitics_plan(self) -> ResearchPlan:

        return ResearchPlan(
            domain=TaskDomain.GEOPOLITICS,
            steps=[
                ResearchStep(
                    name="current_events",
                    description=(
                        "Collect recent verified developments "
                        "relevant to the requested region."
                    ),
                    sources=(
                        ResearchSource(
                            "news",
                            "web",
                        ),
                    ),
                ),
                ResearchStep(
                    name="economic_impact",
                    description=(
                        "Analyze economic and market effects."
                    ),
                    sources=(
                        ResearchSource(
                            "economic_data",
                            "web",
                        ),
                        ResearchSource(
                            "market_data",
                            "market",
                        ),
                    ),
                ),
            ],
            requires_web=True,
            requires_market_data=True,
        )

    # -----------------------------------------------------
    # FORECASTING
    # -----------------------------------------------------

    def _forecast_plan(
        self,
        has_workspace: bool,
    ) -> ResearchPlan:

        steps = [
            ResearchStep(
                name="historical_data",
                description=(
                    "Collect historical observations needed "
                    "for the forecast."
                ),
                sources=(
                    ResearchSource(
                        "historical_market_data",
                        "market",
                    ),
                ),
            ),
            ResearchStep(
                name="current_conditions",
                description=(
                    "Collect current economic, market and "
                    "geopolitical conditions."
                ),
                sources=(
                    ResearchSource(
                        "web_research",
                        "web",
                    ),
                    ResearchSource(
                        "market_data",
                        "market",
                    ),
                ),
            ),
            ResearchStep(
                name="scenario_analysis",
                description=(
                    "Build multiple scenarios and identify "
                    "key assumptions and risks."
                ),
            ),
        ]

        if has_workspace:
            steps.append(
                ResearchStep(
                    name="internal_context",
                    description=(
                        "Include relevant company or personal "
                        "financial data."
                    ),
                    sources=(
                        ResearchSource(
                            "workspace_database",
                            "internal",
                        ),
                    ),
                )
            )

        return ResearchPlan(
            domain=TaskDomain.FORECASTING,
            steps=steps,
            requires_web=True,
            requires_market_data=True,
            requires_internal_data=has_workspace,
        )

    # -----------------------------------------------------
    # PERSONAL FINANCE
    # -----------------------------------------------------

    def _personal_finance_plan(
        self,
        has_workspace: bool,
    ) -> ResearchPlan:

        return ResearchPlan(
            domain=TaskDomain.PERSONAL_FINANCE,
            steps=[
                ResearchStep(
                    name="personal_financial_data",
                    description=(
                        "Analyze available personal financial data."
                    ),
                    sources=(
                        ResearchSource(
                            "workspace_database",
                            "internal",
                        ),
                    ),
                ),
                ResearchStep(
                    name="external_context",
                    description=(
                        "Collect relevant current external "
                        "financial, economic or regulatory "
                        "information when it materially affects "
                        "the user's question."
                    ),
                    sources=(
                        ResearchSource(
                            "web_research",
                            "web",
                        ),
                    ),
                ),
            ],
            requires_web=True,
            requires_internal_data=has_workspace,
        )

    # -----------------------------------------------------
    # COMPANY FINANCE
    # -----------------------------------------------------

    def _company_finance_plan(
        self,
        has_workspace: bool,
    ) -> ResearchPlan:

        return ResearchPlan(
            domain=TaskDomain.COMPANY_FINANCE,
            steps=[
                ResearchStep(
                    name="company_financials",
                    description=(
                        "Analyze available company financial data."
                    ),
                    sources=(
                        ResearchSource(
                            "workspace_database",
                            "internal",
                        ),
                    ),
                ),
                ResearchStep(
                    name="macro_environment",
                    description=(
                        "Collect current macroeconomic conditions "
                        "relevant to the company's country and currency."
                    ),
                    sources=(
                        ResearchSource(
                            "official_statistics",
                            "web",
                        ),
                        ResearchSource(
                            "central_bank",
                            "web",
                        ),
                    ),
                ),
                ResearchStep(
                    name="industry_context",
                    description=(
                        "Collect current industry, market and "
                        "competitive information relevant to "
                        "the company."
                    ),
                    sources=(
                        ResearchSource(
                            "industry_research",
                            "web",
                        ),
                        ResearchSource(
                            "market_data",
                            "market",
                        ),
                    ),
                ),
                ResearchStep(
                    name="external_risks",
                    description=(
                        "Identify current external risks, "
                        "regulatory developments and events "
                        "that may materially affect the company."
                    ),
                    sources=(
                        ResearchSource(
                            "web_research",
                            "web",
                        ),
                    ),
                ),
            ],
            requires_web=True,
            requires_market_data=True,
            requires_internal_data=has_workspace,
        )
