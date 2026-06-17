from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.db.base import Base
from app.db.models import (
    BusinessMetric,
    DailyMarket,
    FactorValue,
    FinancialStatement,
    MetadataCatalog,
    Stock,
)
from app.db.session import SessionLocal, engine


STOCKS = [
    {"symbol": "600519", "name": "贵州茅台", "exchange": "SSE", "industry": "食品饮料", "listed_date": date(2001, 8, 27)},
    {"symbol": "000001", "name": "平安银行", "exchange": "SZSE", "industry": "银行", "listed_date": date(1991, 4, 3)},
    {"symbol": "300750", "name": "宁德时代", "exchange": "SZSE", "industry": "电力设备", "listed_date": date(2018, 6, 11)},
    {"symbol": "601318", "name": "中国平安", "exchange": "SSE", "industry": "非银金融", "listed_date": date(2007, 3, 1)},
    {"symbol": "600036", "name": "招商银行", "exchange": "SSE", "industry": "银行", "listed_date": date(2002, 4, 9)},
    {"symbol": "002415", "name": "海康威视", "exchange": "SZSE", "industry": "计算机", "listed_date": date(2010, 5, 28)},
]

MARKET_ROWS = [
    ("600519", date(2026, 6, 5), 1580.00, 1608.50, 1620.00, 1572.30, 2380000, 3810000000),
    ("000001", date(2026, 6, 5), 10.20, 10.45, 10.51, 10.11, 85600000, 890000000),
    ("300750", date(2026, 6, 5), 196.30, 201.80, 203.10, 195.60, 19200000, 3860000000),
    ("601318", date(2026, 6, 5), 47.20, 48.55, 49.10, 46.90, 49800000, 2410000000),
    ("600036", date(2026, 6, 5), 36.80, 37.42, 37.66, 36.51, 63200000, 2360000000),
    ("002415", date(2026, 6, 5), 31.10, 32.08, 32.40, 30.92, 42100000, 1340000000),
]

FINANCIAL_ROWS = [
    ("600519", "2025Q4", 174100000000, 85700000000, 272000000000, 65000000000, 0.3421, 0.9180),
    ("000001", "2025Q4", 164800000000, 46400000000, 5900000000000, 5400000000000, 0.1160, 0.0000),
    ("300750", "2025Q4", 400900000000, 44100000000, 747000000000, 497000000000, 0.2240, 0.2360),
    ("601318", "2025Q4", 1032000000000, 126700000000, 12200000000000, 11000000000000, 0.1280, 0.0000),
    ("600036", "2025Q4", 343800000000, 146600000000, 12100000000000, 11300000000000, 0.1710, 0.0000),
    ("002415", "2025Q4", 89300000000, 14200000000, 145000000000, 61000000000, 0.1560, 0.4440),
]

FACTOR_ROWS = [
    ("600519", "pe_ttm", date(2026, 6, 5), 24.6),
    ("000001", "pe_ttm", date(2026, 6, 5), 5.2),
    ("300750", "pe_ttm", date(2026, 6, 5), 21.8),
    ("601318", "pe_ttm", date(2026, 6, 5), 7.1),
    ("600036", "pe_ttm", date(2026, 6, 5), 6.4),
    ("002415", "pe_ttm", date(2026, 6, 5), 18.9),
    ("600519", "momentum_20d", date(2026, 6, 5), 0.042),
    ("000001", "momentum_20d", date(2026, 6, 5), 0.018),
    ("300750", "momentum_20d", date(2026, 6, 5), 0.067),
    ("601318", "momentum_20d", date(2026, 6, 5), 0.025),
    ("600036", "momentum_20d", date(2026, 6, 5), 0.033),
    ("002415", "momentum_20d", date(2026, 6, 5), -0.012),
]

BUSINESS_ROWS = [
    ("600519", "渠道库存周转天数", "2025Q4", 38.5, "天"),
    ("000001", "不良贷款率", "2025Q4", 1.05, "%"),
    ("300750", "动力电池装机量", "2025Q4", 96.4, "GWh"),
    ("601318", "综合成本率", "2025Q4", 98.2, "%"),
    ("600036", "不良贷款率", "2025Q4", 0.95, "%"),
    ("002415", "海外收入占比", "2025Q4", 31.6, "%"),
]

METADATA_ROWS = [
    ("table", "stocks", None, "股票基础信息表", "记录股票代码、公司名称、交易所、所属行业和上市日期。", "证券,股票,公司,标的,上市公司", "600519 贵州茅台; 000001 平安银行; 300750 宁德时代"),
    ("column", "stocks.symbol", "stocks", "股票代码", "股票在交易所使用的证券代码，用于连接行情、财报、因子和业务指标。", "证券代码,代码,标的代码", "600519, 000001, 300750"),
    ("column", "stocks.industry", "stocks", "所属行业", "上市公司所属行业分类，例如银行、食品饮料、电力设备、计算机。", "行业,板块,赛道", "银行; 食品饮料; 电力设备"),
    ("table", "daily_market", None, "日行情表", "记录股票每日开盘价、收盘价、最高价、最低价、成交量和成交额。", "行情,价格,收盘价,成交量,成交额,交易日", "trade_date=2026-06-05 close_price=1608.50"),
    ("column", "daily_market.close_price", "daily_market", "收盘价", "股票在交易日结束时的成交价格，常用于排序和收益分析。", "收盘,价格,最新价", "close_price=1608.50"),
    ("column", "daily_market.turnover", "daily_market", "成交额", "交易日内成交金额，单位为元。", "成交金额,交易额,成交额", "turnover=3810000000"),
    ("table", "financial_statements", None, "财务指标表", "记录报告期收入、净利润、总资产、总负债、ROE 和毛利率。", "财报,收入,净利润,资产,负债,ROE,毛利率", "report_period=2025Q4 revenue=174100000000"),
    ("column", "financial_statements.net_profit", "financial_statements", "净利润", "企业报告期归属于股东的净利润，可用于盈利能力排名。", "利润,盈利,净利,归母净利润", "net_profit=85700000000"),
    ("column", "financial_statements.roe", "financial_statements", "净资产收益率", "ROE，衡量公司利用股东权益创造利润的能力。", "ROE,净资产收益率,盈利能力", "roe=0.3421"),
    ("column", "financial_statements.gross_margin", "financial_statements", "毛利率", "收入扣除营业成本后的毛利占收入比例。", "毛利,毛利率,盈利质量", "gross_margin=0.9180"),
    ("table", "factor_values", None, "量化因子表", "记录股票在交易日上的因子名称和因子值，例如市盈率和动量因子。", "因子,估值,市盈率,PE,动量,momentum", "factor_name=pe_ttm factor_value=24.6"),
    ("metric", "pe_ttm", "factor_values", "滚动市盈率", "PE TTM，常用估值因子，数值越低通常代表估值越低。", "PE,市盈率,估值,便宜", "pe_ttm=5.2"),
    ("metric", "momentum_20d", "factor_values", "20日动量", "过去约20个交易日的价格动量，用于衡量短期趋势强弱。", "动量,趋势,momentum,涨幅", "momentum_20d=0.067"),
    ("table", "business_metrics", None, "业务指标表", "记录行业相关业务指标，例如渠道库存周转天数、不良贷款率、动力电池装机量。", "业务指标,经营指标,不良率,装机量,库存周转", "metric_name=动力电池装机量 metric_value=96.4GWh"),
    ("metric", "不良贷款率", "business_metrics", "银行资产质量指标", "银行贷款中不良贷款余额占比，数值越低通常代表资产质量越好。", "不良率,资产质量,银行指标", "招商银行 不良贷款率 0.95%"),
    ("metric", "动力电池装机量", "business_metrics", "动力电池业务规模", "动力电池企业报告期装机规模，单位 GWh。", "装机量,电池,新能源,业务规模", "宁德时代 动力电池装机量 96.4GWh"),
]


def init_schema() -> None:
    Base.metadata.create_all(bind=engine)


def seed_data() -> None:
    with SessionLocal() as session:
        for item in STOCKS:
            if not session.query(Stock).filter_by(symbol=item["symbol"]).first():
                session.add(Stock(**item))
        session.flush()
        stock_by_symbol = {stock.symbol: stock for stock in session.query(Stock).all()}

        for symbol, trade_date, open_price, close_price, high_price, low_price, volume, turnover in MARKET_ROWS:
            stock = stock_by_symbol[symbol]
            exists = session.query(DailyMarket).filter_by(stock_id=stock.id, trade_date=trade_date).first()
            if not exists:
                session.add(DailyMarket(stock_id=stock.id, trade_date=trade_date, open_price=Decimal(str(open_price)), close_price=Decimal(str(close_price)), high_price=Decimal(str(high_price)), low_price=Decimal(str(low_price)), volume=Decimal(str(volume)), turnover=Decimal(str(turnover))))

        for symbol, report_period, revenue, net_profit, total_assets, total_liabilities, roe, gross_margin in FINANCIAL_ROWS:
            stock = stock_by_symbol[symbol]
            exists = session.query(FinancialStatement).filter_by(stock_id=stock.id, report_period=report_period).first()
            if not exists:
                session.add(FinancialStatement(stock_id=stock.id, report_period=report_period, revenue=Decimal(str(revenue)), net_profit=Decimal(str(net_profit)), total_assets=Decimal(str(total_assets)), total_liabilities=Decimal(str(total_liabilities)), roe=Decimal(str(roe)), gross_margin=Decimal(str(gross_margin))))

        for symbol, factor_name, trade_date, factor_value in FACTOR_ROWS:
            stock = stock_by_symbol[symbol]
            exists = session.query(FactorValue).filter_by(stock_id=stock.id, factor_name=factor_name, trade_date=trade_date).first()
            if not exists:
                session.add(FactorValue(stock_id=stock.id, factor_name=factor_name, trade_date=trade_date, factor_value=Decimal(str(factor_value))))

        for symbol, metric_name, period, metric_value, unit in BUSINESS_ROWS:
            stock = stock_by_symbol[symbol]
            exists = session.query(BusinessMetric).filter_by(stock_id=stock.id, metric_name=metric_name, period=period).first()
            if not exists:
                session.add(BusinessMetric(stock_id=stock.id, metric_name=metric_name, period=period, metric_value=Decimal(str(metric_value)), unit=unit))

        for object_type, object_name, parent_name, business_name, description, synonyms, example_values in METADATA_ROWS:
            row = session.query(MetadataCatalog).filter_by(object_type=object_type, object_name=object_name, parent_name=parent_name).first()
            if row:
                row.business_name = business_name
                row.description = description
                row.synonyms = synonyms
                row.example_values = example_values
            else:
                session.add(MetadataCatalog(object_type=object_type, object_name=object_name, parent_name=parent_name, business_name=business_name, description=description, synonyms=synonyms, example_values=example_values))

        session.commit()


def main() -> None:
    init_schema()
    seed_data()
    print("database schema and sample data are ready")


if __name__ == "__main__":
    main()
