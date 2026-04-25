import asyncio
import sys
import time
from datetime import datetime

from database.connection import init_db
from core.worker import run_worker

async def main():
    """
    Clobe E2E 파이프라인 V2 최상위 컨트롤러.
    DB 초기화 및 워커 실행을 오케스트레이션함.
    """
    print("=" * 50)
    print(f"Clobe E2E 파이프라인 V2 가동 - {datetime.now()}")
    print("=" * 50)
    
    start_time = time.time()
    
    # 1. 인프라 초기화 (DB 및 테이블 생성)
    print("\n[Step 1] 데이터베이스 인프라 초기화 중...")
    init_db()
    
    # 2. 데이터 수집 워커 가동
    print("\n[Step 2] Playwright 데이터 수집 워커 가동...")
    try:
        await run_worker()
    except Exception as e:
        print(f"치명적 오류 발생: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print(f"전체 공정 완료 (소요 시간: {duration:.2f}초)")
    print(f"종료 시각: {datetime.now()}")
    print("=" * 50)

if __name__ == "__main__":
    # Windows 비동기 정책 보정 (Playwright 서브프로세스 제어용)
    if sys.platform == "win32":
        # Pytest 환경이 아닌 일반 실행에서는 Proactor를 기본으로 시도하되,
        # 실패 시 Selector로 자동 전환하는 방어 로직 적용
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
    asyncio.run(main())
