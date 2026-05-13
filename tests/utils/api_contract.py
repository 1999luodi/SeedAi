"""Auto-generated-like API contract for test client usage."""

API_ROUTES = {
    'POST_API_AUTH_LOGIN': '/api/auth/login',
    'POST_API_AUTH_REGISTER': '/api/auth/register',
    'GET_API_USERS_PROFILE': '/api/users/profile',
    'POST_API_ADMIN_USERS_BY_USER_ID_TOGGLE_STATUS': '/api/admin/users/{user_id}/toggle-status',
}


def build_route(route_key: str, **params) -> str:
    template = API_ROUTES[route_key]
    for name, value in params.items():
        template = template.replace('{' + name + '}', str(value))
    return template
