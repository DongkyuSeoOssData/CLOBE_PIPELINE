import sys
import os
from typing import List, Dict, Any

# [수정] 프로젝트 루트 경로를 탐색 경로에 추가 (어디서든 실행 가능하도록)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select, desc
from database.connection import engine, StockPrice, BotLog

# FastAPI 앱 객체 생성
app = FastAPI(
    title="Clobe E2E Pipeline Monitoring API",
    description="수집된 주가 데이터 및 봇 실행 상태를 실시간으로 모니터링하는 API 서버",
    version="2.0.0"
)

def get_db():
    """
    FastAPI 의존성 주입을 위한 DB 세션 제너레이터.
    """
    with Session(engine) as session:
        yield session

@app.get("/", tags=["Health"])
async def root():
    """
    API 서버 상태 확인 엔드포인트.
    """
    return {"status": "running", "message": "Clobe V2 Middleware is active."}

@app.get("/dashboard", response_class=HTMLResponse, tags=["UI"])
async def dashboard(session: Session = Depends(get_db)):
    """
    실시간 수집 현황을 시각적으로 보여주는 HTML 대시보드.
    """
    statement = select(StockPrice).order_by(desc(StockPrice.collected_at)).limit(50)
    prices = session.exec(statement).all()

    # 테이블 로우 생성
    rows = ""
    for p in prices:
        # 통화별 포맷팅 분기 (부장님 지시사항 반영)
        if p.currency == "KRW":
            formatted_price = f"₩{int(p.price):,}" # 원화: 소수점 제거 및 ₩ 표기
        else:
            formatted_price = f"${p.price:,.2f}" # 달러: 소수점 2자리 및 $ 표기

        rows += f"""
        <tr>
            <td>{p.symbol}</td>
            <td>{p.name}</td>
            <td class="price">{formatted_price}</td>
            <td>{p.currency}</td>
            <td>{p.collected_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Clobe V2 Monitoring Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; color: #333; }}
            .container {{ max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #3498db; color: white; text-transform: uppercase; font-size: 14px; letter-spacing: 1px; }}
            tr:hover {{ background-color: #f1f1f1; }}
            .price {{ font-weight: bold; color: #27ae60; }}
            .status-bar {{ margin-bottom: 20px; font-size: 14px; color: #7f8c8d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Clobe E2E 실시간 수집 대시보드</h1>
            <div class="status-bar">최근 수집 데이터 기준: {len(prices)}건 표시 중</div>
            <table>
                <thead>
                    <tr>
                        <th>종목코드</th>
                        <th>종목명</th>
                        <th>현재가</th>
                        <th>통화</th>
                        <th>수집시각</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else "<tr><td colspan='5' style='text-align:center;'>데이터가 없습니다. 워커를 가동해 주세요.</td></tr>"}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/prices", response_model=List[StockPrice], tags=["Data"])
async def get_latest_prices(limit: int = 20, session: Session = Depends(get_db)):


    """
    최신 수집된 주가 데이터 목록을 조회함.
    """
    statement = select(StockPrice).order_by(desc(StockPrice.collected_at)).limit(limit)
    results = session.exec(statement).all()
    return results

@app.get("/logs", response_model=List[BotLog], tags=["Monitoring"])
async def get_bot_logs(limit: int = 50, session: Session = Depends(get_db)):
    """
    봇의 실행 및 에러 로그 목록을 조회함.
    """
    statement = select(BotLog).order_by(desc(BotLog.created_at)).limit(limit)
    results = session.exec(statement).all()
    return results

@app.get("/summary", tags=["Monitoring"])
async def get_summary(session: Session = Depends(get_db)):
    """
    수집 현황 요약 정보를 제공함.
    """
    # 총 수집 데이터 수
    total_prices = session.query(StockPrice).count()
    # 에러 로그 수
    error_count = session.query(BotLog).filter(BotLog.level == "ERROR").count()
    # 최신 수집 시각
    latest_item = session.exec(select(StockPrice).order_by(desc(StockPrice.collected_at))).first()
    
    return {
        "total_records": total_prices,
        "error_count": error_count,
        "last_collected_at": latest_item.collected_at if latest_item else None,
        "system_status": "stable" if error_count == 0 else "degraded"
    }

if __name__ == "__main__":
    import uvicorn
    # 독립 실행 시 8000 포트로 서버 가동
    uvicorn.run(app, host="0.0.0.0", port=8000)
