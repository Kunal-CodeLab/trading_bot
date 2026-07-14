document.addEventListener("DOMContentLoaded", () => {
    const state = {
        side: "BUY",
        type: "MARKET",
        mock: true,
        recentOrders: [],
        logsInterval: null,
        autoScrollLogs: true
    };

    const mockStatusPill = document.getElementById("mock-status-pill");
    const apiStatusPill = document.getElementById("api-status-pill");
    const settingsToggle = document.getElementById("settings-toggle");
    
    const orderForm = document.getElementById("order-form");
    const sideBuyBtn = document.getElementById("side-buy");
    const sideSellBtn = document.getElementById("side-sell");
    const typeTabs = document.querySelectorAll(".type-tab");
    const symbolInput = document.getElementById("symbol");
    const quantityInput = document.getElementById("quantity");
    const priceGroup = document.getElementById("price-group");
    const priceInput = document.getElementById("price");
    const stopPriceGroup = document.getElementById("stop-price-group");
    const stopPriceInput = document.getElementById("stop-price");
    const submitOrderBtn = document.getElementById("submit-order-btn");
    const mockModeSwitch = document.getElementById("mock-mode-switch");

    const summarySymbol = document.getElementById("summary-symbol");
    const summarySide = document.getElementById("summary-side");
    const summaryType = document.getElementById("summary-type");
    const summaryQuantity = document.getElementById("summary-quantity");
    const summaryPriceRow = document.getElementById("summary-price-row");
    const summaryPrice = document.getElementById("summary-price");
    const summaryStopPriceRow = document.getElementById("summary-stop-price-row");
    const summaryStopPrice = document.getElementById("summary-stop-price");

    const configSource = document.getElementById("config-source");
    const configUrl = document.getElementById("config-url");

    const responseStatusBadge = document.getElementById("response-status-badge");
    const responseContent = document.getElementById("response-content");

    const settingsModal = document.getElementById("settings-modal");
    const settingsClose = document.getElementById("settings-close");
    const configForm = document.getElementById("config-form");
    const modalApiKey = document.getElementById("modal-api-key");
    const modalApiSecret = document.getElementById("modal-api-secret");

    const sectionTabs = document.querySelectorAll(".section-tab");
    const tabPanels = document.querySelectorAll(".tab-panel");
    const logTerminal = document.getElementById("log-terminal");
    const clearTerminalBtn = document.getElementById("clear-terminal");
    const ordersTableBody = document.querySelector("#orders-table tbody");

    init();

    function init() {
        fetchConfig();
        fetchLogs();
        state.logsInterval = setInterval(fetchLogs, 2000);
        bindEvents();
        updatePreview();
    }

    function bindEvents() {
        sideBuyBtn.addEventListener("click", () => setSide("BUY"));
        sideSellBtn.addEventListener("click", () => setSide("SELL"));

        typeTabs.forEach(tab => {
            tab.addEventListener("click", (e) => {
                typeTabs.forEach(t => t.classList.remove("active"));
                e.target.classList.add("active");
                setType(e.target.dataset.type);
            });
        });

        mockModeSwitch.addEventListener("change", (e) => {
            setMock(e.target.checked);
        });

        symbolInput.addEventListener("input", updatePreview);
        quantityInput.addEventListener("input", updatePreview);
        priceInput.addEventListener("input", updatePreview);
        stopPriceInput.addEventListener("input", updatePreview);

        orderForm.addEventListener("submit", handleOrderSubmit);

        settingsToggle.addEventListener("click", () => {
            settingsModal.classList.add("open");
        });
        settingsClose.addEventListener("click", () => {
            settingsModal.classList.remove("open");
        });
        settingsModal.addEventListener("click", (e) => {
            if (e.target === settingsModal) {
                settingsModal.classList.remove("open");
            }
        });

        configForm.addEventListener("submit", handleConfigSubmit);

        sectionTabs.forEach(tab => {
            tab.addEventListener("click", (e) => {
                sectionTabs.forEach(t => t.classList.remove("active"));
                tabPanels.forEach(p => p.classList.remove("active"));

                const currentTab = e.currentTarget;
                currentTab.classList.add("active");
                
                const targetId = currentTab.dataset.target;
                document.getElementById(targetId).classList.add("active");
            });
        });

        clearTerminalBtn.addEventListener("click", () => {
            logTerminal.innerHTML = `<div class="log-line text-muted">Terminal cleared by user.</div>`;
        });

        logTerminal.addEventListener("scroll", () => {
            const buffer = 10;
            const isAtBottom = logTerminal.scrollHeight - logTerminal.clientHeight - logTerminal.scrollTop <= buffer;
            state.autoScrollLogs = isAtBottom;
        });
    }

    function setSide(side) {
        state.side = side;
        if (side === "BUY") {
            sideBuyBtn.classList.add("active");
            sideSellBtn.classList.remove("active");
            submitOrderBtn.className = "btn btn-primary btn-block buy-mode";
        } else {
            sideSellBtn.classList.add("active");
            sideBuyBtn.classList.remove("active");
            submitOrderBtn.className = "btn btn-primary btn-block sell-mode";
        }
        updatePreview();
    }

    function setType(type) {
        state.type = type;
        
        if (type === "MARKET") {
            priceGroup.style.display = "none";
            priceInput.removeAttribute("required");
            priceInput.value = "";
            stopPriceGroup.style.display = "none";
            stopPriceInput.removeAttribute("required");
            stopPriceInput.value = "";
        } else if (type === "LIMIT") {
            priceGroup.style.display = "flex";
            priceInput.setAttribute("required", "true");
            stopPriceGroup.style.display = "none";
            stopPriceInput.removeAttribute("required");
            stopPriceInput.value = "";
        } else if (type === "STOP_LIMIT") {
            priceGroup.style.display = "flex";
            priceInput.setAttribute("required", "true");
            stopPriceGroup.style.display = "flex";
            stopPriceInput.setAttribute("required", "true");
        }

        updatePreview();
    }

    function setMock(isMock) {
        state.mock = isMock;
        if (isMock) {
            mockStatusPill.className = "status-pill mock-active";
            mockStatusPill.querySelector(".pill-text").textContent = "Mock Mode Active";
        } else {
            mockStatusPill.className = "status-pill mock-inactive";
            mockStatusPill.querySelector(".pill-text").textContent = "Mock Mode Inactive";
        }
        updatePreview();
    }

    function updatePreview() {
        const symbol = symbolInput.value.trim().toUpperCase() || "-";
        const quantity = quantityInput.value || "-";
        const price = priceInput.value || "-";
        const stopPrice = stopPriceInput.value || "-";

        summarySymbol.textContent = symbol;
        summarySide.textContent = state.side;
        summarySide.className = state.side === "BUY" ? "val text-buy" : "val text-sell";
        summaryType.textContent = state.type;
        summaryQuantity.textContent = quantity;

        if (state.type !== "MARKET") {
            summaryPriceRow.style.display = "flex";
            summaryPrice.textContent = price !== "-" ? `${price} USDT` : "-";
        } else {
            summaryPriceRow.style.display = "none";
        }

        if (state.type === "STOP_LIMIT") {
            summaryStopPriceRow.style.display = "flex";
            summaryStopPrice.textContent = stopPrice !== "-" ? `${stopPrice} USDT` : "-";
        } else {
            summaryStopPriceRow.style.display = "none";
        }

        submitOrderBtn.textContent = `Place ${state.side} ${state.type.replace("_", " ")} Order`;
    }

    function fetchConfig() {
        fetch("/api/config")
            .then(res => res.json())
            .then(data => {
                configUrl.textContent = data.base_url;
                
                if (data.configured) {
                    apiStatusPill.className = "status-pill status-configured";
                    apiStatusPill.querySelector(".pill-text").textContent = `API Linked (${data.source})`;
                    configSource.textContent = data.source;
                    configSource.className = "badge status-configured";
                } else {
                    apiStatusPill.className = "status-pill status-unconfigured";
                    apiStatusPill.querySelector(".pill-text").textContent = "API Disconnected";
                    configSource.textContent = "Unconfigured";
                    configSource.className = "badge";
                }
            })
            .catch(err => console.error("Error fetching config status:", err));
    }

    function handleConfigSubmit(e) {
        e.preventDefault();

        const apiKey = modalApiKey.value.trim();
        const apiSecret = modalApiSecret.value.trim();

        fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: apiKey, api_secret: apiSecret })
        })
        .then(res => {
            if (!res.ok) throw new Error("Credentials override failed.");
            return res.json();
        })
        .then(data => {
            settingsModal.classList.remove("open");
            modalApiKey.value = "";
            modalApiSecret.value = "";
            fetchConfig();
            alert("Credentials override applied successfully to the current session!");
        })
        .catch(err => {
            alert(`Error: ${err.message}`);
        });
    }

    function handleOrderSubmit(e) {
        e.preventDefault();

        const payload = {
            symbol: symbolInput.value.trim(),
            side: state.side,
            type: state.type,
            quantity: quantityInput.value,
            price: state.type !== "MARKET" ? priceInput.value : null,
            stop_price: state.type === "STOP_LIMIT" ? stopPriceInput.value : null,
            mock: state.mock
        };

        submitOrderBtn.disabled = true;
        const originalBtnText = submitOrderBtn.textContent;
        submitOrderBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Processing Order...`;
        
        responseStatusBadge.className = "response-badge pending";
        responseStatusBadge.textContent = "Sending...";

        fetch("/api/order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(resData => {
            submitOrderBtn.disabled = false;
            submitOrderBtn.textContent = originalBtnText;

            if (resData.success) {
                renderOrderSuccess(resData.data);
                addOrderToHistory(resData.data, payload);
            } else {
                renderOrderFailure(resData);
            }
        })
        .catch(err => {
            submitOrderBtn.disabled = false;
            submitOrderBtn.textContent = originalBtnText;
            renderOrderFailure({
                error_type: "NetworkError",
                message: `Failed to communicate with local FastAPI server: ${err.message}`
            });
        });
    }

    function renderOrderSuccess(order) {
        responseStatusBadge.className = "response-badge success";
        responseStatusBadge.textContent = "Success";

        const timeStr = formatTimestamp(order.updateTime);
        const avgPrice = order.avgPrice && parseFloat(order.avgPrice) > 0 ? `${order.avgPrice} USDT` : "N/A";

        responseContent.innerHTML = `
            <div class="response-grid">
                <div class="response-row">
                    <span class="label">Order ID:</span>
                    <span class="value code">${order.orderId}</span>
                </div>
                <div class="response-row">
                    <span class="label">Status:</span>
                    <span class="value badge">${order.status}</span>
                </div>
                <div class="response-row">
                    <span class="label">Executed Qty:</span>
                    <span class="value">${order.executedQty}</span>
                </div>
                <div class="response-row">
                    <span class="label">Average Price:</span>
                    <span class="value">${avgPrice}</span>
                </div>
                <div class="response-row">
                    <span class="label">Execution Time:</span>
                    <span class="value">${timeStr}</span>
                </div>
            </div>
        `;
    }

    function renderOrderFailure(err) {
        responseStatusBadge.className = "response-badge failure";
        responseStatusBadge.textContent = "Failure";

        let errorDetails = "";
        if (err.error_type === "APIError") {
            errorDetails = `Code: ${err.code} | Message: ${err.message}`;
        } else {
            errorDetails = err.message;
        }

        responseContent.innerHTML = `
            <div class="response-error-banner">
                <span><i class="fa-solid fa-circle-exclamation"></i> ${err.error_type}</span>
                <p>${errorDetails}</p>
            </div>
        `;
    }

    function addOrderToHistory(order, reqPayload) {
        state.recentOrders.unshift({
            orderId: order.orderId,
            symbol: order.symbol,
            side: reqPayload.side,
            type: reqPayload.type,
            quantity: reqPayload.quantity,
            price: reqPayload.type === "MARKET" ? "MARKET" : reqPayload.price,
            status: order.status,
            time: formatTimestamp(order.updateTime)
        });

        renderOrdersTable();
    }

    function renderOrdersTable() {
        if (state.recentOrders.length === 0) {
            ordersTableBody.innerHTML = `
                <tr class="no-data-row">
                    <td colspan="8">No orders placed in this session yet.</td>
                </tr>
            `;
            return;
        }

        let html = "";
        state.recentOrders.forEach(o => {
            const sideClass = o.side === "BUY" ? "text-buy" : "text-sell";
            const priceVal = o.price === "MARKET" ? `<span class="text-muted">MARKET</span>` : `${o.price} USDT`;
            html += `
                <tr>
                    <td class="code font-weight-bold">${o.orderId}</td>
                    <td>${o.symbol}</td>
                    <td class="${sideClass} font-weight-bold">${o.side}</td>
                    <td>${o.type}</td>
                    <td>${o.quantity}</td>
                    <td>${priceVal}</td>
                    <td><span class="badge">${o.status}</span></td>
                    <td>${o.time}</td>
                </tr>
            `;
        });
        ordersTableBody.innerHTML = html;
    }

    function fetchLogs() {
        fetch("/api/logs")
            .then(res => res.json())
            .then(data => {
                if (!data.logs || data.logs.length === 0) return;
                
                let html = "";
                data.logs.forEach(line => {
                    let levelClass = "INFO";
                    if (line.includes(" - DEBUG - ")) levelClass = "DEBUG";
                    else if (line.includes(" - WARNING - ")) levelClass = "WARNING";
                    else if (line.includes(" - ERROR - ")) levelClass = "ERROR";
                    else if (line.includes(" - CRITICAL - ")) levelClass = "CRITICAL";

                    html += `<div class="log-line ${levelClass}">${escapeHtml(line)}</div>`;
                });

                logTerminal.innerHTML = html;

                if (state.autoScrollLogs) {
                    logTerminal.scrollTop = logTerminal.scrollHeight;
                }
            })
            .catch(err => {
                console.error("Error reading application logs:", err);
            });
    }

    function formatTimestamp(ms) {
        if (!ms) return "N/A";
        try {
            const date = new Date(parseInt(ms));
            return date.toISOString().replace("T", " ").substring(0, 19) + " UTC";
        } catch (e) {
            return ms;
        }
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
