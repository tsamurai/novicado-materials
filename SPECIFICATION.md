# Specification — Novicado Materials

## 1. Landing Page (`/`)

**What it does:** Displays a public, unauthenticated page listing all 6 course lessons.

**Data handled:**
- Fetches `SELECT * FROM lessons ORDER BY sort_order ASC` using the Supabase anon key (RLS allows public read).
- If the query fails or returns 0 rows, shows an appropriate message (see Error Handling).

**UI behavior:**
- Six lesson cards in a vertical list (mobile) / 2-column grid (tablet+) / 3-column grid (desktop).
- Each card shows: lesson number badge, title, short description.
- Top of page: branding (logo + "Novicado Materials"), a one-liner tagline, and a
  **"Sign in with Google"** button rendered by the `AuthButton` component.
- If the user is already authenticated, the sign-in button is replaced by the
  user's avatar + name + a **"Sign out"** link. Each lesson card becomes clickable
  and links to `/lessons/:id`.

**Edge cases:**
- **Supabase unreachable:** show a centered error state: "Could not load lessons. Please try again." with a Retry button.
- **Zero lessons returned:** show "No lessons available yet." placeholder.
- **Slow network:** show 6 skeleton cards (pulsing gray placeholders) while loading.
- **User has no `profiles` row** (race condition after first sign-in): `AuthProvider` retries the profile fetch up to 3 times with 1-second backoff before falling back to a minimal profile with role `'student'`.

### Usage Example

```
1. Visitor opens https://novicado.fly.dev/
2. Sees 6 lesson cards in a clean grid
3. Clicks "Sign in with Google" → Google consent screen
4. Redirected back → now authenticated
5. Lesson cards become clickable, avatar appears in header
6. Clicks "GitHub, Zed, DeepSeek & Context Optimization" card
7. Navigates to /lessons/{id}
```

---

## 2. Authentication (`AuthButton`, `AuthProvider`, `AuthCallback`)

**What it does:** Handles the full Google OAuth sign-in → session → profile lifecycle.

**Data handled:**
- `supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: `${SITE_URL}/auth/callback` } })`
- `AuthCallback` calls `supabase.auth.exchangeCodeForSession(code)` on mount.
- `AuthProvider` fetches profile: `SELECT * FROM profiles WHERE id = auth.user.id` (single row).
- Profile is stored in React context alongside the Supabase session.

**UI behavior:**
- Sign-in button: Google-branded (Google "G" icon + "Sign in with Google" text), follows Google's branding guidelines.
- When authenticated: circular avatar (or initials fallback), user's name, dropdown with "Sign out".
- Sign-out clears the Supabase session and resets context state.

**Edge cases:**
- **OAuth popup blocked:** Supabase SDK falls back to redirect flow automatically.
- **Google returns error** (e.g. `access_denied`): show "Sign-in was cancelled or failed. Please try again." toast.
- **AuthCallback page accessed directly without code:** redirect to `/` with a warning toast ("No sign-in in progress.").
- **Profile trigger fails** (first sign-in): retry logic (3×, 1s backoff). If still missing after 10s, create profile manually from client with a fallback `INSERT`.
- **Session expired:** Supabase SDK auto-refreshes the token. If refresh fails, user is signed out and redirected to `/` with a toast: "Your session expired. Please sign in again."

---

## 3. Lesson Detail Page (`/lessons/:id`)

**What it does:** Displays a single lesson's materials (PDFs, markdown files) with download links. Requires authentication.

**Data handled:**
- Fetches lesson: `SELECT * FROM lessons WHERE id = :id` (public read).
- Fetches materials: `SELECT * FROM materials WHERE lesson_id = :id ORDER BY created_at ASC` (authenticated read — RLS enforced).
- For each material: generates a signed download URL via `supabase.storage.from('materials').createSignedUrl(storage_path, 300)` (5-minute expiry).

**UI behavior:**
- Breadcrumb: `← Back to all lessons` (links to `/`).
- Lesson title as heading, description as subheading.
- Materials list: each row shows:
  - File type icon (📄 for PDF, 📝 for markdown)
  - Material title
  - File type badge ("PDF" or "Markdown")
  - File size (if available, formatted: "2.4 MB")
  - Download button → opens signed URL in new tab
- If user is not authenticated, `RequireAuth` redirects to `/` with a toast: "Please sign in to view materials."

**Edge cases:**
- **Lesson not found** (invalid UUID or deleted): show 404 state: "Lesson not found." with link home.
- **No materials yet:** show "No materials available for this lesson yet." placeholder.
- **Signed URL generation fails:** show "Download unavailable — please try again." for that row, with a retry button.
- **Supabase Storage unreachable:** same fallback as above, per-material.
- **Supabase DB unreachable:** show full-page error: "Could not load lesson. Please try again." with Retry.

### Usage Example

```
1. Authenticated user navigates to /lessons/abc-123
2. Page loads lesson title "Deployment & Databases"
3. Materials list shows:
   ├── 📄 Deploying to fly.io.pdf  [PDF] [2.1 MB] [Download]
   ├── 📝 Supabase setup guide.md  [Markdown] [8 KB] [Download]
   └── 📄 Environment variables.pdf [PDF] [1.4 MB] [Download]
4. User clicks "Download" on the first row
5. PDF opens in a new browser tab via signed URL
```

---

## 4. Not Found Page (`/*`)

**What it does:** Catches all unmatched routes with a friendly 404 page.

**UI behavior:**
- "Page not found" heading.
- "The page you're looking for doesn't exist." subtext.
- "← Back to all lessons" link.

---

## 5. Layout & Shared UI

**Header (persistent across all routes):**
- Left: "Novicado Materials" logo/text (links to `/`).
- Right: `AuthButton` component.
- Clean white/dark background, subtle bottom border.

**Footer (persistent):**
- Minimal: "Novicado Materials — AI School" centered, small muted text.

**Design system:**
- Colors: Dark slate/charcoal primary, white backgrounds, blue accent for links/buttons.
- Typography: System font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`).
- Cards: white background, subtle border + shadow, rounded corners (`rounded-lg`).
- Buttons: solid blue for primary actions, outlined for secondary.
- Spacing: Tailwind defaults (4px scale).

**Responsive breakpoints:**
- Mobile: < 640px — single column, full-width cards
- Tablet: 640–1024px — 2-column grid for lesson cards
- Desktop: > 1024px — 3-column grid, max-width 1200px container

---

## 6. Instructor Workflow (MVP — Supabase Dashboard)

**What the instructor does (no code):**

1. Opens Supabase dashboard → Table Editor → `lessons` table.
2. Inserts a new lesson row (or edits an existing one).
3. Opens Storage → `materials` bucket.
4. Creates a folder (e.g. `lesson-7/`) and uploads PDF/markdown files.
5. Opens Table Editor → `materials` table.
6. Inserts rows linking each file to its lesson:
   - `lesson_id`: the UUID from step 2
   - `title`: human-readable name
   - `file_type`: `'pdf'` or `'markdown'`
   - `storage_path`: `lesson-7/filename.pdf`

**Role gating (future):** When an in-app admin UI is built (later phase), the `role`
column in `profiles` will be checked client-side and via an RLS `INSERT`/`UPDATE`/`DELETE`
policy on `materials` and `lessons` to restrict writes to `role = 'instructor'`.

---

## 7. Error Handling Summary

| Scenario                        | User sees                                           |
| ------------------------------- | --------------------------------------------------- |
| Supabase unreachable (landing)  | "Could not load lessons. Please try again." + Retry |
| Supabase unreachable (lesson)   | "Could not load lesson. Please try again." + Retry  |
| Lesson not found                | "Lesson not found." + link home                     |
| No materials for lesson         | "No materials available for this lesson yet."       |
| Signed URL generation fails     | "Download unavailable — please try again." + Retry  |
| Session expired                 | Redirect to `/`, toast: "Session expired."          |
| OAuth cancelled/failed          | Toast: "Sign-in was cancelled or failed."           |
| Profile creation race condition | 3 retries → fallback INSERT                         |
| 404 route                       | "Page not found." + link home                       |
| Network slow (loading)          | Skeleton placeholders (cards, rows)                 |

---

## 8. Security Constraints

- **No secrets in frontend code.** Supabase anon key is safe to expose (RLS enforces permissions). No service role key in the client.
- **RLS is the sole authorization layer.** Every table and storage bucket has RLS policies. The client never has write access to `lessons` or `materials` in the MVP (instructor uses Supabase dashboard directly).
- **Signed URLs expire after 5 minutes.** Prevents indefinite unauthenticated access to file downloads.
- **OAuth redirect URI is restricted** in Google Cloud Console to the production URL only (no wildcards).
