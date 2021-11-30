from flask import g
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