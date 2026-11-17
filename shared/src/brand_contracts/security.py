"""Shared Clerk session verification + role policy, independent of Django.

Only trusted JWKS URLs from server configuration are used. Do not accept JWKS
locations from token headers or from caller-provided request data.
"""
from collections.abc import Sequence
from functools import lru_cache
import jwt
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError, PyJWKClientConnectionError
from pydantic import ValidationError
from .schemas import ClerkClaims, Role

class TokenRejected(Exception):
    pass

class TokenVerificationUnavailable(TokenRejected):
    """The trusted Clerk JWKS endpoint could not be reached."""
    pass

@lru_cache(maxsize=8)
def jwks_client(url: str) -> PyJWKClient:
    if not url.startswith('https://'):
        raise TokenRejected('Clerk JWKS URL must use HTTPS')
    return PyJWKClient(url, cache_jwk_set=True, lifespan=300)

def verify_clerk_token(token: str, *, issuer: str, jwks_url: str,
                       authorized_parties: Sequence[str],
                       client: PyJWKClient | None = None) -> ClerkClaims:
    if not token or len(token) > 8192 or not issuer.startswith('https://') or not authorized_parties:
        raise TokenRejected('missing Clerk verification configuration or bearer token')
    try:
        key = (client or jwks_client(jwks_url)).get_signing_key_from_jwt(token).key
        decoded = jwt.decode(token, key, algorithms=['RS256'], issuer=issuer,
                             options={'verify_aud': False,
                                      'require': ['sub', 'sid', 'iss', 'azp', 'exp', 'iat', 'nbf']},
                             leeway=5)
        claims = ClerkClaims.model_validate(decoded)
        if claims.azp not in authorized_parties or claims.exp <= claims.iat:
            raise TokenRejected('unexpected authorized party or expiration')
        return claims
    except PyJWKClientConnectionError as exc:
        raise TokenVerificationUnavailable('Clerk JWKS service unavailable') from exc
    except (InvalidTokenError, PyJWKClientError, ValidationError, ValueError, TypeError) as exc:
        raise TokenRejected('invalid or expired Clerk session') from exc

def has_role(actual: Role | None, required: Role) -> bool:
    return actual == required or (actual == Role.EDITOR and required == Role.READER)
