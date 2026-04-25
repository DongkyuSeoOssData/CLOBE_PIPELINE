from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, create_engine

# SQLite 데이터베이스 파일 경로
DB_FILE = "clobe_v2.db"
sqlite_url = f"sqlite:///{DB_FILE}"

# 엔진 설정 (연결 안정성을 위한 옵션 포함)
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

class StockPrice(SQLModel, table=True):
    """
    수집된 주식 가격 데이터를 저장하는 테이블 모델.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, description="종목 코드")
    name: str = Field(description="종목명")
    price: float = Field(description="현재가")
    currency: str = Field(default="USD", description="통화 단위")
    collected_at: datetime = Field(default_factory=datetime.now, description="수집 시각")

class BotLog(SQLModel, table=True):
    """
    자동화 봇의 실행 및 에러 로그를 저장하는 테이블 모델.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    level: str = Field(default="INFO", index=True, description="로그 레벨 (INFO, ERROR)")
    worker_name: str = Field(index=True, description="작업 수행 워커명")
    message: str = Field(description="로그 메시지")
    error_stack: Optional[str] = Field(default=None, description="상세 에러 내용")
    created_at: datetime = Field(default_factory=datetime.now, description="로그 발생 시각")

def init_db() -> None:
    """
    데이터베이스와 필요한 테이블을 초기화함.
    """
    SQLModel.metadata.create_all(engine)
    print(f"V2 데이터베이스 초기화 완료: {DB_FILE}")
