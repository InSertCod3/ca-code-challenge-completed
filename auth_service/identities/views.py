"""Only auth-owned role lookup for verified, live Clerk sessions."""

import json, logging, os, secrets
import traceback
from urllib.error import URLError, HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError
from brand_contracts.schemas import (
    TokenIntrospectionRequest,
    Introspection,
    Role,
    ClerkSession,
)
from brand_contracts.security import (
    verify_clerk_token,
    TokenRejected,
    TokenVerificationUnavailable,
)
from .models import User

logger = logging.getLogger(__name__)


def clerk_config():
    return dict(
        issuer=os.getenv("CLERK_ISSUER", ""),
        jwks_url=os.getenv("CLERK_JWKS_URL", ""),
        authorized_parties=[
            s.strip()
            for s in os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(",")
            if s.strip()
        ],
    )


def live_session(claims):
    """Clerk BAPI check ensures logged-out/revoked sessions cannot write."""
    secret = os.getenv("CLERK_SECRET_KEY", "")
    if not secret.startswith(("sk_live_", "sk_test_")):
        raise OSError("Missing Clerk backend secret")
    url = "https://api.clerk.com/v1/sessions/" + quote(claims.sid, safe="")
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {secret}",
            "Accept": "application/json",
            "User-Agent": "ca-code-challenge-auth-service/1.0",
        },
    )
    try:
        with urlopen(req, timeout=3) as response:
            session = ClerkSession.model_validate_json(response.read(16384))
            # TODO: Add a warning in in respective callers of live_session if the user doesn't exist in the database
            # this is to avoid silent errors without know what's truly happening
            print(session)
    except HTTPError as exc:
        body = exc.read(4096)
        try:
            details = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            details = {}
        if not isinstance(details, dict):
            details = {}
        errors = details.get("errors", [])
        error_codes = []
        error_messages = []
        if isinstance(errors, list):
            for error in errors:
                if not isinstance(error, dict):
                    continue
                if isinstance(error.get("code"), str):
                    error_codes.append(error["code"])
                message = error.get("long_message") or error.get("message")
                if isinstance(message, str):
                    error_messages.append(message)
        if not error_messages and body:
            error_messages.append(body.decode("utf-8", "replace").strip()[:256])
        for value in (secret, claims.sid, claims.sub):
            if value:
                error_messages = [
                    message.replace(value, "[redacted]") for message in error_messages
                ]
        headers = exc.headers or {}
        request_id = (
            headers.get("x-clerk-request-id")
            or headers.get("x-clerk-trace-id")
            or headers.get("clerk-trace-id")
            or details.get("clerk_trace_id")
        )
        cloudflare_ray_id = headers.get("cf-ray") or details.get("ray")
        logger.warning(
            "Clerk session lookup failed: status=%s content_type=%s response_bytes=%s "
            "error_codes=%s error_messages=%s request_id=%s cloudflare_ray_id=%s www_authenticate=%s",
            exc.code,
            headers.get("content-type"),
            len(body),
            sorted(set(error_codes)),
            error_messages,
            request_id,
            cloudflare_ray_id,
            headers.get("www-authenticate"),
        )
        raise
    active = (
        session.id == claims.sid
        and session.user_id == claims.sub
        and session.status == "active"
    )
    request_id = response.headers.get("x-clerk-request-id") or response.headers.get(
        "clerk-trace-id"
    )
    logger.debug(
        "Clerk session lookup completed: status=%s active=%s request_id=%s",
        response.status,
        active,
        request_id,
    )
    return active


@csrf_exempt
def introspect(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "method_not_allowed"}, status=405, headers={"Allow": "POST"}
        )
    key = os.getenv("AUTH_INTROSPECT_KEY", "")
    if len(key) < 32 or not secrets.compare_digest(
        request.headers.get("X-Service-Key", ""), key
    ):
        return JsonResponse({"error": "forbidden"}, status=403)
    if len(request.body) > 10000:
        return JsonResponse({"error": "payload_too_large"}, status=413)
    try:
        data = TokenIntrospectionRequest.model_validate_json(request.body)
        claims = verify_clerk_token(data.token, **clerk_config())
    except TokenVerificationUnavailable:
        traceback.print_exc()
        return JsonResponse({"error": "clerk_service_unavailable"}, status=503)
    except (ValidationError, TokenRejected):
        return JsonResponse(Introspection(active=False).model_dump(mode="json"))
    try:
        live = live_session(claims)
    except HTTPError as exc:
        if exc.code in (404, 410):
            return JsonResponse(Introspection(active=False).model_dump(mode="json"))
        return JsonResponse({"error": "clerk_service_unavailable"}, status=503)
    except (URLError, TimeoutError, OSError, ValidationError):
        traceback.print_exc()
        # Deny writes if Clerk cannot verify session revocation (fail closed).
        return JsonResponse({"error": "clerk_service_unavailable"}, status=503)
    if not live:
        return JsonResponse(Introspection(active=False).model_dump(mode="json"))
    user = User.objects.filter(clerk_user_id=claims.sub, is_active=True).first()
    return JsonResponse(
        Introspection(
            active=bool(user),
            subject=claims.sub if user else None,
            role=Role(user.role) if user else None,
        ).model_dump(mode="json")
    )
