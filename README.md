# 🚀 Clobe E2E Micro-Automation Pipeline V2

본 프로젝트는 클로브(Clobe)팀 'Web Automation Engineer' 직무 포트폴리오를 위해 설계된 **모듈형 엔드투엔드(E2E) 데이터 수집 및 실시간 관제 파이프라인**입니다. 상용 RPA 솔루션에 의존하지 않고, 순수 Python 생태계(Playwright, FastAPI, SQLModel)만으로 설정-수집-적재-관제가 하나로 연결된 엔터프라이즈급 아키텍처를 구축했습니다.

## 🏗️ Core Architecture (Layered Design)
유지보수성과 운영 편의성을 극대화하기 위해 역할과 책임을 명확히 분리했습니다.

- **Config Layer (`targets.json`)**: 타겟 종목(US/KR 대장주)과 URL을 JSON으로 분리. 코드 수정 없이 비즈니스 부서에서 즉각적인 타겟 변경 가능.
- **Core Layer (`worker.py`)**: Playwright 기반 비동기 엔진. 시장별(Yahoo/Naver) 분기 로직 및 CSS Selector 정밀 타겟팅.
- **Database Layer (`database/`)**: SQLModel을 활용한 견고한 ORM 구성. 데이터 무결성 검증과 비즈니스 로직 격리.
- **API Layer (`middleware.py`)**: FastAPI 기반 데이터 서빙 및 실시간 관제 UI (₩/$ 통화 동적 포맷팅 적용).

---

## 💡 Engineering & Troubleshooting (핵심 문제 해결)

단순한 데이터 수집을 넘어, OS 인프라와 동적 웹의 본질적인 제약을 기술적으로 돌파했습니다.

### 1. Windows 환경 비동기(asyncio) 호환성 한계 돌파
- **Issue**: Python 3.13 및 Windows 환경에서 Playwright 가동 시 기본 이벤트 루프(Proactor) 충돌로 인한 `NotImplementedError` 발생.
- **Solution**: `WindowsSelectorEventLoopPolicy` 강제 적용 및 수동 루프 제어 로직을 주입하여 인프라 제약을 완벽히 극복.

### 2. Hidden DOM (Accessibility Blind) 100% 수집 전략
- **Issue**: 네이버 증권 등에서 주가 데이터가 시각적으로 숨겨진(`.blind`) 상태로 렌더링되어, 일반적인 `visible` 대기 시 Timeout 장애 발생.
- **Solution**: `state="attached"` 대기 옵션과 보조 선택자(`#_nowVal`) 결합 전략을 통해 렌더링 지연 및 숨김 요소 수집 성공률 100% 달성.

### 3. Pydantic 기반 무결성 통제
- 웹에서 수집된 지저분한 문자열 데이터를 DB 적재 전 Pydantic Schema를 통해 강제 정제(Sanitization). 오염된 데이터(Null, 음수 등) 유입을 원천 차단하여 파이프라인의 신뢰성 보장.

---

## 🛠️ Tech Stack
- **Language**: Python 3.10+
- **Scraping**: Playwright (Async)
- **Database / ORM**: SQLite3 / SQLModel (SQLAlchemy + Pydantic)
- **API / Dashboard**: FastAPI / Uvicorn

## 🚀 Getting Started
```bash
# 1. 패키지 설치
pip install playwright pydantic sqlmodel fastapi uvicorn

# 2. Playwright 브라우저 엔진 설치
python -m playwright install chromium

# 3. 파이프라인 가동 (수집 및 API 서버 동시 실행)
python main.py