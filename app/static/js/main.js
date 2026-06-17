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
        if (event.target.type === "checkbox") {
            return;
        }

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
            matchesFilter = stock && stock.score >= 75;
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

        row.style.display =
            matchesKeyword && matchesFilter ? "" : "none";
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
// Sidebar Accordion
// ===============================

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
    });
});

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

renderWatchButtons();
applyTableFilters();