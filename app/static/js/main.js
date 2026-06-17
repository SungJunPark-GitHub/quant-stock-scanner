const rows = document.querySelectorAll(".stock-row");
const modal = document.getElementById("stockModal");
const closeBtn = document.getElementById("modalClose");

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");
const rangeButtons = document.querySelectorAll(".range-btn");

let priceChart = null;
let currentStock = null;
let currentRange = "6M";
let activeTableFilter = "all";
let activeSectorFilter = "전체";

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

function getHeroByGrade(grade) {
    if (grade === "S") {
        return {
            title: "시장을 이기는 기업은 조정에도 돈이 붙는다",
            subtitle: "최상위 점수 · 강한 추세 · 우수한 상대강도",
        };
    }

    if (grade === "A") {
        return {
            title: "장사 잘하는 기업은 시장 조정에도 돈이 붙는다",
            subtitle: "우수한 점수 · 안정적 추세 · 리스크 관리 가능",
        };
    }

    if (grade === "B") {
        return {
            title: "좋은 기업도 타이밍은 따져봐야 한다",
            subtitle: "중상위 점수 · 추세 확인 · 진입 시점 점검",
        };
    }

    if (grade === "C") {
        return {
            title: "아직은 관망이 필요한 구간입니다",
            subtitle: "중립 점수 · 모멘텀 약화 · 추가 확인 필요",
        };
    }

    if (grade === "D") {
        return {
            title: "리스크 관리가 우선인 구간입니다",
            subtitle: "낮은 점수 · 추세 불안 · 보수적 접근 필요",
        };
    }

    return {
        title: "리스크가 높은 구간입니다",
        subtitle: "약한 점수 · 손실 위험 · 매수 신중",
    };
}

function updateHeroByStock(stock) {
    const grade = stock.grade || "F";
    const gradeType = stock.grade_type || "grade-f";
    const hero = getHeroByGrade(grade);

    setText("modalHeroTitle", hero.title);
    setText("modalHeroSubtitle", hero.subtitle);
    setText("modalHeroGrade", grade);
    setText("modalGradeBadge", grade);

    const badge = document.getElementById("modalGradeBadge");

    if (badge) {
        badge.className = `grade-badge ${gradeType}`;
    }
}

function openModal(ticker) {
    const stock = STOCKS.find((item) => item.ticker === ticker);

    if (!stock) {
        return;
    }

    currentStock = stock;
    currentRange = "6M";
    updateRangeButtons();

    setText("modalName", stock.name);
    setText("modalTicker", stock.ticker);
    setText("modalDescription", stock.description);
    setText("modalScore", stock.score);
    updateHeroByStock(stock);

    setText("modalPrice", stock.price);
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

    const news = stock.news;

    if (news) {
        setText("modalNewsHeadline", news.headline);

        const newsSentiment = document.getElementById("modalNewsSentiment");

        if (newsSentiment) {
            newsSentiment.textContent = news.sentiment;
            newsSentiment.className = `news-badge ${news.sentiment_type}`;
        }

        const newsList = document.getElementById("modalNewsList");

        if (newsList) {
            newsList.innerHTML = "";

            if (news.items && news.items.length > 0) {
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
            } else {
                newsList.innerHTML = `
                    <div class="modal-news-empty">
                        표시할 뉴스가 없습니다.
                    </div>
                `;
            }
        }
    }

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
                        <strong>${item.label}</strong><br>
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
        } else {
            button.textContent = "☆";
            button.classList.remove("active");
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

function applyTableFilters() {
    const keyword = stockSearchInput
        ? stockSearchInput.value.trim().toLowerCase()
        : "";

    const watchlist = getWatchlist();

    document.querySelectorAll(".stock-row").forEach((row) => {
        const ticker = (row.dataset.ticker || "").toLowerCase();
        const name = (row.dataset.name || "").toLowerCase();
        const description = (row.dataset.description || "").toLowerCase();
        const sector = (row.dataset.sector || "").toLowerCase();
        const stock = STOCKS.find((item) => item.ticker === row.dataset.ticker);

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

        if (activeTableFilter === "entry") {
            matchesFilter =
                stock &&
                stock.score >= 60 &&
                stock.rsi >= 35 &&
                stock.rsi <= 70;
        }

        if (activeTableFilter === "risk") {
            matchesFilter =
                stock &&
                (
                    stock.score < 50 ||
                    stock.rsi >= 70 ||
                    stock.signal_type === "red"
                );
        }

        const sectorText = `${ticker} ${name} ${description} ${sector}`;

        let matchesSector = true;

        if (activeSectorFilter !== "전체") {
            const keywords = getSectorKeywords(activeSectorFilter);
            matchesSector = keywords.some((keyword) =>
                sectorText.includes(keyword.toLowerCase())
            );
        }

        row.style.display =
            matchesKeyword && matchesFilter && matchesSector ? "" : "none";
    });
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

// ===============================
// Market Toggle
// ===============================

const marketSelect = document.getElementById("marketSelect");

if (marketSelect) {
    marketSelect.addEventListener("change", () => {
        const market = marketSelect.value;
        window.location.href = `/?market=${market}`;
    });
}

// ===============================
// Sidebar Accordion + Sector Filter
// ===============================

function getSectorKeywords(label) {
    const map = {
        "미드스트림·파이프라인": ["pipeline", "midstream", "energy"],
        "석유·가스 메이저": ["oil", "gas", "energy", "exxon", "chevron"],
        "원전·우라늄": ["nuclear", "uranium"],
        "게임": ["game", "gaming"],
        "소셜·애드테크": ["advertising", "social", "meta", "google"],
        "스트리밍·콘텐츠": ["streaming", "netflix", "content"],
        "데이터센터 리츠": ["reit", "data center"],
        "로봇·드론": ["robot", "drone"],
        "항공우주·방산": ["aerospace", "defense"],
        "거래소·데이터": ["exchange", "data"],
        "대형은행·IB": ["bank", "financial"],
        "크립토·블록체인": ["crypto", "blockchain"],
        "AI GPU·HBM 핵심": ["nvidia", "nvda", "amd", "semiconductor", "ai", "hbm"],
        "매그니피센트 7": ["googl", "nvda", "amzn", "aapl", "msft", "meta", "tsla", "mag 7"],
        "AI 플랫폼·클라우드": ["cloud", "software", "microsoft", "amazon", "google"],
        "대형 제약": ["pharma", "healthcare"],
        "의료기기": ["medical", "device"],
        "자동차·EV": ["auto", "automotive", "tesla", "ev"],
    };

    return map[label] || [label];
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

if (stockScannerTab && etfTab && stockScannerPanel && etfPanel) {
    stockScannerTab.addEventListener("click", () => {
        stockScannerTab.classList.add("active");
        etfTab.classList.remove("active");

        stockScannerPanel.classList.add("active");
        etfPanel.classList.remove("active");
    });

    etfTab.addEventListener("click", () => {
        etfTab.classList.add("active");
        stockScannerTab.classList.remove("active");

        etfPanel.classList.add("active");
        stockScannerPanel.classList.remove("active");
    });
}

// ===============================
// Table Sorting
// ===============================

let currentSortKey = null;
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

    return 0;
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

renderWatchButtons();
applyTableFilters();