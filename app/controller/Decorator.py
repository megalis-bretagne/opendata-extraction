from flask import g, request, jsonify, current_app
import functools


def isAdmin(f):
    """OAuth 2.0 protected API endpoint accessible via AccessToken with role ADMIN"""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if g.oidc_token_info['usertype'] == 'ADMIN':
            return f(*args, **kwargs)
        else:
            response_body = {'error': 'invalid_role'}
            return response_body, 403, {'WWW-Authenticate': 'Bearer'}

    return decorated


def token_required(f):
    """OAuth 2.0 protected API endpoint accessible via AccessToken with role ADMIN"""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']
        if not token:
            response_body = {'message': 'a valid token is missing'}
            return response_body, 401, {'WWW-Authenticate': 'x-access-tokens'}
        if not (token == current_app.config['API_TOKEN']):
            response_body = {'error': 'token is invalid'}
            return response_body, 401, {'WWW-Authenticate': 'x-access-tokens'}

        return f(*args, **kwargs)

    return decorated
