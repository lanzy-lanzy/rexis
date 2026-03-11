from django.utils.deprecation import MiddlewareMixin


class HTMXMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.htmx = request.headers.get('HX-Request', False)
        return None
