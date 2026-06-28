# Database Setup — Novicado Materials

Run these blocks **in order** in the Supabase SQL Editor
(Project → SQL Editor → New query).

---

## Block 1: Create tables + RLS policies + profiles trigger

```sql
-- ============================================================
-- TABLE: lessons
-- ============================================================
CREATE TABLE public.lessons (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title       TEXT NOT NULL,
  description TEXT NOT NULL,
  sort_order  INTEGER NOT NULL UNIQUE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Public read access (anon users can see the lesson list)
ALTER TABLE public.lessons ENABLE ROW LEVEL SECURITY;
CREATE POLICY "lessons_select_public"
  ON public.lessons
  FOR SELECT
  USING (true);

-- ============================================================
-- TABLE: materials
-- ============================================================
CREATE TABLE public.materials (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lesson_id    UUID NOT NULL REFERENCES public.lessons(id) ON DELETE CASCADE,
  title        TEXT NOT NULL,
  file_type    TEXT NOT NULL CHECK (file_type IN ('pdf', 'markdown')),
  storage_path TEXT NOT NULL,
  file_size    INTEGER,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Only authenticated users can read materials
ALTER TABLE public.materials ENABLE ROW LEVEL SECURITY;
CREATE POLICY "materials_select_authenticated"
  ON public.materials
  FOR SELECT
  USING (auth.role() = 'authenticated');

-- ============================================================
-- TABLE: profiles
-- ============================================================
CREATE TABLE public.profiles (
  id         UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email      TEXT NOT NULL UNIQUE,
  full_name  TEXT,
  avatar_url TEXT,
  role       TEXT NOT NULL DEFAULT 'student'
               CHECK (role IN ('student', 'instructor')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Anyone authenticated can read profiles (needed for name/avatar)
CREATE POLICY "profiles_select_authenticated"
  ON public.profiles
  FOR SELECT
  USING (auth.role() = 'authenticated');

-- Users can insert their own profile row
CREATE POLICY "profiles_insert_own"
  ON public.profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

-- Users can update their own profile row
CREATE POLICY "profiles_update_own"
  ON public.profiles
  FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- ============================================================
-- FUNCTION + TRIGGER: auto-create profile on sign-up
-- ============================================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, avatar_url)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data ->> 'full_name',
    NEW.raw_user_meta_data ->> 'avatar_url'
  );
  RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
```

---

## Block 2: Seed the 6 lessons

Run this **after** Block 1 succeeds.

```sql
INSERT INTO public.lessons (title, description, sort_order) VALUES
(
  'GitHub, Zed, DeepSeek & Context Optimization',
  'Set up your AI dev workspace: Zed editor, DeepSeek API, Git/GitHub, and context optimization. Build and publish your first project.',
  1
),
(
  'Architecture, Design & AI Agent Team',
  'Act as Product Owner: generate architecture/spec/plan/team docs, design a UI, and assemble an AI agent team to build Phase 1.',
  2
),
(
  'Deployment & Databases',
  'Take your project live on fly.io with a Supabase database and Google sign-in.',
  3
),
(
  'Autonomous AI Agent with Memory',
  'Build a 24/7 Telegram AI agent with a second-brain wiki that stores and structures everything it learns.',
  4
),
(
  'AI Marketing Team',
  'Create an AI marketing team (CMO, SEO, content writer, Telegram publisher) that produces and schedules content automatically.',
  5
),
(
  'Diploma Project — Product Presentation',
  'Prepare and deliver your final presentation: AI-generated slides, pitch script, and live demo.',
  6
);
```

---

## Verification

After running both blocks, confirm the data is in place:

```sql
SELECT * FROM public.lessons ORDER BY sort_order;
```

Expected: 6 rows with `sort_order` 1 through 6.
