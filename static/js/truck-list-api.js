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
                '<td class="table-cell"><div class="flex items-center gap-2">' +
                '<button hx-get="' + templateUrl(detailTemplate, truck.id) + '" hx-target="#modal-content" hx-swap="innerHTML" class="inline-flex items-center gap-1 text-[#810B38] hover:text-[#5C0828] text-sm font-medium"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>View</button>' +
                '<button hx-get="' + templateUrl(editTemplate, truck.id) + '" hx-target="#modal-content" hx-swap="innerHTML" class="inline-flex items-center gap-1 text-amber-600 hover:text-amber-800 text-sm font-medium"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>Edit</button>' +
                '<button hx-get="' + templateUrl(deleteTemplate, truck.id) + '" hx-target="#modal-content" hx-swap="innerHTML" class="inline-flex items-center gap-1 text-red-600 hover:text-red-800 text-sm font-medium"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>Delete</button>' +
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
