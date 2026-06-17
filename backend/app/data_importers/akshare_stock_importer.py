from __future__ import annotations

import argparse
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from app.db.models import DailyMarket, MetadataCatalog, Stock
from app.db.session import SessionLocal


EXCHANGE_BY_PREFIX = {
    "6": "SSE",
    "0": "SZSE",
    "3": "SZSE",
    "8": "BSE",
    "4": "BSE",
}


def import_stock_history(
    symbol: str,
    name: str,
    industry: str,
    start_date: str,
    end_date: str,
    adjust: str = "",
) -> dict[str, int | str]:
    import akshare as ak

    normalized_symbol = symbol.strip()
    frame = ak.stock_zh_a_hist(
        symbol=normalized_symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )
    rows = frame.to_dict(orient="records")

    inserted = 0
    updated = 0
    with SessionLocal() as session:
        stock = _ensure_stock(session, normalized_symbol, name, industry)
        for row in rows:
            market_date = _parse_date(row["日期"])
            market_row = session.execute(
                select(DailyMarket).where(
                    DailyMarket.stock_id == stock.id,
                    DailyMarket.trade_date == market_date,
                )
            ).scalar_one_or_none()
            values = {
                "open_price": _decimal(row["开盘"]),
                "close_price": _decimal(row["收盘"]),
                "high_price": _decimal(row["最高"]),
                "low_price": _decimal(row["最低"]),
                "volume": _decimal(row["成交量"]),
                "turnover": _decimal(row["成交额"]),
            }
            if market_row:
                for key, value in values.items():
                    setattr(market_row, key, value)
                updated += 1
            else:
                session.add(DailyMarket(stock_id=stock.id, trade_date=market_date, **values))
                inserted += 1

        _upsert_akshare_metadata(session)
        session.commit()

    return {
        "symbol": normalized_symbol,
        "rows_downloaded": len(rows),
        "inserted": inserted,
        "updated": updated,
        "source": "AKShare stock_zh_a_hist",
    }


def _ensure_stock(session, symbol: str, name: str, industry: str) -> Stock:
    stock = session.execute(select(Stock).where(Stock.symbol == symbol)).scalar_one_or_none()
    if stock:
        stock.name = name or stock.name
        stock.industry = industry or stock.industry
        return stock

    stock = Stock(
        symbol=symbol,
        name=name,
        exchange=_exchange_for(symbol),
        industry=industry,
        listed_date=date(1900, 1, 1),
    )
    session.add(stock)
    session.flush()
    return stock


def _upsert_akshare_metadata(session) -> None:
    metadata_rows = [
        (
            "source",
            "akshare.stock_zh_a_hist",
            None,
            "AKShare A股历史行情接口",
            "从 AKShare 下载沪深京 A 股日频历史行情，字段包括日期、开盘价、收盘价、最高价、最低价、成交量和成交额，并导入 daily_market 表。",
            "AKShare,真实行情,A股历史行情,开源数据,股票数据下载",
            "symbol=600519 start_date=20240601 end_date=20240614",
        ),
        (
            "column",
            "daily_market.source",
            "daily_market",
            "行情数据来源",
            "2.0 版本支持通过 AKShare stock_zh_a_hist 接口下载真实 A 股历史行情并写入 daily_market 表。",
            "数据来源,AKShare,真实数据,行情导入",
            "AKShare stock_zh_a_hist",
        ),
    ]
    for object_type, object_name, parent_name, business_name, description, synonyms, example_values in metadata_rows:
        row = session.execute(
            select(MetadataCatalog).where(
                MetadataCatalog.object_type == object_type,
                MetadataCatalog.object_name == object_name,
                MetadataCatalog.parent_name.is_(parent_name) if parent_name is None else MetadataCatalog.parent_name == parent_name,
            )
        ).scalar_one_or_none()
        if row:
            row.business_name = business_name
            row.description = description
            row.synonyms = synonyms
            row.example_values = example_values
        else:
            session.add(
                MetadataCatalog(
                    object_type=object_type,
                    object_name=object_name,
                    parent_name=parent_name,
                    business_name=business_name,
                    description=description,
                    synonyms=synonyms,
                    example_values=example_values,
                )
            )


def _exchange_for(symbol: str) -> str:
    return EXCHANGE_BY_PREFIX.get(symbol[:1], "UNKNOWN")


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value).replace(",", ""))


def main() -> None:
    parser = argparse.ArgumentParser(description="Import A-share daily market data from AKShare.")
    parser.add_argument("--symbol", required=True, help="A-share symbol, for example 600519 or 000001.")
    parser.add_argument("--name", required=True, help="Stock name, for example 贵州茅台.")
    parser.add_argument("--industry", default="未知", help="Industry name used by local demo filters.")
    parser.add_argument("--start-date", required=True, help="Start date in YYYYMMDD format.")
    parser.add_argument("--end-date", required=True, help="End date in YYYYMMDD format.")
    parser.add_argument("--adjust", default="", choices=["", "qfq", "hfq"], help="AKShare adjust mode.")
    args = parser.parse_args()

    result = import_stock_history(
        symbol=args.symbol,
        name=args.name,
        industry=args.industry,
        start_date=args.start_date,
        end_date=args.end_date,
        adjust=args.adjust,
    )
    print(result)


if __name__ == "__main__":
    main()
