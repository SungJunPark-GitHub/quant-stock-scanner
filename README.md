# 종목탐색기

미국/한국 주식과 ETF를 빠르게 훑어보는 Flask 기반 종목 탐색 도구입니다.  
저장된 스냅샷을 먼저 보여주고, 백그라운드에서 시세와 지표를 주기적으로 갱신합니다.

> 점수, 등급, 신호는 알고리즘 기반 스크리닝 결과입니다. 투자 조언이 아니며 판단과 손익 책임은 사용자에게 있습니다.

## 핵심 기능

- 미국/한국 시장 전환
- 주식 스캐너
  - 미국: S&P 500, 나스닥100, 러셀2000, ETC
  - 한국: 코스피, 코스닥
  - 지수별 필터와 상단 요약 연동
  - 검색, 섹터 필터, 관심종목, 조건 칩 필터
- ETF 현황
  - 미국/한국 ETF 자동 분리
  - 대표지수, 섹터, 테마, 원자재, 채권, 글로벌, 한국 분류 칩
  - ETF 전용 점수와 평균 점수 요약
- 종목 상세 모달
  - 결론, 타이밍, 회사, 상세, 참고 탭
  - Chart.js 가격 차트
  - CAN SLIM, 기술 지표, 재무 지표, US/KR 인사이트
  - 인사이더 거래, 종목 일정, 뉴스 감성
  - 백테스트 요약
  - 캡처 버튼
- 점수 계산
  - CAN SLIM 기본점수
  - 해자 가산점
  - 기술 지표, 추세, 거래량, 변동성, 시장 방향
- 백그라운드 자동 갱신
  - 상단 작업명, 처리 개수, 퍼센트 진행률 표시
- CSV Export
- 익명 토론방
  - 브라우저 localStorage 기반
  - 하루가 지나면 채팅 내용 자동 초기화
- 종목 로고
  - Toss 증권 로고 우선
  - 미국 종목은 IEX 로고 fallback
  - 일부 종목은 회사 도메인 로고 override

## 실행 방법

```bash
source venv/bin/activate
python run.py
```

접속 주소:

```text
http://127.0.0.1:5050
```

현재 `run.py`는 `5050` 포트로 실행됩니다. 기존 `5000` 포트에서 브라우저 403 문제가 날 수 있어 5050을 사용합니다.

## 프로젝트 구조

```text
app/
  __init__.py
  routes.py                    # Flask 라우트, 스냅샷, API, 스캔 데이터 생성
  data/                        # 수동 관리 JSON 데이터
    market_index_groups.json
    sp500_tickers.json
    nasdaq100_tickers.json
    russell2000_tickers.json
    etc_tickers.json
    kospi_tickers.json
    kosdaq_tickers.json
    etf_universe.json
  cache/                       # 생성 캐시와 스냅샷
    scan_snapshots/
    stock_info/
    stock_cache.db
  services/
    market_service.py          # 종목 목록, 기본 정보, yfinance 데이터
    macro_service.py           # 시장 지표, 매크로 이벤트, 지수 그룹
    indicator_service.py       # RSI, MA, ATR, MACD, 52주 고가 등
    score_service.py           # 종합 점수와 시그널
    canslim_service.py         # CAN SLIM 항목 점수
    moat_service.py            # 해자 가산점
    backtest_service.py        # 단순 백테스트
    news_service.py            # 뉴스 감성
  static/
    css/style.css
    js/main.js
    favicon.svg
  templates/
    index.html
    components/
```

## 데이터 관리

이 프로젝트는 빠른 화면 표시를 위해 종목 유니버스를 JSON으로 관리합니다.  
새로고침 때마다 대규모 외부 목록을 긁어오지 않고, 저장된 목록을 기준으로 자동 갱신합니다.

### 미국 주식

미국 그룹 설정:

```text
app/data/market_index_groups.json
```

그룹별 종목 파일:

```text
app/data/sp500_tickers.json
app/data/nasdaq100_tickers.json
app/data/russell2000_tickers.json
app/data/etc_tickers.json
```

`ETC`는 따로 보고 싶은 인기/테마 종목 바구니입니다.  
현재 우주, 양자, AI 데이터센터, 크립토 인프라, 원전·우라늄, 핀테크, 포토닉스 종목들이 들어 있습니다.

예시:

```json
[
  {
    "ticker": "ASTS",
    "name": "AST SpaceMobile, Inc."
  },
  {
    "ticker": "TSM",
    "name": "Taiwan Semiconductor Manufacturing Company Limited"
  }
]
```

새 종목을 추가할 때는 `ticker`와 `name`을 넣으면 됩니다.  
한글명/설명까지 예쁘게 보이게 하려면 `app/services/market_service.py`의 `US_KOREAN_NAME_MAP`, `US_DESCRIPTION_MAP`에도 추가하는 것이 좋습니다.

### 한국 주식

```text
app/data/kospi_tickers.json
app/data/kosdaq_tickers.json
```

한국 종목은 yfinance 형식에 맞춰 `.KS`, `.KQ` 접미사를 사용합니다.

예:

```json
{
  "ticker": "005930.KS",
  "code": "005930",
  "name": "삼성전자",
  "sector": "반도체",
  "description": "반도체 · 스마트폰 · 가전"
}
```

### ETF

```text
app/data/etf_universe.json
```

미국/한국 ETF를 같은 파일에서 관리합니다.  
한국 ETF는 `.KS` 또는 `.KQ` 접미사로 구분합니다.

ETF 화면은 `theme` 값을 기준으로 칩 필터를 자동 생성합니다.

```json
{
  "ticker": "QQQ",
  "name": "Invesco QQQ Trust",
  "category": "나스닥 기술주",
  "theme": "대표지수"
}
```

## 업데이트 방식

첫 화면은 저장된 스냅샷을 즉시 읽어서 빠르게 표시합니다.

앱이 실행되면 백그라운드 자동 갱신 스레드가 시작되고, 오래된 스냅샷을 순서대로 갱신합니다.

1. 미국 주식
2. 한국 주식
3. ETF

기본 자동 갱신 주기는 30분입니다.

```bash
AUTO_UPDATE_INTERVAL_MINUTES=30 python run.py
```

자동 갱신을 끄려면:

```bash
AUTO_UPDATE_ENABLED=0 python run.py
```

초기 갱신 지연 시간을 바꾸려면:

```bash
AUTO_UPDATE_INITIAL_DELAY_SECONDS=30 python run.py
```

상단 `자동갱신` 항목에서 현재 작업명, 처리 개수, 진행률을 볼 수 있습니다.

## 점수 계산

현재 종합점수는 큰 틀에서 아래 구조입니다.

```text
종합점수 = CAN SLIM 기본점수 기반 + 해자 가산점 + 기술/추세 보정
```

### CAN SLIM 기본점수

`app/services/canslim_service.py`

반영 항목:

- C: 최근 실적 성장
- A: 연간 수익성/ROE
- N: 신고가·신제품·새 모멘텀
- S: 수급과 거래량
- L: 주도주 여부
- I: 기관 수급
- M: 시장 방향

각 항목은 단순 통과/실패가 아니라 부분 점수로 계산합니다.

### 해자 가산점

`app/services/moat_service.py`

최대 10점까지 가산합니다.

- 전환비용
- 네트워크 효과
- 무형자산
- 원가 우위
- ROIC 지속성

대형 우량주와 주요 테마주는 별도 override를 두고, 그 외 종목은 섹터와 설명 기반으로 보수적으로 추정합니다.

### 시그널

점수와 기술 상태를 기반으로 테이블에 직관적인 신호를 표시합니다.

- 매수관심
- 관망우세
- 중립
- 주의

상단 필터에는 다음 조건도 제공합니다.

- 관심종목
- S·A등급
- 저점매수
- 과매도
- 과열주의
- 주도주
- 숨은강자

## UI 동작

### 주식 스캐너

- 지수 칩을 누르면 테이블과 상단 요약이 같이 바뀝니다.
- `전체`를 누르면 전체 종목으로 돌아갑니다.
- 왼쪽 사이드바 섹터 필터와 상단 조건 필터를 함께 사용할 수 있습니다.
- 기본 정렬은 시가총액 큰 순서입니다.
- 헤더 클릭으로 점수, 현재가, 등락, RSI, 평균거래량, 시총 정렬이 가능합니다.

### ETF 현황

- 주식용 지수 줄은 ETF 탭에서 숨겨집니다.
- ETF 화면 안에서 테마 칩으로 분류 필터링합니다.
- 상단 요약은 ETF 기준으로 바뀝니다.
  - ETF 종목
  - 강세 ETF
  - 분류
  - 평균 점수

### 상세 모달

- 종목 행을 누르면 상세 모달이 열립니다.
- `Yahoo Finance` 버튼으로 외부 상세 페이지 이동이 가능합니다.
- 캡처 버튼으로 현재 모달 화면을 이미지로 저장할 수 있습니다.
- 참고 탭에서는 인사이더 거래, 종목 일정, 오너십 정보를 확인합니다.

## API

### 주식 업데이트

```http
POST /api/stocks/update
```

요청 예시:

```json
{
  "market": "US"
}
```

### ETF 업데이트

```http
POST /api/etfs/update
```

### 자동 갱신 상태

```http
GET /api/update/status
```

### 종목 참고 정보

```http
GET /api/stock/reference?ticker=AAPL
```

반환 데이터:

- 인사이더 거래
- 종목 일정
- 뉴스 감성

### CSV Export

```http
GET /export/csv?market=US
```

## 캐시와 스냅샷

주식/ETF 화면은 스냅샷 파일을 먼저 읽습니다.

```text
app/cache/scan_snapshots/US.json
app/cache/scan_snapshots/KR.json
app/cache/scan_snapshots/ETF.json
```

종목 기본 정보 캐시:

```text
app/cache/stock_info/
```

가격 히스토리 캐시:

```text
app/cache/stock_cache.db
```

`app/cache/`는 생성 데이터입니다. 배포나 Git 관리 방식에 따라 추적 제외를 고려하는 것이 좋습니다.

## 개발 메모

- 주요 데이터 소스는 `yfinance`입니다.
- Yahoo Finance 응답, 네트워크 상태, 거래소 휴장 여부에 따라 일부 값은 `N/A`가 될 수 있습니다.
- macOS 기본 Python 환경에서는 `urllib3`의 OpenSSL/LibreSSL 경고가 보일 수 있습니다. 앱 실행 자체를 막는 오류는 아닙니다.
- 로고는 Toss 증권 URL을 우선 사용하고, 미국 종목은 IEX 로고를 fallback으로 사용합니다.
- 익명 토론방은 서버 DB가 아니라 브라우저 localStorage 기반입니다.

## 추천 추가 기능

### 1. 점수 상세 Breakdown

현재는 최종 점수와 일부 이유 태그 중심입니다. 종목 상세에 점수 구성표를 넣으면 사용자가 납득하기 쉽습니다.

예:

- CAN SLIM: 61점
- 해자: +6.5점
- 추세: +8점
- 거래량: -3점
- 리스크: -5점

우선순위: 높음

### 2. 사용자 메모와 매매 계획

관심종목마다 개인 메모를 남기면 실사용성이 커집니다.

예:

- 관심 이유
- 목표 진입가
- 손절가
- 체크할 뉴스
- 다음 실적 발표일 메모

우선순위: 높음

### 3. 알림 조건

브라우저 알림이나 화면 알림으로 조건 충족 종목을 알려줄 수 있습니다.

예:

- 관심종목 점수 75 돌파
- RSI 30 이하
- 거래량 2배 이상
- 52주 고가 5% 이내
- ETC 종목 급등락

우선순위: 중간

### 4. 포트폴리오 추적

보유 종목, 수량, 평균단가를 입력하면 평가손익과 리스크를 볼 수 있습니다.

추가하면 좋은 지표:

- 평가손익
- 섹터 집중도
- 종목별 비중
- 전체 변동성
- 손절 기준

우선순위: 중간

### 5. ETF 분석 강화

ETF는 개별 주식과 다른 지표가 중요합니다.

추가 후보:

- 운용보수
- AUM
- 추적 지수
- 보유 상위 종목
- 섹터 비중
- 1년 변동성
- 환헤지 여부

우선순위: 중간

### 6. 데이터 품질 대시보드

어떤 종목의 데이터가 비어 있는지 한눈에 보는 관리 화면입니다.

보면 좋은 항목:

- 가격 누락
- 시총 누락
- 평균거래량 누락
- 차트 데이터 부족
- 로고 실패
- yfinance 조회 실패

우선순위: 중간

### 7. ETC 종목 관리 UI

지금은 JSON을 직접 수정해야 합니다. 화면에서 ETC 종목을 추가/삭제할 수 있으면 관리가 쉬워집니다.

필요 기능:

- 티커 추가
- 한글명/설명 입력
- 테마 태그 입력
- 중복 검사
- 저장 후 다음 갱신에 반영

우선순위: 낮음

## 추천 개발 순서

1. 점수 상세 Breakdown
2. 사용자 메모와 매매 계획
3. 알림 조건
4. 포트폴리오 추적
5. ETF 분석 강화
6. 데이터 품질 대시보드
7. ETC 종목 관리 UI
