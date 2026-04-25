import asyncio
import json
import os
import sys
import traceback
from datetime import datetime
from typing import List, Dict, Any

from playwright.async_api import async_playwright
from database.queries import insert_stock_price, insert_bot_log

# 워커 설정
WORKER_NAME = "ClobeWorker-V2"
CONFIG_PATH = os.path.join("config", "targets.json")

def load_config() -> Dict[str, Any]:
    """
    config/targets.json 파일 전체를 로드함.
    """
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"설정 파일 로드 실패: {e}")
        return {}

async def fetch_stock_price(page, symbol: str, name: str, market: str, market_config: Dict[str, Any]) -> bool:
    """
    시장별(US/KR)로 최적화된 로직을 사용하여 주가를 수집함.
    """
    base_url = market_config.get("base_url", "")
    url = f"{base_url}{symbol}"
    
    try:
        print(f"[{WORKER_NAME}] 수집 시도: {name}({symbol}) @ {market}")
        
        # 1. 페이지 이동
        # 네이버와 야후의 로딩 방식 차이를 고려하여 wait_until 조정
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        
        # 2. 시장별 분기 처리 (부장님 지시사항 반영)
        if market == "US":
            # Yahoo Finance: test-id 기반 정밀 타겟팅
            price_element = page.get_by_test_id("qsp-price")
            await price_element.wait_for(state="attached", timeout=15000)
            raw_price = await price_element.inner_text()
        else:
            # 네이버 증권: ID(#_nowVal) 우선, 실패 시 .no_today 로직 사용
            # [수정] state="attached"를 사용하여 숨겨진 blind 요소도 즉시 획득
            price_element = page.locator("#_nowVal")
            if await price_element.count() == 0:
                price_element = page.locator(".no_today .blind").first
            
            await price_element.wait_for(state="attached", timeout=15000)
            raw_price = await price_element.inner_text()

        # 3. 데이터 정제 및 수치화
        # 콤마 제거 및 공백 제거
        clean_price_str = raw_price.replace(",", "").strip()
        price = float(clean_price_str)
        
        # 4. DB 적재
        currency = "USD" if market == "US" else "KRW"
        insert_stock_price(symbol, name, price, currency)
        
        print(f"[{WORKER_NAME}] 수집 성공: {name} -> {price} {currency}")
        return True
        
    except Exception as e:
        error_msg = f"{symbol}({market}) 수집 에러: {str(e)}"
        print(f"[{WORKER_NAME}] {error_msg}")
        insert_bot_log(WORKER_NAME, error_msg, level="ERROR", error_stack=traceback.format_exc())
        return False

async def run_worker():
    """
    설정된 모든 종목을 순회하며 수집하는 메인 프로세스.
    """
    config = load_config()
    markets_info = config.get("markets", {})
    targets = [t for t in config.get("targets", []) if t.get("enabled")]
    
    if not targets:
        print("수집 대상을 찾을 수 없습니다.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 매 세션마다 깨끗한 환경을 위해 context 분리
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        insert_bot_log(WORKER_NAME, f"V2 고도화 수집 시작 (총 {len(targets)}건)")
        
        for target in targets:
            market = target.get("market", "US")
            market_config = markets_info.get(market, {})
            
            await fetch_stock_price(page, target["symbol"], target["name"], market, market_config)
            
            # 사이트 차단 방지 및 브라우저 안정화를 위한 간격
            await asyncio.sleep(1.5)
            
        await browser.close()
        insert_bot_log(WORKER_NAME, "전체 수집 프로세스 정상 종료")

if __name__ == "__main__":
    # Windows 비동기 루프 정책 강제 설정
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(run_worker())
