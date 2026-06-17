const rows = document.querySelectorAll(".stock-row");
const modal = document.getElementById("stockModal");
const closeBtn = document.getElementById("modalClose");

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");

let priceChart = null;

const CHART_DATA = {
    GOOGL: [312, 318, 306, 299, 315, 322, 331, 344, 352, 347, 356, 361, 389, 394, 384, 392, 386, 381, 388, 375, 371],
    NVDA: [180, 184, 190, 186, 194, 198, 205, 211, 218, 220, 225, 231, 229, 235, 238, 232, 228, 226, 225, 227, 225],
    AMZN: [230, 235, 238, 240, 244, 249, 252, 257, 261, 264, 262, 266, 270, 268, 265, 267, 269, 266, 264, 263, 265],
    AAPL: [270, 272, 275, 281, 285, 288, 290, 294, 298, 296, 299, 301, 304, 306, 303, 300, 297, 295, 296, 298, 296],
    MSFT: [430, 425, 418, 410, 405, 399, 402, 408, 413, 420, 416, 409, 404, 401, 398, 400, 403, 407, 405, 402, 402],
    META: [560, 570, 585, 590, 602, 615, 622, 610, 598, 604, 612, 620, 616, 610, 608, 606, 604, 607, 609, 606, 605],
    TSLA: [390, 400, 415, 430, 445, 460, 452, 440, 435, 442, 455, 465, 472, 460, 455, 448, 440, 438, 442, 447, 445],
};

const CHART_LABELS = [
    "D-20", "D-19", "D-18", "D-17", "D-16",
    "D-15", "D-14", "D-13", "D-12", "D-11",
    "D-10", "D-9", "D-8", "D-7", "D-6",
    "D-5", "D-4", "D-3", "D-2", "D-1", "Today"
];

function formatChange(value) {
    return value >= 0 ? `+${value}%` : `${value}%`;
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

    const buy = stock.price;
    const stop = stock.price * 0.95;
    const tp1 = stock.price * 1.07;
    const tp2 = stock.price * 1.13;

    document.getElementById("entryBuy").textContent = buy.toFixed(2);
    document.getElementById("entryStop").textContent = stop.toFixed(2);
    document.getElementById("entryTp1").textContent = tp1.toFixed(2);
    document.getElementById("entryTp2").textContent = tp2.toFixed(2);

    modal.classList.remove("hidden");

    setTimeout(() => {
        renderPriceChart(stock.ticker);
    }, 50);
}

function closeModal() {
    modal.classList.add("hidden");
}

function renderPriceChart(ticker) {
    const canvas = document.getElementById("priceChart");

    if (!canvas) {
        return;
    }

    const ctx = canvas.getContext("2d");
    const data = CHART_DATA[ticker] || CHART_DATA.GOOGL;

    if (priceChart) {
        priceChart.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 180);
    gradient.addColorStop(0, "rgba(34, 197, 94, 0.25)");
    gradient.addColorStop(1, "rgba(34, 197, 94, 0.02)");

    priceChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: CHART_LABELS,
            datasets: [
                {
                    label: ticker,
                    data: data,
                    borderColor: "#16a34a",
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.35,
                    borderWidth: 3,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false,
                },
                tooltip: {
                    mode: "index",
                    intersect: false,
                    callbacks: {
                        label: function (context) {
                            return `$${context.parsed.y}`;
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
            setTimeout(() => {
                renderPriceChart(ticker);
            }, 50);
        }
    });
});