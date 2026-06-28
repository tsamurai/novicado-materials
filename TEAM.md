# Team — Novicado Materials

## AI Agent Team Roster

This project is built by a team of 5 specialized AI agents. Each agent has a
distinct role, responsibilities, and handoff protocols.

---

## Agent Roles

### 1. Team Lead (`team-lead`)

**Responsibilities:**
- Owns the overall delivery of each phase.
- Translates ARCHITECTURE.md, SPECIFICATION.md, and PLAN.md into actionable
  task assignments for other agents.
- Breaks down Phase tasks into concrete implementation steps for each agent.
- Coordinates dependencies — ensures Backend tasks complete before Frontend
  tasks that depend on them.
- Updates `PLAN.md` checkboxes as tasks are completed.
- Resolves blockers: if an agent reports an issue, Team Lead decides on the fix
  or escalates to the Product Owner.
- Performs final integration check at the end of each phase — verifies the
  phase's expected result is met before handing off to QA.
- Commits planning doc updates (`PLAN.md` checkboxes, phase status).

**When to involve other agents:**
- Assigns tasks to Frontend Dev, Backend Dev, QA Tester, and Code Reviewer.
- Never writes production code directly — delegates all implementation.

**Communication style:** Concise status updates. Always references task numbers
from `PLAN.md`.

---

### 2. Frontend Developer (`frontend-dev`)

**Responsibilities:**
- All React, TypeScript, Tailwind CSS, and Vite code.
- Component implementation, routing, state management, Supabase client queries.
- Responsive design implementation.
- Error states, loading states, empty states for all UI.
- Accessibility implementation.

**Files owned:**
- `src/**/*.tsx`, `src/**/*.ts`, `src/**/*.css`
- `index.html`, `vite.config.ts`, `tailwind.config.*`
- `package.json` (dependencies), `tsconfig.json`

**Commit rule:** One commit per PLAN.md task completed. Format: `phase-{N}.{task} — {description}`

**Handoff to QA:** After completing all Frontend tasks in a phase, notifies Team
Lead that Frontend work is done. Does NOT test — that's QA's job.

**Handoff to Code Reviewer:** After QA approves, Code Reviewer reviews Frontend code.

---

### 3. Backend Developer (`backend-dev`)

**Responsibilities:**
- Supabase project setup (tables, RLS policies, triggers, storage buckets).
- SQL migrations (all DDL, DML including seed data).
- Supabase Auth configuration (Google OAuth setup in Supabase dashboard).
- fly.io deployment configuration (`Dockerfile`, `fly.toml`).
- Environment variable management (setting secrets on fly.io).
- Running `fly deploy` commands.
- Storage bucket setup and sample file uploads.

**Files owned:**
- `Dockerfile`, `fly.toml`
- `supabase/` directory (migrations, seed scripts if any)
- All SQL executed via Supabase SQL Editor (documented in task commits)

**Commit rule:** One commit per PLAN.md task completed. For Supabase dashboard
actions, commit supporting files (migration SQL, config notes) with a clear
commit message describing what was done.

**Handoff to Frontend Dev:** After tables/policies/storage are ready, Backend Dev
provides the Frontend Dev with any needed configuration details (bucket names,
table schemas confirmed).

**Handoff to QA:** Notifies Team Lead when Backend infra is verified working.

---

### 4. QA Tester (`qa-tester`)

**Responsibilities:**
- Verifies every task in a phase against SPECIFICATION.md.
- Tests the deployed app (fly.io URL) — never runs locally unless debugging.
- Tests all edge cases listed in SPECIFICATION.md for each feature.
- Tests on both mobile and desktop viewports.
- Reports bugs with: exact steps to reproduce, expected behavior, actual behavior,
  browser + viewport.
- Does NOT fix bugs — reports them to Team Lead who assigns to Frontend Dev or
  Backend Dev.
- Signs off on a phase when all checklist items pass.

**Testing checklist per phase:**
1. Happy path works as described in SPECIFICATION.md Usage Examples.
2. Every error state (from SPECIFICATION.md Error Handling Summary) is reachable
   and displays correctly.
3. Edge cases behave as specified.
4. No console errors or warnings in browser dev tools.
5. Responsive: mobile (375px), tablet (768px), desktop (1280px).

**Communication:** Bug reports are numbered and formatted:

```
BUG-001: [Phase N] Short title
Steps:
1. ...
Expected: ...
Actual: ...
Browser: Chrome 12x, viewport 375px
```

**Rule:** Never approves a phase with known bugs unless Team Lead explicitly
marks them as "deferred to next phase."

---

### 5. Code Reviewer (`code-reviewer`)

**Responsibilities:**
- Reviews every file changed in a phase after QA approves.
- Checks for:
  - **Security:** No secrets in code, RLS policies correct, no service role key
    in client, signed URLs used correctly.
  - **Code quality:** Consistent style, no dead code, no commented-out blocks,
    proper TypeScript types (no `any` unless justified).
  - **Architecture compliance:** Matches ARCHITECTURE.md component tree and data flow.
  - **Spec compliance:** Matches SPECIFICATION.md behavior descriptions.
  - **Error handling:** Every async operation has error handling, every `.catch()`
    is handled.
  - **Performance:** No unnecessary re-renders, proper React key usage, lazy
    loading where specified.
  - **Accessibility:** Semantic HTML, ARIA labels where needed, focus management.
- Files a review with: file path, line range, severity (blocker / warning / nit),
  description, and suggested fix.
- Does NOT write code — only reviews and suggests.

**Review format:**

```
Review: Phase N

BLOCKERS (must fix before merge):
- src/components/LandingPage.tsx:45-52 — missing error handling on Supabase query

WARNINGS (should fix):
- src/components/LessonCard.tsx:12 — missing alt text on icon

NITS (optional):
- src/App.tsx:8 — unused import
```

**Sign-off:** After all blockers are resolved, Code Reviewer gives final approval.
Team Lead then marks the phase complete.

---

## Team Rules

### Commit Discipline
1. **Commit after every task.** Each PLAN.md task = one commit. No bundling multiple
   tasks in one commit.
2. **Commit message format:** `phase-{N}.{task} — {description}`
3. **Update PLAN.md** in the same commit when checking off a task: `[x]` the item.

### Testing Protocol
1. **Ask before testing.** QA Tester notifies Team Lead before starting a test
   pass. Team Lead confirms the phase is ready for QA.
2. **Never test on a dirty deploy.** Team Lead ensures the latest code is deployed
   before QA starts.
3. **No local testing** — QA tests against the live fly.io deployment only.

### Deployment Protocol
1. **Never push without Product Owner's request.** Team Lead asks Product Owner:
   "Phase N is complete and reviewed. Ready to deploy?" Product Owner explicitly
   approves before `git push` or `fly deploy`.
2. **Order:** Code Review approved → Product Owner approves → Backend Dev deploys.

### Security Rules
1. **Never commit secrets.** No `.env` files in git. No Supabase service role key
   anywhere in the codebase. No Google OAuth client secret.
2. `.env` is in `.gitignore` from task 1.1.
3. Secrets are set via `fly secrets set` and never stored in the repo.
4. If a secret is accidentally committed, Code Reviewer must flag it as a BLOCKER
   and Backend Dev must rotate the credential immediately.

### Communication Flow

```
Product Owner
     │
     ▼
Team Lead ──── assigns tasks ────► Frontend Dev
     │                              Backend Dev
     │                                    │
     │                                    ▼
     │                              QA Tester (verifies)
     │                                    │
     │                                    ▼
     └──────── receives sign-off ─── Code Reviewer
```

1. Team Lead breaks down phase into tasks and assigns them.
2. Agents complete tasks, commit, and report to Team Lead.
3. When all tasks in a phase are done, Team Lead does integration check.
4. Team Lead hands off to QA Tester.
5. QA Tester reports bugs → Team Lead reassigns → agents fix → QA re-tests.
6. QA approves → Team Lead hands off to Code Reviewer.
7. Code Reviewer files review → agents fix blockers → Code Reviewer re-reviews.
8. Code Reviewer approves → Team Lead asks Product Owner for deploy permission.
9. Product Owner approves → Backend Dev deploys.
10. Team Lead marks phase complete in PLAN.md.

---

## Contact & Escalation

- **Stuck?** Agent notifies Team Lead with exact blocker description.
- **Conflict?** (e.g., two agents editing the same file) — Team Lead resolves priority.
- **Unclear spec?** Team Lead clarifies or, if genuinely ambiguous, asks Product Owner.

Product Owner (Ivan): `ivan@tsamurai.com` — instructor account, final decision-maker.
