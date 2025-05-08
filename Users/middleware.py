from django.utils.timezone import now
from django.contrib.auth.middleware import get_user

class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = request.user

        if user.is_authenticated:
            if not user.last_seen or (now() - user.last_seen).total_seconds() > 60:
                user.last_seen = now()
                user.save(update_fields=['last_seen'])

        return response
