from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import APIKey

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('Authorization')

        if not api_key:
            return None

        try:
            key = APIKey.objects.get(key=api_key, is_active=True)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid or inactive API key.')

        return (key.user, None)  # Returning user instance and auth credentials