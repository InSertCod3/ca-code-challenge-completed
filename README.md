# Brand Review Journal | Next.js + Clerk + Django

A WordPress-to-Django take-home migration with a **Next.js 16 App Router** frontend, **Clerk** for sign-in and session management, a separate Django **authorization service** with its own PostgreSQL database, a Django **content/API service** with a different PostgreSQL database, a typed WordPress import, and an installable Pydantic 2 shared package.

The original `CHALLENGE.md`, MariaDB seed and WordPress source are preserved. **Important design deviation:** Pillar 5 originally asks for a *Django credentials-for-token login endpoint*. With Clerk selected, credentials and session issuance are handled by Clerk instead; the Django auth service still exists independently and is the only authority for editor/reader roles. Explain that deviation during the live review.

## 1. Startup (Docker only)

1. Create a **Clerk** application at <https://dashboard.clerk.com/>. In its API Keys / configuration, obtain its **publishable key**, **secret key**, **issuer** (the Clerk Frontend API URL) and **JWKS URL**. Add `http://localhost:3000` as an allowed development origin in Clerk if prompted.
2. Copy `.env.example` to `.env` and fill in the five `CLERK_*` / `NEXT_PUBLIC_CLERK_*` values. The `CLERK_JWKS_URL` typically ends in `/.well-known/jwks.json`; `CLERK_ISSUER` is its origin without the slash. **Never commit `.env`, Clerk keys, or real tokens.** Clerk credentials are external to this repository and are required for sign-in and production Next.js builds.
3. Start all containers:

```bash
cp .env.example .env
# Edit .env: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, CLERK_SECRET_KEY,
# CLERK_ISSUER, CLERK_JWKS_URL, CLERK_AUTHORIZED_PARTIES
# Ensure AUTH_INTROSPECT_KEY is a random 32+ character service secret.
docker compose up --build -d
docker compose logs -f web main auth
```

| Component | URL | Purpose |
| --- | --- | --- |
| **Next.js public site** | http://localhost:3000 | Homepage, directory, details, Clerk UI and editor |
| Brand listing | http://localhost:3000/brand | `<BrandList />` client component |
| Editor | http://localhost:3000/editor | Clerk-protected UI; server enforces editor role |
| Content Django | http://localhost:8000 | Original Django-rendered pages, REST backend |
| Brand listing API | http://localhost:8000/api/brands/ | Public REST API |
| Auth Django | http://localhost:8001/api/tokens/introspect/ | Private service-key-protected introspection |
| WordPress fixture | http://localhost:8080 | Migration reference |
| phpMyAdmin | http://localhost:8081 | Original WP data |

Docker initializes WP MariaDB from `db/dump.sql` and independently migrates `content_db` and `auth_db` on startup. Import commands run on every service restart and use unique WP IDs, preserving human-edited brand descriptions and explicitly linked Clerk identities.

To run the frontend without Docker if Node is already installed: `cd frontend && npm install && npm run dev`. Its internal Django URL must point to the reachable Django server (`DJANGO_API_INTERNAL_URL=http://localhost:8000`). Docker is the supported complete setup; no host Node/Python installation is required.

## 2. Sign-in, user migration and authorization

The original nine `wp_users` rows are imported into `auth.identities.User`. `admin` receives `editor`, others `reader`; all imported Django passwords are **unusable**. Clerk owns registration, MFA, passwords, sessions and login. The auth service stores a **unique `clerk_user_id` link** and the role, and can change roles without deploying the content service. Reviewer attribution stays in the content DB and is never an authentication account.

**First editor setup:**

1. Visit <http://localhost:3000/sign-up> and create a Clerk account (or sign in with an existing Clerk account).
2. From the Clerk Dashboard, **verify the account and obtain its user ID**, such as `user_...`.
3. Explicitly link that identity to the migrated WP admin from the trusted terminal:

```bash
docker compose exec auth python manage.py link_clerk_user \
  --username admin --clerk-user-id user_REPLACE_WITH_REAL_CLERK_ID
```

4. Open <http://localhost:3000/editor>. The editor form uses Clerk's `auth().getToken()` on the Next.js server, then calls Django using a Bearer **Clerk session JWT**. This requires the imported account to be both linked **and** an active `editor`.

**Security properties:** We intentionally **never auto-link on email or username**, because unverified signup data must not inherit a WordPress administrator's privileges. A new Clerk account without an explicit mapping gets **401** on protected writes (auth introspection returns inactive). An explicitly mapped reader gets **403**. A mapped editor gets **200**. A missing/invalid session gets **401**. If Clerk or the auth service cannot be consulted for a protected write, the write fails closed (**503**). Public reads are independent of auth availability.

To exercise the Django endpoint directly, obtain a Clerk **session token** from your signed-in Next.js app's SDK `getToken()` (or from a trusted local test client) and then:

```bash
curl -i -X PATCH http://localhost:8000/api/brands/acme-insurance/ \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $CLERK_SESSION_TOKEN" \
  -d '{"short_description":"Updated using a verified Clerk session."}'
```

**Detailed request flow:** Browser -> Next.js route handler (`await auth()`, `await getToken()`) -> main Django (Pydantic body validation + local Clerk RS256 JWT/JWKS checks, including `iss`, `azp`, `sub`, `sid`, `iat`, `nbf`, `exp`) -> auth Django with private `X-Service-Key` -> auth Django validates Clerk JWT, makes a **live Clerk Backend API session lookup**, checks account linkage, active status and current role -> content DB update. No Clerk secret key goes to the browser or the content service. Both services use `brand_contracts.security.verify_clerk_token()` from `shared/` rather than duplicating cryptographic logic.

**Revocation:** Revoke the session in Clerk or deactivate/change the mapping/role in auth Django. Each write performs live session status and live role checks, so a role downgrade or session revoke takes effect on the next write, assuming Clerk is reachable. A Clerk outage blocks writes. The additional network requests trade write latency for immediate revocation and clear ownership. Public queries do not depend on the authorization service.

**Explicit scope change:** There is no Django password exchange or `/api/token/` endpoint anymore. Clerk performs the credential exchange. WP accounts exist as *auth-side role/migration records*, but they are not automatically provisioned in Clerk. Full bulk user migration into Clerk would require an explicit identity import/link strategy and administrative credentials, which are not present in this take-home.

## 3. Public API and migration contracts

```
GET /api/brands/?industry=insurance&sort=-average_rating&page=1&page_size=12
GET /api/brands/<slug>/             # typed public brand + reviews detail
GET /api/reviews/<slug>/            # typed public review detail
GET /api/reviews/recent/            # latest 6 reviews for Next homepage
PATCH /api/brands/<slug>/           # editor only, short_description only
```

For listing, `industry` is an optional slug, `sort` is `-average_rating` / `average_rating` / `-review_count` / `review_count` (negative is descending), `page` starts at 1, `page_size` is 1–50. Response includes `{count,page,page_size,total_pages,next,previous,results,industries}`. Brand rows include name, slug, industry, calculated review average/count, short description and top review snippet. Highest-rated review wins (newest published and then greatest source ID as tie-breakers). Unrated brands return `null` and sort using `0`.

Pydantic 2 contracts validate WordPress source records **before persistence**, Django REST input/output, identity introspection and token claims, plus live Clerk session lookups. Next.js uses strict **Zod** TypeScript validators across its JSON boundaries. The API URL stays the same under Django (`:8000`) and is also proxied for the Next frontend (`:3000/api/...`).

```bash
docker compose exec main python manage.py migrate_wp --dry-run
docker compose exec main python manage.py migrate_wp
# Re-run; upsert keyed on unique WP IDs, never duplicates.
docker compose exec main python manage.py migrate_wp
docker compose exec auth python manage.py migrate_wp_users
```

A separate `Reviewer` model stores immutable WP-attribution snapshots in the content service; it has no password, role or cross-database FK. Brands and reviews use first-class relational fields. `wp_average_rating` is retained as a source-audit value; live listing averages/counts are computed from review rows to prevent stale aggregates. WordPress ACF field markers and Yoast SEO meta are deliberately omitted because they are outside the requested public experience.

## 4. Next.js UI and SCSS

`frontend/` is a **Next.js App Router** app, not Vite. Its pages:

- `/` server-rendered homepage with best-rated brands + recent reviews
- `/brand` URL-synced, filterable/sortable/paginated `<BrandList />` client component, skeleton/error/retry/empty states and AbortController
- `/brand/[slug]` server-rendered brand detail with review links
- `/review/[slug]` server-rendered review detail
- `/sign-in` and `/sign-up` Clerk-provided views, plus Clerk user controls in header
- `/editor` signed-in page with role-enforced PATCH form

SCSS lives at `frontend/scss/` and is compiled automatically by Next (`import '../scss/main.scss'` from the root layout). `base/` owns tokens, focus rules and reset; `layout/` owns grid/header/footers; `components/` owns cards, controls, ratings and auth/editor styles; `pages/` owns home/directory/details. A standalone compilation also works with `cd frontend && npm run scss`.

## 5. Tests, package releases, limitations

`shared/` is a standalone versioned Python wheel (`brand-contracts` **0.2.0**), installed identically into both Django images via `pip install /app/shared`. It contains Pydantic models, RS256/JWKS Clerk verification and role checks, with no Django imports. It does **not** contain framework, HTTP handler, session lookup or persistence code. For independent deployments, publish a pinned versioned wheel to an internal index and roll out backward-compatible DTO changes before removing fields.

```bash
docker compose run --rm --no-deps main pytest -q /app/shared/tests
docker compose run --rm --no-deps main pytest -q /app/reviews/tests
docker compose run --rm --no-deps auth pytest -q /app/identities/tests
docker compose run --rm --no-deps main python manage.py makemigrations --check --dry-run
docker compose exec web node --version
# Optional local: cd frontend && npm run typecheck
```

Pytest **9.x** and Pydantic **2.x** are retained. Unit tests use synthetic RSA-signed Clerk sessions and mocks rather than real Clerk API keys. **Verified here:** 17 standalone shared-library pytest tests pass, Python files compile. **Not verified in this editing environment:** Docker builds, Next.js npm/TypeScript compilation, and Django integration tests, due to absent Docker and unavailable npm/Django installations. Run the above commands locally before submitting.

## 6. Live interview decisions

Be ready to defend these tradeoffs: *using Next.js in addition to retaining Django's required server-rendered pages; delegating credentials to Clerk instead of implementing the original Django login endpoint; the separate authorization database and explicit linking; trusted local JWT validation **plus** live role/session checks; source-ID upserts preserving editorial changes; derived ratings; small shared package; page-number pagination and shareable client-side filters*. If the job demands strict literal compliance with the credential endpoint, discuss how a Clerk authorization-code/session exchange could be placed in Django without duplicating passwords.

See `LIVE_WALKTHROUGH.md` and the unchanged `CHALLENGE.md` for the interview walkthrough and original requirements.


## 7. React / Clerk dependency compatibility

The frontend pins `react` and `react-dom` to **19.2.3**. This satisfies the React peer dependency declared by `@clerk/nextjs` 7.9.22 and is compatible with Next.js 16.0.10. Keep `react` and `react-dom` on the same version. Do not work around peer dependency errors with `--force` or `--legacy-peer-deps`. If dependencies were previously installed with the incompatible 19.2.0 versions, rebuild the frontend image after this update:

```bash
docker compose build --no-cache web
docker compose up -d
```

### PATCH requests and CSRF

The Next.js `/api/brands/[slug]` route obtains the Clerk session token on the server and forwards it to Django as `Authorization: Bearer <token>`. Django's `/api/brands/<slug>/` JSON endpoint is narrowly exempt from Django CSRF middleware because it does not authenticate with browser session cookies; the PATCH handler still verifies the Clerk token and checks the linked editor role with the authorization service. Normal Django browser forms and other non-exempt views remain covered by `CsrfViewMiddleware`. Do not remove the Bearer-token and editor-role checks or broaden the CSRF exemption to the whole application.
