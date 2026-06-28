# Plan — Novicado Materials

## Phase 1: "Public Shell" — Landing Page + Lesson List from Supabase

**Goal:** The smallest live version. A deployed React app on fly.io that shows
the 6 course lessons from a Supabase database. No auth yet — purely public.

**Expected result:** A visitor opens the URL and sees a clean landing page with
6 lesson cards populated from Supabase. Supabase project is configured with the
`lessons` table and seeded lesson data.

### Task List

| #   | Task                                                          | Depends on | Owner           |
| --- | ------------------------------------------------------------- | ---------- | --------------- |
| 1.1 | Initialize Vite + React + TypeScript project                  | —          | Frontend Dev    |
| 1.2 | Install dependencies: `react-router-dom`, `@supabase/supabase-js`, `tailwindcss`, `@tailwindcss/vite` | 1.1 | Frontend Dev |
| 1.3 | Configure Tailwind (content paths, base styles)               | 1.2        | Frontend Dev    |
| 1.4 | Create `.env` with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (placeholder values) | 1.1 | Frontend Dev |
| 1.5 | Set up Supabase project (free tier): create org, project, note URL + anon key | — | Backend Dev |
| 1.6 | Create `lessons` table in Supabase (SQL from ARCHITECTURE.md) | 1.5        | Backend Dev     |
| 1.7 | Enable RLS on `lessons` — `SELECT` policy: `true` (public read) | 1.6 | Backend Dev |
| 1.8 | Seed `lessons` table with 6 rows (real titles + descriptions) | 1.7        | Backend Dev     |
| 1.9 | Create `supabaseClient.ts` — initialize Supabase JS client   | 1.2, 1.5   | Frontend Dev    |
| 1.10| Build `Layout` component (header, footer, `<Outlet/>`)       | 1.3        | Frontend Dev    |
| 1.11| Build `LandingPage` component — fetch lessons, skeleton loading, error state | 1.9, 1.10 | Frontend Dev |
| 1.12| Build `LessonCard` component — title, description, lesson number badge | 1.11 | Frontend Dev |
| 1.13| Build `NotFound` page (404 catch-all)                         | 1.3        | Frontend Dev    |
| 1.14| Set up React Router with routes: `/`, `/*`                    | 1.10, 1.11, 1.13 | Frontend Dev |
| 1.15| Create `Dockerfile` for static build (nginx serving `dist/`)  | 1.1        | Backend Dev     |
| 1.16| Create `fly.toml` config                                      | 1.15       | Backend Dev     |
| 1.17| Deploy to fly.io (free tier) — `fly launch` + `fly deploy`   | 1.14, 1.15, 1.16 | Backend Dev |
| 1.18| Update `.env` with real Supabase URL + anon key, redeploy     | 1.5, 1.17  | Backend Dev     |
| 1.19| Verify: landing page loads, 6 lesson cards visible, skeleton states work, error states work | 1.17, 1.18 | QA Tester |
| 1.20| Code review — all Phase 1 files                               | 1.19       | Code Reviewer   |

### Phase 1 Checklist (adjusted — local seed data, no Supabase yet)

- [x] Vite + React + Tailwind project initialized & builds
- [x] 6 lessons as local seed data (`src/data/lessons.ts`)
- [x] Landing page renders 6 real lesson cards from local data
- [ ] Loading skeletons (deferred — no async fetch yet)
- [ ] Error state (deferred — no async fetch yet)
- [x] 404 page renders for unknown routes
- [x] Placeholder "Sign in with Google" button in header
- [x] Layout with header, footer, responsive grid
- [ ] Deployed to fly.io (deferred — needs Supabase + Dockerfile)
- [x] All tasks committed individually
- [x] PLAN.md updated with checked-off tasks

---

## Phase 2: "Sign In" — Google Authentication + Profiles

**Goal:** Students can sign in with Google. Their profile is automatically created
in Supabase. The app shows their name and avatar after sign-in.

**Expected result:** A user clicks "Sign in with Google", authenticates, and sees
their avatar + name in the header. A `profiles` row exists in Supabase with role `'student'`.

### Task List

| #   | Task                                                          | Depends on | Owner           |
| --- | ------------------------------------------------------------- | ---------- | --------------- |
| 2.1 | Enable Google OAuth in Supabase (Google Cloud Console: OAuth consent screen, credentials, redirect URI) | Phase 1 | Backend Dev |
| 2.2 | Configure Supabase Auth → Google provider (client ID + secret) | 2.1 | Backend Dev |
| 2.3 | Create `profiles` table in Supabase (SQL from ARCHITECTURE.md) | Phase 1 | Backend Dev |
| 2.4 | Create DB trigger: `handle_new_user` — auto-creates `profiles` row on `auth.users` INSERT | 2.3 | Backend Dev |
| 2.5 | Enable RLS on `profiles`: SELECT (auth), INSERT (own), UPDATE (own) | 2.4 | Backend Dev |
| 2.6 | Build `SupabaseProvider` — wraps app with Supabase client context | Phase 1 | Frontend Dev |
| 2.7 | Build `AuthProvider` — React context: session, user, profile (with retry logic for profile) | 2.6 | Frontend Dev |
| 2.8 | Build `AuthButton` — "Sign in with Google" (unauthenticated) / avatar + name + sign-out (authenticated) | 2.7 | Frontend Dev |
| 2.9 | Build `AuthCallback` page — exchanges OAuth code for session, redirects to `/` | 2.7 | Frontend Dev |
| 2.10| Add `/auth/callback` route to router                           | 2.9, 2.14 | Frontend Dev |
| 2.11| Wire `AuthButton` into `Layout` header                         | 2.8, 2.10 | Frontend Dev |
| 2.12| Update `fly.toml` env vars with production `VITE_SITE_URL`     | Phase 1 | Backend Dev |
| 2.13| Deploy to fly.io with updated env vars                         | 2.12 | Backend Dev |
| 2.14| Verify: sign-in flow works, avatar + name appear, profile created in DB, sign-out clears session | 2.11, 2.13 | QA Tester |
| 2.15| Code review — all Phase 2 files                                | 2.14 | Code Reviewer |

### Phase 2 Checklist

- [ ] Google OAuth configured in Supabase + Google Cloud Console
- [ ] `profiles` table created + trigger functional + RLS enabled
- [ ] Sign-in button visible on landing page
- [ ] Full OAuth flow: click → Google → redirect → authenticated state
- [ ] Avatar + name displayed in header after sign-in
- [ ] Sign-out works, returns to unauthenticated landing page
- [ ] Profile race condition handled (retry logic)
- [ ] OAuth error states handled (cancelled, failed)
- [ ] Session expiry handled gracefully
- [ ] All tasks committed individually
- [ ] PLAN.md updated

---

## Phase 3: "Materials" — Lesson Detail Page + File Downloads

**Goal:** Authenticated users can click a lesson card, see its materials, and
download PDFs and markdown files via signed URLs.

**Expected result:** A signed-in user navigates to `/lessons/:id`, sees a list of
materials with download buttons, and clicking a download opens the file in a new tab.

### Task List

| #   | Task                                                          | Depends on | Owner           |
| --- | ------------------------------------------------------------- | ---------- | --------------- |
| 3.1 | Create `materials` table in Supabase (SQL from ARCHITECTURE.md) | Phase 2 | Backend Dev |
| 3.2 | Enable RLS on `materials`: authenticated users can SELECT     | 3.1        | Backend Dev     |
| 3.3 | Create Supabase Storage bucket `materials` (private)          | Phase 2    | Backend Dev     |
| 3.4 | Enable RLS on `materials` bucket: authenticated users can SELECT | 3.3 | Backend Dev |
| 3.5 | Upload sample materials (1-2 per lesson) to Storage bucket, insert corresponding `materials` rows | 3.1–3.4 | Backend Dev |
| 3.6 | Build `LessonPage` component — fetch lesson + materials, loading, error, empty states | Phase 2 | Frontend Dev |
| 3.7 | Build `MaterialRow` component — icon, title, file type badge, size, download button | 3.6 | Frontend Dev |
| 3.8 | Build `RequireAuth` component — route guard, redirect to `/` with toast | Phase 2 | Frontend Dev |
| 3.9 | Add `/lessons/:id` route (wrapped in `RequireAuth`)           | 3.6, 3.8 | Frontend Dev |
| 3.10| Make `LessonCard` clickable → navigate to `/lessons/:id` (only when authenticated) | Phase 2, 3.9 | Frontend Dev |
| 3.11| Deploy to fly.io                                              | 3.5, 3.10 | Backend Dev     |
| 3.12| Verify: lesson detail page loads, materials listed, download opens file in new tab, 404 for invalid lesson ID, empty state for no materials | 3.11 | QA Tester |
| 3.13| Code review — all Phase 3 files                               | 3.12 | Code Reviewer |

### Phase 3 Checklist

- [ ] `materials` table created + RLS enabled
- [ ] Storage bucket created + RLS enabled + sample files uploaded
- [ ] Lesson cards clickable for authenticated users
- [ ] Lesson detail page shows materials list with download buttons
- [ ] Download opens signed URL in new tab (correct file)
- [ ] Unauthenticated users redirected to landing page with toast
- [ ] Error/empty/loading states all verified
- [ ] All tasks committed individually
- [ ] PLAN.md updated

---

## Phase 4: "Polish" — Responsive Design, Error Boundaries, UX Refinements

**Goal:** Production-quality fit and finish. The app looks and feels polished on
all screen sizes, handles every edge case gracefully, and is ready for real students.

**Expected result:** A responsive, error-resilient app that a student can use on
phone, tablet, or desktop without friction.

### Task List

| #   | Task                                                          | Depends on | Owner           |
| --- | ------------------------------------------------------------- | ---------- | --------------- |
| 4.1 | Responsive audit — verify all breakpoints (mobile, tablet, desktop) | Phase 3 | Frontend Dev |
| 4.2 | Add responsive grid to `LandingPage` (1 col / 2 col / 3 col)  | 4.1        | Frontend Dev    |
| 4.3 | Add responsive layout to `LessonPage` (full-width on mobile)  | 4.1        | Frontend Dev    |
| 4.4 | Add `ErrorBoundary` component — catches render errors, shows fallback UI | Phase 3 | Frontend Dev |
| 4.5 | Wrap app in `ErrorBoundary`                                   | 4.4        | Frontend Dev    |
| 4.6 | Add toast notification system (e.g. `react-hot-toast`)        | Phase 3    | Frontend Dev    |
| 4.7 | Wire up toasts for: sign-in error, sign-out, session expiry, download failure | 4.6 | Frontend Dev |
| 4.8 | Accessibility pass: focus states, `aria-label` on buttons, semantic HTML, color contrast | Phase 3 | Frontend Dev |
| 4.9 | Add favicon + meta tags (title, description, og:image)        | Phase 3    | Frontend Dev    |
| 4.10| Performance: verify bundle size < 200 KB gzipped, lazy-load lesson page | Phase 3 | Frontend Dev |
| 4.11| Deploy to fly.io                                              | 4.1–4.10   | Backend Dev     |
| 4.12| QA: full walkthrough — mobile + desktop, all error states, sign-in/out, downloads | 4.11 | QA Tester |
| 4.13| Code review — all Phase 4 files                               | 4.12 | Code Reviewer |

### Phase 4 Checklist

- [ ] Responsive on mobile, tablet, desktop
- [ ] Error boundary catches and displays gracefully
- [ ] Toast notifications for all key events
- [ ] Accessible (keyboard navigable, screen-reader friendly)
- [ ] Favicon and meta tags present
- [ ] Bundle size acceptable
- [ ] All tasks committed individually
- [ ] PLAN.md updated

---

## Phase 5 (Future): "Admin Upload" — In-App Instructor Page

**Goal:** Instructor can upload materials through the app instead of the Supabase dashboard.

**Not in current scope.** Included here for roadmap visibility.

### Task List (outline only)

| #   | Task                                                              |
| --- | ----------------------------------------------------------------- |
| 5.1 | Add RLS policies: `role = 'instructor'` can INSERT/UPDATE/DELETE on `lessons`, `materials`, and Storage |
| 5.2 | Build `AdminPage` — route gated on `profile.role === 'instructor'` |
| 5.3 | Build `LessonForm` — create/edit lesson (title, description, sort_order) |
| 5.4 | Build `MaterialUpload` — file picker → upload to Storage → insert `materials` row |
| 5.5 | Build `MaterialList` (admin) — edit/delete existing materials |
| 5.6 | QA + deploy |

---

## Dependency Graph

```
Phase 1 ────► Phase 2 ────► Phase 3 ────► Phase 4
                                        └──► Phase 5 (future)
```

Each phase is blocked on the previous one. Within a phase, tasks marked with
dependencies must follow the order. Independent tasks can run in parallel.

## Commit Convention

Every task = one commit. Commit message format:

```
phase-{N}.{task} — {short description}

Example:
phase-1.6 — Create lessons table with RLS policy
```

The AI agent assigned to the task commits immediately after completing it.
The `PLAN.md` checklist for that task is marked `[x]` in the same commit.
