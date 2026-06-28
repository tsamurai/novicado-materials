# Architecture — Novicado Materials

## Overview

A single-page React app (no custom backend) that renders a public landing page with
6 course lessons and, after Google sign-in, lets enrolled students download their
lesson materials. All data, auth, and file storage live in Supabase. The app is
served as a static build from fly.io.

```
┌──────────────────────────────────────────────┐
│                   fly.io                      │
│  ┌────────────────────────────────────────┐  │
│  │         React SPA (Vite + Tailwind)    │  │
│  │                                        │  │
│  │  • Public landing page                 │  │
│  │  • Google sign-in (Supabase client)    │  │
│  │  • Authenticated materials view        │  │
│  │  • Download links (presigned URLs)     │  │
│  └──────────────┬─────────────────────────┘  │
└─────────────────┼────────────────────────────┘
                  │  HTTPS (Supabase JS client,
                  │   anon key — RLS enforced)
                  ▼
┌──────────────────────────────────────────────┐
│              Supabase (free tier)             │
│                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │   Auth   │ │ Postgres │ │   Storage    │  │
│  │ (Google) │ │ (RLS on) │ │ (RLS on)     │  │
│  └──────────┘ └──────────┘ └──────────────┘  │
└──────────────────────────────────────────────┘
```

## Pages & Routes

| Route              | Auth required? | Description                                 |
| ------------------ | -------------- | ------------------------------------------- |
| `/`                | No             | Public landing — 6 lesson cards + sign-in   |
| `/lessons/:id`     | Yes            | Lesson detail — materials list + downloads  |
| `/auth/callback`   | No             | Supabase OAuth redirect handler             |
| `/*` (404 catch)   | No             | Simple "Page not found" with link home      |

## Component Tree

```
<App>
  <SupabaseProvider>          ← wraps app with Supabase client
    <AuthProvider>            ← React context: session, user, profile (incl. role)
      <BrowserRouter>
        <Layout>              ← header (logo, sign-in/out, avatar), <Outlet/>, footer
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/lessons/:id" element={<RequireAuth><LessonPage /></RequireAuth>} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </AuthProvider>
  </SupabaseProvider>
</App>
```

### Key Components

| Component           | Responsibility                                             |
| ------------------- | ---------------------------------------------------------- |
| `LandingPage`       | Fetches `lessons` (public), renders 6 lesson cards         |
| `LessonCard`        | Single card: title, short description, link to lesson page |
| `LessonPage`        | Fetches lesson + materials, renders download list          |
| `MaterialRow`       | Single material: icon, name, file type badge, download btn |
| `Layout`            | Persistent header with branding and auth controls          |
| `AuthButton`        | "Sign in with Google" / user avatar + sign-out             |
| `RequireAuth`       | Route guard — redirects unauthenticated users to `/`      |
| `AuthCallback`      | Handles OAuth redirect, exchanges code for session         |

## Data Model (Supabase Postgres)

### Table: `lessons`

| Column       | Type        | Notes                                |
| ------------ | ----------- | ------------------------------------ |
| `id`         | `uuid`      | PK, default `gen_random_uuid()`      |
| `title`      | `text`      | NOT NULL                             |
| `description`| `text`      | NOT NULL                             |
| `sort_order` | `integer`   | NOT NULL, unique, controls display order |
| `created_at` | `timestamptz`| default `now()`                    |

### Table: `materials`

| Column       | Type        | Notes                                    |
| ------------ | ----------- | ---------------------------------------- |
| `id`         | `uuid`      | PK, default `gen_random_uuid()`          |
| `lesson_id`  | `uuid`      | FK → `lessons.id`, NOT NULL, ON DELETE CASCADE |
| `title`      | `text`      | NOT NULL (display name, e.g. "Slides")  |
| `file_type`  | `text`      | NOT NULL — `'pdf'` or `'markdown'`      |
| `storage_path`| `text`     | NOT NULL — path inside Supabase Storage bucket |
| `file_size`  | `integer`   | nullable, bytes                          |
| `created_at` | `timestamptz`| default `now()`                        |

### Table: `profiles`

| Column       | Type        | Notes                                        |
| ------------ | ----------- | -------------------------------------------- |
| `id`         | `uuid`      | PK, FK → `auth.users.id`, ON DELETE CASCADE  |
| `email`      | `text`      | NOT NULL, unique                             |
| `full_name`  | `text`      | nullable (from Google profile)               |
| `avatar_url` | `text`      | nullable (from Google profile)               |
| `role`       | `text`      | NOT NULL, default `'student'`, CHECK IN (`'student'`, `'instructor'`) |
| `created_at` | `timestamptz`| default `now()`                             |

### Row Level Security (RLS) Policies

**`lessons`:**
- `SELECT` — public (everyone, including anon)

**`materials`:**
- `SELECT` — authenticated users only

**`profiles`:**
- `SELECT` — authenticated users can read any profile (needed for name/avatar display)
- `INSERT` — user can insert their own profile (triggered on sign-up)
- `UPDATE` — user can update their own profile only

**Storage bucket `materials`:**
- `SELECT` — authenticated users only

### Database Trigger

A Postgres function + trigger on `auth.users` INSERT automatically creates a row in
`public.profiles` with the user's `id`, `email`, `full_name`, and `avatar_url` from
the Google OAuth `raw_user_meta_data`.

## External Services

| Service    | Plan       | Purpose                                    |
| ---------- | ---------- | ------------------------------------------ |
| Supabase   | Free tier  | Auth (Google), Postgres DB, file storage   |
| fly.io     | Free tier  | Static site hosting (3 shared-CPU VMs min) |
| Google     | Free       | OAuth 2.0 identity provider (Supabase)     |

## Auth Flow

1. User clicks **"Sign in with Google"** on the landing page.
2. `supabase.auth.signInWithOAuth({ provider: 'google' })` redirects to Google.
3. After consent, Google redirects to `/auth/callback`.
4. `AuthCallback` page exchanges the OAuth code for a Supabase session.
5. On first sign-in, the DB trigger creates their `profiles` row with role `'student'`.
6. `AuthProvider` context makes `session`, `user`, and `profile` available app-wide.
7. User is redirected to `/lessons/:id` (or `/` if no specific lesson).

## File Storage Layout (Supabase Storage)

Bucket name: `materials`

```
materials/
  lesson-1/
    slides.pdf
    cheatsheet.md
    repo-guide.pdf
  lesson-2/
    architecture-template.md
    spec-template.md
  ...
```

The `materials.storage_path` column stores the relative path (e.g. `lesson-1/slides.pdf`).
Download URLs are generated via `supabase.storage.from('materials').createSignedUrl(path, 300)`.

## Environment Variables

| Variable                    | Where set       | Notes                              |
| --------------------------- | --------------- | ---------------------------------- |
| `VITE_SUPABASE_URL`         | fly.io secrets  | Supabase project URL               |
| `VITE_SUPABASE_ANON_KEY`    | fly.io secrets  | Supabase anon (public) key         |
| `VITE_SITE_URL`             | fly.io secrets  | Production URL (for OAuth redirect)|

All three are injected at build time via Vite's `import.meta.env`.
