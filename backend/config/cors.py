from django.conf import settings
from django.http import HttpResponse


class SimpleCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("origin")
        if request.method == "OPTIONS":
            response = HttpResponse()
        else:
            response = self.get_response(request)

        if self._is_allowed_origin(origin):
            response["Access-Control-Allow-Origin"] = origin
            response["Vary"] = "Origin"
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response["Access-Control-Max-Age"] = "86400"

        return response

    def _is_allowed_origin(self, origin):
        if not origin:
            return False
        if getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False):
            return True
        return origin in getattr(settings, "CORS_ALLOWED_ORIGINS", [])
