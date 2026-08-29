from enum import Enum


class TaskDomain(str, Enum):
    GENERAL = "general"
    PERSONAL_FINANCE = "personal_finance"
    COMPANY_FINANCE = "company_finance"
    MACROECONOMICS = "macroeconomics"
    MARKETS = "markets"
    STOCKS = "stocks"
    CRYPTO = "crypto"
    LIQUIDITY_POOLS = "liquidity_pools"
    GEOPOLITICS = "geopolitics"
    FORECASTING = "forecasting"


class DataSourceType(str, Enum):
    INTERNAL = "internal"
    WEB = "web"
    MARKET = "market"
    USER = "user"


class AnalysisTask:
    def __init__(
        self,
        domain: TaskDomain,
        requires_web: bool = False,
        requires_market_data: bool = False,
        requires_internal_data: bool = False,
    ):
        self.domain = domain
        self.requires_web = requires_web
        self.requires_market_data = requires_market_data
        self.requires_internal_data = requires_internal_data
