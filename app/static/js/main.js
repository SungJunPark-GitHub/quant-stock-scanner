const rows = document.querySelectorAll(".stock-row");
const modal = document.getElementById("stockModal");
const closeBtn = document.getElementById("modalClose");

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");

let priceChart = null;

function formatChange(value) {
    return value >= 0 ? `+${value}%` : `${value}%`;
}

function getNumber(value, fallback = 0) {
    const number = Number(value);

    if (Number.isNaN(number)) {
        return fallback;
    }

    return number;
}

function openModal(ticker) {
    const stock = STOCKS.find((item) => item.ticker === ticker);

    if (!stock) {
        return;
    }

    document.getElementById("modalName").textContent = stock.name;
    document.getElementById("modalTicker").textContent = stock.ticker;
    document.getElementById("modalDescription").textContent = stock.description;
    document.getElementById("modalScore").textContent = stock.score;
    document.getElementById("modalPrice").textContent = stock.price;
    document.getElementById("modalChange").textContent = formatChange(stock.change);
    document.getElementById("modalRsi").textContent = stock.rsi;

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
        renderPriceChart(stock);
    }, 50);
}

function closeModal() {
    modal.classList.add("hidden");
}

function renderPriceChart(stock) {
    const canvas = document.getElementById("priceChart");

    if (!canvas) {
        return;
    }

    const ctx = canvas.getContext("2d");

    if (priceChart) {
        priceChart.destroy();
    }

    const chart = stock.chart;

    if (!chart) {
        return;
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

        const ticker = row.dataset.ticker;
        openModal(ticker);
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

        if (target === "summary") {
            const ticker = document.getElementById("modalTicker").textContent;
            const stock = STOCKS.find((item) => item.ticker === ticker);

            if (stock) {
                setTimeout(() => {
                    renderPriceChart(stock);
                }, 50);
            }
        }
    });
});