const rows = document.querySelectorAll(".stock-row");
const modal = document.getElementById("stockModal");
const closeBtn = document.getElementById("modalClose");

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");
const rangeButtons = document.querySelectorAll(".range-btn");

let priceChart = null;
let currentStock = null;
let currentRange = "6M";

function formatChange(value) {
    return value >= 0 ? `+${value}%` : `${value}%`;
}

function getNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isNaN(number) ? fallback : number;
}

function openModal(ticker) {
    const stock = STOCKS.find((item) => item.ticker === ticker);

    if (!stock) {
        return;
    }

    currentStock = stock;
    currentRange = "6M";
    updateRangeButtons();

    document.getElementById("modalName").textContent = stock.name;
    document.getElementById("modalTicker").textContent = stock.ticker;
    document.getElementById("modalDescription").textContent = stock.description;
    document.getElementById("modalScore").textContent = stock.score;
    document.getElementById("modalPrice").textContent = stock.price;
    document.getElementById("modalChange").textContent = formatChange(stock.change);
    document.getElementById("modalRsi").textContent = stock.rsi;
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

    const price = getNumber(stock.price);
    const atr = getNumber(stock.atr, price * 0.03);

    const buy = price;
    const stop = price - (atr * 1.5);
    const tp1 = price + (atr * 2);
    const tp2 = price + (atr * 3);

    document.getElementById("entryBuy").textContent = buy.toFixed(2);
    document.getElementById("entryStop").textContent = stop.toFixed(2);
    document.getElementById("entryTp1").textContent = tp1.toFixed(2);
    document.getElementById("entryTp2").textContent = tp2.toFixed(2);

    const atrElement = document.getElementById("modalAtr");
    if (atrElement) {
        atrElement.textContent = atr.toFixed(2);
    }

    const canslim = stock.canslim;

    if (canslim) {
        document.getElementById("modalCanslimScore").textContent = canslim.score;
        document.getElementById("modalCanslimCount").textContent =
            `${canslim.passed_count}/${canslim.total_count}`;

        const summaryCanslimScore = document.getElementById("summaryCanslimScore");
        if (summaryCanslimScore) {
            summaryCanslimScore.textContent = `${canslim.passed_count}/7`;
        }

        const list = document.getElementById("modalCanslimList");
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

    const label = document.getElementById("chartRangeLabel");
    if (label) {
        label.textContent = currentRange;
    }
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

closeBtn.addEventListener("click", closeModal);

modal.addEventListener("click", (event) => {
    if (event.target === modal) {
        closeModal();
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeModal();
    }
});

tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        const target = tab.dataset.tab;

        tabs.forEach((item) => item.classList.remove("active"));
        panels.forEach((panel) => panel.classList.remove("active"));

        tab.classList.add("active");
        document.getElementById(target).classList.add("active");

        if (target === "summary" && currentStock) {
            setTimeout(() => {
                renderPriceChart(currentStock, currentRange);
            }, 50);
        }
    });
});

const WATCHLIST_KEY = "quant_watchlist";

function getWatchlist() {
    return JSON.parse(
        localStorage.getItem(WATCHLIST_KEY) || "[]"
    );
}

function saveWatchlist(list) {
    localStorage.setItem(
        WATCHLIST_KEY,
        JSON.stringify(list)
    );
}

function toggleWatchlist(ticker) {
    let watchlist = getWatchlist();

    if (watchlist.includes(ticker)) {
        watchlist = watchlist.filter(
            (item) => item !== ticker
        );
    } else {
        watchlist.push(ticker);
    }

    saveWatchlist(watchlist);
    renderWatchButtons();
}

function renderWatchButtons() {
    const watchlist = getWatchlist();

    document.querySelectorAll(".watch-btn")
        .forEach((button) => {
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

document.querySelectorAll(".watch-btn")
    .forEach((button) => {
        button.addEventListener("click", (event) => {
            event.stopPropagation();

            toggleWatchlist(
                button.dataset.ticker
            );
        });
    });

renderWatchButtons();

const watchFilter =
    document.getElementById(
        "watchlistFilter"
    );

let watchMode = false;

if (watchFilter) {
    watchFilter.addEventListener(
        "click",
        () => {
            watchMode = !watchMode;

            watchFilter.classList.toggle(
                "active"
            );

            const watchlist =
                getWatchlist();

            document.querySelectorAll(
                ".stock-row"
            ).forEach((row) => {
                const ticker =
                    row.dataset.ticker;

                if (
                    watchMode &&
                    !watchlist.includes(
                        ticker
                    )
                ) {
                    row.style.display =
                        "none";
                } else {
                    row.style.display =
                        "";
                }
            });
        }
    );
}