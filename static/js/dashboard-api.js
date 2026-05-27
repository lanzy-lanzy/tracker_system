(function () {
    function applyDashboardSummary(root, summary) {
        root.querySelectorAll("[data-api-stat]").forEach(function (node) {
            var key = node.getAttribute("data-api-stat");
            if (!Object.prototype.hasOwnProperty.call(summary, key)) {
                return;
            }
            if (node.getAttribute("data-api-format") === "money") {
                node.textContent = window.TrackerApi.formatMoney(summary[key]);
                return;
            }
            node.textContent = window.TrackerApi.formatNumber(summary[key]);
        });
    }

    async function hydrateDashboard() {
        var root = document.querySelector("[data-api-dashboard-url]");
        if (!root || !window.TrackerApi) {
            return;
        }
        try {
            var summary = await window.TrackerApi.get(root.getAttribute("data-api-dashboard-url"));
            applyDashboardSummary(root, summary);
        } catch (error) {
            console.error("Dashboard API hydration failed:", error);
        }
    }

    document.addEventListener("DOMContentLoaded", hydrateDashboard);
})();
