import requests
from django.conf import settings

def get_valid_access_token(request):
    """
    Checks if the current access token works.
    If expired, tries to refresh.
    If refresh works, updates session with new access.
    """
    access_token = request.session.get('access_token')
    refresh_token = request.session.get('refresh_token')

    if not access_token:
        return None

    # Try a cheap ping to test token validity
    test_url = f"{settings.API_BASE_URL}token/verify/"
    test_response = requests.post(
        test_url,
        json={'token': access_token}
    )

    if test_response.status_code == 200:
        return access_token  # still valid!

    # Else: try refresh
    if not refresh_token:
        return None

    refresh_url = f"{settings.API_BASE_URL}token/refresh/"
    refresh_response = requests.post(
        refresh_url,
        json={'refresh': refresh_token}
    )

    if refresh_response.status_code == 200:
        new_access = refresh_response.json().get('access')
        request.session['access_token'] = new_access
        return new_access

    return None  # refresh failed



