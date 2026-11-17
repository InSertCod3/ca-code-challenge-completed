"""Public server-rendered pages and a small, Pydantic-validated REST interface."""

import json, os
import traceback
from urllib.request import Request, urlopen
from urllib.error import URLError
from django.db.models import Avg, Count, FloatField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError
from brand_contracts.schemas import (
    BrandDTO,
    BrandListQuery,
    BrandPage,
    BrandPatch,
    IndustryDTO,
    Introspection,
    Role,
    BrandDetailDTO,
    ReviewDTO,
    RecentReviewsDTO,
)
from brand_contracts.security import (
    TokenRejected,
    TokenVerificationUnavailable,
    has_role,
    verify_clerk_token,
)
from .models import Brand, Review, Industry


def home(request):
    brands = (
        Brand.objects.with_review_stats()
        .select_related("industry")
        .order_by("-calculated_average", "name")[:6]
    )
    reviews = Review.objects.select_related("brand", "author").order_by(
        "-published_at", "-wp_id"
    )[:6]
    return render(request, "reviews/home.html", {"brands": brands, "reviews": reviews})


def brand_index(request):
    return render(request, "reviews/brand_index.html")


def brand_detail(request, slug):
    brand = get_object_or_404(
        Brand.objects.with_review_stats().select_related("industry"), slug=slug
    )
    return render(
        request,
        "reviews/brand_detail.html",
        {"brand": brand, "reviews": brand.reviews.select_related("author").all()},
    )


def review_detail(request, slug):
    return render(
        request,
        "reviews/review_detail.html",
        {
            "review": get_object_or_404(
                Review.objects.select_related("brand", "author"), slug=slug
            )
        },
    )


def bad_validation(exc):
    return JsonResponse(
        {
            "error": "validation_error",
            "details": [
                {"field": ".".join(map(str, e["loc"])), "message": e["msg"]}
                for e in exc.errors()
            ],
        },
        status=400,
    )


def brand_list_api(request):
    if request.method != "GET":
        return JsonResponse(
            {"error": "method_not_allowed"}, status=405, headers={"Allow": "GET"}
        )
    try:
        q = BrandListQuery.model_validate(request.GET.dict())
    except ValidationError as exc:
        return bad_validation(exc)
    best = (
        Review.objects.filter(brand_id=OuterRef("pk"))
        .order_by("-rating", "-published_at", "-wp_id")
        .values("body")[:1]
    )
    items = Brand.objects.select_related("industry").annotate(
        review_count=Count("reviews"),
        calculated_average=Avg("reviews__rating"),
        sort_rating=Coalesce(
            Avg("reviews__rating"), Value(0.0), output_field=FloatField()
        ),
        top_review=Subquery(best),
    )
    if q.industry:
        items = items.filter(industry__slug=q.industry)
    order = {"average_rating": "sort_rating", "review_count": "review_count"}[
        q.sort.lstrip("-")
    ]
    items = items.order_by(
        ("-" if q.sort.startswith("-") else "") + order, "name", "pk"
    )
    count = items.count()
    pages = (count + q.page_size - 1) // q.page_size
    rows = [
        BrandDTO(
            name=b.name,
            slug=b.slug,
            industry=(
                IndustryDTO(name=b.industry.name, slug=b.industry.slug)
                if b.industry
                else None
            ),
            average_rating=(
                round(float(b.calculated_average), 2)
                if b.calculated_average is not None
                else None
            ),
            review_count=b.review_count,
            short_description=b.short_description,
            top_review_snippet=(b.top_review or "")[:180] or None,
        )
        for b in items[(q.page - 1) * q.page_size : q.page * q.page_size]
    ]
    result = BrandPage(
        count=count,
        page=q.page,
        page_size=q.page_size,
        total_pages=pages,
        next=q.page + 1 if q.page < pages else None,
        previous=q.page - 1 if 1 < q.page <= pages + 1 else None,
        results=rows,
        industries=[
            IndustryDTO(name=i.name, slug=i.slug)
            for i in Industry.objects.order_by("name")
        ],
    )
    return JsonResponse(result.model_dump(mode="json"))


def require_editor(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return JsonResponse({"error": "bearer_token_required"}, status=401)
    token = header[7:].strip()
    try:
        claims = verify_clerk_token(
            token,
            issuer=os.getenv("CLERK_ISSUER", ""),
            jwks_url=os.getenv("CLERK_JWKS_URL", ""),
            authorized_parties=[
                x.strip()
                for x in os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(",")
                if x.strip()
            ],
        )
    except TokenVerificationUnavailable:
        return JsonResponse({"error": "clerk_service_unavailable"}, status=503)
    except TokenRejected:
        return JsonResponse({"error": "invalid_token"}, status=401)
    try:
        req = Request(
            os.getenv("AUTH_INTROSPECT_URL", "http://auth:8000/api/tokens/introspect/"),
            method="POST",
            data=json.dumps({"token": token}).encode(),
            headers={
                "Content-Type": "application/json",
                "X-Service-Key": os.getenv("AUTH_INTROSPECT_KEY", ""),
            },
        )
        with urlopen(req, timeout=2) as response:
            result = Introspection.model_validate_json(response.read(16384))
    except (URLError, TimeoutError, OSError, ValidationError, ValueError):
        return JsonResponse({"error": "authorization_service_unavailable"}, status=503)
    if not result.active or result.subject != claims.sub:
        return JsonResponse({"error": "invalid_token"}, status=401)
    if not has_role(result.role, Role.EDITOR):
        return JsonResponse({"error": "editor_required"}, status=403)
    return None


def brand_patch_api(request, slug):
    if request.method != "PATCH":
        return JsonResponse(
            {"error": "method_not_allowed"}, status=405, headers={"Allow": "PATCH"}
        )
    denied = require_editor(request)
    if denied is not None:
        return denied
    if len(request.body) > 10000:
        return JsonResponse({"error": "payload_too_large"}, status=413)
    try:
        payload = BrandPatch.model_validate_json(request.body)
    except ValidationError as exc:
        return bad_validation(exc)
    brand = get_object_or_404(Brand, slug=slug)
    brand.short_description = payload.short_description
    brand.description_is_edited = True
    brand.save(update_fields=["short_description", "description_is_edited"])
    return JsonResponse(
        {
            "name": brand.name,
            "slug": brand.slug,
            "short_description": brand.short_description,
        }
    )


# The following data endpoints let Next.js replace Django HTML for the public UX
# without duplicating query/business logic or trusting unvalidated payloads.
def review_to_dto(review):
    return ReviewDTO(
        name=review.name,
        slug=review.slug,
        brand_name=review.brand.name,
        brand_slug=review.brand.slug,
        reviewer_name=review.reviewer_name or review.author.display_name,
        reviewer_location=review.reviewer_location,
        rating=review.rating,
        body=review.body,
        published_at=review.published_at,
    )


@csrf_exempt
def brand_detail_api(request, slug):
    # This JSON endpoint is called by the Next.js server route. Mutations are
    # authenticated with a Clerk Bearer token in brand_patch_api, not a Django
    # browser session cookie, so Django's CSRF middleware must not reject the
    # token-authenticated PATCH before the view can verify that token. Keep the
    # exemption scoped to this API endpoint; normal Django forms remain protected.
    if request.method not in ("GET", "PATCH"):
        return JsonResponse(
            {"error": "method_not_allowed"}, status=405, headers={"Allow": "GET, PATCH"}
        )
    if request.method == "PATCH":
        return brand_patch_api(request, slug)
    brand = get_object_or_404(
        Brand.objects.with_review_stats().select_related("industry"), slug=slug
    )
    reviews = list(brand.reviews.select_related("brand", "author"))
    result = BrandDetailDTO(
        name=brand.name,
        slug=brand.slug,
        industry=(
            IndustryDTO(name=brand.industry.name, slug=brand.industry.slug)
            if brand.industry
            else None
        ),
        average_rating=(
            round(float(brand.calculated_average), 2)
            if brand.calculated_average is not None
            else None
        ),
        review_count=brand.review_count,
        short_description=brand.short_description,
        body=brand.body,
        website_url=brand.website_url,
        founded_year=brand.founded_year,
        headquarters=brand.headquarters,
        reviews=[review_to_dto(review) for review in reviews],
    )
    return JsonResponse(result.model_dump(mode="json"))


def review_detail_api(request, slug):
    if request.method != "GET":
        return JsonResponse(
            {"error": "method_not_allowed"}, status=405, headers={"Allow": "GET"}
        )
    review = get_object_or_404(
        Review.objects.select_related("brand", "author"), slug=slug
    )
    return JsonResponse(review_to_dto(review).model_dump(mode="json"))


def recent_reviews_api(request):
    if request.method != "GET":
        return JsonResponse(
            {"error": "method_not_allowed"}, status=405, headers={"Allow": "GET"}
        )
    reviews = Review.objects.select_related("brand", "author").order_by(
        "-published_at", "-wp_id"
    )[:6]
    return JsonResponse(
        RecentReviewsDTO(
            reviews=[review_to_dto(review) for review in reviews]
        ).model_dump(mode="json")
    )
