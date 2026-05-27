(function () {
    var trucks = [];

    function statusBadge(truck) {
        var classes = {
            available: "bg-green-100 text-green-700",
            assigned: "bg-blue-100 text-blue-700",
            on_trip: "bg-orange-100 text-orange-700",
            maintenance: "bg-red-100 text-red-700",
            inactive: "bg-gray-100 text-gray-600"
        };
        return '<span class="badge ' + (classes[truck.status] || "bg-gray-100 text-gray-600") + '">' +
            window.TrackerApi.escapeHtml(truck.status_display || truck.status || "-") +
            "</span>";
    }

    function templateUrl(template, id) {
        return template.replace("/0/", "/" + id + "/");
    }

    function formatDate(value) {
        if (!value) {
            return '<span class="text-gray-400">-</span>';
        }
        var date = new Date(value + "T00:00:00");
        return date.toLocaleDateString(undefined, { month: "short", day: "2-digit", year: "numeric" });
    }

    function renderRows(table, rows) {
        if (!rows.length) {
            table.innerHTML = '<tr><td colspan="7" class="table-cell"><div class="empty-state">' +
                '<p class="text-gray-500 font-medium">No trucks found</p>' +
                '<p class="text-gray-400 text-sm mt-1">Adjust filters or add a new truck.</p>' +
                "</div></td></tr>";
            return;
        }

        var detailTemplate = table.getAttribute("data-detail-template");
        var editTemplate = table.getAttribute("data-edit-template");
        var deleteTemplate = table.getAttribute("data-delete-template");
        table.innerHTML = rows.map(function (truck) {
            return '<tr class="hover:bg-gray-50 transition">' +
                '<td class="table-cell font-medium text-[#541A1A]">' + window.TrackerApi.escapeHtml(truck.plate_number) + "</td>" +
                '<td class="table-cell">' + window.TrackerApi.escapeHtml(truck.unit_number || "-") + "</td>" +
                '<td class="table-cell">' + window.TrackerApi.escapeHtml(truck.truck_type_display || truck.truck_type || "-") + "</td>" +
                '<td class="table-cell">' + window.TrackerApi.escapeHtml(truck.capacity || "-") + "</td>" +
                '<td class="table-cell">' + statusBadge(truck) + "</td>" +
                '<td class="table-cell">' + formatDate(truck.registration_expiry) + "</td>" +
                '<td class="table-cell"><div class="flex items-center space-x-2">' +
                '<button hx-get="' + templateUrl(detailTemplate, truck.id) + '" hx-target="#modal-content" hx-swap="innerHTML" class="text-[#810B38] hover:text-[#5C0828] text-sm font-medium">View</button>' +
                '<button hx-get="' + templateUrl(editTemplate, truck.id) + '" hx-target="#modal-content" hx-swap="innerHTML" class="text-amber-600 hover:text-amber-800 text-sm font-medium ml-3">Edit</button>' +
                '<button hx-get="' + templateUrl(deleteTemplate, truck.id) + '" hx-target="#modal-content" hx-swap="innerHTML" class="text-red-600 hover:text-red-800 text-sm font-medium ml-3">Delete</button>' +
                "</div></td></tr>";
        }).join("");

        if (window.htmx) {
            window.htmx.process(table);
        }
    }

    function applyFilters(table) {
        var searchInput = document.querySelector("[data-api-truck-search]");
        var typeInput = document.querySelector("[data-api-truck-type]");
        var statusInput = document.querySelector("[data-api-truck-status]");
        var query = ((searchInput && searchInput.value) || "").trim().toLowerCase();
        var type = (typeInput && typeInput.value) || "";
        var status = (statusInput && statusInput.value) || "";
        var filtered = trucks.filter(function (truck) {
            var searchable = [
                truck.plate_number,
                truck.unit_number,
                truck.truck_type_display,
                truck.status_display,
                truck.registration_number
            ].join(" ").toLowerCase();
            return (!query || searchable.indexOf(query) >= 0) &&
                (!type || truck.truck_type === type) &&
                (!status || truck.status === status);
        });
        renderRows(table, filtered);
    }

    async function hydrateTruckList() {
        var root = document.querySelector('[data-api-list="trucks"]');
        var table = document.querySelector("[data-api-truck-table]");
        if (!root || !table || !window.TrackerApi) {
            return;
        }
        try {
            trucks = await window.TrackerApi.get(root.getAttribute("data-api-url"));
            applyFilters(table);
            ["[data-api-truck-search]", "[data-api-truck-type]", "[data-api-truck-status]"].forEach(function (selector) {
                var input = document.querySelector(selector);
                if (input) {
                    input.addEventListener("input", function () { applyFilters(table); });
                    input.addEventListener("change", function () { applyFilters(table); });
                }
            });
        } catch (error) {
            console.error("Truck API hydration failed:", error);
        }
    }

    document.addEventListener("DOMContentLoaded", hydrateTruckList);
})();
