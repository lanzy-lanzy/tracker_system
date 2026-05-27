(function () {
    function getCookie(name) {
        var value = "; " + document.cookie;
        var parts = value.split("; " + name + "=");
        if (parts.length === 2) {
            return parts.pop().split(";").shift();
        }
        return "";
    }

    function toJsonBody(body) {
        if (!body || body instanceof FormData) {
            return body;
        }
        if (typeof body === "string") {
            return body;
        }
        return JSON.stringify(body);
    }

    async function request(url, options) {
        var opts = options || {};
        var method = (opts.method || "GET").toUpperCase();
        var headers = Object.assign({ "Accept": "application/json" }, opts.headers || {});
        var body = toJsonBody(opts.body);

        if (body && !(body instanceof FormData) && !headers["Content-Type"]) {
            headers["Content-Type"] = "application/json";
        }
        if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
            headers["X-CSRFToken"] = getCookie("csrftoken");
        }

        var response = await fetch(url, {
            method: method,
            headers: headers,
            body: body,
            credentials: "same-origin"
        });

        if (response.status === 204) {
            return null;
        }

        var contentType = response.headers.get("content-type") || "";
        var payload = contentType.indexOf("application/json") >= 0
            ? await response.json()
            : await response.text();

        if (!response.ok) {
            var message = typeof payload === "string" ? payload : JSON.stringify(payload);
            throw new Error(message || ("Request failed with status " + response.status));
        }
        return payload;
    }

    function formatNumber(value) {
        return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 });
    }

    function formatMoney(value) {
        return "PHP " + Number(value || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function escapeHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    window.TrackerApi = {
        request: request,
        get: function (url) { return request(url); },
        post: function (url, body) { return request(url, { method: "POST", body: body }); },
        patch: function (url, body) { return request(url, { method: "PATCH", body: body }); },
        delete: function (url) { return request(url, { method: "DELETE" }); },
        formatNumber: formatNumber,
        formatMoney: formatMoney,
        escapeHtml: escapeHtml
    };
})();
