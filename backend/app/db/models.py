from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    exchange: Mapped[str] = mapped_column(String(20))
    industry: Mapped[str] = mapped_column(String(100), index=True)
    listed_date: Mapped[date] = mapped_column(Date)


class DailyMarket(Base):
    __tablename__ = "daily_market"
    __table_args__ = (UniqueConstraint("stock_id", "trade_date", name="uq_daily_market_stock_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    open_price: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    close_price: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    high_price: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    low_price: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    volume: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    turnover: Mapped[Decimal] = mapped_column(Numeric(20, 2))


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (UniqueConstraint("stock_id", "report_period", name="uq_financial_stock_period"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    report_period: Mapped[str] = mapped_column(String(20), index=True)
    revenue: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    net_profit: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    total_assets: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    total_liabilities: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    roe: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    gross_margin: Mapped[Decimal] = mapped_column(Numeric(10, 4))


class FactorValue(Base):
    __tablename__ = "factor_values"
    __table_args__ = (UniqueConstraint("stock_id", "factor_name", "trade_date", name="uq_factor_stock_name_date"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    factor_name: Mapped[str] = mapped_column(String(100), index=True)
    trade_date: Mapped[date] = mapped_column(Date, index=True)
    factor_value: Mapped[Decimal] = mapped_column(Numeric(20, 6))


class BusinessMetric(Base):
    __tablename__ = "business_metrics"
    __table_args__ = (UniqueConstraint("stock_id", "metric_name", "period", name="uq_metric_stock_name_period"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    metric_name: Mapped[str] = mapped_column(String(100), index=True)
    period: Mapped[str] = mapped_column(String(20), index=True)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    unit: Mapped[str] = mapped_column(String(20))


class MetadataCatalog(Base):
    __tablename__ = "metadata_catalog"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    object_type: Mapped[str] = mapped_column(String(30), index=True)
    object_name: Mapped[str] = mapped_column(String(100), index=True)
    parent_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    business_name: Mapped[str] = mapped_column(String(100), index=True)
    description: Mapped[str] = mapped_column(Text)
    synonyms: Mapped[str] = mapped_column(Text, default="")
    example_values: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

