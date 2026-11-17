# Project Notes & Implementation

## Tech Stack & Development Approach

- **ChatGPT:** Used a few passes of ChatGPT to assist with development and implementation.
- **Authentication:** Clerk for user login and authentication.
- **Python Types:** Pydantic for data validation and type definitions.
- **TypeScript:** Prefer Prisma for TypeScript types and schema management going forward.
- **Codebase Size** Intentionally made to be a small as possible code to ensure we have a minimal based to build from in the future

## Architecture & Efficiency

In my opinion, we don't need both Python/Django and TypeScript for the bulk of the application.

TypeScript can handle most of the application logic, reducing complexity and avoiding unnecessary token burn from maintaining multiple languages and frameworks.

The goal is to keep the architecture lean, minimize context and token usage, and improve generation speed.

**Formatting approach:** Intentionally use compact, non-decorative formatting rather than overly elaborate formatting. This helps reduce generated tokens and improves response speed.

## Outstanding Tasks

### 1. Brand Selection Dropdown

**Location:** http://localhost:3000/editor

- Fix or add a dropdown for selecting the correct brand.
- Users should be able to select a brand instead of manually typing everything to match the correct brand.
- The dropdown implementation/code already exists, so investigate and reuse the existing functionality rather than rebuilding it unnecessarily.

### 2. Role-Based User Access

Implement functionality based on user roles.

- Link Clerk users to the appropriate Django user accounts.
- Ensure permissions and access are determined by the user's assigned role.

**Existing admin linking command:**

```bash
docker compose exec auth python manage.py link_clerk_user \
  --username admin \
  --clerk-user-id user_3MC4u5fqzSxvNptFeMP2oGlblHc
```

3. Review URL and ID-Based Routing

Current URL example:

http://localhost:3000/review/smooth-auto-claim-after-a-parking-lot-fender-bender

Issue: Reviews are currently accessed through descriptive URL slugs based on their titles. This creates a dependency between the review's identity and its human-readable title.

If a review title changes, its slug may also need to change. This can break existing links, bookmarks, references, or integrations unless redirects and slug updates are carefully maintained.

Proposed solution:

Transition to unique, stable review IDs as the primary URL identifier.

/review/<id>

For example:

/review/12345

The review title can still be displayed on the page without being responsible for identifying the underlying record.

What this solves:

Stable URLs: Changing a review title won't require changing its URL.

Reliable record lookup: Reviews can be retrieved directly using a unique identifier.

Avoids slug collisions: Different reviews can have similar or identical titles without conflicting URLs.

Simpler integrations: Other application features can reference reviews using a consistent ID.

Future scalability: Makes it easier to support editing, sharing, linking, and referencing reviews across the application.

Expected outcome: Review identity is independent of its title, resulting in more reliable routing and easier long-term maintenance.