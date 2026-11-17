"""Cross-service Pydantic 2 contracts and import validation."""
from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, TypeAdapter, field_validator

class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Role(StrEnum):
    READER = 'reader'
    EDITOR = 'editor'

class ClerkClaims(Contract):
    """Validated Clerk session JWT claims (not a custom JWT template)."""
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    sub: str = Field(min_length=5, pattern=r'^user_[A-Za-z0-9]+$')
    sid: str = Field(min_length=5, pattern=r'^sess_[A-Za-z0-9]+$')
    iss: str = Field(min_length=1)
    azp: str = Field(min_length=1)
    iat: int = Field(gt=0)
    nbf: int = Field(gt=0)
    exp: int = Field(gt=0)

class ClerkSession(Contract):
    """Minimal Clerk Backend API session fields needed for live revocation."""
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)
    id: str
    user_id: str
    status: str

class TokenIntrospectionRequest(Contract):
    token: str = Field(min_length=1, max_length=8192)

class Introspection(Contract):
    active: bool
    subject: str | None = None
    role: Role | None = None

class ReviewDTO(Contract):
    name: str
    slug: str
    brand_name: str
    brand_slug: str
    reviewer_name: str
    reviewer_location: str
    rating: int = Field(ge=1, le=5)
    body: str
    published_at: datetime

class BrandDetailDTO(Contract):
    name: str
    slug: str
    industry: 'IndustryDTO | None'
    average_rating: float | None = Field(default=None, ge=1, le=5)
    review_count: int = Field(ge=0)
    short_description: str
    body: str
    website_url: str
    founded_year: int | None
    headquarters: str
    reviews: list[ReviewDTO]

class RecentReviewsDTO(Contract):
    reviews: list[ReviewDTO]

class BrandPatch(Contract):
    short_description: str = Field(min_length=1, max_length=500)

class BrandListQuery(Contract):
    industry: str | None = Field(default=None, pattern=r'^[a-z0-9-]+$', max_length=120)
    sort: str = Field(default='-average_rating', pattern=r'^(?:-?average_rating|-?review_count)$')
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=50)

class IndustryDTO(Contract):
    name: str
    slug: str

class BrandDTO(Contract):
    name: str
    slug: str
    industry: IndustryDTO | None
    average_rating: float | None = Field(default=None, ge=1, le=5)
    review_count: int = Field(ge=0)
    short_description: str
    top_review_snippet: str | None

class BrandPage(Contract):
    count: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total_pages: int = Field(ge=0)
    next: int | None
    previous: int | None
    results: list[BrandDTO]
    industries: list[IndustryDTO]

class WPIndustry(Contract):
    source_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1)

class WPUser(Contract):
    source_id: int = Field(gt=0)
    username: str = Field(min_length=1)
    email: str = ''
    display_name: str = ''

class WPBrand(Contract):
    source_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1, max_length=200, pattern=r'^[a-z0-9-]+$')
    body: str = ''
    short_description: str = ''
    website_url: str = ''
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    headquarters: str = ''
    source_average_rating: float | None = Field(default=None, ge=0, le=5)
    industry_id: int | None = None
    published_at: datetime

    @field_validator('website_url')
    @classmethod
    def website_is_http(cls, value: str) -> str:
        return str(TypeAdapter(HttpUrl).validate_python(value)) if value else ''

class WPReview(Contract):
    source_id: int = Field(gt=0)
    brand_source_id: int = Field(gt=0)
    author_source_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1, max_length=200, pattern=r'^[a-z0-9-]+$')
    body: str = ''
    rating: int = Field(ge=1, le=5)
    reviewer_name: str = ''
    reviewer_location: str = ''
    published_at: datetime
