# Live walkthrough: Next.js + Clerk edition (~10 min)

1. **Architecture (1 min):** Show `docker-compose.yml`: original WP MariaDB as source, separate PostgreSQL for content Django and authorization Django, and Next.js `web` at port 3000. Note the challenge deviation: Clerk owns credential exchange instead of Django.
2. **Data migration (2 min):** Show `reviews/models.py` and `migrate_wp.py`. WP postmeta became typed domain columns; WP ID unique keys make migration replayable; public rating is derived from Review instead of ACF. `Reviewer` is attribution, not an account. Run `docker compose exec main python manage.py migrate_wp --dry-run`.
3. **API (1 min):** Show `/api/brands/` with industry, sort, page. Show correlated subquery for top review. Show Pydantic schemas in `shared/` for query, response and imported records. New Next JSON endpoints for homepage and detail pages.
4. **Next UX (2 min):** Browse homepage -> `/brand` -> detail -> review; inspect client `BrandList`: URL-synced state via Next router, native select controls, AbortController, accessible live announcements and retry UI. Show Sass tokens/partials.
5. **Clerk and authorization (2 min):** Sign in on Next; link the signed-in account by **verified Clerk user ID** with `link_clerk_user`. Visit `/editor`. Explain trusted Next handler gets Clerk session token, main validates RS256/JWKS/issuer/authorized-party, separate auth service checks live Clerk session (revocation) and role in its own DB before write. No implicit email-based linking, so new signups cannot impersonate migrated admin. Reader=403, missing=401, auth outage=503.
6. **Shared package and tests (2 min):** `shared/pyproject.toml` v0.2.0; same package installed in both services. `pytest -q /app/shared/tests` and Django test suites; signing key, expiry, issuer and allowed-origin tests. Discuss immutable wheels for independent release cadence, and that Docker/integration tests must be run locally.

## Likely requirement prompts

- **Bulk user activation:** Provision Clerk accounts or invitations administratively, then write a one-time reviewed mapping from WP IDs to Clerk IDs; never match unverified email to editor roles.
- **Immediate read revocation:** Public reads need no token; protected reads would need the same live authorization check. Consider caching only low-risk reads.
- **API caching/scale:** Paginate by cursor for 100x brands, add ETags and brief response caching, update materialized averages asynchronously with nightly reconciliation.
- **Audit/edit history:** Store an immutable `BrandEdit` event with Clerk subject, previous/new values and timestamp in content DB; keep role authority in auth DB.
- **Clerk outage:** Public directory remains available. Protected edits fail closed and expose an understandable retry message; never downgrade to unsigned data.

## Decisions to own

The original instructions expect a separate Django **login** endpoint. This version instead routes authentication via a managed provider because the requested Next.js + Clerk stack changes the boundary. The Django auth service still owns application-specific access control and WP user migration. It deliberately does **not** share database models or password verification with the content service. Be explicit that this is a deviation and describe an alternative if strict compliance is requested.
