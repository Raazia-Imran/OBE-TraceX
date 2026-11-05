from django.http import HttpResponseForbidden
from .services import role
class PortalSecurityMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        if request.user.is_authenticated and not role(request.user) and request.path not in ['/logout/', '/healthz/']:
            response = HttpResponseForbidden('This account has no authorized portal role.')
        else: response = self.get_response(request)
        response['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        if request.path != '/healthz/' and not request.path.startswith('/static/'):
            response['Cache-Control'] = 'no-store, private'
        return response
