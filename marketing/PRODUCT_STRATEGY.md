# Product Strategy — Novicado Materials

## 1. Product Description

Novicado Materials is the companion web app for Novicado, an AI school that
teaches students how to build real software using modern AI tools (Zed editor,
DeepSeek, GitHub, fly.io, Supabase, AI agents). Students sign in with Google and
instantly access downloadable lesson materials — PDFs, markdown guides, templates,
and cheatsheets — organized by the 6-week course curriculum. A public landing page
showcases the full curriculum so prospective students can see exactly what they'll
learn before enrolling. Built with no custom backend (React + Supabase on fly.io's
free tier), it's a live proof-of-concept that the skills taught in the course are
the same skills used to build the platform itself.

## 2. Target Audience

**Primary: AI-curious builders (developers and technical beginners)**
- Pain point: "I want to build with AI but don't know where to start — too many
  tools, no structured path."
- They've tried following YouTube tutorials but get stuck when things don't work.
- They want hands-on projects, not theory.

**Secondary: Career-switchers into AI-assisted development**
- Pain point: "I know some coding but AI changed everything — I need to catch up fast."
- They value structured curriculum with downloadable reference materials they can keep.

**Where they hang out online:**
- **Twitter/X** — AI dev community, #BuildInPublic, indie hackers
- **GitHub** — browsing open-source AI projects, template repos
- **Reddit** — r/learnprogramming, r/aidev, r/SideProject, r/SaaS
- **Telegram** — AI tool groups, developer communities
- **YouTube** — AI tutorial channels, "I built X with AI" videos
- **Discord** — AI tool servers (Midjourney, Cursor, etc.)

## 3. Growth Loops

### Loop 1: Public curriculum → discovery → enrollment
The landing page is fully public. Each of the 6 lessons has a title and
description visible without signing in. Someone shares a lesson card link on
Twitter ("This AI school teaches you to deploy to fly.io with Supabase —
here's their full curriculum"). Curious developers visit the page, see all 6
lessons, and sign in → become students. The act of sharing creates new users.

### Loop 2: Student project → GitHub → backlink discovery
Lesson 1 literally tasks students with "Build and publish your first project."
Every student project pushed to GitHub becomes a portfolio piece. Students
naturally mention the school in their README ("Built during Novicado AI School").
Other developers find the project → discover the school → enroll.

### Loop 3: Open template materials → SEO / social sharing
Public-facing materials (architecture templates, spec templates, deployment
checklists) are inherently shareable. A single markdown file like
"architecture-template.md" posted on Twitter or indexed by Google becomes a
free lead magnet. Developers find the template → see it's part of a full course →
sign up for the rest.

### Loop 4: Alumni word-of-mouth → cohort growth
Graduates finish the 6-week course with a deployed project, a GitHub portfolio,
and practical AI skills. They share their results in communities they're already
in (Discord, Telegram, Reddit) → peers get curious → next cohort fills up.
The app is the persistent hub alumni still visit for materials.

### Loop 5: "Built with Novicado" badge → social proof
A small badge or footer on student projects ("Built with skills from Novicado
AI School") acts as ambient advertising. Every deployed project becomes a
billboard. The more students deploy, the more the school's name appears in the wild.

## 4. Marketing Ideas

1. **"Build in Public" Twitter thread series** — Document building Novicado
   Materials itself as a 7-part thread series. Each thread covers one lesson's
   topic (e.g., "Thread 3: How I deployed to fly.io with Supabase and Google
   auth — no backend, zero cost"). The product IS the marketing — it proves
   the course works.

2. **Free "AI Dev Stack Cheatsheet" PDF** — Extract a single-page PDF from
   Lesson 1 materials (the tool stack: Zed, DeepSeek, Git, fly.io, Supabase).
   Post it on Twitter/Reddit/Telegram as a free download. Gate it behind a
   one-click Google sign-in on the landing page. Now they're in the app and
   can see the full curriculum.

3. **GitHub template repos** — Publish the architecture template and spec
   template from Lesson 2 as standalone public GitHub repos with clear READMEs.
   Each README ends with: "This template is from Novicado AI School — a 6-week
   course that teaches you to build with AI." SEO-optimized repo names:
   `ai-project-architecture-template`, `product-spec-template`.

4. **Student showcase page** — After each cohort, feature 3-5 student projects
   on the landing page (or a `/showcase` route). "See what our students built
   in 6 weeks." Students share the showcase → their network sees it → enrollment.

5. **Telegram "AI Builders Tips" channel** — A low-effort channel posting one
   practical tip per day (taken from course materials). Each post ends with
   "Learn more in Novicado AI School." The Telegram agent built in Lesson 4
   could even automate this.

6. **YouTube "I built this in 3 hours" video** — Record a time-lapse of building
   the Novicado Materials app itself (React, Supabase, fly.io deploy). Title: "I
   built a full-stack school platform with no backend in 3 hours." The video is
   both a tutorial and an ad — the course teaches the exact skills shown.

7. **Reddit "What I learned" post** — After each cohort, write a genuine
   r/learnprogramming or r/aidev post: "I took a 6-week AI school — here's
   everything I built and what surprised me." Authentic, non-salesy. Links to
   the public curriculum page. This works because the landing page is public
   and shows real value before asking for a sign-up.
