import logging
import time


request_logger = logging.getLogger("performance.requests")


class RequestTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - started) * 1000
        response["X-Response-Time-ms"] = f"{duration_ms:.1f}"
        request_logger.info(
            "request_timing method=%s path=%s status=%s duration_ms=%.1f edge=%s boosted=%s",
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
            request.META.get("HTTP_X_RAILWAY_EDGE", "-"),
            request.META.get("HTTP_HX_BOOSTED", "false"),
        )
        return response
