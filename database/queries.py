from sqlmodel import Session
from .connection import engine, StockPrice, BotLog

def insert_stock_price(symbol: str, name: str, price: float, currency: str = "USD") -> None:
    """
    수집된 주가 데이터를 DB에 저장함.
    """
    with Session(engine) as session:
        new_price = StockPrice(
            symbol=symbol,
            name=name,
            price=price,
            currency=currency
        )
        session.add(new_price)
        session.commit()

def insert_bot_log(worker_name: str, message: str, level: str = "INFO", error_stack: str = None) -> None:
    """
    봇의 실행 이력 및 에러 로그를 DB에 기록함.
    """
    with Session(engine) as session:
        new_log = BotLog(
            level=level,
            worker_name=worker_name,
            message=message,
            error_stack=error_stack
        )
        session.add(new_log)
        session.commit()
