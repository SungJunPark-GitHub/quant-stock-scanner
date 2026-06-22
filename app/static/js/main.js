const rows = document.querySelectorAll(".stock-row");
const modal = document.getElementById("stockModal");
const closeBtn = document.getElementById("modalClose");
const captureBtn = document.getElementById("modalCaptureBtn");

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");
const detailSubtabs = document.querySelectorAll("[data-detail-subtab]");
const detailSubtabPanels = document.querySelectorAll(".detail-subtab-panel");
const rangeButtons = document.querySelectorAll(".range-btn");

let priceChart = null;
let currentStock = null;
let currentRange = "6M";
let activeTableFilter = "all";
let activeSectorFilter = "전체";
let activeIndexFilter = document.querySelector(".index-chip.active")?.dataset.indexKey || "";
const stockDetailCache = new Map();

function reportClientError(payload) {
    const config = window.APP_MONITORING || {};

    if (!config.enabled || !config.clientErrorEndpoint) {
        return;
    }

    const body = JSON.stringify({
        ...payload,
        path: window.location.pathname,
        href: window.location.href,
        userAgent: navigator.userAgent,
        occurredAt: new Date().toISOString(),
    });

    try {
        fetch(config.clientErrorEndpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body,
            keepalive: true,
        }).catch(() => {});
    } catch (error) {
        // Reporting must never break the app itself.
    }
}

window.addEventListener("error", (event) => {
    reportClientError({
        type: "error",
        message: event.message,
        source: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
    });
});

window.addEventListener("unhandledrejection", (event) => {
    const reason = event.reason || {};

    reportClientError({
        type: "unhandledrejection",
        message: reason.message || String(reason),
        stack: reason.stack,
    });
});

async function fetchStockDetail(ticker) {
    const config = window.APP_MONITORING || {};
    const endpoint = config.stockDetailEndpoint || "/api/stock/detail";
    const cacheKey = `${CURRENT_MARKET || "US"}:${ticker}`;

    if (stockDetailCache.has(cacheKey)) {
        return stockDetailCache.get(cacheKey);
    }

    const url = new URL(endpoint, window.location.origin);
    url.searchParams.set("market", CURRENT_MARKET || "US");
    url.searchParams.set("ticker", ticker);

    const response = await fetch(url.toString());

    if (!response.ok) {
        throw new Error(`상세 데이터를 불러오지 못했습니다. (${response.status})`);
    }

    const stock = await response.json();
    stockDetailCache.set(cacheKey, stock);
    return stock;
}

function formatChange(value) {
    if (value === null || value === undefined) {
        return "N/A";
    }

    return value >= 0 ? `+${value}%` : `${value}%`;
}

function getNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isNaN(number) ? fallback : number;
}

function setText(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}

function clearChildren(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

function getModalCssText() {
    return Array.from(document.styleSheets)
        .map((sheet) => {
            try {
                return Array.from(sheet.cssRules)
                    .map((rule) => rule.cssText)
                    .join("\n");
            } catch (error) {
                return "";
            }
        })
        .join("\n");
}

function downloadDataUrl(dataUrl, filename) {
    const link = document.createElement("a");
    link.href = dataUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
}

function canvasToImageInClone(source, clone) {
    const sourceCanvases = source.querySelectorAll("canvas");
    const cloneCanvases = clone.querySelectorAll("canvas");

    sourceCanvases.forEach((canvas, index) => {
        const targetCanvas = cloneCanvases[index];

        if (!targetCanvas) {
            return;
        }

        const image = document.createElement("img");

        try {
            image.src = canvas.toDataURL("image/png");
        } catch (error) {
            return;
        }

        image.style.width = `${canvas.clientWidth || canvas.width}px`;
        image.style.height = `${canvas.clientHeight || canvas.height}px`;
        targetCanvas.replaceWith(image);
    });
}

async function captureModalImage() {
    const source = document.querySelector(".stock-detail-modal");

    if (!source || !currentStock) {
        return;
    }

    const originalText = captureBtn ? captureBtn.textContent : "";

    if (captureBtn) {
        captureBtn.disabled = true;
        captureBtn.textContent = "저장 중...";
    }

    try {
        const clone = source.cloneNode(true);
        canvasToImageInClone(source, clone);

        const width = Math.ceil(source.scrollWidth);
        const height = Math.ceil(source.scrollHeight);
        const cssText = getModalCssText();
        const svg = `
            <svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}">
                <foreignObject width="100%" height="100%">
                    <div xmlns="http://www.w3.org/1999/xhtml">
                        <style>
                            body { margin: 0; background: #ffffff; }
                            ${cssText}
                            .stock-detail-modal { position: static !important; width: ${width}px !important; max-height: none !important; overflow: visible !important; transform: none !important; }
                            .detail-body { max-height: none !important; overflow: visible !important; }
                        </style>
                        ${clone.outerHTML}
                    </div>
                </foreignObject>
            </svg>
        `;
        const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const image = new Image();

        image.onload = () => {
            const canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext("2d");
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, width, height);
            ctx.drawImage(image, 0, 0);
            URL.revokeObjectURL(url);
            downloadDataUrl(canvas.toDataURL("image/png"), `${currentStock.ticker}-detail.png`);

            if (captureBtn) {
                captureBtn.disabled = false;
                captureBtn.textContent = originalText;
            }
        };

        image.onerror = () => {
            URL.revokeObjectURL(url);
            console.warn("[CAPTURE ERROR]", "capture render failed");
            alert("캡처를 저장하지 못했습니다. 브라우저 보안 설정 때문에 실패했을 수 있어요.");

            if (captureBtn) {
                captureBtn.disabled = false;
                captureBtn.textContent = originalText;
            }
        };

        image.src = url;
    } catch (error) {
        console.warn("[CAPTURE ERROR]", error);
        alert("캡처를 저장하지 못했습니다. 브라우저 보안 설정 때문에 실패했을 수 있어요.");

        if (captureBtn) {
            captureBtn.disabled = false;
            captureBtn.textContent = originalText;
        }
    }
}

function pickHeroCopy(stock, copies) {
    const seed = `${stock.ticker || ""}${stock.score || ""}`
        .split("")
        .reduce((sum, char) => sum + char.charCodeAt(0), 0);

    return copies[seed % copies.length];
}

function getLegacyHeroByStock(stock) {
    const grade = stock.grade || "F";
    const score = getNumber(stock.score);
    const rsi = getNumber(stock.rsi);
    const change = getNumber(stock.change);
    const volumeRatio = getNumber(stock.volume_ratio);
    const highDiff = calcHigh52wDiff(stock);
    const sectorText = `${stock.sector || ""} ${stock.description || ""}`.toLowerCase();
    const highDiffNumber = typeof highDiff === "string" ? Number(highDiff.replace("%", "")) : null;
    const isNearHigh = Number.isFinite(highDiffNumber) && highDiffNumber >= -5;
    const isDeepPullback = Number.isFinite(highDiffNumber) && highDiffNumber <= -25;
    const isQuietStrong = score >= 78 && volumeRatio < 1.0;
    const isLeader = score >= 80 && rsi >= 50 && rsi <= 70;
    const isLowBuyCandidate = score >= 55 && rsi <= 42;
    const isSemiconductor = /semiconductor|반도체|hbm|gpu|chip/.test(sectorText);
    const isCloud = /cloud|software|ai|data|platform|클라우드|소프트웨어/.test(sectorText);
    const isHealth = /health|bio|pharma|medical|헬스|바이오|의료|제약/.test(sectorText);
    const isFinance = /financial|bank|insurance|금융|은행|보험/.test(sectorText);
    const isEnergy = /energy|oil|gas|utilities|에너지|가스|유틸리티/.test(sectorText);

    const variants = [
        {
            when: () => score >= 92 && rsi < 72,
            className: "hero-elite",
            letter: "S",
            copies: [
                {
                    title: "얘는 시험지 걷기 전에 이미 상위권 냄새남",
                    subtitle: `점수 ${score} · 추세/수급/퀄리티가 같이 살아있는 희귀 카드`,
                },
                {
                    title: "좋은 종목은 설명이 길어지기 전에 차트가 먼저 말함",
                    subtitle: `등급 ${grade} · RSI ${rsi} · 그래도 진입가는 무조건 따져야 함`,
                },
                {
                    title: "이 정도면 종목이 아니라 시장의 인기투표 1열",
                    subtitle: `점수 ${score} · 강한 놈은 강하지만 추격은 늘 비싸다`,
                },
                {
                    title: "계좌가 좋아하는 재료를 꽤 많이 들고 있음",
                    subtitle: `등급 ${grade} · 거래량 ${volumeRatio.toFixed(1)}x · 손절선만 세우면 볼만함`,
                },
            ],
        },
        {
            when: () => isLeader,
            className: "hero-leader",
            letter: "L",
            copies: [
                {
                    title: "시장보다 한 발 앞서 걷는 놈은 이유가 있음",
                    subtitle: `점수 ${score} · RSI ${rsi} · 주도주 후보, 눌림 타이밍 체크`,
                },
                {
                    title: "얘는 남 눈치보다 자기 추세를 더 믿는 타입",
                    subtitle: `등급 ${grade} · 중립 이상 RSI · 추세 꺾이는지만 보자`,
                },
                {
                    title: "주도주는 비싸 보일 때도 계속 비싸지는 척함",
                    subtitle: `점수 ${score} · 고점 추격보다 지지 확인이 먼저`,
                },
                {
                    title: "시장이 흔들려도 먼저 일어나는 애들이 있음",
                    subtitle: `등급 ${grade} · 상대강도 양호 · 거래량 확인하면 더 좋음`,
                },
            ],
        },
        {
            when: () => isQuietStrong && rsi < 72,
            className: "hero-stealth",
            letter: "H",
            copies: [
                {
                    title: "조용한 강자는 소리 없이 계좌에 들어오려 함",
                    subtitle: `점수 ${score} · 거래량 ${volumeRatio.toFixed(1)}x · 아직 과열 소음은 적음`,
                },
                {
                    title: "남들이 덜 떠드는 종목이 가끔 제일 무서움",
                    subtitle: `등급 ${grade} · 추세는 좋은데 수급 과열은 아님`,
                },
                {
                    title: "불꽃놀이 전 조용한 운동장 같은 느낌",
                    subtitle: `점수 ${score} · 거래량 확인 대기 · 터지면 빨라질 수 있음`,
                },
                {
                    title: "티 안 내고 올라가는 놈은 뒤늦게 보면 비싸져 있음",
                    subtitle: `RSI ${rsi} · 숨은강자 후보 · 기준선 이탈만 조심`,
                },
            ],
        },
        {
            when: () => isLowBuyCandidate,
            className: "hero-lowbuy",
            letter: "DIP",
            copies: [
                {
                    title: "싸게 줍는 척하다가 칼날 잡는지만 확인",
                    subtitle: `RSI ${rsi} · 점수 ${score} · 저점매수 후보, 반등 캔들 필요`,
                },
                {
                    title: "할인매장인지 폐업정리인지 구분해야 함",
                    subtitle: `등급 ${grade} · 눌림 구간 · 거래량 회복 전까진 천천히`,
                },
                {
                    title: "바닥 냄새는 나는데 지하실 문도 같이 보임",
                    subtitle: `RSI ${rsi} · 반등 확인 후 접근 · 성급하면 교육비 냄`,
                },
                {
                    title: "저점매수는 멋있지만 너무 빠르면 그냥 물림",
                    subtitle: `점수 ${score} · 손절 짧게 · 지지선 확인 필수`,
                },
            ],
        },
        {
            when: () => isDeepPullback && score >= 45,
            className: "hero-pullback",
            letter: "P",
            copies: [
                {
                    title: "많이 빠진 건 기회일 수도 있고 사고현장일 수도 있음",
                    subtitle: `52주 고가 대비 ${highDiff} · 점수 ${score} · 회복 신호부터 확인`,
                },
                {
                    title: "낙폭이 크다고 자동으로 싸지는 건 아님",
                    subtitle: `RSI ${rsi} · 눌림 깊음 · 추세 복구 전까진 관망 우세`,
                },
                {
                    title: "떨어진 칼인지 할인 쿠폰인지 아직 판정 중",
                    subtitle: `등급 ${grade} · 52주 고가 대비 ${highDiff} · 분할 접근만 허용`,
                },
                {
                    title: "반등 나오면 재밌고, 안 나오면 오래 아픔",
                    subtitle: `점수 ${score} · 리스크 먼저 · 거래량 붙는지 보자`,
                },
            ],
        },
        {
            when: () => score >= 85 && isNearHigh && rsi < 72,
            className: "hero-breakout",
            letter: "B",
            copies: [
                {
                    title: "이건 차트가 아니라 계단으로 올라가는 중임",
                    subtitle: `점수 ${score} · 52주 고가 대비 ${highDiff} · 고점 근처에서 안 죽는 놈`,
                },
                {
                    title: "남들 겁먹을 때 얘는 고점 문 두드리는 중",
                    subtitle: `등급 ${grade} · 추세 살아있음 · 추격은 말고 눌림에서 노려볼 카드`,
                },
                {
                    title: "이 정도면 시장이 얘한테 자리 비켜주는 중",
                    subtitle: `52주 고가 대비 ${highDiff} · 힘은 좋은데 욕심내면 바로 혼남`,
                },
                {
                    title: "신고가 근처에서 버티는 놈은 이유가 있음",
                    subtitle: `점수 ${score} · 가격 힘 유지 · 손절선 없이 들어가면 그건 기도임`,
                },
            ],
        },
        {
            when: () => volumeRatio >= 1.4 && change > 0 && rsi < 72,
            className: "hero-volume",
            letter: "V",
            copies: [
                {
                    title: "거래량 붙었다. 조용히 누가 사고 있다는 뜻일 수도",
                    subtitle: `거래량 ${volumeRatio.toFixed(1)}x · 등락률 ${formatChange(change)} · 수급 냄새 확인`,
                },
                {
                    title: "갑자기 시끄러워진 종목은 그냥 지나치면 안 됨",
                    subtitle: `거래량 ${volumeRatio.toFixed(1)}x · 가격 반응 있음 · 단타 손 조심`,
                },
                {
                    title: "얘 오늘 심박수 올라감. 이유는 찾아봐야 함",
                    subtitle: `등락률 ${formatChange(change)} · 평소보다 거래량 증가 · 뉴스/수급 체크`,
                },
                {
                    title: "거래량 없이 오른 건 꿈이고, 얘는 일단 소리는 남",
                    subtitle: `거래량 ${volumeRatio.toFixed(1)}x · 점수 ${score} · 진짜 수급인지 확인`,
                },
            ],
        },
        {
            when: () => rsi >= 72,
            className: "hero-overheat",
            letter: "!",
            copies: [
                {
                    title: "지금 추천해주는 사람은 네 계좌랑 원수진 거임",
                    subtitle: `RSI ${rsi} · 좋아 보여도 단기 과열 · 추격매수 금지 구간`,
                },
                {
                    title: "맛있어 보이는데 방금 전자레인지에서 나온 상태",
                    subtitle: `RSI ${rsi} · 손 대면 뜨거움 · 식는지 보고 들어가도 안 늦음`,
                },
                {
                    title: "차는 좋은데 지금 타면 안전벨트부터 매야 함",
                    subtitle: `등급 ${grade} · RSI 과열 · 눌림 없는 진입은 벌금 씨게 냄`,
                },
                {
                    title: "불꽃놀이 예쁘다고 손으로 잡으면 계좌가 탐",
                    subtitle: `RSI ${rsi} · 단기 흥분 구간 · 분할 아니면 구경이 낫다`,
                },
            ],
        },
        {
            when: () => rsi <= 35 && score >= 45,
            className: "hero-rebound",
            letter: "R",
            copies: [
                {
                    title: "많이 맞긴 했는데 아직 살아는 있음",
                    subtitle: `RSI ${rsi} · 점수 ${score} · 반등 후보지만 확인 없이 들어가면 같이 맞음`,
                },
                {
                    title: "바닥 같아 보일 때 지하실 문 열리는 경우 많음",
                    subtitle: `RSI ${rsi} · 과매도권 · 반등 신호 확인 후 접근`,
                },
                {
                    title: "쌈마이 가격이라고 다 보석은 아님",
                    subtitle: `점수 ${score} · 가격은 눌림 · 거래량 회복 전까진 의심부터`,
                },
                {
                    title: "얘는 구조대 기다리는 중이지 축제 중이 아님",
                    subtitle: `RSI ${rsi} · 손절선 짧게 · 반등 나오면 그때 판단`,
                },
            ],
        },
        {
            when: () => isSemiconductor && score >= 65,
            className: "hero-chip",
            letter: "AI",
            copies: [
                {
                    title: "AI 붙은 종목이라고 다 천국행 티켓은 아님",
                    subtitle: `${stock.sector} · 점수 ${score} · 진짜 실적이 붙는지 확인`,
                },
                {
                    title: "반도체는 좋을 땐 왕, 꺾이면 롤러코스터임",
                    subtitle: `${stock.description} · 모멘텀 있음 · 고점 매수 조심`,
                },
                {
                    title: "GPU 냄새 나면 시장이 일단 쳐다보긴 함",
                    subtitle: `점수 ${score} · AI 수혜 체크 · 기대감만 있으면 위험`,
                },
                {
                    title: "얘가 진짜 AI 수혜주인지 이름만 AI인지 까봐야 함",
                    subtitle: `${stock.sector} · 거래량 ${volumeRatio.toFixed(1)}x · 실적 연결 확인`,
                },
            ],
        },
        {
            when: () => isCloud && score >= 60,
            className: "hero-cloud",
            letter: "C",
            copies: [
                {
                    title: "클라우드는 멋있는데 숫자가 안 붙으면 그냥 안개임",
                    subtitle: `${stock.description} · 점수 ${score} · 매출 성장 확인`,
                },
                {
                    title: "구독 매출은 달콤하지만 밸류에이션은 매움",
                    subtitle: `${stock.sector} · 점수 ${score} · 성장값과 현금흐름 점검`,
                },
                {
                    title: "소프트웨어 종목은 꿈값 빠지면 표정 싹 바뀜",
                    subtitle: `점수 ${score} · 추세와 실적 같이 확인 · 이름값만 믿지 말기`,
                },
                {
                    title: "데이터 장사 잘하면 무섭고, 못하면 그냥 PPT임",
                    subtitle: `${stock.description} · 점수 ${score} · 현금흐름 체크`,
                },
            ],
        },
        {
            when: () => isHealth,
            className: "hero-health",
            letter: "+",
            copies: [
                {
                    title: "바이오는 한 방도 있지만 한 방에 계좌도 감",
                    subtitle: `${stock.sector} · 점수 ${score} · 이벤트 리스크 체크`,
                },
                {
                    title: "좋은 약은 병을 고치고, 나쁜 진입은 계좌를 아프게 함",
                    subtitle: `${stock.description} · 점수 ${score} · 임상/실적 일정 확인`,
                },
                {
                    title: "헬스케어는 방어주인 척하다가 가끔 세게 때림",
                    subtitle: `RSI ${rsi} · 변동성 주의 · 뉴스 확인 필수`,
                },
                {
                    title: "파이프라인 좋다는 말만 듣고 사면 실험체 되는 거임",
                    subtitle: `${stock.sector} · 데이터와 실적 둘 다 봐야 함`,
                },
            ],
        },
        {
            when: () => isFinance,
            className: "hero-finance",
            letter: "$",
            copies: [
                {
                    title: "은행주는 심심해 보여도 돈 냄새는 제일 솔직함",
                    subtitle: `${stock.sector} · 점수 ${score} · 금리/연체/자본비율 체크`,
                },
                {
                    title: "배당 보고 들어갔다가 주가로 맞으면 그게 진짜 금융교육",
                    subtitle: `${stock.description} · 점수 ${score} · 방어력 확인`,
                },
                {
                    title: "금융주는 멋보다 숫자임. 허세 부리면 바로 들킴",
                    subtitle: `점수 ${score} · 수익성/리스크 같이 보기`,
                },
                {
                    title: "이 종목은 시장보다 금리 눈치를 더 많이 봄",
                    subtitle: `${stock.sector} · 등락률 ${formatChange(change)} · 매크로 영향 체크`,
                },
            ],
        },
        {
            when: () => isEnergy,
            className: "hero-energy",
            letter: "E",
            copies: [
                {
                    title: "유가 따라 웃고 우는 종목, 감정기복 장난 아님",
                    subtitle: `${stock.sector} · 등락률 ${formatChange(change)} · 원자재 사이클 체크`,
                },
                {
                    title: "에너지주는 잘 타면 난방비 벌고, 못 타면 계좌가 탐",
                    subtitle: `${stock.description} · 점수 ${score} · 사이클 진입 위치 확인`,
                },
                {
                    title: "현금흐름 좋다고 무작정 사면 유가가 뒤통수침",
                    subtitle: `거래량 ${volumeRatio.toFixed(1)}x · 변동성 관리 필요`,
                },
                {
                    title: "얘는 실적표보다 원자재 차트를 먼저 보는 게 맞음",
                    subtitle: `${stock.sector} · 등락률 ${formatChange(change)} · 매크로 민감`,
                },
            ],
        },
        {
            when: () => grade === "S" || grade === "A",
            className: "hero-quality",
            letter: grade,
            copies: [
                {
                    title: "장사 잘하는 기업은 조정에도 돈이 붙는다",
                    subtitle: `등급 ${grade} · 점수 ${score} · 근데 몰빵하면 그건 실력이 아니라 객기`,
                },
                {
                    title: "이 정도면 적어도 쓰레기통에서는 건진 종목",
                    subtitle: `등급 ${grade} · 추세 양호 · 그래도 진입가는 따져야 함`,
                },
                {
                    title: "추천받고 산 게 아니라 네가 고른 거면 꽤 괜찮음",
                    subtitle: `점수 ${score} · 리스크 관리만 하면 볼만한 카드`,
                },
                {
                    title: "시장이 흔들려도 얘는 쉽게 표정 안 무너지는 타입",
                    subtitle: `등급 ${grade} · 안정적 추세 · 손절선은 그래도 필수`,
                },
                {
                    title: "좋은 종목도 비싸게 사면 마음고생은 공짜가 아님",
                    subtitle: `등급 ${grade} · RSI ${rsi} · 진입 타점만 차분히 보자`,
                },
                {
                    title: "이 정도면 관심종목에 넣어도 욕은 덜 먹음",
                    subtitle: `점수 ${score} · 재료와 추세 둘 다 살아있는 편`,
                },
                {
                    title: "강한 놈은 강한데, 네 매수가도 강해야 함",
                    subtitle: `등급 ${grade} · 거래량 ${volumeRatio.toFixed(1)}x · 기준가 체크`,
                },
            ],
        },
        {
            when: () => grade === "B" || grade === "C",
            className: "hero-neutral",
            letter: grade,
            copies: [
                {
                    title: "애매한 종목은 사람 마음을 제일 피곤하게 함",
                    subtitle: `등급 ${grade} · 점수 ${score} · 확신 없으면 현금도 포지션임`,
                },
                {
                    title: "나쁘진 않은데 막 설레지도 않음. 딱 그 느낌",
                    subtitle: `등급 ${grade} · 타이밍 확인 · 괜히 먼저 뛰지 말기`,
                },
                {
                    title: "이 종목은 고백하기 전에 썸인지 착각인지 확인해야 함",
                    subtitle: `점수 ${score} · 추세/거래량 둘 다 체크`,
                },
                {
                    title: "지금 사면 수익보다 스트레스가 먼저 올 수도 있음",
                    subtitle: `등급 ${grade} · 방향성 애매 · 조건 충족 기다리기`,
                },
                {
                    title: "괜찮아 보이는데 결정타가 아직 안 보임",
                    subtitle: `점수 ${score} · 한 가지 신호 더 붙으면 볼만함`,
                },
                {
                    title: "좋지도 나쁘지도 않은 종목이 제일 오래 고민시킴",
                    subtitle: `등급 ${grade} · 거래량 ${volumeRatio.toFixed(1)}x · 확신 생길 때까지 대기`,
                },
                {
                    title: "지금은 주연보다 조연 느낌. 대사 더 들어봐야 함",
                    subtitle: `점수 ${score} · 추세/수급 중 하나는 더 필요`,
                },
            ],
        },
        {
            when: () => grade === "D",
            className: "hero-weak",
            letter: "D",
            copies: [
                {
                    title: "가능성은 있는데 지금은 숙제가 너무 많음",
                    subtitle: `등급 ${grade} · 점수 ${score} · 반등 확인 전까진 관망`,
                },
                {
                    title: "사고 싶다는 마음보다 안 사야 할 이유가 더 큼",
                    subtitle: `RSI ${rsi} · 추세 약함 · 급하게 들어갈 자리 아님`,
                },
                {
                    title: "얘는 아직 면접 대기실임. 합격 통보 아님",
                    subtitle: `점수 ${score} · 거래량 ${volumeRatio.toFixed(1)}x · 조건 더 필요`,
                },
                {
                    title: "계좌에 넣기 전에 왜 떨어졌는지부터 물어봐야 함",
                    subtitle: `등급 ${grade} · 리스크 우선 · 지지선 확인`,
                },
            ],
        },
        {
            when: () => grade === "F",
            className: "hero-danger",
            letter: "F",
            copies: [
                {
                    title: "지금은 매수 버튼보다 뒤로가기 버튼이 더 예쁨",
                    subtitle: `등급 ${grade} · 점수 ${score} · 회복 신호 없으면 관망`,
                },
                {
                    title: "이 종목은 용기가 아니라 보호장비가 필요함",
                    subtitle: `RSI ${rsi} · 리스크 높음 · 반등 확인 전까지 접근 금지`,
                },
                {
                    title: "싸 보여서 샀다가 더 싼 가격 구경할 수 있음",
                    subtitle: `점수 ${score} · 추세 약함 · 바닥 확인 필수`,
                },
                {
                    title: "계좌가 심심하다고 이런 걸 넣으면 안 됨",
                    subtitle: `등급 ${grade} · 변동성 조심 · 먼저 살아남기`,
                },
            ],
        },
    ];

    const selected = variants.find((variant) => variant.when());

    if (selected) {
        return {
            className: selected.className,
            letter: selected.letter,
            ...pickHeroCopy(stock, selected.copies),
        };
    }

    const riskCopies = [
        {
            title: "이 종목 추천해준 사람은 네 인생 망하라고 추천한 거임",
            subtitle: `등급 ${grade} · 점수 ${score} · 일단 살아남는 게 먼저`,
        },
        {
            title: "계좌에 스릴이 부족하면 몰라도 굳이 이걸?",
            subtitle: `등급 ${grade} · 추세 약함 · 손 대기 전에 이유 세 개는 말해야 함`,
        },
        {
            title: "이건 투자라기보다 벌칙 수행에 가까움",
            subtitle: `점수 ${score} · 리스크 우선 · 반등 확인 전까지 관망`,
        },
        {
            title: "싸다고 샀다가 더 싸지는 걸 교육비라고 부름",
            subtitle: `등급 ${grade} · 리스크 큼 · 바닥 확인 없으면 접근 금지`,
        },
        {
            title: "이 차트 보고 설렜다면 잠깐 물부터 마시고 와야 함",
            subtitle: `점수 ${score} · 감정매수 금지 · 데이터가 아직 약함`,
        },
        {
            title: "이건 종목 분석보다 자기통제가 먼저 필요한 구간",
            subtitle: `등급 ${grade} · 반등 확인 전까지 손가락 잠금`,
        },
        {
            title: "수익률보다 후회율이 먼저 떠오르는 그림",
            subtitle: `점수 ${score} · 추세 회복 전엔 관망이 전략`,
        },
    ];

    return {
        className: "hero-risk",
        letter: grade,
        ...pickHeroCopy(stock, riskCopies),
    };
}

function getOptionalNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
}

function formatHeroNumber(value, digits = 0) {
    if (!Number.isFinite(value)) {
        return "N/A";
    }

    return value.toFixed(digits).replace(/\.0+$/, "");
}

function getHeroFactLine(stock, score, rsi, change, volumeRatio, highDiff) {
    const facts = [`점수 ${score}`];

    if (Number.isFinite(rsi)) {
        facts.push(`RSI ${formatHeroNumber(rsi, 1)}`);
    }

    if (Number.isFinite(volumeRatio) && volumeRatio > 0) {
        facts.push(`거래량 ${volumeRatio.toFixed(1)}x`);
    }

    if (Number.isFinite(change)) {
        facts.push(`등락 ${formatChange(change)}`);
    }

    if (highDiff !== "N/A") {
        facts.push(`52주고가 ${highDiff}`);
    }

    if (stock.sector) {
        facts.push(stock.sector);
    }

    return facts.slice(0, 5).join(" · ");
}

function buildHeroComment(metrics) {
    const { score, rsi, change, volumeRatio, highDiffNumber, moatScore } = metrics;
    const notes = [];

    if (score >= 85) {
        notes.push("점수는 상위권입니다");
    } else if (score >= 70) {
        notes.push("기본기는 통과권입니다");
    } else if (score >= 55) {
        notes.push("아직 확인할 조건이 남아 있습니다");
    } else {
        notes.push("지금은 리스크 체크가 먼저입니다");
    }

    if (Number.isFinite(rsi) && rsi >= 72) {
        notes.push("RSI 과열이라 추격은 부담입니다");
    } else if (Number.isFinite(rsi) && rsi <= 35) {
        notes.push("과매도권이지만 반등 확인이 필요합니다");
    }

    if (Number.isFinite(volumeRatio) && volumeRatio >= 1.6 && Number.isFinite(change) && change > 0) {
        notes.push("거래량과 가격 반응이 같이 붙었습니다");
    } else if (Number.isFinite(volumeRatio) && volumeRatio >= 1.6 && Number.isFinite(change) && change < 0) {
        notes.push("거래량 동반 하락이라 매도 압력도 봐야 합니다");
    } else if (Number.isFinite(volumeRatio) && volumeRatio < 0.8) {
        notes.push("거래량이 얇아 신호 확신은 낮습니다");
    }

    if (Number.isFinite(highDiffNumber) && highDiffNumber >= -5) {
        notes.push("52주 고가 근처라 힘은 살아 있습니다");
    } else if (Number.isFinite(highDiffNumber) && highDiffNumber <= -30) {
        notes.push("고점 대비 낙폭이 커 회복 확인이 중요합니다");
    }

    if (Number.isFinite(moatScore) && moatScore >= 7) {
        notes.push("해자 점수가 높아 장기 경쟁력은 플러스입니다");
    }

    return notes.slice(0, 2).join(" · ");
}

function getHeroByStock(stock) {
    const grade = stock.grade || "F";
    const score = getNumber(stock.score);
    const rsi = getOptionalNumber(stock.rsi);
    const change = getOptionalNumber(stock.change);
    const volumeRatio = getOptionalNumber(stock.volume_ratio);
    const moatScore = getOptionalNumber(stock.moat?.total);
    const highDiff = calcHigh52wDiff(stock);
    const highDiffNumber = typeof highDiff === "string" ? Number(highDiff.replace("%", "")) : null;
    const sectorText = `${stock.sector || ""} ${stock.description || ""}`.toLowerCase();
    const factLine = getHeroFactLine(stock, score, rsi, change, volumeRatio, highDiff);
    const baseComment = buildHeroComment({ score, rsi, change, volumeRatio, highDiffNumber, moatScore });
    const isNearHigh = Number.isFinite(highDiffNumber) && highDiffNumber >= -7;
    const isDeepPullback = Number.isFinite(highDiffNumber) && highDiffNumber <= -25;
    const isSeverePullback = Number.isFinite(highDiffNumber) && highDiffNumber <= -45;
    const isOverheat = Number.isFinite(rsi) && rsi >= 72;
    const isOversold = Number.isFinite(rsi) && rsi <= 35;
    const isHealthyRsi = Number.isFinite(rsi) && rsi >= 45 && rsi <= 68;
    const isHighVolume = Number.isFinite(volumeRatio) && volumeRatio >= 1.5;
    const isQuietVolume = Number.isFinite(volumeRatio) && volumeRatio > 0 && volumeRatio < 0.85;
    const isUp = Number.isFinite(change) && change > 0;
    const isDown = Number.isFinite(change) && change < 0;
    const hasStrongMoat = Number.isFinite(moatScore) && moatScore >= 7;
    const isSemiconductor = /semiconductor|반도체|hbm|gpu|chip/.test(sectorText);
    const isCloud = /cloud|software|ai|data|platform|클라우드|소프트웨어|인터넷/.test(sectorText);
    const isHealth = /health|bio|pharma|medical|헬스|바이오|의료|제약/.test(sectorText);
    const isFinance = /financial|bank|insurance|금융|은행|보험/.test(sectorText);
    const isEnergy = /energy|oil|gas|utilities|에너지|가스|유틸리티/.test(sectorText);
    const isDefense = /defense|aerospace|우주|방산|항공|위성|드론/.test(sectorText);
    const isConsumer = /consumer|retail|food|restaurant|beauty|소비|유통|푸드|음료|뷰티|외식/.test(sectorText);

    const variants = [
        {
            when: () => score >= 92 && !isOverheat,
            className: "hero-elite",
            letter: "S",
            copies: [
                ["숫자가 먼저 합격 도장 찍은 최상위권", "점수는 매우 높습니다. 매수가는 차분히 따져야 합니다"],
                ["좋은 종목이라는 말보다 데이터가 먼저 말함", "추세와 점수는 강합니다. 추격보다 기준가가 중요합니다"],
                ["관심종목 맨 위에 올릴 자격은 있음", "팩트는 좋습니다. 다만 좋은 기업도 비싸게 사면 피곤합니다"],
                ["이 정도면 시장이 그냥 지나치기 어려움", "상위 점수권입니다. 눌림과 거래량 유지 여부를 보세요"],
            ],
        },
        {
            when: () => score >= 86 && hasStrongMoat && !isOverheat,
            className: "hero-quality",
            letter: "MOAT",
            copies: [
                ["점수도 높은데 해자까지 있으면 얘기가 달라짐", "경쟁 우위 점수가 높습니다. 장기 체력은 플러스입니다"],
                ["장사 잘하고 방어력도 있는 타입", "해자와 종합점수가 같이 좋습니다. 단기 타점만 따로 보세요"],
                ["쉽게 무너지지 않는 기업은 조정 때 표정이 다름", "경쟁력은 양호합니다. 가격 부담만 체크하면 됩니다"],
            ],
        },
        {
            when: () => score >= 82 && isHealthyRsi,
            className: "hero-leader",
            letter: "L",
            copies: [
                ["시장보다 앞서 걷는 주도주 후보", "RSI가 과열 전이고 점수도 높습니다. 눌림에서 더 예쁩니다"],
                ["힘은 있는데 아직 정신줄은 잡고 있음", "추세 양호. 고점 추격보다 지지 확인이 낫습니다"],
                ["차트가 버티는 이유가 숫자에도 있음", "주도주 후보지만 손절선 없는 진입은 금지입니다"],
                ["강한데 아직 폭주 모드는 아님", "점수와 RSI 균형이 좋습니다. 거래량 유지가 핵심입니다"],
            ],
        },
        {
            when: () => score >= 78 && isQuietVolume && !isOverheat,
            className: "hero-stealth",
            letter: "H",
            copies: [
                ["조용한데 점수는 높은 숨은 강자", "거래량 과열 없이 버티는 중입니다. 수급 붙는 날을 보세요"],
                ["아직 시끄럽진 않은데 데이터는 괜찮음", "관심종목에 넣고 거래량 붙는 날을 기다릴 만합니다"],
                ["소문보다 숫자가 먼저 움직이는 타입", "좋은 조용함인지 무관심인지 다음 수급이 판정합니다"],
                ["시장 관심은 적은데 성적표는 나쁘지 않음", "거래량만 살아나면 카드 색깔이 달라질 수 있습니다"],
            ],
        },
        {
            when: () => isOverheat && score >= 70,
            className: "hero-overheat",
            letter: "HOT",
            copies: [
                ["좋은 종목이어도 지금은 손이 뜨거운 구간", "RSI 과열입니다. 따라 사면 수익보다 심장박동이 먼저 옵니다"],
                ["차트는 신났고 매수자는 조심해야 함", "단기 과열 신호입니다. 눌림 확인 전 추격은 벌점이 큽니다"],
                ["불꽃은 예쁜데 손으로 잡는 건 다른 문제", "강하면 눌림 후에도 기회는 옵니다. 지금은 속도 조절입니다"],
                ["급등 구간은 박수칠 자리와 살 자리가 다름", "점수는 좋아도 단기 과열이면 진입 타이밍은 따로 봐야 합니다"],
            ],
        },
        {
            when: () => isOversold && score >= 45,
            className: "hero-rebound",
            letter: "LOW",
            copies: [
                ["많이 식었다. 이제 반등 증거가 필요함", "과매도권이지만 바닥 확인 전엔 칼날일 수 있습니다"],
                ["저점매수 후보지만 확인 버튼은 아직 안 눌림", "가격은 눌렸고 리스크는 남아 있습니다. 분할만 허용입니다"],
                ["싸 보이는 것과 싸진 것은 다름", "RSI는 낮습니다. 거래량 회복이 붙어야 이야기가 됩니다"],
                ["바닥 냄새는 나는데 지하실 문도 같이 보임", "과매도는 신호일 뿐입니다. 반등 캔들과 거래량을 보세요"],
            ],
        },
        {
            when: () => isSeverePullback,
            className: "hero-danger",
            letter: "DROP",
            copies: [
                ["많이 빠진 건 팩트, 안전하다는 뜻은 아님", "52주 고가 대비 낙폭이 큽니다. 회복 신호 전엔 방어가 먼저입니다"],
                ["할인매장인지 사고현장인지 아직 판정 중", "낙폭은 큽니다. 거래량 없는 반등은 믿기 어렵습니다"],
                ["싸 보여서 들어갔다가 더 싼 가격 볼 수 있음", "고점 대비 크게 밀렸습니다. 바닥 확인이 먼저입니다"],
            ],
        },
        {
            when: () => isDeepPullback && score >= 45,
            className: "hero-pullback",
            letter: "DIP",
            copies: [
                ["낙폭은 큰데 회복 신호는 따로 봐야 함", "52주 고가 대비 많이 빠졌습니다. 싸다보다 살아나는지가 중요합니다"],
                ["할인인지 사고현장인지 아직 판정 중", "반등 캔들과 거래량 없으면 섣불리 줍지 않는 쪽이 낫습니다"],
                ["많이 내려온 건 사실. 그래서 더 조심", "가격 매력은 생겼지만 추세 복구가 먼저입니다"],
                ["눌림은 기회가 될 수 있지만 확인은 별개", "지지선 회복과 거래량 동반 여부가 핵심입니다"],
            ],
        },
        {
            when: () => score >= 82 && isNearHigh && !isOverheat,
            className: "hero-breakout",
            letter: "B",
            copies: [
                ["고점 근처에서 안 죽는 건 힘이 있다는 뜻", "52주 고가 부근입니다. 추격보다 눌림 매수가 더 깔끔합니다"],
                ["신고가 문 앞에서 버티는 종목", "힘은 좋습니다. 다만 매수가는 네 편이어야 합니다"],
                ["위로 가려는 의지는 보임", "가격 힘이 유지되는 중입니다. 거래량까지 붙으면 더 선명합니다"],
                ["천장 근처에서 버틴다는 건 시장 관심이 있다는 뜻", "신고가 근접 구간입니다. 돌파 후 안착 여부를 보세요"],
            ],
        },
        {
            when: () => isHighVolume && isUp && !isOverheat,
            className: "hero-volume",
            letter: "VOL",
            copies: [
                ["거래량이 붙었다. 시장이 쳐다보기 시작함", "평소보다 손이 많이 탄 날입니다. 뉴스와 수급을 확인하세요"],
                ["조용하던 종목이 갑자기 말이 많아짐", "거래량 증가와 가격 반응이 같이 나왔습니다. 진짜 수급인지 체크입니다"],
                ["오늘은 그냥 지나치기 아까운 거래량", "단기 신호는 좋지만 다음 날 follow-through가 중요합니다"],
                ["가격도 오르고 거래량도 붙었다면 일단 메모", "단기 관심은 충분합니다. 장대양봉 뒤 추격은 조심하세요"],
            ],
        },
        {
            when: () => isHighVolume && isDown,
            className: "hero-risk",
            letter: "SELL",
            copies: [
                ["거래량이 붙었는데 내려갔다면 좋은 소리만은 아님", "매도 압력 가능성이 있습니다. 반등 전까지 확인이 필요합니다"],
                ["사람들이 몰렸는데 가격이 밀리면 조심해야 함", "거래량 동반 하락입니다. 수급 방향을 다시 확인하세요"],
                ["시끄럽게 빠지는 종목은 일단 거리두기", "거래량과 하락이 같이 나왔습니다. 회복 캔들이 먼저입니다"],
            ],
        },
        {
            when: () => isSemiconductor && score >= 60,
            className: "hero-chip",
            letter: "AI",
            copies: [
                ["AI 수혜주는 이름보다 실적 연결이 핵심", "반도체/AI 재료는 좋습니다. 숫자로 이어지는지 확인하세요"],
                ["반도체는 좋을 땐 빠르고 꺾일 땐 더 빠름", "모멘텀은 있지만 진입가는 보수적으로 잡는 게 낫습니다"],
                ["AI 간판 달았으면 매출표도 같이 봐야 함", "테마만으로는 부족합니다. 거래량과 실적 확인입니다"],
                ["칩 이야기는 뜨겁고, 숫자는 더 뜨거워야 함", "테마 프리미엄이 실적으로 연결되는지 봐야 합니다"],
            ],
        },
        {
            when: () => isCloud && score >= 60,
            className: "hero-cloud",
            letter: "C",
            copies: [
                ["클라우드는 멋있지만 현금흐름이 본체", "성장주는 숫자 약해지면 프리미엄이 빨리 빠집니다"],
                ["플랫폼 종목은 꿈값과 실적값을 분리해야 함", "이름값보다 매출 성장과 마진 확인입니다"],
                ["데이터 장사 잘하면 무섭고 못하면 그냥 PPT", "사업성은 좋을 수 있습니다. 밸류 부담을 같이 보세요"],
                ["소프트웨어는 꿈이 크고 조정도 빠름", "매출 성장, 마진, 현금흐름을 같이 봐야 합니다"],
            ],
        },
        {
            when: () => isHealth && score >= 50,
            className: "hero-health",
            letter: "+",
            copies: [
                ["바이오는 이벤트 하나에 표정이 바뀜", "임상/실적/승인 일정 확인 없이는 들어가기 애매합니다"],
                ["헬스케어는 방어주처럼 보여도 변동성은 있음", "뉴스 리스크와 일정 체크가 먼저입니다"],
                ["좋은 약도 나쁜 진입가를 치료하진 못함", "사업성보다 먼저 리스크 일정을 확인하세요"],
                ["의료주는 숫자와 이벤트 둘 다 봐야 함", "실적 안정성과 일정 리스크를 같이 체크하세요"],
            ],
        },
        {
            when: () => isFinance && score >= 50,
            className: "hero-finance",
            letter: "$",
            copies: [
                ["금융주는 결국 숫자가 말한다", "금리, 자본비율, 연체 리스크를 같이 봐야 합니다"],
                ["배당만 보고 사면 주가가 교육시킬 수 있음", "방어력은 좋을 수 있지만 매크로 민감도 체크입니다"],
                ["심심해 보여도 돈 냄새는 솔직한 업종", "수익성은 숫자로, 리스크는 금리로 확인하세요"],
                ["금융주는 화려함보다 안정성이 본체", "수익성과 건전성 지표를 같이 봐야 합니다"],
            ],
        },
        {
            when: () => isEnergy && score >= 50,
            className: "hero-energy",
            letter: "E",
            copies: [
                ["이 종목은 실적표와 원자재 차트를 같이 봐야 함", "유가/가스/전력 사이클 영향이 큽니다"],
                ["에너지는 현금흐름 좋다가도 사이클이 뒤통수침", "원자재 방향과 마진 체크가 필요합니다"],
                ["매크로 바람을 정면으로 맞는 업종", "좋은 구간이면 강하지만 타이밍이 중요합니다"],
                ["에너지는 숫자보다 사이클이 먼저 움직일 때가 많음", "가격 변수와 수익성 추세를 같이 보세요"],
            ],
        },
        {
            when: () => isDefense && score >= 55,
            className: "hero-defense",
            letter: "DEF",
            copies: [
                ["방산·우주는 재료는 강한데 변동성도 같이 옴", "수주와 실적 전환이 진짜 포인트입니다"],
                ["테마는 뜨겁고 숫자는 확인해야 함", "뉴스보다 매출 인식과 마진을 먼저 보세요"],
                ["우주로 가는 이야기라도 손절선은 지상에 있어야 함", "재료는 좋지만 가격 변동성 관리가 필요합니다"],
            ],
        },
        {
            when: () => isConsumer && score >= 55,
            className: "hero-consumer",
            letter: "BUY",
            copies: [
                ["소비주는 결국 사람들이 계속 사주느냐가 핵심", "매출 성장과 마진 방어력을 같이 확인하세요"],
                ["브랜드는 좋아도 주가는 숫자를 봄", "수요가 꾸준한지, 비용 압박은 없는지 체크입니다"],
                ["유행은 빠르고 실적은 느리게 확인됨", "인기와 이익률이 같이 가는지 봐야 합니다"],
            ],
        },
        {
            when: () => grade === "A" || grade === "B",
            className: "hero-quality",
            letter: grade,
            copies: [
                ["데이터는 괜찮다. 이제 타이밍 싸움", "점수와 등급은 양호합니다. 매수가는 욕심 줄여야 합니다"],
                ["관심종목에 넣을 이유는 충분함", "강점은 보이지만 무리한 추격은 별개 문제입니다"],
                ["좋은 후보지만 가격표를 먼저 봐야 함", "종목은 괜찮아도 비싸게 사면 피곤합니다"],
                ["기본기는 있다. 이제 네 진입가가 문제", "좋은 후보입니다. 기준가와 손절선을 먼저 정하세요"],
                ["완벽하진 않아도 볼 이유는 충분함", "강점이 보입니다. 약점은 거래량과 가격 위치에서 확인하세요"],
            ],
        },
        {
            when: () => score >= 60 && score < 70 && isUp,
            className: "hero-watch",
            letter: "W",
            copies: [
                ["살짝 좋아지는 중인데 아직 합격은 아님", "상승 반응은 있습니다. 점수가 더 올라오는지 보세요"],
                ["분위기는 나아졌지만 확신은 이르다", "가격은 반응했습니다. 거래량과 추세 확인이 필요합니다"],
                ["이제 막 고개 드는 후보", "한 번 더 좋은 캔들이 나오면 관심도가 올라갑니다"],
            ],
        },
        {
            when: () => grade === "C" || grade === "D",
            className: "hero-neutral",
            letter: grade,
            copies: [
                ["애매한 구간. 한 가지 신호가 더 필요함", "나쁘진 않지만 확신 주기엔 아직 부족합니다"],
                ["지금은 매수보다 관찰이 더 깔끔함", "조건이 더 붙으면 볼만하고, 아니면 그냥 지나가도 됩니다"],
                ["데이터가 반만 설득하는 종목", "추세나 거래량 중 하나는 더 살아나야 합니다"],
                ["할인인지 사고인지 아직 구분 안 됨", "확인 신호가 부족합니다. 급하게 살 이유는 약합니다"],
                ["지켜볼 수는 있는데 설레면 안 되는 구간", "점수와 신호가 중간권입니다. 기다림이 유리합니다"],
            ],
        },
        {
            when: () => score < 45 && isOversold,
            className: "hero-weak",
            letter: "WAIT",
            copies: [
                ["많이 빠졌다고 바로 기회는 아님", "과매도지만 점수가 낮습니다. 반등 확인 전엔 관망입니다"],
                ["바닥처럼 보여도 아직 데이터가 약함", "낮은 RSI보다 낮은 점수가 더 문제입니다"],
                ["싸 보이는 종목은 항상 이유가 있음", "회복 신호와 거래량이 붙기 전까지 기다리세요"],
            ],
        },
        {
            when: () => true,
            className: "hero-danger",
            letter: grade,
            copies: [
                ["지금은 매수 버튼보다 관망 버튼이 더 예쁨", "점수와 신호가 약합니다. 회복 확인 전엔 무리 금지입니다"],
                ["싸 보여도 더 싸질 수 있는 구간", "추세 회복 전까지는 계좌 보호가 우선입니다"],
                ["이건 기회보다 리스크 설명서가 먼저 보임", "반등 증거가 나오기 전까진 구경이 전략입니다"],
                ["지금 들어가면 분석보다 기도가 많아질 수 있음", "데이터가 약합니다. 조건 충족 전엔 기다리는 쪽이 낫습니다"],
                ["차트가 내 편이라는 증거가 아직 부족함", "거래량, 추세, 점수 중 하나는 더 살아나야 합니다"],
            ],
        },
    ];

    const selected = variants.find((variant) => variant.when());
    const heroCopy = pickHeroCopy(
        stock,
        selected.copies.map(([copyTitle, copyComment]) => ({
            title: copyTitle,
            facts: factLine,
            comment: baseComment ? `${copyComment} · ${baseComment}` : copyComment,
            subtitle: `${factLine} · ${copyComment}`,
        }))
    );

    return {
        className: selected.className,
        letter: selected.letter,
        title: heroCopy.title,
        subtitle: heroCopy.subtitle,
        facts: heroCopy.facts,
        comment: heroCopy.comment,
    };
}

function clamp(value, min = 0, max = 100) {
    return Math.min(max, Math.max(min, value));
}

function setBar(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.style.width = `${clamp(value)}%`;
    }
}

function setScoreText(id, value) {
    const element = document.getElementById(id);

    if (!element) {
        return;
    }

    const score = Number(value || 0);
    element.textContent = score.toFixed(1);
    element.classList.toggle("bad", score < 40);
    element.classList.toggle("mid", score >= 40 && score < 68);
}

function getStockHigh52w(stock) {
    const savedHigh = getNumber(stock.high_52w);

    if (savedHigh > 0) {
        return savedHigh;
    }

    const yearlyPrices = stock.chart?.["1Y"]?.prices || [];
    const chartHigh = yearlyPrices
        .map((price) => Number(price))
        .filter((price) => Number.isFinite(price) && price > 0)
        .reduce((max, price) => Math.max(max, price), 0);

    return chartHigh;
}

function calcHigh52wDiff(stock) {
    const high = getStockHigh52w(stock);
    const price = getNumber(stock.price);

    if (!high || !price) {
        return "N/A";
    }

    return `${Math.round(((price - high) / high) * 100)}%`;
}

function renderPeerRows(stock) {
    const tbody = document.getElementById("modalPeerRows");

    if (!tbody) {
        return;
    }

    const peers = STOCKS
        .filter((item) => item.sector === stock.sector || item.ticker === stock.ticker)
        .sort((a, b) => Number(b.score || 0) - Number(a.score || 0))
        .slice(0, 6);

    tbody.innerHTML = "";

    peers.forEach((item) => {
        const row = document.createElement("tr");
        row.className = item.ticker === stock.ticker ? "current-peer" : "";
        row.innerHTML = `
            <td>
                <strong>${item.name}</strong>
                <span>${item.ticker}</span>
            </td>
            <td>${item.score}</td>
            <td>${item.market_cap || "N/A"}</td>
            <td>${item.price}</td>
            <td class="${item.change >= 0 ? "up" : "down"}">
                ${item.change >= 0 ? "+" : ""}${item.change}%
            </td>
            <td>${item.rsi}</td>
        `;
        tbody.appendChild(row);
    });
}

function renderInsiderTransactions(stock) {
    const insider = stock.insider_transactions || {};
    const list = document.getElementById("insiderList");

    setText("insiderBuyTotal", insider.buy_total || "$0");
    setText("insiderSellTotal", insider.sell_total || "$0");
    setText("insiderCount", insider.count || 0);
    setText("insiderNetTotal", `${insider.net_label || "순매매"} ${insider.net_total || "—"}`);
    setText("insiderSource", insider.source || "SEC Form 4 (yfinance)");

    if (!list) {
        return;
    }

    list.innerHTML = "";

    if (!insider.items || insider.items.length === 0) {
        list.innerHTML = `<div class="reference-empty">표시할 인사이더 거래가 없습니다.</div>`;
        return;
    }

    insider.items.forEach((item) => {
        const row = document.createElement("div");
        row.className = "insider-row";
        row.innerHTML = `
            <span class="reference-date">${item.date}</span>
            <span class="insider-action ${item.action_type}">${item.action}</span>
            <div>
                <strong>${item.holder}</strong>
                <small>${item.position || ""}</small>
            </div>
            <b>${item.value}</b>
        `;
        list.appendChild(row);
    });
}

function renderStockEvents(stock) {
    const events = stock.stock_events || {};
    const list = document.getElementById("stockEventList");

    setText("stockEventCount", `${events.count || 0}건`);
    setText("stockEventSource", events.source || "yfinance 캘린더");

    if (!list) {
        return;
    }

    list.innerHTML = "";

    if (!events.items || events.items.length === 0) {
        list.innerHTML = `<div class="reference-empty">120일 이내 표시할 종목 일정이 없습니다.</div>`;
        return;
    }

    events.items.forEach((item) => {
        const row = document.createElement("div");
        row.className = "event-row";
        row.innerHTML = `
            <span class="event-dday">${item.d_label}</span>
            <span class="event-type">${item.type}</span>
            <strong>${item.label}</strong>
            <time>${item.date}</time>
        `;
        list.appendChild(row);
    });
}

function renderNews(stock) {
    const news = stock.news || {};
    setText("modalNewsHeadline", news.headline || "표시할 뉴스가 없습니다.");

    const newsSentiment = document.getElementById("modalNewsSentiment");

    if (newsSentiment) {
        newsSentiment.textContent = news.sentiment || "Neutral";
        newsSentiment.className = `news-badge ${news.sentiment_type || "yellow"}`;
    }

    const newsList = document.getElementById("modalNewsList");

    if (!newsList) {
        return;
    }

    newsList.innerHTML = "";

    if (!news.items || news.items.length === 0) {
        newsList.innerHTML = `
            <div class="modal-news-empty">
                표시할 뉴스가 없습니다.
            </div>
        `;
        return;
    }

    news.items.forEach((item) => {
        const div = document.createElement("div");
        div.className = "modal-news-item";

        div.innerHTML = `
            <div>
                <strong>${item.title}</strong>
                <p>${item.publisher || "Yahoo Finance"}</p>
            </div>
            <span class="news-badge ${item.sentiment_type}">
                ${item.sentiment}
            </span>
        `;

        if (item.link) {
            div.addEventListener("click", () => {
                window.open(item.link, "_blank");
            });
            div.classList.add("clickable");
        }

        newsList.appendChild(div);
    });
}

function updateInsightReference(stock) {
    const insider = stock.insider_transactions || {};
    const events = stock.stock_events || {};
    const news = stock.news || {};
    const isKr = stock.ticker.endsWith(".KS") || stock.ticker.endsWith(".KQ");

    setText("modalInsightNews", news.sentiment || "Neutral");
    setText("modalInsightNewsText", news.headline || "최근 뉴스 데이터 확인 중");
    setText(
        "modalInsightInsider",
        `${insider.net_label || "순매매"} ${insider.net_total || "—"}`
    );
    setText(
        "modalInsightInsiderText",
        isKr ? "한국 종목은 SEC Form 4 미지원" : `${insider.count || 0}건 · SEC Form 4 기반`
    );
    setText("modalInsightEvents", `${events.count || 0}건`);
    setText("modalInsightEventsText", events.source || "yfinance 캘린더 기반");
}

async function loadReferenceData(stock, force = false) {
    if (!stock || stock.reference_loading || (!force && stock.reference_loaded)) {
        return;
    }

    stock.reference_loading = true;

    try {
        const response = await fetch(
            `/api/stock/reference?ticker=${encodeURIComponent(stock.ticker)}&t=${Date.now()}`
        );

        if (!response.ok) {
            throw new Error(`reference api ${response.status}`);
        }

        const data = await response.json();
        stock.insider_transactions = data.insider_transactions || stock.insider_transactions;
        stock.stock_events = data.stock_events || stock.stock_events;
        stock.news = data.news || stock.news;
        stock.reference_loaded = true;

        if (currentStock && currentStock.ticker === stock.ticker) {
            renderInsiderTransactions(stock);
            renderStockEvents(stock);
            renderNews(stock);
            updateInsightReference(stock);
        }
    } catch (error) {
        console.warn("[REFERENCE LOAD ERROR]", stock.ticker, error);
    } finally {
        stock.reference_loading = false;
    }
}

function updateMoatAxisBars(axes) {
    const axisMap = {
        switching_cost: ["moatSwitchingBar", "moatSwitchingScore"],
        network_effect: ["moatNetworkBar", "moatNetworkScore"],
        intangible_assets: ["moatAssetBar", "moatAssetScore"],
        cost_advantage: ["moatCostBar", "moatCostScore"],
        roic_durability: ["moatRoicBar", "moatRoicScore"],
    };
    const values = {};

    (axes || []).forEach((axis) => {
        values[axis.key] = axis;
    });

    Object.entries(axisMap).forEach(([key, ids]) => {
        const axis = values[key] || {};
        const score = getNumber(axis.score);
        const maxScore = getNumber(axis.max_score || 2) || 2;
        const percent = clamp((score / maxScore) * 100);

        setBar(ids[0], percent);
        setText(ids[1], `${score.toFixed(1).replace(".0", "")}/${maxScore}`);
    });
}

function updateDetailMetrics(stock) {
    const score = getNumber(stock.score);
    const rsi = getNumber(stock.rsi);
    const volumeRatio = getNumber(stock.volume_ratio);
    const targetFactor = clamp(getNumber(stock.target_change) + 50);
    const trendScore = stock.ma_status === "정배열" ? 85 : 45;
    const rsiScore = clamp(100 - Math.abs(rsi - 55) * 2);
    const macdScore = stock.macd?.status_type === "up" ? 82 : stock.macd?.status_type === "down" ? 35 : 55;
    const momentumScore = clamp(score + getNumber(stock.change));
    const drawdownScore = clamp(100 - Math.abs(getNumber(stock.backtest?.mdd)));
    const supplyScore = clamp(volumeRatio * 50);
    const epsScore = clamp(getNumber(stock.canslim?.items?.[0]?.passed ? 82 : 56));
    const roeScore = clamp(getNumber(stock.canslim?.items?.[1]?.passed ? 88 : 18));
    const newHighScore = clamp(stock.canslim?.items?.[2]?.passed ? 88 : 10);

    setText("modalSectorBadge", stock.sector);
    setText("modalRs", score);
    setText("modalRiskScore", `Risk ${Math.max(1, 100 - score)} /99 주의`);
    setText("modalMarketCap", stock.market_cap || "N/A");
    setText("modalMarketCapDetail", stock.market_cap || "N/A");
    setText("modalAverageVolume", stock.average_volume || "N/A");
    setText("modalAverageVolumeDetail", stock.average_volume || "N/A");
    setText("modalVolumeRatio", `${volumeRatio.toFixed(1)}×`);
    setText("modalHigh52wDiff", calcHigh52wDiff(stock));
    setText("modalTargetChange", formatChange(stock.target_change));
    setText("modalPeerSector", stock.sector);
    const moat = stock.moat || {};
    const moatAxes = moat.axes || [];
    const moatTotal = getNumber(moat.total);

    setText("modalMoatLabel", moat.label || "해자 평가");
    setText("modalMoatScore", `${moatTotal.toFixed(1).replace(".0", "")}/10`);
    setText("modalMoatText", moat.summary
        ? `${stock.name}은(는) ${stock.description} 영역에서 경쟁합니다. ${moat.summary}. 종합점수에는 최대 10점까지 가산됩니다.`
        : `${stock.name}은(는) ${stock.description} 영역에서 경쟁합니다. 해자 데이터는 전환비용·네트워크·무형자산·원가우위·ROIC 지속성 기준으로 계산됩니다.`);
    setText("modalTimingHeadline", stock.reason ? stock.reason.join(" · ") : stock.signal);
    setText("modalTechnicalHeadline", `${stock.ticker} 기술 지표`);
    setText("modalTechnicalSummary", `RSI ${stock.rsi || "N/A"} · ${stock.ma_status || "-"} · ${stock.macd?.status || "-"} · 거래량 ${volumeRatio.toFixed(1)}×`);
    setText("modalTechnicalRsiText", `${stock.rsi_status || "중립"} 구간입니다.`);
    setText("modalTechnicalMaText", `${stock.ma_status || "-"} 상태입니다.`);
    setText("modalTechnicalMacdText", `${stock.macd?.status || "-"} 신호입니다.`);
    setText("modalTechnicalVolumeText", `평균 대비 ${volumeRatio.toFixed(1)}배 거래량입니다.`);
    setText("modalFinancialPrice", stock.price_display || stock.price || "N/A");
    setText("modalFinancialRs", score);
    setText("modalFinancialTarget", stock.target || "N/A");
    setText("modalInsightHeadline", stock.ticker.endsWith(".KS") || stock.ticker.endsWith(".KQ") ? "KR 인사이트" : "US 인사이트");
    setText("modalInsightReason", Array.isArray(stock.reason) ? stock.reason[0] : (stock.signal || "-"));

    const yahoo = document.getElementById("modalYahooLink");
    if (yahoo) {
        yahoo.href = `https://finance.yahoo.com/quote/${stock.ticker}`;
    }

    const fearMarker = document.getElementById("modalFearMarker");
    if (fearMarker) {
        fearMarker.style.left = `${clamp(score)}%`;
    }

    setScoreText("modalMomentumScore", momentumScore);
    setScoreText("modalTrendScore", trendScore);
    setScoreText("modalDrawdownScore", drawdownScore);
    setScoreText("modalSmartMoneyScore", supplyScore);
    setScoreText("modalTargetFactor", targetFactor);
    setScoreText("modalTechnicalRsiScore", rsiScore);
    setScoreText("modalTechnicalMaScore", trendScore);
    setScoreText("modalTechnicalMacdScore", macdScore);
    setScoreText("modalTechnicalVolumeScore", supplyScore);
    setScoreText("modalEpsScore", epsScore);
    setScoreText("modalRoeScore", roeScore);
    setScoreText("modalNewHighScore", newHighScore);
    setScoreText("modalSupplyScore", supplyScore);

    setBar("modalMomentumBar", momentumScore);
    setBar("modalTrendBar", trendScore);
    setBar("modalDrawdownBar", drawdownScore);
    setBar("modalSmartMoneyBar", supplyScore);
    setBar("modalTargetBar", targetFactor);
    setBar("modalTechnicalRsiBar", rsiScore);
    setBar("modalTechnicalMaBar", trendScore);
    setBar("modalTechnicalMacdBar", macdScore);
    setBar("modalTechnicalVolumeBar", supplyScore);
    setBar("modalEpsBar", epsScore);
    setBar("modalRoeBar", roeScore);
    setBar("modalNewHighBar", newHighScore);
    setBar("modalSupplyBar", supplyScore);
    updateMoatAxisBars(moatAxes);

    renderPeerRows(stock);
    renderInsiderTransactions(stock);
    renderStockEvents(stock);
    updateInsightReference(stock);
}

function updateHeroByStock(stock) {
    const grade = stock.grade || "F";
    const gradeType = stock.grade_type || "grade-f";
    const hero = getHeroByStock(stock);
    const heroCard = document.getElementById("modalHeroCard");
    const heroSubtitle = document.getElementById("modalHeroSubtitle");

    setText("modalHeroTitle", hero.title);
    setText("modalHeroGrade", hero.letter || grade);
    setText("modalGradeBadge", grade);

    if (heroSubtitle) {
        clearChildren(heroSubtitle);

        const factLine = document.createElement("span");
        factLine.className = "hero-facts";
        factLine.textContent = hero.facts || hero.subtitle || "";
        heroSubtitle.appendChild(factLine);

        if (hero.comment) {
            const commentLine = document.createElement("span");
            commentLine.className = "hero-comment";
            commentLine.textContent = hero.comment;
            heroSubtitle.appendChild(commentLine);
        }
    }

    if (heroCard) {
        heroCard.className = `detail-hero ${hero.className}`;
    }

    const badge = document.getElementById("modalGradeBadge");

    if (badge) {
        badge.className = `grade-badge ${gradeType}`;
    }
}

async function openModal(ticker) {
    let stock = STOCKS.find((item) => item.ticker === ticker);

    if (!stock) {
        return;
    }

    try {
        stock = {
            ...stock,
            ...await fetchStockDetail(ticker),
        };
    } catch (error) {
        console.warn("[STOCK DETAIL ERROR]", error);
        reportClientError({
            type: "stock-detail",
            message: error.message,
            ticker,
        });
    }

    currentStock = stock;
    currentRange = "6M";
    updateRangeButtons();
    activateDetailSubtab("canslim");

    setText("modalName", stock.name);
    setText("modalTicker", stock.ticker);
    setText("modalDescription", stock.description);
    setText("modalScore", stock.score);
    updateHeroByStock(stock);
    updateDetailMetrics(stock);

    setText("modalPrice", stock.price_display || stock.price);
    setText("modalChange", formatChange(stock.change));
    setText("modalRsi", stock.rsi);

    const premarket = document.getElementById("modalPremarket");
    if (premarket) {
        premarket.textContent = stock.premarket_price
            ? `$${stock.premarket_price} (${formatChange(stock.premarket_change)})`
            : "N/A";
    }

    const aftermarket = document.getElementById("modalAftermarket");
    if (aftermarket) {
        aftermarket.textContent = stock.aftermarket_price
            ? `$${stock.aftermarket_price} (${formatChange(stock.aftermarket_change)})`
            : "N/A";
    }

    renderNews(stock);
    loadReferenceData(stock, true);

    const rsiStatus = document.getElementById("modalRsiStatus");
    if (rsiStatus) {
        rsiStatus.textContent = stock.rsi_status;
        rsiStatus.className = stock.rsi_status_type;
    }

    const maStatus = document.getElementById("modalMaStatus");
    if (maStatus) {
        maStatus.textContent = stock.ma_status;
        maStatus.className = stock.ma_status_type;
    }

    const macdStatus = document.getElementById("modalMacdStatus");
    if (macdStatus && stock.macd) {
        macdStatus.textContent = stock.macd.status;
        macdStatus.className = stock.macd.status_type;
    }

    const price = getNumber(stock.price);
    const atr = getNumber(stock.atr, price * 0.03);

    const buy = price;
    const stop = price - (atr * 1.5);
    const tp1 = price + (atr * 2);
    const tp2 = price + (atr * 3);

    setText("entryBuy", buy.toFixed(2));
    setText("entryStop", stop.toFixed(2));
    setText("entryTp1", tp1.toFixed(2));
    setText("entryTp2", tp2.toFixed(2));

    const atrElement = document.getElementById("modalAtr");
    if (atrElement) {
        atrElement.textContent = atr.toFixed(2);
    }

    const canslim = stock.canslim;

    if (canslim) {
        setText("modalCanslimScore", canslim.score);
        setText("modalCanslimCount", `${canslim.passed_count}/${canslim.total_count}`);

        const summaryCanslimScore = document.getElementById("summaryCanslimScore");
        if (summaryCanslimScore) {
            summaryCanslimScore.textContent = `${canslim.passed_count}/7`;
        }

        const list = document.getElementById("modalCanslimList");

        if (list) {
            list.innerHTML = "";

            canslim.items.forEach((item) => {
                const div = document.createElement("div");
                div.className = item.passed ? "canslim-pass" : "canslim-fail";
                div.innerHTML = `
                    <b>${item.key}</b>
                    <span>
                        <strong>${item.label} · ${item.score ?? (item.passed ? 82 : 45)}점</strong><br>
                        ${item.description}
                    </span>
                `;
                list.appendChild(div);
            });
        }
    }

    const backtest = stock.backtest;

    if (backtest) {
        setText("backtestTradeCount", backtest.trade_count);
        setText("backtestWinRate", `${backtest.win_rate}%`);
        setText("backtestAvgReturn", `${backtest.avg_return}%`);
        setText("backtestMdd", `${backtest.mdd}%`);
    }

    modal.classList.remove("hidden");

    setTimeout(() => {
        renderPriceChart(stock, currentRange);
    }, 50);
}

function closeModal() {
    modal.classList.add("hidden");
}

function activateDetailSubtab(target) {
    detailSubtabs.forEach((button) => {
        button.classList.toggle("active", button.dataset.detailSubtab === target);
    });

    detailSubtabPanels.forEach((panel) => {
        panel.classList.toggle("active", panel.id === `detailSubtab-${target}`);
    });
}

function updateRangeButtons() {
    rangeButtons.forEach((button) => {
        button.classList.toggle("active", button.dataset.range === currentRange);
    });

    setText("chartRangeLabel", currentRange);
}

function renderPriceChart(stock, range = "6M") {
    const canvas = document.getElementById("priceChart");

    if (!canvas || !stock.chart || !stock.chart[range]) {
        return;
    }

    const ctx = canvas.getContext("2d");
    const chart = stock.chart[range];

    if (priceChart) {
        priceChart.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 180);
    gradient.addColorStop(0, "rgba(34, 197, 94, 0.25)");
    gradient.addColorStop(1, "rgba(34, 197, 94, 0.02)");

    priceChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: chart.labels,
            datasets: [
                {
                    label: `${stock.ticker} Close`,
                    data: chart.prices,
                    borderColor: "#16a34a",
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.35,
                    borderWidth: 3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                },
                {
                    label: "MA20",
                    data: chart.ma20,
                    borderColor: "#2563eb",
                    backgroundColor: "transparent",
                    fill: false,
                    tension: 0.25,
                    borderWidth: 2,
                    pointRadius: 0,
                },
                {
                    label: "MA50",
                    data: chart.ma50,
                    borderColor: "#f97316",
                    backgroundColor: "transparent",
                    fill: false,
                    tension: 0.25,
                    borderWidth: 2,
                    pointRadius: 0,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        boxWidth: 10,
                        font: {
                            size: 11,
                            weight: "bold",
                        },
                    },
                },
                tooltip: {
                    mode: "index",
                    intersect: false,
                    callbacks: {
                        label: function (context) {
                            if (context.parsed.y === null) {
                                return "";
                            }

                            return `${context.dataset.label}: $${context.parsed.y}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    display: false,
                    grid: {
                        display: false,
                    },
                },
                y: {
                    display: false,
                    grid: {
                        display: false,
                    },
                },
            },
        },
    });
}

rows.forEach((row) => {
    row.addEventListener("click", (event) => {
        
        if (event.target.classList.contains("watch-btn")) {
            return;
        }

        openModal(row.dataset.ticker);
    });
});

rangeButtons.forEach((button) => {
    button.addEventListener("click", () => {
        if (!currentStock) {
            return;
        }

        currentRange = button.dataset.range;
        updateRangeButtons();
        renderPriceChart(currentStock, currentRange);
    });
});

if (closeBtn) {
    closeBtn.addEventListener("click", closeModal);
}

if (captureBtn) {
    captureBtn.addEventListener("click", captureModalImage);
}

if (modal) {
    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });
}

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal) {
        closeModal();
    }
});

detailSubtabs.forEach((button) => {
    button.addEventListener("click", () => {
        activateDetailSubtab(button.dataset.detailSubtab);
    });
});

tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        const target = tab.dataset.tab;

        tabs.forEach((item) => item.classList.remove("active"));
        panels.forEach((panel) => panel.classList.remove("active"));

        tab.classList.add("active");

        const targetPanel = document.getElementById(target);

        if (targetPanel) {
            targetPanel.classList.add("active");
        }

        if (target === "summary" && currentStock) {
            setTimeout(() => {
                renderPriceChart(currentStock, currentRange);
            }, 50);
        }
    });
});

// ===============================
// Watchlist
// ===============================

const WATCHLIST_KEY = "quant_watchlist";

function getWatchlist() {
    return JSON.parse(localStorage.getItem(WATCHLIST_KEY) || "[]");
}

function saveWatchlist(list) {
    localStorage.setItem(WATCHLIST_KEY, JSON.stringify(list));
}

function toggleWatchlist(ticker) {
    let watchlist = getWatchlist();

    if (watchlist.includes(ticker)) {
        watchlist = watchlist.filter((item) => item !== ticker);
    } else {
        watchlist.push(ticker);
    }

    saveWatchlist(watchlist);
    renderWatchButtons();
    applyTableFilters();
}

function renderWatchButtons() {
    const watchlist = getWatchlist();

    document.querySelectorAll(".watch-btn").forEach((button) => {
        const ticker = button.dataset.ticker;

        if (watchlist.includes(ticker)) {
            button.textContent = "★";
            button.classList.add("active");
            button.setAttribute("aria-label", "관심종목 해제");
        } else {
            button.textContent = "☆";
            button.classList.remove("active");
            button.setAttribute("aria-label", "관심종목 추가");
        }
    });
}

document.querySelectorAll(".watch-btn").forEach((button) => {
    button.addEventListener("click", (event) => {
        event.stopPropagation();
        toggleWatchlist(button.dataset.ticker);
    });
});

// ===============================
// Search + Unified Table Filters
// ===============================

const stockSearchInput = document.getElementById("stockSearchInput");
const summaryTotalLabel = document.getElementById("summaryTotalLabel");
const summaryGradeLabel = document.getElementById("summaryGradeLabel");
const summarySectorLabel = document.getElementById("summarySectorLabel");
const summaryScanCount = document.getElementById("summaryScanCount");
const summaryTopGradeCount = document.getElementById("summaryTopGradeCount");
const summaryReliabilityLabel = document.getElementById("summaryReliabilityLabel");
const summaryReliabilityTooltip = document.getElementById("summaryReliabilityTooltip");
let activeEtfTheme = "";

function getVisibleStocks() {
    return Array.from(document.querySelectorAll(".stock-row"))
        .filter((row) => row.style.display !== "none")
        .map((row) => STOCKS.find((item) => item.ticker === row.dataset.ticker))
        .filter(Boolean);
}

function getRankMap(values) {
    const sorted = values
        .map((value, index) => ({ value, index }))
        .sort((a, b) => a.value - b.value);
    const ranks = new Array(values.length);

    sorted.forEach((item, rank) => {
        ranks[item.index] = rank + 1;
    });

    return ranks;
}

function getPearsonCorrelation(left, right) {
    if (left.length !== right.length || left.length < 3) {
        return null;
    }

    const leftAvg = left.reduce((sum, value) => sum + value, 0) / left.length;
    const rightAvg = right.reduce((sum, value) => sum + value, 0) / right.length;
    let numerator = 0;
    let leftVariance = 0;
    let rightVariance = 0;

    left.forEach((leftValue, index) => {
        const leftDiff = leftValue - leftAvg;
        const rightDiff = right[index] - rightAvg;
        numerator += leftDiff * rightDiff;
        leftVariance += leftDiff * leftDiff;
        rightVariance += rightDiff * rightDiff;
    });

    const denominator = Math.sqrt(leftVariance * rightVariance);
    return denominator ? numerator / denominator : null;
}

function calculateVisibleScoreReliability(stocks) {
    const scores = [];
    const returns = [];

    stocks.forEach((stock) => {
        const prices = (stock.chart?.["1Y"]?.prices || [])
            .map((price) => Number(price))
            .filter((price) => Number.isFinite(price) && price > 0);

        if (prices.length < 25) {
            return;
        }

        const startPrice = prices[prices.length - 21];
        const endPrice = prices[prices.length - 1];
        const score = Number(stock.score);

        if (!startPrice || !Number.isFinite(score)) {
            return;
        }

        scores.push(score);
        returns.push((endPrice - startPrice) / startPrice);
    });

    if (scores.length < 10) {
        return {
            label: "검증 부족 · 표본 적음",
            detail: `${scores.length}개 표본이라 신뢰도 계산이 제한됩니다.`,
        };
    }

    const ic = getPearsonCorrelation(getRankMap(scores), getRankMap(returns));

    if (ic === null) {
        return {
            label: `검증 부족 · ${scores.length}개 검증`,
            detail: "순위 상관(IC)을 계산할 데이터가 부족합니다.",
        };
    }

    let strength = "중립";

    if (ic >= 0.25) {
        strength = "좋음";
    } else if (ic >= 0.1) {
        strength = "보통";
    } else if (ic <= -0.1) {
        strength = "약함";
    } else {
        strength = "아직 약함";
    }

    return {
        label: `${strength} · ${scores.length}개 검증`,
        detail: `표시된 종목의 점수 순위와 최근 20거래일 수익률 순위 상관(IC) ${ic >= 0 ? "+" : ""}${ic.toFixed(2)}`,
    };
}

function updateScannerSummary() {
    const visibleStocks = getVisibleStocks();
    const isWatchlistMode = activeTableFilter === "watchlist";

    if (summaryTotalLabel) {
        summaryTotalLabel.textContent = isWatchlistMode ? "관심 종목" : "스캔 종목";
    }

    if (summaryGradeLabel) {
        summaryGradeLabel.textContent = isWatchlistMode ? "상승 추세" : "S등급";
    }

    if (summarySectorLabel) {
        summarySectorLabel.textContent = "섹터";
    }

    if (summaryScanCount) {
        summaryScanCount.textContent = `${visibleStocks.length}개`;
    }

    if (summaryTopGradeCount) {
        const count = isWatchlistMode
            ? visibleStocks.filter((stock) => Number(stock.score_delta) > 0).length
            : visibleStocks.filter((stock) => stock.grade === "S").length;
        summaryTopGradeCount.textContent = `${count}개`;
    }

    if (activeSectorLabel) {
        activeSectorLabel.textContent = activeSectorFilter;
    }

    if (summaryReliabilityLabel || summaryReliabilityTooltip) {
        const reliability = calculateVisibleScoreReliability(visibleStocks);

        if (summaryReliabilityLabel) {
            summaryReliabilityLabel.textContent = reliability.label;
        }

        if (summaryReliabilityTooltip) {
            summaryReliabilityTooltip.title = `현재 표시된 종목 기준입니다. ${reliability.detail}`;
        }
    }
}

function getVisibleEtfRows() {
    return Array.from(document.querySelectorAll(".etf-row"))
        .filter((row) => row.style.display !== "none");
}

function updateEtfSummary() {
    const visibleRows = getVisibleEtfRows();
    const scores = visibleRows
        .map((row) => Number(row.dataset.score || 0))
        .filter((score) => Number.isFinite(score));
    const averageScore = scores.length
        ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length)
        : 0;

    if (summaryTotalLabel) {
        summaryTotalLabel.textContent = "ETF 종목";
    }

    if (summaryGradeLabel) {
        summaryGradeLabel.textContent = "강세 ETF";
    }

    if (summarySectorLabel) {
        summarySectorLabel.textContent = "분류";
    }

    if (summaryScanCount) {
        summaryScanCount.textContent = `${visibleRows.length}개`;
    }

    if (summaryTopGradeCount) {
        summaryTopGradeCount.textContent = `${scores.filter((score) => score >= 75).length}개`;
    }

    if (activeSectorLabel) {
        activeSectorLabel.textContent = activeEtfTheme || "전체";
    }

    if (summaryReliabilityLabel) {
        summaryReliabilityLabel.textContent = `평균 ${averageScore}점`;
    }

    if (summaryReliabilityTooltip) {
        summaryReliabilityTooltip.title = "현재 표시된 ETF의 평균 점수입니다. 추세, RSI, 이동평균, 거래량을 반영합니다.";
    }
}

function applyEtfFilters() {
    document.querySelectorAll(".etf-row").forEach((row) => {
        const theme = row.dataset.theme || "";
        row.style.display = !activeEtfTheme || theme === activeEtfTheme ? "" : "none";
    });

    updateEtfSummary();
}

function applyTableFilters() {
    const keyword = stockSearchInput
        ? stockSearchInput.value.trim().toLowerCase()
        : "";

    const watchlist = getWatchlist();
    const indexMembers = typeof INDEX_MEMBERS === "undefined" ? {} : INDEX_MEMBERS;
    const activeIndexMembers = activeIndexFilter
        ? new Set((indexMembers[activeIndexFilter] || []).map((ticker) => ticker.toUpperCase()))
        : null;

    document.querySelectorAll(".stock-row").forEach((row) => {
        const rawTicker = row.dataset.ticker || "";
        const ticker = rawTicker.toLowerCase();
        const name = (row.dataset.name || "").toLowerCase();
        const description = (row.dataset.description || "").toLowerCase();
        const sector = row.dataset.sector || "";
        const stock = STOCKS.find((item) => item.ticker === rawTicker);

        const matchesKeyword =
            ticker.includes(keyword) ||
            name.includes(keyword) ||
            description.includes(keyword);

        let matchesFilter = true;

        if (activeTableFilter === "watchlist") {
            matchesFilter = watchlist.includes(row.dataset.ticker);
        }

        if (activeTableFilter === "grade") {
            matchesFilter = stock && ["S", "A"].includes(stock.grade);
        }

        if (activeTableFilter === "bottom-buy") {
            const price = Number(stock?.price || 0);
            const ma200 = Number(stock?.ma200 || 0);
            matchesFilter =
                stock &&
                stock.rsi <= 40 &&
                stock.score >= 45 &&
                (!ma200 || price >= ma200 * 0.9);
        }

        if (activeTableFilter === "oversold") {
            matchesFilter =
                stock &&
                stock.rsi <= 30;
        }

        if (activeTableFilter === "overheat") {
            const price = Number(stock?.price || 0);
            const high52w = getStockHigh52w(stock);
            const nearHigh = high52w > 0 && price >= high52w * 0.97;
            matchesFilter =
                stock &&
                (
                    stock.rsi >= 70 ||
                    nearHigh
                );
        }

        if (activeTableFilter === "leader") {
            const price = Number(stock?.price || 0);
            const high52w = getStockHigh52w(stock);
            const nearHigh = high52w > 0 && price >= high52w * 0.9;
            matchesFilter =
                stock &&
                stock.score >= 70 &&
                nearHigh &&
                stock.ma20 > stock.ma50 &&
                stock.ma50 > stock.ma200;
        }

        if (activeTableFilter === "hidden-strong") {
            matchesFilter =
                stock &&
                !["S", "A"].includes(stock.grade) &&
                stock.score >= 65 &&
                stock.rsi >= 45 &&
                stock.rsi <= 70 &&
                Number(stock.volume_ratio || 0) >= 1.1;
        }

        let matchesSector = true;

        if (activeSectorFilter !== "전체") {
            matchesSector = matchesSectorFilter(sector, activeSectorFilter);
        }

        const matchesIndex =
            !activeIndexMembers || activeIndexMembers.has(rawTicker.toUpperCase());

        row.style.display =
            matchesKeyword && matchesFilter && matchesSector && matchesIndex ? "" : "none";
    });

    updateScannerSummary();
}

if (stockSearchInput) {
    stockSearchInput.addEventListener("input", applyTableFilters);
}

document.querySelectorAll(".chip[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
        activeTableFilter = button.dataset.filter;

        document.querySelectorAll(".chip[data-filter]").forEach((item) => {
            item.classList.remove("active");
        });

        button.classList.add("active");
        applyTableFilters();
    });
});

document.querySelectorAll(".index-chip[data-index-key]").forEach((button) => {
    button.addEventListener("click", () => {
        const selectedKey = button.dataset.indexKey || "";

        activeIndexFilter = selectedKey;

        document.querySelectorAll(".index-chip[data-index-key]").forEach((item) => {
            item.classList.toggle("active", item.dataset.indexKey === activeIndexFilter);
        });

        applyTableFilters();
    });
});

// ===============================
// Market Toggle
// ===============================

document.querySelectorAll(".market-toggle-btn").forEach((button) => {
    button.addEventListener("click", () => {
        const market = button.dataset.market;
        window.location.href = `/?market=${market}`;
    });
});

async function updateAutoUpdateStatus() {
    const statusElement = document.getElementById("autoUpdateStatus");
    const progressWrap = document.getElementById("autoUpdateProgress");
    const progressBar = document.getElementById("autoUpdateProgressBar");
    const progressText = document.getElementById("autoUpdateProgressText");

    if (!statusElement) {
        return;
    }

    try {
        const response = await fetch("/api/update/status");

        if (!response.ok) {
            return;
        }

        const status = await response.json();

        if (!status.enabled) {
            statusElement.textContent = "꺼짐";
            progressWrap?.classList.add("hidden");
            return;
        }

        if (status.running) {
            const current = Number(status.current || 0);
            const total = Number(status.total || 0);
            const percent = Math.max(0, Math.min(100, Number(status.percent || 0)));
            const itemText = status.item ? ` · ${status.item}` : "";
            const countText = total ? ` ${current}/${total}` : "";

            statusElement.textContent = `${status.task || "진행중"}${countText}${itemText}`;

            if (progressWrap && progressBar && progressText) {
                progressWrap.classList.remove("hidden");
                progressBar.style.width = `${percent}%`;
                progressText.textContent = `${percent}%`;
            }

            return;
        }

        progressWrap?.classList.add("hidden");

        if (status.last_error) {
            statusElement.textContent = "오류";
            return;
        }

        statusElement.textContent = status.last_finished_at
            ? `완료 ${status.last_finished_label}`
            : "대기";
    } catch (error) {
        console.warn("[AUTO UPDATE STATUS ERROR]", error);
    }
}

// ===============================
// Sidebar Accordion + Sector Filter
// ===============================

const SECTOR_FILTER_ALIASES = {
    "조선·해운": ["조선·해운", "항공·물류"],
    "대형 조선": ["조선·해운"],
    "조선 기자재": ["조선·해운"],
    "해운·물류": ["조선·해운", "항공·물류", "물류·유통"],
    "철강·화학": ["철강·화학", "소재", "Materials"],
    "석유화학·정밀화학": ["철강·화학", "소재", "정유·에너지"],
    "철강·비철": ["철강·화학", "소재"],
    "전력 인프라": ["전력 인프라", "유틸리티", "Utilities"],
    "변압기·전력기기": ["전력 인프라"],
    "신재생·ESS": ["전력 인프라", "이차전지", "유틸리티·가스"],
    "원전·SMR": ["전력 인프라", "유틸리티·가스"],
    "전선·케이블": ["전력 인프라"],
    "EV충전·수소모빌리티": ["전력 인프라", "자동차", "이차전지"],
    "정유·에너지": ["정유·에너지", "에너지", "Energy"],
    "에너지유통·화학": ["정유·에너지", "철강·화학"],
    "정유": ["정유·에너지", "에너지", "석유 · 가스"],
    "스마트팜·에그테크": ["스마트팜·에그테크", "산업재", "필수소비재"],
    "스마트팜·농기계": ["스마트팜·에그테크", "산업재"],
    "콘텐츠·엔터": ["콘텐츠·엔터", "콘텐츠 · 엔터", "커뮤니케이션"],
    "게임": ["콘텐츠·엔터"],
    "K-엔터·IP": ["콘텐츠·엔터", "콘텐츠 · 엔터"],
    "건설 건자재": ["건설·인프라", "산업재"],
    "건자재·시멘트": ["건설·인프라", "소재"],
    "대형 건설": ["건설·인프라"],
    "건설기계·중공업": ["건설·인프라", "산업재"],
    "건설기계": ["건설·인프라", "산업재"],
    "중공업·플랜트": ["건설·인프라", "산업재"],
    "지주사·종합상사": ["지주사·종합상사", "산업재"],
    "대형 지주사": ["지주사·종합상사"],
    "종합상사·무역": ["지주사·종합상사"],
    "바이오 CDMO": ["바이오 CDMO", "바이오·헬스케어", "헬스케어"],
    "CDMO 전문": ["바이오 CDMO", "바이오·헬스케어"],
    "디지털헬스·AI의료": ["디지털헬스·AI의료", "의료기기", "바이오·헬스케어", "헬스케어"],
    "헬스케어플랫폼·EMR": ["디지털헬스·AI의료", "의료기기", "바이오·헬스케어"],
    "AI의료영상·진단": ["디지털헬스·AI의료", "의료기기", "바이오·헬스케어"],
    "금융·밸류업": ["금융", "대형은행", "결제 · 신용서비스", "Financial Services"],
    "보험": ["금융"],
    "은행·금융지주": ["금융", "대형은행"],
    "증권·자산운용": ["금융"],
    "핀테크·금융데이터": ["금융", "결제 · 신용서비스"],
    "이차전지·ESS": ["이차전지"],
    "배터리 셀": ["이차전지"],
    "배터리 소재": ["이차전지", "철강·화학"],
    "배터리 장비·리사이클": ["이차전지"],
    "사이버보안": ["사이버보안", "기술", "클라우드 소프트웨어", "응용 소프트웨어"],
    "엔드포인트·네트워크보안": ["사이버보안", "기술"],
    "AI위협분석·제로트러스트": ["사이버보안", "기술"],
    "유틸리티·가스": ["유틸리티·가스", "유틸리티", "Utilities"],
    "가스·에너지": ["유틸리티·가스", "정유·에너지", "에너지"],
    "생활인프라·환경": ["유틸리티·가스", "유틸리티"],
    "반도체": ["반도체", "Semiconductor"],
    "메모리·HBM": ["반도체"],
    "반도체장비·소재": ["반도체"],
    "시스템반도체": ["반도체"],
    "AI서버기판·패키징": ["반도체", "AI 인프라"],
    "양자컴퓨팅": ["양자컴퓨팅", "기술"],
    "양자보안·암호": ["양자컴퓨팅", "사이버보안"],
    "양자센서·하드웨어": ["양자컴퓨팅", "기술"],
    "AI 인프라": ["AI 인프라", "기술", "클라우드 소프트웨어", "인터넷 플랫폼"],
    "온디바이스AI": ["AI 인프라", "기술", "반도체", "소비자 전자기기"],
    "통신·광네트워크": ["통신", "커뮤니케이션", "AI 인프라"],
    "AI플랫폼·클라우드": ["AI 인프라", "인터넷 플랫폼", "클라우드 소프트웨어", "응용 소프트웨어", "기술"],
    "로봇·자동화": ["로봇·자동화", "산업재", "자동차", "전장·부품"],
    "산업로봇·물류자동화": ["로봇·자동화", "산업재"],
    "자율주행·전장": ["자동차", "전장·부품", "로봇·자동화"],
    "휴머노이드 부품": ["로봇·자동화", "전장·부품"],
    "바이오·헬스케어": ["바이오·헬스케어", "바이오 CDMO", "의료기기", "대형 제약", "건강보험", "헬스케어"],
    "바이오 신약": ["바이오·헬스케어", "대형 제약"],
    "비만치료제·GLP-1": ["바이오·헬스케어", "대형 제약"],
    "의료기기·디지털헬스": ["바이오·헬스케어", "의료기기", "디지털헬스·AI의료"],
    "CMO·CDMO": ["바이오 CDMO", "바이오·헬스케어"],
    "물류·유통": ["물류·유통", "항공·물류", "전자상거래", "경기소비재"],
    "유통·이커머스": ["물류·유통", "전자상거래", "K-소비재", "경기소비재"],
    "택배·종합물류": ["물류·유통", "항공·물류"],
    "K-소비재": ["K-소비재", "소비재", "필수소비재", "소비자 전자기기"],
    "면세·여행": ["K-소비재", "경기소비재"],
    "K-뷰티": ["K-소비재", "소비재"],
    "K-푸드·음료": ["K-소비재", "소비재", "필수소비재"],
    "K-방산": ["방산·항공우주", "산업재"],
    "드론·우주": ["방산·항공우주", "항공우주·방산"],
    "방산 대형주": ["방산·항공우주", "항공우주·방산"],
    "방산 부품·전자전": ["방산·항공우주", "항공우주·방산"],
    "우주·위성": ["방산·항공우주", "항공우주·방산"],
    "위성·발사체": ["방산·항공우주", "항공우주·방산"],
    "항공MRO·부품": ["방산·항공우주", "항공·물류", "산업재"],
};

function normalizeSectorFilterText(value) {
    return String(value || "")
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "")
        .replace(/[·ㆍ\-/_.]/g, "");
}

function getSectorAliases(label) {
    return SECTOR_FILTER_ALIASES[label] || [label];
}

function matchesSectorFilter(stockSector, filterLabel) {
    const normalizedSector = normalizeSectorFilterText(stockSector);

    if (!normalizedSector) {
        return false;
    }

    return getSectorAliases(filterLabel).some((alias) =>
        normalizeSectorFilterText(alias) === normalizedSector
    );
}

const activeSectorLabel = document.getElementById("activeSectorLabel");

document.querySelectorAll(".sidebar-title").forEach((title) => {
    title.addEventListener("click", () => {
        const group = title.closest(".sidebar-group");

        if (group) {
            group.classList.toggle("closed");
        }
    });
});

document.querySelectorAll(".sidebar-sub button").forEach((button) => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".sidebar-sub button").forEach((item) => {
            item.classList.remove("active");
        });

        button.classList.add("active");
        sidebarAll?.classList.remove("active");

        activeSectorFilter = button.textContent.trim();

        if (activeSectorLabel) {
            activeSectorLabel.textContent = activeSectorFilter;
        }

        applyTableFilters();
    });
});

const sidebarAll = document.querySelector(".sidebar-all");

if (sidebarAll) {
    sidebarAll.addEventListener("click", () => {
        activeSectorFilter = "전체";
        sidebarAll.classList.add("active");

        if (activeSectorLabel) {
            activeSectorLabel.textContent = "전체";
        }

        document.querySelectorAll(".sidebar-sub button").forEach((item) => {
            item.classList.remove("active");
        });

        applyTableFilters();
    });
}

// ===============================
// Scanner / ETF Tab
// ===============================

const stockScannerTab = document.getElementById("stockScannerTab");
const etfTab = document.getElementById("etfTab");
const stockScannerPanel = document.getElementById("stockScannerPanel");
const etfPanel = document.getElementById("etfPanel");
const stockIndexStrip = document.querySelector(".index-strip");

if (stockScannerTab && etfTab && stockScannerPanel && etfPanel) {
    stockScannerTab.addEventListener("click", () => {
        localStorage.setItem("quant_active_tab", "stocks");
        stockScannerTab.classList.add("active");
        etfTab.classList.remove("active");

        stockScannerPanel.classList.add("active");
        etfPanel.classList.remove("active");

        if (stockIndexStrip) {
            stockIndexStrip.classList.remove("hidden");
        }

        applyTableFilters();
    });

    etfTab.addEventListener("click", () => {
        localStorage.setItem("quant_active_tab", "etf");
        etfTab.classList.add("active");
        stockScannerTab.classList.remove("active");

        etfPanel.classList.add("active");
        stockScannerPanel.classList.remove("active");

        if (stockIndexStrip) {
            stockIndexStrip.classList.add("hidden");
        }

        applyEtfFilters();
    });

    if (localStorage.getItem("quant_active_tab") === "etf") {
        etfTab.click();
    }
}

document.querySelectorAll(".etf-chip[data-etf-theme]").forEach((button) => {
    button.addEventListener("click", () => {
        activeEtfTheme = button.dataset.etfTheme || "";

        document.querySelectorAll(".etf-chip[data-etf-theme]").forEach((item) => {
            item.classList.toggle("active", item.dataset.etfTheme === activeEtfTheme);
        });

        applyEtfFilters();
    });
});

// ===============================
// Table Sorting
// ===============================

let currentSortKey = "market_cap";
let currentSortOrder = "desc";

function getStockValue(stock, key) {
    if (!stock) {
        return 0;
    }

    if (key === "score") {
        return Number(stock.score || 0);
    }

    if (key === "price") {
        return Number(stock.price || 0);
    }

    if (key === "change") {
        return Number(stock.change || 0);
    }

    if (key === "rsi") {
        return Number(stock.rsi || 0);
    }

    if (key === "target") {
        return Number(stock.target || 0);
    }

    if (key === "average_volume") {
        return Number(stock.average_volume_value || 0) || parseCompactNumber(stock.average_volume);
    }

    if (key === "market_cap") {
        return Number(stock.market_cap_value || 0) || parseCompactNumber(stock.market_cap);
    }

    return 0;
}

function parseCompactNumber(value) {
    if (value === null || value === undefined) {
        return 0;
    }

    const text = String(value).trim().toUpperCase();

    if (!text || text === "N/A" || text === "—") {
        return 0;
    }

    const number = Number(text.replace(/[^0-9.-]/g, ""));

    if (Number.isNaN(number)) {
        return 0;
    }

    if (text.endsWith("T")) {
        return number * 1_000_000_000_000;
    }

    if (text.endsWith("B")) {
        return number * 1_000_000_000;
    }

    if (text.endsWith("M")) {
        return number * 1_000_000;
    }

    if (text.endsWith("K")) {
        return number * 1_000;
    }

    return number;
}

function sortStockTable(sortKey) {
    const tbody = document.querySelector(".stock-row")?.closest("tbody");

    if (!tbody) {
        return;
    }

    if (currentSortKey === sortKey) {
        currentSortOrder = currentSortOrder === "desc" ? "asc" : "desc";
    } else {
        currentSortKey = sortKey;
        currentSortOrder = "desc";
    }

    const sortedRows = Array.from(document.querySelectorAll(".stock-row")).sort((a, b) => {
        const stockA = STOCKS.find((item) => item.ticker === a.dataset.ticker);
        const stockB = STOCKS.find((item) => item.ticker === b.dataset.ticker);

        const valueA = getStockValue(stockA, sortKey);
        const valueB = getStockValue(stockB, sortKey);

        if (currentSortOrder === "desc") {
            return valueB - valueA;
        }

        return valueA - valueB;
    });

    sortedRows.forEach((row) => {
        tbody.appendChild(row);
    });

    updateSortHeaders();
    applyTableFilters();
}

function applyInitialStockSort() {
    const tbody = document.querySelector(".stock-row")?.closest("tbody");

    if (!tbody) {
        updateSortHeaders();
        return;
    }

    const sortedRows = Array.from(document.querySelectorAll(".stock-row")).sort((a, b) => {
        const stockA = STOCKS.find((item) => item.ticker === a.dataset.ticker);
        const stockB = STOCKS.find((item) => item.ticker === b.dataset.ticker);

        return getStockValue(stockB, currentSortKey) - getStockValue(stockA, currentSortKey);
    });

    sortedRows.forEach((row) => {
        tbody.appendChild(row);
    });

    updateSortHeaders();
}

function updateSortHeaders() {
    document.querySelectorAll(".sortable").forEach((header) => {
        const label = header.textContent
            .replace(" ▲", "")
            .replace(" ▼", "")
            .replace(" ↕", "");

        const sortKey = header.dataset.sort;

        if (sortKey === currentSortKey) {
            header.textContent = `${label} ${currentSortOrder === "desc" ? "▼" : "▲"}`;
        } else {
            header.textContent = `${label} ↕`;
        }
    });
}

document.querySelectorAll(".sortable").forEach((header) => {
    header.addEventListener("click", () => {
        sortStockTable(header.dataset.sort);
    });
});

applyInitialStockSort();

function updateMarketUpdatedLabel() {
    const elements = document.querySelectorAll(".market-updated[data-updated-at]");

    if (!elements.length) {
        return;
    }

    const updatedAt = new Date(elements[0].dataset.updatedAt);

    if (Number.isNaN(updatedAt.getTime())) {
        return;
    }

    const elapsedMinutes = Math.max(
        0,
        Math.floor((Date.now() - updatedAt.getTime()) / 60000)
    );

    const label = elapsedMinutes === 0
        ? "방금 전 갱신"
        : `${elapsedMinutes}분 전 갱신`;

    elements.forEach((element) => {
        element.textContent = label;
    });
}

// ===============================
// Anonymous Chat
// ===============================

const ANON_CHAT_KEY = "quant_anon_chat_messages";
const ANON_CHAT_DATE_KEY = "quant_anon_chat_date";
const anonChatPanel = document.getElementById("anonChatPanel");
const anonChatToggle = document.getElementById("anonChatToggle");
const anonChatForm = document.getElementById("anonChatForm");
const anonChatInput = document.getElementById("anonChatInput");
const anonChatBody = document.getElementById("anonChatBody");
const anonOnlineCount = document.getElementById("anonOnlineCount");

function getAnonChatDateKey() {
    const now = new Date();
    return [
        now.getFullYear(),
        String(now.getMonth() + 1).padStart(2, "0"),
        String(now.getDate()).padStart(2, "0"),
    ].join("-");
}

function resetExpiredAnonChat() {
    const todayKey = getAnonChatDateKey();
    const savedKey = localStorage.getItem(ANON_CHAT_DATE_KEY);

    if (!savedKey) {
        localStorage.setItem(ANON_CHAT_DATE_KEY, todayKey);
        return;
    }

    if (savedKey !== todayKey) {
        localStorage.removeItem(ANON_CHAT_KEY);
        localStorage.setItem(ANON_CHAT_DATE_KEY, todayKey);
    }
}

function getAnonMessages() {
    resetExpiredAnonChat();
    return JSON.parse(localStorage.getItem(ANON_CHAT_KEY) || "[]");
}

function saveAnonMessages(messages) {
    resetExpiredAnonChat();
    localStorage.setItem(ANON_CHAT_DATE_KEY, getAnonChatDateKey());
    localStorage.setItem(ANON_CHAT_KEY, JSON.stringify(messages.slice(-80)));
}

function getAnonName() {
    let name = localStorage.getItem("quant_anon_name");

    if (!name) {
        name = `익명${Math.floor(1000 + Math.random() * 9000)}`;
        localStorage.setItem("quant_anon_name", name);
    }

    return name;
}

function renderAnonMessages() {
    if (!anonChatBody) {
        return;
    }

    const messages = getAnonMessages();
    anonChatBody.innerHTML = "";

    if (messages.length === 0) {
        anonChatBody.innerHTML = `
            <div class="anon-chat-empty">
                아직 메시지가 없습니다. 첫 의견을 남겨보세요.
            </div>
        `;
        return;
    }

    messages.forEach((message) => {
        const item = document.createElement("div");
        item.className = "anon-message";
        item.innerHTML = `
            <div>
                <strong>${message.author}</strong>
                <time>${message.time}</time>
            </div>
            <p>${message.text}</p>
        `;
        anonChatBody.appendChild(item);
    });

    anonChatBody.scrollTop = anonChatBody.scrollHeight;
}

function updateAnonOnlineCount() {
    if (!anonOnlineCount) {
        return;
    }

    const base = getAnonMessages().length > 0 ? 1 : 0;
    anonOnlineCount.textContent = `${base}명 접속`;
}

if (anonChatToggle && anonChatPanel) {
    anonChatToggle.addEventListener("click", () => {
        anonChatPanel.classList.toggle("hidden");
        renderAnonMessages();
        updateAnonOnlineCount();

        if (!anonChatPanel.classList.contains("hidden") && anonChatInput) {
            anonChatInput.focus();
        }
    });
}

if (anonChatForm && anonChatInput) {
    anonChatForm.addEventListener("submit", (event) => {
        event.preventDefault();

        const text = anonChatInput.value.trim();

        if (!text) {
            return;
        }

        const messages = getAnonMessages();
        const now = new Date();

        messages.push({
            author: getAnonName(),
            text,
            time: `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`,
        });

        saveAnonMessages(messages);
        anonChatInput.value = "";
        renderAnonMessages();
        updateAnonOnlineCount();
    });
}

renderWatchButtons();
applyTableFilters();
updateMarketUpdatedLabel();
setInterval(updateMarketUpdatedLabel, 60000);
updateAutoUpdateStatus();
setInterval(updateAutoUpdateStatus, 2000);
renderAnonMessages();
updateAnonOnlineCount();
