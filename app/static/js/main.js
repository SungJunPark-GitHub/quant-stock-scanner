const rows = document.querySelectorAll(".stock-row");
const modal = document.getElementById("stockModal");
const closeBtn = document.getElementById("modalClose");

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
}

function closeModal() {
    modal.classList.add("hidden");
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

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");

tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        const target = tab.dataset.tab;

        tabs.forEach((item) => item.classList.remove("active"));
        panels.forEach((panel) => panel.classList.remove("active"));

        tab.classList.add("active");
        document.getElementById(target).classList.add("active");
    });
});