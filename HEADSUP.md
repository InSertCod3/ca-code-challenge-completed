# Project Notes & Implementation

## Tech Stack & Development Approach

- **ChatGPT:** Used a few passes of ChatGPT to assist with development and implementation.
- **Authentication:** Clerk for user login and authentication.
- **Python Types:** Pydantic for data validation and type definitions.
- **TypeScript:** Prefer Prisma for TypeScript types and schema management going forward.

## Architecture & Efficiency

In my opinion, we don't need both Python/Django and TypeScript for the bulk of the application.

TypeScript can handle most application logic, reducing complexity and avoiding unnecessary token burn from maintaining multiple languages and frameworks.

The goal is to keep the architecture lean, minimize context and token usage, and improve generation speed.

**Formatting approach:** Intentionally use compact, non-decorative formatting rather than overly elaborate formatting. This reduces generated tokens and improves response speed.

## Outstanding Tasks

### 1. Brand Selection Dropdown

**Location:** http://localhost:3000/editor

**Issue:** Users currently have to manually type brand information and match it correctly. This is error-prone and makes brand selection unnecessarily difficult.

**Solution:**
- Fix or enable the existing brand dropdown implementation.
- Allow users to select the correct brand from available options instead of manually entering and matching brand names.
- Reuse the existing code rather than rebuilding the functionality.

**Expected outcome:** More accurate brand associations, fewer user errors, and a faster editing workflow.

### 2. Role-Based User Access

**Issue:** Clerk handles authentication, but users also need to be associated with the correct application-level accounts and permissions.

**Solution:**
- Link Clerk identities to the appropriate Django user accounts.
- Implement role-based access control so users only have access to functionality and resources permitted by their assigned role.
- Ensure roles are consistently enforced across the application.

**Existing admin linking command:**

```bash
docker compose exec auth python manage.py link_clerk_user \
  --username admin \
  --clerk-user-id user_3MC4u5fqzSxvNptFeMP2oGlblHc
```

**Expected outcome:** Reliable user identification, consistent permissions, and controlled access to administrative and application features.

### 3. Review URL and ID-Based Routing

**Current URL example:**

http://localhost:3000/review/smooth-auto-claim-after-a-parking-lot-fender-bender

**Issue:** Reviews are currently accessed through descriptive URL slugs based on their titles. This creates a dependency between the review's identity and its human-readable title.

If a review title changes, its slug may also need to change. This can break existing links, bookmarks, references, or integrations unless redirects and slug updates are carefully maintained.

**Proposed solution:**

Transition to unique, stable review IDs as the primary URL identifier.

```text
/review/<id>
```

For example:

```text
/review/12345
```

The review title can still be displayed on the page without being responsible for identifying the underlying record.

**What this solves:**
- **Stable URLs:** Changing a review title won't require changing its URL.
- **Reliable record lookup:** Reviews can be retrieved directly using a unique identifier.
- **Avoids slug collisions:** Different reviews can have similar or identical titles without conflicting URLs.
- **Simpler integrations:** Other application features can reference reviews using a consistent ID.
- **Future scalability:** Makes it easier to support editing, sharing, linking, and referencing reviews across the application.

**Expected outcome:** Review identity is independent of its title, resulting in more reliable routing and easier long-term maintenance.